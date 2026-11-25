# Dữ liệu nghiên cứu trên máy

SQLite có bốn bảng nguồn. View `demographics_by_source` nối dữ liệu tuổi và BMI có gắn nguồn, gồm 4.314 dòng. Mỗi dòng được đếm trong nguồn của nó. View chưa xác minh trùng người giữa các nguồn.

| Nguồn | Dòng | Phạm vi |
| --- | ---: | --- |
| MatchThem | 2.585 | 2.392 dòng có nhãn trong mô hình minh họa |
| Clinical72 | 72 | Mô tả lâm sàng. Một BMI bằng 0 được để trống ở `bmi_clean`. |
| RCT247 | 247 | Khám phá dữ liệu can thiệp |
| KOA Care Pathways | 1.410 | Khảo sát cắt ngang về chăm sóc ở Thụy Sĩ. BMI để trống vì nguồn không thu thập. |

`carepathways_research.csv` giữ 139 cột của bản làm sạch công bố, với khoảng trắng ở đầu/cuối giá trị được bỏ. Bảng SQLite `carepathways` chỉ chứa các trường sử dụng trong phân tích chăm sóc và kiểm tra chất lượng. `source_record_key` là số dòng nội bộ. Biến `duration_sy_to_diag` giữ nguyên số âm; dashboard bỏ biến này khỏi biểu đồ. Trang web chỉ chứa thống kê tổng hợp.

Nguồn KOA Care Pathways v2 do Céline Moetteli-Graf, Stefan Neuner-Jehle và Karin Niedermann công bố trên Zenodo theo CC BY 4.0. Mã MD5 của CSV gốc là `96657a53eacc45b97a1c3df9b2694b35`. Các mã SHA-256 và mô tả nguồn nằm trong `source_registry.json` và `quality_report.json`. [Bộ dữ liệu và codebook](https://doi.org/10.5281/zenodo.22692421) · [Giấy phép CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Nguồn dữ liệu cho nghiên cứu 48 tháng cần kết quả X-quang theo thời gian của cùng người và cùng bên gối. Chưa có bộ như vậy trong thư mục này.
