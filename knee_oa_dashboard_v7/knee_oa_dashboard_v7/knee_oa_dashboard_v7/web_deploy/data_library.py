"""Explore source-specific aggregate data without publishing patient rows."""
from pathlib import Path
import json
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def load_library(base):
    data=json.loads((Path(base)/'multisource_data.json').read_text(encoding='utf-8'))
    if data.get('schema_version')!=1:
        raise ValueError('Phiên bản kho dữ liệu chưa được hỗ trợ.')
    for sid,p in data['profiles'].items():
        for field in ['age','bmi']:
            v=p[field]
            if sum(v['hist'])!=v['valid_n'] or v['valid_n']+v['missing_n']!=p['n']:
                raise ValueError(f'Thống kê {sid}/{field} không khớp số dòng.')
    return data


def render_data_library(base, chart, heading):
    st.markdown('<div class="section-kicker">NGUỒN VÀ CHẤT LƯỢNG</div><h2>Kho dữ liệu đa nguồn</h2>',unsafe_allow_html=True)
    try:data=load_library(base)
    except Exception as e:
        st.error(f'Chưa mở được kho dữ liệu: {e}');return
    counts=data['counts'];profiles=data['profiles']
    a,b,c=st.columns(3)
    a.metric('Bộ dữ liệu đã có',counts['downloaded_sources'])
    b.metric('Dòng trong kho',f"{counts['source_rows_total']:,}".replace(',', '.'))
    c.metric('Hồ sơ có nhãn dùng cho ML',f"{profiles['matchthem']['source_outcome']['valid_n']:,}".replace(',', '.'))
    st.info(data['training_note'])
    st.caption('Ngày kiểm tra nguồn: '+data['checked_date']+'. '+data['count_note'])
    catalog,explore,quality,expansion=st.tabs(['Danh mục nguồn','Khám phá từng nguồn','Chất lượng dữ liệu','Bổ sung nguồn mới'])
    with catalog:
        registry=pd.DataFrame([{'Nguồn':r['title'],'Trạng thái':r['status'],'Số dòng đã có':f"{r['rows']:,}" if r['rows'] is not None else 'Chưa tải',
                    'Mục đích':r['purpose'],'Trang nguồn':r['url']} for r in data['registry']])
        st.dataframe(registry,hide_index=True,width='stretch',column_config={
            'Trang nguồn':st.column_config.LinkColumn('Trang nguồn',display_text='Mở nguồn'),
            'Số dòng đã có':st.column_config.TextColumn()})
        with st.container(border=True):
            heading('Tuổi và BMI theo nguồn','Thống kê theo bộ dữ liệu; mẫu nhỏ và cách chọn mẫu có thể khác nhau','data')
            selected = st.multiselect('Nguồn cần so sánh', list(profiles), default=list(profiles),
                                      format_func=lambda sid: profiles[sid]['name'], key='comparison_sources')
            summary=[]
            for sid in selected:
                p = profiles[sid]
                summary.append({'Nguồn':p['name'],'Số dòng':p['n'],'Tuổi trung vị':p['age']['median'],
                                'Tuổi nhỏ nhất':p['age']['min'],'Tuổi lớn nhất':p['age']['max'],
                                'BMI trung vị hợp lệ':p['bmi']['median'],'Dòng có BMI hợp lệ':p['bmi']['valid_n'],
                                'Tỷ lệ có BMI (%)':100*p['bmi']['valid_n']/p['n']})
            if summary:
                comparison = pd.DataFrame(summary).round(2)
                st.dataframe(comparison, hide_index=True, width='stretch')
                st.download_button('Tải bảng so sánh nguồn CSV',
                                   comparison.to_csv(index=False).encode('utf-8-sig'),
                                   'knee_oa_so_sanh_nguon.csv', 'text/csv')
            else:
                st.info('Chọn ít nhất một nguồn để xem bảng.')
        st.caption('Số dòng là theo từng nguồn, không phải số người duy nhất đã được xác minh giữa các nguồn. Phạm vi người dùng mà mô hình hỗ trợ vẫn theo tập train cũ.')
        for r in data['registry']:
            with st.expander(r['title']):
                st.write(r['merge_decision'])
                st.caption('Giấy phép / điều kiện: '+r['license'])
                st.caption('Trích dẫn: '+r['citation'])
                if r.get('original_sha256'):
                    st.caption('Phiên bản nguồn: '+str(r['version'])+' · File gốc: '+r['original_file'])
    with explore:
        sid=st.selectbox('Chọn nguồn để khám phá',list(profiles),format_func=lambda k:profiles[k]['name'],key='library_source')
        p=profiles[sid]
        a,b,c=st.columns(3)
        a.metric('Số hồ sơ trong nguồn',p['n'])
        b.metric('Tuổi trung vị',f"{p['age']['median']:g}" if p['age']['valid_n'] else '—')
        c.metric('BMI trung vị hợp lệ',f"{p['bmi']['median']:.2f}" if p['bmi']['valid_n'] else '—')
        a,b=st.columns(2)
        for col,field,label,color in [(a,'age','Tuổi (năm)','#7da5cd'),(b,'bmi','BMI (kg/m²)','#0868b5')]:
            with col:
                with st.container(border=True):
                    heading('Phân bố '+('tuổi' if field=='age' else 'BMI'),'Chỉ tính giá trị hợp lệ của nguồn đang chọn','chart')
                    v=p[field];edges=np.array(v['edges'])
                    if not v['valid_n']:
                        st.caption(f"Nguồn có {p['n']} dòng và không có giá trị {label} để hiển thị.")
                        continue
                    fig=go.Figure(go.Bar(x=(edges[:-1]+edges[1:])/2,y=v['hist'],width=np.diff(edges)*.8,
                                        marker_color=color,marker_cornerradius=5,
                                        hovertemplate='%{x:g}<br>Số dòng: %{y}<extra></extra>'))
                    fig.update_layout(xaxis_title=label,yaxis_title='Số dòng')
                    chart(fig,'lib_'+sid+'_'+field,290)
                    st.caption(f"Có {v['valid_n']} giá trị hợp lệ; {v['missing_n']} thiếu hoặc không dùng trong biểu đồ.")
        with st.container(border=True):
            heading('Nhãn hoặc điểm được ghi trong nguồn',p['outcome_title'],'data')
            v=p['source_outcome']
            fig=go.Figure(go.Bar(x=v['labels'],y=v['counts'],text=v['counts'],textposition='outside',marker_color='#0868b5',marker_cornerradius=5))
            fig.update_layout(xaxis_title=p['outcome_title'],yaxis_title='Số dòng',xaxis_type='category')
            chart(fig,'lib_'+sid+'_outcome',280)
            st.caption(f"Có {v['valid_n']} giá trị và {v['missing_n']} ô thiếu. Không quy đổi các nhãn/điểm khác nghĩa thành cùng một kết cục.")
        if p.get('extra_numeric'):
            key=st.selectbox('Thang đo bổ sung trong nguồn',list(p['extra_numeric']),key='library_score_'+sid)
            v=p['extra_numeric'][key];edges=np.array(v['edges'])
            fig=go.Figure(go.Bar(x=(edges[:-1]+edges[1:])/2,y=v['hist'],marker_color='#7da5cd',marker_cornerradius=5))
            fig.update_layout(xaxis_title=key+' · đơn vị điểm nguồn',yaxis_title='Số dòng')
            chart(fig,'lib_'+sid+'_extra',260)
            st.caption('Thống kê mô tả giá trị nguồn, không phải khuyến nghị điều trị hoặc điểm nguy cơ cá nhân.')
    with quality:
        for sid,p in profiles.items():
            with st.container(border=True):
                heading(p['name'],'Các vấn đề đã kiểm tra và cách xử lý','shield')
                for note in p['quality_notes']:st.markdown('- '+note)
                if p['missing']:
                    with st.expander('Số ô thiếu theo cột trong bản nghiên cứu'):
                        st.dataframe(pd.DataFrame([{'Cột':k,'Ô thiếu':v} for k,v in p['missing'].items()]),hide_index=True,width='stretch')
        report={sid:{k:p[k] for k in ['n','missing','quality_notes','training_eligible']} for sid,p in profiles.items()}
        st.download_button('Tải báo cáo chất lượng tổng hợp',json.dumps(report,ensure_ascii=False,indent=2),
                           file_name='knee_oa_source_quality.json',mime='application/json')
    with expansion:
        st.markdown('''**Để thêm một nguồn vào kho nghiên cứu:**

1. Lưu file gốc, tên nghiên cứu, phiên bản, đường dẫn, giấy phép và định nghĩa các mã.
2. Kiểm tra mỗi dòng là người, đầu gối hay lần khám; giữ mã người và thời điểm khi nguồn cho phép.
3. Chuẩn hóa đơn vị tuổi, BMI và tên cột; để trống thông tin không có, không mặc định là 0.
4. Khảo sát riêng từng nguồn trước khi quyết định biến nào và nhãn nào có thể dùng chung.
5. Nếu cùng định nghĩa kết cục: thiết kế lại đánh giá theo người/thời gian; dùng nguồn độc lập để kiểm chứng. Không chọn hoặc chỉnh mô hình theo test cũ.

**Dữ liệu dọc cho hướng cảnh báo sớm:** cần tình trạng khớp gối ban đầu, ngày đánh giá, nhãn ở mốc theo dõi xác định, bên gối và mã người. Các nguồn hiện có chưa đáp ứng đầy đủ bài toán này.

**OAI:** hoàn thành thỏa thuận sử dụng dữ liệu, đăng nhập và xin quyền theo hướng dẫn của kho OAI.

**MOST:** đề nghị giảng viên/PI hoặc senior researcher đứng đơn tại AgingResearchBiobank. Dữ liệu chưa được tải vào phiên bản này.
''')
        st.link_button('Hướng dẫn xin dữ liệu OAI','https://www.oaiknowledgebase.com/about/FAQs/')
        st.link_button('Hướng dẫn xin dữ liệu MOST','https://agingresearchbiobank.nia.nih.gov/how-to-make-a-request/')
        st.caption('Phiên bản web chỉ chứa thống kê tổng hợp. CSV nghiên cứu và cơ sở dữ liệu SQLite được giữ trong thư mục research_data của gói tải về.')
