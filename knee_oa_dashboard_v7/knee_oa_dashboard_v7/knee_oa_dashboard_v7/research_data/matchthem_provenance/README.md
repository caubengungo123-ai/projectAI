# Bộ dữ liệu dự án thoái hóa khớp gối — phiên bản 2

Ngày chuẩn bị: 25/10/2026.

## Bộ này có gì?

- `matchthem_osteoarthritis_all_2585.csv`: chuyển đổi nguyên giá trị 2.585 hồ sơ, 7 cột nguồn sang CSV; ô thiếu để trống.
- `knee_oa_labeled_2392.csv`: 2.392 hồ sơ có nhãn, 6 biến đầu vào tiềm năng, nhãn `koa_followup` và khóa nội bộ `record_key`.
- `knee_oa_unlabeled_193.csv`: 193 hồ sơ thiếu nhãn, tách riêng; không tự điền nhãn.
- `data_dictionary.json`: giải thích biến, mã hóa, đơn vị và hạn chế.
- `quality_report.json`: số lượng hồ sơ, phân bố nhãn, dữ liệu thiếu và vấn đề mã hóa.
- `sources.json`: nguồn chính thức, nguồn dẫn xuất và URL tải cố định theo commit.
- `oai_expansion_schema_PROPOSED.json`: thiết kế 30 trường cho OAI gốc, CHƯA có quan sát, CHƯA ánh xạ tên biến gốc.
- `HUONG_DAN_OAI.md`: cách truy cập và chuẩn bị bộ dữ liệu lâm sàng phong phú hơn.
- `source/osteoarthritis.rdata`: dữ liệu đầu vào để kiểm tra lại việc chuyển đổi.

## Phân biệt nguồn

Dữ liệu CSV này được lấy từ đối tượng `osteoarthritis` của gói MatchThem 1.2.1, qua mirror CRAN/MatchThem. Tác giả mô tả dữ liệu là dẫn xuất từ OAI **có chỉnh sửa**. Đây không phải bản OAI gốc, không được giới thiệu là 2.585 hồ sơ bệnh nhân gốc chưa chỉnh sửa. Chưa xác định đầy đủ bản chất những chỉnh sửa đó. Dùng làm bộ thực hành có nguồn và để xây dựng pipeline ban đầu; nghiên cứu kết quả lâm sàng nên dùng OAI gốc sau khi được cấp quyền.

Không trộn với 300 dòng mô phỏng bạn đã tải lên. Không sinh thêm người bệnh, nhân bản dòng để tăng số mẫu, hoặc tự bổ sung triệu chứng không có trong nguồn.

## Nhãn và dữ liệu thiếu

Theo tài liệu MatchThem, KOA là tình trạng khớp gối ở lần theo dõi: 0 = at risk, 1 = diagnosed. Chưa xác minh thời hạn theo dõi và tiêu chuẩn xác định kết cục cụ thể, nên không gọi đầu ra là nguy cơ mắc trong 12/24/48 tháng. Phân bố có nhãn: 1.197 hồ sơ mã 0 và 1.195 hồ sơ mã 1. Không dùng tỷ lệ này làm tỷ lệ mắc bệnh trong cộng đồng.

Toàn bộ 2.585 hồ sơ thiếu: BMI=1, RAC=2, SMK=28, KOA=193. Tuổi, SEX, OSP không thiếu. Các giá trị thiếu được giữ nguyên, không thay bằng 0. File có nhãn vẫn có thể thiếu đầu vào.

Có 68 dòng lặp lại tổ hợp giá trị của cả 7 cột theo phép kiểm tra duplicated(). Vì nguồn không có ID người tham gia xác minh được, đây có thể là các người khác nhau có cùng đặc điểm, không đủ bằng chứng để gọi là cùng bệnh nhân. Giữ nguyên các dòng, ghi nhận hạn chế này khi đánh giá tính độc lập giữa các tập; bộ OAI gốc có ID là hướng ưu tiên để khắc phục.

## Vấn đề mã giới tính

File chứa SEX=1/2, nhưng tài liệu kèm gói mô tả SEX=0/1. Giữ nguyên mã trong `sex_code_unverified`, không suy đoán mã nào là nam/nữ. Tạm loại biến này khỏi mô hình có giao diện cho người dùng cho tới khi được tác giả hoặc data dictionary phù hợp xác nhận. `record_key` chỉ là số dòng nội bộ, không phải ID OAI và không thể dùng để nối dữ liệu gốc.

## Dùng để học mô hình

Chỉ dùng file có nhãn cho phân loại có giám sát. Với mô hình ban đầu, chọn tuổi, BMI, hút thuốc, loãng xương; có thể khảo sát thêm RAC với cách mã hóa phân loại và đánh giá tính phù hợp với nhóm người dùng. Không đưa record_key vào X. Chia tập trước, học bước điền dữ liệu thiếu/chuẩn hóa/mã hóa trên tập huấn luyện trong từng fold. Không điền toàn bộ dữ liệu trước khi chia. Không điền nhãn thiếu để báo cáo độ chính xác.

Tập dẫn xuất không có ID gốc, bên gối, mốc khám hoặc nhiều triệu chứng của bộ mô phỏng cũ. Vì vậy bộ này tăng số hồ sơ có nguồn, nhưng ít loại đặc trưng hơn bộ mô phỏng. Muốn có cả hồ sơ thật và triệu chứng phong phú, làm theo HUONG_DAN_OAI.md.

## Trích dẫn và quyền sử dụng

Trích dẫn Pishgar, Greifer, Leyrat và Stuart (2021), MatchThem: Matching and Weighting after Multiple Imputation, The R Journal; xem sources.json. Tài liệu gói ghi nguồn OAI có thay đổi. Metadata gói công bố GPL (>=2), xem source/MatchThem_DESCRIPTION.txt; không suy diễn rằng giấy phép phần mềm thay thế các điều khoản truy cập dữ liệu OAI gốc. Khi dùng OAI gốc, thực hiện Data Use Agreement và hướng dẫn ghi nhận OAI tương ứng.
