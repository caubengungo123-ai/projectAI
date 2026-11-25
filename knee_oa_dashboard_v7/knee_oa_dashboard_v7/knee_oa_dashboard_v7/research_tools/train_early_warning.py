"""Offline audit and research training. Does not replace the public demo model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web_deploy'))
from early_warning import PROTOCOL, TARGET, FEATURES, BINARY, audit, read_csv
import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def make_pipeline(estimator, features):
    numeric = [c for c in features if c not in BINARY]
    binary = [c for c in features if c in BINARY]
    transformers = []
    if numeric:
        transformers.append(('numeric', Pipeline([
            ('imputer', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
            ('scale', StandardScaler()),
        ]), numeric))
    if binary:
        transformers.append(('binary', SimpleImputer(strategy='most_frequent', add_indicator=True,
                                                    keep_empty_features=True), binary))
    return Pipeline([('preprocess', ColumnTransformer(transformers)), ('model', estimator)])


def research_split(df, external_cohort=None):
    groups = df['_person_group']
    if external_cohort:
        test = np.flatnonzero(df.cohort_id.eq(external_cohort))
        train = np.flatnonzero(~df.cohort_id.eq(external_cohort))
        method = 'independent cohort holdout: ' + external_cohort
    else:
        train, test = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=42).split(df, groups=groups))
        method = 'internal participant-group holdout, random_state=42'
    if not len(train) or not len(test):
        raise ValueError('Train hoặc test rỗng; kiểm tra cohort giữ riêng và số người.')
    if set(groups.iloc[train]) & set(groups.iloc[test]):
        raise ValueError('Phát hiện cùng người ở train và test.')
    y = df[TARGET]
    for name, idx in [('train', train), ('test', test)]:
        if y.iloc[idx].nunique() != 2:
            raise ValueError(name + ' không có đủ hai lớp; cần dữ liệu phù hợp, không thử seed để chọn kết quả đẹp.')
    train_df = df.iloc[train]
    if any(train_df.loc[train_df[TARGET].eq(k), '_person_group'].nunique() < 5 for k in [0, 1]):
        raise ValueError('Mỗi lớp trong train cần ít nhất 5 người độc lập để thử CV 5 fold; đây chỉ là điều kiện tính toán.')
    cv = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42).split(
        train_df, train_df[TARGET], groups=train_df['_person_group']))
    for a, b in cv:
        if set(train_df['_person_group'].iloc[a]) & set(train_df['_person_group'].iloc[b]):
            raise ValueError('CV không độc lập theo người.')
        if train_df[TARGET].iloc[a].nunique() != 2 or train_df[TARGET].iloc[b].nunique() != 2:
            raise ValueError('Một fold thiếu lớp. Cần thêm dữ liệu/điều chỉnh thiết kế trước, không dùng test để lựa chọn.')
    return train, test, cv, method


def train_research(df, manifest, output, input_sha, manifest_sha, external_cohort=None):
    train, test, cv, method = research_split(df, external_cohort)
    # Candidate features are prespecified; availability is assessed only in development train.
    features = [f for f in FEATURES if df.iloc[train][f].notna().any()]
    X_train, y_train = df.iloc[train][features], df.iloc[train][TARGET]
    candidates = {
        'LogisticRegression': make_pipeline(LogisticRegression(max_iter=2000, random_state=42), features),
        'RandomForest': make_pipeline(RandomForestClassifier(n_estimators=300, max_depth=5,
                                       min_samples_leaf=10, random_state=42, n_jobs=1), features),
    }
    scores = {}
    for name, model in candidates.items():
        values = cross_val_score(model, X_train, y_train, cv=cv, scoring='roc_auc', error_score='raise')
        scores[name] = {'mean': float(values.mean()), 'std': float(values.std()), 'folds': values.tolist()}
    selected = max(scores, key=lambda k: scores[k]['mean'])
    model = candidates[selected].fit(X_train, y_train)
    X_test, y_test = df.iloc[test][features], df.iloc[test][TARGET]
    prob = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
    pred = (prob >= .5).astype(int)
    metrics = {'accuracy': accuracy_score(y_test, pred), 'precision_class_1': precision_score(y_test, pred, zero_division=0),
               'recall_class_1': recall_score(y_test, pred, zero_division=0), 'f1_class_1': f1_score(y_test, pred, zero_division=0),
               'roc_auc': roc_auc_score(y_test, prob), 'average_precision': average_precision_score(y_test, prob),
               'brier_score': brier_score_loss(y_test, prob)}
    majority = int(y_train.mode().iloc[0])
    train_prior = float(y_train.mean())
    # Fixed bins describe calibration; they do not recalibrate the model on test.
    calibration = []
    for low, high in zip(np.arange(0, 1, .1), np.arange(.1, 1.01, .1)):
        mask = (prob >= low) & (prob < high if high < .999 else prob <= 1)
        if mask.any():
            calibration.append({'lower': float(low), 'upper': float(high), 'n': int(mask.sum()),
                                'mean_score': float(prob[mask].mean()),
                                'observed_fraction': float(y_test.to_numpy()[mask].mean())})
    report = {'protocol': PROTOCOL, 'source_sha256': input_sha, 'manifest_sha256': manifest_sha,
              'selected_model_by_training_cv': selected, 'features': features,
              'omitted_all_missing_features': [f for f in FEATURES if f not in features],
              'split_method': method, 'train_rows': len(train), 'test_rows': len(test),
              'train_participants': int(df.iloc[train]['_person_group'].nunique()),
              'test_participants': int(df.iloc[test]['_person_group'].nunique()),
              'train_class_counts': {str(k): int(v) for k,v in y_train.value_counts().items()},
              'test_class_counts': {str(k): int(v) for k,v in y_test.value_counts().items()},
              'cv_roc_auc': scores, 'test_metrics': {k: float(v) for k,v in metrics.items()},
              'test_confusion_matrix_order_0_1': confusion_matrix(y_test, pred, labels=[0,1]).tolist(),
              'majority_baseline_test_accuracy': float((y_test == majority).mean()),
              'train_prior_baseline_test_brier': float(brier_score_loss(y_test, np.full(len(y_test), train_prior))),
              'calibration_bins': calibration, 'threshold': .5,
              'limitations': ['Research only; not automatically deployed or clinically validated.',
                             'No low/medium/high clinical risk cutoffs have been established.',
                             'Outcomes and identity mappings depend on documented source review.',
                             'Complete-case outcome cohort; attrition may cause selection bias.',
                             'Metrics are knee-level; two knees are correlated. No patient-level confidence interval is claimed.',
                             'A small CV difference does not establish superiority. Test must not guide subsequent tuning.']}
    split = df[['cohort_id', 'participant_id', 'knee_side']].copy()
    split['set'] = ''
    split.iloc[train, split.columns.get_loc('set')] = 'train'
    split.iloc[test, split.columns.get_loc('set')] = 'test'
    split.to_csv(output / 'participant_split_PRIVATE.csv', index=False, encoding='utf-8-sig')
    save_json(output / 'research_metrics.json', report)
    save_json(output / 'protocol.json', PROTOCOL)
    save_json(output / 'source_manifest_PRIVATE.json', manifest)
    joblib.dump({'model': model, 'features': features, 'protocol': PROTOCOL,
                 'clinical_deployment_approved': False}, output / 'early_warning_RESEARCH_ONLY.joblib')
    return report


def main():
    parser = argparse.ArgumentParser(description='Kiểm tra dữ liệu dọc và huấn luyện nghiên cứu cảnh báo sớm.')
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('private_results/early_warning'))
    parser.add_argument('--audit-only', action='store_true')
    parser.add_argument('--external-cohort', help='Giữ toàn bộ cohort này làm test ngoài.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.exit(2, 'Thư mục kết quả đã có tệp. Dùng thư mục mới để giữ nguyên lần đánh giá trước.\n')
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
        result, eligible, row_issues = audit(read_csv(args.data), manifest)
        save_json(args.output / 'audit.json', result)
        row_issues.to_csv(args.output / 'row_issues_PRIVATE.csv', index=False, encoding='utf-8-sig')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result['global_errors'] or eligible.empty:
            parser.exit(2, 'Chưa có dữ liệu đủ điều kiện. Không huấn luyện.\n')
        if args.audit_only:
            print('Đã kiểm tra cấu trúc; chưa huấn luyện.'); return
        report = train_research(eligible, manifest, args.output, digest(args.data), digest(args.manifest), args.external_cohort)
        print('Mô hình nghiên cứu:', report['selected_model_by_training_cv'])
        print('ROC-AUC test:', round(report['test_metrics']['roc_auc'], 4))
        print('Đã lưu kết quả riêng; không thay thế mô hình trên web.')
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, 'Không thể tiếp tục: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
