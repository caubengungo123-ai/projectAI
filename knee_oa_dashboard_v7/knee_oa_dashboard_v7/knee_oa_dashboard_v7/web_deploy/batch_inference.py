"""Validate four MatchThem features and score eligible CSV rows together."""
import csv
import io

import numpy as np
import pandas as pd

from dashboard_core import FEATURES, predict_validated

MAX_BYTES = 2_000_000
MAX_ROWS = 10_000
RESULT_COLUMNS = ['ho_so', 'trang_thai', 'nhan_du_doan', 'diem_nhan_1', 'ly_do']
EXAMPLE_CSV = ','.join(FEATURES) + '\n68,28.1,0,0\n72,31.4,1,0\n'


def read_batch(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('CSV tối đa 2 MB.')
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
        header = next(reader, [])
        if len(header) != len(FEATURES) or set(header) != set(FEATURES):
            raise ValueError('CSV phải có đúng 4 cột trong mẫu. Hãy kiểm tra tên, cột trùng và dấu phẩy phân cách.')
        records = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(f'Hồ sơ {len(records) + 1} có sai số lượng ô. Kiểm tra dấu phân cách.')
            if len(records) >= MAX_ROWS:
                raise ValueError('CSV tối đa 10.000 hồ sơ.')
            records.append(row)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError('Không đọc được CSV. Hãy lưu tệp dưới dạng CSV UTF-8.') from exc
    if not records:
        raise ValueError('CSV chưa có hồ sơ.')
    return pd.DataFrame(records, columns=header)[FEATURES]


def score_batch(context, raw):
    source = read_batch(raw)
    inputs = source.apply(pd.to_numeric, errors='coerce').astype(float)
    limits = context['summary']['input_ranges']
    invalid = {
        'age': ~inputs.age.between(*limits['age']),
        'bmi': ~inputs.bmi.between(*limits['bmi']),
        'smoking': ~inputs.smoking.isin([0, 1]),
        'osteoporosis_baseline': ~inputs.osteoporosis_baseline.isin([0, 1]),
    }
    issues = pd.DataFrame(invalid)
    valid = ~issues.any(axis=1)
    results = pd.DataFrame({
        'ho_so': np.arange(1, len(source) + 1),
        'trang_thai': np.where(valid, 'hop_le', 'loi_dau_vao'),
        'nhan_du_doan': pd.Series(pd.NA, index=source.index, dtype='Int64'),
        'diem_nhan_1': np.nan,
        'ly_do': ['; '.join(field for field, failed in zip(FEATURES, row) if failed)
                  for row in issues.to_numpy()],
    })
    if valid.any():
        labels, probabilities = predict_validated(context['model'], inputs.loc[valid])
        results.loc[valid, 'diem_nhan_1'] = probabilities
        results.loc[valid, 'nhan_du_doan'] = labels
    return results[RESULT_COLUMNS]
