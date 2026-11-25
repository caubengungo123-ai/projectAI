"""Research readiness page. Uploads disabled by default on public deployment."""
import json
import os
import pandas as pd
import streamlit as st
from early_warning import PROTOCOL, audit, read_csv, template_csv, manifest_template


def render_early_warning():
    st.markdown('<div class="section-kicker">PHÁT TRIỂN ĐÚNG MỤC TIÊU</div><h2>Cảnh báo sớm · Chuẩn bị nghiên cứu</h2>', unsafe_allow_html=True)
    st.warning('Chưa có mô hình dự báo 48 tháng được huấn luyện. Điểm mô hình ở trang Thử mô hình thuộc bài toán MatchThem cũ.')
    protocol, sources, check = st.tabs(['Định nghĩa bài toán', 'Dữ liệu cần bổ sung', 'Kiểm tra dữ liệu nghiên cứu'])
    with protocol:
        st.markdown('''**Mục tiêu nghiên cứu được đề xuất:** dùng thông tin ban đầu để dự báo tình trạng thoái hóa khớp gối trên X-quang tại mốc 48 tháng, với cửa sổ lần khám 45–51 tháng.

- **Đơn vị:** một bên gối của một người; ban đầu KL = 0 hoặc 1, chưa thay khớp.
- **Nhãn 1:** KL tại lần theo dõi = 2, 3 hoặc 4.
- **Nhãn 0:** KL tại lần theo dõi = 0 hoặc 1.
- **Loại khỏi phân tích:** mất theo dõi, nhãn chưa xác minh, sai mốc theo dõi hoặc đã thay khớp trước lần theo dõi.

Đây là định nghĩa nghiên cứu cần trao đổi với giảng viên/người có chuyên môn. Nó dự báo tình trạng X-quang tại lần khám đã chọn; chưa xác định thời điểm khởi phát, triệu chứng hay mức độ nguy hiểm.
''')
        st.dataframe(pd.DataFrame([
            ['Đầu vào bắt buộc', 'Tuổi và BMI đo tại ban đầu'],
            ['Đầu vào có thể bổ sung', 'Hút thuốc, loãng xương, tiền sử chấn thương gối và NRS đau 0–10 tại ban đầu'],
            ['Tạo nhãn', 'KL ban đầu, KL theo dõi, tháng theo dõi, tình trạng thay khớp và xác minh kết cục'],
            ['Chia tập', 'Theo người: hai bên gối và các bản sao nguồn của cùng người thuộc cùng tập'],
            ['Đánh giá', 'CV chỉ trên train; test riêng; kiểm chứng cohort độc lập khi có dữ liệu'],
        ], columns=['Thành phần', 'Quy định']), hide_index=True, width='stretch')
        st.caption('KL theo dõi và mọi thông tin sau ban đầu chỉ phục vụ tạo nhãn; không được đưa vào vector dự đoán.')
        st.markdown('[Nghiên cứu về thoái hóa X-quang mới xuất hiện trong OAI](https://pmc.ncbi.nlm.nih.gov/articles/PMC4947746/) · [Kho OAI và các mốc theo dõi](https://nda.nih.gov/oai)')
    with sources:
        st.metric('Nguồn hiện có đã xác nhận đủ cho bài toán 48 tháng', '0')
        st.dataframe(pd.DataFrame([
            ['MatchThem · 2.585', 'Chưa xác minh ID người, KL ban đầu/theo dõi và mốc 48 tháng'],
            ['Nagy · 72', 'Dữ liệu cắt ngang; không có kết cục dọc tương ứng'],
            ['Hossain · 247', 'Dữ liệu can thiệp Pre/Post; chưa đáp ứng kết cục 48 tháng'],
            ['KOA Care Pathways · 1.410', 'Khảo sát chăm sóc cắt ngang, chưa có kết cục 48 tháng'],
            ['OAI gốc', 'Cần xin quyền và trích xuất dữ liệu ban đầu + theo dõi cùng người, cùng bên gối'],
        ], columns=['Nguồn', 'Khoảng trống dữ liệu']), hide_index=True, width='stretch')
        st.link_button('Xin quyền truy cập OAI', 'https://www.oaiknowledgebase.com/about/FAQs/')
        st.write('Giữ mã người nghiên cứu nhất quán giữa các bản sao của cùng cohort. Không thay bằng số dòng tự sinh rồi gọi đó là ID người.')
    with check:
        st.write('Để ghép các bảng OAI ban đầu và 48 tháng trên máy, dùng prepare_longitudinal.py và hướng dẫn OAI trong gói dự án.')
        st.write('Tải hai mẫu và chuẩn hóa dữ liệu đã được phép sử dụng trên máy của nhóm. Tệp CSV mẫu chỉ có tiêu đề; không chứa bệnh nhân giả.')
        st.download_button('Tải mẫu CSV dữ liệu dọc', template_csv(), 'longitudinal_template.csv', 'text/csv')
        st.download_button('Tải mẫu xác nhận nguồn', json.dumps(manifest_template(), ensure_ascii=False, indent=2), 'source_manifest_template.json', 'application/json')
        st.download_button('Tải định nghĩa bài toán', json.dumps(PROTOCOL, ensure_ascii=False, indent=2), 'early_warning_protocol.json', 'application/json')
        if os.environ.get('EW_ENABLE_RESEARCH_UPLOAD') != '1':
            st.info('Nhập hồ sơ nghiên cứu đang tắt trên bản công khai. Dùng công cụ kiểm tra trong thư mục research_tools trên máy của nhóm; xem HUONG_DAN.md trong gói tải về.')
            return
        st.info('Chế độ nghiên cứu riêng: tệp tải lên được gửi tới máy chủ đang chạy ứng dụng. Chỉ dùng môi trường được phép; không nhập tên, số điện thoại, CCCD hoặc mã bệnh án trực tiếp. Ứng dụng không chủ động ghi tệp vào cơ sở dữ liệu.')
        data_file = st.file_uploader('CSV theo mẫu chuẩn, tối đa 10 MB', type=['csv'], key='ew_csv')
        manifest_file = st.file_uploader('JSON xác nhận nguồn', type=['json'], key='ew_manifest')
        if data_file is not None and manifest_file is not None:
            if data_file.size > 10_000_000 or manifest_file.size > 100_000:
                st.error('Tệp vượt dung lượng cho phép. Hãy kiểm tra trên máy bằng công cụ dòng lệnh.'); return
            try:
                frame = read_csv(data_file)
                result, _, _ = audit(frame, json.load(manifest_file))
            except Exception:
                st.error('Không đọc được tệp. Kiểm tra CSV UTF-8 và cấu trúc JSON theo mẫu.'); return
            a,b,c = st.columns(3)
            a.metric('Dòng gửi kiểm tra', result['input_rows'])
            b.metric('Dòng đủ điều kiện cấu trúc', result['eligible_rows'])
            c.metric('Người đủ điều kiện', result['participants'])
            for error in result['global_errors']: st.error(error)
            if result['exclusion_reasons']:
                st.dataframe(pd.DataFrame([{'Lý do': k, 'Số dòng': v} for k,v in result['exclusion_reasons'].items()]), hide_index=True, width='stretch')
                st.caption('Một dòng có thể có nhiều lý do loại.')
            st.caption(result['note'])
            st.download_button('Tải báo cáo tổng hợp', json.dumps(result, ensure_ascii=False, indent=2), 'longitudinal_audit.json', 'application/json')
