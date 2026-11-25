"""Show separate aggregate views for the care survey and the clinical sample."""
import json

import plotly.graph_objects as go
import streamlit as st

from data_library import load_library


def category_chart(data, axis, key, chart):
    figure = go.Figure(go.Bar(x=data['counts'], y=data['labels'], orientation='h',
                              marker_color='#0868b5'))
    figure.update_layout(xaxis_title=axis, yaxis_autorange='reversed')
    chart(figure, key, 270)


def render_care_clinical(base, histogram, chart, heading):
    data = json.loads((base / 'care_clinical_data.json').read_text(encoding='utf-8'))
    clinical = load_library(base)['profiles']['clinical72']
    st.markdown('## Chăm sóc & lâm sàng')
    care_tab, clinical_tab = st.tabs(['Quá trình chăm sóc', 'Đặc điểm lâm sàng'])
    with care_tab:
        st.caption('Khảo sát tại Thụy Sĩ ở người đã được chẩn đoán thoái hóa khớp gối.')
        groups = data['groups']
        group = st.selectbox('Nhóm chăm sóc', list(groups), format_func=lambda key: groups[key]['label'],
                             key='care_group')
        selected = groups[group]
        people, age = st.columns(2)
        people.metric('Người trong nhóm', f"{selected['n']:,}".replace(',', '.'))
        age.metric('Tuổi trung vị', f"{selected['age']['median']:g}")
        left, right = st.columns(2)
        with left:
            heading('Phân bố tuổi', 'Số người theo nhóm tuổi', 'chart')
            distribution = selected['age']
            histogram(distribution['hist'], distribution['edges'], 'Tuổi (năm)', 'care_age', '#7da5cd')
        with right:
            heading('Tập luyện và giáo dục', 'Phân loại theo biến đã hiệu chỉnh của nguồn', 'chart')
            category_chart(selected['firstline'], 'Số người', 'care_firstline', chart)
            st.caption('Nguồn xếp toàn bộ nhóm GLA:D vào mục “Tập luyện và giáo dục” theo cấu trúc chương trình.')
        st.caption(data['care_notes'][2])
        st.link_button('Dữ liệu và codebook trên Zenodo', 'https://zenodo.org/records/22692421')

    with clinical_tab:
        people, bmi = st.columns(2)
        people.metric('Hồ sơ lâm sàng', clinical['n'])
        bmi.metric('BMI hợp lệ', f"{clinical['bmi']['valid_n']}/{clinical['n']}")
        heading('Mật độ khoáng xương', 'Nhóm theo mã BMD_CAT trong tài liệu nguồn', 'chart')
        category_chart(data['bone_density'], 'Số hồ sơ', 'clinical_bmd', chart)
        left, right = st.columns(2)
        for column, field, title in [(left, 'vas', 'VAS'), (right, 'womac', 'WOMAC')]:
            with column:
                stats = clinical['extra_numeric'][field]
                heading(title, f"Trung vị {stats['median']:g} điểm · {stats['valid_n']} hồ sơ", 'chart')
                histogram(stats['hist'], stats['edges'], f'{title} (điểm)', f'clinical_{field}', '#7da5cd')
        st.caption('Một BMI bằng 0 được loại khỏi thống kê BMI. RAD SCORE có giá trị thập phân và được giữ theo mã nguồn.')
