"""Single-record demo and independent symptom information."""
from datetime import datetime, timezone
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from classification_ui import render_batch
from dashboard_core import FEATURES, RED_FLAGS, assess, care_direction


def load_example():
    st.session_state.update(demo_age=68, demo_bmi=28.1, demo_smoke='Không', demo_bone='Không',
                            demo_bmi_mode='Nhập BMI trực tiếp')
    st.session_state.pop('demo_result', None)


def render_single(context, chart):
    summary = context['summary']
    ranges = summary['input_ranges']
    st.button('Điền hồ sơ mẫu', on_click=load_example)
    mode = st.radio('Cách nhập BMI', ['Nhập BMI trực tiếp', 'Tính từ chiều cao và cân nặng'],
                    horizontal=True, key='demo_bmi_mode')
    left, right = st.columns([1, 1.1], gap='large')
    with left:
        with st.form('matchthem_single'):
            age = st.number_input('Tuổi (năm)', min_value=18, max_value=100, step=1, value=None,
                                  key='demo_age', help=f"Khoảng trong tập tham chiếu {ranges['age'][0]:g}–{ranges['age'][1]:g}.")
            if mode == 'Nhập BMI trực tiếp':
                bmi = st.number_input('BMI (kg/m²)', min_value=10., max_value=70., step=.1, value=None,
                                      key='demo_bmi', help=f"Khoảng trong tập tham chiếu {ranges['bmi'][0]:g}–{ranges['bmi'][1]:g}.")
            else:
                height = st.number_input('Chiều cao (cm)', min_value=100., max_value=230.,
                                         step=.5, value=None, key='demo_height')
                weight = st.number_input('Cân nặng (kg)', min_value=20., max_value=250.,
                                         step=.1, value=None, key='demo_weight')
                bmi = weight / (height / 100) ** 2 if height is not None and weight is not None else None
            binary_choices = {'Chưa chọn': None, 'Không': 0, 'Có': 1}
            smoking = st.selectbox('Tình trạng hút thuốc', binary_choices, key='demo_smoke')
            bone = st.selectbox('Loãng xương đã xác định', binary_choices, key='demo_bone')
            submitted = st.form_submit_button('Chạy phân loại', type='primary', width='stretch')
        if submitted:
            inputs = {'age': age, 'bmi': bmi, 'smoking': binary_choices[smoking],
                      'osteoporosis_baseline': binary_choices[bone]}
            result = assess(context, inputs)
            st.session_state['demo_result'] = {
                key: result[key] for key in ('inputs', 'prediction', 'issues', 'model_name', 'model_sha256', 'scope')
            }
            st.session_state['demo_result']['time_utc'] = datetime.now(timezone.utc).isoformat()
    with right:
        result = st.session_state.get('demo_result')
        if not result or result['model_sha256'] != summary['model_sha256']:
            st.info('Điền bốn đặc trưng hoặc chọn hồ sơ mẫu để chạy phân loại.')
            return
        prediction = result['prediction']
        if prediction is None:
            for issue in result['issues']:
                st.warning(issue)
            return
        label = prediction['label']
        score = prediction['score']
        a, b = st.columns(2)
        a.metric('Nhãn dự đoán', label)
        b.metric('Điểm lớp 1', f'{score:.3f}')
        st.write(f"Nhãn {label} tương ứng với **{'diagnosed' if label == 1 else 'at risk'}** theo MatchThem.")
        if summary.get('score_reference'):
            show_score(summary['score_reference'], score, chart)
        st.caption('Kết quả trên bộ dữ liệu thực hành. Điểm lớp 1 chưa được hiệu chỉnh thành xác suất lâm sàng.')
        with st.expander('Xem đầu vào đã gửi'):
            st.json(result['inputs'])
        st.download_button('Tải kết quả JSON', json.dumps(result, ensure_ascii=False, indent=2),
                           'matchthem_ket_qua_mot_ho_so.json', 'application/json')
        return result


def render_single_csv(result):
    st.markdown('### Xuất hồ sơ vừa phân loại')
    if result is None:
        st.caption('Nhập thông tin hợp lệ và bấm Chạy phân loại trong tab Một hồ sơ.')
        return
    prediction = result['prediction']
    row = {field: result['inputs'][field] for field in FEATURES}
    row.update(nhan_du_doan=prediction['label'], diem_nhan_1=prediction['score'])
    data = pd.DataFrame([row])
    st.dataframe(data, hide_index=True, width='stretch')
    st.download_button('Tải CSV hồ sơ vừa nhập', data.to_csv(index=False).encode('utf-8-sig'),
                       'matchthem_ho_so_da_nhap.csv', 'text/csv', on_click='ignore')


def show_score(reference, score, chart):
    edges = np.array(reference['edges'])
    figure = go.Figure(go.Bar(x=(edges[:-1] + edges[1:]) / 2, y=reference['hist'],
                              width=np.diff(edges) * .9, marker_color='#aec9d5'))
    figure.add_vline(x=score, line_color='#b37422', line_width=3)
    figure.update_layout(xaxis_title='Điểm lớp 1', yaxis_title='Số hồ sơ train', xaxis_range=[0, 1])
    chart(figure, 'personal_score', 260)
    st.caption('Vạch vàng biểu thị điểm của hồ sơ đã gửi. Các cột biểu thị phân bố điểm trong tập train.')


def render_symptoms():
    st.caption('Hướng dẫn tham khảo dựa trên thông tin bạn tự khai.')
    with st.form('symptom_info'):
        flags = st.multiselect('Dấu hiệu hiện có', RED_FLAGS)
        checked = st.checkbox('Tôi đã kiểm tra danh sách dấu hiệu.')
        prolonged = st.selectbox('Đau gối không cải thiện sau vài tuần?', ['Chưa trả lời', 'Không', 'Có'])
        look_up = st.form_submit_button('Xem hướng dẫn')
    if look_up:
        st.session_state['symptom_guidance'] = care_direction(
            flags, checked, None if prolonged == 'Chưa trả lời' else prolonged == 'Có',
        )
    care = st.session_state.get('symptom_guidance')
    if care:
        display = {'urgent': st.error, 'appointment': st.warning, 'selfcare': st.info, 'unknown': st.info}[care['level']]
        display(f"**{care['title']}**\n\n{care['message']}")
        st.link_button('Thông tin về đau gối của NHS', care['source'])


def render_demo(context, chart):
    st.markdown('## Thử mô hình phân loại MatchThem')
    single, batch, symptoms = st.tabs(['Một hồ sơ', 'Từ tệp CSV', 'Thông tin triệu chứng'])
    with single:
        result = render_single(context, chart)
    with batch:
        render_single_csv(result)
        st.divider()
        render_batch(context)
    with symptoms:
        render_symptoms()
