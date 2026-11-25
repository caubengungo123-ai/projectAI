"""Versioned research endpoint. Never turn legacy MatchThem labels into incidence."""
import json
import numpy as np
import pandas as pd

PROTOCOL_ID = 'incident_rkoa_48m_v1'
TARGET = 'incident_rkoa_48m'
FEATURES = ['age_baseline', 'bmi_baseline', 'smoking_baseline',
            'osteoporosis_baseline', 'knee_injury_history_baseline', 'pain_nrs_baseline']
BINARY = FEATURES[2:5]
KEYS = ['source_id', 'cohort_id', 'participant_id', 'knee_side',
        'baseline_visit_id', 'followup_visit_id']
REQUIRED_NUMERIC = ['age_baseline', 'bmi_baseline', 'kl_baseline', 'kl_followup',
                    'followup_months', 'outcome_verified', 'prior_knee_replacement',
                    'knee_replacement_before_followup']
COLUMNS = KEYS + REQUIRED_NUMERIC + FEATURES[2:]
CHECKS = ['permission_confirmed', 'codebook_confirmed', 'participant_namespace_confirmed',
          'predictor_timing_confirmed', 'outcome_definition_confirmed', 'real_observations_confirmed']
PROTOCOL = {
    'protocol_id': PROTOCOL_ID,
    'status': 'research_preparation_no_trained_early_warning_model',
    'unit': 'one knee per participant at one baseline and one follow-up',
    'population': 'adult knees with baseline KL 0 or 1 and no prior knee replacement',
    'horizon_months': 48, 'allowed_visit_window_months': [45, 51],
    'target_1': 'KL 2, 3 or 4 at the selected 48-month follow-up',
    'target_0': 'KL 0 or 1 at the selected 48-month follow-up',
    'excluded': 'missing/unverified outcome, prior or interval knee replacement, other follow-up times',
    'interpretation': 'radiographic status at the specified visit; not first onset time or symptomatic OA',
    'features': FEATURES,
    'split_unit': 'cohort_id + participant_id, shared across all source copies and both knees',
    'deployment': 'not deployed; research protocol needs clinical review and independent evaluation',
}


def template_csv():
    return ','.join(COLUMNS) + '\n'


def manifest_template():
    return {'protocol_id': PROTOCOL_ID, 'is_synthetic': False, 'sources': [{
        'source_id': 'REPLACE_WITH_SOURCE', 'cohort_id': 'REPLACE_WITH_ORIGINAL_COHORT',
        'source_url': '', 'version': '', 'license_or_access_terms': '', 'codebook_reference': '',
        **{key: False for key in CHECKS},
    }]}


def read_csv(source):
    # Preserve leading zeroes in participant identifiers and literal identifiers such as NA.
    return pd.read_csv(source, dtype=str, keep_default_na=False, encoding='utf-8-sig')


def audit(frame, manifest):
    """Return aggregate findings, eligible rows and row reasons; no file writes."""
    df = frame.copy().reset_index(drop=True)
    n = len(df)
    reasons = [[] for _ in range(n)]
    errors = []
    missing = [c for c in KEYS + REQUIRED_NUMERIC if c not in df]
    if missing:
        errors.append('Thiếu cột bắt buộc: ' + ', '.join(missing))
    unexpected = [str(c) for c in df if c not in COLUMNS]
    if unexpected:
        errors.append('Có cột ngoài mẫu chuẩn. Chỉ nhập các cột trong mẫu; không gửi định danh trực tiếp hoặc biến sau theo dõi.')
    if not isinstance(manifest, dict):
        manifest = {}
    if manifest.get('protocol_id') != PROTOCOL_ID:
        errors.append('Manifest chưa khớp phiên bản định nghĩa bài toán.')
    if manifest.get('is_synthetic') is not False:
        errors.append('Chưa xác nhận dữ liệu thực; dữ liệu tổng hợp không được dùng như cohort đánh giá thực.')
    sources = manifest.get('sources', [])
    source_map = {}
    if not isinstance(sources, list):
        sources = []
    for item in sources:
        if not isinstance(item, dict):
            errors.append('Khai báo nguồn không hợp lệ.'); continue
        sid = item.get('source_id')
        if not isinstance(sid, str) or not sid.strip() or sid in source_map:
            errors.append('source_id trong manifest phải có giá trị và duy nhất.'); continue
        source_map[sid] = item
        if any(item.get(k) is not True for k in CHECKS):
            errors.append('Nguồn chưa hoàn tất xác nhận quyền dùng, mã hóa, ID, thời điểm, nhãn và dữ liệu thực.')
        if any(not isinstance(item.get(k), str) or not item[k].strip() for k in
               ['cohort_id', 'source_url', 'version', 'license_or_access_terms', 'codebook_reference']):
            errors.append('Thông tin xuất xứ/phiên bản/codebook của nguồn chưa đầy đủ.')
    if not sources:
        errors.append('Chưa khai báo nguồn trong manifest.')
    if n == 0:
        errors.append('Tệp chỉ có tiêu đề hoặc không có hồ sơ.')

    def flag(mask, message):
        for idx in np.flatnonzero(np.asarray(mask, dtype=bool)):
            reasons[idx].append(message)

    for c in KEYS:
        if c not in df:
            df[c] = ''
        df[c] = df[c].astype('string').fillna('').str.strip()
        flag(df[c].eq(''), 'Thiếu mã nguồn/người/bên gối/lần khám')
    flag(~df.knee_side.isin(['L', 'R']), 'Bên gối phải là L hoặc R')
    flag(df.baseline_visit_id.eq(df.followup_visit_id), 'Lần khám đầu và lần theo dõi phải khác nhau')
    for sid, group in df.groupby('source_id'):
        info = source_map.get(sid)
        if info is None:
            flag(df.index.isin(group.index), 'Nguồn chưa được khai báo')
        elif not group.cohort_id.eq(info.get('cohort_id')).all():
            flag(df.index.isin(group.index), 'cohort_id không khớp nguồn gốc trong manifest')

    for c in REQUIRED_NUMERIC + FEATURES[2:]:
        if c not in df:
            df[c] = np.nan
        raw = df[c].astype('string').fillna('').str.strip()
        value = pd.to_numeric(raw.where(raw.ne(''), np.nan), errors='coerce').astype(float)
        flag(raw.ne('') & (~np.isfinite(value)), 'Có giá trị số không hợp lệ')
        df[c] = value
    for c in REQUIRED_NUMERIC:
        flag(df[c].isna(), 'Thiếu biến bắt buộc hoặc kết cục')
    flag(~df.age_baseline.between(18, 100), 'Tuổi ngoài khoảng kiểm tra dữ liệu 18–100')
    flag(~df.bmi_baseline.between(10, 70), 'BMI ngoài khoảng kiểm tra dữ liệu 10–70')
    for c in ['kl_baseline', 'kl_followup']:
        flag(~df[c].isin([0, 1, 2, 3, 4]), 'KL phải là số nguyên 0–4, không làm tròn điểm khác')
    flag(~df.kl_baseline.isin([0, 1]), 'Không thuộc nhóm KL 0/1 ban đầu')
    flag(~df.followup_months.between(45, 51), 'Ngoài cửa sổ theo dõi 45–51 tháng')
    flag(~df.outcome_verified.eq(1), 'Kết cục chưa được xác minh')
    for c in ['prior_knee_replacement', 'knee_replacement_before_followup']:
        flag(~df[c].eq(0), 'Thay khớp hoặc chưa xác định tình trạng thay khớp')
    for c in BINARY:
        flag(df[c].notna() & ~df[c].isin([0, 1]), 'Biến nhị phân phải là 0/1 hoặc để trống')
    flag(df.pain_nrs_baseline.notna() & ~df.pain_nrs_baseline.between(0, 10), 'NRS đau phải trong 0–10')
    duplicate = df.duplicated(['cohort_id', 'participant_id', 'knee_side'], keep=False)
    flag(duplicate, 'Trùng người–bên gối, có thể trùng giữa các bản sao nguồn')
    valid = np.array([not r for r in reasons], dtype=bool)
    eligible = df.loc[valid, COLUMNS].copy() if not errors else df.iloc[:0].reindex(columns=COLUMNS)
    eligible[TARGET] = eligible.kl_followup.ge(2).astype(int)
    eligible['_person_group'] = [json.dumps([c, p], ensure_ascii=False) for c, p in
                                  zip(eligible.cohort_id, eligible.participant_id)]
    counts = {}
    for row in reasons:
        for reason in set(row):
            counts[reason] = counts.get(reason, 0) + 1
    result = {'protocol_id': PROTOCOL_ID, 'input_rows': n, 'eligible_rows': len(eligible),
              'excluded_rows': n - len(eligible), 'global_errors': sorted(set(errors)),
              'exclusion_reasons': counts, 'unexpected_column_count': len(unexpected),
              'participants': int(eligible['_person_group'].nunique()),
              'class_counts': {str(k): int(v) for k, v in eligible[TARGET].value_counts().sort_index().items()},
              'note': 'Qua kiểm tra cấu trúc không xác nhận tính đúng của hồ sơ hay khả năng triển khai lâm sàng.'}
    row_issues = pd.DataFrame({'csv_row': np.arange(n) + 2,
                               'reasons': ['; '.join(dict.fromkeys(r)) for r in reasons]})
    return result, eligible, row_issues
