"""Interactive MatchThem evaluation and private, optional CSV scoring."""
import hashlib
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from batch_inference import EXAMPLE_CSV, score_batch
from dashboard_core import MODEL_NAMES

MEASURES = {
    'accuracy': 'Accuracy', 'precision_class_1': 'Precision lớp 1',
    'recall_class_1': 'Recall lớp 1', 'f1_class_1': 'F1 lớp 1',
    'roc_auc': 'ROC-AUC', 'average_precision': 'Average Precision',
}


def render_batch(context):
    st.markdown('### Phân loại hàng loạt từ CSV')
    st.caption('Mỗi dòng gồm tuổi, BMI, hút thuốc và loãng xương. Hai cột cuối dùng mã 0 hoặc 1. Dùng dấu chấm cho số thập phân.')
    st.download_button('Tải CSV mẫu', EXAMPLE_CSV, 'matchthem_mau.csv', 'text/csv')
    if os.environ.get('KNEE_OA_ENABLE_BATCH') != '1':
        st.info('Để thử tệp CSV, chạy start_demo_local.ps1 trong gói dự án. Trang này đang ở chế độ minh họa công khai.')
        return
    st.caption('Dùng dữ liệu minh họa hoặc dữ liệu được phép xử lý. Tối đa 10.000 hồ sơ hoặc 2 MB.')
    uploaded = st.file_uploader('Chọn CSV có 4 cột như mẫu', type=['csv'], key='matchthem_batch')
    if uploaded is None:
        st.session_state.pop('matchthem_batch_result', None)
        return
    raw = uploaded.getvalue()
    version = (hashlib.sha256(raw).hexdigest(), context['summary']['model_sha256'])
    if st.button('Chạy phân loại CSV', type='primary'):
        st.session_state.pop('matchthem_batch_result', None)
        try:
            st.session_state['matchthem_batch_result'] = (version, score_batch(context, raw))
        except ValueError as exc:
            st.error(str(exc))
    saved = st.session_state.get('matchthem_batch_result')
    if not saved or saved[0] != version:
        return
    data = saved[1]
    total, valid, invalid = st.columns(3)
    count = int(data.nhan_du_doan.notna().sum())
    total.metric('Tổng hồ sơ', len(data))
    valid.metric('Đã phân loại', count)
    invalid.metric('Lỗi đầu vào', len(data) - count)
    st.caption('Lý do ghi các cột còn thiếu, sai mã hoặc ngoài phạm vi của mô hình.')
    st.dataframe(data.round({'diem_nhan_1': 4}), hide_index=True, width='stretch')
    st.download_button('Tải kết quả CSV', data.to_csv(index=False, float_format='%.8f').encode('utf-8-sig'),
                       'matchthem_ket_qua.csv', 'text/csv')


def read_diagnostics(base, summary):
    path = base / 'model_diagnostics.json'
    if not path.is_file():
        return None
    results = json.loads(path.read_text(encoding='utf-8'))
    if (results.get('version') == 1 and results.get('model_sha256') == summary['model_sha256']
            and results.get('report_sha256') == summary['report_sha256']):
        return results
    return None


def result_table(report):
    return pd.DataFrame([
        {'Mô hình': MODEL_NAMES[name], **{label: values['metrics'][key] for key, label in MEASURES.items()}}
        for name, values in report['test'].items()
    ])


def render_confusion(report, chart):
    options = {name: MODEL_NAMES[name] for name in report['test']}
    name = st.selectbox('Mô hình xem chi tiết', list(options), format_func=options.get, key='evaluation_model')
    normalized = st.toggle('Hiện tỷ lệ theo từng lớp thực tế', key='evaluation_normalized')
    actual = np.array(report['test'][name]['confusion_matrix'])
    tn, fp, fn, tp = actual.ravel()
    denominator = actual.sum(axis=1, keepdims=True)
    rates = np.divide(100 * actual, denominator, out=np.zeros_like(actual, dtype=float), where=denominator > 0)
    fig = go.Figure(go.Heatmap(
        z=rates if normalized else actual, x=['Dự đoán 0', 'Dự đoán 1'], y=['Thực tế 0', 'Thực tế 1'],
        text=np.char.mod('%.1f%%', rates) if normalized else actual.astype(str), texttemplate='%{text}',
        customdata=actual, colorscale='Blues', showscale=False, zmin=0,
        zmax=100 if normalized else max(1, int(actual.max())),
        hovertemplate='%{y}<br>%{x}<br>Số hồ sơ %{customdata}<extra></extra>',
    ))
    fig.update_yaxes(autorange='reversed')
    chart(fig, 'evaluation_cm', 280)
    left, right = st.columns(2)
    left.metric('Nhãn 1 dự đoán đúng', f'{tp}/{tp + fn}')
    right.metric('Nhãn 0 dự đoán thành 1', f'{fp}/{tn + fp}')


def render_curves(diagnostics, report, chart):
    reference = report['test']['LogisticRegression']['metrics']
    positive = int(diagnostics['test_class_counts']['1'])
    fraction = positive / report['test_rows']
    panels = [
        ('ROC', 'fpr', 'tpr', 'Tỷ lệ dương tính giả', 'Recall lớp 1', [0, 1], f"AUC {reference['roc_auc']:.4f}"),
        ('PR', 'recall', 'precision', 'Recall lớp 1', 'Precision lớp 1', [fraction, fraction],
         f"AP {reference['average_precision']:.4f}"),
    ]
    for col, (title, x, y, xlabel, ylabel, baseline, label) in zip(st.columns(2), panels):
        with col:
            values = diagnostics[title.lower()]
            fig = go.Figure()
            fig.add_scatter(x=[0, 1], y=baseline, mode='lines', name='Mốc tham chiếu',
                            line={'dash': 'dot', 'color': '#8b9daa'})
            fig.add_scatter(x=values[x], y=values[y], mode='lines', name=label,
                            line={'color': '#0868b5', 'shape': 'vh' if title == 'PR' else 'linear'})
            fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel,
                              xaxis_range=[0, 1], yaxis_range=[0, 1], legend={'y': -.27})
            chart(fig, 'evaluation_' + title, 330)
    st.caption(f"Precision–Recall dùng tỷ lệ nhãn 1 của tập kiểm tra làm mốc ({positive}/{report['test_rows']}).")


def render_evaluation(base, context, chart):
    st.markdown('## Hiệu năng mô hình')
    report = context['report']
    if context['report_kind'] != 'comparison':
        st.dataframe(pd.DataFrame([report.get('metrics', {})]).T, width='stretch')
        return
    diagnostics = read_diagnostics(base, context['summary'])
    st.caption(f"{report['train_rows']:,} hồ sơ train · {report['test_rows']:,} hồ sơ test · Ngưỡng báo cáo {report['decision_threshold']:g}.")
    results, curves, experiment = st.tabs(['So sánh trên test', 'ROC & Precision–Recall', 'Tối ưu trên train'])
    with results:
        table = result_table(report)
        st.dataframe(table.round(4), hide_index=True, width='stretch')
        if diagnostics:
            baseline = diagnostics['baseline']
            st.caption(f"Mốc so sánh Accuracy: {baseline['accuracy']:.1%} khi luôn đoán lớp {baseline['class']}, lớp nhiều nhất trong train.")
        render_confusion(report, chart)
        st.download_button('Tải bảng chỉ số CSV', table.to_csv(index=False, float_format='%.6f').encode('utf-8-sig'),
                           'matchthem_chi_so_test.csv', 'text/csv')
    with curves:
        if diagnostics:
            st.caption('Logistic Regression trên tập test đã tái lập từ dữ liệu MatchThem.')
            render_curves(diagnostics, report, chart)
        else:
            st.info('Bản mô hình này chưa có tệp dữ liệu để dựng đường cong.')
    with experiment:
        if diagnostics:
            study = diagnostics['study']
            variants = pd.DataFrame([
                {'Cấu hình': name, 'ROC-AUC trung bình': v['mean'], 'Độ lệch chuẩn': v['std'],
                 **{f'Fold {i}': score for i, score in enumerate(v['folds'], 1)}}
                for name, v in study['variants'].items()
            ]).sort_values('ROC-AUC trung bình', ascending=False)
            st.write(f"Cấu hình có ROC-AUC CV cao nhất trong lần thử: **{study['best_in_cv']}**.")
            st.dataframe(variants.round(4), hide_index=True, width='stretch')
            st.caption('Các cấu hình dùng chung 5 fold trên train. Chênh lệch nhỏ giữa các cấu hình chưa đủ để kết luận mô hình tốt hơn trên dữ liệu mới.')
            st.download_button('Tải kết quả tối ưu CSV', variants.to_csv(index=False, float_format='%.6f').encode('utf-8-sig'),
                               'matchthem_cv_toi_uu.csv', 'text/csv')
        else:
            st.info('Bản mô hình này chưa có kết quả thử cấu hình.')
