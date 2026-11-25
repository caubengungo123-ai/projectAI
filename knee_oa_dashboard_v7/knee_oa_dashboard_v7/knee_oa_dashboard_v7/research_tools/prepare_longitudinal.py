"""Join the reviewed source tables for the 48-month protocol on a local machine."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web_deploy'))
from early_warning import COLUMNS, PROTOCOL_ID, audit


PERSON = ['participant_id']
KNEE = PERSON + ['knee_side']
TABLES = {
    'clinical_baseline': (PERSON, ['age_baseline', 'bmi_baseline'],
                          ['smoking_baseline', 'osteoporosis_baseline']),
    'xray_baseline': (KNEE, ['kl_baseline'],
                      ['knee_injury_history_baseline', 'pain_nrs_baseline']),
    'xray_followup': (KNEE, ['kl_followup', 'outcome_verified'], []),
    'followup_status': (KNEE, ['followup_months', 'prior_knee_replacement',
                               'knee_replacement_before_followup'], []),
}


def required_text(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Cần khai báo {key}.')
    return value.strip()


def file_hash(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def load_table(name, spec, mapping_dir):
    keys, required, optional = TABLES[name]
    columns = spec['columns']
    missing_fields = set(keys + required) - columns.keys()
    unknown_fields = columns.keys() - set(keys + required + optional)
    if missing_fields or unknown_fields:
        raise ValueError(f'{name}: kiểm tra ánh xạ cột {sorted(missing_fields | unknown_fields)}.')
    if any(not isinstance(col, str) or not col.strip() for col in columns.values()):
        raise ValueError(f'{name}: tên cột nguồn phải là chuỗi có giá trị.')
    path = (mapping_dir / required_text(spec, 'path')).resolve()
    delimiter = spec.get('delimiter')
    if not isinstance(delimiter, str) or len(delimiter) != 1 or delimiter in '\r\n':
        raise ValueError(f'{name}: delimiter phải là một ký tự.')
    before = file_hash(path)
    with path.open(encoding='utf-8-sig', newline='') as source:
        header = next(csv.reader(source, delimiter=delimiter), [])
    if any(header.count(col) != 1 for col in columns.values()):
        raise ValueError(f'{name}: cột nguồn được chọn phải xuất hiện đúng một lần ở hàng tiêu đề.')
    # usecols avoids loading unrelated columns, including source identifiers outside the mapping.
    raw = pd.read_csv(path, sep=delimiter, dtype=str, keep_default_na=False,
                      encoding='utf-8-sig', usecols=list(columns.values()))
    if file_hash(path) != before:
        raise ValueError(f'{name}: tệp nguồn đã thay đổi trong lúc đọc.')
    if raw.empty:
        raise ValueError(f'{name}: không có dòng dữ liệu.')

    missing_codes = spec.get('missing_codes', {})
    value_maps = spec.get('value_maps', {})
    if (set(missing_codes) | set(value_maps)) - columns.keys() or 'participant_id' in value_maps:
        raise ValueError(f'{name}: kiểm tra khai báo mã khuyết và mã hóa lại.')
    frame = pd.DataFrame(index=raw.index)
    for target, source in columns.items():
        values = raw[source].str.strip()
        codes = missing_codes.get(target, [])
        if not isinstance(codes, list) or any(not isinstance(code, str) for code in codes):
            raise ValueError(f'{name}/{target}: mã khuyết phải là danh sách chuỗi.')
        values = values.mask(values.isin(codes), '')
        if target in value_maps:
            code_map = value_maps[target]
            if not isinstance(code_map, dict) or any(
                not key.strip() or not isinstance(value, str) for key, value in code_map.items()
            ):
                raise ValueError(f'{name}/{target}: bảng mã phải dùng mã gốc có giá trị và đích là chuỗi.')
            unrecognized = values.ne('') & ~values.isin(code_map)
            if unrecognized.any():
                raise ValueError(f'{name}/{target}: {unrecognized.sum()} dòng có mã ngoài bảng ánh xạ.')
            values = values.replace(code_map)
        frame[target] = values

    empty_keys = frame[keys].eq('').any(axis=1)
    if empty_keys.any():
        raise ValueError(f'{name}: {empty_keys.sum()} dòng thiếu khóa ghép.')
    if 'knee_side' in keys and not frame.knee_side.isin(['L', 'R']).all():
        raise ValueError(f'{name}: khai báo mã bên gối để chuẩn hóa toàn bộ thành L/R.')
    duplicates = frame.duplicated(keys, keep=False)
    if duplicates.any():
        raise ValueError(f'{name}: {duplicates.sum()} dòng trùng khóa; chọn đúng bản đọc/lần khám trước khi ghép.')
    return frame, before


def prepare(mapping_path, manifest):
    mapping_bytes = mapping_path.read_bytes()
    mapping = json.loads(mapping_bytes.decode('utf-8-sig'))
    source_id = required_text(mapping, 'source_id')
    cohort_id = required_text(mapping, 'cohort_id')
    baseline_visit = required_text(mapping, 'baseline_visit_id')
    followup_visit = required_text(mapping, 'followup_visit_id')
    if mapping.get('protocol_id') != PROTOCOL_ID or baseline_visit == followup_visit:
        raise ValueError('Kiểm tra mã protocol và hai mã lần khám.')
    if cohort_id.upper() == 'OAI' and (baseline_visit, followup_visit) != ('V00', 'V06'):
        raise ValueError('Cấu hình OAI cần dùng V00 và V06 cho protocol này.')
    tables = {}
    inputs = {}
    for name in TABLES:
        frame, checksum = load_table(name, mapping['tables'][name], mapping_path.parent)
        tables[name] = frame
        inputs[name] = {'rows': len(frame), 'sha256': checksum}

    joined = tables['xray_baseline']
    links = {}
    for name in ('clinical_baseline', 'xray_followup', 'followup_status'):
        keys = TABLES[name][0]
        cardinality = 'many_to_one' if keys == PERSON else 'one_to_one'
        joined = joined.merge(tables[name], on=keys, how='left', validate=cardinality, indicator=True)
        found = joined.pop('_merge').eq('both')
        links[name] = {'matched_baseline_knees': int(found.sum()),
                       'unmatched_baseline_knees': int((~found).sum())}
    joined = joined.assign(source_id=source_id, cohort_id=cohort_id,
                           baseline_visit_id=baseline_visit, followup_visit_id=followup_visit)
    longitudinal = joined.reindex(columns=COLUMNS, fill_value='').fillna('')
    result, _, issues = audit(longitudinal, manifest)
    report = {'protocol_id': PROTOCOL_ID, 'input_tables': inputs,
              'mapping_sha256': hashlib.sha256(mapping_bytes).hexdigest(), 'links': links, 'audit': result}
    return longitudinal, report, issues


def main():
    parser = argparse.ArgumentParser(description='Ghép bảng lâm sàng và X-quang dọc cho protocol 48 tháng.')
    parser.add_argument('--mapping', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='Thư mục kết quả mới (chưa tồn tại).')
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if output.exists():
            raise ValueError('Thư mục kết quả đã tồn tại. Hãy chọn tên mới.')
        manifest_bytes = args.manifest.read_bytes()
        manifest = json.loads(manifest_bytes.decode('utf-8-sig'))
        longitudinal, report, issues = prepare(args.mapping, manifest)
        report['manifest_sha256'] = hashlib.sha256(manifest_bytes).hexdigest()
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent) as temp:
            stage = Path(temp) / 'prepared'
            stage.mkdir()
            longitudinal.to_csv(stage / 'longitudinal_PRIVATE.csv', index=False, encoding='utf-8-sig')
            issues.to_csv(stage / 'row_issues_PRIVATE.csv', index=False, encoding='utf-8-sig')
            (stage / 'join_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                   encoding='utf-8')
            stage.rename(output)
        result = report['audit']
        print(f"Gối ban đầu: {result['input_rows']} | Gối đủ điều kiện: {result['eligible_rows']}")
        print(f'Báo cáo ghép và kiểm tra: {output / "join_report.json"}')
        if result['global_errors'] or not result['eligible_rows']:
            parser.exit(2, 'Dữ liệu chưa qua kiểm tra. Xem báo cáo trước khi huấn luyện.\n')
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.exit(2, f'Không thể chuẩn bị dữ liệu: {exc}\n')


if __name__ == '__main__':
    main()
