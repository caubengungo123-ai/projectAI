"""KneeScope research dashboard with a card-based, responsive interface."""
from html import escape
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_library import load_library, render_data_library
from care_clinical import render_care_clinical
from early_warning_ui import render_early_warning
from classification_ui import render_evaluation
from dashboard_core import MODEL_NAMES, LABEL_NAMES, SOURCES, load_context
from demo_ui import render_demo

BASE=Path(__file__).resolve().parent
COLORS=['#7da5cd','#0868b5','#cad4df']
PAGES={
    'Tổng quan': '⌂', 'Thử mô hình': '♧', 'Hiệu năng mô hình': '▥',
    'Kho dữ liệu': '▦', 'Chăm sóc & lâm sàng': '✚', 'Phương pháp & nguồn': '▤',
    'Hướng phát triển': '◷',
}
SITE_NAME = 'KneeScope'
PAGE_TITLE = 'Phân loại tình trạng thoái hóa khớp gối'

st.set_page_config(page_title=f'{SITE_NAME} · {PAGE_TITLE}', page_icon='🦵',
                   layout='wide', initial_sidebar_state='auto')
st.markdown((BASE/'dashboard_style.css').read_text(encoding='utf-8'),unsafe_allow_html=True)


def icon(name, size=22):
    paths={
        'pulse':'<path d="M3 12h4l3-7 4 14 3-7h4"/>',
        'chart':'<path d="M4 4v16h16M8 15l4-5 4 3 5-8"/>',
        'data':'<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M4 10h16M10 10v10"/>',
        'user':'<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
        'check':'<path d="m5 12 4 4L19 6"/>',
        'arrow':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
        'shield':'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"/><path d="m8 12 3 3 5-6"/>',
        'book':'<path d="M12 5v16M3 4h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v15h-5a4 4 0 0 0-4 2 4 4 0 0 0-4-2H3z"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths.get(name,paths["data"])}</svg>'


def navigate(page):
    st.session_state['navigation'] = page


@st.cache_resource(show_spinner='Đang đọc dữ liệu và mô hình…')
def cached_context(base,signature):
    return load_context(base)


def chart(fig,key,height=300):
    fig.update_layout(height=height,margin=dict(t=20,b=45,l=30,r=15),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Arial, sans-serif',color='#587086',size=12),legend=dict(orientation='h',y=-.22,x=0),
                      hoverlabel=dict(bgcolor='white',font_color='#24394d'))
    fig.update_xaxes(showgrid=False,automargin=True)
    fig.update_yaxes(gridcolor='#edf1f4',zeroline=False,automargin=True)
    st.plotly_chart(fig,width='stretch',theme=None,key=key,config={'displayModeBar':False,'responsive':True})


def histogram(counts,edges,xlabel,key,color):
    e=np.array(edges)
    fig=go.Figure(go.Bar(x=(e[:-1]+e[1:])/2,y=counts,width=np.diff(e)*.72,marker_color=color,marker_cornerradius=5,
                         customdata=list(zip(e[:-1],e[1:])),
                         hovertemplate='Khoảng %{customdata[0]:g}–%{customdata[1]:g}<br>Số hồ sơ: %{y}<extra></extra>'))
    fig.update_layout(xaxis_title=xlabel,yaxis_title='Số hồ sơ')
    chart(fig,key)


def panel_heading(title,subtitle='',symbol='chart'):
    st.markdown(f'<div class="panel-heading"><span class="icon-box">{icon(symbol)}</span><div><h3>{escape(title)}</h3><p>{escape(subtitle)}</p></div></div>',unsafe_allow_html=True)


try:
    paths=list(BASE.glob('*.csv'))+list(BASE.glob('dashboard_data.json'))+list((BASE/'results').rglob('*.json'))+list((BASE/'results').rglob('*.joblib'))+list((BASE/'results').rglob('split.csv'))
    sig=tuple(sorted((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths))
    ctx=cached_context(str(BASE),sig)
except Exception as exc:
    st.error(f'Chưa thể mở dashboard: {exc}')
    st.caption('Cần có mô hình trong results và CSV hoặc dashboard_data.json phù hợp.')
    st.stop()
s=ctx['summary']; report=ctx['report']
with st.sidebar:
    st.markdown(f'<div class="side-brand"><span class="brand-mark">{icon("pulse",26)}</span><div>{SITE_NAME}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="side-label">KHÔNG GIAN NGHIÊN CỨU</div>',unsafe_allow_html=True)
    page=st.radio('Điều hướng',list(PAGES),key='navigation',label_visibility='collapsed',
                  format_func=lambda v:f'{PAGES[v]}  {v}')
    st.markdown(f'<div class="side-model"><span class="icon-box">{icon("shield")}</span><strong>Mô hình minh họa hiện tại</strong><p>{MODEL_NAMES[ctx["model_name"]]}</p><small>MatchThem · phân loại nhãn 0/1.</small></div>',unsafe_allow_html=True)
    st.markdown('<div class="side-label">PHẠM VI CỦA MÔ HÌNH</div>',unsafe_allow_html=True)
    for key,label in [('age','Tuổi'),('bmi','BMI')]:
        st.caption(f"{label}: {s['input_ranges'][key][0]:g}–{s['input_ranges'][key][1]:g}")
    st.caption('Dữ liệu dẫn xuất MatchThem. Chỉ phục vụ học tập và nghiên cứu.')

st.markdown(f'<div class="topbar"><div><strong>{SITE_NAME}</strong><i>/</i>{escape(page)}</div></div>',
            unsafe_allow_html=True)

if page == 'Hướng phát triển':
    render_early_warning()

if page=='Tổng quan':
    catalog = load_library(BASE)
    with st.container(key='welcome'):
        left, right = st.columns([1.4, 1], gap='large', vertical_alignment='center')
        with left:
            st.markdown(f'<h1>{PAGE_TITLE}</h1><p class="hero-copy">'
                        'Thử mô hình Logistic Regression trên dữ liệu MatchThem và khám phá dữ liệu từ bốn nguồn.</p>',
                        unsafe_allow_html=True)
            st.caption('Kết quả phục vụ học tập và nghiên cứu.')
        with right, st.container(key='welcome_action'):
            st.button('Thử mô hình', type='primary', on_click=navigate, args=('Thử mô hình',),
                      key='hero_assess', width='stretch')
            st.button('Xem hiệu năng', on_click=navigate, args=('Hiệu năng mô hình',),
                      key='hero_eval', width='stretch')
    sources, all_rows, test_rows = st.columns(3)
    sources.metric('Nguồn dữ liệu', catalog['counts']['downloaded_sources'])
    all_rows.metric('Dòng trong kho', f"{catalog['counts']['source_rows_total']:,}".replace(',', '.'))
    test_rows.metric('Hồ sơ test MatchThem', report.get('test_rows', report.get('split', {}).get('test_rows', 0)))

    title_col,source_col=st.columns([1.2,1],vertical_alignment='bottom')
    with title_col:
        st.markdown('<div class="section-kicker">BỨC TRANH TỔNG THỂ</div><h2>Dữ liệu MatchThem</h2>',unsafe_allow_html=True)
    with source_col:
        keys=['all','labeled'] if 'all' in s['datasets'] else ['labeled']
        selected=st.selectbox('Tập MatchThem hiển thị',keys,format_func=lambda k:s['datasets'][k]['title'],key='overview_source')
    d=s['datasets'][selected]
    labeled=sum(d['label_counts'][:2]);coverage=100*labeled/d['n']
    cols=st.columns(4)
    for col,label,value in zip(cols,['Tổng hồ sơ','Hồ sơ có nhãn','Tuổi trung vị','BMI trung vị'],
                               [f"{d['n']:,}",f"{labeled:,}",f"{d['age_median']:.0f} tuổi",f"{d['bmi_median']:.1f}"]):
        col.metric(label,value)
    left,right=st.columns([1,1.12],gap='medium')
    with left:
        with st.container(border=True,key='data_status'):
            panel_heading('Độ đầy đủ của nhãn','Tỷ lệ hồ sơ có nhãn kết cục trong bảng đang chọn','data')
            ring=f'<div class="ring" style="--coverage:{coverage:.3f}%"><div><strong>{coverage:.1f}%</strong><small>Có nhãn</small></div></div>'
            st.markdown(f'<div class="coverage-row">{ring}<div><h3>{labeled:,} / {d["n"]:,} hồ sơ</h3><p>Đã có nhãn kết cục</p><span class="subtle-pill">{d["label_counts"][2]:,} hồ sơ chưa có nhãn</span></div></div>',unsafe_allow_html=True)
            st.markdown(f'<div class="data-tiles"><div><span class="tile-dot blue"></span><small>Nhãn 0 · at risk</small><strong>{d["label_counts"][0]:,}</strong></div><div><span class="tile-dot navy"></span><small>Nhãn 1 · diagnosed</small><strong>{d["label_counts"][1]:,}</strong></div><div><span class="tile-dot gray"></span><small>Chưa có nhãn</small><strong>{d["label_counts"][2]:,}</strong></div></div>',unsafe_allow_html=True)
            st.caption('Mức đầy đủ của dữ liệu, không phải chỉ số sức khỏe. Nhãn 0 không đồng nghĩa hoàn toàn khỏe mạnh.')
    with right:
        with st.container(border=True,key='model_snapshot'):
            panel_heading('Hồ sơ hiệu năng mô hình','So sánh trên cùng cách chia train / test','chart')
            if ctx['report_kind']=='comparison':
                rows=''
                for name,result in report['test'].items():
                    selected_model=name==ctx['model_name']
                    tag='<span class="selected-tag">Đang dùng</span>' if selected_model else ''
                    rows+=f'<tr><td><strong>{MODEL_NAMES[name]}</strong>{tag}</td><td>{report["cv"][name]["roc_auc"]["mean"]:.4f}</td><td>{result["metrics"]["roc_auc"]:.4f}</td><td>{100*result["metrics"]["accuracy"]:.1f}%</td></tr>'
                st.markdown(f'<div class="table-wrap"><table class="model-table"><thead><tr><th>MÔ HÌNH</th><th>CV AUC</th><th>TEST AUC</th><th>ACCURACY</th></tr></thead><tbody>{rows}</tbody></table></div>',unsafe_allow_html=True)
                st.caption('Lựa chọn dựa trên CV trong tập train. Chênh lệch nhỏ chưa chứng minh mô hình vượt trội.')
            else:
                st.write(MODEL_NAMES[ctx['model_name']]);st.caption('Báo cáo mô hình cơ sở.')
        with st.container(border=True,key='train_split'):
            panel_heading('Thiết kế đánh giá','Giữ nguyên tập kiểm tra để báo cáo kết quả','shield')
            ntrain=report.get('train_rows',report.get('split',{}).get('train_rows',0))
            ntest=report.get('test_rows',report.get('split',{}).get('test_rows',0))
            train_pct=100*ntrain/(ntrain+ntest) if ntrain+ntest else 0
            st.markdown(f'<div class="split-numbers"><strong>{ntrain:,}<small>Train · 5 fold CV</small></strong><strong>{ntest:,}<small>Test · đánh giá cuối</small></strong></div><div class="split-bar"><span style="width:{train_pct:.3f}%"></span></div><div class="split-legend"><span>● Tập huấn luyện</span><span>● Tập kiểm tra</span></div>',unsafe_allow_html=True)
    st.markdown('<h2>Phân bố và độ đầy đủ của dữ liệu</h2>',unsafe_allow_html=True)
    distribution,demographic,quality=st.tabs(['Phân bố nhãn','Tuổi & BMI','Chất lượng dữ liệu'])
    with distribution:
        a,b=st.columns(2,gap='medium')
        with a:
            with st.container(border=True):
                panel_heading('Phân bố nhãn dữ liệu','Số hồ sơ theo từng nhóm nhãn','data')
                fig=go.Figure(go.Bar(x=LABEL_NAMES,y=d['label_counts'],marker_color=COLORS,marker_cornerradius=7,text=d['label_counts'],textposition='outside'))
                fig.update_layout(yaxis_title='Số hồ sơ');chart(fig,'labels')
        with b:
            with st.container(border=True):
                panel_heading('Tỷ lệ nhãn 1 theo tuổi','Trong số hồ sơ có nhãn của từng nhóm tuổi','chart')
                g=d['age_groups'];rates=[100*v['label_1_n']/v['labeled_n'] if v['labeled_n'] else None for v in g]
                fig=go.Figure(go.Bar(x=[v['group'] for v in g],y=rates,marker_color=COLORS[1],marker_cornerradius=7,
                    customdata=[[v['label_1_n'],v['labeled_n']] for v in g],hovertemplate='Tuổi %{x}<br>Nhãn 1: %{customdata[0]}/%{customdata[1]}<br>Tỷ lệ %{y:.1f}%<extra></extra>'))
                fig.update_layout(yaxis_title='Tỷ lệ nhãn 1 (%)',yaxis_range=[0,100],xaxis_title='Nhóm tuổi (năm)');chart(fig,'age_rate')
        st.caption('Dữ liệu dẫn xuất không đại diện tỷ lệ mắc bệnh của dân số. Các liên hệ trong biểu đồ không chứng minh nhân quả.')
    with demographic:
        a,b=st.columns(2,gap='medium')
        with a:
            with st.container(border=True):
                panel_heading('Phân bố tuổi','Độ tuổi của các hồ sơ trong bảng','user')
                histogram(d['age_hist'],d['age_edges'],'Tuổi (năm)','ages',COLORS[0])
        with b:
            with st.container(border=True):
                panel_heading('Phân bố BMI','BMI = cân nặng (kg) / chiều cao (m)²','chart')
                histogram(d['bmi_hist'],d['bmi_edges'],'BMI (kg/m²)','bmis',COLORS[1])
                st.caption(f"Hồ sơ có BMI: {d['n']-d['missing'].get('bmi',0):,}.")
        with st.container(border=True):
            panel_heading('Phân bố đồng thời tuổi và BMI','Màu thể hiện số hồ sơ, không thể hiện mức nguy hiểm','chart')
            al=[f'{int(x)}–{int(y)-1}' for x,y in zip(d['age_edges'][:-1],d['age_edges'][1:])]
            bl=[f'{x:g}–<{y:g}' for x,y in zip(d['bmi_edges'][:-1],d['bmi_edges'][1:])]
            fig=go.Figure(go.Heatmap(z=np.array(d['heatmap']).T,x=al,y=bl,colorscale=[[0,'#f1f6fb'],[1,'#0967b2']],colorbar=dict(title='Số hồ sơ'),
                hovertemplate='Tuổi %{x}<br>BMI %{y}<br>Số hồ sơ: %{z}<extra></extra>'))
            fig.update_layout(xaxis_title='Nhóm tuổi (năm)',yaxis_title='Khoảng BMI (kg/m²)');chart(fig,'age_bmi')
            st.caption(f"Có {d['paired_n']:,} hồ sơ đủ cả hai biến.")
    with quality:
        with st.container(border=True):
            panel_heading('Dữ liệu thiếu','Các ô thiếu được loại khỏi thống kê số tương ứng','data')
            missing={k:v for k,v in d['missing'].items() if v}
            if missing:
                field_names={'bmi':'BMI','race_code':'Mã chủng tộc','smoking':'Hút thuốc','koa_followup':'Nhãn kết cục','sex_code_unverified':'Mã giới tính'}
                fig=go.Figure(go.Bar(x=list(missing.values()),y=[field_names.get(k,k) for k in missing],orientation='h',marker_color=COLORS[0],marker_cornerradius=5,text=list(missing.values()),textposition='outside'))
                fig.update_layout(xaxis_title='Số ô thiếu');chart(fig,'missing')
            else:st.info('Bảng đang chọn không có ô thiếu.')

if page=='Kho dữ liệu':
    render_data_library(BASE,chart,panel_heading)

if page=='Chăm sóc & lâm sàng':
    render_care_clinical(BASE, histogram, chart, panel_heading)

if page == 'Thử mô hình':
    render_demo(ctx, chart)

if page == 'Hiệu năng mô hình':
    render_evaluation(BASE, ctx, chart)

if page=='Phương pháp & nguồn':
    st.markdown('<div class="section-kicker">MINH BẠCH NGHIÊN CỨU</div><h2>Phương pháp & nguồn</h2>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        ['Biểu đồ dữ liệu','Thống kê từ CSV','Không phải tỷ lệ mắc bệnh của dân số'],
        ['Điểm lớp 1','Điểm đầu ra Logistic Regression','Chưa hiệu chỉnh thành xác suất lâm sàng'],
        ['Hướng dẫn đi khám','Triệu chứng tự khai và tài liệu NHS','Độc lập với mô hình ML; không thay thế khám'],
    ],columns=['Thành phần','Căn cứ','Giới hạn']),hide_index=True,width='stretch')
    st.markdown('''
**Bài toán:** phân loại nhị phân `koa_followup` từ tuổi, BMI, hút thuốc và loãng xương ban đầu. Nhãn nguồn 0 = “at risk”, 1 = “diagnosed” tại lần theo dõi; chưa xác minh thời hạn kết cục.

**Loãng xương và thoái hóa khớp gối là hai tình trạng khác nhau.** Loãng xương hiện là đầu vào đã biết. Muốn dự đoán loãng xương cần dữ liệu, nhãn và đánh giá riêng; đánh giá y tế có thể bao gồm đo mật độ xương DXA.

**Giới hạn:** bộ MatchThem là dẫn xuất OAI có chỉnh sửa. Mã giới tính không khớp tài liệu nên chưa dùng. Chưa có ID OAI được xác minh để bảo đảm chia tập độc lập theo người. Điểm trên bộ này không đại diện nguy cơ bệnh trong cộng đồng.

**Phương pháp:** chia train/test trước; điền thiếu và chuẩn hóa trong pipeline. Chọn mô hình bằng ROC-AUC trung bình trên các fold huấn luyện. Trang Hiệu năng hiển thị tập test của bản công bố và một lần thử cấu hình bổ sung trên train.
''')
    st.markdown('**Tài liệu tham khảo**')
    for title,url in SOURCES.items():st.markdown(f'- [{title}]({url})')
    st.caption('Nguồn y khoa kiểm tra ngày 27/10/2026. Thông tin giáo dục, không phải phác đồ điều trị cá nhân.')
st.markdown(f'<div class="foot">{SITE_NAME} · Đồ án học máy và phân tích dữ liệu</div>', unsafe_allow_html=True)
