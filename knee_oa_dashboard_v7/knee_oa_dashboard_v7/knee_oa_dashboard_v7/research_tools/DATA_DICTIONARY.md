# Chuẩn dữ liệu dọc — incident_rkoa_48m_v1

Mỗi dòng là MỘT bên gối của MỘT người ở MỘT thời điểm ban đầu, ghép với MỘT lần theo dõi. CSV UTF-8, dùng dấu chấm thập phân. Để trống ô thiếu; không dùng -1/99/999 thay cho thiếu nếu chưa chuyển đổi theo codebook. ID phải là mã nghiên cứu được phép sử dụng, không phải tên, CCCD, số điện thoại hoặc mã bệnh án trực tiếp.

## Các cột bắt buộc

| Cột | Định nghĩa / mã |
| --- | --- |
| source_id | Tên định danh bản dữ liệu; khớp manifest |
| cohort_id | Cohort gốc; các bản sao OAI phải cùng cohort OAI |
| participant_id | Mã người nghiên cứu nhất quán trong cohort, giữ nguyên số 0 ở đầu; không sinh từ số dòng |
| knee_side | L = trái, R = phải; chuẩn hóa theo codebook, không tự suy luận mã 1/2 |
| baseline_visit_id | Mã lần khám ban đầu, đã xác minh thời điểm |
| followup_visit_id | Mã lần theo dõi khác ban đầu, đã xác minh thời điểm |
| age_baseline | Tuổi ban đầu, năm; kiểm tra hợp lý 18–100, không phải phạm vi lâm sàng đã được xác thực |
| bmi_baseline | BMI ban đầu, kg/m²; kiểm tra hợp lý 10–70, không phải phạm vi mô hình cũ |
| kl_baseline | KL nguyên 0–4; chỉ KL 0 hoặc 1 vào phân tích |
| kl_followup | KL nguyên 0–4 tại lần khám theo dõi; không thay bằng điểm RAD SCORE chưa rõ mã |
| followup_months | Khoảng thời gian thực hoặc mốc khám theo protocol đã xác minh; chỉ nhận 45–51 tháng; không tự điền 48 cho mọi nguồn |
| outcome_verified | 1 khi có kết cục được xác minh từ đánh giá nguồn được phép dùng; 0 = chưa xác minh, bị loại. Dự đoán AI không phải nhãn |
| prior_knee_replacement | 0 = xác minh chưa thay khớp trước ban đầu; 1 = có; thiếu/có đều bị loại |
| knee_replacement_before_followup | 0 = xác minh chưa thay khớp tới lần khám theo dõi; 1 = có; thiếu/có đều bị loại |

## Đặc trưng bổ sung — có thể để trống

| Cột | Mã / đơn vị |
| --- | --- |
| smoking_baseline | 0 = không hút thuốc, 1 = có; cần thống nhất đang hút/hút trong đời theo protocol trước khi gộp nguồn |
| osteoporosis_baseline | 0 = xác minh không, 1 = xác minh có loãng xương tại ban đầu |
| knee_injury_history_baseline | 0/1, tiền sử chấn thương ở cùng bên gối trước hoặc tại ban đầu; định nghĩa nguồn phải tương thích |
| pain_nrs_baseline | NRS đau 0–10 ở cùng bên gối tại ban đầu; cần thống nhất khoảng hồi tưởng. Không tự đổi WOMAC/VAS thành NRS |

Danh sách 6 đặc trưng là ứng viên được định trước, không phải 6 trường đã có trong bộ hiện tại. Trong lần huấn luyện mới, cột hoàn toàn thiếu trong train được bỏ và ghi rõ vào báo cáo. Giá trị thiếu còn lại được xử lý trong pipeline từng fold; không học từ test.

## Tạo nhãn và loại trừ

Chỉ sau khi kiểm tra mã nguồn, nhãn, mốc thời gian và KL ban đầu, nhãn mới `incident_rkoa_48m` = 1 nếu KL theo dõi >= 2, ngược lại = 0. Đây là tình trạng X-quang tại mốc theo dõi được chọn, không phải thời điểm khởi phát đầu tiên, chẩn đoán triệu chứng hay xác suất cần điều trị.

Gối đã có KL >= 2 ở ban đầu bị loại; muốn dự báo tiến triển ở gối đã mắc bệnh cần một protocol khác. Mất theo dõi/thay khớp không tự gán là 0. Việc loại các trường hợp này có thể tạo thiên lệch chọn mẫu; cần báo cáo tỷ lệ mất theo dõi và xem xét nghiên cứu sống còn nếu phù hợp.

Trùng `cohort_id + participant_id + knee_side` bị loại TOÀN BỘ các dòng trùng, kể cả trùng giữa source_id khác nhau. Hai gối khác bên được giữ, nhưng luôn ở cùng tập train/test và cùng phần CV. Các ID đổi giữa nguồn phải có bảng đối chiếu được phép sử dụng trước khi gộp, phần mềm không tự xác minh danh tính.

## Manifest xác nhận nguồn

`source_manifest_template.json` bắt đầu với các xác nhận = false; chỉ đổi thành true sau khi nhóm kiểm tra được hồ sơ và tài liệu:

- `permission_confirmed`: được phép dùng cho mục đích nghiên cứu này, lưu trữ/xử lý ở môi trường đã chọn.
- `codebook_confirmed`: đã đối chiếu định nghĩa và cách mã hóa từng biến, bao gồm tình trạng thay khớp.
- `participant_namespace_confirmed`: cohort_id và ID nhất quán giữa các bản sao; đã kiểm tra liên hệ giữa cohort nếu có.
- `predictor_timing_confirmed`: mọi đặc trưng là thông tin có tại ban đầu, không dùng dữ liệu tương lai.
- `outcome_definition_confirmed`: KL, mốc khám, người/đơn vị xác minh kết cục và định nghĩa nhãn phù hợp protocol.
- `real_observations_confirmed`: là quan sát thực. Dữ liệu tổng hợp chỉ dùng kiểm thử mã và phải được ghi riêng.

`is_synthetic` phải là false cho phân tích thực. Các xác nhận là khai báo của người nghiên cứu; phần mềm không thể thay thế thẩm định nguồn. Không đổi false thành true chỉ để vượt qua kiểm tra.

## Hướng trích xuất OAI

1. Xin quyền dữ liệu và đọc codebook đúng bản phát hành.
2. Lấy bảng lâm sàng ban đầu cho tuổi/BMI/biến bổ sung và bảng chấm X-quang ở ban đầu + mốc 48 tháng. Kho OAI định danh mốc ban đầu V00 và mốc 48 tháng V06; cần kiểm tra bản phát hành đang dùng.
3. Đối chiếu ID người và bên gối, chuyển bảng về một dòng mỗi bên gối. Ghép 1:1, kiểm tra dòng không ghép được và số lượng trước/sau ghép.
4. Chuẩn hóa mã khuyết/special values theo codebook. Không tự đoán cột, cách mã hóa hoặc tên biến từ tài liệu nghiên cứu khác.
5. Xác minh nhãn và tình trạng thay khớp; điền CSV + manifest. Giữ tài liệu ánh xạ cột gốc → cột chuẩn trên máy nghiên cứu.

Công cụ ghép và mẫu ánh xạ nằm trong [OAI_QUICKSTART.md](OAI_QUICKSTART.md). Các cột nguồn phải được điền từ codebook đúng bản phát hành. Gói chưa có tệp OAI gốc để xác nhận ánh xạ thực tế.

## Nguồn phương pháp, kiểm tra 11/11/2026

- MatchThem (dữ liệu có chỉnh sửa, không xác định đủ mốc 48 tháng): https://search.r-project.org/CRAN/refmans/MatchThem/html/osteoarthritis.html
- Kho OAI: https://nda.nih.gov/oai
- Các mốc OAI: https://nda.nih.gov/edit_collection.html?id=2343
- Xin quyền OAI: https://www.oaiknowledgebase.com/about/FAQs/
- Nghiên cứu OAI về thoái hóa X-quang mới xuất hiện (không phải protocol hoàn toàn giống gói này): https://pmc.ncbi.nlm.nih.gov/articles/PMC4947746/
- Chia tập theo người: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html
- Giữ nhóm người ở test: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html
