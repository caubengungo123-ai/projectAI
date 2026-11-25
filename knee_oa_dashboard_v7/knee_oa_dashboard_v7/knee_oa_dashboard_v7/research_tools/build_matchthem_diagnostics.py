"""Rebuild aggregate diagnostics and compare preset variants on training CV."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (average_precision_score, confusion_matrix, precision_recall_curve,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'web_deploy'))
from dashboard_core import FEATURES, load_context, sha


def build(root):
    source = root / 'research_data/matchthem_research.csv'
    context = load_context(root / 'web_deploy')
    reference = context['report']['test']['LogisticRegression']
    frame = pd.read_csv(source).rename(columns={'smk': 'smoking', 'osp': 'osteoporosis_baseline'})
    labeled = frame.loc[frame.koa.notna()]
    X_train, X_test, y_train, y_test = train_test_split(
        labeled[FEATURES], labeled.koa.astype(int), test_size=.2, random_state=42, stratify=labeled.koa,
    )
    model = context['model']
    class_index = list(model.classes_).index(1)
    scores = model.predict_proba(X_test)[:, class_index]
    predicted = model.predict(X_test)
    expected = reference['metrics']
    train_scores = model.predict_proba(X_train)[:, class_index]
    summary = context['summary']
    if (
        (len(X_train), len(X_test)) != (context['report']['train_rows'], context['report']['test_rows'])
        or not np.array_equal(confusion_matrix(y_test, predicted), reference['confusion_matrix'])
        or not np.isclose(roc_auc_score(y_test, scores), expected['roc_auc'], rtol=0, atol=1e-12)
        or not np.isclose(average_precision_score(y_test, scores), expected['average_precision'], rtol=0, atol=1e-12)
        or not np.allclose(np.quantile(train_scores, [1/3, 2/3]), summary['score_reference']['tertiles'],
                           rtol=0, atol=1e-12)
    ):
        raise ValueError('Tập tái lập không khớp báo cáo công bố của mô hình.')

    majority = int(y_train.value_counts().idxmax())
    fpr, tpr, _ = roc_curve(y_test, scores)
    precision, recall, _ = precision_recall_curve(y_test, scores, drop_intermediate=True)

    spline = clone(model)
    numeric = make_pipeline(
        clone(model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['imputer']),
        SplineTransformer(n_knots=4, degree=2, include_bias=False),
    )
    spline.set_params(preprocess__numeric=numeric)
    candidates = {
        'Logistic gốc (C=1)': clone(model),
        'Logistic (C=0,1)': clone(model).set_params(classifier__C=.1),
        'Logistic (C=10)': clone(model).set_params(classifier__C=10),
        'Logistic spline tuổi/BMI': spline,
        'Histogram Gradient Boosting': clone(model).set_params(
            classifier=HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=7,
                                                     l2_regularization=1, random_state=42)),
    }
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X_train, y_train))
    variants = {}
    with threadpool_limits(limits=1):
        for name, candidate in candidates.items():
            values = cross_val_score(candidate, X_train, y_train, cv=folds,
                                     scoring='roc_auc', error_score='raise')
            variants[name] = {'mean': float(values.mean()), 'std': float(values.std()),
                              'folds': values.tolist()}
    return {
        'version': 1,
        'model_sha256': summary['model_sha256'],
        'report_sha256': summary['report_sha256'],
        'research_csv_sha256': sha(source),
        'baseline': {'class': majority, 'accuracy': float(y_test.eq(majority).mean())},
        'test_class_counts': {str(c): int(y_test.eq(c).sum()) for c in (0, 1)},
        'roc': {'fpr': fpr.tolist(), 'tpr': tpr.tolist()},
        'pr': {'recall': recall[::-1].tolist(), 'precision': precision[::-1].tolist()},
        'study': {'seed': 42, 'n_splits': len(folds), 'train_rows': len(X_train),
                  'baseline': next(iter(variants)),
                  'best_in_cv': max(variants, key=lambda name: variants[name]['mean']),
                  'variants': variants},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    data = json.dumps(build(ROOT), ensure_ascii=False, indent=2, allow_nan=False)
    with args.output.open('x', encoding='utf-8') as target:
        target.write(data + '\n')
