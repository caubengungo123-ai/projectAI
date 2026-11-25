# Kiểm tra Knee OA v7

- 17 kiểm thử Python đạt. Kiểm thử CSV kiểm tra thứ tự và tên cột, UTF-8 BOM, tệp sai định dạng, dòng thiếu giá trị hoặc sai mã và kết quả khớp với chế độ một hồ sơ.
- Streamlit AppTest mở được cả 7 trang. Đã thử điều hướng từ trang chủ, hồ sơ mẫu, tính BMI từ chiều cao/cân nặng, lọc nguồn, lọc nhóm chăm sóc và đổi mô hình/chuẩn hóa ma trận nhầm lẫn.
- AppTest xác nhận chế độ công khai ẩn nhập CSV. Ở chế độ cục bộ, đã thử nhập tệp có hai dòng hợp lệ, một dòng lỗi, kiểm tra nút xuất CSV và đổi sang tệp sai cấu trúc để xác nhận kết quả cũ được xóa khỏi trang.
- Tái lập tệp thống kê MatchThem hai lần, kết quả trùng byte. Ma trận nhầm lẫn, ROC-AUC và Average Precision của Logistic Regression khớp kết quả test trước đó. Điểm của hồ sơ mẫu vẫn khoảng 0,516. Tệp mô hình và báo cáo đánh giá lịch sử trùng bản v6.
- Năm cấu hình được so sánh trên cùng năm fold trong tập train. Logistic Regression gốc có ROC-AUC trung bình cao nhất trong lần thử. Chưa có đánh giá cohort ngoài. Thư mục web chỉ chứa dữ liệu tổng hợp.
- Kiểm tra được thực hiện trên môi trường Python/Streamlit. Gói có lệnh cho PowerShell, chưa chạy trực tiếp trên Windows và chưa cập nhật website công khai.
