# Knee OA v7 — Phân loại MatchThem và dashboard đa nguồn

Đề tài hiện tại dùng Logistic Regression để phân loại nhãn `koa_followup` trên bộ MatchThem. Dashboard có 4.314 dòng từ bốn nguồn, trong đó 2.392 dòng MatchThem có nhãn dùng trong thực nghiệm học máy. Clinical72, RCT247 và KOA Care Pathways phục vụ phân tích mô tả.

## Các chức năng

- **Tổng quan** hiển thị số nguồn, số dòng, tỷ lệ có nhãn và phân bố đặc trưng của MatchThem.
- **Thử mô hình** nhận một hồ sơ mẫu hoặc nhập tay, hỗ trợ tính BMI và tải kết quả JSON. Chế độ cục bộ có thêm nhập CSV và xuất kết quả theo từng dòng.
- **Hiệu năng mô hình** so sánh Logistic Regression và Random Forest trên báo cáo test đã công bố, hiển thị ma trận nhầm lẫn theo số lượng hoặc tỷ lệ và tải bảng CSV. Đường ROC và Precision–Recall được tái lập cho Logistic Regression.
- **Kho dữ liệu** lọc và tải bảng so sánh tuổi, BMI và độ đầy đủ BMI theo nguồn.
- **Chăm sóc & lâm sàng** có bộ lọc nhóm khảo sát chăm sóc và các thống kê riêng của bộ lâm sàng.
- **Hướng phát triển** lưu protocol, mẫu và công cụ ghép dữ liệu dọc cho nghiên cứu 48 tháng.

## Kết quả tối ưu trên train

Cùng năm fold, Logistic Regression gốc có ROC-AUC trung bình 0,64684, Logistic C=0,1 đạt 0,64682, Logistic C=10 đạt 0,64678, Logistic spline đạt 0,64556 và Histogram Gradient Boosting đạt 0,61333. Lần thử này dùng một thiết kế CV được ghi trong mã và cùng tập train 1.913 dòng của lần chia đã tái lập. Mô hình đang dùng là Logistic Regression gốc. Kết quả test lịch sử của mô hình là Accuracy 62,0% và ROC-AUC 0,6403. Chưa có dữ liệu ngoài để kiểm chứng.

Tái lập đường cong và các thử nghiệm CV từ gói dự án:

```powershell
.\.venv\Scripts\python.exe research_tools\build_matchthem_diagnostics.py --output diagnostics_local.json
```

Đường cong và chỉ số đầu ra là thống kê tổng hợp. Mã nguồn kiểm tra lại ma trận nhầm lẫn, ROC-AUC, Average Precision và tam phân vị train của mô hình gốc trước khi xuất.

## Chạy web trên Windows

Mở terminal ở thư mục chứa HUONG_DAN.md. Dùng Python 3.12 để khớp mô hình đóng gói:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r web_deploy\requirements.txt
.\.venv\Scripts\python.exe -m streamlit run web_deploy\app.py
```

Trang đầu là **Tổng quan**. Vào **Thử mô hình → Một hồ sơ → Điền hồ sơ mẫu → Chạy phân loại** để kiểm tra nhanh. Điểm lớp 1 của mẫu là khoảng 0,516. Nhãn nguồn 0 là “at risk” và nhãn 1 là “diagnosed”.

Để chạy nhiều hồ sơ trên Windows, khởi động bằng lệnh:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_demo_local.ps1
```

Vào **Thử mô hình → Từ tệp CSV**, tải mẫu rồi nhập các cột `age,bmi,smoking,osteoporosis_baseline`. Hai cột cuối nhận 0 hoặc 1. Dùng dấu chấm cho số thập phân. Trang trả danh sách hồ sơ hợp lệ và lỗi theo thứ tự tệp. Kết quả CSV gồm số thứ tự hồ sơ, nhãn, điểm và lý do lỗi. App chạy trên địa chỉ 127.0.0.1 và nhập CSV mặc định tắt trên bản công khai.

Để kiểm tra dữ liệu dọc cho hướng 48 tháng trên máy, dùng lệnh riêng:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_research_local.ps1
```

Script chỉ bật nhập tệp trong tiến trình này và chỉ bind 127.0.0.1. Không bật chế độ nghiên cứu trên app public. Tệp upload được gửi đến máy chủ đang chạy app; app không chủ động lưu hồ sơ vào backend.

## Cập nhật website hiện tại

Nếu cần cập nhật Streamlit Community Cloud, tải toàn bộ **nội dung** trong `web_deploy` vào repository website, dùng Python 3.12 và `app.py`. Xem `web_deploy/BAT_DAU_O_DAY.md`. Giữ `research_data` và các tệp nghiên cứu cục bộ trên máy. Bản ZIP chưa được triển khai công khai.

## Nhánh nghiên cứu 48 tháng

Nhánh này sử dụng protocol riêng cho tình trạng X-quang ở gối có KL 0/1 ban đầu. Chưa có dữ liệu dài hạn đã xác minh và chưa huấn luyện mô hình 48 tháng. Xem `research_tools/OAI_QUICKSTART.md` nếu tiếp tục hướng này.

## Chuẩn bị dữ liệu

research_tools/templates gồm:

- longitudinal_template.csv: chỉ có tiêu đề, KHÔNG có bệnh nhân giả.
- source_manifest_template.json: nguồn, phiên bản, codebook, điều kiện sử dụng và các xác nhận ban đầu false.
- protocol.json: định nghĩa bài toán có phiên bản.

Với bảng nguồn OAI, dùng hướng dẫn ghép trong research_tools/OAI_QUICKSTART.md. Nếu đã có CSV chuẩn, tạo private_data trên máy và lưu thành longitudinal.csv; điền manifest thành source_manifest.json. Giữ file gốc và bảng ánh xạ cột gốc → cột chuẩn. Không lưu tên, điện thoại, CCCD hoặc mã bệnh án trực tiếp vào mẫu. Không đổi xác nhận sang true nếu chưa kiểm tra được điều kiện tương ứng.

Đọc DATA_DICTIONARY.md trước khi điền. Thiếu biến bổ sung phải để trống, không mặc định 0. Thiếu kết cục phải loại và báo số lượng, không đổi thành không bệnh. Hai bản sao cùng xuất phát từ OAI phải có cùng cohort_id và hệ ID người. Phần mềm không tự xác minh danh tính hoặc sự độc lập giữa cohort.

## Kiểm tra trước khi huấn luyện

Chạy từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe research_tools\train_early_warning.py --data private_data\longitudinal.csv --manifest private_data\source_manifest.json --audit-only --output private_results\audit_01
```

Kết quả là audit.json và row_issues_PRIVATE.csv. File lỗi ghi số dòng CSV cần xem, dòng đầu dữ liệu là dòng 2. Một dòng có thể có nhiều lý do loại. Thiếu cột/xác nhận nguồn hoặc có cột ngoài mẫu chặn toàn bộ phân tích; lỗi từng hồ sơ được loại riêng và thống kê. Qua kiểm tra cấu trúc không chứng minh dữ liệu đúng về y khoa.

## Huấn luyện khi đã đủ dữ liệu phù hợp

```powershell
.\.venv\Scripts\python.exe research_tools\train_early_warning.py --data private_data\longitudinal.csv --manifest private_data\source_manifest.json --output private_results\experiment_01
```

Mặc định giữ khoảng 20% số NGƯỜI làm test nội bộ, seed 42. Hai gối cùng người luôn cùng tập và cùng phần CV. Chọn mô hình bằng CV train, ngưỡng 0,5 cố định; không chọn theo test. Không đổi seed để tìm test đẹp. Cột ứng viên hoàn toàn thiếu trong train được bỏ và ghi vào báo cáo; giá trị thiếu còn lại được xử lý trong pipeline mỗi fold.

Có thể thêm `--external-cohort TEN_COHORT` để giữ cohort đó làm test ngoài nếu đã xác minh thực sự độc lập. Bản sao OAI không phải cohort độc lập.

Thư mục kết quả phải mới/rỗng để tránh ghi đè. Giữ snapshot dữ liệu/manifest cho mỗi nghiên cứu; SHA256 được ghi lại. Chạy lại trên test đã xem không biến nó thành đánh giá độc lập mới.

Kết quả gồm research_metrics.json, protocol.json, early_warning_RESEARCH_ONLY.joblib và các file PRIVATE. Chúng phục vụ nghiên cứu, không tự thay mô hình trên web. Chưa có ngưỡng nguy cơ thấp/trung bình/cao hay xác suất lâm sàng được kiểm chứng. Không đưa dữ liệu cấp hồ sơ, các file PRIVATE hoặc tệp model nghiên cứu lên GitHub public.

Ít nhất 5 người mỗi lớp trong train chỉ là kiểm tra tính toán tối thiểu cho CV, KHÔNG chứng nhận cỡ mẫu đủ. Cần đánh giá số ca, độ bất định và sai lệch do mất theo dõi. Chỉ số tính theo gối; hai gối có tương quan và script chưa báo khoảng tin cậy theo người. Chưa có kiểm định lâm sàng hoặc triển khai tự động.

## Kiểm thử phần mềm

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s research_tools -v
```

Test tạo dữ liệu nhân tạo nhỏ trong bộ nhớ để kiểm tra mã; không phải dữ liệu nghiên cứu mới và không được dùng báo cáo hiệu quả y tế. Kết quả kiểm tra bản đóng gói ở VALIDATION.md.

## Nguồn phương pháp

- Kho OAI: https://nda.nih.gov/oai
- Mốc khám OAI: https://nda.nih.gov/edit_collection.html?id=2343
- Quyền truy cập: https://www.oaiknowledgebase.com/about/FAQs/
- Nghiên cứu OAI về thoái hóa X-quang mới xuất hiện: https://pmc.ncbi.nlm.nih.gov/articles/PMC4947746/ . Không có nghĩa protocol trong gói đã được thẩm định.
- Chia nhóm người: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html

Nguồn dữ liệu, giấy phép và làm sạch v3 được giữ ở NGUON_DU_LIEU_V3.md và research_data/source_registry.json.
