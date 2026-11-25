# Chuẩn bị dữ liệu OAI tại mốc 48 tháng

Sau khi có quyền sử dụng OAI, chạy các bước dưới đây trên máy được phép lưu và xử lý dữ liệu. Công cụ ghép dữ liệu dùng tệp CSV hoặc bảng văn bản phân tách ký tự, mã UTF-8. Việc ghép dùng bên gối từ codebook và giữ nguyên mã người có số 0 đầu.

## 1. Lấy bảng và đối chiếu tài liệu

Hoàn thành Data Use Agreement và yêu cầu quyền nhóm Osteoarthritis Initiative theo [hướng dẫn OAI CORE](https://www.oaiknowledgebase.com/about/FAQs/). Trong [kho OAI](https://nda.nih.gov/oai), lấy bảng lâm sàng, bảng chấm X-quang và tài liệu đi kèm phiên bản dữ liệu được cấp. [Danh mục NIH](https://nda.nih.gov/edit_collection.html?id=2343) xác nhận V00 là ban đầu và V06 là lần khám 48 tháng.

| Bảng trong cấu hình | Nội dung cần lấy | Khóa sau chuẩn hóa |
| --- | --- | --- |
| `clinical_baseline` | Tuổi và BMI ban đầu. Tìm trong AllClinical00 hoặc bảng khám thể chất ban đầu tương ứng. Có thể thêm hút thuốc và loãng xương nếu định nghĩa đã thống nhất. | Mã người |
| `xray_baseline` | Điểm KL ban đầu. Tên bảng tham khảo là kxr_sq_bu00. Nếu dùng tiền sử chấn thương hoặc NRS đau, đưa các cột đã đối chiếu vào bản xuất này theo cùng bên gối. | Mã người và bên gối |
| `xray_followup` | Điểm KL lúc V06. Tên bảng tham khảo là kxr_sq_bu06. Trong bản xuất đã rà soát, thêm `outcome_verified` bằng 1 cho điểm đọc hợp lệ đã xác minh. Để trống hoặc dùng 0 khi chưa xác minh. | Mã người và bên gối |
| `followup_status` | Khoảng theo dõi và tình trạng thay khớp trước baseline và đến lần theo dõi cho từng gối. Dùng `oai_followup_status_template.csv` để đối chiếu định dạng. | Mã người và bên gối |

Một [nghiên cứu dùng OAI](https://pmc.ncbi.nlm.nih.gov/articles/PMC5569023/) có mô tả các bảng AllClinical00, kxr_sq_bu00 và kxr_sq_bu06. Các tên cột `CONFIRM_...` trong mẫu là chỗ điền theo codebook của bản thực tế. Nếu có nhiều lần đọc hoặc phiên bản, chọn một cách đọc phù hợp trước khi ghép và ghi lựa chọn vào hồ sơ nghiên cứu. Dùng cùng hệ mã người trên cả bốn bảng. Kho NDA có thể dùng hệ mã khác giữa bản xuất Query và tệp ASCII/SAS tải toàn bộ. [Mô tả xuất dữ liệu NDA](https://nda.nih.gov/general-query.html?q=query%3Dfeatured-datasets%3AOsteoarthritis+Initiative+%28OAI%29)

Đối chiếu tình trạng thay khớp theo hồ sơ có bên gối và thời điểm. Chỉ điền 0 khi đã xác minh chưa thay khớp tại mốc tương ứng. Nếu không xác định được thì để trống. Tính khoảng thời gian từ thông tin lần khám, hoặc sử dụng mốc lịch được tài liệu nguồn và protocol cho phép. Cửa sổ chấp nhận là 45–51 tháng. Xem định nghĩa trường ở [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## 2. Điền cấu hình và xác nhận nguồn

Từ thư mục gốc, tạo môi trường Python theo HUONG_DAN.md rồi chạy trong PowerShell:

```powershell
New-Item -ItemType Directory -Force private_data
Copy-Item research_tools\templates\oai_mapping_template.json private_data\oai_mapping.json
Copy-Item research_tools\templates\source_manifest_template.json private_data\source_manifest.json
Copy-Item research_tools\templates\oai_followup_status_template.csv private_data\oai_followup_status.csv
```

- Đặt bốn bảng trong `private_data` hoặc sửa `path` theo vị trí thực tế. Đường dẫn tương đối tính từ tệp cấu hình. Nếu tệp gốc dùng dấu `|`, khai báo `"delimiter": "|"`.
- Trong mỗi khối `columns`, giữ tên cột chuẩn ở bên trái. Điền đúng tên cột nguồn ở bên phải. Nếu đang xuất từ bảng rộng có gối trái và phải trên cùng một dòng, hãy chuyển về một dòng cho mỗi bên trước.
- Có thể bổ sung `missing_codes` để chuyển các mã khuyết ghi trong codebook thành ô trống. Ví dụ cú pháp `"missing_codes": {"kl_followup": ["MISSING"]}`. Có thể dùng `value_maps` để chuyển cột chỉ định sang mã chuẩn, ví dụ cú pháp `"value_maps": {"knee_side": {"RIGHT": "R", "LEFT": "L"}}`. Đối chiếu mã thực tế trước khi áp dụng, kể cả nếu bảng dùng số.
- Điền cùng `source_id` và `cohort_id` ở tệp ánh xạ và manifest. Ghi rõ bản phát hành, tài liệu mã hóa và điều khoản sử dụng. Các xác nhận trong mẫu bắt đầu bằng `false`. Chỉ xác nhận sau khi nhóm đã đối chiếu.

## 3. Ghép và kiểm tra

```powershell
.\.venv\Scripts\python.exe research_tools\prepare_longitudinal.py --mapping private_data\oai_mapping.json --manifest private_data\source_manifest.json --output private_results\oai_prepared_01
```

Mỗi lần chạy dùng một thư mục đầu ra mới. Tệp `join_report.json` cho biết số gối ban đầu có hoặc thiếu từng bảng ghép, số đủ điều kiện, phân bố nhãn, lý do loại và SHA-256 đầu vào. `longitudinal_PRIVATE.csv` giữ các dòng ban đầu để lần theo ca mất theo dõi. `row_issues_PRIVATE.csv` chỉ vị trí của từng dòng cần kiểm tra trong tệp đã ghép. Một dòng có thể có nhiều lý do loại. Khóa trùng hoặc mã bên gối không ánh xạ được sẽ dừng bước ghép. Khi cấu trúc nguồn đã ghép được nhưng manifest chưa đầy đủ hoặc không có gối đủ điều kiện, công cụ vẫn ghi báo cáo và trả mã lỗi 2.

## 4. Huấn luyện khi đã có dữ liệu thực đủ điều kiện

```powershell
.\.venv\Scripts\python.exe research_tools\train_early_warning.py --data private_results\oai_prepared_01\longitudinal_PRIVATE.csv --manifest private_data\source_manifest.json --output private_results\oai_experiment_01
```

Script huấn luyện chạy lại kiểm tra đầu vào và giữ cả hai gối của một người trong cùng tập. Kết quả là đánh giá nghiên cứu cho tình trạng X-quang tại mốc đã chọn. Lưu các bảng nguồn, bảng ánh xạ và tệp kết quả riêng để truy vết. Chỉ phần `web_deploy` có thể dùng để cập nhật dashboard công khai.
