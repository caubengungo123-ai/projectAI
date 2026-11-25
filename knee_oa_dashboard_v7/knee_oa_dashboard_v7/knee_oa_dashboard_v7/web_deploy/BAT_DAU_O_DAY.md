# Dashboard Knee OA v7

Để chạy cục bộ, xem HUONG_DAN.md ở thư mục gốc. Trang đầu **Tổng quan** trình bày dữ liệu MatchThem và dẫn đến **Thử mô hình** và **Hiệu năng mô hình**. Muốn nhập CSV, khởi động bằng `start_demo_local.ps1` từ gói đầy đủ.

Để cập nhật Streamlit Community Cloud, chép toàn bộ nội dung của `web_deploy` vào gốc repository. Dùng `app.py` làm main file và Python 3.12. Giữ các tệp Python, JSON, CSS, requirements.txt, results và .streamlit cùng nhau. Tệp `model_diagnostics.json` chứa thống kê ROC và Precision–Recall, mốc so sánh Accuracy và kết quả thử cấu hình trên train.

Chế độ nhập CSV và tệp nghiên cứu mặc định tắt trên bản công khai. Dashboard hiển thị kết quả phân loại trên bộ MatchThem phục vụ học tập.

[Tài liệu triển khai Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
