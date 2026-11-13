# Nhật ký kết quả từng bước — Corporate actions DELTA

Cập nhật ngày 12/11/2026. Nhánh làm việc: `feature/indicators-v1`.

File này được tạo riêng theo yêu cầu owner để theo dõi liên tục kết quả từng bước.
Phạm vi tổng hợp là quá trình chuyển bộ thu thập, review V7 và hoàn thiện dữ liệu
ORS từ 04–06/11/2026. Các kết quả trước phiên lập nhật ký được dẫn lại từ
[trạng thái thực hiện](CURRENT_STATUS.md) và evidence tương ứng; không chạy lại batch
hoặc kiểm thử cũ để lập tài liệu này. Không coi đây là báo cáo hoàn tất toàn chiến dịch.

## Kết quả hiện tại

**Chỉ đạo mới nhất bước25: chỉ tạm ngừng DATE_ONLY trong corporate_actions**,
gồm corporate action đưa sang Product/M3/research, đến khi owner yêu cầu dùng lại.
Financial và phần khác giữ policy DATE_ONLY đã duyệt trong đúng scope/gate cũ.
Phạm vi toàn DELTA ở bước24 đã được D-TIME-ONLY-02/config execution V2 thay thế.
Trong corporate_actions ưu tiên timestamp công bố đúng semantics/clock/timezone;
thiếu thì giữ evidence/DEFERRED. Chưa thêm hard guard mọi CLI cũ.

**ORS đủ toàn văn 85/85 bài trong snapshot tìm kiếm đã quan sát; còn 0 bài thiếu nội dung.**

| Nội dung | Kết quả |
| --- | --- |
| HTTP raw có hash và receipt GET HTTP200 | 20 bài |
| Toàn văn rendered DOM có hash và receipt thu nhận | 65 bài |
| Bài chỉ có fields review | 0 bài |
| Bài thiếu toàn văn | 0 bài |
| Bài cổ phiếu đúng mã ORS | 31 bài |
| Bài trái phiếu có mã đầy đủ khác ORS | 54 bài |
| Candidate điều chỉnh giá cổ phiếu | 3 bài |
| Candidate đã có ex-date đọc trực tiếp từ nguồn bổ sung | 3/3; chưa duyệt canonical |
| PDF gốc HOSE 79 quyền mua 2024 | Đã lưu, SHA-256 khớp bản Vietstock cũ |
| Số lượng kết quả có PDF UBCKNN năm 2024 | Quyền mua 100.000.000; cổ tức 35.999.743 CP |
| Nguồn Sở xác nhận ex-date quyền mua 2021 | Bước17 đọc HNX trực tiếp:10/06/2021; text AX/receipt/hash, chưa HTTP raw/PDF |
| Packet/bundle offline cho ba sự kiện | Bước18 giữ54 dòng cũ,59 dòng hiện hành/27 observation mới; hai field đã chọn, chưa canonical |
| Đề xuất giảm review thủ công | CA-REVIEW-DELEGATION-V1, chờ duyệt nguyên gói; chưa kích hoạt |
| Quy tắc khi hai nguồn mâu thuẫn | Owner đã chỉ định; áp dụng chọn2 field ở bước15 và replay bước16 |
| Kết quả áp dụng nguồn thứ ba | Đã chọn2/2 field ở bước15; giữ dissent, chưa canonical |
| Workflow đối chiếu ba nguồn offline | Bước16 đã tự tính lại chọn2/2; chưa tự tìm nguồn/đọc PDF;78 test đạt |
| Review gap còn lại | Bước17 đọc8PDF/26trang,triage13bài; đóng5/6nhóm gap,PDF4122 tùy chọn còn thiếu |
| Bundle hợp nhất evidence và readiness | Bước18 PASS scope cho3/3packet;43 test/compileall đạt; canonical/PIT/identity chưa mở |
| Hai lỗi đường dẫn helper test legacy | Bước19 đã sửa decision_packet và cached_review;94/94 test,compileall,synthetic smoke đạt |
| Evidence ngày công bố ba sự kiện | Bước20 có2ứng viên HOSE cho2024;2021 còn thiếu;17/59field có ứng viên,0available_at được gán |
| CafeF lookup đúng ba sự kiện | Bước21 khớp3bản tin,2PDF trùngHOSE;0/3CreateDate đúngevent vì endpoint102record chỉ BCTC;chưa áp ngày |
| Ưu tiên thời gian theo chỉ đạo owner | Bước22 ưu tiên timestamp công bố có evidence/múi giờ; DATE_ONLY fallback theo rule đã duyệt,không chọn modified/update |
| Xác minh timestamp nguồn HOSE/HNX | Bước23 xác minh2cách giải mã postedDate bằng UTC; phát hiện lệch7giờ giữa metadata bản tin/file;0instant công bố thực được chốt,2021còn thiếu |
| Chỉ đạo DATE_ONLY hiện hành | Bước25 chỉ tạm ngừng corporate_actions; financial/phần khác giữ policy đã duyệt; phạm vi toàn project bước24 đã superseded |
| Timestamp có offset mới | Bước26: Stockbiz22811809 khai báo16/01/2024 14:51:00+07:00, PDF khớpHOSE79; chưa chứng nhận first-publication HOSE/available_at |
| Supplement timestamp hiện hành | Bước27:3packet/3timestamp nguồn khai báo;59row giữ nguyên;22row cósupport/2partial/35thiếu,0available_at |
| Contract admission timestamp | Bước28:proposalProduct/M3 pilot13mapping/46hold;MANUAL_REVIEW_REQUIRED,inactive;Mekong có giờ và ex-date2024 |
| Đối chiếu nguồn/archival timestamp | Bước29: archive Mekong ghi11:18:31+07, trang hiện tại11:18:00; điều khoản báo khác khớp, giờ2021 chưa được xác nhận độc lập |
| Proposal timestamp V2 | Bước30:6mapping cổ tức dùng11:18:31+07;7mapping2021 giữgap;13candidate/46hold,inactive,chưaavailability |
| Archive quyền mua2021 | Bước31:9GET/8search chưa cócapture độc lập;giữ7gap,0timestamp mới;PARTIAL/DEFERRED |
| Thông báo HNX/TPS quyền2021 | Bước32:lưuPOSTrawHNX390773,khớpAX/9field;TPS769/771chỉngày,publicationtimestamp vẫnDEFERRED |
| Live binding quyền2024 | Bước33:legacyarticle1548002→PDFHTTP200 khớpHOSE;11field cóbinding live,temporal admission chưareview |
| Proposal timestamp V3 | Bước 34: 24 candidate/35 hold; thêm 11 composite Stockbiz mapping, ngoại lệ modified vắng có phạm vi; inactive/chờ approval |
| Nguồn báo khác quyền2024 | Bước35:TNCK17:36:15+07 khácStockbiz14:51;6field support/1partial/4thiếu;chưa xác nhận exactinstant |
| Nguồn FUNAN quyền2024 | Bước36:đúngORS/noticeURL,không cópublicationclock;18/1làex-date,không xác nhận14:51 |
| Lookup Vietstock quyền2024 | Bước37:entrypage403,dừngroute;chưa cóarticleURL/timestamp;filemodified không dùng làmpublication |
| Clock gốc HOSE quyền2024 | Bước41:vẫnOPEN;FireAnt14:51+07 directPDF khớpHOSE,không là vote độc lập Stockbiz;VNDIRECT_API403DEFERRED |
| Timestamp được chấp nhận cho Product/M3 pilot | Bước42:owner chấp nhậnFireAnt16/01/2024 14:51:00+07 cho đúng11field166577;11ADMITTED/48DEFERRED trongoverlay mới |
| Review13mapping của hai sự kiện còn lại | Bước43:7TNCK02/06/2021 16:55:48+07 và6Mekong11/06/2024 11:18:31+07 đãreview;chưaadmission,giữ11/48actual |
| Timestamp pilot hiện hành | Bước44:owner chấp nhận thêm13row;V2 có24ADMITTED/35DEFERRED,11FireAnt giữ nguyên;không firstSở/strictPIT |
| Kiểm kê các trường còn chờ | Bước 45 đối chiếu 35 trường với 11 nhóm tài liệu, gồm 3 dòng dùng để lưu khác biệt giữa nguồn |
| Múi giờ công bố HNX | Bước 48 xác minh `+07:00` trên RSS tháng 11/2026 và đối chiếu khớp 3 ID với bảng UPCoM. Hai bài ORS tháng 08/2021 còn chờ xác minh múi giờ |
| Lưu trữ RSS HNX tháng 08/2021 | Bước 49 chưa tìm thấy hai mục ORS trong nguồn đã đọc. Arquivo.pt trả 0 kết quả cho ba URL, Wayback và Common Crawl chưa xác định do lỗi HTTP |
| Ngày công bố Nghị quyết 11 của ORS | Bước 50 xác minh qua công văn TPS ngày 22/07/2021 và hai trang nghị quyết khớp bản CafeF. 5 trường còn chờ giờ đăng |
| Bản công bố Nghị quyết 05 của ORS | Bước 51 gắn bài HOSE 1688391 với đúng PDF TPS. Giờ hiển thị 14:20, quy ước múi giờ lịch sử còn chờ |
| Thông báo hủy quyền họp/lấy ý kiến | 3 bài |
| Thông báo cổ phiếu không điều chỉnh giá | 25 bài |
| Trường canonical đã áp dụng trong các stage review ORS | 0 |

Nguồn số liệu hiện hành: [summary inventory V3](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v3/summary.json).
Danh sách từng bài, phân loại và đường dẫn evidence nằm trong
[inventory 85 bài](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v3/article_inventory.jsonl).

## Bảng theo dõi các bước

| Bước | Ngày | Công việc | Kết quả |
| --- | --- | --- | --- |
| 01 | 04/11/2026 | Chuyển bộ thu thập sang nhánh Indicators | PASS stage chuyển nhánh; prefix 616 query được giữ |
| 02 | 04/11/2026 | Sửa supervisor V7 sau lỗi khởi tạo thư mục run | PASS stage sửa supervisor; worker V6 giữ nguyên |
| 03 | 06/11/2026 | Review offline run V7 | PASS 1.072/1.072 query trong scope; ORS còn chênh 5 ID |
| 04 | 06/11/2026 | Chẩn đoán ORS bằng Chrome ẩn | PARTIAL; GET trang 1 trả body 0 byte |
| 05 | 06/11/2026 | Đối chiếu danh sách ORS trên Chrome thường | PASS; quan sát đủ 85/85 ID |
| 06 | 06/11/2026 | Review năm bài ở trang cuối | PASS phân loại; mới lưu fields, chưa có toàn văn |
| 07 | 06/11/2026 | Kiểm kê cache ORS V1 | PASS inventory; 20 raw + 5 fields + 60 thiếu detail |
| 08 | 06/11/2026 | Bổ sung/review 24 bài cổ phiếu | PASS nội dung; inventory V2 còn 36 bài thiếu detail |
| 09 | 06/11/2026 | Thu 36 bài trái phiếu và toàn văn 5 bài cũ | PASS; inventory V3 đủ toàn văn 85/85 |
| 10 | 06/11/2026 | Review ex-date, điều khoản và revision của ba candidate | PASS trường quan sát 3/3; event readiness PARTIAL, chờ review nguồn/lineage |
| 11 | 06/11/2026 | Bổ sung nguồn gốc HOSE, kết quả phát hành và lineage | Review có giới hạn hoàn tất; readiness PARTIAL vì HNX ex-date/revision/discrepancy |
| 12 | 06/11/2026 | Lập packet quyết định offline cho ba sự kiện | PASS chuẩn bị packet; 54 field / 22 nguồn / 6 quyết định pending, readiness PARTIAL |
| 13 | 06/11/2026 | Soạn quy tắc ủy quyền agent tự review | PASS chuẩn bị đề xuất; 12 quy tắc / 12 tình huống, policy inactive chờ duyệt một lần |
| 14 | 06/11/2026 | Ghi chỉ đạo chọn theo nguồn thứ ba xác nhận | PASS ghi quy tắc đã được owner chỉ định; policy V2 riêng, 0 field mới được chọn |
| 15 | 06/11/2026 | Tìm/đối chiếu nguồn thứ ba cho hai conflict ORS | PASS2/2 field selection; VSDC+HOSE đơn vị quyền2024, HNX+VSDC nominal2021; event PARTIAL |
| 16 | 06/11/2026 | Tích hợp workflow đối chiếu ba nguồn offline | PASS chọn2/2 từ observation đã pin;78 test,compileall,synthetic smoke đạt; canonical0 |
| 17 | 06/11/2026 | Bổ sung HNX ex-date2021 và review tài liệu ORS còn treo | PASS scope:5/6nhóm gap đóng,8PDF/26trang,13bài triage;77test đạt/1lỗi legacy; readinessPARTIAL |
| 18 | 06/11/2026 | Hợp nhất bundle offline cho ba sự kiện ORS | PASS scope:54dòng cũ giữ nguyên,59field/27observation bổ sung/46nguồn;43test vàcompileall đạt; canonical0 |
| 19 | 06/11/2026 | Sửa đường dẫn gốc project trong hai test legacy | PASS:94/94 test,compileall,synthetic smoke; giữ nguyên assertion/runtime/evidence |
| 20 | 06/11/2026 | Kiểm kê temporal evidence ngày công bố từ cache ORS | PASS evidence scope;64nguồn/194observation/59field;2ứng viên HOSE,2021thiếu;test migration PARTIAL |
| 21 | 07/11/2026 | Tìm CafeF disclosure/CreateDate và khớp event/tài liệu | PARTIAL CreateDate0/3;3news khớp,2PDF trùngHOSE;12GET/35test vàcompileall đạt |
| 22 | 07/11/2026 | Ghi chỉ đạo timestamp-first và rà ứng viên hiện có | PASS ghi ưu tiên;8ứng viên,0publication timestamp xác minh đủ;22test/compileall đạt;canonical0 |
| 23 | 07/11/2026 | Xác minh raw metadata/decoder HOSE và tìm timestamp HNX2021 | PARTIAL:2encoding xác minh,clock công bố chưa rõ;2GET200/1TLSerror,3query Chrome;22test/compileall đạt |
| 24 | 07/11/2026 | Ghi override DATE_ONLY toàn DELTA và kiểm nguồn timestamp bổ sung | PASS ghi chỉ đạo; lookup PARTIAL,1GET200TPS/1metadata DOM VSDC;0timestamp mới đủ điều kiện |
| 25 | 07/11/2026 | Đính chính tạm ngừng DATE_ONLY chỉ corporate_actions | PASS ghi phạm vi mới D-TIME-ONLY-02/V2; financial/phần khác giữ policy đã duyệt;0network |
| 26 | 07/11/2026 | Tìm nguồn timestamp/offset và đối chiếu đúng tài liệu ORS | PARTIAL:1timestamp Stockbiz+07 cóPDF khớp;8GET/4HTTP200/3archive429;22test/compileall đạt |
| 27 | 07/11/2026 | Ghép timestamp Stockbiz và tìm thêm giờ đăng bài2021/cổ tức2024 | PASS supplement3packet,59row giữ;3timestamp nguồn khai báo/2mới,2GET200;PIT vẫnPARTIAL |
| 28 | 07/11/2026 | Review contract availability theo field, tìm nguồn GDKHQ | PASS review;proposal13mapping/46hold chờapproval;5GET/3HTTP200;22test+11negativechecks/compileall đạt |
| 29 | 07/11/2026 | Đối chiếu báo khác và archive độc lập cho timestamp | PARTIAL; archive Mekong11:18:31,2021 chưa xác nhận độc lập;11GET/22test/compileall;0activation |
| 30 | 07/11/2026 | Chuẩn bị/review proposal V2 giữ timestamp tới giây | PASS chuẩn bị;6mapping+31giây,7gap2021;0network/activation;22test+22negativeguards/compileall |
| 31 | 07/11/2026 | Tra cứu archive bài quyền mua2021 theo URL dài/ngắn/mobile | PARTIAL/DEFERRED;9GET/0capture độc lập;22test/compileall;giữproposal |
| 32 | 07/11/2026 | Tìm timestamp thông báo gốc HNX/TPS quyền2021 | PARTIAL;rawHNX390773 khớp9field,chưa cópublicationclock;9HTTP/22test/compileall |
| 33 | 07/11/2026 | Xác minh directlive article–PDF binding quyền2024 | PASS binding11field;3GET/3HTTP200;22test+14negativechecks/compileall;0admission |
| 34 | 07/11/2026 | Chuẩn bị/review V3 cho 11 mapping quyền 2024 bổ sung | PASS chuẩn bị;24 candidate/35 hold;22 test+33 negative checks/compileall;0 activation |
| 35 | 07/11/2026 | Tìm một nguồn khác đối chiếu giờ quyền2024 | PARTIAL;TNCK17:36:15,không khớp14:51;1GET/17query/22test/compileall;0approval |
| 36 | 07/11/2026 | Đối chiếu thêm nguồn FUNAN quyền2024 | PARTIAL;đúngPDFURL nhưng thiếupublicationtime;1GET/7query/22test/compileall |
| 37 | 07/11/2026 | Tìm bản tin Vietstock gắn PDF quyền2024 | PARTIAL/DEFERRED;1GET403/9query;chưa cóclock;22test/compileall |
| 38 | 08/11/2026 | Xác minh clock HOSE1614236 và historicalsource | PARTIAL/OPEN;capturehomepage tìmđược,replay3lần429;12request/22test/compileall;0instantselected |
| 39 | 08/11/2026 | Resume Wayback và đối chiếu Common Crawl homepage HOSE | PARTIAL/OPEN;429;WARC hợp lệ chỉ chứa chuyển hướng;4request/22test/compileall;1489pin giữ nguyên |
| 40 | 08/11/2026 | Tìm public historical publication-clock contract HOSE | PARTIAL/OPEN;15query/4GET200;FAQ/terms rỗng,PDFscan review có giới hạn;22test/compileall,1535pin giữ nguyên |
| 41 | 08/11/2026 | Lookup FireAnt và thêm VNDIRECT theo owner | PARTIAL;FireAnt14:51+07/directPDF khớpHOSE;VNDIRECT_API403;8request/16query/22test/compileall,1584pin giữ nguyên |
| 42 | 08/11/2026 | Áp owner-approved FireAnt timestamp cho đúng11field pilot | PASS scope;overlay59row:11ADMITTED/48DEFERRED;69test/compileall/synthetic đạt;0network/DATE_ONLY/canonical |
| 43 | 08/11/2026 | Review riêng13candidate timestamp TNCK2021/Mekong2024 | PASS review;7+6row chờ quyếtđịnh riêng,0newadmission;37test/compileall,1676pin giữ nguyên |
| 44 | 11/11/2026 | Áp owner-approved TNCK7/Mekong6 bằng overlay V2 | PASS;24ADMITTED/35DEFERRED;11FireAnt/35held byte-preserved;89test/compileall/synthetic,0network |
| 45 | 12/11/2026 | Kiểm kê giờ công bố và lần sửa đổi của 35 trường ORS | PASS kiểm kê. Còn 35 trường chờ, 0 timestamp mới. 22 kiểm thử và compileall đạt |
| 46 | 12/11/2026 | Tra giờ đăng cho hai ngày quyền mua ORS 2021 | PARTIAL. Tìm thấy bản lưu TPS 769, lượt mở trả 429. Hai trường vẫn chờ |
| 47 | 12/11/2026 | Thử lại bản lưu TPS 769 và tra thông báo HNX về kết quả 2021 | PARTIAL. Hai giờ đăng HNX khớp tệp đính kèm, múi giờ còn chờ. Wayback trả 429 |
| 48 | 12/11/2026 | Đối chiếu giờ đăng UPCoM với `pubDate` của RSS HNX | PARTIAL. Khớp 3 ID tháng 11/2026 với offset `+07:00`. Hai bài ORS 2021 còn chờ |
| 49 | 12/11/2026 | Tra RSS HNX tháng 08/2021 và tài liệu kỹ thuật công khai | PARTIAL. Hai bài ORS năm 2021 vẫn chờ bằng chứng múi giờ |
| 50 | 12/11/2026 | Tra giờ công bố TPS 858 và Nghị quyết 11 | PARTIAL. Công văn xác nhận ngày đăng, CafeF chỉ có `dateModified` kèm offset |
| 51 | 12/11/2026 | Tra TPS 2004, HOSE 1688391 và PDF Nghị quyết 05 | PARTIAL. Tìm được đúng bài HOSE và PDF, còn chờ xác minh cách diễn giải `postedDate` |

## Bước 01 — chuyển bộ thu thập sang nhánh Indicators

**Mục tiêu:** đưa bộ thu thập corporate actions từ `m3-backtest@8827ebf` sang
`feature/indicators-v1`, tái dùng preparation và dữ liệu đã freeze.

**Kết quả theo hồ sơ stage:**

- Đối chiếu 438 file chuyển sang với source branch; 89 runtime hash và 91 protected
  code/config hash khớp. Dữ liệu local tiếp tục ở đường dẫn cũ.
- V6 `--check` đạt `OFFLINE_CHECK_PASS`: kiểm 24.585 raw file đã freeze, tái dùng
  616 checkpoint; còn 456 query trong scope và ORS HOLD tại mốc đó.
- Bộ kiểm thử corporate actions báo 397 test, gồm một integration Windows opt-in
  skip; compileall và synthetic smoke đạt.
- Kiểm tra offline có 0 request nguồn và không mở browser.

Evidence: [hồ sơ kiểm tra chuyển nhánh](../tmp/ca_branch_transfer_20261104_v1/).
Việc chuyển nhánh thuộc lịch sử ngày 04/11; các stage ORS sau đó không đổi nhánh.

## Bước 02 — sửa supervisor V7

**Sự cố:** V6 preflight đạt nhưng worker coi thư mục vừa do supervisor tạo là một
run cũ chưa seal. Run `run-20261104T040725938706Z` chưa tạo state hoặc gửi request nguồn.

**Kết quả theo hồ sơ stage:**

- Lưu nguyên folder và lock sự cố; xác minh hai process PID 27236 và 27440 đã thoát.
- Supervisor V7 ghi audit/pause vào metadata riêng, để worker tự tạo run directory
  sau history check. Worker, preparation và runtime V6 giữ nguyên byte.
- CLI hiện hành: `scripts/corporate_actions/collect_vsdc_recovery_supervisor_v7.py`.
- Báo cáo kiểm thử: 30 targeted tests, gồm một opt-in skip; compileall và synthetic
  smoke đạt. Đối chiếu 91 runtime hash, 83 preparation file và prefix 616 query đạt.
- Có 0 request VSDC thật trong kiểm thử; không lặp việc kiểm 24.585 file đã freeze.

Evidence: [sự cố đã lưu](../data/corporate_actions/work/vsdc_supervisor_v7_incident_review_20261104_v1/)
và [hồ sơ kiểm tra supervisor V7](../tmp/ca_supervisor_v7_20261104_v1/).

## Bước 03 — review offline phiên V7

**Run được review:** `run-20261104T041619408451Z`.
**Kết luận:** `PASS_OFFLINE_SCOPED_LIST_REVIEW_ORS_HOLD`.

- Review đủ 1.072/1.072 query trong scope, qua 54 batch.
- Đối chiếu SHA-256 của 43.883 tệp trong ZIP và 616 checkpoint nhập với seed đã review.
- Parse lại 1.225 trang của 456 query mới, kiểm ZIP con, ledger, budget và tiến độ.
- Phát hiện 9.278 ID bài mới; tổng ID danh sách đã biết tăng từ 40.295 lên 49.573.
- Run có 27.731 reusable detail ID. Đây là số liệu cache của run, không phải chứng
  nhận đầy đủ sự kiện lịch sử hoặc đủ detail của từng query.
- Review chỉ đọc ZIP, có 0 request VSDC; không áp dụng canonical/PIT/identity.

**ORS tại bước này:** quan sát 80/85 ID; trang 5 trả HTTP200, body 33 byte và không
có vùng danh sách. Giữ `HOLD_SOURCE_COUNT_GAP`, không kết luận nguồn chỉ có 80 bài.

Evidence: [review V7](../data/corporate_actions/work/vsdc_v7_offline_review_20261106_v1/review.json).

## Bước 04 — chẩn đoán ORS bằng Chrome ẩn

**Run:** `run-20261106T012817260681Z`.
**Kết luận:** `PARTIAL_QUERY_HOLD_REVIEW_REQUIRED`.

- Giới hạn phiên ở tối đa năm request danh sách; thực tế dừng sau request đầu tiên.
- GET trang 1 nhận HTTP200 với body 0 byte. DOM không có vùng danh sách, selector timeout.
- Chưa xác minh được trang nào trong phiên mới và chưa tới trang 5.
- Seal ZIP, giải phóng lock; giữ nguyên evidence phản hồi rỗng.
- Hồ sơ stage ghi 14 test liên quan, compileall và synthetic smoke đạt; đã kiểm ZIP,
  manifest và ledger.

Evidence: [thư mục run chẩn đoán](../data/corporate_actions/work/vsdc_ors_gap_diagnostic_v1/run-20261106T012817260681Z/).
Không dùng kết quả phiên này để kết luận nguồn thiếu bài; chuyển sang quan sát Chrome thường.

## Bước 05 — đối chiếu danh sách ORS trên Chrome thường

**Kết luận:** `PASS_ORS_PUBLIC_BROWSER_LIST_RECONCILIATION`.

- Quan sát đủ năm trang của cùng query ORS: 85 ID khác nhau trên 85 bản ghi nguồn báo.
- Trang 1–4 khớp đúng thứ tự 80 ID cũ; trang 5 bổ sung `21128`, `16287`, `9509`,
  `7739`, `5416`. Số slot danh sách chưa quan sát giảm từ 5 xuống 0.
- Evidence là quan sát danh sách rendered trên Chrome; không có HTTP receipt hoặc
  raw HTML cho quan sát danh sách này.
- Không sửa trạng thái/hashes của hai phiên cũ trả body rỗng; không áp dụng canonical.

Evidence: [review danh sách 85 ID](../data/corporate_actions/work/vsdc_ors_browser_list_review_20261106_v1/review.json).

## Bước 06 — review nội dung năm bài trang cuối

**Kết luận:** `PASS_ORS_FIVE_DETAIL_CLASSIFICATION`.

| ID | Loại họp | Ngày đăng ký cuối cùng | Lịch họp dự kiến đọc được |
| --- | --- | --- | --- |
| 21128 | Thường niên | 27/05/2014 | 25/06/2014 |
| 16287 | Thường niên | 06/05/2013 | 28/05/2013 |
| 9509 | Thường niên | 23/03/2012 | 26/04/2012 |
| 7739 | Bất thường | 03/11/2011 | 26–30/11/2011 |
| 5416 | Thường niên | 21/04/2011 | 18/05/2011 |

Cả năm là `NON_PRICE_ACTION_NOTICE`, có 0 candidate điều chỉnh giá. Mệnh giá
10.000 đồng thuộc thông tin chứng khoán; tỷ lệ 1:1 là quyền biểu quyết.
Ngày cập nhật trang được giữ riêng với ngày đăng ký cuối cùng.

Bài `9509`, `5416` ghi Tiên Phong trong header nhưng Phương Đông trong nội dung họp;
giữ cả hai nhãn, không tự promote historical identity. Tại bước này chỉ lưu fields
review; chưa lưu toàn văn hoặc HTTP raw. Khoảng thiếu toàn văn được xử lý ở bước 09.

Evidence: [review năm bài](../data/corporate_actions/work/vsdc_ors_detail_review_20261106_v1/review.json).

## Bước 07 — kiểm kê cache ORS V1

**Kết luận:** `PASS_ORS_85_DETAIL_CACHE_INVENTORY`, với 0 request nguồn.

Đối chiếu 85 ID với index raw đã pin, reusable-detail inventory V7 và năm review DOM:

| Mức evidence tại V1 | Số bài | Phân loại khi kiểm kê |
| --- | --- | --- |
| Raw + hash + GET HTTP200 receipt | 20 | 2 bài cổ phiếu, 18 bài trái phiếu |
| Fields review từ DOM | 5 | 5 bài cổ phiếu |
| Chưa có detail trong cache đã audit | 60 | 24 tiêu đề cổ phiếu, 36 tiêu đề trái phiếu |

Tổng phạm vi danh sách là 31 bài cổ phiếu và 54 bài có tiêu đề mã trái phiếu ORS*.
Phân loại từ tiêu đề chưa tự xác nhận nội dung của 60 bài thiếu detail.

Evidence: [summary V1](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v1/summary.json),
[inventory V1](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v1/article_inventory.jsonl)
và [queue V1](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v1/missing_detail_queue.json).
Index raw đã pin: `tmp/ca_cache_inventory_20261102_v4/raw_document_index.jsonl`.

## Bước 08 — bổ sung và review 24 bài cổ phiếu ORS

**Kết luận nội dung:** `PASS_ORS_24_MISSING_EQUITY_CONTENT_REVIEW`.

- Thu đúng 24/24 ID trong queue cổ phiếu qua Chrome, ưu tiên `171704`, `166577`,
  `142284`; lưu 24 toàn văn rendered text, receipt thu nhận DOM và SHA-256.
- Tái dùng hai raw cổ phiếu và năm review fields. Tổng 31 bài cổ phiếu gồm ba
  candidate điều chỉnh giá, ba cancellation và 25 thông báo không điều chỉnh giá.
- Review offline 18 raw trái phiếu: mã chi tiết khác chính xác ORS, loại chứng khoán
  là trái phiếu. 36 bài còn lại vẫn chỉ có tiêu đề tại bước này.
- Inventory V2: 20 HTTP raw + 24 rendered text + 5 fields-only + 36 thiếu detail.
  24 bài cổ phiếu được ưu tiên theo scope stage; không có yêu cầu kỹ thuật phải chia
  60 bài thiếu ban đầu thành các lượt nhỏ.

### Ba candidate được xác nhận từ nội dung

| ID | Loại sự kiện | Ngày đăng ký cuối cùng | Điều khoản |
| --- | --- | --- | --- |
| 171704 | Cổ tức cổ phiếu | 17/06/2024 | 100 cổ phiếu nhận 12 cổ phiếu mới; làm tròn xuống, phần lẻ bị hủy |
| 166577 | Quyền mua | 19/01/2024 | 1 CP nhận 1 quyền, 2 quyền mua 1 CP mới; 10.000 đồng/CP |
| 142284 | Quyền mua | 11/06/2021 | 1 CP nhận 1 quyền, 1 quyền mua 1 CP mới; 10.000 đồng/CP |

Hai đợt quyền mua đều nêu dự kiến phát hành 100.000.000 cổ phiếu.

| ID | Mã quyền mua | Chuyển nhượng quyền | Đăng ký mua/nộp tiền | Hiệu lực cấp/hủy mã quyền |
| --- | --- | --- | --- | --- |
| 166577 | MIRORS241 / VNMIRORS2418 | 05/02–04/03/2024 | 05/02–11/03/2024 | 05/02–14/03/2024 |
| 142284 | MIRORS211 / VNMIRORS2111 | 25/06–09/07/2021 | 25/06–16/07/2021 | 25/06–21/07/2021 |

Các số liệu trên là điều khoản nguồn báo, chưa phải event canonical hoặc hệ số điều chỉnh.
Chưa xác minh ex-date, chưa chứng nhận không còn revision khác.

### Các liên kết hủy và bài kế tiếp

| Bài hủy | Bài gốc khớp nội dung | Quyền/ngày bị hủy | Văn bản gốc được bài hủy dẫn |
| --- | --- | --- | --- |
| 182168 | 179241 | Họp thường niên 2025; 05/03/2025 | 176/TB-CNVSDC ngày 12/02/2025 |
| 68163 | 64007 | Họp thường niên 2020; 17/03/2020 | 177/TB-CNVSD ngày 21/02/2020 |
| 50840 | 50492 | Lấy ý kiến bằng văn bản; 25/10/2018 | 1287/TB-CNVSD ngày 09/10/2018 |

Mapping ID dựa trên mã, loại quyền và ngày đăng ký cuối cùng trong snapshot; bài
hủy không có hyperlink tới ID gốc, text bài gốc không hiển thị số thông báo.
Ba bài hủy này không hủy ba candidate cổ tức/quyền mua ở bảng trên.

`182169` (chốt 23/05/2025), `68162` (chốt 02/06/2020), `51446` (chốt 21/12/2018)
là possible successor của các nhóm tương ứng. Chưa có liên kết trực tiếp đủ để
gán supersedes/canonical revision. Bài `50492` có agenda phát hành riêng lẻ nhưng
bản thân là quyền lấy ý kiến, không phải thông báo thực hiện quyền mua.

### Kiểm tra và giới hạn

Self-review đối chiếu 53 file artifact mới và 34 input đã pin đạt; compileall,
synthetic smoke và `git diff --check` đạt. Chạy 46 targeted tests: 45 đạt, một lỗi
legacy tại `CachedReviewTests.test_runner_refuses_overwrite_and_path_escape` vì
test tìm helper ở `tests/unit/scripts/review_cached_corporate_actions26_v1.py`
không tồn tại. Không sửa hoặc giảm assertion để làm test pass.

Lần thử pytest bằng system Python thiếu module; chuyển sang unittest của repository.
Default sandbox temp không cho tạo thư mục con; chạy lại unittest với TEMP/TMP trong
workspace. Kết quả 45/46 ở trên là sau khi đã xử lý vấn đề temp.

Evidence: [review 24 bài](../data/corporate_actions/work/vsdc_ors_equity_detail_review_20261106_v1/review.json),
[summary V2](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v2/summary.json),
[self-review](../tmp/ors_equity_detail_review_20261106_v1/self_review.json)
và [kết quả kiểm tra](../tmp/ors_equity_detail_review_20261106_v1/validation.json).

## Bước 09 — hoàn tất 41 bài còn thiếu toàn văn

**Kết luận:** `PASS_ORS_REMAINING_41_FULLTEXT` và `PASS_ORS_85_FULLTEXT_INVENTORY_V3`.

- Theo yêu cầu owner, thực hiện trong một stage cả 36 bài trái phiếu còn thiếu và
  bổ sung toàn văn năm bài cổ phiếu cũ. Thu đủ 41/41 ID, lưu 41 text, 41 receipt
  thu nhận DOM và SHA-256; không gặp challenge/access control, không có bài deferred.
- Nội dung 36 bài trái phiếu xác nhận 35 thông báo trả lãi và một thông báo lấy ý
  kiến trái chủ (`186160`, mã `ORS12101`). Không coi tiền lãi trái phiếu là cổ tức
  tiền mặt của cổ phiếu ORS.
- Năm bài cổ phiếu vẫn là bốn họp thường niên/một họp bất thường. ISIN, sàn, ngày
  đăng ký cuối cùng, ngày cập nhật và lịch họp dự kiến khớp fields review cũ; giữ
  khác biệt tên Tiên Phong/Phương Đông tại `9509`, `5416`.
- Không có candidate điều chỉnh giá cổ phiếu mới từ 41 bài bổ sung.
- Tái dùng nguyên 44 record của V2 ngoài scope thu mới; tạo V3 với đủ toàn văn
  85/85 bài: 20 HTTP raw và 65 rendered text. Không còn fields-only hoặc thiếu detail.

Self-review kiểm tra 41 ID kỳ vọng, 82 tệp capture mới và 85 tham chiếu evidence.
Kiểm tra cuối đối chiếu 66 tệp baseline, 89 tệp trong hai manifest mới và 44 record
tái dùng không đổi. Compileall và `git diff --check` đạt. Không sửa runtime hoặc
pipeline nên không chạy lại batch/test/pipeline đã giữ nguyên.

Evidence: [review 41 bài](../data/corporate_actions/work/vsdc_ors_remaining_fulltext_20261106_v1/review.json),
[self-review](../data/corporate_actions/work/vsdc_ors_remaining_fulltext_20261106_v1/self_review.json),
[summary V3](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v3/summary.json),
[queue còn lại](../data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v3/missing_detail_queue.json)
và [kiểm tra cuối](../tmp/ors_remaining_fulltext_20261106_v1/validation.json).

## Bước 10 — review ba candidate và ngày giao dịch không hưởng quyền

**Kết quả:** hoàn tất review ba hồ sơ được giao. Điều khoản/ex-date quan sát đạt
`PASS_3_OF_3`; readiness giữ `PARTIAL_EVENT_READINESS_REVISION_ARCHIVE_NOT_CERTIFIED`.

| Bài | Ex-date đọc được | Ngày đăng ký cuối cùng | Nguồn và mức evidence |
| --- | --- | --- | --- |
| 171704 | 14/06/2024 | 17/06/2024 | PDF HOSE ngày 10/06/2024 từ host HOSE; raw + GET200 receipt + hash |
| 166577 | 18/01/2024 | 19/01/2024 | PDF HOSE 79 ngày 15/01/2024, copy trên Vietstock; raw + GET200 receipt + hash |
| 142284 | 10/06/2021 | 11/06/2021 | Công bố doanh nghiệp postId 769, text DOM + receipt thu nhận + hash; PDF VSDC 950 đối chiếu điều khoản |

Đã đọc toàn bộ bảy trang của ba PDF bằng ảnh render vì PDF không có text layer
đọc được. Cổ tức dự kiến phát hành 36.000.000 cổ phiếu; hai quyền mua dự kiến mỗi
đợt 100.000.000 cổ phiếu, giá 10.000 đồng/CP. Tỷ lệ và lịch chuyển nhượng/đăng ký
mua khớp text VSDC đã lưu. Các số lượng là dự kiến, không đổi thành lượng thực phát hành.

PDF VSDC 950/TB-CNVSD ngày 01/06/2021 xác nhận mã ORS, ISIN, mã quyền MIRORS211,
tỷ lệ 1:1, giá và lịch quyền; không nêu ex-date. Nguồn ex-date là nội dung HTML
doanh nghiệp, không phải suy ngày liền trước. PDF HOSE 79 có chữ ký/dấu nhìn thấy
nhưng host tải là Vietstock; chưa có byte match với bản trên host HOSE, chưa kiểm
chữ ký số. Ghi đúng giới hạn nguồn, không tự đặt source priority.

Review cache 31 bài cổ phiếu loại trừ 54 bài trái phiếu theo evidence định danh;
không thấy revision trực tiếp của ba candidate trong scope. Ba bài hủy quyền
họp/lấy ý kiến không thuộc ba sự kiện giá. Các từ `điều chỉnh` ở boilerplate TVLK
và hủy cổ phiếu lẻ không được gán thành revision/hủy sự kiện.

Bổ sung hai thông báo VSDC ngoài snapshot quyền: `170753` nêu giao dịch cổ phiếu
phát hành thêm ngày 13/05/2024 cho đợt chốt 19/01/2024; `173807` nêu ngày 12/08/2024
cho cổ tức chốt 17/06/2024. Đây là evidence sau sự kiện, không phải ex-date hoặc
thông báo thay đổi lịch quyền; không tự xác nhận terminal execution đầy đủ.

Search công khai không phải chứng nhận không có revision khác. Bộ lọc công bố
doanh nghiệp quay về query rỗng, chưa quan sát được archive lọc hoàn chỉnh. Web
tool có cache-miss khi mở PDF; GET trong sandbox lỗi kết nối. Chrome đọc được
HTML và tải PDF 950; GET công khai ngoài sandbox lưu thành công hai PDF và hai
bài VSDC với HTTP200. Không dùng cookie/token, không đổi fingerprint, không gặp
challenge hoặc đăng nhập. Một download qua Chrome kéo dài khoảng 383 giây.

Evidence catalog gồm ba rendered text gốc dùng lại, bốn HTTP raw mới, hai DOM text
và một PDF tải qua Chrome không có HTTP receipt. Inventory V3, các hash cũ và 85 ID
không đổi. Không chọn available_at, không promote PIT/identity, không tính hệ số
điều chỉnh và không ghi canonical. Bộ 14 test revision, compileall đạt; không sửa
runtime/pipeline nên không chạy lại synthetic smoke hoặc batch nguồn đã hoàn thành.

Evidence: [summary stage](../data/corporate_actions/work/ors_three_event_review_20261106_v1/summary.json),
[hồ sơ cổ tức 171704](../data/corporate_actions/work/ors_three_event_review_20261106_v1/171704.event_review.json),
[hồ sơ quyền mua 166577](../data/corporate_actions/work/ors_three_event_review_20261106_v1/166577.event_review.json),
[hồ sơ quyền mua 142284](../data/corporate_actions/work/ors_three_event_review_20261106_v1/142284.event_review.json),
[catalog nguồn](../data/corporate_actions/work/ors_three_event_review_20261106_v1/source_catalog.json),
[review PDF](../data/corporate_actions/work/ors_three_event_review_20261106_v1/pdf_visual_review.json)
và [review revision](../data/corporate_actions/work/ors_three_event_review_20261106_v1/revision_review.json).

`MANUAL_REVIEW_REQUIRED` tiếp tục áp dụng cho lựa chọn nguồn/trường và freeze
canonical: config offline reconciliation giữ `automatic_field_approval=false`,
`canonical_build=false`; AGENTS yêu cầu owner review thay đổi methodology/freeze.
Stage này chỉ chuẩn bị hồ sơ để review, không kích hoạt policy mới.

## Bước 11 — bổ sung nguồn Sở, kết quả phát hành và lineage

**Phạm vi:** ba đợt đã lập hồ sơ ở bước 10; bổ sung nguồn Sở và thông báo sửa/bổ
sung/kết quả. Không thu lại 85 bài, không mở 7 mã lớn hoặc 418 mã toàn chiến dịch.

**Kết quả:**

- Tải thông báo HOSE 79 ngày 15/01/2024 trực tiếp từ host HOSE, dựa trên bài
  1614236 và API tệp đính kèm công khai. PDF gốc có SHA-256
  `364beb609427cb4b451bbffed5c2718285b9e683dd1371e2f405670f06ae7787`,
  byte khớp copy Vietstock cũ. Giữ nguyên bản và review bước 10; ex-date 18/01/2024
  nay có HTTP raw/receipt từ host gốc. API chỉ GET không xác thực.
- UBCKNN 1914 ngày 29/03/2024 dẫn giấy phép 442 và báo cáo 128 ngày 26/03, ghi
  phân phối 100.000.000 CP. UBCKNN 3994 ngày 27/06/2024 dẫn báo cáo 252 ngày
  20/06, ghi phân phối cổ tức 35.999.743 CP. Không thay số kế hoạch bằng số thực
  hiện hoặc suy ngày giao dịch từ công văn này.
- NQ05 ngày 21/03/2024: đăng ký/nộp tiền 94.919.294 CP, dư 5.080.706 CP; giá mua
  ban đầu 10.000, giá phân phối lại 11.000 đồng/CP, hạn phần dư 25/03/2024.
- NQ11 ngày 22/07/2021: bán cho cổ đông 99.122.718 CP, dư 877.282 CP; giá ban đầu
  10.000, phân phối lại 11.000 đồng/CP, hạn phần dư 15:00 ngày 23/07/2021.
  Các hạn này dành cho phần dư, không tự ghi thành revision gia hạn đợt mua gốc.
- HNX 430/2651 ngày 18/08 và 2716 ngày 23/08/2021 trên host doanh nghiệp ghi
  đăng ký bổ sung 100 triệu CP, mệnh giá tổng phần bổ sung 1.000 tỷ; tổng sau bổ
  sung 200 triệu CP/2.000 tỷ. Ngày giao dịch 99.122.718 CP tự do là 27/08/2021,
  877.282 CP hạn chế là 01/08/2022. Không dùng các ngày này làm ex-date.
- NQ17 ngày 22/11/2023 dẫn NQ11 ngày 03/08/2023 và thay rõ Điều 4 bằng Điều 2
  về ủy quyền; bổ sung kế hoạch sử dụng vốn. Đã đọc đủ ba trang; không thấy thay
  record date/ex-date/giá/tỷ lệ/lịch mua trong nội dung nghị quyết này.
- Đính chính postId 1849 sửa thông tin trái phiếu **ORSH2328001**, được xác nhận
  từ HTML và PDF, loại khỏi sự kiện cổ phiếu. PostId 1225 hoãn đợt 2022 tăng vốn
  lên 4.000 tỷ, khác đợt 2021 lên 2.000 tỷ; không nối nhầm cancellation.

**Phạm vi revision đã quan sát:** 110 tiêu đề trên hai khoảng trang liên tiếp
(trang yêu cầu 8–13 và 19–23), bracket các khoảng 01/08/2023–31/08/2024 và
01/04/2021–01/09/2021. Ba bộ lọc quyền mua/cổ tức/phát hành lưu đủ 21/4/59 ID theo
snapshot của từng query. Một lượt page=1 lặp page=0 được giữ evidence và loại khỏi
đếm. Đây là title screening và review các detail/PDF được chọn, không phải đọc
mọi body của 413 bài. Chưa chứng nhận vắng sửa/hủy/gia hạn toàn lịch sử.

**Các khác biệt cần review:**

- HTML postId 924 ghi giá trị danh nghĩa bổ sung 2.000 tỷ cho 100 triệu CP, trong
  khi PDF HNX phân biệt 1.000 tỷ bổ sung và 2.000 tỷ tổng. Giữ cả hai observation;
  không tự chọn source priority hoặc sửa HTML evidence.
- NQ11/2023 trang 1–2 diễn đạt hai CP cũ nhận một quyền, một quyền mua một CP mới;
  VSDC sau đó diễn đạt đơn vị quyền khác. Tỷ lệ kinh tế CP cũ:mới cùng 2:1; chưa
  tự đồng nhất đơn vị quyền hay gán formal correction khi chưa có thông báo rõ.

**Evidence và kiểm tra:** 69 receipt gồm 65 GET200, hai lỗi transport, một 301 và
một 404; một body bổ sung chưa receipt do lỗi stdout encoding được giữ riêng,
không gán HTTP200, rồi GET lại bằng key mới. Tổng 70 lần GET; accounting ghi rõ
lệch một request do guard đếm receipt thay vì attempt. Không còn request tiếp.
14 PDF có receipt; đọc hình ảnh đủ 27 trang của 13 PDF mới, tái dùng review hai
trang HOSE cũ bằng byte match. Receipt ghi đúng media type; đuôi `.html` cũng có
JSON/JS. Hash áp dụng entity body đã decode HTTP content encoding, không phải
compressed wire bytes. Không kiểm chứng chữ ký số bằng mật mã.

Pin/đối chiếu 42 input của stage trước, kiểm lại các raw/hash/receipt mới;
14 test revision và compileall đạt. Không sửa runtime/pipeline nên không chạy
lại synthetic smoke. Snapshot V3 vẫn 20 raw + 65 DOM; 65 GET200 mới ở đây là
request nguồn bổ sung (gồm list/API/PDF), không phải relabel 65 DOM thành raw.

**Trạng thái:** review có giới hạn hoàn tất; readiness
`PARTIAL_HNX_EXDATE_AND_UNCERTIFIED_GLOBAL_REVISION_COVERAGE`.
Direct GET một PDF giao dịch bổ sung trên HNX lỗi kiểm chứng TLS; không tắt TLS
verification. Thông báo HNX xác nhận ex-date 10/06/2021 vẫn thiếu; HTML doanh
nghiệp postId 769 vẫn là chứng cứ ex-date đã đọc trực tiếp. Một số PDF hỗ trợ
khác mới title/HTML review, liệt kê rõ trong lineage. Không ghi canonical, hệ số
điều chỉnh, available_at hoặc promote PIT/identity.

Evidence: [summary bước 11](../data/corporate_actions/work/ors_three_event_lineage_supplement_20261106_v1/summary.json),
[đối chiếu nguồn Sở](../data/corporate_actions/work/ors_three_event_lineage_supplement_20261106_v1/exchange_source_reconciliation.json),
[lineage và các gap](../data/corporate_actions/work/ors_three_event_lineage_supplement_20261106_v1/lineage_review.json),
[review PDF](../data/corporate_actions/work/ors_three_event_lineage_supplement_20261106_v1/pdf_visual_review.json),
[archive title review](../data/corporate_actions/work/ors_three_event_lineage_supplement_20261106_v1/issuer_archive_review.json)
và [accounting thu thập](../data/corporate_actions/work/ors_three_event_lineage_supplement_20261106_v1/acquisition_accounting.json).

**Bước tiếp theo đề xuất:** lập packet quyết định offline, bảng từng field/nguồn
cho ba sự kiện, giữ riêng discrepancy đơn vị quyền/giá trị bổ sung và các gap
HNX/revision. Owner review trước lựa chọn field/source hoặc freeze canonical
(`MANUAL_REVIEW_REQUIRED` theo AGENTS và config tắt automatic approval).

## Bước 12 — lập packet quyết định offline cho ba sự kiện

**Mục tiêu:** chuyển hồ sơ bước 10–11 thành bảng có thể review và quyết định cụ
thể, dùng lại evidence đã seal. Stage chỉ lập packet, không chọn thay owner hoặc
coi yêu cầu thực hiện là phê duyệt source/field/canonical.

**Đã làm:**

- Pin và kiểm lại 441 input từ các manifest bước 10–11, inventory V3, input
  evidence đã tham chiếu và config offline hiện hành. Không sửa các version cũ.
- Lập 54 dòng field cho ba sự kiện: giá trị quan sát, loại phạm vi, nguồn hỗ trợ,
  JSON pointer hoặc câu nguồn để truy ngược, điểm cần review và mã quyết định.
  Có 22 nguồn được tham chiếu trong packet, mỗi nguồn có path/hash/receipt và
  loại evidence đúng như đã lưu; DOM/PDF không có HTTP receipt không gán HTTP200.
- Tách điều khoản gốc, số lượng kế hoạch, số lượng kết quả, phân phối lại phần dư
  và ngày giao dịch cổ phiếu bổ sung. Không ghi đè giá 10.000 bằng 11.000 đồng/CP,
  không đổi ngày giao dịch bổ sung thành ex-date.
- Soạn sáu quyết định có phương án và đề xuất: **D01** bộ điều khoản/phạm vi;
  **D02** ex-date 2021 từ nguồn doanh nghiệp; **D03** đơn vị quyền 2024;
  **D04** giá trị danh nghĩa bổ sung 2021 giữa HTML/PDF; **D05** phạm vi revision
  và readiness; **D06** liên kết kết quả có dẫn nguồn rõ hoặc chỉ corroborated.
- Giữ toàn bộ `owner_decision`, `selected_option`, `approved_value` là null;
  `selected_source_ids` rỗng, `applied=false`. JSON mang nhãn REVIEW_ONLY, không
  đưa vào runtime decision/config. Đề xuất bộ PDF HNX ở D04 chưa phải source
  priority đã áp dụng. Phương án D02 vẫn ghi rõ provenance doanh nghiệp/gap HNX.
- Liệt kê các gate chưa mở: full-history revision, publication/available_at,
  historical security identity, canonical freeze và price adjustment. Giữ danh
  sách 13 title hỗ trợ và bốn nhóm attachment/body còn thiếu review từ bước 11.

**Kết quả:** `PASS_PACKET_PREPARATION`; readiness của cả ba sự kiện tiếp tục
`PARTIAL_MANUAL_REVIEW_REQUIRED`. Gửi **0 request nguồn**, không chạy batch hoặc
thu lại 85 bài. Các số 54/22/6 là dòng field/nguồn/quyết định của packet, không
phải số bài ORS mới. Snapshot vẫn đủ 85/85 toàn văn, 0 bài thiếu.

**Kiểm tra:** đối chiếu giá trị từng dòng với observation/JSON pointer đã pin;
kiểm source hash, receipt path, link Markdown và các trường approval chưa chọn;
14 test revision và `python -m compileall -q src tests scripts run.py` đạt.
Không sửa production code/pipeline nên không chạy lại synthetic smoke. Script
one-off lập packet được lưu cùng artifact để tái kiểm tra, không dùng làm runtime.
Không đổi policy/config, không tính hệ số, không áp dụng canonical hoặc PIT/identity.

Evidence: [packet dễ đọc](../data/corporate_actions/work/ors_three_event_decision_packet_20261106_v1/ORS_DECISION_PACKET.md),
[bảng field](../data/corporate_actions/work/ors_three_event_decision_packet_20261106_v1/field_matrix.json),
[sáu quyết định](../data/corporate_actions/work/ors_three_event_decision_packet_20261106_v1/decision_requests.json),
[danh mục nguồn](../data/corporate_actions/work/ors_three_event_decision_packet_20261106_v1/source_index.json)
và [gate chưa mở](../data/corporate_actions/work/ors_three_event_decision_packet_20261106_v1/readiness_gates.json).

**Bước tiếp theo đề xuất:** owner review D01–D06 trong packet; khi giao stage ghi
nhận, ghi đúng những lựa chọn rõ ràng thành version mới, giữ mục chưa quyết định
unresolved. Không tự freeze canonical hoặc mở nhóm 7/418 mã. Căn cứ approval là
[AGENTS.md](../AGENTS.md): “phải ghi rõ `MANUAL_REVIEW_REQUIRED` và STOP khi cần
approval”; [config offline](../configs/data/corporate_actions/corporate_actions_offline_reconcile_v1.json)
vẫn giữ `automatic_field_approval=false`, `canonical_build=false`.

## Bước 13 — chuẩn bị quy tắc ủy quyền agent tự review

**Yêu cầu:** owner không muốn tự đọc/duyệt từng bài sau crawl. Stage này chuẩn bị
một bộ quy tắc cụ thể để chấp thuận một lần, không diễn giải yêu cầu soạn quy tắc
thành phê duyệt policy hoặc áp dụng canonical.

**Đã làm:** lập CA-REVIEW-DELEGATION-V1 với 12 quy tắc và config đề xuất inactive,
12 tình huống hành vi kỳ vọng, mapping sáu quyết định của packet bước 12, input
manifest và self-review. Tách rõ agent review kỹ thuật, pipeline deterministic
chưa triển khai và các gate canonical/research còn đóng.

- Field được nguồn chính thức nêu rõ, đúng security/event/scope và evidence
  hợp lệ, không có conflict cùng field thì agent tự kết luận technical review.
- Ngày do doanh nghiệp nêu trực tiếp được đề xuất chấp nhận có provenance doanh
  nghiệp/gap Sở, không suy từ record date hoặc gắn exchange-confirmed. Đây là
  acceptance đề xuất mới, chưa áp dụng cho ex-date ORS 2021 trong stage này.
- Thiếu dữ liệu hoặc cùng field có conflict thì giữ unresolved; agent tự tìm
  chứng cứ khi được giao và báo ảnh hưởng, không buộc owner đọc PDF/chọn nguồn.
  Không ưu tiên PDF/Sở chỉ vì định dạng/tác giả; D04 dự kiến giữ conflict chứ
  không áp đề xuất chọn PDF từ packet cũ.
- Phân biệt số kế hoạch/kết quả, giá quyền gốc/phần dư, ex-date/ngày giao dịch CP
  bổ sung và explicit/corroborated lineage. PASS coverage chỉ đúng snapshot/query.
- Exception mặc định `owner_action_required=false`. Chỉ xin quyết định khi cần
  đổi methodology, phạm vi hoặc final freeze thật sự; không hỏi owner giải ngoại
  lệ dữ liệu thông thường. Giữ single-agent và dừng sau stage được giao.

**Đính chính cách yêu cầu review trước đó:** D01–D06 là hồ sơ các vấn đề kỹ thuật,
không phải sáu việc owner bắt buộc làm. Agent phải kiểm chứng dữ liệu và tự giữ
điểm chưa đủ evidence. AGENTS không yêu cầu owner đọc từng bài; approval bắt buộc
áp dụng khi thay methodology/freeze cần quyết định, và config hiện hành vẫn tắt
tự phê duyệt field/canonical. Việc soạn quy tắc không thay các ranh giới đó.

**Kết quả:** `PASS_PROPOSAL_PREPARATION`; proposal giữ
`PROPOSED_MANUAL_REVIEW_REQUIRED`, `active=false`, approval null. Không sửa 54 field
hoặc quyết định D01–D06, không chạy acquisition/batch hay tính factor/canonical.
Snapshot ORS giữ nguyên 85/85 bài, 0 thiếu toàn văn. Design case chỉ là đặc tả
expected behavior, không ghi thành test engine đã thực thi.

**Kiểm tra:** hash của input evidence/config, JSON/ID/tham chiếu quy tắc,
inactive/approval-null guards, link Markdown và các giới hạn ủy quyền; 14 test
revision và compileall đạt. Không đổi production code/pipeline nên không chạy
lại synthetic smoke. Config đề xuất nằm trong artifact, không cài vào runtime.

Evidence: [quy tắc dễ đọc](../data/corporate_actions/work/ors_review_delegation_proposal_20261106_v1/QUY_TAC_UY_QUYEN_REVIEW.md),
[config đề xuất inactive](../data/corporate_actions/work/ors_review_delegation_proposal_20261106_v1/policy_proposal.json),
[tác động dự kiến tới D01–D06](../data/corporate_actions/work/ors_review_delegation_proposal_20261106_v1/ors_impact_assessment.json)
và [các tình huống kỳ vọng](../data/corporate_actions/work/ors_review_delegation_proposal_20261106_v1/design_cases.json).

**Bước tiếp theo đề xuất:** owner chấp thuận nguyên gói CA-REVIEW-DELEGATION-V1,
không cần trả lời từng D01–D06. Sau đó giao stage agent áp dụng cho 54 field ORS,
xuất kết quả đạt/unresolved và tác động. Không tự chạy stage sau, mở pipeline
deterministic hoặc canonical. Lý do cần phê duyệt: acceptance/ủy quyền mới đang là
đề xuất; AGENTS giữ `MANUAL_REVIEW_REQUIRED` trước thay methodology/freeze khi cần,
config offline hiện tại giữ hai cờ automatic approval/canonical tắt.

## Bước 14 — ghi nhận chỉ đạo đối chiếu nguồn thứ ba

Owner chỉ định: hai nguồn tài liệu cho kết quả khác nhau thì tìm nguồn thứ ba;
nếu nguồn thứ ba giống một trong hai nguồn đầu thì chọn. Đây là authorization
cho quy tắc xử lý conflict, không phải phê duyệt ngầm toàn bộ ủy quyền V1 hoặc
final canonical. Không yêu cầu owner duyệt lại quy tắc đã chỉ định.

**Đã làm:** tạo CA-THIRD-SOURCE-V1, delegation policy V2 kế thừa V1 với component
conflict resolution được ghi owner-directed; owner approval phần general delegation
vẫn null và runtime inactive. V1, 54 field, D01–D06 và inventory giữ nguyên.

- A=x, B=y, C=x → chọn x, lưu A+C hỗ trợ và B bất đồng; C=y thì chọn y, lưu B+C
  và A bất đồng. C thiếu/không đủ điều kiện hoặc C=z khác cả hai thì unresolved.
- So đúng field/đơn vị/security/event/semantic scope/hiệu lực. Không trộn giá
  quyền gốc với phần dư, tỷ lệ kinh tế với đơn vị quyền, bổ sung với tổng.
- C có tài liệu/provenance riêng; cùng PDF đăng hai host không tính hai nguồn.
  Không bắt buộc khác publisher chỉ theo tên; cần xác định nguồn gốc và quan hệ
  sao chép/trích dẫn. Chưa rõ độc lập thì chưa đủ điều kiện xác nhận.
- Kiểm revision trước khi đếm xác nhận; không phủ một sửa đổi rõ bằng hai bản cũ.
  Giữ mọi evidence đã biết và thứ tự tìm; không chọn lọc hoặc tìm nguồn thứ tư
  chỉ để ép ra đa số mong muốn khi nguồn thứ ba đủ điều kiện khác cả hai.
- Selection receipt ghi comparison key, value, ba nguồn, cặp hỗ trợ/nguồn bất
  đồng, assessment nguồn gốc, locator/receipt/hash và scope. Kết luận field vẫn
  không tự freeze canonical hoặc mở PIT/historical identity/price factor.

**Kết quả:** `PASS_RULE_RECORDING`, component có trạng thái
`OWNER_DIRECTED_RULE_RECORDED`; 0 request nguồn, 0 field ORS mới được chọn. Hai
conflict đơn vị quyền 2024/giá trị danh nghĩa bổ sung 2021 chưa được giải quyết.
Tám design case là hành vi kỳ vọng, không phải test engine được triển khai.

**Kiểm tra:** input hash, approval theo component, giữ general approval null,
runtime/canonical false, tham chiếu JSON/Markdown và các artifact cũ; 14 test
revision và compileall đạt. Không đổi production code/pipeline nên không chạy
lại synthetic smoke. Không sửa hash/policy version cũ hoặc chạy lại batch.

Evidence: [quy tắc dễ đọc](../data/corporate_actions/work/ors_third_source_rule_20261106_v1/QUY_TAC_NGUON_THU_BA.md),
[quy tắc máy đọc](../data/corporate_actions/work/ors_third_source_rule_20261106_v1/third_source_rule.json),
[delegation V2](../data/corporate_actions/work/ors_third_source_rule_20261106_v1/delegation_policy_v2.json)
và [tình huống kỳ vọng](../data/corporate_actions/work/ors_third_source_rule_20261106_v1/design_cases.json).

**Bước tiếp theo đề xuất:** trong stage ORS được giao, tìm nguồn thứ ba cho hai
conflict, kiểm tính tương đương và nguồn gốc rồi chọn/giữ unresolved theo quy tắc.
Không xin lại approval cho CA-THIRD-SOURCE-V1, không giao owner đọc PDF hoặc tự
chạy stage kế tiếp/canonical/nhóm 7/418 mã.

## Bước 15 — chọn hai field bằng nguồn thứ ba

**Phạm vi:** áp CA-THIRD-SOURCE-V1 cho hai conflict đã biết, không thu lại85 bài
hoặc chạy campaign. Không yêu cầu owner duyệt lại rule/case đã đủ điều kiện.

**Kết quả `PASS_2_OF_2_FIELD_SELECTIONS`:**

| Field | Nguồn bất đồng giữ lại | Cặp nguồn xác nhận | Giá trị review được chọn |
| --- | --- | --- | --- |
| Đơn vị quyền mua đợt19/01/2024 | NQ11/2023: hai CP cũ nhận một quyền/một quyền mua một CP mới | VSDC166577 và HOSE79 ngày15/01/2024 | Một CP cũ nhận một quyền; hai quyền mua một CP mới |
| Giá trị danh nghĩa100 triệu CP bổ sung2021 | HTML doanh nghiệp924:2.000 tỷ phần bổ sung | HNX430 ngày18/08/2021 và VSDC143656/GCN152-5 ngày02/08/2021 | 1.000.000.000.000 VND phần bổ sung;2.000 tỷ là tổng sau bổ sung |

Đã đọc hình ảnh hai trang PDF HOSE gốc bằng byte match với ảnh copy đã pin.
HOSE79 có số/thời điểm/letterhead/người ký riêng, không là bản repost NQ11/VSDC;
copy Vietstock không tính thêm nguồn. Độc lập kiểm ở origin văn bản, không claim
hai cơ quan audit độc lập dữ kiện nền cùng corporate action. Chọn cách ghi đơn
vị operational cho đợt2024, không sửa NQ11/2023 hoặc chứng nhận đã có văn bản
đính chính chính thức nghị quyết sớm này.

Nguồn C nominal2021 là thông báo đăng ký riêng do VSDC phát hành, nêu trực tiếp
giá trị, có ngày trước HNX430; không suy từ phép nhân số CP/mệnh giá. Match tranche
theo ORS/ISIN,100 triệu bổ sung/200 triệu tổng và lịch registry/trading2021.
Profile619 xác nhận GCΝ152-5/ngày/số lượng; VSDC144117 dẫn HNX2716 và ngày giao
dịch27/08/2021, dùng làm linkage, không tính phiếu vì nó dẫn HNX.

**Acquisition:** public search tìm profile619; GET200 profile nhưng POST phân
trang công khai trả400/body rỗng. Giữ receipt lỗi rồi dùng Chrome thường click
issuer-news pages2–3, thấy143656 và đọc body. Lưu ba DOM text/capture receipt/hash
(hai list region, một article body), không gán HTTP status/header. GET riêng
143656 và144117 đều200: tổng bốn request HTTP trực tiếp gồm ba200/một400, không
có raw bị thiếu receipt. Text raw143656/DOM khớp sau chuẩn hóa khoảng trắng,
vẫn giữ hai cơ chế riêng. Không gặp challenge/access control hoặc dùng cookie/
token/fingerprint/TLS bypass. Không download PDF mới hoặc chạy lại batch.

143656 không nằm trong snapshot truy vấn thực hiện quyền85 ID trước đó; đây là
nguồn hậu kiểm bổ sung ngoài scope query ấy. Không sửa inventoryV3 hoặc tuyên bố
đủ mọi tin ORS.85/85 toàn văn và20raw/65DOM trong snapshot vẫn nguyên.

**Đính chính extraction:** raw post869 đã có body trong public SSR JSON nhúng,
trước đây phép lấy visible text bỏ script nên review chưa đọc được phần này.
Đã trích riêng có parent hash/JSON pointer/receipt dẫn về raw cũ, không relabel
DOM hoặc PDF mới. Body dẫn SSC4122 ngày29/07/2021, phân phối100 triệu CP; tiền thu
1.000.877.282.000 đồng là field proceeds, không so cùng nominal value hoặc dùng
làm phiếu thứ ba. Chưa lấy được PDF công văn kết quả.

**Artifacts:** hai selection receipt ghi comparison key, source A/B/C và value,
cặp support/dissent, origin assessment, locator/hash, scope tìm, thứ tự tìm và
revision caveat. Review overlay mới giữ nguyên54 field/decision packet cũ.
Không ghi canonical/factor/available_at, promote PIT/identity hoặc claim full
historical revision coverage. Readiness event tổng thể vẫn PARTIAL do các gate
khác, gồm HNX ex-date2021 còn thiếu.

**Kiểm tra:**485 input pin, source raw/hash/receipt, ba DOM capture, exact text
locator VSDC/issuer, PDF visual evidence, value matching và dissent preservation;
14 test revision và compileall đạt. Không đổi production code/pipeline nên không
chạy lại synthetic smoke. Bảo toàn rule/config và tất cả evidence/version cũ.

Evidence: [kết quả dễ đọc](../data/corporate_actions/work/ors_third_source_resolution_20261106_v1/KET_QUA_DOI_CHIEU.md),
[selection đơn vị quyền](../data/corporate_actions/work/ors_third_source_resolution_20261106_v1/ORS_2024_RIGHTS_UNITS.selection_receipt.json),
[selection nominal](../data/corporate_actions/work/ors_third_source_resolution_20261106_v1/ORS_2021_ADDITIONAL_NOMINAL.selection_receipt.json),
[review overlay](../data/corporate_actions/work/ors_third_source_resolution_20261106_v1/field_selection_overlay.json)
và [catalog nguồn](../data/corporate_actions/work/ors_third_source_resolution_20261106_v1/source_catalog.json).

**Bước tiếp theo đề xuất:** tích hợp rule nguồn thứ ba và selection receipt vào
workflow đối chiếu offline version mới có tests; giữ canonical/PIT/identity tắt.
Chưa triển khai pipeline deterministic hoặc tự mở stage nhóm7/418 mã.

## Bước16 — triển khai và chạy workflow đối chiếu ba nguồn offline

**Yêu cầu:** đưa quy tắc và selection receipt vào đối chiếu offline có kiểm thử,
đồng thời giải thích rõ hai nguồn đang ghi khác nhau và nguồn thứ ba là nguồn nào.
Chỉ stage này, giữ nhánh feature/indicators-v1/single-agent, không đổi version cũ.

**Đã triển khai:** module
`src/delta_t1/ingestion/corporate_actions/third_source_reconcile.py`, CLI
`scripts/corporate_actions/reconcile_third_source_v1.py`, config
`configs/data/corporate_actions/third_source_reconcile_ors_v1.json`,29 test mới.
Logic trong ingestion, script chỉ điều phối; không đổi core reconcile/revision cũ.

- Nhận source A/B/C observations có review locator và pin. Kiểm authorization
  CA-THIRD-SOURCE-V1, config/case envelopes và hash từng tệp đọc. Không dùng giá
  trị selected_value cũ để tự xác nhận; test cố ý đặt selected_value upstream sai
  vẫn tính lại đúng từ ba observed value.
- So exact security/event/field/scope/đơn vị/hiệu lực/revision, đúng nguồn gốc đã
  review; nguồnC trùng bytes/document/origin group không tính. Giữ observation,
  support/dissent, locator/hash/caveat. Không average/tolerance/unit inference hoặc
  suy bool=1. JSON có NaN/Infinity/duplicate key bị từ chối.
- Hash/receipt/URL/value binding sai, thiếu nguồn, cả ba khác nhau hoặc known
  counter-evidence/revision gap → unresolved queue, owner_action_required=false;
  case độc lập vẫn xử lý. DOM receipt không thể mang HTTP/raw labels.
- Output mới có manifest/input replay/runtime hash, refuse overwrite; CLI exit0
  khi chọn đủ,3 khi còn unresolved,2 khi lỗi policy/config/envelope/path/overwrite.

**Bản chạy cuối:** `run_output_release` tại
`data/corporate_actions/work/ors_third_source_reconcile_20261106_v1/`:
`PASS_ALL_CASES_SELECTED`,2/2 selected,0 unresolved,0 request nguồn,0 canonical.
Đối chiếu value, cặp support và dissent với hai selection receipt bước15 đều khớp.
Các lượt chạy phát triển trước bản cuối được giữ riêng để không ghi đè artifact;
chúng không phải replay campaign hoặc batch nguồn đã hoàn thành.

| Field | Nguồn A | Nguồn B | Nguồn C | Chọn |
| --- | --- | --- | --- | --- |
| Đơn vị quyền2024 | NQ11/2023 doanh nghiệp:2CP cũ/1quyền,1quyền/1CP mới | VSDC166577:1CP cũ/1quyền,2quyền/1CP mới | HOSE79 ngày15/01/2024 khớp B | B+C, giữ A dissent |
| Nominal bổ sung2021 | HTML doanh nghiệp924:2.000 tỷ | HNX430 ngày18/08/2021:1.000 tỷ | VSDC143656/GCN152-5 ngày02/08/2021:1.000 tỷ | B+C:1.000.000.000.000 VND, giữ A dissent |

**Kiểm thử cuối:**78 targeted tests đạt gồm29 mới và49 reconciliation/revision/
decision packet cũ; không xóa/giảm assertion. Compileall đạt. Synthetic smoke
`python run.py run --config configs/data/synthetic_smoke.example.json` bản cuối
`run-20261106T135235Z-4204f521` complete/synthetic=True; giữ các lượt smoke trước
đó theo các bản code trong quá trình self-review.530 input cũ giữ đúng hash.

**Giới hạn thực tế:** tự động hóa mới ở lớp so sánh observation đã được upstream
trích xuất và đánh giá origin/comparability/revision. Engine chưa tự tìm nguồnC,
đọc hiểu PDF hoặc tự chứng minh độc lập tác giả. Case chưa có metadata/evidence
thì queue để acquisition/agent review trong stage được giao, không đẩy PDF cho
owner. Config vẫn tắt automatic field approval/canonical; selected_value là review
selection, không là giá trị canonical. Không mở PIT/identity/available_at/full-
history revision gates, tính factor, thu lại85 bài/1.072 query hoặc mở7/418 mã.

Evidence: [kết quả tích hợp và sáu nguồn](../data/corporate_actions/work/ors_third_source_reconcile_20261106_v1/KET_QUA_TICH_HOP.md),
[summary bản cuối](../data/corporate_actions/work/ors_third_source_reconcile_20261106_v1/run_output_release/summary.json),
[hai kết quả tự tính](../data/corporate_actions/work/ors_third_source_reconcile_20261106_v1/run_output_release/results.json),
[hàng đợi unresolved](../data/corporate_actions/work/ors_third_source_reconcile_20261106_v1/run_output_release/unresolved_queue.json)
và [config mới](../configs/data/corporate_actions/third_source_reconcile_ors_v1.json).

**Bước tiếp theo đề xuất:** nối hàng đợi với tạo observation/tìm nguồn và agent
review provenance trong scope ORS được giao; chưa tự mở stage mới hoặc canonical.

## Bước 17 — xác nhận HNX và review phần tài liệu còn treo

**Mục tiêu:** xử lý gap có thể ảnh hưởng ngày/điều khoản/revision của ba sự kiện
ORS142284,166577,171704. Dùng cache trước; không chạy lại85 bài/V7 hoặc mở mã khác.
Theo yêu cầu mới, tạo0 file Markdown; chỉ cập nhật hai tài liệu hiện có.

**Kết quả:** `PASS_SCOPED_GAP_REVIEW`, đóng5/6 nhóm gap đầu vào; readiness toàn
event vẫn PARTIAL vì các gate và coverage chưa mở. Các nhóm là gap evidence,
không phải số bài thiếu: inventory snapshot ORS vẫn đủ85/85, thiếu0 bài toàn văn.

- **HNX2021 đã đọc được:** Chrome thường → sơ đồ website → UPCoM → Lịch thực hiện
  quyền → ORS,01/05–30/06/2021. Một dòng kết quả; mở chi tiết thấy rõ ex-date
  10/06/2021,record11/06/2021,1:1,giá10.000; chuyển nhượng25/06–09/07,đặt mua
  25/06–16/07. Khớp issuer769/VSDC142284 về các trường tương ứng. Hai transcript
  từ output accessibility đã lưu text/receipt/hash, loại
  `RENDERED_ACCESSIBILITY_TEXT_TRANSCRIPT`; bỏ index/control/footer và chuẩn hóa
  trình bày. Không là HTTP raw/PDF ký hoặc bằng chứng ngày công bố lịch sử.
  Tin từ Sở cùng bộ lọc trước đó không có kết quả; không suy rộng thành thiếu
  mọi dữ liệu, vì lịch quyền/chi tiết đã có positive evidence.
- **Ba attachment còn treo:** đọc đủ NQ01/2024 ngày05/01(2trang),NQ10/2024 ngày
  13/05(4trang),NQ11/2024 ngày04/06(2trang). Record/lịch quyền mua2024 và
  cổ tức100:12/record17/06 khớp. Hủy phần cổ phiếu lẻ không là hủy sự kiện.
- **13 bài hỗ trợ:** thu body publicSSR JSON và triage đủ13; không relabel DOM.
  Chọn thêm5PDF liên quan: NQ06/2021(4trang),GCN61/2021(2),GCN442/2023(2),
  AGM01/2024(8),HOSE424/2024(2). Tổng8PDF/26trang đã nhìn trực quan.
  HOSE424 là kết quả niêm yết35.999.743CP cổ tức; số36triệu là kế hoạch, khác
  scope. Ngày niêm yết có hiệu lực19/07 không được dùng làm ex-date/ngày giao dịch.
- AGM24/04/2024 có kế hoạch quyền mua210,3triệu CP,2:1,2,sau cổ tức/ESOP; đây
  là kế hoạch tương lai riêng, không sửa đợt100triệu CP tháng1/2024. Không tự mở
  sự kiện mới trong stage này. Trong các tài liệu vừa đọc chưa thấy hủy/đổi lịch
  ba sự kiện; không claim đã rà toàn lịch sử/phụ lục.
- HTML2042/2153 ghi nhãn vốn “tỷ đồng” đáng ngờ. Giữ nguyên literal và đánh dấu
  anomaly metadata; chưa sửa đơn vị/chọn canonical hoặc tạo conflict giả giữa
  các thời kỳ/phạm vi khác nhau. Hai selection theo nguồn thứ ba bước15–16 giữ
  nguyên; không có conflict mới đủ khóa so sánh để chạy lại rule.

**Evidence mới:**21 GET200,raw/receipt/hash đầy đủ (13HTML+8PDF); hai transcript
HNX có rendered receipt riêng. Browser/web discovery ghi riêng, không suy số
subrequest browser thành21. Helper giới hạn32 request trực tiếp; đã dùng21.
Không gặp challenge, không lấy cookie/token, không đổi fingerprint/TLS.

**Kiểm tra/self-review:**575 pin đầu vào khớp; kiểm receipt/body/hash, binding
SSR-derived về JSONpointer/raw,26 ảnh trang PDF,13triage và exactORS đạt.
78 targeted tests chạy:77đạt,1lỗi legacy helper path tại
`test_runner_path_safety_and_no_overwrite` tìm `tests/unit/scripts/...`; đã ghi
trong gap cũ, không sửa ngoài stage. Ban đầu gọi pytest thiếu package và unittest
thiếu PYTHONPATH; chuyển stdlib unittest với PYTHONPATH=src, giữ log kết quả thực.
Compileall đạt. Không đổi production code/config/pipeline; không chạy lại synthetic
smoke, giữ kết quả cuối bước16.0 canonical/pricefactor; không đổi hash/policy cũ.

**Còn thiếu:** PDF kết quả SSC4122/2021 chưa tìm được, xếp tùy chọn vì issuer869
đã có body kết quả và các followup đăng ký/niêm yết. Chưa review mọi attachment
hành chính,AGM2021 ký,prospectus/phụ lục2024. HNX chỉ có rendered text của snapshot
hiện tại, chưa raw/PDF ký/thời điểm công bố. Toàn lịch sử revision,PIT,identity,
available_at/freeze vẫn chưa mở; không giao owner đọc/phê duyệt từng tài liệu.

Evidence: [summary](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/summary.json),
[PDF review](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/pdf_visual_review.json),
[triage13bài](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/detail_triage.json),
[HNX detail](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/sources/hnx_2021_detail.rendered_ax.txt),
[gap review](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/gap_queue_review.json),
[verification](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/verification.json).

**Bước tiếp theo đề xuất:** hợp nhất observation/locator mới và hai field đã chọn
vào bundle đối chiếu offline mới cho ba sự kiện; xuất readiness và ngoại lệ còn
lại, dùng cache hiện có. Chưa tự thực hiện stage này hoặc canonical/nhóm7/418 mã.

## Bước 18 — hợp nhất bundle offline và readiness ba sự kiện

**Phạm vi:** chỉ đóng gói evidence đã review cho ORS142284,166577,171704, gồm
phần HNX/PDF bổ sung bước17 và hai selection đã chạy ở bước16. Không network,
không chạy lại query/batch/engine và không đổi code sản phẩm,config hay policy.
Không tạo Markdown mới; cập nhật nhật ký và CURRENT_STATUS hiện có.

**Kết quả:** `PASS_SCOPED_OFFLINE_BUNDLE`. Ba packet offline mới có59 dòng trường:
giữ nguyên54 observation cũ và thêm5field (đơn vị quyền2024 và bốn field hậu kiểm
niêm yết cổ tức2024).27 observation bổ sung gắn vào từng field, có source/receipt/
hash/locator và ref review đã pin. Catalog46 record gồm nguồn điều khoản,hậu kiểm,
dissent/context; không phải46 nguồn độc lập để bỏ phiếu. Bản HOSE copy/gốc chung
family; calendar/detail HNX là hai biểu diễn cùng announcement, không đếm hai phiếu.

- Giữ đủ giá trị và metadata cũ trong `legacy_observation`, có ref về đúng54 dòng
  packet bước12. Nhãn pending lịch sử còn ở bản lưu, trạng thái hiện hành không
  yêu cầu owner đọc từng tài liệu. Đây không phải kích hoạt general automatic
  approval policy hoặc phê duyệt tất cả field làm canonical.
- Hai selection tái sử dụng nguyên value,support,dissent,origin assessment và
  caveat từ `run_output_release` bước16: đơn vị quyền2024 và nominal bổ sung2021.
  Không tính lại vote hoặc ghi formal correction thay văn bản bất đồng.
- HNX2021 có8 observation từ transcript renderedAX đã lưu, với literal và offset
  ký tự trong text đã pin. PDF chỉ dùng semantic review/locator đã có ở bước17;
  kiểm máy xác nhận hash/JSONpointer/page-ref, không claim tự hiểu/review lại PDF.
- Giữ riêng kế hoạch36triệu/kết quả35.999.743CP,giá quyền10.000/giá phần dư11.000,
  nominal bổ sung1.000tỷ/tổng2.000tỷ và ex-date/ngày niêm yết. Hai tên field kế
  hoạch100triệu của quyền mua2024 đánh dấu alias, không cộng hai lần. Kế hoạch
  tương lai210,3triệu/ESOP vẫn là context ngoài ba sự kiện.
- D01–D06 của packet cũ được mapping sang trạng thái hiện hành, không sửa packet:
  D02 đã bổ sung HNX,D03/D04 đã có selection,D01 giữ observation theo scope,
  D05 giữ giới hạn revision,D06 giữ độ mạnh liên kết hậu kiểm.0 yêu cầu owner
  review tài liệu ở stage này.

**Readiness:**3/3 bộ observation đọc offline được; chưa là canonical/research ready.
Tám ngoại lệ chia rõ bốn gate chưa mở (coverage toàn lịch sử,publication/available_at,
historical security_id,future canonical freeze) và bốn mục hình thức/context/kỹ thuật
(HNX raw/PDF,PDF4122,nhãn đơn vị vốn,lỗi test helper). Không lấy ngày ký/cập nhật/
fetch làm publication,không dùng current ticker thay historical identity,không suy
vắng revision từ tìm kiếm không kết quả. Future methodology/freeze áp dụng
MANUAL_REVIEW_REQUIRED theo AGENTS; không xin/chạy approval đó trong stage bundle.

**Kiểm tra/self-review:**732 pin evidence cũ khớp và pin AGENTS thêm riêng;
179 ref hash/JSONpointer trỏ được. Giữ54 dòng cũ,27 supplemental và hai selection
đúng nguồn/scope. Bảy tình huống sửa sai dữ liệu trong bộ nhớ đều bị từ chối:
hash,AX thànhHTTP,literal HNX,đổi support bằng dissent,lấy actual đè planned,đổi
đơn vị quyền và bật canonical. Không sửa file evidence để chạy kiểm tra âm.
43 targeted tests (29third-source+14revision) và compileall đạt. Lỗi legacy
`test_runner_path_safety_and_no_overwrite` ở bước17 giữ nguyên,không chạy lại
bộ78 hoặc sửa assertion để che lỗi. Không đổi pipeline nên không chạy lại synthetic
smoke; bản cuối bước16 còn pin.0 request,0 canonical,0 factor,0 Markdown mới.

Lượt chuẩn bị đầu phát hiện locator cũ trỏ object chứa `value`,không trỏ scalar.
Đã sửa helper đóng gói để unwrap rõ schema và resume phần chuẩn bị chưa seal;
ba artifact đã ghi được kiểm bằng equality,không ghi đè. Không có lỗi raw hoặc
thay hash evidence. Bản cuối được kiểm độc lập trước seal manifest.

Evidence: [kết quả cuối](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/final_summary.json),
[readiness](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/readiness.json),
[field matrix](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/field_matrix.json),
[nguồn](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/source_catalog.json),
[ngoại lệ](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/exceptions.json),
[selection index](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/selection_index.json),
[verification](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/verification.json).

**Bước tiếp theo đề xuất:** sửa lỗi đường dẫn helper của test legacy trong một
stage kỹ thuật riêng, chạy targeted tests và compileall. Không tự mở canonical,
thu lại85 bài hoặc triển khai nhóm7/418 mã.

## Bước 19 — sửa hai đường dẫn helper test legacy

**Mục tiêu:** giải quyết lỗi kỹ thuật đã biết của test decision_packet ở bước17–18,
không đổi runtime,pipeline,config,policy hoặc dữ liệu ORS. Khi đối chiếu nhật ký,
phát hiện lỗi cached_review từ bước8 cùng nguyên nhân; sửa trong cùng stage path
fix này, không mở stage dữ liệu/nghiên cứu mới.

**Nguyên nhân và thay đổi:** hai file test đã chuyển từ `tests/unit/ingestion`
xuống `corporate_actions/legacy_sources` nhưng vẫn lấy `Path(__file__).parents[3]`.
Vì vậy ROOT thành `tests/unit` và helper bị tìm dưới `tests/unit/scripts`.
Đổi thành `parents[5]` tại hai file:

- `tests/unit/ingestion/corporate_actions/legacy_sources/test_corporate_action_decision_packet.py`.
- `tests/unit/ingestion/corporate_actions/legacy_sources/test_corporate_action_cached_review.py`.

**Kết quả:** `PASS_LEGACY_TEST_PATH_FIX`. Baseline từng test đều tái hiện
FileNotFoundError trước sửa. Bản sửa đầu decision_packet chạy78/78 đạt; sau sửa
thêm cached_review,bộ cuối94/94 targeted tests đạt. Compileall bản cuối đạt.
Synthetic smoke `run-20261106T144527Z-71e8ee60` complete/synthetic=True; chạy một
lần,production code/config không đổi giữa hai lượt sửa test. Đây là smoke local
CSV synthetic,không thu nguồn thật hoặc chạy lại batch85 bài/V7.

Self-review so AST before/after xác nhận chỉ biểu thức ROOT đổi,tất cả test case
và assertion giữ nguyên. Hai kiểm tra chống overwrite/path escape thực sự chạy
qua helper gốc; không bỏ/skip/patch assertion để pass.763 input pin cũ khớp;
before/after code,patch,baseline FAIL và log PASS lưu version mới. Không sửa log,
exception/manifest immutable của bước8/17/18; bổ sung record giải quyết ngoại lệ.

Lượt verification đầu và summary trung gian chỉ bao gồm decision_packet; kết quả
cuối ở `final_summary.json` bao gồm cả hai file và94test. Không claim bộ78 cũ
đã kiểm cached_review.0 request thu thập,0 canonical/pricefactor,0 Markdown mới;
chỉ cập nhật nhật ký và CURRENT_STATUS hiện có.

Evidence: [kết quả cuối](../data/corporate_actions/work/ors_legacy_test_path_fix_20261106_v1/final_summary.json),
[verification cuối](../data/corporate_actions/work/ors_legacy_test_path_fix_20261106_v1/final_verification.json),
[94 test](../data/corporate_actions/work/ors_legacy_test_path_fix_20261106_v1/targeted_tests_final.log),
[ngoại lệ đã xử lý](../data/corporate_actions/work/ors_legacy_test_path_fix_20261106_v1/exception_resolution.json).

**Còn lại/bước tiếp theo đề xuất:** lỗi test đã đóng,nhưng coverage toàn lịch sử,
publication/available_at,historical identity và canonical freeze chưa đổi. Đề
xuất stage kiểm kê evidence ngày công bố/available_at của ba sự kiện từ cache,
ghi rõ có/thiếu,không tự lấy ngày ký/cập nhật/fetch làm publication. Không tự
thực hiện stage tiếp hoặc mở canonical/nhóm7/418 mã.

## Bước 20 — kiểm kê evidence ngày công bố/available_at

**Phạm vi:** chỉ dùng cache đã pin cho ba sự kiện; không network/thu lại raw hoặc
batch85/V7. Bổ sung18 source context đã lưu vào46 source bundle,kiểm receipt/hash
và tách194 temporal observation. Không đổi code sản phẩm,config,acceptance policy,
available_at,usable_from_date hoặc canonical. Tạo0 Markdown mới.

**Kết quả:** `PASS_SCOPED_PUBLICATION_EVIDENCE_AUDIT` về inventory/provenance;
readiness toàn event vẫn PARTIAL. Hai ứng viên ngày đăng:

- **171704 — cổ tức2024:** text DOM HOSE1703956 đã pin ghi rõ
  `Đăng ngày: 11/06/2024 09:31:00`. Filename trong chính bài khớp PDF HOSE đã pin;
  không lấy ngày ở danh sách related news2026. Đây là observed posting label,
  chưa xác minh timezone hoặc snapshot first-publication năm2024.
- **166577 — quyền mua2024:** API HOSE article1614236 có postedDate1705416660;
  media API trỏ đúng PDF gốc đã pin. JavaScript HOSE cache dùng formatter
  `utc(e,"X").format("DD/MM/YYYY  HH:mm:ss")` cho postedDate. Tái dựng phần ngày
  hiển thị16/01/2024,giờ14:51:00,ghi đúng loại derived từ API+UI formatter. Không
  gọi là DOM mới hoặc coi UTC dùng để decode formatter là timezone thực của
  thời điểm công bố. postedDate/createdDate,publishFrom,approvedDate và metadata
  attachment giữ riêng; không lấy giá trị sớm nhất để backdate.
- **142284 — quyền mua2021:** VSDC có nhãn cập nhật02/06/2021 14:14:34; issuer769
  display_date02/06/2021,issuer77103/06/2021 từ exact-ID trong archive đã pin.
  Chưa có nhãn ngày đăng/công bố đủ rõ cho notice2021 trong cache audit này.
  Archive/detail cùng CMS không thành hai phiếu độc lập; update/display date
  không tự là publication. Ngày01/06 của văn bản950 là ngày ký,không thay thế.

**Theo field:** chỉ17/59 dòng có source dẫn tới hai ứng viên HOSE nêu trên;
42 dòng còn lại chưa có ứng viên tương ứng trong scope. Không kế thừa ngày đăng
notice sang actual result,residual allocation,nominal registration hoặc listing
followup.0/59 được gán available_at/usable_from_date. Ba trạng thái evidence khác
nhau không làm thay đổi hai selection nguồn thứ ba hoặc các field value cũ.

Rule CafeF CreateDate Product/M3 đã duyệt được ghi rõ,không tự mở rộng sang nhãn
HOSE/issuer/VSDC. Chỉ đọc index cache27761row đã có,lọc20 record trong folderORS:
2cổ phiếu đúng mãORS và18 mã đầy đủ khác. Không có core notice142284/166577/171704
hoặc CafeF CreateDate trong20record này. Đây là negative lookup scope,không là
bằng chứng mọi cache/CafeF không có bài. Không đọc lại toàn bộ raw corpus.

**Kiểm tra/self-review:**799 pin đầu vào khớp; ref JSONpointer,literal/offset,
attachment URL/filename và formatter derivation kiểm đạt.8 tình huống sai bị từ
chối: nâng update/display/capture thành publication/available_at,kế thừa ngày
notice cho result,suy timezone,relabel API-derived thànhDOM,đếm bond prefix thành
ORS equity hoặc mở rộng CafeF rule. Stage này không xin owner review từng tài liệu.

Kiểm thử entrypoint di chuyển chạy36test:34đạt,2 lỗi ở
`CacheAuditTests.test_runner_path_escape_and_immutable_output` và
`test_bounded_file_reads_keep_input_order_and_propagate_failure`,do ROOT tìm helper
`tests/unit/scripts/audit_corporate_action_cache_v1.py`. Đây là test file khác hai
file đã sửa bước19; giữ pin các bản sửa trước,không coi là lỗi tái phát. Đối chứng
hai entrypoint gốc byte-identical chạy36/36 đạt,compileall đạt; tổng trạng thái
kiểm thử vẫn PARTIAL vì hai lỗi migration chưa sửa. Không chọn bản pass để xóa
hoặc che log fail. Không đổi pipeline nên không chạy lại synthetic smoke,bản cuối
bước19 giữ pin. Helper đọc receipt cũ dùng schema source_hash/sha256 theo bản lưu,
không sửa/relabel receipt để đồng nhất.

Evidence: [kết quả cuối](../data/corporate_actions/work/ors_publication_evidence_audit_20261106_v1/final_summary.json),
[ứng viên ngày đăng](../data/corporate_actions/work/ors_publication_evidence_audit_20261106_v1/posting_date_candidates.json),
[coverage59field](../data/corporate_actions/work/ors_publication_evidence_audit_20261106_v1/field_publication_coverage.json),
[audit2021](../data/corporate_actions/work/ors_publication_evidence_audit_20261106_v1/142284.publication_audit.json),
[derivationHOSE](../data/corporate_actions/work/ors_publication_evidence_audit_20261106_v1/hose_formatter_derivation.json),
[kiểm thử](../data/corporate_actions/work/ors_publication_evidence_audit_20261106_v1/test_results.json).

**Bước tiếp theo đề xuất:** tìm có mục tiêu Công bố thông tin CafeF/CreateDate
cho ba sự kiện,ưu tiên2021; xác minh đúng event/tài liệu và giữ raw/receipt/hash.
Chỉ dùng DATE_ONLY Product/M3 rule đã duyệt nếu đủ; không tự chốt canonical,
research hoặc mở nhóm7/418 mã. Hai lỗi test migration giữ ngoại lệ kỹ thuật riêng.

## Bước 21 — tìm CafeF/CreateDate và xác minh đúng ba sự kiện

**Mục tiêu:** lookup có mục tiêu CafeF cho quyền mua2021,quyền mua2024,cổ tức2024,
ưu tiên2021; chỉ áp D-CRAWL-02 nếu có CreateDate đúng record/tài liệu. Không tự
thay policy hoặc mở canonical/research. Dùng cache trước: không thấy file record
ORS.csv/ORS.json trong các run disclosure_dates_v1 được liệt kê; không claim mọi
raw tài chính không có ORS. Không thu lại85 bài hoặc1.072queryV7.

**Kết quả:** `PARTIAL_NO_TARGET_EVENT_CREATEDATE`.12 GET công khai,10HTTP200 và
2redirect301/body0byte,có raw/receipt/hash riêng. Không gặp challenge/access control,
không cookie/token/login/fingerprint/TLS bypass. Giữ request đã xong,không fetch
lại để sửa lỗi đọc file local.

- API `ajaxcongbothongtin.ashx?symbol=ORS...` trả Count102:page1 có100,page2 có2,
  uniqueID102,tất cả exactORS và title BCTC. Có CreateDate thật nhưng0record khớp
  ba thông báo quyền/cổ tức. Không lấy ngày gửi BCTC cùng năm gán cho sự kiện.
  Trang Công bố thông tin public và JS inline xác nhận bảng dùng Data.BctcList/
  CreateDate. Đây là đính chính hướng tìm ở bước20: endpoint này không cung cấp
  ba notice trong snapshot đã quan sát,không nên tiếp tục phân trang vô hạn.
- Trang Tin doanh nghiệp ORS được mở theo link Xem tiếp của article. Theo redirect
  và bộ lọc public “Trả cổ tức - Chốt quyền”(configID2,page1,size30),quan sát16row,
  tìm đúng cả ba article. Không suy16row là toàn bộ lịch sử ORS.
- **142284:** article1505338 hiển thị08/06/2021 11:22; NewsArticle.dateModified
  là2021-06-08T11:22:19+07:00. Body khớp8 anchor:exactORS,record11/06,ex-date10/06,
  100triệu,1:1,giá10.000,và các mốc chuyển nhượng/đặt mua. Footer “TheoHOSE” không
  chứng minh đây là HNX original hoặc nguồn nội dung độc lập.
- **166577:** article1931113 hiển thị16/01/2024 00:00. Link PDF công khai đã tải
  có SHA-256 `364beb60...ae7787`,trùng byte bản HOSE79 đã pin; giữ provenance copy,
  không đếm thêm phiếu. Không dùng00:00 làm giờ công bố thực.
- **171704:** article2011515 tìm từ filter,hiển thị11/06/2024 00:00. PDF tải có
  SHA-256 `922534e7...12c8e`,trùng byte thông báo HOSE cổ tức đã pin. Không cần
  đọc/review lại PDF trùng hash; giữ liên kết article→PDF→original rõ ràng.

Ba article không có CreateDate hoặc NewsArticle.datePublished. Có nhãn ngày trên
article và NewsArticle.dateModified cùng ngày; WebPage.dateModified07/11/2026 là
metadata trang động được giữ riêng. Text/JSON-LD trích từ HTTP raw có derived
receipt/hash,không gán renderedDOM. Vì source/semantics khác input đã được duyệt,
**0rule DATE_ONLY được áp,0available_at/usable_from_date được gán,0canonical**.
Đây không là value conflict cùng field để bỏ phiếu nguồn thứ ba; hai field đã
chọn trước giữ nguyên. Nhãn ngày là evidence mới cho review,không thành CreateDate giả.

**Kiểm tra/self-review:**834 input pin khớp;12raw/receipt,102exactID,3article/body/
JSON-LD selector và2PDF hashbinding kiểm đạt.8 tình huống sai bị từ chối: gán
BCTC sang CA,relabel dateModified thànhCreateDate,lấyWebPage2026 cho2021,gán
available_at khi chưa rule,nhầm mã prefix,tính PDFcopy làphiếu độc lập,áp rule
cho record không khớp hoặc saihash.35 targeted tests(CafeF deep semantics và
corporate timing) cùng compileall đạt. Không đổi production pipeline nên không
chạy lại synthetic smoke;bản trước giữ pin. Hai lỗi cache_audit migration bước20
không sửa/che trong stage lookup.0 Markdown mới,chỉ cập nhật hai file hiện có.

Evidence: [kết quả cuối](../data/corporate_actions/work/ors_cafef_publication_lookup_20261107_v1/final_summary.json),
[endpoint102record](../data/corporate_actions/work/ors_cafef_publication_lookup_20261107_v1/disclosure_endpoint_review.json),
[ba event match](../data/corporate_actions/work/ors_cafef_publication_lookup_20261107_v1/event_match_review.json),
[rule applicability](../data/corporate_actions/work/ors_cafef_publication_lookup_20261107_v1/rule_applicability.json),
[verification](../data/corporate_actions/work/ors_cafef_publication_lookup_20261107_v1/verification.json).

**Bước tiếp theo đề xuất:** chuẩn bị policy riêng cho ngày hiển thị của đúng bản
tin CafeF DATE_ONLY,giới hạn Product/M3 và từng tài liệu/field; dùng ba record đã
review làm ví dụ có thể kiểm tra. Acceptance mới phải MANUAL_REVIEW_REQUIRED theo
AGENTS trước áp,không tự xem CreateDate rule đã duyệt là quyền đổi sang dateModified.
Chưa tạo/áp policy đó,không yêu cầu owner đọc từng PDF và không mở7/418 mã.

## Bước 22 — ưu tiên timestamp công bố theo chỉ đạo owner

**Chỉ đạo:** “hãy ưu tiên timestamp”. Đã ghi receipt ưu tiên riêng,không cần
owner duyệt lại thứ tự này. Stage chỉ đổi ưu tiên review/discovery cho ba event,
không kích hoạt source acceptance mới hoặc áp ngày bản tin CafeF.

Thứ tự: **timestamp công bố đã xác minh semantics/múi giờ trước;DATE_ONLY theo
rule đã chấp nhận là fallback;chưa đủ thì giữ gap**. Ngày ký,update,dateModified,
fetched_at và thời gian first-observed không tự là timestamp công bố lịch sử.
00:00 không mặc định thật hoặc giả; phải có evidence về độ chính xác của nguồn.

Rà8 ứng viên cache:ba VSDC update,ba CafeF NewsArticle.dateModified và hai HOSE
posted/nhãn đăng. CafeF2021 có11:22:19+07:00 nhưng semantics là modified nên chưa
đủ publication. HOSE quyền mua2024 có display16/01/2024 14:51:00 từ cachedAPI+
formatter; HOSE cổ tức2024 có label11/06/2024 09:31:00. Hai HOSE được đưa queue
xác minh raw/semantics/timezone trước,khi chưa có bằng chứng không tự gắnUTC/+07.
Nguồn gốc publication2021 vẫn cần tìm. Trong8 ứng viên:0publication timestamp
được xác minh đủ,0available_at/canonical được gán; không phải cả ba sự kiện thiếu giờ.

**Kiểm tra/self-review:**911 input pin và8ref review khớp,22 timing tests và
compileall đạt. Không đổi runtime/config/policy nguồn,không chạy lại synthetic
smoke/batch/query;0network,0canonical,0Markdown mới. Hai lỗi cache_audit migration
cũ giữ riêng,không thuộc22test đã chạy. Nhật ký và CURRENT_STATUS cập nhật tại chỗ.

Evidence: [summary](../data/corporate_actions/work/ors_timestamp_priority_review_20261107_v1/summary.json),
[chỉ đạo owner](../data/corporate_actions/work/ors_timestamp_priority_review_20261107_v1/owner_priority_receipt.json),
[review thời gian](../data/corporate_actions/work/ors_timestamp_priority_review_20261107_v1/timestamp_review.json),
[queue tiếp](../data/corporate_actions/work/ors_timestamp_priority_review_20261107_v1/timestamp_search_queue.json).

**Bước tiếp theo đề xuất:** xác minh timestamp công bố theo queue,ưu tiên
metadata/timezone đúng hai article HOSE và nguồn notice2021. Đề xuất DATE_ONLY
news policy ở bước21 chưa kích hoạt; không tự chuyển tiếp hoặc mở canonical/
nhóm7/418 mã.

## Bước 23 — xác minh timestamp và clock của nguồn

**Ngày:**07/11/2026. **Phạm vi:** đúng hai article HOSE1614236/1703956 và
tìm timestamp thông báo quyền2021; ưu tiên timestamp theo chỉ đạo bước22.

**Đã thực hiện:** lấy raw JSON detail và media của article1703956, cả hai
GET200 có receipt/hash. Tái dùng detail/media1614236, JavaScript formatter và
hai PDF đã pin; liên kết filePath/rawId với đúng URL/SHA-256 PDF, không tải lại.
Sáu đoạn JavaScript đối chiếu đúng offset xác nhận alias tới Moment2.24.0,
tokenX là Unix seconds và `utc(e,"X")` định dạng ngày/giờ bằng UTC.

| Bài | Giờ hiển thị/decoder | Encoded UTC theo parser, chưa là instant công bố được chấp nhận |
| --- | --- | --- |
| Quyền mua2024 —166577 |16/01/2024 14:51:00 |2024-01-16T14:51:00+00:00 |
| Cổ tức2024 —171704 |11/06/2024 09:31:00 |2024-06-11T09:31:00+00:00 |

**Phát hiện cần giữ:** ở cả hai bài, createdDate của bản tin và file lệch đúng
7giờ; publishFrom cũng lệch7giờ. Đây là các trường khác semantics, không dùng
để bầu chọn hoặc chứng minh clock nào sai. Decoder UTC đã rõ nhưng backend có
thực sự ghi instant UTC hay mã hóa wall clock vẫn chưa xác minh. Không tự thêm
+07 vào giờ hiển thị, dịch7giờ, lấy approvedDate/createdDate/publishFrom của bài
hoặc file làm lần công bố đầu. Đặc biệt approvedDate bài quyền mua ở tháng4,
khác postedDate tháng1; từng trường đã lưu nguyên nghĩa.

GET trang HNX lỗi xác thực certificate; giữ receipt lỗi, không tắt kiểm TLS.
Chrome thông thường không có certificate warning/challenge đã kiểm tra ba query:
Tin từSở01/05–30/06/2021 titleORS; Tin từTCPH cùng khoảng symbolORS; Tin từTCPH
01/06–08/06/2021 title“quyền mua”. Không quan sát được record khớp sau lọc.
Lưu transcript chuẩn hóa từ các state AX đã quan sát, ngày quan sát và thời điểm
chuyển ghi tách riêng; không có timestamp chính xác của từng thao tác, không
claim full AX export/HTTPraw hoặc vắng dữ liệu toàn lịch sử. Bốn query web tìm
timezone HOSE/notice HNX cũng không trả kết quả trong snapshot. Calendar/detail
HNX bước17 tiếp tục là evidence điều khoản, không biến thành ngày đăng.

**Kết quả:** `PARTIAL_ENCODING_VERIFIED_PUBLICATION_CLOCK_UNRESOLVED`.
Xác minh2encoding,0instant công bố thực đủ evidence,2021chưa tìm được timestamp;
0available_at,0canonical,không đổi source acceptance/policy. Không giao owner
đọc PDF/chọn timestamp thủ công.

**Kiểm tra/self-review:**923 input pin khớp trước/sau; binding article/PDF và
raw hash đạt;22 timing tests và compileall đạt. Không sửa production pipeline,
không chạy lại synthetic smoke. Hai lỗi helper cache_audit bước20 chưa xử lý ở
stage này. Không thu lại85/V7 hoặc mở7/418 mã;0Markdown mới.

**Evidence:** [summary](../data/corporate_actions/work/ors_publication_timestamp_verification_20261107_v1/summary.json),
[review HOSE](../data/corporate_actions/work/ors_publication_timestamp_verification_20261107_v1/hose_timestamp_review.json),
[decoder](../data/corporate_actions/work/ors_publication_timestamp_verification_20261107_v1/formatter_encoding_review.json),
[receipt ba query HNX](../data/corporate_actions/work/ors_publication_timestamp_verification_20261107_v1/sources/hnx_bounded_queries.dom_receipt.json),
[queue còn lại](../data/corporate_actions/work/ors_publication_timestamp_verification_20261107_v1/remaining_queue.json).

**Bước tiếp theo đề xuất:** tích hợp bộ trích timestamp offline tự động, giữ
raw/encodedUTC/semantics/clock_status và chỉ xuất available_at khi đủ evidence.
2021 và clock HOSE để DEFERRED, không chặn record khác; chưa chạy stage tiếp,
không tự nới acceptance hoặc canonical/PIT gate.

## Bước 24 — tạm ngừng DATE_ONLY toàn DELTA, tập trung timestamp thực

**Ngày:**07/11/2026. Owner ban đầu yêu cầu tạm ngừng DATE_ONLY và tập trung tìm
timestamp đúng; sau đó làm rõ phạm vi toàn DELTA, không riêng ORS. Ghi chỉ đạo
bổ sung version mới, cập nhật AGENTS/DECISIONS/CHANGELOG/config thực thi. DATE_ONLY
không còn là fallback cho mọi xử lý mới financial, corporate actions, Product/M3
và research đến khi owner yêu cầu dùng lại. Không đổi các policy version hay
artifact cũ; các trường ngày kỳ báo cáo/record/ex/operational giữ đúng nghĩa.

**Lookup đã làm:** kiểm currentNews post771 từ raw TPS đã pin: chỉ có id,
display_date2021-06-03, type và data. Lấy đúng public page JavaScript dẫn từ HTML
cũ, GET200 có raw/receipt/hash; UI dùng trường display_date. Route backend xuất
hiện trong public frontend trỏ hostname nội bộ, không truy cập hoặc dò route
nội bộ/khác để lấy metadata. Chrome đọc metadata công bố VSDC142284:0meta thuộc
whitelist publication,0time element,0JSON-LD; nhãn hiển thị vẫn là cập nhật.
Capture giữ riêng DOM observation, không relabel HTTPraw; chỉ lưu metadata công
bố thuộc scope, không lưu/dùng các metadata bảo mật không liên quan. Tám query
web bổ sung không mang lại bằng chứng đủ điều kiện cho timestamp/clock; kết quả
không đúng nguồn/ngữ nghĩa bị loại, không suy vắng toàn lịch sử.

**Kết quả:** chỉ đạo toàn project đã ghi (`PASS_GLOBAL_DATE_ONLY_SUSPENSION_RECORDED`),
tìm timestamp vẫn `PARTIAL_NO_ADDITIONAL_VERIFIED_TIMESTAMP`.0available_at,
0usable_from_date,0canonical; không biến decoder UTC bước23 thành clock công bố
đã xác minh. Bộ trích timestamp tự động đề xuất trước đó tạm hoãn để ưu tiên
tìm bằng chứng nguồn. Không thêm code production/pipeline hoặc hard guard mọi
CLI legacy; chỉ đạo áp ở agent execution/stage review, các route DATE_ONLY
không được agent chạy mới khi override còn hiệu lực.

AGENTS là governance document được cập nhật theo chỉ đạo mới; bản trước thay đổi
được bảo toàn byte/hash trong artifact bước24. Không sửa manifest lịch sử hoặc
báo toàn bộ input ở path cũ còn giống khi AGENTS đã đổi.949 input pin được đánh
giá:947 path giữ nguyên; AGENTS và DECISIONS sửa theo chỉ đạo mới có bản trước
khớp hash bảo toàn.22 timing tests và compileall đạt. Không tạo Markdown mới,
không thu lại85/V7 hoặc mở chiến dịch7/418.

**Evidence:** [summary](../data/corporate_actions/work/ors_exact_timestamp_investigation_20261107_v1/summary.json),
[chỉ đạo toàn project](../data/corporate_actions/work/ors_exact_timestamp_investigation_20261107_v1/owner_global_scope_addendum.json),
[config](../configs/data/publication_timestamp_only_execution_20261107_v1.json).

**Bước tiếp theo đề xuất:** tìm bằng chứng trực tiếp xác nhận clock publication
HOSE và timestamp bản tin gốc2021; giữ gap khi chưa đủ, không quay về DATE_ONLY.
Global override không tự mở broader crawl/canonical/PIT hoặc thực thi stage tiếp.

## Bước 25 — đính chính DATE_ONLY chỉ tạm ngừng trong corporate_actions

**Ngày:**07/11/2026. **Chỉ đạo mới nhất:** “tạm ngừng DATE_ONLY trong
`corporate_actions` thôi nhé”. Đây là đính chính phạm vi toàn DELTA ghi bước24.
Tạm ngừng cho mọi xử lý mới corporate_actions, kể cả dữ liệu CA đưa sang
Product/M3/research, đến khi owner yêu cầu dùng lại. Financial và phần khác
tiếp tục dùng DATE_ONLY theo policy đã duyệt trong scope/gate cũ; không mở
acceptance/research gate mới hoặc áp DATE_ONLY sang corporate_actions.

**Đã làm:** cập nhật AGENTS và phần hiện hành của status/nhật ký; nối quyết định
D-TIME-ONLY-02 và changelog, tạo config execution V2. V1/config/evidence/manifest
bước24 giữ nguyên. Governance trước sửa được lưu nguyên byte/hash trong version
artifact mới; thay đổi có khai báo. Không sửa code pipeline, canonical hoặc chạy
lại batch. Không thêm hard guard mọi CLI legacy; chỉ đạo áp tại agent execution.

**Kiểm tra/self-review:** kiểm scope config V2 chỉ corporate_actions, DATE_ONLY
financial không bị suspend và V1 giữ hash; kiểm snapshot trước/sau, JSON và liên
kết Markdown. Không thêm test hoặc chạy lại compile/smoke vì chỉ sửa tài liệu và
config chỉ đạo, không thay code/pipeline.0network,0Markdown mới,0lookup timestamp
mới,0available_at/usable_from_date/canonical. Không mở chiến dịch7/418.

**Evidence:** [summary](../data/corporate_actions/work/publication_date_only_scope_correction_20261107_v1/summary.json),
[config V2](../configs/data/publication_timestamp_only_execution_20261107_v2.json).

**Bước tiếp theo đề xuất:** trong corporate_actions tiếp tục tìm evidence clock
publication HOSE và timestamp nguồn gốc2021; giữ gap khi thiếu, không dùng
DATE_ONLY fallback. Chưa thực hiện stage tiếp theo trong bước đính chính này.

## Bước 26 — tìm nguồn timestamp có offset, đối chiếu tài liệu ORS

**Ngày:**07/11/2026. **Phạm vi:** followup ba sự kiện142284/166577/171704 theo
bước25; DATE_ONLY corporate_actions tạm ngừng, financial giữ policy cũ. Không
sửa acceptance/pipeline/canonical hoặc thu lại85/V7/nhóm7/418.

**Bằng chứng mới:** raw HTML Stockbiz article22811809 trảGET200 có
NewsArticle.datePublished=`2024-01-16T14:51:00+07:00`; time.datetime cũng ghi đúng
giá trị, nhãn hiển thị14:51 16/01/2024. AuthorHSX, publisherStockbiz; headline
khớp nguyên văn title HOSE1614236/mãORS. UTC theo offset nguồn khai báo là
07:51:00, bằng attachment.createdDate của HOSE; postedDate API HOSE giải mãUTC
lại ra14:51:00, lệch7giờ. Giữ quan sát này làm corroboration clock, không lấy
createdDate thay publication hoặc tự chốt clock backend lịch sử.

Web tool rendered/cache của cùng article có link public file
NewsAttachedFile/1548002. File GET200 và SHA-256 bằng
`364beb609427cb4b451bbffed5c2718285b9e683dd1371e2f405670f06ae7787`, khớp PDF
HOSE79 đã pin. **Giới hạn:** HTML/Chrome live hiện chỉ dẫn nguồn HSX chung,
không hiển thị link file; không gộp observation cache của web tool với rawHTML
hoặc coi đó là archive2024. Raw file/link observation/currentDOM lưu riêng.
Copy cùng tài liệu không là nguồn độc lập để bầu chọn nội dung.

Timestamp đạt mức **nguồn Stockbiz khai báo ngày công bố có offset, đã khớp tài
liệu**. Chưa chứng minh lần công bố đầu trên HOSE hoặc timestamp này tồn tại
nguyên trạng ở snapshot2024. Không đổi nguồn/semantics sang HOSE, không tự đưa
vào available_at. Nguồn công khai mới bổ sung evidence thật, không mở acceptance.

**Các route khác:** RSS footer chính thức HOSE dẫn feed và category21, haiGET200.
Các entry dùng Atom:updated với+07:00, không cópubDate/targetORS; chỉ là context
clock, không thay timestamp notice lịch sử. DNSE snippet có timestampUTC cho
171704 nhưng live listingGET307 về homepage; không có article/PDF binding nên
không nhận. Tìm trên Stockbiz chỉ trả optionAsk ở palette, query“ORS cổ tức”
trên trang tìm kiếm trả không thấy kết quả; không gửi Ask/login, không suy vắng
mọi bản tin.13query web đã ghi discovery receipt, không nhận nguồn sai/suy từ
trading timezone hoặc title đơn lẻ.

Tra archive đúng issuerTPS post769 năm2021, limit3capture: baGET đều429, retry
sau>=30giây và>=2phút, hết budget3attempt đánh DEFERRED. Chưa nhận index/capture,
không kết luận nguồn thiếu snapshot; không bypass rate limit/challenge.

**Kết quả:** `PARTIAL_ONE_EXPLICIT_OFFSET_TIMESTAMP_DOCUMENT_MATCHED`;
1timestamp nguồn khai báo mới cho166577, clock HOSE trực tiếp vẫn chưa xác minh,
171704 và nguồn gốc2021 còn gap.8GET/4HTTP200/1HTTP307/3HTTP429;990input pin
giữ nguyên.22timing tests/compileall đạt; không chạy lại synthetic smoke vì
không thay production pipeline.0DATE_ONLY,0available_at/usable_from_date/canonical,
0Markdown mới. Self-review giữ mọi khác biệt cơ chế/vintage và không đếm copy.

**Evidence:** [summary](../data/corporate_actions/work/ors_timestamp_source_followup_20261107_v1/summary.json),
[review166577](../data/corporate_actions/work/ors_timestamp_source_followup_20261107_v1/166577.stockbiz_timestamp_review.json),
[RSS context](../data/corporate_actions/work/ors_timestamp_source_followup_20261107_v1/official_RSS_clock_context.json),
[archive deferred](../data/corporate_actions/work/ors_timestamp_source_followup_20261107_v1/archive_route_review.json),
[queue còn lại](../data/corporate_actions/work/ors_timestamp_source_followup_20261107_v1/remaining_queue.json).

**Bước tiếp theo đề xuất:** ghép timestamp/binding Stockbiz vào packet166577 với
provenance/giới hạn riêng; tìm publication timestamp có offset cho171704 và
nguồn gốc2021 khi archive hết429. Không giao owner đọc PDF/chọn clock từng case;
chưa thực hiện stage tiếp, áp available_at/canonical hoặc dùng DATE_ONLY fallback.

## Bước 27 — supplement timestamp nguồn công khai cho ba packet

**Ngày:**07/11/2026. **Phạm vi:** ghép Stockbiz bước26 vào packet166577 và tìm
timestamp cho hai event còn lại. Tạo version supplement riêng cho cả ba packet;
không sửa bundle18/raw/policy/version cũ, không dùng DATE_ONLY corporate_actions.

**Nguồn mới:** raw hai bài Tin nhanh chứng khoánGET200 có receipt/hash:

| Event | Nguồn | Timestamp nguồn khai báo |
| --- | --- | --- |
|142284 quyền mua2021 |Article270871, tác giảN.T |2021-06-02T16:55:48+07:00 |
|171704 cổ tức2024 |Article347098, tác giảLạc Nhạn |2024-06-11T17:26:26+07:00 |

Mỗi nguồn có NewsArticle.datePublished, meta article:published_time,
time.datetime và data-time Unix khớp nhau. Bốn biểu diễn cùng publisher không
là bốn nguồn độc lập. Raw dùng offset+0700, normalizedISO giữ+07:00; không suy
giờ. dateModified bằng datePublished trong snapshot nhưng lưu riêng, không
lấy modified thay publication. Thời gian này thuộc chính bài báo; không gán
nhãn công bố đầu của VSDC/HNX/HOSE hoặc chứng nhận historical snapshot.

Bài2021 nêu ORS,100triệuCP,tỷ lệ1:1,giá10.000đ,transfer25/06–09/07/2021 và
subscribe25/06–16/07/2021; sapo ghi ngày chốt11/6. Bài2024 tổng hợp nhiều mã;
chỉ đúng đoạn bắt đầu“* ORS:” nêu cổ tứcCP100:12,36triệuCP kế hoạch,chốt17/6.
Không lấy ex-date/tỷ lệ của THG hay mã liền kề. Các ngày record fragment chỉ
ghi ngày/tháng, giữ mức support context riêng, chưa coi full date nêu trực tiếp.
Hai bài này không đính kèm exact notice PDF; binding là nội dung scoped khớp event.

Stockbiz166577 tái dùng đầy đủ raw/receipt/offset và exact-PDF binding bước26,
kèm giới hạn link file ở web-tool cache khác HTML/Chrome live. Không tải lại
file hoặc biến copy thành phiếu độc lập. Source catalog mới dẫn catalog bundle
cũ bằng ref; source_ids/rows/selection metadata cũ giữ nguyên trong mỗi packet.
Chỉ thêm timestamp_supplement với refs và support matrix; readiness canonical/
research/automatic approval không được nâng.

**Support matrix59row:**22row có nguồn nội dung hoặc PDF khớp hỗ trợ;2row
record date chỉ có ngày/tháng;35row không được nguồn timestamp mới hỗ trợ.
22row gồm7ở142284,11ở166577,4ở171704; đây là sốrow legacy (có alias planned
shares), không phải sốfield unique hoặc available_at đã chấp nhận. Ex-date2021
và cổ tức2024, mã quyền/ISIN và followup/kết quả/niêm yết thiếu nguồn timestamp
tương ứng vẫn giữ gap, không kế thừa giờ đăng bài notice sang mọi giá trị.

**Kết quả:** `PASS_THREE_PACKET_TIMESTAMP_SUPPLEMENT` về bổ sung offline;
temporal readiness vẫnPARTIAL.3timestamp nguồn khai báo (1reuse/2mới),3packet,
59row/two selections trước giữ nguyên.2GET/2HTTP200;archive429 giữDEFERRED,không
thử lại route đó ở bước này.1039input pin khớp;22timing tests/compileall đạt.
Không thay production pipeline nên không chạy lại smoke.0available_at/
usable_from_date/canonical,0DATE_ONLY,0Markdown mới; không đổi financial policy.

**Evidence:** [summary](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/summary.json),
[packet index](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/packet_index.json),
[ba timestamp](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/publication_timestamp_observations.json),
[field support](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/timestamp_field_support.json),
[queue](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/remaining_queue.json).

**Bước tiếp theo đề xuất:** review contract availability ở field level từ ba
timestamp nguồn khai báo và matrix; xác định support trực tiếp/PDF/context/
thiếu,ưu tiên ex-date2021/cổ tức2024 và followup còn thiếu. Không tự gán giờ cho
toàn event; nếu cần acceptance mới phải trình cụ thể theo AGENTS,không buộc
owner đọc từng PDF. Chưa thực hiện stage tiếp hoặc mở canonical/nhóm7/418.

## Bước 28 — review contract timestamp theo field, chuẩn bị approval cụ thể

**Ngày:**07/11/2026. **Phạm vi:** kiểm từng field của59row từ ba packet bước27,
phân biệt source support và admission; tìm timestamp cho ex-date2021/cổ tức2024.
Không thay công thức/gate hoặc tự kích hoạt draft PIT. DATE_ONLY chỉ dừng trong
corporate_actions, financial giữ policy đã duyệt. Stage single-agent.

**Nguồn mới có ích:** Mekong ASEAN article30000, publication
`2024-06-11T11:18:00+07:00`; NewsArticle.datePublished/meta published_time/nhãn
11/06/2024 11:18 khớp; dateModified bằng publication trong snapshot. Đúng đoạn
ORS nêu36triệuCP kế hoạch,100:12,record17/6/2024,ex-date14/6. Năm2024 choex-date
được trace về full record date ngay cùng đoạn; đây là context của eventdate,
không suy publication time hoặc dùng DATE_ONLY. Các đoạn210,3triệuCP quyền mua/
ESOP ở bài này không gắn sang sự kiện khác.

Hai bài calendar TNCK271471/347255 có timestamp rõ nhưng không cóORS trong body,
nên loại dù headline trùng ngày GDKHQ. Kinh tế Chứng khoán95427 trả403với title
Attention Required! | Cloudflare và thông báo bịblock; dừng route, không retry
bằngChrome hay thayfingerprint. Heuristic client trong receipt ban đầu false;
manual access review ghi bổ sung STOP_ROUTE_ACCESS_CONTROL, không sửa receipt.
Openstock trảTLS validation error; không hạTLS. CUA thất bại trước điều khiển
trang vì kernel assets path missing; reset1lần vẫn lỗi, dừng và ghi không có DOM
observation. Archive429 cũ không gọi lại.5GET gồm3HTTP200/1HTTP403/1TLSerror.

**Contract review:** CA PIT V1 vẫn là draft inactive/approvalnull, reconcile vẫn
automatic_field_approval=false. Metadata do publisher hiện tại khai báo chưa là
archive độc lập chứng minh exact content/version ở ngày lịch sử. Vì vậy việc
nhận chúng làm available_at là acceptance mới; stage này chỉ chuẩn bị proposal
`CA-SOURCE-TIMESTAMP-ORS-PILOT-V1`, **MANUAL_REVIEW_REQUIRED**, activatedfalse.

| Nhóm mapping đề xuất | Source time | Phạm vi field |
| --- | --- | --- |
|7field quyền2021 |TNCK270871:02/06/2021 16:55:48+07:00 |ticker,type,ratio,giá,CP kế hoạch,transferwindow,subscriptionwindow |
|6field cổ tức2024 |Mekong30000:11/06/2024 11:18:00+07:00 |ticker,type,record,ex-date,ratio,CP kế hoạch |

Đề xuất chỉ cho Product/M3 pilot và13mapping đã pin. Yêu cầu datetime có offset,
metadata nhất quán,dateModified không muộn,nội dung đúng ticker/event/field/value,
raw/receipt/hash. Cho phép năm eventdate từ explicit full date ngay cùng đoạn;
không lấy năm publication date để bù ngày event. Không claim timestamp Sở đăng
đầu hoặc historical snapshot được chứng nhận,không mở canonical/strictresearch.

**46row giữ lại:**11Stockbiz cótimestamp nhưng linkPDF chỉ quan sát ở webcache,
livearticle không có exactfieldtext/linkPDF;1record2021 chỉday/month chưafull
anchor cùngđoạn;34chưa có supportedpublicationtimestamp. Stage27source support22
và stage28admissioncandidate13 là hai metric khác nhau,không xóa support cũ.
59row/packet và hai selection trước giữ nguyên;0available_at/usable_from_date/
canonical. Source declaration/historical-vintage tradeoff đã ghi để owner duyệt
một quy tắc/phạm vi,agent tự review kỹ thuật nguồn; không yêu cầu đọc từngPDF.

**Kiểm tra:**13mapping qua offlineproposalvalidator;11negativecase bịtừchối:
dateonly,thiếuoffset,modifiedrelabel,HTTP403,saiticker,hashsai,cachedlinkonly,
futurefollowup,sai value,modificationmuộn,sainămcontext.22timingtests vàcompileall
đạt. Validator chỉ phục vụ reviewproposal,không claim activeingestion. Không
thayproductionpipeline nên không chạy lại smoke. Raw/policyversion/manifest cũ
immutable; DECISIONS cập nhật ghi proposal có snapshot trước sửa khớp hash.
0Markdown mới; không mở chiến dịch7/418 hoặc thu lại85/V7.

**Evidence:** [summary](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/summary.json),
[13mapping](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/proposed_field_bounds.json),
[admission59row](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/field_admission_review.json),
[proposal](../configs/data/corporate_actions/ors_source_timestamp_contract_proposal_20261107_v1.json),
[route outcomes](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/route_outcomes.json).

**Bước tiếp theo:** owner quyết định acceptance proposal hiện đã cụ thể hóa.
Nếu được duyệt, stage sau mới triển khai/test version availabilityoverlay cho
13mapping; giữ46hold và các gate khác. Chưa tựactivate hoặc sửa draft cũ.

## Bước 29 — đối chiếu nguồn bổ sung và archive lịch sử

Bước 29 hoàn tất tra cứu trong scope, kết quả **PARTIAL** về timestamp.
[Summary](../data/corporate_actions/work/ors_additional_source_crosscheck_20261107_v1/summary.json)
và [đối chiếu](../data/corporate_actions/work/ors_additional_source_crosscheck_20261107_v1/cross_source_comparison.json)
ghi riêng nội dung khớp, giờ từng bài và mức độc lập nguồn.

- Cổ tức 2024: Common Crawl lưu bài Mekong cũ ngày 16/06/2024 02:08:25 UTC.
  HTML lịch sử khai báo **11/06/2024 11:18:31+07:00**; đoạn ORS khớp nguyên văn
  trang hiện tại (tỷ lệ 100:12, 36 triệu CP kế hoạch, record 17/6/2024, ex 14/6).
  Trang hiện tại khai báo 11:18:00: thiếu 31 giây so với bản lịch sử. Archive
  độc lập về lưu trữ, cùng nguồn gốc Mekong; capture sau ex-date nên chưa chứng
  minh nội dung đã có trước ex-date, cũng không chứng minh giờ đăng đầu HOSE.
- Phụ nữ Việt Nam khai báo 10/06/2024 08:47+07:00; đoạn ORS khớp cổ tức 12%,
  ex 14/6 chỉ ngày/tháng. Báo Mới khai báo 11/6 12:18+07:00 và ghi nguồn Mekong,
  có originalUrl bài cũ. Đây là các publication khác; không vote giờ khác bài,
  không coi bản đăng lại là nguồn giá trị độc lập hay suy lỗi múi giờ.
- Quyền mua 2021: VietnamBiz khớp 100 triệu CP, 1:1, giá 10.000, các cửa sổ
  chuyển nhượng/đăng ký; ghi Theo Dòng Vốn Kinh Doanh. Timestamp 15/6 10:14
  thiếu offset và sau ex-date; chưa xác nhận giờ TNCK 02/06/2021 16:55:48+07.
  Hai exact index Common Crawl không có capture; index thứ ba lỗi 504, DEFERRED.
  Không suy archive vắng toàn bộ. Body hiện tại có quảng cáo 2026; chỉ review
  đoạn cổ phiếu, không gắn toàn bộ body hiện tại với thời gian 2021.

11 GET: 5 HTTP200, 1 HTTP206, 1 HTTP301, 2 HTTP404, 2 HTTP504. Raw live,
WARC range và derived archived HTML giữ riêng; WARC target/status/payload digest
khớp CDX. 1.110 input pin giữ nguyên; 22 timing tests và compileall đạt.
Không sửa production pipeline nên không chạy lại synthetic smoke. Không dùng
DATE_ONLY, không gán available_at/usable_from_date/canonical; 0 Markdown mới.

**Đính chính evidence so với bước 28:** đã có archive độc lập về lưu trữ cho
Mekong, với độ chính xác tới giây; chưa có cho TNCK 2021 trong scope đã tra.
Proposal V1 vẫn immutable/inactive/chưa được owner duyệt; mốc 11:18:00 cho
6 mapping cổ tức cần version mới theo evidence 11:18:31 trước khi xét activation.
Tra cứu thêm nguồn không được hiểu là approval của contract.

**Bước tiếp theo đề xuất:** review/chuẩn bị proposal version mới dùng timestamp
lịch sử 11:18:31 cho phần cổ tức; giữ riêng gap 2021 và clock HOSE, nêu rõ mức
source assertion/capture. Chưa triển khai availability overlay hay chạy stage
kế tiếp, chưa mở nhóm 7/418 hoặc thu lại 85 bài/V7.

## Bước 30 — proposal V2 giữ chính xác timestamp lịch sử

Bước 30 **PASS phần chuẩn bị/review**, activation vẫn **MANUAL_REVIEW_REQUIRED**.
[Proposal V2](../configs/data/corporate_actions/ors_source_timestamp_contract_proposal_20261107_v2.json)
và [13 mapping](../data/corporate_actions/work/ors_timestamp_precision_proposal_20261107_v2/proposed_field_bounds.json)
chỉ là đề xuất inactive, approval=null. Owner yêu cầu thực hiện bước chuẩn bị,
chưa được hiểu là phê duyệt dùng timestamp làm availability.

- 6 mapping cổ tức 2024: ticker, loại sự kiện, record date, ex-date, tỷ lệ,
  số CP kế hoạch chuyển mốc đề xuất từ 11/06/2024 11:18:00 sang
  **11/06/2024 11:18:31+07:00**, theo datePublished trong WARC Mekong cũ.
  Giá trị điều khoản không đổi. Giữ locator/hash đúng đoạn HTML lịch sử;
  ex-date lấy năm từ record17/6/2024 cùng đoạn, không suy giờ hoặc offset.
- 7 mapping quyền mua 2021 giữ timestamp nguồn khai báo
  **02/06/2021 16:55:48+07:00**, đánh dấu chưa được archive độc lập xác nhận.
  Không đóng gap chỉ vì VietnamBiz khớp điều khoản. 46 hold khác giữ nguyên.
- 13 mapping đều chưa có available_at/usable_from_date. Nguồn báo tự khai báo
  publication; archive Mekong thu16/6 sau ex-date14/6, chưa chứng minh nội dung
  ở instant11/6 hoặc giờ đăng đầu HOSE. V2 giữ rõ rủi ro này cho cả hai nhóm.

[Binding](../data/corporate_actions/work/ors_timestamp_precision_proposal_20261107_v2/171704.archived_timestamp_binding.json)
phân biệt networkHTTP206 khi đọc WARC với archived publisherHTTP200; derived
HTML không relabel raw HTTP live. Kiểm tra CDX/payload digest, WARC target/date,
range/length, SHA-256, metadata và đúng đoạn ORS. Current11:18:00 và
historical11:18:31 được giữ riêng, không average/vote. V1 không sửa.

0 network, không chạy lại85/V7; 22 timing tests,22 negative evidence guard cases
và compileall đạt. Không thay production pipeline nên không chạy lại smoke.
DATE_ONLY corporate_actions vẫn off, financial không đổi,0 canonical/availability,
0 Markdown mới. [Summary](../data/corporate_actions/work/ors_timestamp_precision_proposal_20261107_v2/summary.json).

**Bước tiếp theo đề xuất:** tra cứu bổ sung có giới hạn cho timestamp bài quyền
mua 2021 còn DEFERRED. Chưa tự triển khai overlay hoặc activate V2; không mở
nhóm7/418, strict research, canonical hay backtest.

## Bước 31 — tra cứu archive bài quyền mua 2021

Bước31 thực hiện lookup bổ sung đúng bài TNCK270871; kết quả **PARTIAL/DEFERRED**.
[Summary](../data/corporate_actions/work/ors_rights2021_archive_followup_20261107_v1/summary.json)
và [lookup observations](../data/corporate_actions/work/ors_rights2021_archive_followup_20261107_v1/archive_lookup_observations.json)
giữ đủ raw API/error body, receipt/hash; chưa thu được archived article HTML.

9GET:2HTTP200 API Wayback,1HTTP404 exact Common Crawl,6HTTP504. Wayback không
trả snapshot khả dụng cho URL dài và URL ngắn ở mốc yêu cầu gần02/06/2021.
Index2022-05 không có capture cho URL dài;2021-39/43,2022-21 và June2021 cho
URL ngắn/mobile gặp504. Biến thể URL ngắn/mobile lấy từ og:url/alternate trong
raw publisher đã pin, không đoán slug. Route2021-39 đã3attempt kể cả bước29,
backoff>=30/120giây, vẫn504 nênDEFERRED. Các route504 khác giữDEFERRED tại điểm
dừng scope; không claim đã hết mọi retry hoặc archive vắng toàn bộ lịch sử.

8web search queries chưa tìm thấy xác nhận độc lập của giây48. Giữ timestamp
nguồn khai báo **02/06/2021 16:55:48+07:00** và gap7mapping2021;46hold khác không
đổi. Kết quả lookup không phủ định timestamp, không tạo vote nguồn mới và không
gắn API response/error page thành fulltext cache của bài.

22timing tests/compileall đạt; không thay production pipeline nên không chạy
lại smoke. Proposal V1/V2 vẫn giữ nguyên/inactive;0availability/canonical,
khôngDATE_ONLY,0Markdown mới, không thu lại85/V7 hoặc mở nhóm7/418.

**Bước tiếp theo đề xuất:** đổi hướng sang đúng thông báo gốc HNX/TPS quyền mua
2021 để tìm publication timestamp của chính tài liệu đó, tái dùng evidence đã
có. Giữ giờ báo TNCK riêng, không kế thừa thành giờ công bố của Sở; chưa thực
hiện stage nguồn gốc này hoặc activate proposal.

## Bước 32 — thông báo gốc HNX/TPS quyền mua 2021

Bước32 **PARTIAL**: lưu được raw thông báo HNX, chưa tìm thấy publication
timestamp đủ ngày/giờ/múi giờ. [Summary](../data/corporate_actions/work/ors_primary_publication_lookup_20261107_v1/summary.json),
[review HNX](../data/corporate_actions/work/ors_primary_publication_lookup_20261107_v1/142284.hnx_primary_review.json)
và [cache TPS](../data/corporate_actions/work/ors_primary_publication_lookup_20261107_v1/142284.issuer_cached_date_review.json).

HNX query ORS01/05–30/06/2021 trả đúng1lịch quyền, articleID390773, khớp
record11/6,ex10/6,ngày thực hiện25/6. Đọc đúng popup theo endpoint/ID trong
HTML công khai, lưu **HTTP raw POST200**/receipt/hash. Title+body sau chuẩn hóa
whitespace/casefold khớp bản renderedAX bước17;9field điều khoản giữ nguyên.
Raw mới là sidecar riêng, không relabel DOM cũ hoặc sửa inventory20GET+65DOM.

Popup390773 không có publication date/time metadata. Hai query “Ngày đăng tin”
từ Sở/TCPH cho ORS trong05–06/2021 trả0row; hồ sơ từ link ORS trả shell không
có target data. Chỉ kết luận trong query/snapshot này, không suy nguồn mất hết
lịch sử. TPS archive cache có post769 display_date02/06/2021 và post771
03/06/2021, không có giờ/offset; giữ ngày làm evidence, không gán DATE_ONLY.
HTTPDate/fetched time, ngày VSD950 và ngày tạo/sửaPDF không thay publication.

Python TLS thiếu issuer CA; Windows .NET mặc định xác minh TLS thành công,
không custom validation callback/cookie/auth/fingerprint.9HTTP attempts gồm
6HTTP200,2HTTP302,1TLSerror. CUA/node runtime lỗi kernel assets trước navigation,
không có DOM mới. TPS web403 được giữ route, không retry client khác hoặc truy
cập internal backend; tái dùng raw cache.22timing tests,compileall và syntax
helpers đạt; không thay pipeline nên không chạy lại smoke.0Markdown mới.

Timestamp2021 vẫnDEFERRED,7mapping nguồn báo chưa được xác nhận độc lập;
46hold khác và proposal V1/V2 giữ nguyên/inactive.0availability/canonical,
không thu lại85/V7 hoặc mở nhóm7/418.

**Bước tiếp theo đề xuất:** giữ gap2021 và xử lý11field quyền mua2024 đang chờ
binding bài–PDF công khai trực tiếp; tìm evidence liên kết với timestamp đã
có, không tiếp tục lặp các lookup2021 vừa hoàn thành. Chưa thực hiện stage này
hoặc activate proposal.

## Bước 33 — live article/PDF binding quyền mua 2024

Bước33 **PASS phần binding**, temporal admission chưa review. Đã tìm được bài
Stockbiz legacy1548002 có link PDF trực tiếp trong raw HTTP200. GET attachment
trả526.299byte, SHA-256 trùng bảnHOSE đã pin và bảnFireAnt bước26:
`364beb609427cb4b451bbffed5c2718285b9e683dd1371e2f405670f06ae7787`.
[Binding review](../data/corporate_actions/work/ors_rights2024_live_document_binding_20261107_v1/166577.live_article_document_binding.json),
[11field](../data/corporate_actions/work/ors_rights2024_live_document_binding_20261107_v1/166577.eleven_field_binding_review.json)
và [summary](../data/corporate_actions/work/ors_rights2024_live_document_binding_20261107_v1/summary.json).

Legacy hiển thị16/01/2024 2:51:00CH, quy đổi ký hiệu12giờ thành14:51:00 nhưng
không gán offset. Bảnmodern22811809 đã pin khai báo14:51:00+07, có cùng headline,
clock components, nguồnHSX/HOSE và imageNewsID1548002. Legacy link download dùng
đúngNewsID1548002. Đây là public article-family matching; chưa thấy hyperlink
trực tiếp modern→legacy/PDF, không relabel modernraw thành có attachment link.
URLlookup legacy được dựng từ pattern links thật+date/ID/slug, sau đó response
đúngheadline/og:url/date và attachment xác nhận; không dòID hoặcAPI riêng.

**Đính chính gap11field:** không còn chỉ có cached-link evidence; đã có link
article→PDF live trực tiếp trênlegacy, nội dungPDF trùng byte nên tái dùng review
cũ và giữ11giá trị. Tuy nhiên V2 chỉ pin13mapping cũ, chưa bao phủ11mapping này;
legacy thiếu offset, modern schema thiếu dateModified, nên không tự giả định
modified=published hoặc chuyển+07 giữa hai record. Giờ đăng đầuHOSE và historical
vintage vẫn chưa được chứng nhận. [Gap admission](../data/corporate_actions/work/ors_rights2024_live_document_binding_20261107_v1/remaining_admission_gaps.json).

V2 immutable vẫn13conditional/46hold; supplement59row ghi riêng11binding mới đã
xác nhận, không coi46hold là46field hoàn toàn thiếu nội dung.0available_at/
usable_from_date/canonical;DATE_ONLY vẫn off.3GET/3HTTP200,22timingtests,
14negative binding checks/compileall đạt; không thay production pipeline nên
không chạy lại smoke.0Markdown mới, không chạy lại85/V7 hoặc mở7/418.

**Bước tiếp theo đề xuất:** review/chuẩn bị proposal version mới cho11mapping
bổ sung, ghi cụ thể crossfrontend evidence và cách xử lý dateModified vắng;
không âm thầm nới V2 hoặc activate. Gap2021/clockHOSE giữ riêng.

## Bước 34 — đề xuất V3 cho 24 mapping timestamp ORS

Bước 34 **PASS phần chuẩn bị và tự review**. [Proposal V3](../configs/data/corporate_actions/ors_source_timestamp_contract_proposal_20261107_v3.json)
và [24 mapping](../data/corporate_actions/work/ors_timestamp_admission_proposal_20261107_v3/proposed_field_bounds.json)
đã pin, vẫn **MANUAL_REVIEW_REQUIRED**, activated=false, approval=null.
Yêu cầu chuẩn bị đề xuất chưa phải approval áp dụng timestamp.

| Nhóm | Mapping đề xuất | Timestamp của nguồn | Giới hạn giữ lại |
| --- | --- | --- | --- |
| Quyền mua 2021 | 7, giữ nguyên V2 | 02/06/2021 16:55:48+07:00, TNCK | Chưa có archive độc lập xác nhận |
| Quyền mua 2024 | 11 bổ sung | 16/01/2024 14:51:00+07:00, Stockbiz modern | Composite binding với legacy/PDF; dateModified vắng; chưa có historical vintage |
| Cổ tức 2024 | 6, giữ nguyên V2 | 11/06/2024 11:18:31+07:00, Mekong lịch sử | Archive thu sau ex-date, chưa chứng minh nội dung ở đúng instant công bố |

11 mapping mới dùng timestamp có offset của đúng record modern 22811809.
Nội dung đi qua bài legacy 1548002 có link PDF trực tiếp, hash trùng HOSE 79.
Rule đề xuất yêu cầu cùng headline, date/wall clock, image news ID, nguồn
HSX/HOSE, legacy download news ID, receipt/hash và đúng field/value đã review.
Đây là composite evidence matching; không claim có hyperlink modern→legacy,
không gán timezone hoặc publication_at cho legacy và không giải quyết clock HOSE.

[Ngoại lệ có phạm vi](../data/corporate_actions/work/ors_timestamp_admission_proposal_20261107_v3/stockbiz_scoped_exception_proposal.json)
chỉ cho đúng 11 row ID và raw/PDF đã pin: dateModified vắng được giữ
NOT_PUBLISHED, không suy bằng datePublished hoặc chứng minh bài chưa sửa.
Metadata modification muộn/bất đồng phải DEFERRED. 13 mapping cũ giữ nguyên
rule V2; không cho phép thiếu modified trên toàn pipeline hoặc fallback DATE_ONLY.
10 row mới là ORIGINAL_TERMS, 1 row là operational rights units đã review;
giữ nguyên đơn vị phân bổ/thực hiện quyền, không sửa tỷ lệ hoặc giá trị.

Tổng vẫn 59 dòng: **24 candidate có điều kiện, 35 hold** gồm 1 ngày sự kiện
partial và 34 dòng chưa có timestamp hỗ trợ. Đây không phải 24 dòng đã được
nhận availability. V1/V2, raw, packet và selection cũ immutable. 0 network,
0 available_at/usable_from_date/canonical; DATE_ONLY corporate_actions vẫn off,
financial không đổi, không mở strict research hoặc chứng nhận giờ đăng đầu Sở.

22 timing tests, 33 negative proposal checks và compileall đạt. Không thay
production pipeline nên không chạy lại synthetic smoke; 0 Markdown mới.
[Summary](../data/corporate_actions/work/ors_timestamp_admission_proposal_20261107_v3/summary.json)
và [phạm vi quyết định](../data/corporate_actions/work/ors_timestamp_admission_proposal_20261107_v3/approval_scope_review.json).

**Bước tiếp theo:** owner quyết định V3 với đúng 24 mapping và ngoại lệ 11 row,
đặc biệt composite binding và metadata modification vắng. Agent đã review
tài liệu; không yêu cầu owner đọc từng PDF. Chỉ sau approval cụ thể mới triển
khai và kiểm thử availability overlay version mới; giữ 35 hold và các gap khác.
Stage hiện tại dừng ở proposal, chưa triển khai overlay hoặc activate policy.

## Bước 35 — nguồn báo khác đối chiếu giờ quyền mua 2024

Bước 35 **PARTIAL**: tìm thêm đúng một bài nguồn khác, nhưng không xác nhận
được cùng instant Stockbiz 14:51:00+07. [Review TNCK](../data/corporate_actions/work/ors_rights2024_timestamp_other_publisher_20261107_v1/166577.tnck_publication_review.json)
và [bảng so sánh](../data/corporate_actions/work/ors_rights2024_timestamp_other_publisher_20261107_v1/source_time_comparison.json).

Tin nhanh chứng khoán, bài 337892 “Sự kiện chứng khoán đáng chú ý ngày 17/1”,
khai báo **16/01/2024 17:36:15+07:00**. Raw GET200: JSON-LD, meta publication,
time.datetime và data-time epoch cùng instant; dateModified bằng publication.
Đúng đoạn ORS nêu record19/1, 100 triệu CP, tỷ lệ2:1, giá10.000. 6 row có support
(gồm hai row số CP kế hoạch cùng giá trị), record date chỉ ngày/tháng, 4 row
không được đoạn này hỗ trợ. Cửa sổ16/1–26/1/2024 thuộc SHB bên cạnh, đã loại.
Không có binding tới exact PDF HOSE trong bài TNCK này.

17:36:15 muộn hơn Stockbiz 2giờ45phút15giây. Đây là hai publication khác nhau
cùng sự kiện, không phải hai metadata mâu thuẫn của cùng article; không vote
chọn giờ và không coi TNCK xác nhận/phủ định Stockbiz14:51. Cache HOSE giữ
wall-clock14:51 nhưng publisher clock còn gap7giờ; CafeF chỉ00:00/modified,
không dùng làm xác nhận instant. Tái dùng evidence cũ, không tải lại PDF.

17 query web trong phạm vi không tìm thấy xác nhận độc lập của exact14:51+07;
không kết luận mọi nguồn vắng.1GET/1HTTP200,22timing tests/compileall đạt,
không thay pipeline nên không chạy lại smoke;0Markdown mới. Proposal V1/V2/V3
và toàn bộ field values giữ nguyên,0availability/canonical/DATE_ONLY.

**Phạm vi approval:** chưa có approval. Theo clarification mới nhất, nếu owner
sau này chỉ chấp thuận14:51 thì chỉ hiểu cho11field quyền2024, không tự duyệt
13mapping khác của V3. Tra cứu thêm nguồn hiện tại không phải approval.

**Bước tiếp theo đề xuất:** giữ14:51 chưa được nguồn mới xác nhận độc lập.
Nếu chọn giờ báo khác làm evidence, review riêng17:36:15 cho đúng6field TNCK
nêu; giữ1partial/4unsupported, không truyền timestamp sang toàn11field. Chưa
thực hiện review admission mới hoặc activate proposal.

## Bước 36 — đối chiếu thêm nguồn FUNAN quyền mua 2024

Bước 36 **PARTIAL**: nguồn mới FUNAN có đúng hàng ORS và URL PDF thông báo,
nhưng không có publication timestamp để so với Stockbiz/TNCK.
[Review nguồn](../data/corporate_actions/work/ors_rights2024_additional_broker_source_20261107_v1/166577.funan_source_review.json)
và [summary](../data/corporate_actions/work/ors_rights2024_additional_broker_source_20261107_v1/summary.json).

Lịch sự kiện FUNAN trang3 có đúng1hàng ORS:2:1,giá10.000,18/01/2024. Header
ghi rõ ngày này là **Ngày GDKHQ**, không phải ngày đăng. Onclick chứa HTML
popup dẫn đúng URL PDF Vietstock đã pin có hash trùngHOSE. Chỉ decode HTML
attribute, không executeJS hoặc claim popupDOM mới. Tái dùng receipt/hash của
bảnPDF cũ, không tải lại hoặc claim vừa xác minh bytes hiện tại của targetURL.

Không có giờ trong row/popup hoặc publication metadata; không lấy18/1, ngày
16/1 trong đường dẫn/tênPDF, hay fetched time làm giờ đăng. FUNAN chưa xác nhận
14:51Stockbiz hoặc17:36:15TNCK; không tạo majorityvote giữa ngày sự kiện và giờ
publication.7query web,1GET/HTTP200,22timingtests/compileall đạt. Không thay
pipeline nên không chạy lại smoke.0Markdown mới,0availability/canonical/DATE_ONLY.
Proposal V1/V2/V3 và toàn bộ evidence/field values cũ giữ nguyên; chưa approval.

**Bước tiếp theo đề xuất:** nếu tiếp tục đối chiếu nguồn, ưu tiên trang bản tin
Vietstock gắn với exactPDFURL này để đọc publication metadata của bài. Không
lấy filedate hoặc mở rộng lịch sự kiện chỉ cóex-date. Giữ14:51chưa được xác nhận
độc lập; chưa thực hiện lookupVietstock hoặc activateproposal trong stage này.

## Bước 37 — lookup bản tin Vietstock quyền mua 2024

Bước 37 **PARTIAL/DEFERRED**. Chưa xác định được URL bản tin Vietstock gắn
với PDF ORS đã pin, chưa thu được publication timestamp mới.
[Route review](../data/corporate_actions/work/ors_rights2024_vietstock_publication_lookup_20261107_v1/vietstock_route_review.json)
và [summary](../data/corporate_actions/work/ors_rights2024_vietstock_publication_lookup_20261107_v1/summary.json).

Trang chủ Vietstock trả HTTP403, body146byte ghi rõ “403 Forbidden”, nginx.
Dừng route vì server từ chối truy cập; classifier challenge=false chỉ có nghĩa
chưa thấy JS/CAPTCHA, không phải quyền tiếp tục. Không đổi fingerprint, dùng
cookie/token, thử alias/finance host hoặc browser để vượt route này. Đây là
status của entrypage, không claim đã mở exacttargetarticle rồi nhận403.

9 query search trong phạm vi vẫn chỉ tìm được PDF đã biết và các nguồn khác;
không suy bài không tồn tại trên toàn nguồn. Receipt PDF cũ có Last-Modified
16/01/2024 07:57:56GMT (14:57:56+07 khi chỉ đổi cách hiển thị instant header),
nhưng đó là thời gian sửa file, không phải ngày/giờ đăng bản tin. Không áp mốc
này, ngày tênfile hoặc documentdate vào publication/availability; không tải lạiPDF.
[Review semantics](../data/corporate_actions/work/ors_rights2024_vietstock_publication_lookup_20261107_v1/pinned_PDF_header_semantics_review.json).

Không thêm xác nhận độc lập cho Stockbiz14:51 hoặc TNCK17:36:15.1GET/HTTP403,
22 timing tests và compileall đạt; không thay pipeline nên không chạy lại smoke.
Evidence/policy/proposal/field values cũ giữ nguyên,0availability/canonical/
DATE_ONLY và0Markdown mới. Chưa có approval; nếu owner sau này chỉ duyệt14:51,
scope vẫn chỉ11field quyền2024, không tự duyệt13mapping khác củaV3.

**Bước tiếp theo đề xuất:** giữ Vietstock DEFERRED. Nếu tiếp tục xác minh14:51,
ưu tiên bằng chứng quy ước clock của đúng thông báo gốc HOSE1614236, tái dùng
metadata đãpin và chỉ tìm evidence mới phù hợp. Không retry route403 hoặc lấy
giờ báo đăng lại làm xác nhận giờ Sở. Chưa thực hiện followup HOSE trong stage này.

## Bước 38 — xác minh clock HOSE 1614236

Bước 38 **PARTIAL, vấn đề vẫn OPEN**. Đã tái kiểm tra đúng raw API, media và
formatter đã pin; chưa có bằng chứng chọn một publication instant của HOSE.
[Hai cách hiểu](../data/corporate_actions/work/ors_hose_clock_contract_followup_20261108_v1/1614236.clock_hypotheses.json)
và [kết quả xác minh](../data/corporate_actions/work/ors_hose_clock_contract_followup_20261108_v1/official_clock_verification.json).

| Cách hiểu chưa được chấp nhận | Giờ Việt Nam tương ứng | Điều kiện chưa chứng minh |
| --- | --- | --- |
| postedDate là Unix UTC thực | 16/01/2024 21:51+07 | Backend mã hóa đúng instant publication UTC |
| postedDate chứa wall-clock Việt Nam đóng gói như UTC | 16/01/2024 14:51+07 | Có clock contract/historical source cho cách đóng gói này |

Giao diện cached dùng Moment.utc(...,"X") nên hiển thị thành phần14:51, nhưng
JS được thu năm2026, không tự chứng minh backend/historical UI năm2024. H2 là
giả thuyết có điều kiện, không gán offset thật cho HOSE. Nó trùng số với media
createdDate không có nghĩa created là publication. Giữ riêng media.publishDate,
approvedDate, publishFrom, RSSupdated, PDFmodified; không chọn/average/vote chúng.
Stockbiz14:51+07 vẫn là timestamp riêng do Stockbiz khai báo, không bị phủ định
và không tự trở thành first-publication HOSE.

RSS theo target category343 trả404, không phải chứng minh bài không tồn tại.
Hai index Common Crawl của candidate URL legacy gặp504; Wayback sau30/120giây
retry trả200 nhưng không có snapshot khả dụng cho hai candidate prefixwww/www1.
Pattern legacy có nguồn công khai, GUID từ API, nhưng exact URL identity chưa
được xác nhận bằng capture body; không kết luận archive vắng toàn bộ.

**Đầu mối mới cụ thể:** Wayback API trả capture trang chủ HOSE
**18/01/2024 06:22:41 UTC**, URL
`https://web.archive.org/web/20240118062241/https://www.hsx.vn/`.
API availability không phải HTML. Replay cả3attempt vẫn429, backoff>=30/120giây;
giữDEFERRED, không đổi client/host/proxy để né. Đây là homepage để tìm clocklabel,
chưa phải capture bài ORS. [Resume queue](../data/corporate_actions/work/ors_hose_clock_contract_followup_20261108_v1/resume_queue.json).

12request trong basebudget10+addendum chỉ cho2retry cùngreplayURL,9query web.
22timingtests,compileall/helpercompile đạt; không thay pipeline nên không chạy
lại smoke.0Markdown mới; raw/policy/proposal/field values cũ giữ nguyên,
0availability/canonical/DATE_ONLY,không thu lại85/V7 hoặc mở7/418.

**Bước tiếp theo:** khi replay service hết429, resume đúng capture đã có để đọc
nhãn clock lịch sử và đánh giá phạm vi áp dụng cho bài1614236; không tìm lại
toàn bộ hoặc tựchốt14:51/21:51. Vấn đề chưa đóng; không yêu cầu owner phê duyệt
HOSE instant chưa xác minh. Nếu sau này owner chỉ chấp nhận sourceasserted
Stockbiz14:51 thì scope phải rõ11field, không tựduyệt13mapping khác củaV3.

## Bước 39 — resume archive để tìm clock lịch sử HOSE

**Phạm vi:** tiếp tục đúng vấn đề timestamp thông báo HOSE1614236 theo yêu cầu
owner, không chuyển sang stage overlay/canonical hoặc chiến dịch mã khác.

**Kết quả: PARTIAL, vấn đề vẫn OPEN.** Resume capture Wayback
`https://web.archive.org/web/20240118062241/https://www.hsx.vn/` vẫn429, body
khớp lần trước, Retry-After vắng. Không có HTML lịch sử để đọc clock; không
lặp retry ngay hoặc đổi client/host/proxy. Lần trước đã có3attempt với backoff;
lần này probe sau hơn5phút vẫn cùng kết quả.

Dùng Common Crawl độc lập trong cùng mục tiêu, với scope/budget addendum lưu
riêng, giữ base scope immutable:

- CC-MAIN-2024-10 trả record `http://hsx.vn/`, capture01/03/2024 14:18:42UTC.
  Tải đúng public range633byte, HTTP206; kiểm lại SHA-256 receipt và payload
  SHA-1 khớp CDX/WARC. HTML trích xuất103byte **chỉ chuyển hướng** sang
  `https://www.hsx.vn`; không chứa nội dung trang chủ hoặc nhãn clock.
  Ghi rõ archived HTTP body derived từ WARC, không relabel thành HTTP raw mới
  của HOSE, rendered DOM hoặc capture bài ORS. Query exact dùng canonical root
  key có thể gộp scheme/www; actual record URL mới là target đã quan sát.
- Theo đúng đích HTTPS đọc được, kiểm thêm CC-MAIN-2024-18:404 JSON “No Captures
  found”. Chỉ kết luận cho query/index/filter đã quan sát; không suy không có
  capture ở nơi khác. Không có record để tải WARC thứ hai.

Chưa xác minh clock HOSE, chưa chọn14:51+07 hoặc21:51+07. Giờ Stockbiz14:51+07
vẫn là publication assertion riêng của Stockbiz; không đổi thành giờ công bố
đầu tiên của Sở. Không dùng archive time/HTTP Date/Last-Modified/media created
để lấp gap và không yêu cầu owner phê duyệt instant HOSE chưa được chứng minh.

**Kiểm tra:**4request, effective budget5;22timingtests vàcompileall đạt. Review
offline kiểm độc lập chuỗiCDX→WARC→HTTPbody và1489inputpin giữ nguyên. Không
thay pipeline nên không chạy lại synthetic smoke.0Markdown mới,0availability/
canonical/DATE_ONLY; proposalV1/V2/V3 và59field cũ không thay đổi. Không thu lại
85/V7 hoặc mở nhóm7/418.

Evidence: [review archive](../data/corporate_actions/work/ors_hose_archive_clock_resume_20261108_v1/historical_home_capture_review.json),
[summary](../data/corporate_actions/work/ors_hose_archive_clock_resume_20261108_v1/summary.json)
và [yêu cầu bằng chứng tiếp theo](../data/corporate_actions/work/ors_hose_archive_clock_resume_20261108_v1/next_evidence_requirements.json).

**Bước tiếp theo đề xuất:** tìm tài liệu kỹ thuật/lịch sử công khai của HOSE
nêu rõ clock/timezone và encoding của publication `postedDate`, có căn cứ áp
dụng cho năm2024. Không lặp ngay query archive đã hoàn tất; Wayback giữDEFERRED.
Đây là đề xuất, chưa thực hiện stage lookup contract mới hoặc chọn timestamp.

## Bước 40 — tìm tài liệu công khai về clock publication HOSE

**Phạm vi:** thực hiện đúng lookup tài liệu kỹ thuật/lịch sử đã đề xuất ở bước39,
tìm contract `postedDate` có căn cứ áp dụng cho bài1614236 năm2024. Không thay
methodology, chạy lại archive hoặc chuyển sang activation/chiến dịch mã khác.

**Kết quả: PARTIAL; chưa xác minh được clock gốc HOSE.**15query web trong scope
chưa tìm được tài liệu chính thức giải thích encoding/timezone publication API.
Không dùng lịch giao dịch, timezone của thư viện hay giờ báo đăng lại để lấp gap.
Tin bên ngoài về website mới năm2025 chỉ giữ làm đầu mối; không đủ xác nhận
ngày migration hoặc semantics của dữ liệu lịch sử.

Các bằng chứng mới có raw/receipt/hash:

- API Điều khoản sử dụng và FAQ, suy route từ đúng pinned publicJS:2GETHTTP200,
  mỗi body132byte, JSONsuccess=true/list[]/totalCount0. Đây là danh sách rỗng
  trong hai query đã quan sát, không phải response0byte hay chứng minh không
  tồn tại tài liệu ở nơi khác. Không đoán private schema/auth endpoint.
- PDF quy chế340/QĐ-SGDHCM ngày19/8/2016, HTTP200,9.751.617byte,67trang scan.
  Trích text layer0ký tự, không lấy kết quả tìm text0match làm bằng chứng vắng.
  Render/đọc trực quan trang1–12; giữ contact sheets và ảnh riêng trang4/6/7.
  Phần đã đọc phân biệt báo cáo gửi/nhận với thông tin đăng website; yêu cầu
  thể hiện ngày/giờ không giải thích Unix/timezone củaAPI. Chưa audit toàn67
  trang, chưa xác nhận hiệu lực năm2024 hoặc contract cho đúngpostedDate.
- Query public UI/API một cửa sổ28/4–5/5/2025, tối đa20record:HTTP200,19record,
  không phân trang; thấy notice ngày đầu KRX2372398. Giờ vận hành trong nội dung
  không phải publication timestamp; chưa thấy clockcontract trong19record này.

PDF raw mới được giữ đúng loại; render/text PDF là derived evidence, không phải
renderedDOM hay HTTPraw HTML. Webtool output chỉ là discovery/extraction, không
relabel thành publisher HTTPraw. Không tự chọn14:51+07 hoặc21:51+07 cho HOSE;
Stockbiz vẫn có assertion riêng14:51+07, chưa thành first-publication của Sở.

**Kiểm tra/self-review:**4request córeceipt đềuHTTP200;22timingtests/compileall
đạt,1535inputpin giữ nguyên. Không thay pipeline nên không chạy lại synthetic
smoke.0Markdown mới,0timestamp được chọn/availability/canonical/DATE_ONLY;
proposalV1/V2/V3 và59field cũ giữ nguyên. Không retryWayback hoặc thu lại85/V7/7/418.

Evidence: [review contract](../data/corporate_actions/work/ors_hose_public_clock_contract_lookup_20261108_v1/public_clock_contract_review.json),
[summary](../data/corporate_actions/work/ors_hose_public_clock_contract_lookup_20261108_v1/summary.json)
và [phạm vi review PDF](../data/corporate_actions/work/ors_hose_public_clock_contract_lookup_20261108_v1/PDF_visual_render_receipt.json).

**Bước tiếp theo đề xuất:** tra bản tin công khai FireAnt từ imageNewsID1548002
đã quan sát trong bài Stockbiz pinned; kiểm exactarticle/PDF, timestamp cóoffset
và quan hệ nguồn trước khi coi là xác nhận độc lập. ImageID chưa chứng minh URL
bản tin. Nếu chung feed thì không vote độc lập; thời gian báo đăng lại không
tự chứng minh clock HOSE. [Lead](../data/corporate_actions/work/ors_hose_public_clock_contract_lookup_20261108_v1/next_evidence_lead.json).
Chưa lookupFireAnt trong stage này. Clock HOSE vẫnOPEN; không hỏi owner duyệt
một instant chưa rõ và không đề xuất lặp ngay lookupclock vừa hoàn tất.

## Bước 41 — FireAnt và VNDIRECT cho thông báo quyền mua ORS2024

**Phạm vi:** thực hiện đầu mốiFireAnt đã đề xuất và thêmVNDIRECT theo owner;
chỉ đúng thông báo quyền muaORS2024. Không mở campaign mã khác hoặc activation.

**Kết quả FireAnt:** rootmobile404, sau đó trangweb công khai200 có mẫu link
`/bai-viet/{slug}/{ID}`. Từ mẫu này vàID22811809 của Stockbiz pinned tạo một
publicURLcandidate; chỉ sau HTTP200/body đúng tiêu đề/ORS/nguồnHSX mới xác nhận
danh tính. Không suy imageID1548002 là currentarticleID. Bài có:

- `initialPost.date=2024-01-16T14:51:00+07:00`.
- JSON-LD `datePublished=2024-01-16T07:51:00.000Z`, cùnginstant với mốc trên.
- Direct download anchor và `files[].fileContentUrl` cùng dẫn
  `https://mobiv2.fireant.vn/News/NewsAttachedFile/1548002`.
- PDFHTTP200/526.299byte, SHA-256
  `364beb609427cb4b451bbffed5c2718285b9e683dd1371e2f405670f06ae7787`, trùng bản
  gốcHOSE đã pin. Chỉ so bytes/hash; không claim đọc lại điều khoảnPDF mới.

Timestamp cóoffset và directarticle/PDF binding nằm trong cùngHTMLHTTPraw;
không còn phải dùng composite modernStockbiz→legacy để chứng minh binding của
riêng nguồnFireAnt. Đây vẫn là source-asserted FireAnt publication, không phải
clock/first-publication HOSE. Chưa có historicalcapture2024/dateModified;
không suy nội dung chưa sửa, không lấy media.createdDate trùng số làm bằng chứng.
Không claim đã quan sát renderedDOM hoặc giờ hiển thị trực quan của browser.

**Tính độc lập:** FireAnt/Stockbiz cùng currentpostID22811809, FireAntimage1548002,
và legacyNewsID/attachment1548002. Stockbiz link sang FireAntORSSymbol, không
phải articlehyperlink. Giữ các dấu hiệu quan hệ/sharedfeed; chưa chứng nhận
ownership/kiến trúc dữ liệu. Không tính hai giao diện thành hai phiếu độc lập,
không áp majorityrule giữa giờ riêng của báo và trườngpublication chưa rõ củaSở.

**Kết quả VNDIRECT:** ORSoverview và2JSbundle công khaiHTTP200. Bundle khai báo
APIbase `https://api-finfo.vndirect.com.vn/` + `v4/news`, anonymousGETwrapper,
qtagCodes và sortnewsDate/newsTime. QueryexactORS/date16/01/2024 giới hạn100
record trảHTTP403/body13byte “Access Denied”. Dừngroute/provider ngay; không
retry bằng aliasfinfo-api, embeddedhostdstock.vn, browser, token hoặc cookie.
Helperflagchallenge=true vì khớpAccessDenied; chưa khẳng định có CAPTCHA/JS
challenge. Chưa xác minh filter hoặc thấy bản tin/timestamp; không suy bài vắng.

**Trạng thái:**PARTIAL. FireAnt bổ sung directlivebinding và timestamp rõ offset;
chưa có xác nhận độc lập mới cho14:51, clockHOSE14:51/21:51 vẫnOPEN. VNDIRECT
DEFERRED do từ chối truy cập. ProposalV1/V2/V3 inactive/không approval;0availability/
canonical/DATE_ONLY,59field cũ không đổi, không tựduyệt13mapping khácV3.

**Kiểm tra/self-review:**8request córeceipt (6HTTP200/1HTTP404/1HTTP403),16query;
22timingtests/compileall đạt,1584inputpin giữ nguyên. Không thay pipeline nên
không chạy lại synthetic smoke;0Markdown mới, không thu lại85/V7/7/418/archive.

Evidence: [FireAnt binding](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/fireant_target_timestamp_binding_review.json),
[source independence](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/source_independence_review.json),
[VNDIRECT route](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/vndirect_route_review.json)
và [summary](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/summary.json).

**Bước tiếp theo đề xuất:** review/cập nhật proposal inactive cho đúng11field
quyền2024 bằng source-asserted FireAnt timestamp/directPDFbinding trong cùngHTML.
Giữ gap lịch sử/dateModified/HOSEclock và giới hạnsourceindependence. Admission
làmethodology-sensitive, `MANUAL_REVIEW_REQUIRED` trướcactivation; chưa thực hiện
stageproposal mới/availability hoặc mở gate trong bướclookup này.

## Bước42 — chấp nhận và áp timestamp FireAnt cho đúng11field pilot

**Authorization:** sau khi owner hỏi FireAnt trùng nguồn nào và được giải thích
đề xuất dùng14:51 cho đúng11field quyền muaORS2024, nguồnFireAnt, Product/M3
pilot, owner yêu cầu “hãy thực hiện”. Stage42 thực thi phạm vi cụ thể đó, không
xin lại approval, không hiểu thành chấp nhận toàn24mappingV3 hoặc clockHOSE.
[Receipt approval](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/owner_approval_receipt.json).

**Kết quả: PASS scope.** Tạo [policy version mới](../configs/data/corporate_actions/ors_fireant_timestamp_admission_20261108_v1.json),
`OWNER_APPROVED/activated=true`, giữpolicy/proposalV1/V2/V3 cũ immutable. Scope
exact11row ID/value/field:10ORIGINAL_TERMS và1ORIGINAL_OPERATIONAL_RIGHTS_UNITS.
Không đổi điều khoản, tỷlệ, cửa sổ vận hành hoặcmetadata nguồn để lấp gap.

Mốc được áp **2024-01-16T14:51:00+07:00**, nguồnFireAnt. Builder kiểm lại raw
HTML/embeddedJSON/datePublished07:51:00Z cùnginstant, directanchor/fileURL,
PDFHTTP200hash trùngHOSE, receipt vàpriorfieldreview. MissingdateModified được
chấp nhận có phạm vi đúng11row, đểnull; không impute, không chứng nhận chưa sửa
hoặc nội dung nguyên trạng ởtimestamp2024. Không voteFireAnt/Stockbiz như hai
nguồn độc lập, không suy giờ từmedia.createdDate và không chọnclockHOSE.

[Artifact mới](../data/corporate_actions/product_m3/ors166577_fireant_timestamp_20261108_v1/manifest.json)
gồm59row:11ADMITTED/available_at=14:51+07;48DEFERRED/available_at=null. Giữ nguyên
59giá trị/scope,usable_from_date=null. 13mapping khácV3 nằm trong48row còn chờ,
không được tựaccept. Canonical/factor/strictresearch/financialpolicy không đổi.

Thêm ingestionbuilder/CLI offline vàconsumer`eligible_fields` đọcversioned
artifact choProduct/M3 pilot, không tựnối dashboard/finalbacktest. Consumer
kiểmhashes, revalidateapproval/evidence vàexactrowcontent; chỉ trả row khi
available_at<=decision_at cóoffset. Date-only/naiveclock, canonical hoặc
strictresearchpurpose bị từ chối. [Boundary thực](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/actual_overlay_boundary_review.json):
14:50:59 trả0row;14:51:00,07:51:00Z và14:51:01 trả11row.

**Kiểm tra/self-review:**69targetedtests gồm15new overlay/22timing/32acquisition+
layout;compileall vàsynthetic smoke đạt. Tests mới kiểmapproval/scopes/values,
hash/HTTP403/PDF/modified/timezone, immutableoutput, clockboundary vàoffline.
Các lượt đầu vướngTEMP Windows sandbox hoặcconsolecharmap, đã giữ log/artifact;
test chạy lại trongworkspaceTMP/UTF-8, không giảmassertion/sửalegacycode.0network,
0Markdown mới; không thu lại85/V7/7/418/archive. Kiểm1637inputpin đầu stage;
bytesdocs/DECISIONS cũ được giữsnapshot trước cập nhậtquyếtđịnh, mọiraw/policy/
proposal/packet khác không đổi. ClockHOSE vẫnOPEN;VNDIRECT403giữDEFERRED.

Evidence: [execution review](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/execution_review.json),
[verification](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/verification.json)
và [summary](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/summary.json).

**Bước tiếp theo đề xuất:** review riêng13mapping timestamp của hai sự kiện
ORS2021/cổtức2024 để nêu rõ mức chứng cứ/gap và chuẩn bị quyết định riêng.
Chưa thực hiện hoặc gộpapproval trongstage42.

## Bước43 — review13mapping timestamp của hai sự kiện ORS còn lại

**Phạm vi:** thực hiện đề xuất bước42: tái kiểm tra7mapping quyềnmua2021 và
6mapping cổtức2024, chuẩn bị quyết định riêng cho từng nhóm. Không apply13row
hoặc mở rộng approvalFireAnt11; không tìmnguồn/network/crawl lại batch.

**Kết quả: PASS review; admission MANUAL_REVIEW_REQUIRED.**

| Sự kiện/nguồn | Timestamp đề xuất (GMT+7) | Row đãreview | Giới hạn |
| --- | --- | --- | --- |
| Quyền mua2021 / Tin nhanh chứng khoán270871 | 02/06/2021 16:55:48 | 7 | Chưa archive độc lập xác nhận publication/nội dung tạiinstant2021 |
| Cổ tức2024 / MekongASEAN35579 trongCommonCrawl | 11/06/2024 11:18:31 | 6 | Capture16/6 sauex-date14/6, không chứng minh nội dung trước ex-date |

TNCK: rawHTMLHTTP200/receipt/hash giữ nguyên, NewsArticle/meta/time datetime/
epoch cùngpublication16:55:48+07, dateModified bằngpublication. Scope đúnghai
đoạn thân bài: ticker/eventtype,1:1,10.000đ,100triệucp,chuyểnnhượng25/6–9/7 và
đăngký25/6–16/7/2021. Không lấymarketprice32.300 làmgiá quyềnmua hoặc gán giờ
cho recorddate/exdate2021 còn ngoài7mapping.
[Review TNCK](../data/corporate_actions/work/ors_remaining13_timestamp_decision_review_20261108_v1/142284.source_review.json).

Mekong: tái kiểm CDX/WARCraw/HTTP206receipt/range/target/payloadSHA1/derivedHTML
hash; archivedpublisherHTTP200, JSON-LD/metapublication vàmodified khớp11:18:31.
ĐoạnORS riêng hỗtrợ6field; fullrecorddate17/6/2024 làmyearanchor choex-date14/6
theo rule đã đề xuất, không suygiờ. Không trộn paragraphESOP14,5triệu/quyềnmua
210,3triệu hoặc actualdistributed35.999.743 vào planned36triệu.

Giữ current11:18:00 và historical11:18:31 khác31giây, exactORSparagraph vẫnkhớp;
khôngaverage/floor/vote. Đề xuấtgiữ mốc lịch sử đã có trongV2/V3 cho6row; chưa
activate. Capture16/6 không phải publication11/6; khoarchive độc lập khônglà
nguồn nội dung/phiếu thời gian độc lập. DerivedHTMLarchive khôngrelabelrawlive
hoặcDOM. [Review Mekong](../data/corporate_actions/work/ors_remaining13_timestamp_decision_review_20261108_v1/171704.source_review.json).

**Điểm compatibility:**13recordproposal cũ vắngfield_scope nhưng packet gốc
có. Review mới mang rõscope từđúngpacket, giữvalue/rowidentity; khôngsửaoldrecord
hoặc tựnới semantics. Verifier đãápFireAnt ởbước42 chỉhiểu profileFireAnt/
directPDF;13row này cần adapter/testversion mới cho articletext/archive sau
acceptance, không thể đổisource/configrồi tựmởgate.

**Đề xuất để quyết định:** chấp nhận giờ do chínhbáo khai báo choProduct/M3
pilot với đúng7rowTNCK và6rowMekong, giữgappublicationhistory/firstexchange và
strictPIT. [Decision packet riêng](../data/corporate_actions/work/ors_remaining13_timestamp_decision_review_20261108_v1/separate_decision_packet.json)
cótimestamp/rowIDs/value/scope/risk; khônggiaoowner đọcchọn từngđiềukhoảnPDF.
Hiện **11ADMITTED/48DEFERRED không đổi**.24/35 chỉlàprojection nếu cảhai
nhómđượcduyệt và triểnkhai/test thànhcông, khônglàkếtquả hiệnhành.

**Kiểm tra/self-review:**37targetedtests (15overlay+22timing),compileall vàhelper
compile đạt;1676effectiveinputpin giữ nguyên, gồm activepolicy/overlay bước42.
PinDECISIONS cũ đượcresolve theo transition/snapshot đãseal ởbước42, khôngsửa
manifest lịch sử. Khôngproductioncode/policy/contractchange nên không chạy lại
smoke;0network/Markdown mới,0available_at/usable_from_date mới, khôngcanonical/
research/DATE_ONLY hoặc85/V7/7/418. [Summary](../data/corporate_actions/work/ors_remaining13_timestamp_decision_review_20261108_v1/summary.json).

**Bước tiếp theo:** quyết định riêng hai nhóm với mứcsourceassertion đãnêu.
Sau approval cụthể mới triểnkhai/testprofilemới vàoverlayversionmới; chưathực
hiệntrongstage43, khôngxinlạiapprovalFireAnt11.

## Bước44 — áp hai nhóm timestamp đã được chấp nhận vào overlay V2

**Authorization:** owner yêu cầu “hãy thực hiện” sau đề xuất dùng đúng7field
TNCK2021 và6field Mekongarchived2024 cho Product/M3 pilot, với các gap đã nêu.
Đã ghi [approval receipt](../data/corporate_actions/work/ors_remaining13_timestamp_admission_20261111_v1/owner_approval_receipt.json)
gồm event/rowIDs/timestamp và tạo [policy version mới](../configs/data/corporate_actions/ors_remaining13_timestamp_admission_20261111_v1.json).
Không xin lại cùng approval, không sửa các proposal/policy inactive lịch sử.

**Kết quả: PASS scope.** Bổ sung hai profile evidence, giữ module/CLI V1 cũ:

- LIVE_SCOPED_ARTICLE_TEXT_V1: rawHTTP200/receipt/hash, exactarticleidentity,
  publication JSON-LD/meta/time/epoch nhất quán, modified bằngpublication;
  locator/hash đoạn nguồn khớp field/value/scope đã review. Dùng đúng7field
  TNCK ở **02/06/2021 16:55:48 GMT+7**.
- ARCHIVED_SCOPED_ARTICLE_TEXT_V1: CDXrawHTTP200 vàWARC rangeHTTP206, range/
  length/target/capture/CDXdigest/WARCpayload/archivedHTTP200/derivedbody đều
  kiểm lại; publication metadata cóoffset, modified bằngpublication và scoped
  paragraphhash. Dùng đúng6field Mekong ở **11/06/2024 11:18:31 GMT+7**.

13proposal record cũ thiếufield_scope được kiểm bằng explicit scopeprovenance
từpacket đã pin; không sửaoldrecord hoặc suy scope. Builder kiểm exactgroup
approval/rowIDs, không nhận mapping/approvalgroup trùng, không thay fieldcarried.
ReaderV2 chỉ cho Product/M3pilot, revalidate toàn artifact/input/approval trước
so timestamp; date-only/naiveclock/canonical/strictresearchpurpose bị từ chối.

[Artifact mới](../data/corporate_actions/product_m3/ors_three_events_timestamp_20261111_v2/manifest.json)
có59row: **24ADMITTED/35DEFERRED**;13available_at mới,11FireAnt byte-identical,
35held cũng byte-identical.59giá trị/scope không đổi;usable_from_date=null.
Cácpolicy,raw,packet,proposal,overlay vàruntimeV1 cũ immutable. Không tựnối
dashboard/finalbacktest hoặc tính canonical/adjustmentfactor.

Giữ gap publisherassertion: TNCKsnapshot2026 chưa chứng minh timestamp/nội dung
tại2021 bằng archiveđộc lập. Mekongcapture16/6 sauexdate14/6, chưapre-excontent
proof; historical11:18:31 vàcurrent11:18:00 vẫn giữriêng, khôngaverage/floor/vote.
Archive storagekhác origin không tạo phiếu nguồn độc lập. DerivedarchiveHTML
không relabel HTTPrawlive/DOM; capture/modified/fetched/created không làm giờ
publication. Giờ công bố gốcSở/strictPIT vẫn chưa được xác nhận, DATE_ONLY vẫn dừng.

**Kiểm tra/self-review:**89targetedtests gồm20V2+15V1+22timing+32acquisition/
layout,compileall vàsynthetic smoke đạt. Khi thêmduplicate-prior guard, một
fixture banđầu đồngthời đổi current/prior gâywrongexpectederror; giữlog, tách
fixture và thêmtest riêng, không giảmassertion/guard.9boundarychecks trênartifact
thật:0trướcTNCK,7từTNCK,18từFireAnt,18tạiMekong11:18:00/11:18:30,24từ11:18:31.
0network/Markdown mới, không thu lại85/V7/7/418/archive.1695inputpin được kiểm
trước cập nhậtdocs; oldDECISIONSbytes giữsnapshot, các raw/policy/artifact khác
không đổi. [Boundary review](../data/corporate_actions/work/ors_remaining13_timestamp_admission_20261111_v1/actual_overlay_boundary_review.json),
[verification](../data/corporate_actions/work/ors_remaining13_timestamp_admission_20261111_v1/verification.json)
và [summary](../data/corporate_actions/work/ors_remaining13_timestamp_admission_20261111_v1/summary.json).

**Bước tiếp theo đề xuất:** kiểm kê35field cònchờ theo exactrevision/publication
gap, ưu tiênrecord/ex-date2021 vànotice sửađổi/kếtquả. Chưa thực hiện stage này,
không tựlan timestamp13field mới sang35field hoặc campaign mãkhác.

## Bước 45 — kiểm kê 35 trường ORS còn chờ

Đối chiếu 35 dòng chờ trong overlay V2 với hồ sơ gốc và chuỗi tài liệu của ba
sự kiện. Phân bố gồm 19 trường quyền mua 2021, 11 trường quyền mua 2024 và 5
trường cổ tức 2024. Ba dòng trong số này lưu ý kiến khác hoặc cách diễn đạt
của nguồn để phục vụ audit. [Kiểm kê từng trường](../data/corporate_actions/work/ors_deferred35_publication_inventory_20261112_v1/field_inventory.json).

- HNX 390773 xác nhận ngày không hưởng quyền 10/06/2021 và ngày đăng ký cuối
  cùng 11/06/2021. Bản chi tiết HNX thiếu giờ đăng. TPS 769 chỉ có ngày hiển thị.
  Đoạn TNCK nêu 11/6 thiếu năm và thiếu ngày không hưởng quyền.
- Hồ sơ quyền mua 2021 gắn NQ 11 với kết quả đăng ký và phân phối phần dư.
  VSDC 144117 dẫn HNX 2716, HNX 2716 dẫn QĐ 430. Giữ phạm vi riêng của 1.000 tỷ
  tăng thêm, 2.000 tỷ tổng sau thay đổi và con số 2.000 tỷ ở dòng TPS khác biệt.
- Hồ sơ quyền mua 2024 gắn NQ 05 với phần dư, văn bản UBCKNN 1914 với kết quả
  phân phối. NQ 17 sửa ủy quyền và sử dụng vốn. Chưa có dẫn chiếu xác nhận
  văn bản này sửa đơn vị quyền. Cổ tức 2024 có văn bản UBCKNN 3994 và quyết
  định HOSE 424, cùng ghi lượng thực tế 35.999.743 cổ phiếu.

Rà metadata của 10 trang TPS đã lưu và nhãn giờ trên 3 bản VSDC. TPS có ngày
hiển thị, VSDC có giờ cập nhật. Kiểm hash và receipt của 15 nguồn hỗ trợ, giữ
đúng dạng bằng chứng của từng bản. Kết quả chỉ bao phủ tập tài liệu đã quan sát.
[Rà soát nguồn](../data/corporate_actions/work/ors_deferred35_publication_inventory_20261112_v1/source_review.json).

Tổng số trường trong pilot là 24 đã gán timestamp và 35 còn chờ. Kiểm tra 1.732
hash đầu vào, 22 kiểm thử timing và compileall đạt. Đây là kiểm kê offline dựa
trên evidence có sẵn. Bước tiếp theo là tìm giờ đăng có múi giờ cho tài liệu
chứa đầy đủ hai ngày quyền mua 2021. Các thông báo kết quả và sửa đổi được xếp
theo tài liệu trong [danh sách ưu tiên](../data/corporate_actions/work/ors_deferred35_publication_inventory_20261112_v1/followup_queue.json).

## Bước 46 — tra giờ đăng cho hai ngày quyền mua ORS 2021

Phạm vi gồm ngày giao dịch không hưởng quyền 10/06/2021 và ngày đăng ký cuối
cùng 11/06/2021. Tái dùng phản hồi POST của HNX 390773, bản đã lưu của TPS 769
và HTML cùng biên nhận HTTP 200 của CafeF 1505338.

- 16 truy vấn tìm kiếm xác định CafeF hiển thị 08/06/2021 lúc 11:22 và nội
  dung khớp cả hai ngày. HTML cho thấy offset +07:00 thuộc trường
  `dateModified`, còn giờ hiển thị thiếu offset và `datePublished` vắng.
- Wayback Availability tìm thấy bản lưu của đúng URL TPS 769, lúc
  20:55:12 UTC ngày 26/07/2021. Lượt mở trả HTTP 429. Thời điểm trên là lúc
  Wayback chụp trang. Nội dung bản lưu còn chờ đọc.
- Truy vấn Common Crawl CC-MAIN-2021-25 theo đúng URL và lọc HTTP 200 cho
  CafeF trả 404. Wayback Availability cũng không trả bản lưu cho URL CafeF.
  Truy vấn TPS trả 504 hai lần, trong đó lần sau lặp lại đúng URL sau khoảng
  chờ. Kết quả chỉ áp dụng cho các truy vấn đã thực hiện.

Đã lưu body, biên nhận và hash của 6 lượt HTTP. 22 kiểm thử timing và
`compileall` đạt. Hai trường vẫn chờ, pilot hiện có 24/59 trường đã gán
timestamp. [Rà soát nguồn và bản lưu](../data/corporate_actions/work/ors_rights2021_entitlement_clock_lookup_20261112_v1/source_review.json).

Bước tiếp theo là đọc đúng bản lưu TPS 769 khi Wayback phục vụ lại. Nhóm
kết quả và giao dịch bổ sung năm 2021 có đầu mối riêng từ HNX 2716 và
quyết định 430.

## Bước 47 — giờ đăng của thông báo bổ sung ORS 2021

Thử lại đúng URL bản lưu TPS 769 sau khoảng chờ. Wayback trả 429 với body
trùng hash lần trước. Tìm trên bảng công bố HNX cho ORS từ 16 đến 31/08/2021.
Tab tin từ Sở trả hai bài, tab tin từ tổ chức phát hành trả danh sách rỗng
trong truy vấn đã chạy.

- HNX 399860 hiển thị ngày đăng 19/08/2021 12:22. PDF đính kèm trùng
  hash thông báo 2651 đã đọc. Văn bản này dẫn quyết định 430 và ghi số
  lượng đăng ký tăng thêm 100 triệu cổ phiếu, mệnh giá tăng thêm 1.000 tỷ.
- HNX 400173 hiển thị ngày đăng 23/08/2021 16:17. PDF đính kèm trùng
  hash thông báo 2716 đã đọc. Văn bản hỗ trợ 8 trường trong kiểm kê.
- CafeF hiển thị cùng phút 12:22 và đính kèm PDF trùng bytes với HNX 2651.
  Offset +07:00 nằm trong `NewsArticle.dateModified` của CafeF. Chưa tìm
  được bằng chứng xác minh múi giờ của cột HNX hoặc giờ đăng riêng của
  quyết định 430.

Đã kiểm hash và biên nhận của 9 lượt HTTP, gồm 8 lượt HTTP 200 và một lượt
429. 22 kiểm thử timing và compileall đạt. 24 trường trong pilot đã có
timestamp và 35 trường còn chờ. [Rà soát nguồn](../data/corporate_actions/work/ors_rights2021_hnx_followup_clock_20261112_v1/source_review.json).

Bước tiếp theo là tìm quy ước múi giờ của cột Ngày đăng tin, ưu tiên
bản công bố có offset cho cùng hai mã bài HNX. TPS 769 chờ Wayback
phục vụ. [Kết quả bước 47](../data/corporate_actions/work/ors_rights2021_hnx_followup_clock_20261112_v1/summary.json).

## Diễn biến mức hoàn thiện cache ORS

| Mốc inventory | HTTP raw | Toàn văn DOM | Fields-only | Chưa có detail | Có toàn văn |
| --- | --- | --- | --- | --- | --- |
| V1 — sau kiểm kê | 20 | 0 | 5 | 60 | 20/85 |
| V2 — sau 24 bài cổ phiếu | 20 | 24 | 5 | 36 | 44/85 |
| V3 — sau 41 bài còn lại | 20 | 65 | 0 | 0 | 85/85 |

Rendered DOM là text vùng bài đã hiển thị, từ tiêu đề đến trước Tin cùng tổ chức.
Receipt DOM ghi cơ chế/URL/thời điểm/hash thu nhận, không phải HTTP response receipt.
Không có HTTP status/header/body gốc cho 65 capture DOM; không relabel thành raw cache.
Chưa audit file đính kèm ngoài nội dung inline. Đủ 85 bài của snapshot không đồng
nghĩa đủ mọi sự kiện lịch sử hoặc vượt qua các gate canonical/PIT/identity.

## Phần còn thiếu và bước tiếp theo

**Đã hoàn tất:** danh sách và toàn văn85 bài trong snapshot ORS đã quan sát;
hai lỗi đường dẫn helper test legacy đã sửa tại bước19.

**Còn thiếu/chưa thực hiện:**

- 65 bài DOM chưa có HTTP raw; giữ đúng mức evidence hiện có, không tự thu lại.
- Ba candidate đã có ex-date đọc được và điều khoản khớp; còn review nguồn/trường,
  archive revision chưa được chứng nhận đầy đủ để xét canonical.
- Bản gốc HOSE79 đã lưu/khớp copy ở bước11; bước17 đã đọc thông báo HNX trực tiếp
  xác nhận ex-date2021 ở mức renderedAX. Chưa HTTPraw/PDF ký của thông báo này.
  Các PDF HNX giao dịch bổ sung hiện có trên host doanh nghiệp.
- Hai discrepancy ở bước12 đã có field selection bằng nguồn thứ ba ở bước15;
  nguồn bất đồng vẫn giữ, chưa chọn canonical. Các PDF hỗ trợ khác chưa review
  và các gate chưa mở vẫn ghi riêng; không giao owner đọc/chọn từng nguồn.
- Các possible successor vẫn unresolved; chưa áp dụng canonical hoặc hệ số điều chỉnh.
- Bước26 bổ sung timestamp Stockbiz16/01/2024 14:51:00+07:00 vớiPDF khớpHOSE79.
  Bước27 bổ sung giờ đăng bài báo2021/cổ tức2024 và ghép3packet; nguồn gốc/Sở
  vẫn chưa có timestamp first-publication xác minh, archive429 DEFERRED.
  Bước28 cóMekongtimestamp và ex-date2024 trong cùngđoạn,proposal13mapping đang
  MANUAL_REVIEW_REQUIRED. available_at chưa gán; không chuyển giờ nguồn sangSở.
  Bước21 đã lưu nhãn ngày CafeF08/06/2021 đúng event nhưng chưa đủ rule CreateDate.
  Hai lỗi helper
  của test file cache_audit di chuyển mới phát hiện chưa sửa; khác hai file bước19.
- Nhóm 7 mã lớn và 418 mã cần xác minh của toàn chiến dịch chưa được thực hiện.

Đề xuất review ba candidate đã thực hiện ở bước 10, bổ sung nguồn/lineage ở bước 11.
Packet quyết định đã chuẩn bị ở bước 12, quy tắc ủy quyền soạn ở bước 13.
Owner chỉ định quy tắc nguồn thứ ba tại bước14; bước15 đã chọn được hai field.
Workflow đã chạy ở bước16,bổ sung HNX ở bước17 và hợp nhất bundle offline/readiness
ba sự kiện ở bước18; hai lỗi helper decision_packet/cached_review sửa ở bước19.
Bước20 kiểm kê publication,bước21 khớp3news nhưng không có CreateDate đúngevent.
Bước22 owner chỉ định timestamp-first; bước23 xác minh encoding HOSE và ghi
gap clock/2021; bước25 thu hẹp tạm ngừng DATE_ONLY chỉ corporate_actions, thay
phạm vi toàn DELTA bước24. Bước26 có timestamp Stockbiz+07 khớp tài liệu166577.
Đã ghép3packet ở bước27 với hai timestamp bài báo mới cho2021/cổ tức2024.
Reviewcontract đã hoàn tất ởbước28,proposal13mapping/46hold hiệninactive.
**Bước tiếp theo:** owner quyết định quy tắc source-asserted timestamp Product/M3
pilot; nếu duyệt mới triển khai/test overlayversionmới,không dùng DATE_ONLY.
Không cần owner đọc từng PDF; chưa mở
canonical/PIT/identity hoặc thu lại85 bài.

Hai field đã chọn theo quy tắc owner chỉ định, không chờ owner review từng case.
Acceptance/methodology khác và freeze canonical tiếp tục giữ gate cần approval;
chưa tự mở canonical hoặc stage nhóm7 mã lớn/418 mã.

**Cập nhật bước 29:** chưa xin kích hoạt proposal V1 cũ. Archive Mekong mới
phát hiện cho thấy cần giữ giây 31. Bước tiếp theo là review/chuẩn bị version
proposal mới với evidence này, không thực hiện availability overlay từ mốc
11:18:00. Giờ TNCK 2021 và clock HOSE vẫn còn gap; không gán DATE_ONLY.

**Cập nhật bước30:** đã chuẩn bị V2 và kiểm tra evidence/precision; chưa activate.
Bước tiếp theo đề xuất là lookup có giới hạn cho timestamp quyền2021 còn
DEFERRED; chưa thực hiện lookup này, overlay hoặc chiến dịch mã khác.

**Cập nhật bước31:** lookup archive chưa có capture xác nhận độc lập; giữgap.
Đề xuất tiếp theo đổi sang publication timestamp của thông báo gốc HNX/TPS2021,
không tự lặp lại các query hoàn thành, activateV2 hoặc dùngDATE_ONLY.

**Cập nhật bước32:** raw HNX390773 đã lưu riêng và khớpAX cũ; chưa cótimestamp
công bố. Đề xuất tiếp xử lý11field quyền2024 thiếu directPDFbinding, giữgap2021
và không tự lặp lookup, activateV2 hoặc dùngDATE_ONLY.

**Cập nhật bước33:**11field cólinkPDF live trênStockbizlegacy; không còn chỉcached.
Bước tiếp theo là review/chuẩn bị proposal cho crossfrontendtimestamp vàmetadata
modified vắng; chưa activatehoặc gánavailability, giữgap2021/HOSE.

**Cập nhật bước 34:** đã chuẩn bị và tự review V3 cho 24 mapping/35 hold.
Bước tiếp theo là owner quyết định exact contract, composite binding và ngoại lệ
modified vắng cho đúng 11 row; chỉ sau đó mới triển khai/test overlay version mới.
Chưa có approval, availability, canonical hoặc DATE_ONLY; không tạo proposal lặp
nếu không có evidence/scope mới.

**Cập nhật bước35:** TNCK có giờ riêng17:36:15, chưa xác nhận giờStockbiz14:51.
Chưa cóapproval; nếu owner chỉ duyệt14:51 thì scope chỉ11field2024, không13field
khác củaV3. Có thể review riêng6field cóTNCK support ở17:36:15, không suy cho
toàn event hoặc autoactivate.

**Cập nhật bước36:** FUNAN cóđúngORS/noticeURL nhưng không cópublicationclock;
18/1làex-date. Nếu tìmnguồn tiếp, ưu tiên bản tinVietstock gắnexactPDF; chưa
lookup hoặc tựactivatepolicy. Scope approval14:51 nếu có vẫnchỉ11field2024.

**Cập nhật bước37:** Vietstock entrypage403,dừngroute; chưa cótargetarticleURL
hoặcpublicationclock. Nếu tiếp tục14:51, ưu tiên xác minhclockHOSE1614236 bằng
evidence mới; không lặp route403, ápfilemodified hoặc tựactivateproposal.

**Cập nhật bước38:** vấn đề clockHOSE vẫnOPEN. Cóexacthistoricalhomepagecapture
18/1/2024 nhưngreplay3attempt429; resumeđúngURLkhi routeavailable, khônglặpdiscovery
hoặc tựchọn14:51/21:51. Không hỏiowner duyệtprimaryinstant chưaxácminh.

**Cập nhật bước39:** đã thực hiện resume, vẫn429; Common Crawl tải được WARC
hợp lệ nhưng chỉ chứa meta-refresh, không phải trang chủ có clock.14:51/21:51
vẫn chưa chọn. Tiếp theo đề xuất tìm public historical clock/postedDate contract
của HOSE, giữ WaybackDEFERRED; không lặp ngay route hoặc xin duyệt giờ chưa rõ.

**Cập nhật bước40:** đã lookup public clockcontract, chưa có bằng chứng áp dụng
choAPI2024; hai API hỗ trợ trảlist[],PDFscan chỉreview12/67trang. Tiếp theo đề
xuất kiểm đầu mốiFireAnt1548002/timestamp/PDF/sourceindependence; chưa thực hiện.
HOSEclock vẫnOPEN; giữinactive,khôngDATE_ONLY hoặc lặpquery đã hoàn tất.

**Cập nhật bước41:** FireAnt có14:51+07 và directPDFhash khớpHOSE;VNDIRECT_API
403AccessDenied,dừngroute. FireAnt/Stockbiz chưa là hai nguồn độc lập. Đề xuất
tiếp reviewproposal cho đúng11field bằng directFireAntbinding; chưa thực hiện,
chưaapproval/activation và clockHOSE vẫnOPEN.

**Cập nhật bước42:** timestampFireAnt14:51+07 đã được owner chấp nhận và gán cho
đúng11field Product/M3 pilot trongoverlay mới;48field khác giữDEFERRED.69test/
compileall/synthetic đạt; giờ gốcHOSE vẫnOPEN. Tiếp theo đề xuất review riêng13
mapping của hai sự kiện còn lại, không tựmở rộngapproval hiện tại.

**Cập nhật bước43:**13mappingđãreview:7TNCK16:55:48+07 ngày02/06/2021 và
6Mekong11:18:31+07 ngày11/06/2024. Đã chuẩn bị quyếtđịnh riêng/risk, chưaapply;
actual11ADMITTED/48DEFERRED giữ nguyên. Tiếp theo là acceptance cụthể trước
sourceprofile/overlaymới, không áp lạiapprovalFireAnt hoặc tựmởgate.

**Cập nhật bước44:**13timestamp mới đãáp theo ownerapproval;artifactV2 hiện24
ADMITTED/35DEFERRED,11FireAnt/35held giữtừngbyte.89test/compileall/synthetic đạt;
không canonical/strictPIT/DATE_ONLY. Tiếp theo đềxuất kiểmkê35heldfield theo
revision/publicationgap, chưathực hiện hoặc mở rộng phạmvi.

## Bước 48 — xác minh múi giờ trên RSS HNX

RSS **Thông tin công bố từ Sở** có 50 mục từ 04 đến 12/11/2026, tất cả có
`pubDate` ghi `+0700`. So với cột **Ngày đăng tin** trong bảng UPCoM,
ba bài 641613, 60023862 và 60023852 khớp ID, tiêu đề và giờ đến phút.

Trang riêng của bài ORS 400173 ghi **23/08/2021 16:17** và liên kết đúng
PDF 2716 đã kiểm ở bước 47. Hai bài ORS 399860 và 400173 đều vắng trong
RSS hiện tại. Chỉ mục Wayback trỏ tới bản lưu RSS ngày 28/01/2021. Lượt
mở bản lưu nhận HTTP 429, nên chưa đọc được nội dung lịch sử.

Trạng thái `PARTIAL`. Hai bài ORS năm 2021 vẫn thiếu bằng chứng về múi giờ
cho 8 trường. Pilot có 24/59 trường đã gán timestamp và 35 trường chờ.
22 kiểm thử về corporate-action timing và `compileall` đều đạt.
[Hồ sơ đối chiếu](../data/corporate_actions/work/ors_hnx_followup_timezone_review_20261112_v1/source_review.json).

**Bước tiếp theo** là tìm bản lưu RSS tháng 08/2021 hoặc đặc tả chính thức
về múi giờ công bố áp dụng cho hệ thống HNX lúc đó.

## Bước 49 — tìm giờ công bố lịch sử trên RSS HNX

Trong khoảng 19–31/08/2021, Arquivo.pt trả 0 bản lưu cho ba biến thể URL RSS
HNX đã quan sát. Truy vấn chỉ mục Wayback cho URL có tiền tố `vi-vn` trả
HTTP 400. Truy vấn chỉ mục Common Crawl tháng 09/2021 trả HTTP 504. Hai phản
hồi lỗi chỉ cho biết tình trạng truy vấn, nên kết quả tìm trong hai kho này
chưa xác định.

Trang HNX xác nhận InfoFile cung cấp thông tin công bố UPCoM. Đặc tả dữ liệu
chi tiết được cấp sau khi ký hợp đồng. Tab thông tin công bố trả ba gói,
còn trang đầu tab dữ liệu quá khứ trả 0 dòng. Các trang đọc được chưa xác
minh múi giờ cho bài 399860 và 400173.

Trạng thái `PARTIAL`. 8 trường liên quan vẫn chờ timestamp. Pilot có 24/59
trường đã gán timestamp, 35 trường chờ. 22 kiểm thử corporate-action timing
và `compileall` đều đạt.
[Hồ sơ và HTTP receipts](../data/corporate_actions/work/ors_hnx_historical_timezone_lookup_20261112_v1/source_review.json).

**Bước tiếp theo** là tìm timestamp công bố cho TPS 858 hoặc nguồn gắn đúng
PDF Nghị quyết 11 ngày 22/07/2021, phục vụ 5 trường kết quả quyền mua và phân
phối phần dư.

## Bước 50 — tìm giờ công bố Nghị quyết 11 trên TPS và CafeF

Công văn 507/2021/TPS-CV trong tệp đính kèm CafeF xác nhận TPS đã công bố
Nghị quyết 11/2021/NQ-HĐQT ngày 22/07/2021 và dẫn đúng bài TPS 858. Hai
trang nghị quyết trong tệp CafeF có SHA-256 của ảnh render khớp tương ứng
với hai trang TPS. PDF CafeF có thêm một trang công văn.

Điều 1 và 2 xác nhận 99.122.718 cổ phiếu bán cho cổ đông hiện hữu,
877.282 cổ phiếu dư, giá phân phối phần dư 11.000 đồng/cổ phiếu, hạn nộp
tiền 15:00 ngày 23/07/2021 và hạn chế chuyển nhượng một năm. Công văn ghi
ngày công bố, còn trường thời gian trên chữ ký có ngữ nghĩa ký tài liệu.
CafeF hiển thị 25/07/2021 23:52 và có `dateModified` 23:52:43 `+07:00`.

Hai bảng HNX đã tra cho mã ORS từ 22/07 đến 06/08/2021 trả 0 dòng. Wayback
Availability trả rỗng cho hai biến thể URL TPS và URL CafeF. Trạng thái
`PARTIAL`, 5 trường vẫn chờ timestamp. Pilot có 24/59 trường đã gán
timestamp và 35 trường chờ. 22 kiểm thử corporate-action timing và
`compileall` đều đạt.
[Hồ sơ và HTTP receipts](../data/corporate_actions/work/ors_tps858_residual_publication_clock_20261112_v1/source_review.json).

**Bước tiếp theo** là tra giờ công bố Nghị quyết 05 ngày 21/03/2024 gắn
với bài TPS 2004 hoặc bản đính kèm đúng văn bản, cho 5 trường của đợt 2024.

## Bước 51 — tìm giờ công bố Nghị quyết 05 của ORS năm 2024

Đã đọc 7 trang API HOSE cho hai khoảng 21–22/03 và 25–26/03/2024.
580 dòng trả về chứa 579 ID riêng, với một ID lặp ở kỳ đầu. Bài ORS
1688391 khớp giữa danh sách, chi tiết và danh mục tệp. PDF HOSE trùng
SHA-256 với PDF CafeF 1965156. Ba trang nghị quyết có các ảnh nhúng trùng
SHA-256 với PDF TPS 2004. Công văn 11/2024/TPS-CBTT ghi TPS công bố trên
bài 2004 ngày 21/03/2024. Mốc 15:18:28 +07:00 nằm ở trường giờ ký công văn.

`postedDate` của HOSE là `1711376400`. Hàm hiển thị của HOSE cho 14:20
ngày 25/03/2024. Nếu đọc số này là Unix timestamp rồi đổi sang giờ Việt Nam
thì ra 21:20. Cả hai mẫu ORS 1688391 và 1614236 có chênh 7 giờ khi so
`postedDate` của bài với `createdDate` của tệp và khi so hai trường
`publishFrom`. Quan sát này chưa xác minh được đồng hồ công bố lịch sử.
CafeF có `dateModified` lúc 00:00 và Wayback chưa trả bản lưu URL TPS.

Trạng thái `PARTIAL`. 5 trường đợt quyền mua 2024 vẫn chờ timestamp.
Pilot có 24/59 trường đã gán timestamp và 35 trường chờ. 22 kiểm thử
corporate-action timing và `compileall` đều đạt.
[Hồ sơ nguồn và HTTP receipts](../data/corporate_actions/work/ors_tps2004_residual_publication_clock_20261112_v1/source_review.json).

**Bước tiếp theo** là tìm giờ công bố gắn đúng bài TPS 2016 hoặc bản công
bố báo cáo kết quả chào bán và công văn UBCKNN 1914, phục vụ một trường
kết quả phân phối của đợt 2024.

## Cách cập nhật nhật ký sau mỗi stage

Ghi nối tiếp một bước mới theo thứ tự thực hiện, gồm: ngày, phạm vi/mục tiêu,
việc đã làm, kết quả và trạng thái, kiểm tra đã chạy, evidence/artifact, phần còn
thiếu và bước tiếp theo đề xuất. Chỉ ghi stage chưa chạy ở dạng đề xuất.

Giữ các kết quả lịch sử, kể cả lỗi và PARTIAL. Nếu có đính chính, ghi rõ mốc đính
chính và lý do, không sửa evidence immutable. Cập nhật bảng kết quả hiện tại và
đường dẫn bàn giao sau mỗi stage; không tự chạy stage kế tiếp.
