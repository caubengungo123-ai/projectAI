# Mở rộng dữ liệu và dashboard khớp gối

Phiên bản ngày 11/11/2026. Gói này bổ sung hai nguồn dữ liệu thực đã tải và kiểm tra, cùng mục Kho dữ liệu trên ứng dụng Streamlit.

## Đã thu thập được gì

| Nguồn | Số dòng dùng cho nghiên cứu | Vai trò |
| --- | ---: | --- |
| MatchThem osteoarthritis | 2.585 | Nguồn hiện tại; 2.392 hồ sơ có nhãn dùng cho mô hình cũ |
| Knee OA 72 của Nagy và Nagy-Finna | 72 | Thống kê lâm sàng, xét nghiệm, tuổi, BMI và chất lượng dữ liệu |
| Knee OA Dataset của Hossain | 247 | Thống kê dữ liệu thử nghiệm, tuổi, BMI, độ KL và các thang đo trước can thiệp |

319 dòng được bổ sung từ hai nguồn mới. Tổng bảng theo nguồn có 2.904 dòng. Chưa xác minh được số người duy nhất giữa các nghiên cứu; không gọi đây là 2.904 bệnh nhân độc lập. OAI, MOST và bộ ảnh X-quang chỉ có thông tin danh mục trong phiên bản này, chưa tải hồ sơ/ảnh.

## Hai thư mục dùng cho hai công việc

**web_deploy:** các file để chạy hoặc cập nhật website. Chỉ chứa mô hình, mã ứng dụng và thống kê tổng hợp. Không có bảng hồ sơ của ba nguồn.

**research_data:** CSV, cơ sở dữ liệu SQLite, codebook, báo cáo chất lượng và thông tin trích dẫn để nghiên cứu trên máy. Các mã source_record_key chỉ là số dòng nội bộ, không phải ID bệnh nhân đã xác minh.

## Cập nhật GitHub và Streamlit

1. Giải nén gói vào một thư mục mới.
2. Mở repository Raselot16/knee-oa-dashboard trên GitHub.
3. Chọn Add file rồi Upload files.
4. Kéo NỘI DUNG bên trong thư mục web_deploy vào. app.py phải nằm ngay ở gốc repository, cùng dashboard_style.css, data_library.py và multisource_data.json. Giữ cấu trúc results/model_comparison và .streamlit.
5. Bấm Commit changes. Nếu app đã được triển khai, đợi Streamlit cập nhật rồi tải lại trang. Nếu chưa, tạo app từ repository với branch main, main file app.py, Python 3.12.
6. Mở mục Kho dữ liệu ở thanh điều hướng bên trái để xem nguồn và biểu đồ mới.

Nếu chỉ cập nhật tối thiểu từ bản web đã gửi trước: thay app.py, thêm data_library.py và multisource_data.json. Các file còn lại trong gói là bản đầy đủ để triển khai lại. Không tải thư mục research_data lên repository web công khai.

Chạy trên máy từ terminal trong web_deploy nếu đã cài Python:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Nguồn và quyền sử dụng

- MatchThem: https://search.r-project.org/CRAN/refmans/MatchThem/html/osteoarthritis.html . Là dữ liệu dẫn xuất OAI có chỉnh sửa, không phải OAI gốc.
- Nagy, Előd Ernő; Nagy-Finna, Csilla (2026). Knee_OA_72_data_2026. Mendeley Data, V1. https://doi.org/10.17632/m5b9hfbkk8.1 . Giấy phép CC BY 4.0.
- Hossain, Kazi Md Azman (2026). Knee OA Dataset. Mendeley Data, V1. https://doi.org/10.17632/skf2mxd5h8.1 . Giấy phép CC BY 4.0.
- License: https://creativecommons.org/licenses/by/4.0/ . Ghi công tác giả, liên kết giấy phép và nêu các thay đổi khi tái sử dụng.

File source_registry.json lưu phiên bản, SHA256 file gốc, đường dẫn và quyết định có dùng cho huấn luyện hay không. Các CSV trong gói là bản đã biến đổi, không phải file Excel nguyên bản do tác giả phát hành.

## Xử lý đã thực hiện

- MatchThem: giữ dữ liệu và nhãn nguồn; chuẩn hóa tên cột, thêm mã dòng, tuổi và BMI cho bảng thống kê chung. Không xác nhận lại được mã giới tính nên không dùng biến này để suy luận.
- Bộ 72: file gốc có 74 dòng sau tiêu đề. Hai dòng cuối là tiêu đề lặp và chú giải, được loại khỏi bảng hồ sơ. Giữ đủ 72 hồ sơ.
- PATIENT ID của bộ 72 không được đưa vào CSV chia sẻ hoặc website; thay bằng số dòng nội bộ. Bản gốc tải về được giữ riêng trong quá trình thu thập, không nằm trong gói web.
- Bộ 72 có 1 BMI bằng 0. Giá trị này vẫn ở cột bmi; cột bmi_clean để trống. Biểu đồ và trung vị BMI sử dụng 71 giá trị hợp lệ, không tự điền số thay thế.
- Giữ RAD SCORE dạng thập phân, không làm tròn thành KL nguyên. Giữ mã OBEZ/DIS HIST khi quan sát khác với chú giải, nêu vấn đề trong báo cáo chất lượng.
- Bộ thử nghiệm: giữ đủ 247 dòng và 34 biến nguồn. Tạo mã dòng nội bộ vì file chưa có ID người tham gia. Chưa tự giải mã Group, Gender và Symptoms_side.
- Giữ các biến trước/sau can thiệp trong bản nghiên cứu. Web chỉ khảo sát các thang đo ban đầu; không suy luận hiệu quả điều trị khi chưa có protocol.
- Cơ sở dữ liệu có bảng riêng cho từng nguồn, và view demographics_by_source để so sánh tuổi/BMI. View không tạo nhãn KOA chung.

## Vì sao chưa gộp tất cả để huấn luyện

MatchThem có nhãn KOA tại lần theo dõi; bộ 72 là dữ liệu cắt ngang ở bệnh nhân OA; bộ thử nghiệm có độ KL 1 và 2 cùng các cột Pre/Post. Đây là các ý nghĩa nhãn và bối cảnh khác nhau. Thiếu trường không được đổi thành 0. Không lấy độ KL hoặc tình trạng đã mắc OA để tự tạo cùng nhãn koa_followup.

Mô hình Logistic Regression, tập train/test, SHA dữ liệu gốc và các chỉ số cũ được giữ nguyên. Thêm 319 dòng vào kho khám phá không phải thêm 319 mẫu huấn luyện, và không chứng minh độ chính xác đã tăng.

## Bước tiếp theo để làm cảnh báo sớm

Ưu tiên tiếp cận dữ liệu dọc OAI hoặc MOST: có ID người, bên gối, đánh giá ban đầu, ngày khám, thời hạn theo dõi và kết cục phù hợp. Lọc đối tượng theo định nghĩa bài toán, chỉ lấy thông tin đã có ở thời điểm dự đoán, chia tập theo người và thiết kế kiểm chứng trên nguồn độc lập.

- OAI: https://nda.nih.gov/oai . Hướng dẫn xin quyền: https://www.oaiknowledgebase.com/about/FAQs/ . Hoàn thành thỏa thuận sử dụng dữ liệu và các yêu cầu hiển thị trong tài khoản; phiên bản này chưa truy cập hồ sơ gốc.
- MOST: https://agingresearchbiobank.nia.nih.gov/studies/most/details . Hướng dẫn: https://agingresearchbiobank.nia.nih.gov/how-to-make-a-request/ . Yêu cầu PI/senior researcher đủ điều kiện đứng đơn, thường cần phối hợp với giảng viên. Chưa tải hồ sơ MOST.
- Ảnh X-quang: Chen, Pingjun (2018). https://doi.org/10.17632/56rmx5bjcr.1 . Gói gốc khoảng 7,17 GB, chưa tải. Đây là ảnh từ OAI; không phải một cohort độc lập và cần mô hình ảnh riêng.

## Kiểm tra nhanh sau khi cập nhật

- Trang Tổng quan cũ vẫn có 2.585 hồ sơ, 2.392 hồ sơ có nhãn.
- Kho dữ liệu hiển thị ba nguồn đã có và 319 dòng mới; chọn được nguồn 72 hoặc 247 hồ sơ.
- BMI hợp lệ trong bộ 72 là 71 hồ sơ.
- Thử tuổi 68, BMI 28.1, không hút thuốc, không loãng xương: điểm mô hình vẫn khoảng 0.516.
- Chỉ số cũ không thay đổi: LR Accuracy 0.6200, ROC-AUC 0.6403. Đây là kết quả nội bộ trên dữ liệu dẫn xuất, không phải đánh giá lâm sàng độc lập.
