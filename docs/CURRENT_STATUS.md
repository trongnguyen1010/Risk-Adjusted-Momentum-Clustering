# Trạng thái hiện tại — M1 market foundation reported

Nhật ký chi tiết corporate actions theo từng bước nằm tại
[NHAT_KY_CORPORATE_ACTIONS.md](NHAT_KY_CORPORATE_ACTIONS.md).

## Corporate action — giờ công bố Nghị quyết 05 của ORS năm 2024, 12/11/2026

Bước 51 tìm được bài HOSE **1688391**. PDF tải từ HOSE trùng SHA-256
với bản CafeF 1965156. Ba trang nghị quyết chứa cùng các ảnh scan với PDF
của TPS 2004. Công văn 11/2024/TPS-CBTT xác nhận ngày công bố trên website
TPS là 21/03/2024 và ghi đúng URL bài 2004.

Trường `postedDate` của HOSE cho giờ hiển thị 25/03/2024 **14:20** theo
hàm định dạng của trang. Nếu số đó biểu diễn Unix timestamp thực thì khi
đổi sang giờ Việt Nam sẽ là **21:20**. Kiểm tra cùng mẫu tháng 01/2024
cho thấy hai trường của bản tin lệch đúng 7 giờ so với các trường tương
ứng trong bản ghi tệp, song chưa xác minh được quy ước lịch sử. CafeF có
`dateModified` lúc 00:00 và công văn có giờ ký. Cả hai mốc này chưa xác
nhận giờ công bố. 5 trường vẫn chờ, pilot có 24/59 trường đã gán timestamp.
[Hồ sơ đối chiếu](../data/corporate_actions/work/ors_tps2004_residual_publication_clock_20261112_v1/source_review.json).

**Bước tiếp theo** là tra timestamp công bố báo cáo kết quả chào bán 2024
hoặc công văn UBCKNN 1914 trên TPS 2016 và bản đăng cùng tài liệu. Đây là
nhóm riêng gồm một trường kết quả phân phối.
[Kết quả bước 51](../data/corporate_actions/work/ors_tps2004_residual_publication_clock_20261112_v1/summary.json).

## Corporate action — giờ công bố Nghị quyết 11 của ORS năm 2021, 12/11/2026

Bước 50 tìm thấy bản đăng lại CafeF 1392871. Tệp đính kèm gồm công văn
507/2021/TPS-CV và hai trang Nghị quyết 11. Cả hai trang khớp với bản TPS
khi so sánh bản render. Công văn xác nhận TPS đã công bố nghị quyết trên
bài 858 ngày 22/07/2021, đến độ chính xác ngày.

CafeF hiển thị 25/07/2021 23:52, với `dateModified` là
`2021-07-25T23:52:43+07:00`. Giờ công bố vẫn chưa xác minh được. Hai bảng
HNX trong kỳ 22/07–06/08 trả 0 dòng ORS và chỉ mục Wayback trả rỗng cho ba
URL đã tra. 5 trường liên quan vẫn chờ timestamp. Pilot có 24/59 trường
đã gán timestamp và 35 trường chờ.
[Hồ sơ đối chiếu](../data/corporate_actions/work/ors_tps858_residual_publication_clock_20261112_v1/source_review.json).

**Bước tiếp theo** là tìm giờ công bố của Nghị quyết 05 ngày 21/03/2024
trên TPS 2004 hoặc bản đăng khác đính kèm đúng văn bản, phục vụ 5 trường
riêng của đợt quyền mua 2024.
[Kết quả bước 50](../data/corporate_actions/work/ors_tps858_residual_publication_clock_20261112_v1/summary.json).

## Corporate action — tìm bản lưu RSS HNX tháng 08/2021, 12/11/2026

Bước 49 tra các URL RSS HNX đã biết trong khoảng 19–31/08/2021. Arquivo.pt
trả 0 kết quả cho cả ba biến thể URL. Chỉ mục Wayback trả HTTP 400, còn
chỉ mục Common Crawl tháng 09/2021 trả HTTP 504, nên kết quả ở hai kho này
chưa xác định.

HNX xác nhận InfoFile phân phối thông tin công bố UPCoM và cung cấp đặc tả
chi tiết sau khi ký hợp đồng. Trang hướng dẫn và danh mục công khai đã kiểm
chưa cho thấy quy ước múi giờ của hai bài ORS 399860 và 400173. 8 trường
gắn với hai bài vẫn chờ bằng chứng múi giờ. Pilot có 24/59 trường đã gán
timestamp. [Hồ sơ tra cứu](../data/corporate_actions/work/ors_hnx_historical_timezone_lookup_20261112_v1/source_review.json).

**Bước tiếp theo** là tìm giờ công bố gắn đúng TPS 858 hoặc PDF Nghị quyết
11 ngày 22/07/2021 để xử lý 5 trường về kết quả quyền mua và phân phối phần
dư. Hai bài HNX trên tiếp tục chờ nguồn lịch sử mới.
[Kết quả bước 49](../data/corporate_actions/work/ors_hnx_historical_timezone_lookup_20261112_v1/summary.json).

## Corporate action — múi giờ trên RSS HNX và hai bài ORS 2021, 12/11/2026

Bước 48 kiểm tra RSS **Thông tin công bố từ Sở** của HNX. Cả 50 mục trong
feed ngày 04–12/11/2026 đều ghi `pubDate` với offset `+07:00`. Đối chiếu cùng
ID và tiêu đề, cả 3 bài lấy từ bảng UPCoM ngày 11–12/11 đều khớp đến phút
với cột **Ngày đăng tin**.

Hai bài ORS 399860 và 400173 vắng trong feed này. Trang riêng của bài
400173 xác nhận 23/08/2021 16:17 và cùng tệp PDF 2716, với giờ hiển thị đến
phút. Wayback trả về đầu mối bản lưu RSS ngày 28/01/2021, còn lượt mở trả
HTTP 429. Múi giờ của hai bài tháng 08/2021 vẫn chờ xác minh. 8 trường gắn
với hai bài vẫn chờ timestamp. Pilot hiện có 24/59 trường đã gán timestamp.
[Bằng chứng và kết quả đối chiếu](../data/corporate_actions/work/ors_hnx_followup_timezone_review_20261112_v1/source_review.json).

**Bước tiếp theo** là tìm bản lưu RSS HNX vào tháng 08/2021 hoặc tài liệu
chính thức quy định múi giờ của hệ thống công bố HNX trong giai đoạn đó.
[Kết quả bước 48](../data/corporate_actions/work/ors_hnx_followup_timezone_review_20261112_v1/summary.json).

## Corporate action — giờ đăng của hai thông báo HNX về ORS 2021, 12/11/2026

Bước 47 xác minh hai giờ hiển thị trong cột **Ngày đăng tin** của bảng công
bố HNX cho ORS. Hai PDF tải trực tiếp từ chi tiết HNX trùng SHA-256 với các
bản đã đọc trong hồ sơ.

| Bài HNX | Ngày giờ hiển thị | Văn bản đính kèm |
| --- | --- | --- |
| 399860 | 19/08/2021 12:22 | Thông báo 2651, dẫn quyết định 430 |
| 400173 | 23/08/2021 16:17 | Thông báo 2716 về giao dịch bổ sung |

Các văn bản đối chiếu được với 8 trường còn chờ. Cột HNX có độ chính xác
đến phút và chưa xác minh được múi giờ. CafeF ghi cùng phút 12:22 và đính kèm
đúng PDF 2651, còn offset +07:00 nằm trong trường sửa bài của CafeF. Thời
điểm đăng riêng của quyết định 430 vẫn chưa xác minh. Lượt mở lại bản lưu
TPS 769 trả HTTP 429. Pilot hiện có 24/59 trường được gán timestamp.
[Hồ sơ nguồn và ánh xạ trường](../data/corporate_actions/work/ors_rights2021_hnx_followup_clock_20261112_v1/source_review.json).

**Bước tiếp theo** là tìm quy ước múi giờ của cột HNX hoặc bản công bố có
offset cho cùng hai mã bài 399860 và 400173. Bản lưu TPS 769 tiếp tục chờ
Wayback phục vụ. [Kết quả bước 47](../data/corporate_actions/work/ors_rights2021_hnx_followup_clock_20261112_v1/summary.json).

## Corporate action — tra giờ đăng cho hai ngày quyền mua ORS 2021, 12/11/2026

Bước 46 tìm được bản lưu Wayback của đúng URL TPS 769, chụp lúc
**20:55:12 UTC ngày 26/07/2021**. Lượt mở bản lưu trả HTTP 429, nên nội dung
và giờ đăng trong bản lưu vẫn chưa được xác minh. Hai truy vấn Common Crawl
cho URL TPS trả HTTP 504. Với URL CafeF, Wayback không trả bản lưu và
truy vấn chính xác trên chỉ mục tháng 6/2021 trả HTTP 404.

HNX 390773 và bản tin CafeF 1505338 đều ghi ngày giao dịch không hưởng
quyền **10/06/2021** và ngày đăng ký cuối cùng **11/06/2021**. CafeF hiển thị
**08/06/2021 lúc 11:22**. HTML đã lưu thiếu `datePublished` và offset cho giờ
hiển thị. Giá trị `11:22:19+07:00` có nhãn `dateModified`. Cả hai trường
tiếp tục chờ timestamp đủ điều kiện, với 24/59 trường đã gán timestamp
trong pilot. [Hồ sơ nguồn](../data/corporate_actions/work/ors_rights2021_entitlement_clock_lookup_20261112_v1/source_review.json).

Bước tiếp theo là mở lại đúng bản lưu TPS 769 khi dịch vụ Wayback phục vụ.
Trong khi đó, thông báo HNX 2716 và quyết định 430 là đầu mối cho lượt tra
riêng về kết quả và giao dịch bổ sung năm 2021.
[Kết quả bước 46](../data/corporate_actions/work/ors_rights2021_entitlement_clock_lookup_20261112_v1/summary.json).

## Corporate action — kiểm kê 35 trường ORS còn chờ, 12/11/2026

Bước 45 hoàn tất đối chiếu 35 trường đang chờ trong overlay V2. Cả 35 có giá
trị trong hồ sơ đối chiếu, gồm 3 dòng lưu khác biệt hoặc cách diễn đạt của
nguồn. Hiện có 24/59 trường được gán timestamp cho Product/M3 pilot.
[Kiểm kê từng trường](../data/corporate_actions/work/ors_deferred35_publication_inventory_20261112_v1/field_inventory.json).

| Sự kiện | Trường chờ | Tài liệu cần xác minh giờ đăng |
| --- | ---: | --- |
| Quyền mua 2021 | 19 | HNX 390773 và TPS 769 cho hai ngày quyền. NQ 11, QĐ 430 và HNX 2716 cho kết quả, phần dư và giao dịch bổ sung |
| Quyền mua 2024 | 11 | VSDC 166577 cho định danh quyền. NQ 05 và văn bản UBCKNN 1914 cho phần dư và kết quả |
| Cổ tức 2024 | 5 | Báo cáo kết quả 252, văn bản UBCKNN 3994 và quyết định HOSE 424 |

Hai ngày được ưu tiên là ngày giao dịch không hưởng quyền **10/06/2021** và
ngày đăng ký cuối cùng **11/06/2021**. HNX 390773 xác nhận cả hai ngày. Bản chi
tiết đã lưu thiếu giờ đăng. TPS 769 có ngày hiển thị. TNCK chỉ nêu 11/6 ở
đoạn liên quan và thiếu ngày không hưởng quyền.

Đối chiếu lại 10 trang TPS đã lưu cho thấy chỉ có ngày hiển thị. Ba giờ trên
VSDC mang nhãn “Cập nhật”. Các mốc hạn nộp tiền, ngày ký và ngày hiệu lực được
ghi theo đúng vai trò của chúng. Đã kiểm hash và biên nhận của 15 nguồn hỗ trợ.
[Bằng chứng nguồn](../data/corporate_actions/work/ors_deferred35_publication_inventory_20261112_v1/source_review.json).

**Bước tiếp theo** là tra một bản tin công khai hoặc bản lưu gắn với HNX 390773
hoặc TPS 769, có cả hai ngày đầy đủ và giờ đăng kèm múi giờ. Các thông báo hậu
sự kiện có đầu mối tra cứu riêng trong
[danh sách ưu tiên](../data/corporate_actions/work/ors_deferred35_publication_inventory_20261112_v1/followup_queue.json).
Kết quả hiện giới hạn ở các bản đã lưu.

## Corporate action — áp 13 trường TNCK/Mekong, 11/11/2026

Bước44 **PASS trong phạm vi owner chấp nhận**. Yêu cầu “hãy thực hiện” sau
đề xuất bước43 đã được ghi thành
[approval hai nhóm](../data/corporate_actions/work/ors_remaining13_timestamp_admission_20261111_v1/owner_approval_receipt.json).
[Policy mới](../configs/data/corporate_actions/ors_remaining13_timestamp_admission_20261111_v1.json)
thêm đúng7field quyền mua2021/TNCK **02/06/2021 16:55:48 GMT+7** và6field
cổ tức2024/Mekong archived **11/06/2024 11:18:31 GMT+7**, chỉ cho Product/M3 pilot.

[Artifact V2](../data/corporate_actions/product_m3/ors_three_events_timestamp_20261111_v2/summary.json)
hiện có **24ADMITTED/35DEFERRED trên59row**.11FireAnt và35held giữ nguyên từng
byte so với V1;59giá trị/scope không đổi,usable_from_date=null. Raw, proposal,
policy/overlay/runtime V1 không sửa. V2 reader kiểm hashes, approval, metadata
publication/modified và field locator; profile live text và archive tách đúng
loại evidence, không biến WARC-derivedHTML thành HTTPraw live/DOM.

Giữ nguyên gap: TNCK chưa archive độc lập xác nhận năm2021; Mekong capture16/6
sau ex-date14/6, metadata lịch sử11:18:31 khác current11:18:00. Timestamp được
owner chấp nhận theo publisher assertion, không phải giờ gốcSở hoặc chứng nhận
strictPIT. Không dùng capture/created/modified/fetched time, không DATE_ONLY,
canonical/factor/strictresearch, không tựnối dashboard/finalM3backtest.

**Boundary thực:** trước TNCK16:55:48 đọc0row; đúng giờ đọc7; từ FireAnt14:51
đọc18; Mekong11:18:00/11:18:30 vẫn18, đúng11:18:31 đọc24.89targetedtests
(20V2+15V1+22timing+32acquisition/layout),compileall vàsynthetic smoke đạt.
0network/Markdown mới;1695inputpin kiểm trước cập nhật docs, riêngDECISIONS
giữ oldbytes trongsnapshot theo quy trình. Không thu lại85/V7/7/418/archive.
[Summary stage](../data/corporate_actions/work/ors_remaining13_timestamp_admission_20261111_v1/summary.json)
và [boundary review](../data/corporate_actions/work/ors_remaining13_timestamp_admission_20261111_v1/actual_overlay_boundary_review.json).

**Bước tiếp theo đề xuất:** kiểm kê35field còn chờ theo đúng revision và gap
publication, ưu tiên record/ex-date2021 và thông báo sửa đổi/kết quả. Chưa thực
hiện trongstage44; không suy timestamp từfield đã được duyệt hoặc mở campaign mã khác.

## Corporate action — review riêng 13 mapping còn ở proposal, 08/11/2026

Bước43 **PASS phần review; admission13row vẫn MANUAL_REVIEW_REQUIRED**.
Đã tái kiểm tra đúng13mapping bằng evidence offline đã pin, không gọi network
hoặc mở rộng approvalFireAnt11. [Decision packet](../data/corporate_actions/work/ors_remaining13_timestamp_decision_review_20261108_v1/separate_decision_packet.json)
và [summary](../data/corporate_actions/work/ors_remaining13_timestamp_decision_review_20261108_v1/summary.json).

| Nhóm đề xuất quyết định riêng | Giờ nguồn khai báo (GMT+7) | Số field | Gap còn giữ |
| --- | --- | --- | --- |
| Quyền muaORS2021, TNCK270871 | 02/06/2021 16:55:48 | 7 | Chưa có archive độc lập xác nhận timestamp/nội dung tạiinstant2021 |
| Cổ tứcORS2024, bản lưu Mekong35579 | 11/06/2024 11:18:31 | 6 | Archive16/6 sau ex-date14/6; chưa chứng minh nội dung cótrướcex-date |

TNCKrawHTTP200/receipt/hash: NewsArticle/meta/time/epoch publication khớp,
modified bằngpublication; đúng2đoạn điều khoản hỗ trợ7field. Không nhận thêm
recorddate2021 còn thiếu full-yearcontext, ex-dateHNX chưa publicationclock
hoặc marketprice32.300 vào giá quyềnmua10.000.

Mekong: kiểm độc lậpCDX→WARCresponse→HTTPbody, range/target/digest/hashes đều
khớp; metadata bản lưu11:18:31+07, modified bằngpublication. Đúng đoạnORS hỗtrợ
6field; nămex-date14/6 lấy từ fullrecorddate17/6/2024 cùng đoạn, giữ rule cũ.
Bản hiện tại11:18:00 khác31giây, cùng đoạnORS; giữ snapshot riêng, không average/
làmtròn/vote. Capturetime16/6 không phải publication; archive storage độc lập
không tạo phiếu nguồn công bố thứba. DerivedarchiveHTML không là rawlive/DOM.

13record proposal cũ thiếufield_scope; packet gốc đã có. Review mới mang rõ
scope từ packet và đối chiếu nguyênvalue, không sửa13record cũ. Verifier hiện
hành chỉ hỗtrợ FireAnt/directPDF; nếu owner chấp nhận13row thì cần adapter/test
phiên bản mới cho directarticletext vàarchiveprofile, không nhét vào configFireAnt.

**Đề xuất:** chấp nhận từng nhóm theo mức **giờ do chính publisher khai báo cho
Product/M3 pilot**, giữ các gap nêu trên; không gọi là giờ công bố đầu tiên của
Sở hoặc chứng nhậnstrictPIT. Đây là13row được chuẩn bị để quyết định, chưa
được gánavailable_at. Thực tế vẫn11ADMITTED/48DEFERRED;24/35 chỉ là dự kiến nếu
cả hai nhóm được duyệt và triển khai/test thành công.

37targetedtests/compileall/helpercompile đạt;1676effectiveinputpin giữ nguyên,
gồm activeFireAntpolicy/overlay.0network/Markdown mới, không đổi productioncode/
policy/proposal, không chạy lại smoke hoặc85/V7/7/418. Chưa có timestampapproval
mới; không dùngDATE_ONLY/canonical/researchgate.

**Bước tiếp theo:** owner quyết định riêng7rowTNCK và6rowMekong với hai mốc giờ
và rủi ro cụ thể trên. Sau acceptance mới triển khai/test sourceprofile mới và
overlayversion mới. Stage43 dừng ở hồ sơ quyết định; không xin duyệt lại11rowFireAnt.

## Corporate action — áp timestamp FireAnt cho 11 field pilot, 08/11/2026

Bước42 **PASS trong phạm vi owner đã chấp nhận**: dùng timestamp FireAnt
**16/01/2024 14:51:00 GMT+7** cho đúng11field quyền muaORS2024. Approval là yêu
cầu thực hiện ngay sau đề xuất cụ thể, được ghi tại
[receipt](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/owner_approval_receipt.json).
[Policy mới](../configs/data/corporate_actions/ors_fireant_timestamp_admission_20261108_v1.json)
chỉ active cho phạm vi này; proposalV1/V2/V3 và13mapping khác không được tựduyệt.

[Artifact Product/M3 pilot](../data/corporate_actions/product_m3/ors166577_fireant_timestamp_20261108_v1/summary.json)
có59row:11ADMITTED vớiavailable_at=14:51+07,48DEFERRED vớiavailable_at=null.
59giá trị/scope giữ nguyên; không suyusable_from_date hoặc dùngDATE_ONLY. Nguồn
ghi rõFireAnt/sourceassertion/directPDF hashmatch; không relabel thành giờ gốc
HOSE. ClockHOSE vẫnOPEN, chưa cóhistoricalsnapshot/dateModified/independentfeed
certification. Owner chấp nhận mức chứng cứ này riêng choProduct/M3 pilot.

Đã thêm offlinebuilder/CLI vàconsumer`eligible_fields` để đọcartifact theoexact
timestamp; không recompute model/feature hoặc tự nối dashboard/finalM3backtest.
Consumer kiểminput/outputhashes, approvalscope, giá trịfield và directPDFbinding;
strictresearch/canonicalpurpose bị từ chối. Boundaryartifact thật14:50:59 đọc0,
14:51:00 và07:51:00Z đọc11; giữ48field khác chờ xử lý.

69targetedtests (15overlay+22timing+32acquisition/layout),compileall vàsynthetic
smoke đạt. Lượt đầu vướng WindowsTEMP/consoleencoding đã giữ log/artifact;
chạy lại bằngworkspaceTMP/UTF-8, không sửalegacyassertion.0network/Markdown mới,
không thu lại85/V7/7/418 hoặc mởcanonical/factor/strictresearch.1637inputpin lúc
đầu được kiểm; riêngdocs/DECISIONS cập nhật hợp lệ đã giữ nguyên bytes cũ trong
snapshot, các raw/policy/proposal/packet khác không đổi.
[Execution review](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/execution_review.json)
và [summary](../data/corporate_actions/work/ors_fireant_timestamp_admission_20261108_v1/summary.json).

**Bước tiếp theo đề xuất:** review riêng13mapping timestamp của hai sự kiện
ORS2021 vàcổtức2024 còn ởV3, nêu rõ bằng chứng/gap và chuẩn bị quyết định riêng.
Chưa thực hiện trongstage42; không mở rộng approval11field hiện tại hoặc chạy
campaign mã khác.

## Corporate action — FireAnt và VNDIRECT quyền mua ORS2024, 08/11/2026

Bước 41 **PARTIAL; FireAnt có direct timestamp/PDF binding, VNDIRECT DEFERRED**.
Đã kiểm tra cả hai nguồn theo yêu cầu owner. Clock gốc HOSE1614236 vẫn OPEN;
chưa chọn14:51/21:51 cho Sở và chưa activate admission/availability.
[Summary](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/summary.json).

**FireAnt:** đọc đúng bài22811809 qua HTTP200; tiêu đề/mã ORS/nguồn HSX khớp.
`initialPost.date=2024-01-16T14:51:00+07:00`, JSON-LD
`datePublished=2024-01-16T07:51:00.000Z`; hai biểu diễn cùng instant, offset
được nguồn ghi rõ. Bài có anchor tải PDF trực tiếp và `files[].fileContentUrl`
đều dẫn `https://mobiv2.fireant.vn/News/NewsAttachedFile/1548002`.
PDFHTTP200/526.299byte có SHA-256
`364beb609427cb4b451bbffed5c2718285b9e683dd1371e2f405670f06ae7787`, trùng nguyên
bản HOSE đã pin. Đây là HTTPraw HTML/embeddedJSON và PDFraw; không claim review
DOM hoặc historicalcapture2024. DateModified vẫn vắng, không suy nội dung chưa
từng sửa. [Review binding](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/fireant_target_timestamp_binding_review.json).

Giờ14:51 của FireAnt khớp Stockbiz. Tuy nhiên cả hai cùng postID22811809 và
ảnh1548002 trên hostFireAnt, attachment khớp legacyNewsID1548002. Stockbiz còn
link sang trang thảo luận mãORS trênFireAnt, không phải link trực tiếp hai bài.
Đây là dấu hiệu cùng/quan hệ feed; chưa xác minh ownership hoặc kiến trúc feed,
**không tính thành hai phiếu độc lập** hoặc xác nhận first-publication HOSE.
[Review tính độc lập](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/source_independence_review.json).

**VNDIRECT:** trangORS và2bundleJS công khai HTTP200; từ bundle xác định API
`https://api-finfo.vndirect.com.vn/v4/news`. Query giới hạn ORS/ngày16/1/2024
trảHTTP403/body13byte “Access Denied”; dừng provider route ngay, không retry/
alias/browser/token/cookie. Chưa trả bản tin/timestamp hoặc xác minh semantics
filter; không kết luận VNDIRECT thiếu bài. RootmobileFireAnt404 cũng không phải
bằng chứng bài FireAnt vắng. [Route review](../data/corporate_actions/work/ors_rights2024_fireant_vndirect_lookup_20261108_v1/vndirect_route_review.json).

8request córeceipt:6HTTP200/1HTTP404/1HTTP403;16query web.22timingtests/compileall
đạt,1584inputpin giữ nguyên. Không thay pipeline nên không chạy lại smoke;
0Markdown mới,0availability/canonical/DATE_ONLY, không đổi proposalV1/V2/V3 hoặc
59field cũ. Không thu lại85/V7/7/418 hay retryarchive.

**Bước tiếp theo đề xuất:** review/cập nhật proposal inactive cho đúng11field
quyền2024, dùng source-asserted FireAnt timestamp với direct article→PDF binding
trong cùngHTML. Giữ gap historicalvintage/dateModified và clockHOSE; không
coi là sourcevote độc lập hoặc tựduyệt13mapping khácV3. Admission là thay đổi
nhạy cảm methodology, `MANUAL_REVIEW_REQUIRED` trước activation; stage này chỉ
thu/review evidence, chưa tạo/activate proposal mới hoặc xin duyệt giờ chưa rõ.

## Corporate action — tìm clock contract công khai HOSE, 08/11/2026

Bước 40 **PARTIAL; clock HOSE1614236 vẫn OPEN**. Đã thực hiện lookup tài liệu
kỹ thuật/lịch sử công khai theo đề xuất bước39; chưa tìm được contract có căn
cứ áp dụng cho publication `postedDate` năm2024 trong phạm vi quan sát.
[Review](../data/corporate_actions/work/ors_hose_public_clock_contract_lookup_20261108_v1/public_clock_contract_review.json)
và [summary](../data/corporate_actions/work/ors_hose_public_clock_contract_lookup_20261108_v1/summary.json).

- 15query web; các kết quả về giờ giao dịch hoặc báo đăng lại không được dùng
  làm contract clock API. Tin về đổi website năm2025 chỉ là đầu mối, chưa chứng
  minh ngày migration hoặc encoding của dữ liệu cũ.
- Từ pinnedJS suy ra đúng public UI/API route Điều khoản sử dụng và FAQ. Cả hai
  HTTP200, mỗi body132byte là JSON `list:[]`, `totalCount:0`; không phải body
  rỗng, cũng không chứng minh tài liệu vắng trên toàn nguồn. Không gọi private
  data-feed hoặc đoán Swagger/auth endpoint.
- Lưu PDF quy chế CBTT340/2016 trên host HOSE, HTTP200/raw/hash/receipt. Đây là
  scan67trang, text layer trích xuất0ký tự. Đã render/đọc trực quan trang1–12,
  tập trung trang4/6/7 để phân biệt báo cáo gửi/nhận và thông tin đăng website.
  Chưa có timezone/Unix API contract ở phần đã đọc; không claim đã audit cả67
  trang hoặc xác nhận hiệu lực/khả năng áp dụng choAPI2024.
- Một query public UI/API giới hạn cửa sổ28/4–5/5/2025 trả19record HOSE; thấy
  thông báo ngày đầu KRX, không phải đặc tả publication clock. Không phân trang
  hoặc suy giờ vận hành KRX thành giờ công bố bài.

4request thu nhận córeceipt, đềuHTTP200;22timingtests/compileall đạt,1535inputpin
giữ nguyên. Không thay pipeline nên không chạy lại smoke.0Markdown mới,0timestamp
được chọn/availability/canonical/DATE_ONLY; proposalV1/V2/V3 giữ nguyên inactive.
Không retryWayback hoặc thu lại85/V7/7/418.14:51+07 và21:51+07 cho HOSE chưa chọn;
giờ riêng Stockbiz14:51+07 không bị relabel thành first-publication HOSE.

**Bước tiếp theo đề xuất:** tra bản tin FireAnt công khai từ đầu mối
`NewsID1548002` trong URL ảnh bài Stockbiz đã pin; kiểm tra timestamp, exactPDF
binding và quan hệ dữ liệu với Stockbiz. Đây mới là imageID, chưa xác nhận URL
bản tin hoặc tính độc lập. Nếu dùng chung feed thì không tính là phiếu nguồn
độc lập; giờ đăng lại cũng không tự giải quyết clock gốc HOSE.
[Đầu mối và giới hạn](../data/corporate_actions/work/ors_hose_public_clock_contract_lookup_20261108_v1/next_evidence_lead.json).
Chưa thực hiện lookupFireAnt trong stage này; giữ vấn đề HOSE OPEN, không yêu
cầu owner phê duyệt một giờ chưa xác minh hoặc lặp lookup clock vừa hoàn tất.

## Corporate action — resume archive clock HOSE, 08/11/2026

Bước 39 **PARTIAL; vấn đề giờ công bố HOSE vẫn OPEN**. Đã resume đúng capture
Wayback đã tìm được; vẫn HTTP429, body khớp lần trước, không có Retry-After.
Không lặp retry ngay hoặc đổi client/host để né. Chưa đọc được HTML capture
18/01/2024. [Review evidence](../data/corporate_actions/work/ors_hose_archive_clock_resume_20261108_v1/historical_home_capture_review.json).

Đã kiểm tra thêm Common Crawl độc lập trong cùng stage:

- Index CC-MAIN-2024-10 trả một record `http://hsx.vn/` ngày 01/03/2024.
  Tải đúng range WARC 633 byte, HTTP206; digest payload khớp CDX và WARC.
  Body HTTP lưu trữ chỉ 103 byte, chứa meta-refresh sang `https://www.hsx.vn`.
  Đây là HTML trích từ archive, không phải HTTP raw mới của HOSE hay rendered
  DOM; chưa có nội dung trang chủ HTTPS, nhãn múi giờ hoặc bài ORS.
- Index CC-MAIN-2024-18 cho đích HTTPS trả404 với “No Captures found”. Chỉ kết
  luận cho query exact root/status200 của index này, không suy vắng mọi archive.

Vì vậy chưa chọn **14:51+07 hay 21:51+07 ngày16/01/2024 cho HOSE1614236**.
Stockbiz vẫn khai báo giờ riêng14:51+07; chưa được đổi thành first-publication
HOSE. Không dùng capture time, HTTP Date, file modified hoặc media created để
lấp gap; chưa yêu cầu owner duyệt một instant HOSE chưa xác minh.

4request trong effective budget5 với addendum lưu riêng, 22timingtests và
compileall đạt. Đã xác minh1489inputpin giữ nguyên; không thay pipeline, không
chạy lại synthetic smoke. Không tạo Markdown mới, không đổi/activate proposal
V1/V2/V3, không gán availability/canonical/DATE_ONLY hoặc thu lại85/V7/7/418.
[Summary](../data/corporate_actions/work/ors_hose_archive_clock_resume_20261108_v1/summary.json).

**Bước tiếp theo đề xuất:** tìm tài liệu kỹ thuật/lịch sử công khai của HOSE
nêu rõ clock/timezone và cách mã hóa trường publication `postedDate`, có căn cứ
áp dụng cho hệ thống năm2024. Tái dùng API/formatter đã pin; không coi lệch7giờ
là bằng chứng tự đủ. Giữ replay Wayback DEFERRED, không lặp ngay các query vừa
hoàn tất. Chưa thực hiện lookup contract mới hoặc mở gate trong stage này.

## Corporate action — xác minh clock HOSE 1614236, 08/11/2026

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

## Corporate action — lookup bản tin Vietstock quyền mua 2024, 07/11/2026

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

## Corporate action — đối chiếu thêm nguồn FUNAN quyền mua 2024, 07/11/2026

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

## Corporate action — nguồn báo khác đối chiếu giờ quyền mua 2024, 07/11/2026

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

## Corporate action — đề xuất V3 cho 24 mapping timestamp ORS, 07/11/2026

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

## Corporate action — live article/PDF binding quyền mua 2024, 07/11/2026

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

## Corporate action — thông báo gốc HNX/TPS quyền mua 2021, 07/11/2026

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

## Corporate action — tra cứu archive quyền mua 2021, 07/11/2026

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

## Corporate action — proposal V2 giữ chính xác timestamp lịch sử, 07/11/2026

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

## Corporate action — đối chiếu nguồn bổ sung và archive lịch sử, 07/11/2026

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

## Corporate action — review contract timestamp theo field, 07/11/2026

Bước28 review hoàn tất, activation **MANUAL_REVIEW_REQUIRED**. [Summary](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/summary.json),
[13mapping đề xuất](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/proposed_field_bounds.json)
và [proposal inactive](../configs/data/corporate_actions/ors_source_timestamp_contract_proposal_20261107_v1.json)
đã chuẩn bị để owner quyết định một quy tắc evidence, không review từng PDF.

Nguồn mới [Mekong30000](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/171704.mekong_timestamp_review.json)
khai báo11/06/2024 11:18:00+07:00; đúng đoạn ORS nêu record17/6/2024, ex-date14/6,
tỷ lệ100:12,36triệuCP kế hoạch. Năm ex-date lấy từ full record date trong cùng
đoạn, không suy giờ công bố. Hai bản tin calendar có timestamp nhưng không cóORS
đã bị loại. KTCK403 là Cloudflare access control: dừng route, classifier client
ban đầu false được manual review bổ sung; không sửa receipt cũ. Openstock lỗiTLS,
CUA không khởi động sau1reset nên không có quan sát trang Chrome; giữDEFERRED.

**Đề xuất Product/M3 pilot:**7field quyền2021 dùng timestamp bài TNCK270871;
6field cổ tức2024 dùng Mekong30000. Publisher tự khai báo publication/modified
time trong snapshot hiện tại, không có archive độc lập của nội dung lịch sử:
đây là tradeoff acceptance cần owner chấp thuận. Không claim giờ đăng đầu của
VSDC/HOSE, không mở strict research/canonical. DATE_ONLY corporate_actions vẫnoff.

[Admission review](../data/corporate_actions/work/ors_field_timestamp_contract_review_20261107_v1/field_admission_review.json)
giữ46row:11Stockbiz chỉ có cached-link binding,1record date2021 partial,
34chưa có field timestamp. Số13 là candidate theo proposal, khác số22source
support bước27; không phải13field đã được áp available_at.59row/packet cũ giữ.
5GET gồm3HTTP200/1HTTP403/1TLSerror;22timing tests,11negative guard checks và
compileall đạt.0available_at/usable_from_date/canonical,0Markdown mới; chưa
triển khai pipeline. Governance entry mới có snapshot bản trước khớp hash.

**Bước tiếp theo:** owner quyết định proposal chính xác này; nếu được duyệt mới
triển khai/test version availability overlay cho13mapping. Chưa tự activate,
sửa policy/manifest cũ, mở7/418 hoặc chạy canonical/research/backtest.

## Corporate action — ba packet có timestamp nguồn khai báo, 07/11/2026

Bước27 hoàn tất supplement offline cho3/3packet, giữ nguyên59row và hai selection
cũ. [Summary](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/summary.json)
và [ba observation](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/publication_timestamp_observations.json)
ghi rõ publisher/semantics, raw/receipt/hash và giới hạn tương ứng.

| Sự kiện | Timestamp do nguồn công khai khai báo | Binding |
| --- | --- | --- |
| Quyền mua2021 —142284 |02/06/2021 16:55:48+07:00 — Tin nhanh chứng khoán270871 | Nội dung bài khớp điều khoản; không có PDF notice gốc |
| Quyền mua2024 —166577 |16/01/2024 14:51:00+07:00 — Stockbiz22811809 | Tái dùng exact-PDF binding bước26, giữ giới hạn cached-link/liveDOM |
| Cổ tức2024 —171704 |11/06/2024 17:26:26+07:00 — Tin nhanh chứng khoán347098 | Chỉ đoạn ORS trong bài tổng hợp, không lấy dữ liệu mã liền kề |

Hai bài báo mới GET200: JSON-LD datePublished, meta article:published_time,
time.datetime và data-time Unix cùng instant; dateModified giữ riêng. Không
suy giờ/offset. Đây là giờ nguồn báo/Stockbiz đăng nội dung, không tự trở thành
giờ đăng gốc VSDC/HOSE, hoặc chứng nhận snapshot lịch sử của toàn field bundle.

[Support matrix](../data/corporate_actions/work/ors_timestamp_packet_supplement_20261107_v1/timestamp_field_support.json)
ghi22/59row có support từ nội dung hoặc PDF khớp;2row chỉ nêu ngày/tháng trong
fragment,35row chưa có support từ các nguồn timestamp này. Đây không phải22field
đã được gán available_at. Không truyền timestamp sang ex-date2021/cổ tức2024,
mã quyền hoặc followup/kết quả phát hành mà bài báo không nêu. Năm trong record
date fragment chỉ từ context chưa được âm thầm nâng thành full explicit date.

1039 input pin khớp;22timing tests và compileall đạt;2GET/2HTTP200,không retry
archive429 hoặc thu lại85/V7.0available_at/usable_from_date/canonical,0DATE_ONLY,
0Markdown mới; source acceptance/pipeline không đổi. Financial policy giữ nguyên.

**Bước tiếp theo đề xuất:** review contract availability theo từng field từ ba
observation và matrix, phân biệt support trực tiếp/PDF binding/context/thiếu;
ưu tiên ex-date2021/cổ tức2024 và followup thiếu timestamp riêng. Không tự áp
timestamp cho toàn event; acceptance mới nếu cần phải trình cụ thể theo AGENTS,
không giao owner đọc từng PDF. Chưa thực hiện stage tiếp hoặc mở canonical/7/418.

## Corporate action — bổ sung timestamp có offset cho ORS, 07/11/2026

Bước26 kết quả `PARTIAL_ONE_EXPLICIT_OFFSET_TIMESTAMP_DOCUMENT_MATCHED`.
[Summary](../data/corporate_actions/work/ors_timestamp_source_followup_20261107_v1/summary.json)
và [review Stockbiz](../data/corporate_actions/work/ors_timestamp_source_followup_20261107_v1/166577.stockbiz_timestamp_review.json)
ghi timestamp do nguồn khai báo cho article22811809: **2024-01-16T14:51:00+07:00**,
UTC tương ứng07:51:00. JSON-LD NewsArticle.datePublished và time.datetime cùng
giá trị; headline khớp đúng HOSE1614236/mã ORS. File đính kèm public được liên
kết trong bản render/cache của web tool có SHA-256 trùng PDF HOSE79 đã pin.

Giữ rõ giới hạn evidence: link file đến từ web-tool rendered/cache của cùng URL;
HTML/Chrome live hiện chỉ hiển thị nguồn HSX chung, không có link attachment.
Raw metadata, raw PDF và các observation khác cơ chế giữ riêng. Stockbiz khai
báo authorHSX/publisherStockbiz; chưa biến timestamp này thành lần công bố đầu
được chứng minh trực tiếp trên HOSE hoặc chứng nhận historical vintage.
Không tính copy PDF thành phiếu độc lập, không áp majority giữa created/posting.

RSS chính thức HOSE khai báo+07:00, nhưng dùng Atom:updated/category/build time
và không có ba bài ORS cần tìm; không dùng để suy timestamp lịch sử. Chênh7giờ
giữa postedDate API HOSE và timestamp Stockbiz được bảo toàn. DNSE có snippet
UTC cho bài cổ tức nhưng URL live redirect về homepage, chưa đủ binding nên
không chấp nhận. Clock lịch sử hai bài HOSE và timestamp gốc2021 vẫn thiếu.

8 GET gồm4HTTP200,1redirect307 và3HTTP429 từ đúng archive noticeTPS769. Hai lần
retry có backoff>=30giây và>=2phút; hết budget3attempt đánh DEFERRED, không suy
archive thiếu snapshot.13 query web và hai view tìm kiếm Stockbiz giới hạn không
chứng nhận mọi nguồn vắng bài.990 input pin khớp;22 timing tests/compileall đạt.
0available_at/usable_from_date/canonical,0DATE_ONLY,0Markdown mới; policy không đổi.

**Bước tiếp theo đề xuất:** ghép timestamp Stockbiz và binding vào packet166577
với provenance riêng; tìm bản tin có publication timestamp/offset cho171704 và
nguồn gốc2021 khi archive hết429. Không tự áp available_at/canonical hoặc mở7/418.

## Chỉ đạo hiện hành — chỉ tạm ngừng DATE_ONLY corporate_actions, 07/11/2026

**Bước25: owner đính chính chỉ tạm ngừng DATE_ONLY trong `corporate_actions`**,
gồm corporate action đưa sang Product/M3/research, đến khi owner yêu cầu dùng lại.
Financial và các phần khác tiếp tục theo policy DATE_ONLY đã duyệt trong phạm vi
và gate cũ. Phạm vi toàn DELTA ở bước24 đã được thay thế, không còn hiện hành.

AGENTS, [D-TIME-ONLY-02](DECISIONS.md) và
[config execution V2](../configs/data/publication_timestamp_only_execution_20261107_v2.json)
đã ghi đính chính. V1/evidence cũ bảo toàn; không thay pipeline hoặc thu lại batch.
Đây là chỉ đạo thực thi cho agent, chưa thêm hard guard mọi CLI legacy.
[Kết quả bước25](../data/corporate_actions/work/publication_date_only_scope_correction_20261107_v1/summary.json).

**Bước tiếp theo đề xuất:** trong corporate_actions, tìm bằng chứng clock HOSE
và timestamp bản tin gốc2021; thiếu thì giữ gap, không dùng DATE_ONLY fallback.
Stage này chỉ đính chính phạm vi, không thực hiện lookup mới hoặc mở stage tiếp.

## Lịch sử bước24 — phạm vi DATE_ONLY toàn DELTA đã được thu hẹp

**Bước24: owner tạm ngừng DATE_ONLY trên toàn project cho mọi xử lý mới**, gồm
financial, corporate actions, Product/M3 và research; không chỉ ORS. Chỉ dùng lại
khi owner yêu cầu. Đây là override các chấp nhận/fallback DATE_ONLY trước đây,
kể cả CafeF CreateDate và financial daily/monthly. AGENTS,
[D-TIME-ONLY-01](DECISIONS.md) và
[config thực thi version mới](../configs/data/publication_timestamp_only_execution_20261107_v1.json)
đã ghi rõ. Không tự tạo timestamp bằng00:00, timezone hoặc ngày phiên tiếp theo.
Record thiếu timestamp công bố/clock xác minh giữ evidence và DEFERRED;
không gán availability/usable_from_date bằng DATE_ONLY.

Đây là chỉ đạo agent execution/stage review; chưa thêm hard guard trên mọi CLI
legacy. Không chạy mới route DATE_ONLY khi override còn hiệu lực. Không sửa
policy version/raw/artifact đã freeze hoặc thu lại batch hoàn thành. Các ngày
kỳ báo cáo, record date, ex-date và vận hành giữ nguyên semantics riêng.

Lookup có giới hạn ở bước24: public JavaScript TPS trả GET200, currentNews của
post771 trong HTML cũ chỉ có display_date, không có publication timestamp;
metadata DOM của VSDC142284 không có publication meta/time/JSON-LD theo các
selector đã kiểm. Nhãn nhìn thấy vẫn là “Cập nhật”, không chuyển thành công bố.
Không tìm thêm timestamp đủ điều kiện; hai gap clock HOSE và nguồn gốc2021 còn.
[Kết quả bước24](../data/corporate_actions/work/ors_exact_timestamp_investigation_20261107_v1/summary.json)
giữ riêng với bước23. Global override không mở rộng crawl sang7/418 mã.
22 timing tests và compileall đạt;949 input pin được đánh giá:947 path giữ
nguyên,2 governance document được sửa có bản trước thay đổi khớp hash bảo toàn.

**Bước tiếp theo đề xuất:** tiếp tục tìm bằng chứng trực tiếp về quy ước clock
publication của HOSE và timestamp bản tin gốc2021. Tạm hoãn đề xuất tích hợp
extractor ở bước23; DATE_ONLY không còn là fallback trong thời gian override.

## Corporate action — xác minh timestamp HOSE/HNX, 07/11/2026

Bước23 hoàn tất review có giới hạn, kết quả `PARTIAL_ENCODING_VERIFIED_PUBLICATION_CLOCK_UNRESOLVED`.
[Summary](../data/corporate_actions/work/ors_publication_timestamp_verification_20261107_v1/summary.json)
và [review hai bài HOSE](../data/corporate_actions/work/ors_publication_timestamp_verification_20261107_v1/hose_timestamp_review.json)
giữ raw metadata, receipt/hash, liên kết đúng PDF cũ và từng loại thời gian.

| Sự kiện | Kết quả xác minh | Giới hạn còn lại |
| --- | --- | --- |
| Quyền mua2024 —166577 | API postedDate1705416660; UI giải mã thành16/01/2024 14:51:00 bằng Moment UTC | Chưa chứng minh clock backend phản ánh instant công bố thực |
| Cổ tức2024 —171704 | Raw JSON mới postedDate1718098260; UI/DOM cùng11/06/2024 09:31:00 | Chưa chứng minh clock backend phản ánh instant công bố thực |
| Quyền mua2021 —142284 | Ba truy vấn tin HNX giới hạn không trả record phù hợp | Chưa tìm được timestamp nguồn gốc; không suy vắng toàn lịch sử |

**Điểm mới:** ở cả hai bài HOSE, `createdDate` bản tin trừ `createdDate` file bằng
25.200 giây; `publishFrom` bản tin trừ `publishFrom` file cũng bằng25.200 giây.
Bộ định dạng đã pin dùng `utc(e,"X")`; tokenX và parser trong chính bundle xác
nhận Unix seconds, UTC khi hiển thị. Điều này xác minh cách giải mã, **chưa xác
minh clock lúc nhập dữ liệu**. Chênh7giờ giữa các loại metadata không chứng minh
clock nào đúng hoặc ngày nào là lần công bố đầu. Không tự gắn+07 cho giờ UI,
không lấy thời gian file thay postedDate hoặc chọn bằng đa số.

Hai raw JSON mới GET200; một GET HNX lỗi xác thực certificate và không hạ TLS.
Chrome thông thường đọc được; ba kết quả truy vấn lưu dưới dạng transcript AX
chuyển ghi có receipt/hash, không phải HTTPraw hay full AX export.0challenge.
923 input pin khớp;22 timing tests và compileall đạt. Không thay code/pipeline,
không chạy lại smoke đã hoàn thành; hai lỗi helper cache_audit bước20 vẫn riêng.
0 timestamp công bố thực được xác nhận đủ,0available_at/canonical,0Markdown mới.

**Bước tiếp theo đề xuất:** tích hợp trích timestamp tự động offline từ metadata
đã pin, giữ riêng raw value, encodedUTC, semantics và clock status. Chỉ gán
available_at khi nguồn/clock đủ evidence; các gap2021 và clock HOSE ở DEFERRED,
không chặn xử lý record khác. Chưa thực hiện stage này, không tự đổi acceptance
hoặc mở canonical, không thu lại85/V7 hay nhóm7/418 mã.

## Corporate action — owner chỉ định ưu tiên timestamp, 07/11/2026

Bước22 đã ghi chỉ đạo **timestamp công bố có evidence/múi giờ rõ → DATE_ONLY
theo rule đã được chấp nhận nếu thiếu timestamp → giữ gap nếu chưa đủ cả hai**.
[Kết quả](../data/corporate_actions/work/ors_timestamp_priority_review_20261107_v1/summary.json)
và [tám ứng viên thời gian](../data/corporate_actions/work/ors_timestamp_priority_review_20261107_v1/timestamp_review.json)
lưu version riêng. Đây là ưu tiên owner đã chỉ định,không xin duyệt lại; không
thay source acceptance hoặc biến ngày/modified time thành publication.

- HOSE quyền mua2024: ngày hiển thị16/01/2024 14:51:00 tái dựng từ postedDate/API
  và formatter; ưu tiên xác minh semantics timestamp/timezone,không tự gắnUTC/+07.
- HOSE cổ tức2024: “Đăng ngày11/06/2024 09:31:00” trong DOM; ưu tiên raw metadata
  và timezone của đúng article1703956.
- CafeF2021 có2021-06-08T11:22:19+07:00 nhưng là dateModified; ba VSDC là update.
  Các giá trị này không đủ cho timestamp công bố dù có giờ/offset.00:00 chỉ có
  thể dùng chính xác khi có evidence về precision/semantics,không mặc định thật
  hoặc giả. Trong8 ứng viên hiện rà,0 timestamp công bố đủ xác minh,0available_at
  được gán; không đồng nghĩa không có giờ hiển thị.

911 input pin khớp;22 timing tests và compileall đạt.0 network,0 canonical,
0 Markdown mới. Đề xuất policy ngày bản tin ở bước21 chưa kích hoạt và nhường
ưu tiên cho việc xác minh timestamp. **Bước tiếp theo đề xuất:** tìm/xác minh
timestamp theo [queue](../data/corporate_actions/work/ors_timestamp_priority_review_20261107_v1/timestamp_search_queue.json),
ưu tiên metadata/timezone HOSE và nguồn gốc2021; không chạy lại85/V7 hoặc7/418 mã.

## Corporate action — lookup CafeF cho ba sự kiện ORS, 07/11/2026

Bước21 kết quả `PARTIAL_NO_TARGET_EVENT_CREATEDATE`;
[summary cuối](../data/corporate_actions/work/ors_cafef_publication_lookup_20261107_v1/final_summary.json)
ghi0/3 record CreateDate khớp sự kiện,nhưng đã lấy đủ ba bản tin đúng event và
hai PDF2024 trùng SHA-256 bản HOSE đã pin.12 GET công khai (10HTTP200,2redirect301),
raw/receipt/hash đầy đủ,không challenge/đăng nhập hoặc thu lại batch85/V7.

**Đính chính hướng tìm bước20:** `ajaxcongbothongtin.ashx` trả102 record ORS qua
hai trang,tất cả có nội dung BCTC. CreateDate tồn tại thật nhưng thuộc tài liệu
tài chính,không được chuyển sang ba thông báo quyền. Trang public cũng khai báo
bảng Data.BctcList/CreateDate. Kết luận đầy đủ chỉ trong102record của snapshot
endpoint này,không claim mọi nguồn CafeF không có corporate action.

| Sự kiện | Bản tin CafeF đã khớp | Metadata thời gian |
| --- | --- | --- |
| Quyền mua2021 —142284 | Article1505338;8 điều khoản body khớp HNX/issuer | Ngày hiển thị08/06/2021 11:22;NewsArticle.dateModified cùng ngày |
| Quyền mua2024 —166577 | Article1931113;PDF trùng bản HOSE79 | Ngày hiển thị16/01/2024 00:00;NewsArticle.dateModified cùng ngày |
| Cổ tức2024 —171704 | Article2011515;PDF trùng thông báo HOSE | Ngày hiển thị11/06/2024 00:00;NewsArticle.dateModified cùng ngày |

Ba article không có CreateDate/datePublished trong raw; metadata WebPage.dateModified
là07/11/2026 của trang động,giữ riêng với NewsArticle. Không đổi tên nhãn ngày/
dateModified thành CreateDate,không coi00:00 là giờ công bố thực. Copy PDF không
thành phiếu độc lập.0 áp rule DATE_ONLY,0 available_at/usable_from_date,0 canonical.

834 pin cũ khớp;8 tình huống binding sai bị từ chối;35 targeted tests và compileall
đạt. Không đổi production code/config/pipeline nên không chạy lại synthetic smoke.
Hai lỗi test cache_audit migration bước20 giữ riêng,chưa sửa ở stage lookup này.
0 Markdown mới,chỉ cập nhật nhật ký và status hiện có.

**Bước tiếp theo đề xuất:** chuẩn bị policy riêng,phạm vi hẹp cho ngày hiển thị
bản tin CafeF DATE_ONLY Product/M3 dựa trên ba record đã review. Đây là đề xuất
acceptance mới,`MANUAL_REVIEW_REQUIRED` trước khi áp theo AGENTS; chưa thay policy
hoặc yêu cầu owner review từng bài/PDF. Không tiếp tục đợi CreateDate từ sai
endpoint,không tự chốt canonical/research hoặc mở7/418 mã.

## Corporate action — kiểm kê ngày công bố ba sự kiện ORS, 06/11/2026

Bước20 đạt `PASS_SCOPED_PUBLICATION_EVIDENCE_AUDIT` về evidence;
[kết quả cuối](../data/corporate_actions/work/ors_publication_evidence_audit_20261106_v1/final_summary.json)
ghi64 record nguồn (46 nguồn bundle+18 cache bổ sung),194 temporal observation,
59 trường và hai ứng viên ngày đăng.0 request,0 gán available_at/usable_from_date,
0 canonical,0 Markdown mới; không đổi code sản phẩm hoặc acceptance policy.

| Sự kiện | Evidence ngày đăng trong cache | Giới hạn |
| --- | --- | --- |
| Quyền mua2021 —142284 | Chưa có nhãn ngày đăng được xác nhận; VSDC cập nhật02/06/2021,issuer769 display_date02/06,issuer77103/06 | Update/display date không tự là publication |
| Quyền mua2024 —166577 | HOSE postedDate suy ra phần ngày hiển thị16/01/2024 từ API+formatter đã pin | Là derived từ cache,không là DOM mới/UTC instant đã xác minh |
| Cổ tức2024 —171704 | DOM HOSE ghi rõ Đăng ngày11/06/2024 09:31:00,có đúng filename đính kèm | Chưa xác minh timezone/first-publication vintage hoặc tự gán available_at |

Hai ứng viên chỉ gắn với đúng tài liệu:17/59 field có source dẫn tới ứng viên;
42 field còn lại chưa có ứng viên tương ứng trong scope cache. Không kế thừa ngày
thông báo quyền sang kết quả/phần dư/niêm yết. Giữ riêng postedDate,createdDate,
publishFrom,approvedDate,ngày ký,update,capture và ngày vận hành; không lấy min hay
đếm đa số giữa các semantics/tài liệu khác nhau. Rule CafeF CreateDate Product/M3
đã duyệt được giữ đúng scope,chưa áp cho HOSE/issuer. Index đã pin có20 record ở
nhóm ORS (2cổ phiếu đúngORS,18mã khác); không có CreateDate CafeF trong20record này,
không suy mọi cache/CafeF thiếu bài.

799 pin đầu vào khớp;8 kiểm tra dữ liệu giả sai bị từ chối.36 test ở entrypoint
gốc pass,compileall pass. Entry point di chuyển của `test_corporate_action_cache_audit`
có2 lỗi helper path (34/36 pass); byte nội dung hai bản test giống nhau,đường dẫn
ROOT sau di chuyển khác. Giữ log,không sửa ngoài stage audit và không claim mọi
test đã pass. Hai file đã sửa ở bước19 vẫn giữ pin,không phải lỗi tái phát ở đó.

**Bước tiếp theo đề xuất:** tìm có mục tiêu bản ghi Công bố thông tin CafeF/
CreateDate cho ba sự kiện,ưu tiên2021; xác minh đúng event/tài liệu,giữ raw/receipt/
hash và chỉ dùng rule DATE_ONLY Product/M3 đã duyệt khi đủ evidence. Chưa tự mở
stage thu thập này,canonical/research hoặc nhóm7/418 mã. Lỗi test migration ghi
riêng,không được che bằng việc dùng entrypoint gốc.

## Corporate action — đã sửa hai lỗi đường dẫn test legacy, 06/11/2026

Bước19 đạt `PASS_LEGACY_TEST_PATH_FIX`;
[kết quả cuối](../data/corporate_actions/work/ors_legacy_test_path_fix_20261106_v1/final_summary.json)
ghi94/94 targeted tests đạt,compileall đạt và synthetic smoke
`run-20261106T144527Z-71e8ee60` complete/synthetic=True.

Hai test file ở `tests/unit/ingestion/corporate_actions/legacy_sources/` vẫn dùng
`parents[3]` sau khi chuyển sâu thêm hai cấp, nên tìm helper dưới `tests/unit/scripts`.
Sửa thành `parents[5]` trong decision_packet và cached_review. Đã tái hiện cả
hai lỗi trước sửa; giữ nguyên toàn bộ test case/assertion,bao gồm chống ghi đè
và path escape. Không sửa helper/runtime sản phẩm,config,policy hoặc dữ liệu ORS.

Ngoại lệ `LEGACY_TEST_HELPER_PATH` của bundle bước18 đã được giải quyết bằng
record bổ sung; lỗi cached_review ghi từ bước8 cũng đã sửa. Giữ nguyên log FAIL
và manifest cũ.763 pin đầu vào khớp;0 request thu thập,0 canonical,0 Markdown mới.
Bundle ba sự kiện vẫn ready ở lớp review offline; các gate coverage,publication/
available_at,historical identity và canonical freeze chưa đổi.

**Bước tiếp theo đề xuất:** kiểm kê bằng chứng ngày công bố/available_at của ba
sự kiện ORS từ cache đã pin, ghi rõ có/thiếu. Không suy ngày ký/cập nhật/fetch là
publication,không tự chốt canonical hoặc mở nhóm7/418 mã. Chưa chạy stage này.

## Corporate action — bundle offline ba sự kiện ORS đã hợp nhất, 06/11/2026

Bước18 đạt `PASS_SCOPED_OFFLINE_BUNDLE`; [kết quả cuối](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/final_summary.json)
và [readiness từng sự kiện](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/readiness.json)
được lưu version mới. Giữ nguyên54 observation của packet bước12; bundle có
59 dòng trường,27 observation bổ sung và46 record nguồn/context. Catalog không
là46 phiếu độc lập: copy HOSE và hai transcript HNX cùng nguồn đã nhóm rõ.

- Ba packet142284,166577,171704 đều sẵn sàng đọc ở lớp review offline. Mỗi trường
  có nguồn/receipt/hash/locator hoặc review-ref đã pin; không tự đọc lại PDF hay
  chạy lại engine/crawl. Loại HTTP raw,renderedDOM,renderedAX và browser PDF chưa
  receiptHTTP được giữ riêng.
- Hai selection bước16 được tái sử dụng nguyên value/support/dissent và caveat;
  không tạo lựa chọn mới. Ngày HNX2021 đã có observation trực tiếp trong bundle.
  54 dòng cũ, gồm cả wording bất đồng và nhãn pending lịch sử, được giữ nguyên
  dưới `legacy_observation`; trạng thái hiện hành không yêu cầu owner đọc/chọn
  từng PDF. Không kích hoạt general automatic approval policy.
- Kế hoạch/kết quả,giá quyền/phần dư,nominal bổ sung/tổng và ex-date/ngày niêm yết
  được giữ khác field/scope.59 dòng không phải59 giá trị canonical đã phê duyệt.

**Readiness:**3/3 bundle observation hoàn tất; canonical/research vẫn PARTIAL.
[Danh sách ngoại lệ](../data/corporate_actions/work/ors_three_event_offline_bundle_20261106_v1/exceptions.json)
ghi riêng bốn gate chưa mở: toàn lịch sử revision,publication/available_at,
historical security_id và future canonical freeze. Các thiếu hụt hình thức
HNX raw/PDF,PDF4122 và anomaly nhãn vốn là nhóm riêng, không đẩy thành yêu cầu
owner review tài liệu. Nếu sau này thực hiện methodology/freeze thì áp dụng
`MANUAL_REVIEW_REQUIRED` theo AGENTS; stage này không thực hiện hoặc xin duyệt đó.

732 pin evidence cũ khớp; dependencyAGENTS được pin thêm riêng.43 targeted tests
và compileall đạt; bảy kiểm tra dữ liệu giả sai (hash,locator,AX label,support,
planned/actual,đơn vị quyền,canonical flag) bị từ chối đúng. Lỗi test helper legacy
từ bước17 còn nguyên, không thuộc43 test đã chạy lần này.0 request,0 canonical,
0 factor,0 Markdown mới; chỉ cập nhật hai tài liệu hiện có.

**Bước tiếp theo đề xuất:** sửa riêng lỗi đường dẫn helper trong test legacy,
chạy lại targeted tests và compileall để loại ngoại lệ kỹ thuật đã biết. Chưa
tự chạy stage sửa test, canonical hoặc nhóm7/418 mã.

## Corporate action — bổ sung xác nhận HNX và review gap ORS, 06/11/2026

Bước17 đạt `PASS_SCOPED_GAP_REVIEW`: đóng5/6 nhóm gap đầu vào; nhóm còn lại
là PDF kết quả UBCKNN4122/2021 tùy chọn, đã có body kết quả doanh nghiệp869.
[Summary](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/summary.json)
và [đối chiếu gap](../data/corporate_actions/work/ors_remaining_gap_review_20261106_v1/gap_queue_review.json)
được lưu version mới; không sửa inventory85 bài hay hai lựa chọn nguồn thứ ba.

**Đã đọc trực tiếp HNX qua Chrome:** UPCoM → Lịch thực hiện quyền, lọc ORS từ
01/05–30/06/2021 trả đúng một dòng; mở chi tiết thấy ex-date10/06/2021,
record11/06/2021,1:1,10.000 đồng/CP và lịch chuyển nhượng/đặt mua khớp nguồn cũ.
Lưu hai transcript text từ accessibility output, có receipt/hash, ghi rõ
`RENDERED_ACCESSIBILITY_TEXT_TRANSCRIPT`, không phải HTTP raw/PDF ký hoặc bằng
chứng thời điểm công bố lịch sử. Gap xác nhận ngày từ Sở đã được bổ sung ở mức
rendered; chưa lưu HTTP raw hoặc PDF gốc của thông báo HNX này.

Thu21 GET200 có raw/receipt/hash:13 bài doanh nghiệp và8 PDF; đọc trực quan đủ
26 trang PDF. Ba nghị quyết còn treo NQ01/2024,NQ10/2024,NQ11/2024 đã review;
lịch quyền mua và100:12/record17/06 khớp.13 bài hỗ trợ đã triage từ body public
SSR JSON, không gán DOM. Giấy phép/phát hành/niêm yết được tách khỏi thay đổi
quyền; kế hoạch quyền mua210,3 triệu CP trong AGM24/04/2024 là đợt tương lai
riêng, không ép thành revision đợt100 triệu CP tháng1. Trong tài liệu vừa review
chưa thấy hủy/đổi lịch ba sự kiện; không chứng nhận toàn lịch sử không có revision.

**Còn giới hạn:** PDF4122 chưa tìm được; chưa review mọi PDF hành chính, phụ lục,
bản cáo bạch. HTML2042/2153 có nhãn đơn vị vốn đáng ngờ, giữ nguyên và chưa chọn
giá trị canonical. Không phát sinh conflict cùng field cần chạy lại rule nguồn
thứ ba. ORS vẫn đủ85/85 toàn văn trong snapshot; readiness toàn event còn PARTIAL
do coverage/PIT/identity/available_at/freeze chưa mở, không chờ owner đọc từng PDF.

575 input pin khớp;78 test đã chạy có77 đạt,1 lỗi legacy
`test_runner_path_safety_and_no_overwrite` do tìm helper dưới `tests/unit/scripts`;
không sửa test/code ngoài stage. Compileall đạt. Không thay production pipeline
nên không chạy lại synthetic smoke; smoke cuối bước16 giữ pin.0 Markdown mới,
chỉ cập nhật nhật ký và trạng thái hiện có;0 canonical/price factor.

**Bước tiếp theo đề xuất:** hợp nhất observation/locator bổ sung và hai field đã
chọn thành bundle đối chiếu offline mới cho ba sự kiện, xuất readiness và danh
sách ngoại lệ rõ ràng. Dùng cache đã có; chưa cần thu lại85 bài hoặc tiếp tục tìm
PDF hành chính. Không tự chạy bước này, canonical hoặc nhóm7/418 mã.

## Corporate action — workflow đối chiếu ba nguồn offline ORS đã chạy, 06/11/2026

Bước16 đạt `PASS_OFFLINE_THIRD_SOURCE_WORKFLOW`: triển khai module
`src/delta_t1/ingestion/corporate_actions/third_source_reconcile.py`, CLI
`scripts/corporate_actions/reconcile_third_source_v1.py` và
[config ORS riêng](../configs/data/corporate_actions/third_source_reconcile_ors_v1.json).
[Kết quả tích hợp](../data/corporate_actions/work/ors_third_source_reconcile_20261106_v1/KET_QUA_TICH_HOP.md)
ghi bản chạy cuối `run_output_release`: tự tính lại **chọn2/2 case, unresolved0,
network0, canonical0**, khớp hai selection receipt bước15 về value/support/dissent.

| Field | Hai nguồn ghi khác nhau | Nguồn thứ ba | Lựa chọn tự tính lại |
| --- | --- | --- | --- |
| Đơn vị quyền2024 | NQ11/2023 doanh nghiệp vs VSDC166577 | HOSE79 ngày15/01/2024 khớp VSDC | Một CP cũ nhận một quyền; hai quyền mua một CP mới |
| Nominal phần bổ sung2021 | HTML doanh nghiệp924 vs PDF HNX430 | VSDC143656/GCN152-5 khớp HNX | 1.000.000.000.000 VND phần bổ sung;2.000 tỷ là tổng |

Workflow kiểm authorization rule, pin/raw/receipt/locator, đúng field/scope/đơn vị/
hiệu lực, source origin đã review và known counter-evidence. Copy/shared origin,
thiếu nguồn, ba giá trị khác nhau, hash/receipt sai hoặc revision chưa đủ đều giữ
unresolved, đưa queue `owner_action_required=false`; case độc lập vẫn tiếp tục.
Giữ dissent/observation, refuse overwrite và ghi input replay/output manifest.
Không đọc `selected_value` cũ để làm quyết định.

**Giới hạn:** mới tự động so sánh observation đã trích xuất và review provenance;
chưa tự tìm nguồn trên mạng, đọc hiểu PDF hoặc đánh giá origin từ raw. Config giữ
`automatic_field_approval=false`, `canonical_build=false`; chỉ chọn field lớp review,
không mở PIT/identity/available_at/revision coverage hoặc final freeze.

78 targeted tests đạt (29 mới,49 legacy core), compileall đạt; synthetic smoke
bản cuối `run-20261106T135235Z-4204f521` complete/synthetic=True.530 pin cũ khớp,
không sửa runtime/config/evidence đã freeze hoặc thu lại85 bài/1.072 query.

**Bước tiếp theo đề xuất:** kết nối unresolved queue với bước tạo observation và
tìm/review nguồn thứ ba trong stage ORS được giao. Không tự chạy acquisition mới,
canonical hoặc nhóm7/418 mã; gap HNX ex-date2021 và các gate research vẫn riêng.

## Corporate action — ORS chọn được hai field theo nguồn thứ ba, 06/11/2026

Bước 15 đạt `PASS_2_OF_2_FIELD_SELECTIONS` theo CA-THIRD-SOURCE-V1 owner đã chỉ
định; [kết quả đối chiếu](../data/corporate_actions/work/ors_third_source_resolution_20261106_v1/KET_QUA_DOI_CHIEU.md)
và hai selection receipt được lưu version mới, giữ nguyên nguồn bất đồng.

- **Đơn vị quyền2024:** chọn một CP cũ nhận một quyền, hai quyền mua một CP mới.
  VSDC166577 và PDF HOSE79 ngày15/01/2024 trang1–2 khớp nhau. NQ11/2023 ghi đơn vị
  khác được giữ làm dissent. HOSE79 là văn bản Sở riêng, không tính copy Vietstock
  thành nguồn mới; kiểm độc lập ở mức văn bản/provenance, không claim audit độc lập
  dữ kiện nền. Chưa tìm thấy formal correction NQ11, không sửa lịch sử nghị quyết.
- **Giá trị danh nghĩa bổ sung2021:** chọn **1.000.000.000.000 VND** cho100 triệu
  CP bổ sung. Nguồn thứ ba VSDC143656/GCN152-5 ngày02/08/2021 nêu trực tiếp, khớp
  PDF HNX430 trang2; tổng sau bổ sung là200 triệu CP/2.000 tỷ. HTML post924 ghi
  2.000 tỷ phần bổ sung vẫn giữ làm dissent; không chọn bằng phép nhân mệnh giá.

Thu bốn HTTP request trực tiếp (ba GET200, một POST tìm kiếm400/body rỗng), dùng
Chrome thường đọc issuer-news pages2–3 và143656, lưu riêng ba text DOM/receipt/hash.
143656 ở ngoài snapshot thực hiện quyền85 ID; giữ inventoryV3 immutable, không
đổi85 thành full historical coverage. Có raw và DOM143656 khớp text sau chuẩn hóa
khoảng trắng, vẫn giữ đúng hai loại evidence. Hạch toán VSDC144117 chỉ dùng liên
kết HNX2716, không tính thêm phiếu độc lập. Không gặp challenge/access control.

Đính chính extraction cũ: post869 có body trong public embedded SSR JSON của raw
đã pin; đã trích riêng, không gán DOM/PDF mới. Tiền thu1.000.877.282.000 đồng trong
đó khác giá trị danh nghĩa, không đem so cùng field. Chưa lấy được PDF công văn.

Hai field được chọn ở review overlay, 0 canonical/price factor. 14 test revision,
compileall và kiểm integrity/locator/selection receipt đạt. Toàn event vẫn PARTIAL:
HNX ex-date2021, global revision coverage và PIT/identity/available_at/freeze chưa
được mở. **Bước tiếp theo đề xuất:** tích hợp rule và selection receipt vào workflow
đối chiếu offline version mới có tests, giữ các gate này tắt. Không tự mở stage
engine/canonical hoặc nhóm7/418 mã.

## Corporate action — owner chỉ định quy tắc nguồn thứ ba, 06/11/2026

Bước 14 ghi [CA-THIRD-SOURCE-V1](../data/corporate_actions/work/ors_third_source_rule_20261106_v1/QUY_TAC_NGUON_THU_BA.md):
hai nguồn cùng field cho giá trị khác nhau thì tìm nguồn thứ ba; nếu khớp một
bên, chọn giá trị được hai nguồn xác nhận, giữ cả nguồn bất đồng. **Quy tắc này
đã được owner chỉ định, không yêu cầu duyệt lại.** Tạo delegation policy V2 riêng,
không sửa V1, packet cũ hoặc hash evidence.

Đối chiếu đúng security/event/field/đơn vị/phạm vi/hiệu lực; nguồn thứ ba có gốc
tài liệu riêng, không tính bản copy đăng lại thành phiếu mới. Kiểm revision trước
khi đếm xác nhận. Nguồn thứ ba thiếu/không đủ điều kiện hoặc khác cả hai thì
giữ unresolved; không bỏ nguồn bất đồng, lấy trung bình hoặc tìm chọn lọc để ép
đồng thuận. Selection receipt phải giữ ba nguồn, value, cặp xác nhận, nguồn bất
đồng, locator/hash/receipt, nguồn gốc, thứ tự tìm và scope review.

Stage đạt `PASS_RULE_RECORDING`, 0 request và 0 lựa chọn field ORS mới. Pipeline
deterministic/canonical chưa bật; các phần ủy quyền khác không tự được coi là
approved bởi chỉ đạo riêng này. Tám tình huống kỳ vọng là đặc tả, không phải kết
quả chạy engine. Input hash, liên kết và guards kiểm đạt; 14 test revision và
compileall đạt. V3 vẫn đủ toàn văn 85/85 bài, hai conflict chưa được giải quyết.

**Bước tiếp theo đề xuất:** tìm/đối chiếu nguồn thứ ba cho giá trị danh nghĩa bổ
sung 2021 và đơn vị quyền 2024 trong stage ORS được giao. Đủ chứng cứ thì chọn
theo quy tắc đã chỉ định; chưa đủ thì giữ unresolved, không giao owner đọc PDF
hoặc xin lại approval cho chính quy tắc này. Không tự mở nhóm 7/418 mã/canonical.

## Corporate action — đề xuất ủy quyền agent tự review, 06/11/2026

Bước 13 đã lập [quy tắc CA-REVIEW-DELEGATION-V1](../data/corporate_actions/work/ors_review_delegation_proposal_20261106_v1/QUY_TAC_UY_QUYEN_REVIEW.md),
gồm 12 quy tắc, 12 tình huống kỳ vọng và mapping D01–D06 của packet cũ.
**Đây là đề xuất chờ duyệt một lần, chưa kích hoạt**; config đề xuất nằm riêng trong
artifact, không đưa vào runtime. Đọc quy tắc và nguyên gói ủy quyền thay vì yêu cầu
owner chọn 54 field hoặc sáu mục D01–D06.

Agent nhận trách nhiệm kiểm chứng kỹ thuật, phân loại nguồn/field/lineage và tự
giữ `UNRESOLVED`/`DEFERRED` khi chưa đủ chứng cứ. Exception mặc định không tạo việc
owner phải đọc PDF/chọn nguồn. Một nguồn chính thức nêu rõ field có thể đủ cho
technical review; cho phép ngày từ doanh nghiệp với provenance doanh nghiệp là
acceptance mới được đề xuất, chưa áp dụng cho ORS 2021. Mâu thuẫn cùng field vẫn
giữ mọi observation, không tự ưu tiên PDF/nguồn Sở hoặc lấy trung bình.

Đính chính cách bàn giao bước 12: D01–D06 là các điểm review đã ghi nhận, không
phải sáu việc owner bắt buộc tự thẩm định. AGENTS yêu cầu approval khi cần đổi
methodology/freeze; không yêu cầu owner đọc từng bài. Config hiện vẫn tắt automatic
field approval/canonical. Phê duyệt quy tắc không tương đương freeze canonical,
chọn price basis, gán available_at hoặc mở PIT/identity/research gates.

Stage chuẩn bị đề xuất đạt `PASS_PROPOSAL_PREPARATION`; policy giữ
`PROPOSED_MANUAL_REVIEW_REQUIRED`, `active=false`. Không có request nguồn,
không sửa production code, config đang chạy, quyết định packet cũ hoặc inventory.
Kiểm tra input hash, cấu trúc quy tắc/ủy quyền, link, 14 test revision và compileall
đạt. Các design case là đặc tả hành vi kỳ vọng, không phải test engine đã chạy.

**Bước tiếp theo đề xuất:** owner chấp thuận nguyên gói CA-REVIEW-DELEGATION-V1;
sau đó giao một stage áp dụng bằng agent cho 54 field ORS và báo đạt/unresolved.
Không cần owner trả lời D01–D06. Pipeline deterministic tự review chưa được triển
khai; stage triển khai sau phải có config/version/tests và smoke khi thay pipeline.
Không tự mở nhóm 7/418 mã, chạy stage kế tiếp hoặc freeze canonical.

## Corporate action — packet quyết định offline ba sự kiện ORS, 06/11/2026

Bước 12 đã chuẩn bị [packet để owner review](../data/corporate_actions/work/ors_three_event_decision_packet_20261106_v1/ORS_DECISION_PACKET.md)
tại `data/corporate_actions/work/ors_three_event_decision_packet_20261106_v1/`.
Packet có **54 dòng field, 22 tham chiếu nguồn và sáu quyết định D01–D06**;
artifact máy đọc giữ riêng observation, nguồn, vị trí review, đề xuất và quyết định
owner. `owner_decision`, `selected_option`, `approved_value` đều chưa được điền;
không coi yêu cầu lập packet là phê duyệt các lựa chọn.

Sáu quyết định gồm bộ điều khoản/phạm vi số lượng và giá; ex-date 2021 từ nguồn
doanh nghiệp; khác biệt đơn vị quyền 2024; giá trị danh nghĩa bổ sung 2021 khác
giữa HTML/PDF; giới hạn revision coverage; mức liên kết kết quả/hậu kiểm.
Mỗi quyết định có phương án, đề xuất và lý do cụ thể, chưa thực thi. Tỷ lệ CP
cũ:mới, đơn vị quyền, số kế hoạch/kết quả và giá quyền gốc/phần dư được giữ riêng.

Stage packet đạt `PASS_PACKET_PREPARATION`; readiness sự kiện vẫn
`PARTIAL_MANUAL_REVIEW_REQUIRED`. Gửi **0 request nguồn**, pin và kiểm lại 441 input;
inventory V3 vẫn đủ 85/85 bài, 0 bài thiếu toàn văn. Kiểm tra field/source/JSON
pointer và link trong packet đạt; 14 test revision và compileall đạt. Không đổi
runtime, policy, source priority, canonical, available_at hoặc gate PIT/identity.

**Bước tiếp theo đề xuất:** owner review D01–D06 ngay trong packet. Khi được giao
stage ghi nhận, chỉ ghi các lựa chọn rõ ràng vào version mới và giữ các mục chưa
quyết định ở trạng thái unresolved. Theo AGENTS, lựa chọn nguồn/trường hoặc final
freeze cần `MANUAL_REVIEW_REQUIRED`; config offline giữ automatic approval và
canonical build tắt. Chưa mở stage thu thập mới, canonical hay nhóm 7/418 mã.

## Corporate action — bổ sung nguồn Sở và lineage ba sự kiện ORS, 06/11/2026

Đã hoàn tất review có giới hạn tại
`data/corporate_actions/work/ors_three_event_lineage_supplement_20261106_v1/`;
readiness giữ `PARTIAL_HNX_EXDATE_AND_UNCERTIFIED_GLOBAL_REVISION_COVERAGE`.
Snapshot ORS vẫn đủ **85/85 bài toàn văn, 0 bài thiếu**; không thu lại inventory.

- Tải PDF gốc HOSE 79/TB-SGDHCM ngày 15/01/2024 qua chuỗi API/tệp đính kèm công
  khai. SHA-256 khớp hoàn toàn copy Vietstock đã review ở bước 10; khép gap host
  gốc cho ex-date quyền mua 18/01/2024, không thay hash hay sửa bản cũ.
- UBCKNN 1914 ngày 29/03/2024 ghi đã phân phối 100.000.000 cổ phiếu của giấy phép
  442; UBCKNN 3994 ngày 27/06/2024 ghi phân phối cổ tức 35.999.743 cổ phiếu.
  Đây là số lượng kết quả, giữ riêng số lượng kế hoạch và điều khoản quyền gốc.
- NQ05 ngày 21/03/2024 ghi 94.919.294 cổ phiếu đăng ký/nộp tiền, 5.080.706 cổ
  phiếu dư. NQ11 ngày 22/07/2021 ghi 99.122.718 cổ phiếu bán cho cổ đông và
  877.282 cổ phiếu dư. Cả hai đợt phân phối lại phần dư ở giá **11.000 đồng/CP**;
  không thay giá quyền mua ban đầu **10.000 đồng/CP** hoặc tự coi hạn nộp tiền
  cho phần dư là gia hạn kỳ đăng ký ban đầu.
- PDF HNX 430/2651/2716 trên host doanh nghiệp xác nhận thêm 100 triệu cổ phiếu
  năm 2021; 99.122.718 cổ phiếu giao dịch từ 27/08/2021, 877.282 cổ phiếu hạn chế
  từ 01/08/2022. Đây không phải ex-date. Direct GET host HNX lỗi TLS; không tắt
  kiểm chứng chứng chỉ. Thông báo HNX xác nhận ex-date 10/06/2021 vẫn thiếu;
  chứng cứ ngày này tiếp tục là HTML doanh nghiệp postId 769 đã lưu.
- NQ17/2023 bổ sung NQ11/2023 về sử dụng vốn/ủy quyền, thay rõ Điều 4. Đính chính
  postId 1849 thuộc trái phiếu **ORSH2328001**, loại khỏi ba sự kiện cổ phiếu.
  Hoãn phát hành postId 1225 thuộc phương án 2022 lên vốn 4.000 tỷ, không gắn vào
  đợt 2021 lên 2.000 tỷ.

Đã lưu 69 receipt request (65 GET200, hai lỗi transport, một 301, một 404), thêm
một body chưa có receipt do lỗi encoding cục bộ và GET lại bằng key mới; tổng
70 lần GET được ghi rõ trong accounting. Giữ body chưa receipt đúng loại, không
gán HTTP200. 14 PDF có receipt; đọc hình ảnh 27 trang của 13 PDF mới, tái dùng
review hai trang PDF HOSE do byte khớp. Không kiểm chứng chữ ký số bằng mật mã.

Review tiêu đề 110 ID trên hai khoảng trang liên tiếp; các snapshot bộ lọc quyền
mua/cổ tức/phát hành đủ tương ứng 21/4/59 ID. Không phải review toàn bộ nội dung
413 bài doanh nghiệp. Chưa chứng nhận không còn revision trong PDF/nguồn/khoảng
thời gian khác. Giữ hai discrepancy: HTML doanh nghiệp về giá trị đăng ký bổ sung
2021 khác PDF HNX; cách diễn đạt đơn vị quyền ở NQ11/2023 khác VSDC sau đó dù tỷ
lệ kinh tế cổ phiếu cũ:mới cùng 2:1. Không tự ưu tiên nguồn hay chuẩn hóa khác biệt.

Evidence/input cũ giữ nguyên; 14 test revision và compileall đạt. Không sửa
runtime/pipeline, policy, canonical, PIT/identity hoặc tính hệ số điều chỉnh.

**Bước tiếp theo đề xuất:** lập packet quyết định offline cho ba sự kiện, gồm bảng
từng field/nguồn, các discrepancy và lựa chọn giữ unresolved phần HNX/revision.
Owner review trước lựa chọn field/source hoặc freeze canonical
(`MANUAL_REVIEW_REQUIRED` theo AGENTS và config đang tắt automatic approval).
Không tự chạy stage kế tiếp hoặc mở nhóm 7 mã lớn/418 mã.

## Corporate action — review ba candidate ORS và ex-date, 06/11/2026

Đã hoàn tất phần review được giao, tạo ba hồ sơ sự kiện tại
`data/corporate_actions/work/ors_three_event_review_20261106_v1/`.
Điều khoản và ex-date quan sát được đạt `PASS_3_OF_3`; mức sẵn sàng event tổng thể
giữ `PARTIAL_EVENT_READINESS_REVISION_ARCHIVE_NOT_CERTIFIED`.

| Bài VSDC | Sự kiện | Ngày đăng ký cuối cùng | Ex-date đọc trực tiếp | Nguồn bổ sung |
| --- | --- | --- | --- | --- |
| 171704 | Cổ tức cổ phiếu 100:12 | 17/06/2024 | 14/06/2024 | PDF HOSE ngày 10/06/2024, tải trực tiếp từ host HOSE |
| 166577 | Quyền mua 2:1, giá 10.000 đồng/CP | 19/01/2024 | 18/01/2024 | Bản thông báo HOSE 79/TB-SGDHCM ngày 15/01/2024 trên Vietstock |
| 142284 | Quyền mua 1:1, giá 10.000 đồng/CP | 11/06/2021 | 10/06/2021 | Nội dung công bố doanh nghiệp, postId 769; PDF VSDC 950 đối chiếu điều khoản |

Đã xem đủ bảy trang của ba PDF. PDF 2021 không nêu ex-date; ngày 10/06/2021 được
nêu trong HTML doanh nghiệp, không suy từ ngày đăng ký cuối cùng. Bản HOSE 79 tải
từ Vietstock có chữ ký/dấu nhìn thấy, chưa đối chiếu byte với host HOSE và chưa
kiểm chữ ký số. Các trường được ghi để review, không tự chọn thành canonical.

Review cache 31 bài cổ phiếu của snapshot 85 ID: không tìm thấy revision gắn trực
tiếp với ba candidate trong phạm vi đó; ba thông báo hủy thuộc quyền họp/lấy ý kiến.
Từ `điều chỉnh` trong boilerplate đối chiếu TVLK không tự tạo revision. Search công
khai và bộ lọc doanh nghiệp chưa tạo được archive revision hoàn chỉnh, nên không
chứng nhận không có sửa/hủy/gia hạn khác. Bổ sung HTTP raw của hai thông báo VSDC
`170753`, `173807`, liên kết rõ ngày đăng ký cuối cùng tương ứng 19/01/2024 và
17/06/2024, nêu ngày giao dịch cổ phiếu phát hành thêm 13/05/2024 và 12/08/2024.
Hai ngày này không phải ex-date và không tự chứng nhận hoàn tất mọi khâu phát hành.

Evidence gồm ba text cũ dùng lại, bốn HTTP raw GET200 mới, hai text DOM và một PDF
tải qua Chrome không có HTTP receipt. Giữ raw/receipt/hash đúng loại; inventory V3
và 85 ID cũ không thay đổi. Không đổi runtime/policy, không tính hệ số điều chỉnh,
không mở gate PIT/historical identity. Bộ 14 test revision và compileall đạt.

**Bước tiếp theo đề xuất:** owner review ba hồ sơ cụ thể để quyết định nguồn/trường
và yêu cầu evidence lineage còn thiếu; ưu tiên bản gốc HOSE 79 và thông báo HNX
2021 nếu cần đối chiếu nguồn Sở. `automatic_field_approval=false` và
`canonical_build=false` trong config offline reconciliation tiếp tục có hiệu lực.
Giữ `MANUAL_REVIEW_REQUIRED` cho lựa chọn field/source và freeze canonical; chưa
tự triển khai canonical hoặc mở stage nhóm 7 mã lớn/418 mã.

## Corporate action — ORS đủ toàn văn 85/85 bài trong snapshot, 06/11/2026

Stage đạt `PASS_ORS_REMAINING_41_FULLTEXT`: thu một lượt qua Chrome toàn bộ 36 bài
trái phiếu còn thiếu và bổ sung toàn văn năm bài cổ phiếu chỉ có fields review.
Lưu 41 text vùng bài hiển thị, 41 receipt thu nhận DOM và SHA-256 tại
`data/corporate_actions/work/vsdc_ors_remaining_fulltext_20261106_v1/`.
Không gặp challenge/access control, không có bài deferred. Đây là rendered DOM,
không gán HTTP status hoặc coi capture mới là HTTP raw.

Inventory V3 ở `data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v3/`
ghi nhận **85/85 bài có toàn văn, 0 bài thiếu nội dung, 0 bài chỉ có fields**:
20 HTTP raw có hash/receipt và 65 rendered text có hash/receipt thu nhận DOM.
Trong snapshot có 31 bài cổ phiếu đúng mã ORS và 54 bài trái phiếu có mã đầy đủ
khác ORS; phân biệt bằng trường mã và loại chứng khoán trong từng bài.

36 bài mới gồm 35 thông báo trả lãi và một thông báo lấy ý kiến trái chủ
(`186160`, mã `ORS12101`). Năm bài cổ phiếu xác nhận lại bốn họp thường niên,
một họp bất thường; ngày đăng ký cuối cùng, ISIN, sàn, ngày cập nhật và lịch họp
dự kiến khớp fields cũ. Giữ khác biệt nhãn Tiên Phong/Phương Đông ở `9509`, `5416`.
Không có candidate điều chỉnh giá cổ phiếu mới từ 41 bài này; ba candidate trong
stage trước và trạng thái revision/canonical giữ nguyên.

Self-review đối chiếu chính xác 41 ID cần bổ sung, 82 tệp capture mới, toàn bộ
85 tham chiếu evidence và manifest/input đã pin. Các version cũ giữ nguyên.
Không sửa runtime, policy, hash cũ hoặc áp dụng canonical; không chạy lại batch
đã hoàn thành. Phạm vi đủ toàn văn chỉ áp dụng cho snapshot tìm kiếm 85 ID đã
quan sát; 65 bài vẫn chưa có HTTP raw và chưa audit file đính kèm ngoài nội dung
inline. Chưa chứng nhận full historical event coverage.

Phần thu toàn văn ORS trong snapshot đã xong. Bước tiếp theo đề xuất là
review/reconcile ex-date và revision của ba candidate cổ phiếu trước khi xét
canonical. Nhóm 7 mã lớn và 418 mã của chiến dịch chưa thực hiện trong stage này.

### Stage tiếp theo đề xuất — review ba sự kiện điều chỉnh giá ORS

Mục tiêu là lập hồ sơ sự kiện có thể kiểm tra cho `171704` (cổ tức cổ phiếu),
`166577` và `142284` (quyền mua). Đọc lại evidence đã lưu và tìm trong cache các
thông báo sửa/hủy/gia hạn liên quan; chỉ bổ sung nguồn công khai cho trường còn
thiếu. Không thu lại 85 bài đã có toàn văn.

1. Đối chiếu ngày đăng ký cuối cùng, tỷ lệ cổ phiếu/quyền mua, giá phát hành và
   lịch chuyển nhượng/đăng ký mua với text từng bài; tách ngày cập nhật nguồn.
2. Xác minh ngày giao dịch không hưởng quyền (ex-date) bằng thông báo của Sở hoặc
   nguồn có thẩm quyền theo contract hiện hành; không tự suy từ ngày đăng ký cuối cùng.
3. Kiểm tra revision, hủy hoặc gia hạn của từng sự kiện; phân biệt với ba thông
   báo hủy quyền họp/lấy ý kiến đã review. Thiếu liên kết thì giữ unresolved.
4. Tạo bảng review có source/evidence/hash cho từng trường và kết luận mức sẵn
   sàng của từng sự kiện. Chưa tự áp dụng canonical hoặc hệ số điều chỉnh giá.

Đầu ra mong đợi là ba hồ sơ sự kiện, danh sách trường còn thiếu và kết luận
`PASS`/`PARTIAL` theo evidence. Nếu cần đổi methodology hoặc freeze canonical,
ghi `MANUAL_REVIEW_REQUIRED` và dừng để owner review. Đây là đề xuất; chưa execute.
Sau stage này mới đề xuất riêng phần rà soát nhóm 7 mã lớn/418 mã của chiến dịch.

## Corporate action — bổ sung/review đủ 24 bài cổ phiếu ORS, 06/11/2026

Stage đạt `PASS_ORS_24_MISSING_EQUITY_CONTENT_REVIEW` trên nhánh
`feature/indicators-v1`. Đọc đủ 24/24 ID cổ phiếu trong queue đã pin qua Chrome,
lưu toàn text vùng bài hiển thị, receipt thu nhận DOM và SHA-256 vào
`data/corporate_actions/work/vsdc_ors_equity_detail_review_20261106_v1/`.
Đây là rendered DOM, không phải HTTP raw; không gán HTTP200 cho capture mới.
Không chạy lại batch V7, đổi hash/policy, chuyển nhánh hoặc áp dụng canonical.

Ba bài ưu tiên xác nhận từ nội dung:

| ID | Nội dung | Ngày đăng ký cuối cùng | Điều khoản đọc được |
| --- | --- | --- | --- |
| 171704 | Cổ tức bằng cổ phiếu | 17/06/2024 | 100 cổ phiếu nhận 12 cổ phiếu mới |
| 166577 | Quyền mua | 19/01/2024 | 2 quyền mua 1 cổ phiếu mới; 10.000 đồng/cổ phiếu |
| 142284 | Quyền mua | 11/06/2021 | 1 quyền mua 1 cổ phiếu mới; 10.000 đồng/cổ phiếu |

Ba thông báo hủy `182168`, `68163`, `50840` lần lượt khớp nội dung/ngày đăng ký
cuối cùng của `179241`, `64007`, `50492`; đều là quyền họp/lấy ý kiến, không phải
hủy ba sự kiện giá trên. Thông báo hủy có số/ngày văn bản gốc; mapping ID bài theo
mã, loại quyền và ngày trong snapshot, không có hyperlink ID gốc. Các bài sau
`182169`, `68162`, `51446` chỉ là possible successor, chưa xác nhận supersedes.
Ngày cập nhật bài và ngày văn bản được dẫn chiếu có thể khác nhau.

Tái dùng hai bài raw và năm review fields, tổng 31 bài cổ phiếu có review: ba
price-action candidate, ba cancellation và 25 thông báo không điều chỉnh giá.
Đọc offline 18 raw trái phiếu: mã chi tiết đều khác chính xác `ORS`, loại chứng
khoán là trái phiếu; 36 bài trái phiếu còn lại vẫn chỉ được phân loại theo tiêu đề.
Inventory mới ở `data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v2/`,
gồm 20 HTTP raw + 24 rendered text + 5 fields-only + 36 thiếu detail; version cũ
giữ nguyên và đối chiếu manifest đạt. Review fields của năm bài trang cuối vẫn
chưa có full text; 24 bài mới vẫn chưa có HTTP raw. Không audit file đính kèm
ngoài nội dung inline, không suy ex-date, hệ số điều chỉnh hay full history.

Self-review kiểm tra đủ ID, hash/receipt/URL, loại chứng khoán và liên kết hủy.
Đối chiếu 53 tệp artifact mới và 34 input đã pin đạt; compileall và synthetic
smoke đạt. Bộ kiểm thử liên quan chạy 46 test: 45 đạt, một lỗi legacy do test tìm
helper ở `tests/unit/scripts/review_cached_corporate_actions26_v1.py` không tồn tại.
Giữ nguyên test/runtime; chưa sửa lỗi đường dẫn ngoài scope. Log, self-review và
validation ở `tmp/ors_equity_detail_review_20261106_v1/`.
Bước tiếp theo đề xuất là review/reconcile ba candidate với evidence ex-date và
revision theo contract hiện hành trước khi xét canonical. Nhóm 7 mã lớn và 418
mã của chiến dịch chưa thực hiện; không tự mở stage đó.

## Corporate action — kiểm kê cache chi tiết ORS, 06/11/2026

Đối chiếu đủ 85 ID danh sách với index raw đã pin, inventory reusable V7 và năm bài
đã review DOM. Có 20 bài với raw, SHA-256 và receipt GET HTTP200 đã đối chiếu. Năm bài
trang cuối có các trường review từ DOM. Còn 60 bài vắng trong cache chi tiết đã audit,
gồm 24 tiêu đề mã cổ phiếu ORS và 36 tiêu đề mã trái phiếu bắt đầu bằng ORS.

Toàn bộ danh sách gồm 31 bài gắn tiêu đề/nội dung cổ phiếu ORS và 54 tiêu đề trái
phiếu ORS*. Hai bài cổ phiếu và 18 bài trái phiếu thuộc nhóm có raw. Năm review DOM
chỉ lưu trường đã đọc. Inventory ghi riêng mức evidence này. Kết quả kiểm kê đạt
`PASS_ORS_85_DETAIL_CACHE_INVENTORY`, với 0 network request.

Bước tiếp theo là bổ sung/review nội dung 24 bài tiêu đề cổ phiếu ORS. Ưu tiên
`171704` (cổ tức cổ phiếu), `166577` và `142284` (quyền mua) theo tiêu đề, sau đó
kiểm tra các thông báo hủy danh sách/ngày đăng ký cuối cùng để nối revision.
Evidence và queue ở `data/corporate_actions/work/vsdc_ors_cache_inventory_20261106_v1/`.
Prompt bàn giao cho chat mới nằm trong `handoff_prompt.txt` tại cùng thư mục.

## Corporate action — phân loại năm thông báo ORS, 06/11/2026

Đã đọc nội dung chính của năm bài ở trang 5 và đối chiếu ID với hồ sơ danh sách ORS.
Cả năm là thông báo chốt quyền họp và biểu quyết, gồm bốn ĐHĐCĐ thường niên và một
ĐHĐCĐ bất thường. Phân loại `NON_PRICE_ACTION_NOTICE` theo cách phân loại của bộ
thu thập VSDC. Mệnh giá 10.000 đồng nằm trong phần thông tin chứng khoán. Có 0 ứng
viên sự kiện điều chỉnh giá từ năm bài này.

Bài `9509` và `5416` hiển thị Tiên Phong trong phần thông tin tổ chức phát hành và
Phương Đông trong nội dung họp. Ghi nhận cả hai nhãn trong review. Hồ sơ lưu ngày
đăng ký cuối cùng và lịch họp dự kiến đọc từ DOM, với 0 trường canonical áp dụng.
Xem `data/corporate_actions/work/vsdc_ors_detail_review_20261106_v1/review.json`.

## Corporate action — đối chiếu đủ danh sách ORS trên Chrome, 06/11/2026

Đã quan sát đủ năm trang của cùng truy vấn ORS trên tab Chrome người dùng đang mở.
Danh sách có 85 ID khác nhau trên 85 bản ghi được báo. Các trang 1–4 khớp đúng thứ tự
của 80 ID đã review. Trang 5 bổ sung ID `21128`, `16287`, `9509`, `7739`, `5416`.
Số bản ghi chưa quan sát trong danh sách ORS giảm từ 5 xuống 0. Bằng chứng là
phạm vi hiển thị và link ID trên DOM, lưu trong
`data/corporate_actions/work/vsdc_ors_browser_list_review_20261106_v1/review.json`.

Năm ID trên vắng trong inventory danh sách và cache chi tiết V7. Bước tiếp theo là
review riêng năm bài để phân loại nội dung trước khi dùng ở lớp corporate action.
Kết quả trên Chrome xác minh phạm vi danh sách hiển thị. Hai phiên thu thập cũ ghi
nhận phản hồi rỗng ở hai lần khác nhau và vẫn là bằng chứng của các lần đó.

## Corporate action — chẩn đoán ORS dừng ở trang 1, 06/11/2026

Phiên riêng `run-20261106T012817260681Z` dùng Chrome ẩn và giới hạn năm request danh
sách. Request GET đầu tiên nhận HTTP 200 với body 0 byte. DOM thiếu vùng danh sách,
chờ selector hết thời gian. Phiên đã seal ZIP và giải phóng lock sau một request.
Kết quả `PARTIAL_QUERY_HOLD_REVIEW_REQUIRED` chưa xác minh được trang nào trong phiên
mới. ORS vẫn HOLD với mốc đã review là 80/85 bản ghi. Chưa xác định nguyên nhân nguồn
trả body rỗng. Phiên này chưa đến bước kiểm tra trang 5.

Đã kiểm tra lại ZIP, manifest và ledger. Bộ kiểm thử liên quan đạt 14 test,
compileall và synthetic smoke đạt. Evidence trong
`data/corporate_actions/work/vsdc_ors_gap_diagnostic_v1/run-20261106T012817260681Z/`.
Bước tiếp theo là xác minh trang tìm kiếm ORS có hiển thị danh sách trong trình
duyệt thường trước khi thử phân trang ở một phiên chẩn đoán riêng.

## Corporate action — review offline phiên V7, 06/11/2026

Phiên `run-20261104T041619408451Z` đạt review offline cho **1.072/1.072 mã trong scope**
qua 54 batch. Đối chiếu SHA-256 của 43.883 tệp trong ZIP và 616 checkpoint nhập với
seed đã review. Parse lại 1.225 trang của 456 truy vấn mới, kiểm tra ZIP con, ledger,
budget và log tiến độ. Có 9.278 ID bài mới trong danh sách. Review dùng dữ liệu trong
ZIP và có 0 request VSDC. Kết quả áp dụng cho danh sách truy vấn trong scope. Các gate
canonical, PIT, historical identity và full history vẫn chờ quy trình review tương ứng.

ORS giữ `HOLD_SOURCE_COUNT_GAP`. Bốn trang đầu có 80 ID khác nhau trên tổng 85 được
nguồn báo. Trang 5 trả HTTP 200, body 33 byte và không có vùng danh sách. Bước tiếp
theo là chuẩn bị một phiên chẩn đoán giới hạn cho ORS để xác minh phần chênh 5 bản ghi.
Hồ sơ review nằm tại `data/corporate_actions/work/vsdc_v7_offline_review_20261106_v1/review.json`.

## Corporate action — sửa supervisor nhận diện chính phiên đang chạy, 04/11/2026

V6 preflight đã đạt nhưng worker coi thư mục vừa được supervisor tạo là phiên cũ chưa
seal. Phiên `run-20261104T040725938706Z` chưa tạo state hoặc gửi source request.
Cả PID 27236 và 27440 đã được xác minh thoát. Folder và lock được lưu nguyên nội dung
trong `data/corporate_actions/work/vsdc_supervisor_v7_incident_review_20261104_v1/`.

Public CLI hiện hành là `scripts/corporate_actions/collect_vsdc_recovery_supervisor_v7.py`.
V7 ghi audit/pause vào metadata riêng và để worker tự tạo run directory sau history check.
Worker, preparation và runtime V6 được giữ nguyên byte, tiếp tục dùng prefix 616 query,
còn 456 query trong scope và ORS HOLD. Output checkpoint vẫn thuộc thư mục V6.
Tests đã tái lập luồng supervisor → process ẩn → actual V6 worker CLI → history → seal
bằng synthetic source responses. Evidence ở `tmp/ca_supervisor_v7_20261104_v1/`.
Stage sửa supervisor PASS với 30 targeted tests, gồm 1 opt-in test skip, compileall và
synthetic smoke. Đối chiếu 91 runtime hash, preparation V6 83 file và history prefix
616 query đạt. Dùng bằng chứng raw preflight PASS ngay trước lỗi, tránh lặp kiểm tra
24.585 file đã freeze trong cùng stage. Có 0 request VSDC thật trong kiểm thử.
Bước tiếp theo là chạy local theo hướng dẫn hiện hành (đã gỡ khỏi repo ở commit `3fe08da`, xem lịch sử git)
và gửi `OUTPUT_ZIP` để review. Các mục chuyển nhánh bên dưới là lịch sử.

## Chuyển corporate action sang feature/indicators-v1 — 04/11/2026

Đưa nguyên nội dung code/config/schema/fixtures/tests và các đường dẫn tương thích của
corporate action từ `m3-backtest@8827ebf` sang nhánh hiện tại. Stage chuyển bộ thu thập.
Dữ liệu local và preparation V6 tiếp tục dùng đúng đường dẫn cũ. Runtime 89 file khớp
SHA-256 đã pin. Prefix có 616 query hoàn tất, còn 456 query trong scope V6 và ORS HOLD.
Việc thu thập tiếp chạy local theo hướng dẫn V6 (đã gỡ khỏi repo ở commit `3fe08da`, xem lịch sử git).

Stage chuyển nhánh PASS. Đã đối chiếu 438 file được đưa sang với source branch, 89 runtime
hash và 91 protected code/config hash. V6 `--check` đạt `OFFLINE_CHECK_PASS`, gồm kiểm
24.585 raw file đã freeze, 616 checkpoint dùng lại được và 456 query còn lại. Bộ tests
corporate action đạt 397 test, gồm 1 skip cho integration Windows opt-in. Compileall và
synthetic smoke đạt. Kiểm tra offline có 0 source request và không mở browser.
Evidence kiểm thử ở `tmp/ca_branch_transfer_20261104_v1/`.

Bước tiếp theo là chạy public supervisor V6 local theo hướng dẫn, rồi gửi `OUTPUT_ZIP`
khi hoàn tất, pause hoặc gặp lỗi để review. ORS còn HOLD. Budget batch 032 còn khoảng
103 giây active theo preparation đã pin, vượt cap sẽ STOP để review.

## Hướng chính thức (D-DIR-01, 26/10/2026)

- **Phân cụm thị trường (M2):** mô hình A của bundle web v4 — 9 đặc trưng, lọc thanh khoản nhẹ, log + cắt đuôi +
  z-score, K-Means k=3 học trên mã có giao dịch (chọn bằng `clustering_rework_v2`; chọn lại chỉ trên 2019–2023 vẫn k=3).
- **Phân cụm tài chính:** mô hình B của bundle v4 (9 chỉ số, k=3, chưa đạt ngưỡng ổn định — giới hạn đã ghi).
- **M3:** `M3/KE_HOACH_M3_SCHEMA_GITHUB.md` + ADR D-M3-01 (03/11/2026); đọc A v4 + B-PIT + Indicators v1 + ngày công bố CafeF. `M3/M3_PLAN.md` là lịch sử đề xuất.
- **Hướng cũ (LEGACY, chỉ làm đối chứng/tái lập):** bàn giao M2 K=2 trong `M2/`, báo cáo `Bao_cao_M2_Nhiem_vu_4.*`,
  dashboard Streamlit `m3_dashboard.py`, web cũ `web/index.html|app.js|styles.css`. Giữ nguyên đường dẫn vì code/test
  cũ còn đọc; không dùng làm input cho việc mới.
- Bằng chứng: `artifacts/reports/m2-vs-rework-v1/report.md`.

Các mục bên dưới là lịch sử theo thời gian; khi mâu thuẫn, mục này được ưu tiên.

## M3 — Development và Holdout đã chạy và seal (04/11/2026)

M3-A Development (run `20261104T121107Z-5557288c`) và Holdout (run `20261104T133507Z-5557288c`)
đã chạy, verify và seal với code `c9c1f5f`, config `configs/experiments/m3_strategy_v1.json` LOCKED.
Final Evaluation NOT_READY do chưa đủ dữ liệu 2026; M3-C PARTIAL; M3-B (dashboard) chưa làm.
Kết quả: `docs/REPORT_BACKTEST.md`, `M3/reports/BAO_CAO_KY_THUAT_M3.md`; CSV trong `M3/outputs/`.

## M3 — methodology khóa, code sync, chờ build B-PIT trên máy có dữ liệu (03/11/2026)

ADR D-M3-01; kế hoạch chuẩn `M3/KE_HOACH_M3_SCHEMA_GITHUB.md`. Code/config đã sync; B-PIT đã có code nhưng chưa
build (cần `data/` local). Việc tiếp theo và lệnh chạy: `M3/M3_READINESS.md`.

## M3 giai đoạn 0 và lõi engine (25/10/2026)

`scripts/m3_stage0.py`: manifest đầu vào có hash, đếm tập ứng viên từng tháng, kiểm cơ sở lợi suất (không tính lợi
suất danh mục). Development: trung vị 8 ứng viên, 38/60 tháng dưới 10 → cần mentor chốt lại Q5/Q6. `adj_close` đã gồm
cổ tức tiền mặt; 1.030 lỗi adj lệch một phiên (đề xuất Q17). Engine `src/delta_t1/m3/` + 16 test PASS.
Chi tiết: `M3/M3_PLAN.md` mục 7.

## Ngày công bố BCTC cho M3 — đã crawl (25/10/2026)

Theo D-CRAWL-02: `scripts/crawl_cafef_disclosure_dates.py` lấy "Thời gian gửi" (`CreateDate`) từ API Công bố thông tin
CafeF cho 1.362 mã có nhãn B (`data/financial/disclosure_dates_v1/full-20261025`, không bị chặn).
`scripts/build_financial_availability.py` → `availability-0c412f60f7c21bd3/availability.csv`: FY ≥ 2022 dùng ngày CafeF
(1.257–1.327 mã/năm), trước 2022 dùng quy tắc trễ 30/06 năm sau (CafeF nhập lại lịch sử ngày 26/11/2022).
Đối chiếu 9 mã-năm kiểm tay: không ngày nào sớm hơn thực tế. Chi tiết: `M3/M3_PLAN.md` nhiệm vụ 0.2.

## Bundle v4 = v3 + giải thích (bản đồ mô hình, tên cụm) — đã build, CHỜ OWNER KIỂM TRA (25/10/2026)

`scripts/build_delta_bundle_v4.py` → `data/web/delta-intelligence-v4/` (cụm giữ nguyên như v3, không học lại).
Atlas mặc định "Bản đồ mô hình" (PCA của không gian mô hình), tên + mô tả 1 câu cho mỗi cụm
(`src/delta_t1/product/cluster_story.py`), khung "Mô hình hoạt động thế nào?"; trang cổ phiếu hiện nhóm giá/tài
chính/kết hợp của mã. Deploy đã chuyển sang v4 (commit 6380959, Render + Vercel, 25/10/2026).


## Bundle v3 (học trên mã có giao dịch, gán phần còn lại) — đã build, CHỜ OWNER KIỂM TRA (25/10/2026)

`scripts/build_delta_bundle_v3.py` → `data/web/delta-intelligence-v3/` (v1, v2 giữ nguyên; deploy vẫn trỏ v2).
2025: A 1.410 mã = 789 có giao dịch + 621 "Kém thanh khoản", cụm 803/418/189; C 1.139 mã, cụm 605/242/181/111.
Nhãn "Kém thanh khoản" trên trang cổ phiếu, bảng thành viên Atlas; ghi chú B chưa ổn định trên Atlas.


## Phân cụm lại v2 (lọc thanh khoản + Ward/PCA + chọn đa thước đo) — đã chạy, CHỜ OWNER DUYỆT (25/10/2026)

`scripts/run_clustering_rework_v2.py` → `data/experiments/clustering_rework_v2/rework2-549f29de83924b07/report.md`.
A lọc nhẹ (789 mã có giao dịch, 621 "Kém thanh khoản" 2025) K-Means k=3; lọc chặt (552/858) PCA+K-Means k=3.
B: không cấu hình nào đạt ổn định lấy mẫu con ≥0,8 (B đang chạy chỉ 0,50). C: PCA+K-Means k=3/4. Ward không ổn định.
Bundle v2 trên web chưa đổi.


## Phân cụm lại v1 — owner duyệt, bundle v2 đã build, CHỜ KIỂM TRA TRƯỚC DEPLOY (25/10/2026)

`scripts/build_delta_bundle_v2.py` → `data/web/delta-intelligence-v2/` (v1 giữ nguyên). Cỡ cụm 2025:
A 634/324/323/129; B 705/279/216; C 733/291/115. Chạy local với `DELTA_BUNDLE=data/web/delta-intelligence-v2`.
Owner duyệt v2: local, Render (`DELTA_BUNDLE`) và `publish_hf_data.py` đã chuyển sang v2; mới dry-run, CHƯA upload/deploy.

## Indicators v1 — Giai đoạn 1–5 xong, local, chưa push (25/10/2026)

Nhánh `feature/indicators-v1`. Input `data/financial/indicators_v1/inputs/inputs-5b4836454b70d737/`
(1.510 mã, 14.738 mã-năm; ngân hàng/CK/bảo hiểm từ raw CafeF; DStock lấp 616 mã-năm CafeF thiếu;
CFO của 181 mã từ LCTT trực tiếp). Kết quả `data/financial/indicators_v1/results/indicators-2c4a24e3830d325f/`
(`indicators.sqlite`, 319.620 ô, `qa-report.md`). QA độc lập 800 ô PASS. Mục tiêu 2025 đạt hết:
EPS 92,5%, P/E 91,8%, P/B 91,5%, ROE 99,9%, F 88,4%, M 80,0% (sát ngưỡng; 114 ô dùng khấu hao
dự phòng từ hao mòn lũy kế), Z 91,2%. EPS khớp EPS công bố ±10%: 75%.
Giai đoạn 4 xong: 4 endpoint `/api/v2/stocks/{ticker}/{overview,fundamentals,scores/{year},peers}`
(`web/backend/app/fundamentals.py`, pointer `configs/product/indicators_v1.json`), 7 API tests mới PASS.
Giai đoạn 5 xong: trang `/stocks` mới (header giá/vốn hóa, 6 thẻ + tooltip 1 câu, 4 tab Tổng quan /
Chỉ số tài chính / Điểm sức khỏe / So sánh cùng nhóm, modal "Cách tính"); bỏ chữ review/vintage/cohort/pilot
khỏi giao diện chính; `npm run build` PASS; screenshots FPT/VCB/BHH 1440 + 390 tại `.tmp/indicators-ui/`.
Còn lại: deploy public chờ owner duyệt; phân cụm lại bằng chỉ số mới (ROADMAP).

## Bổ sung EPS theo kỳ và UX chỉ số — local, chưa release (24/10/2026)

Đã chạy offline trên inventory 1.522 mã: đối chiếu raw code/label/đơn vị EPS,
period/provider và raw value, giữ 53.716 reported EPS observations/1.427 mã
(12.782 annual, 40.934 quý/lũy kế). Serving source có 47.208 EPS/1.426 mã sau
khi giữ 6.508 source-zero chưa xác nhận ở trạng thái chờ đối chiếu; không gọi
reported EPS là EPS tự tính hoặc independently verified. Ledger gồm 85.212
period/mode slots × 6 families = 511.272 cells, có cả kỳ chưa có số.
79.566 calculator evaluations/13.261 annual provider partitions vẫn chưa sinh
score mới đủ điều kiện release: weighted shares/EPS numerator, đủ9 F signals,
owned PPE depreciation, reconciled EBIT và dated valuation basis còn thiếu.
Không dùng inferred shares/proxy EBIT hoặc ghép giá để tạo coverage giả.
UI đổi sang năm/kỳ báo cáo và giải thích mục đích từng chỉ số; technical package
IDs/vintages/hashes xuống source details. API đọc SQLite EPS theo ticker, không
load 53k evidence rows mỗi request. 26 targeted tests, compile/synthetic smoke và
production build PASS ở lượt kiểm này. Chưa đóng research/PIT gates hoặc deploy.
[Runbook và artifacts](../web/README.md#bổ-sung-eps-theo-nămquý-và-trải-nghiệm-chỉ-số).

## Nâng cấp DELTA — triển khai local, chưa release (24/10/2026)

Đã triển khai D0/D1/U1–U3, diagnostics R0 và bounded R1 theo yêu cầu thực hiện
hoàn chỉnh plan. [Kết quả từng stage, pins/tests và gates còn mở](DELTA_UPGRADE_PLAN.md#11-thực-thi-nâng-cấp--24102026).
87 unique numeric observations/11 mã; hai Z FY2024 đã nối đúng vintage. UI năm trang
đã tổ chức lại, 25 responsive cases PASS; R1 757 models được independent replay PASS. Có selector P1/P3 preview (202 snapshots), baseline vẫn mặc định.
Chưa promote model, chưa đóng source/usefulness/PIT hoặc public release. Full suite
984 tests còn một error do thiếu immutable legacy fixture, bốn Streamlit skips.


## Rà soát demo: sáu chỉ số và đồ thị phân cụm — 24/10/2026

Đã sửa omission product: EPS/P/E/P/B/F/M/Z đã review có panel riêng tại Tra cứu cổ phiếu,
API v2 indicators, pin hai nguồn (85 numeric rows/11 mã và pilot5 29/30 subset; không cộng trùng).
FPT pilotFY2025: EPS5216,068015; PE14,301961; PB3,483579; F3/9; M−2,279981; Z7,106292.
PE/PB dùng raw22/04/2026, book31/12/2025; không gán vào market31/12/2025 như PIT.
Snapshot/vintage và YTD/quarter được giữ riêng; VNM F thiếu vẫnnull. Không tính lại/model mới.

Review source `dual-cluster-review-v1/separation-drivers.csv`: A31/12/2025 liquidity share
0,9999658458053156; native groups26/1384. Atlas cảnh báo rõ baseline bị liquidity chi phối.
Website owner gửi (`cafz.phuongquan.vn/companyDetail/FPT`) có tab Tech Peers Clustering,
quan sát7mã/3màu/trụcPE–ROE, chưa có protocol/scaler/cohort đầy đủ để chứng nhận chất lượng.
Không lấy giá trị hoặc labels của website làm research input.

Giao diện demo đã Việt hóa theo yêu cầu owner: 5 màn hình, nhãn đặc trưng, trạng thái, hướng dẫn và định dạng `vi-VN`; giữ mã feature, công thức và protocol gốc để đối chiếu. Không thay dữ liệu hoặc mô hình.

## Execution59 — Demo web A/B/C đã triển khai — 24/10/2026

Web mới `web/frontend` (Next.js/TypeScript/ECharts/TanStack) + `web/backend` (FastAPI)
đọc SQLite presentation local, giữ dashboard cũ. Adapter không fit/scaler/research metric.
Bundle thật có 75.801 A, 11.720 B, 5.593 C observations và 3.214.287 daily price rows.
API verify checksum, read-only; missing/ambiguous fail closed, không forward-fill hoặc
trộn price basis. Migration alignment chỉ đổi display target labels; original labels giữ nguyên.

10 API contract tests PASS; compileall + legacy JS syntax PASS; production build PASS.
Verifier thực PASS: 101 snapshots/219 profiles/7 matrices/22 hashes, sample price replay.
Full suite 240s: PARTIAL, 254 tests OK trước fixture crawl 50 mã bị timeout; không có full-suite PASS.
Browser QA đã kiểm Overview, Atlas C/tiny cluster/FPT drawer, Stock Explorer,
Financial matrix/FY2016 empty state và Research Lab; responsive 390px.

Chạy `python scripts/start_delta_terminal.py`; [setup và giới hạn](../web/README.md).
Code stage59 đang local; chưa push. Data, node_modules và .next bị ignore.
Financial published_at vẫn 0/11.720; fixed full10 survivorship bias và tiny clusters chưa giải quyết.

## Execution58 — A/B đối chiếu và C kết hợp đã chạy — 24/10/2026

Đã giữ A market-only (168 profiles/84tháng) và B financial-only (30 profiles/10năm)
riêng, tạo bảng đối chiếu và chạy C theo cấu hình owner đã duyệt trong chat.
C:14features, z-score từng năm trên common cohort, blockweights50/50,
KMeans k3/seed42/n_init20/max_iter300, no clipping/PCA/imputation. 7 models hội tụ,
5.593assignments trên2019–2025; independent verification PASS. C2025 có663/479/6mã;
cả7năm có cụm dưới10, quality REVIEW_REQUIRED. Không sửa A/B hoặc tối ưu bằng returns.

- [Report A/B/C](../artifacts/reports/cluster-comparison-v1/report.md).
- [Bảng nhãn A/B/C cuối năm](../artifacts/reports/cluster-comparison-v1/memberships-a-b-c-year-end.csv):9.213unionrows,5.593BOTH có C.
- [Catalog219profiles](../artifacts/reports/cluster-comparison-v1/cluster-catalog-a-b-c.csv).
- [Protocol C](../configs/experiments/combined_reference_v1.json).
- [C verification](../artifacts/reports/combined-reference-v1/verification.json).
- [C result pointer](../artifacts/reports/combined-reference-v1/result-ref.json).

Market liquidity_21 chiếm median99,997% phần tách centroid theo fittedmetric;
không tự chứng minh dataerror. Financial180outlierrows/157vectors replay đúng
selected inputs; scope/unit/facts chưa tự nghiệm thu. 0/11.720rows có published_at
trong delivery: C là EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT, khônghistoricalPIT,
khôngbacktest/M3, khôngnewholdout. Historical C vẫn cần gates theoUnifiedPlan§15–16.

Integration tới efb7104 đã push; Execution58 là công việc mới local, chưa push.
Full repository gate vẫn chưa có PASS; targeted và numerical verification ghi riêng.


### Chốt integration — 24/10/2026

Đã xử lý toàn bộ merge conflicts; imported data giữ local theo ignore policy.
Financial checkpoint `819cd82`, market parent `340519d`; active branch `integration/market-financial`.
PowerShell wrapper `scripts/market_financial_integration.ps1 -Mode Verify` đã PASS:
market19C8outputs/68holdoutoutputs/84models/75.801assignments; financial1.786pins/11.720rows.
Targeted76tests OK (4optionalStreamlit skips), PCA6tests PASS, importer/immutability5tests PASS
(suite5 gồm4tests đã có trong targeted76 và1test bổ sung, không cộng trùng).
Compile, synthetic smoke và webJS syntax PASS; importer replay20files PASS.

Full repository gate vẫn PARTIAL: sandbox timeout240,2giây; ngoài sandbox timeout360,1giây,
ít nhất250testlines kết thúcok, chưa cóFAIL/ERRORtrước timeout; cuối log ở
`unit.experiments.test_financial_crawl_trial.TrialTests.test_invalid_payload_stops_next_wave_with_all_symbol_gap_rows`.
Không khẳng định suite treo hoặc xác định nguyên nhân từ việc timeout; không bỏ assertions.
Logs `.tmp/integration-full-suite*.log`, summaries `.tmp/integration-full-suite*.json`.

Không fit lại model thực, không acquisition/PDF/OCR mới, không backtest; PIT/research/M3
vẫn false, chất lượng cụm REVIEW_REQUIRED. Commit tích hợp chỉ local; chưa push remote.


**Integration market + financial — 23/10/2026.** Nhánh `integration/market-financial`
kế thừa financial checkpoint `819cd82` và market `340519d`. C8 V2 đã nhập từ
`DELTA_02_ACTIVE_M2_M3.zip`, giữ đúng hashes và path. Market có 84 snapshots
2019–2025, K=2/robust; financial có 1.172 mã × annual 2016–2025, K=3/zscore.
Đây là hai baseline độc lập. Cả hai cần review chất lượng cụm; strict PIT/research/M3
chưa được nghiệm thu. Giao ticker tại cuối 2025 là 1.148 mã, chưa phải historical PIT join.

Chạy `scripts/verify_market_financial_integration.py --publish` để kiểm current
60+24 artifacts và tạo manifest tham chiếu có version; script này không fit.
`verify_m2_task12.py` và `generate_m2_task13_handoff.py` là historical V1,
không dùng chúng để tái tạo current84. Xem `M2/artifacts/market-financial-integration-v1/`.

### Kiểm chứng integration đã thực hiện

- Market:19/19C8outputs,68holdoutoutputs,9frozenpins,84models và75.801assignments PASS;
  kiểm sourceeligibility và nearestcentroid, không refit.
- Financial:1.786inputpins,11.720rows, scaler/assignment/inertia/profiles/checkpoints PASS
  với hai frozen source files đúng hash trong sourceoverlay có version; output review riêng.
- 76 targeted tests: OK,4Streamlittests skipped do thiếu optionaldashboarddependency;
  6 PCAartifacttests PASS. Importer/immutability tests bổ sung PASS.
- compileall, synthetic smoke (`run-20261023T161947Z-e04ef3b8`), `node --check web/app.js` PASS.
- Full repository suite chưa PASS: sandboxtimeout240giây; lượt ngoàisandbox được giới hạn360giây,
  xem `.tmp/integration-full-suite-unsandboxed.json` và log. Không bỏ assertions.
- Plain diffcheck toàn nhánh có inheritedCRLF/Markdownhardbreak warnings từ market artifacts;
  scoped integrationdiffcheck với `cr-at-eol` không có whitespace errors. Không sửa sealedbytes để làm sạch warnings.

## Ghi chú và lineage từ các giai đoạn trước

**Execution56 — baseline financial đã chạy (23/10/2026):** 1.172 candidates × 10 annual
periods, 70.320 core ratios tính lại khớp, 10 static K-Means models hội tụ. [Report](../artifacts/reports/financial-full10-baseline-v1/report.md),
[verification](../artifacts/reports/financial-full10-baseline-v1/verification.json).
1.786 input pins, scaler từng năm, assignments/inertia/profiles và checkpoints đã kiểm độc lập.
11 targeted tests/compile/synthetic smoke PASS. Chất lượng **REVIEW_REQUIRED**: mọi năm có cụm
dưới 10 mã, năm 2025 là 1.168/3/1; không gọi M2/M3 final PASS. Giữ protocol hiện tại,
không tự loại outliers hoặc đổi scaling. Checkpoint trước chạy `f1a5ba7` đã push lên
`origin/research/financial-data`. Các section dưới là lịch sử.

**Execution55 — lịch sử đã gom:** data221→59roots, reports57→13. [Archive vàrestore](../artifacts/archives/financial-history-20261023/README.md). Giữ dependency/control của dataset1.172mã; M2chỉ đọc handoff hiệnhành. Phân cụm chưa chạy.

**Cleanup54 — cache cũ đã lưu lạnh:** 102,504candidatefiles từbốn batch được chuyểnZIPđãverify, raw/receipts/journals giữtrực tiếp. [Guide restore](../artifacts/archives/financial-cache-20261023/README.md). Chỉdùng [handoff mới nhất](../data/handoffs/financial-reference-2016-2025/README.md) choM2; dataset1.172full10khôngđổi, chưa phâncụm. Fullhistoricalreplay cóthểcầnrestorecache.

**Bắt đầu với bộ financial hiện hành:** [Dataset1.172mã/2016–2025](../data/handoffs/financial-reference-2016-2025/README.md) · [Report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md) · [Lệnh đang dùng](../scripts/README.md).

**Cleanup53 đã hoàn tất, phân cụm chưa chạy:** 2,889file đãgỡ khỏiworkingtree; report/helpers lịch sử giữZIP cóhash vàrestore, cachetái tạo đượcxóa. Không đổi raw/canonical, counter, dataset13.529rows/1.172full10 hoặc model. Chi tiếttạiExecution53 trongreporttổng. Các sectioncũ dướiđây làlineage, khôngđại diệnworker đangchạy.

**Báo cáo tổng financial:** [Mở lịch sử và tiến độ hiện tại](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md). Cập nhật liên tục qua các giai đoạn; đọc trước các report theo run.

**Ưu tiên hiện tại — Execution50 (23/10/2026): 1.172 mã đủ annual 2016–2025 / 13.529 core-ratio reference rows.** Đã thử hết 2.444 Regular gap cases qua49+50; tăng170full10 và961rows, giữ12.568baseline rows. Còn761held kỳ/257Regular candidates và93candidates ngoài Regular schema;95mã thiếu1kỳ. [Report tổng](../artifacts/reports/FINANCIAL_DATA_MASTER_REPORT.md), [report50/runbook](../artifacts/reports/financial-dstock-remaining-v1/report.md), [1.172mã](../artifacts/reports/financial-dstock-remaining-v1/full10-candidates.csv), [cohort/features](../artifacts/reports/financial-dstock-remaining-v1/delivery-result-ref.json), [field review](../artifacts/reports/financial-dstock-remaining-v1/field-review.csv). 47targeted tests/independent verification PASS;0PDF/0OCR. Worker đã dừng. EPS/P/E/P/B/F/M/Z toàn lịch sử và PIT/M3 vẫn PARTIAL. Xem `scripts/financial_dstock_remaining.ps1 -Mode Status`; dashboard acquisition cũ không phải counter DStock.


**20/10/2026 — Financial F3 critical review/reference PARTIAL; goal ACTIVE.**
[Execution hiện tại](crawl/FINANCIAL_HISTORY_PIT_PLAN.md#21-execution-tiếp--gas-pdf-reference-và-shs-critical-quarantine-20102026),
[PowerShell](../scripts/financial_history_process.ps1),
[critical review — archive](../artifacts/archives/financial-history-20261023/data/financial/history_critical_review_v1/4c87c15431782b8e491b/summary.json).
GAS PDF32reviewedfacts,2Z″EM referencevalues cho2025/2024 từ FY2025vintage;8accountingchecksPASS.
GASannualHKCDKT:2namedfields sai lệch, Q4 đúng theoPDF. SHSannualKLCTT:7namedPDFnonzero/APIzero,
1unresolvednonzeroorphan;2APIpartitionsquarantine, khôngrepair/accept. SHSreusePDFcache10MB,
publication website22/03/2026 không gán sangcachedPDFcover23/03/2026. GASexplicitpub04/03/2026.
OCR130pages/0errors. Cumulative2.284requests/211.688.837bytes/18PDFattempts;2SHSfileschạpcap25MB
vẫn được tính, khôngretry/reset. VDSC2HTTP302 khôngfollow; BMSCDBC2013linklegacyHTTP chưa dùng.
IndependentF3audit vẫn4/6/35fieldmatches+1signconflict; DCM/HSG2025 và2auditPDF cònmở.
Baseline29/30/VNM Fnull, strictPIT0, chưa50/M3.167targeted/compile/syntheticPASS;activeverify PASS;cachepreflight209PDFfiles/200uniquehashes.
Fullrepo gate chưaPASS; knownM2-PREP frozenhash mismatch giữ nguyên, không waiveassertion.

**19/10/2026 — Financial history pilot5: acquisition COMPLETE, QA/delivery PARTIAL.**
[Flow/commands](crawl/FINANCIAL_HISTORY_PIT_PLAN.md#9-qa-offline-và-handoff-bổ-sung-chọn-lọc),
[final acquisition](../data/financial/history_pit_v1/reports/4bf06a5671299d42c73f/report.md),
[offline QA — archive](../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/1692b3eb579b426c1e2f/report.md).
Worker đã kết thúc: 563 new requests/attempts, 5.313.164 bytes, 27 cache hits,
71.073 candidate cells, không pending. Coverage980: 918 main candidate-present,
5 auxiliary, 57 missing (19 issuer-periods). Catalogue host latch giữ nguyên.
QA riêng không sửa acquisition code/raw: 1.161 structural group-header zeros được
chứng minh từ đúng template, 69.912 nonstructural cells; 7.890 code/label mappings
chỉ diagnostic. 1.551 raw accounting equalities/95 differences; annual–Q4 có
6.652 equalities/1.993 differences, giữ provider partitions và unknown vintage/scope.
Detector bắt BRC/VNM FY2025 row shifts dù tổng cân, không sửa vị trí. Reviewed
PDF raw-value comparisons:138match/12conflict; không suy unit hoặc acceptance.
Queue90issuer-periods (6priority1/84priority2),13có cache PDF candidates. H1 không
tự thay Q2. 0 new accepted/PIT facts; chưa historical compute/batch20. Baseline29/30,
VNM F thiếu input. 59 targeted tests/compile/synthetic smoke PASS; acquisition và
QA replay kiểm độc lập; [validation — archive](../artifacts/archives/financial-history-20261023/data/financial/history_pit_qa_v1/validation/verification.json).
Registry/code pins và counters cũ giữ nguyên; không tiếp resume acquisition đã hết task.

**19/10/2026 — Materialize hai plan và registry team: OFFLINE INVENTORY COMPLETE; acquisition PLANNED.**
[Market ≥1.500 cổ phiếu lịch sử](crawl/MARKET_HISTORY10Y_1500_PLAN.md),
[financial history/PIT](crawl/FINANCIAL_HISTORY_PIT_PLAN.md),
[registry dùng chung](../configs/data/securities_collection_registry_v1.csv).
Market chính2016–2025 +warm-up2013–2015; financial2013–2025 +closing2012 khi cần.
Registry1.522 current candidates =500C5+452C7complete+7failed+3partial+138not-yet+422outside.
952C8processed/905ready tại28/08/2026; identity/M3 chưa verified. Current discovery
không phải historical census. Local financial exports/pilot5 được inventory, phần
khác giữ UNKNOWN/NOT_INVENTORIED; counts reference chỉ FY2025 pilot5, không full history.
Không network/OCR/crawl mới, không sửa sealed data hoặc reset boundaries; pilot vẫn29/30.
Next work theo stageM0/F0 của hai plan, không chạy scale từ CSV ngay.
Offline checks PASS:1.522unique/45columns,37pinned source files, C8price SHA khớp
sealed manifest và17local links của hai plan. Financial:5pilot references+50other
candidate exports;1.467not-inventoried trong scope quét, không kết luận chưa crawl.

**19/10/2026 — VNM subsidiary debt review: PARTIAL 29/30.**
[Evidence/replay](../data/financial/vnm_subsidiary_debt_review_v1/report.md).
Thêm 7 PDF: MCM/Vilico 2025, Vietsugar 2024/2025 + AGM, VNM Q1/2025;
50.239.615 bytes, 54 trang render/40 ảnh xem/0 OCR thành công. MCM/Vilico
cùng nhóm vay 4–6 tháng, chỉ loại một lần trong diagnostic bounds. Vietsugar
đối chiếu được 587.715.602.250/420.793.498.260 VND nhưng kỳ hạn gốc chưa rõ;
không loại chỉ theo nhãn ngắn hạn. Hai kết quả leverage vẫn có thể xảy ra.
0 accepted metric inputs; giữ 29/30/gates false. Đã soạn yêu cầu IR, chưa gửi.
34 targeted tests PASS; offline replay/compile kiểm riêng, không lặp full gate.

**19/10/2026 — VNM quarterly-debt follow-up: PARTIAL 29/30.**
[Evidence và replay](../data/financial/vnm_quarter_debt_followup_v1/report.md).
Tải thêm Q4/2024 XLSX và Q4/2025 PDF từ observed links: 2 requests,
4.179.903 bytes; 16 trang render/8 ảnh xem/0 OCR. Workbook chỉ ba statement sheets;
Q4/2025 và cached H1/2025/H1/2026 chưa tách closing original-maturity current
portion 2024/2025. PDF xác nhận tổng vay Q4/2025 cao hơn QUY API 1 triệu VND.
Primary Piotroski Table 1 xác nhận phải gồm current portion; không đổi công thức.
0 new accepted metric inputs; giữ nguyên result, 29/30 và các gates false.

**19/10/2026 — Kiểm tra nhận xét dữ liệu quý/năm của owner.**
[Report](../data/financial/cafef_quarter_row_check_v1/report.md).
11QUYCDKTrequests cho5mã;2.876cells; annual dùng pinned cache, BRCUIlive xác nhận.
Các hàng vay/quỹ BRCQ4/2025 đặt đúng nhóm hơn annual2025; VNMcũng có mẫu lệch
annual319–323. Chưa kết luận mọi quarterlyfield đúng:64arithmetic checks có4conflicts,
gồm BRCQ1/2026totalassets0, BRCQ4/2025chênh50triệu và VNMQ4/2025chênh1triệu.
Quarter/reviewedPDF có revision differences; không dịch hàng hoặc accept toàn bảng.
Không thay29metrics/gates; gap original-maturity VNM chưa đóng.

**19/10/2026 — Closing-debt continuation: PARTIAL29/30.**
[Flow](crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md),
[result](../data/financial/pilot5_completion_v1/results/ee79bf4278f3ae944d02/report.md).
Acquire1PDF mẹ VNM2.626.709bytes; note16/PDF40 xác nhận vay mẹ1–12tháng.
Closing current portion tại công ty con vẫn thiếu2024/2025. Không lấp bằng flow
phân loại lại hay số2023. Runner nhận reviewed closing-stock pair, QA components,
PDF/image pins; PowerShellrun/replay/verify và terminal cache thực chạy.
29giá trị baseline không đổi; goal30chưa đạt; financial/research/cluster gatesfalse.
46targeted tests/compile/synthetic smokePASS; full448tests447PASS/1pre-existing
M2-PREPdocs hasherror, không thay assertion hoặc frozen artifact.

**19/10/2026 — Provider/PDF validation:**
[runbook](crawl/FINANCIAL_PROVIDER_VALIDATION_USER_GUIDE.md),
[report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-vietfin-pilot5-v1/report.md).
Đã kiểm wheel VietFin0.2.0; controlled routes TCBS15/15HTTP404 và SSI1catalogHTTP403
rồi stop, chưa chạySDK và0new provider fields đượcQA. Reuse235pinned reviewed facts,
176comparisons=164MATCH/12conflicts; selected PDF references và recompute29/30
giữ nguyên. VNM F chưa rõ current portion2024/2025.0newPDF/OCR, không resetCafeF.
34targeted tests/compile/synthetic smoke/PowerShell review+verifyPASS.
Full436tests435PASS/1pre-existingM2-PREP docs hasherror; không thay assertion/evidence.

**19/10/2026 — Dọn entry scripts:** flow financial hiện tại là
[pilot5](crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md). 48 legacy entry scripts
được gói vào verified ZIP rồi gỡ khỏi `scripts/`. Đã dọn thêm 8 thư mục báo cáo cũ; tổng 5.548 file. Xem
[inventory](../artifacts/repository/current-flow-cleanup-v1/plan.json) và
[restore](README.md). Các entry có ngày cũ bên dưới là lịch sử.
Shared code/tests/config và evidence dependencies được giữ; chỉ số vẫn 29/30.
Provider/PDF validation mới nhất ở entry trên; cleanup không thay số reference.

**18/10/2026 — CafeF pilot5 thực chạy:PARTIAL_WITH_RESULTS29/30.**
[Report](../artifacts/reports/financial-cafef-pilot5-execution-v1/report-v2.md),
[runbook](crawl/FINANCIAL_CAFEF_PILOT5_USER_GUIDE.md).
BRC/FPT/MWG/GMD đủEPS/annualPE/book-snapshotPB/F/M/Z; VNM có5families,
F8/9signals interval4–5 vì closing original-long-term current portion2024/2025
chưa rõ dù đã đọc full VAS VN/EN.158unique field-periodMATCH; giáraw22/04/2026.
48attempts/38logical/3PDFattempts/7.103.375bytes/0newOCR; legacyEPSlatch nguyên.
PowerShell flow, immutable inputs/results,48targeted tests, compile/smoke,
Decimal QA/replay/resumePASS. Full421tests420PASS/1pre-existingM2-PREP hasherror.
Goal30chưa đạt; financial/research/cluster gatesfalse và cohort50baseline32/300
không đổi. Entry plan chưa execute bên dưới được giữ làm lịch sử.

**18/10/2026 — Financial pilot5 plan v2 (chưa execute):** [plan](crawl/FINANCIAL_CAFEF_PILOT5_EXECUTION_PLAN_V2.md),
[tổng hợp/handoff — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cafef-pilot5-handoff-v2/report.md).
Owner yêu cầu giao agent crawl lại vài mã tới actual metrics; chốt BRC/FPT/MWG/
GMD/VNM, annualFY2025/supporting2024/assets2023. Target5×6=30primary recomputed+
checked cells;3complete workflows chỉ checkpoint. Dedicated APIs/disclosure,
PDF/BCTNnotes, BRC row mismatch và per-group LCTT paging phải vào implementation.
Future agent thực hiện toànP0–P5, không dừng sau discovery/report/provider ratios.
Caps5mã/16PDF/400newOCR/6hnetwork, cache reuse; nguyên source/policy/gates và
old hard stops. Lượt này chỉ plan/verification,0newnetwork/OCR/metrics. Baseline
32/300references/production0 giữ nguyên; active handoff đổi từplan12 sangv2.

**18/10/2026 — BRC document deep audit:** [report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cafef-brc-deep-audit-v1/report.md),
[source cập nhật](crawl/sources/CAFEF.md). Computer-use đủ5document groups192links;
5disclosure pages92records exactURL/title/datejoins92/92. Tải6PDF/215pages, đọc
selected statement/notes,51visual candidates; đã có EPS numerator/WA, owned-PPE
DEP, capital no-change disclosure và supportingassets2023. Xác nhận annual2025
website debt sub-row mismatch1,18tỷ vsPDF24,14tỷ; cần code/label/template QA.
13scripted CDN attempts gồm6sandboxDNSfail,52.318.132successful PDFbytes;1browser
downloadtimeout giữ riêng. Owner xác nhận normal access trước UI audit; oldEPS
campaign latch không reset.0OCR/productionmetrics; strict acceptance/integration,
full history và TTM còn PARTIAL; baseline32/300/gatesfalse giữ nguyên.

**18/10/2026 — CafeF rediscovery BRC:** đã cập nhật trực tiếp
[source note](crawl/sources/CAFEF.md), [report/worklog](../artifacts/reports/financial-cafef-rediscovery-v2/report.md)
và route/field inventory. Đã khảo sát6main tabs/6financial tabs;5FinancialAjax
bodies chỉ ra CDKTv2/KQKDdetail/LCTT/ratios/plans; EPS detail UI có numerator,
weighted shares và share-days. Disclosure dates FPT/QNP LCTT dùng verified cache
lượt correction. **Live API validation PARTIAL:** scripted13attempts/1.528.364bytes,
11HTML thành công, EPS canonical gặp challenge; latch giữ true, không fetch tiếp.
12tasks chưa attempt, sector/history chưa verify.0PDF/OCR/acceptedmetrics mới;
baseline32/300referencecells và gatesfalse giữ nguyên. Bước sau: adapter/sample
validation của routes mới, không mặc định mở rộng OCR hoặc scale50/100.

**18/10/2026 — CafeF UI/API correction:** [report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-cafef-disclosure-ui-correction-v1/report.md),
[source addendum cho agent](crawl/sources/CAFEF_DISCLOSURE_AND_FINANCIAL_TABS.md).
Sau phản hồi owner, kiểm trực tiếp FPT disclosure UI/API: `CreateDate`→ngày gửi,
20records cóID/link/date; FY2025audited ID/link khớp FileBCTC cũ. QNP LCTT tab
có dedicated GetReportLCTT JSON3groups, không phải chỉ summary hoặc PDF.
Current Python crawler thiếu cả disclosure/FinancialAjax/GetReportLCTT routes.
Discovery trước chưa đủ sâu ở các routes này; nguồn có metadata/data chưa tích hợp,
không gọi chung là “không có PIT/LCTT”.5scripted requests/473.570bytes,0PDF/OCR/
metrics mới; runtime/strict PIT/gates giữ nguyên. Agent đọc addendum trướcR1 của
plan12 đã lập; original sealed plan/report giữ nguyên.

**18/10/2026 — Financial replan / handoff:** [Tổng hợp — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-replan-20261018-v1/report.md)
và [plan thực thi R0–R5](crawl/FINANCIAL_CAFEF_REVALIDATION_PLAN.md) đã viết cho agent.
Goal: audit lại CafeF trên12 mã đại diện, crawl thử, sửa parser/mapping có evidence,
tính metrics thật và giao flow PowerShell tái chạy được. Profile thực dụng cho phép
reported EPS/PE/PB, QA theo template, thiếu publication không chặn số học và named
proxies/partial outputs; strict historical PIT/research/market-only giữ riêng.
Plan JSON **PLANNED_NOT_EXECUTED**, chưa đổi runtime hoặc chạy crawl mới.
Baseline gần nhất vẫn32/300 ô reference,10/50 mã, EPS10/Z10/F6/M6, PE/PB0 trong
assessment FY2025, production0. Snapshot nguồn50 từng có84,41% wire coverage;
không đồng nhất với metric/PIT readiness hoặc kết luận nguồn đủ/thiếu toàn bộ.
Đọc prompt cuối plan để giao trọn công việc; không bắt agent dừng xin làm tiếp
sau từng checkpoint trong scope. Các entry dưới giữ nguyên lịch sử.

Financial publication follow-up09/10/2026: **DISCOVERY VERIFIED / ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-publication-followup-v1/report.md).
GMD issuer posts ghi30/03/2026(FY2025),31/03/2025(FY2024), direct attachments exact SHA2/2.
Hai dates là candidates; đề xuất evidence class mới cầnMANUAL_REVIEW_REQUIRED theoAGENTS,
runtime explicit-publication-statement chưa đổi. MWG32postrecords/VHC408PDFanchors vẫn nguyên;
không chứng minh sameURL bytes unchanged. DGC notice screenshot có access challenge, không bypass.
Campaign evidence riêng7requests/28.096.954bytes,0OCR;21tests/compile/active workflow verifyPASS.
Old counters/deadline/facts giữ nguyên; deadline09/10/2026 11:26:53UTC đã hết.
32/300referencecells,10/50mã, production0/gatesfalse; periodic refresh/TTM/PE/PB/cluster chưa mở.
Các entry dưới là lịch sử.

Financial continuation09/10/2026: **RECOVERY_REFERENCE_COMPLETE / BOUNDED_OFFLINE_HANDOFF_VERIFIED**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-continuation50-v2/report.md).
GMD2024 đã tải đúng một lần,55pages OCR97,688s; thêm TA2023 và owned-PPE depreciation2024.
GMD FY2025 F5/9/M−2,330411, EPS/Z giữ nguyên. Cohort32/300referencecells(10,67%),
10/50mã,EPS10/Z10/F6/M6/PE0/PB0; production0/gatesfalse. Successor runV2 trên
`research/financial-data`, config riêng doctorPASS;110PDF/812OCRpages/706reservations,
230transport/134PDFattempts,965.495.640downloaded bytes, deadline vẫn09/10/2026
11:26:53UTC. Owner wrapper `scripts/financial_resume.ps1` + sealed adapterV3 giải quyết
inherited result thiếu pdf_sha256 mà không rewrite pinned V2.37targeted tests,
52pins/Decimal/cache replay/verify/smokePASS. Full suite có environment failures được
recheck10testsPASS; còn pre-existing M2-PREP docs/DECISIONS hash mismatch, không full-gatePASS.
Next: exact publication/human acceptance và bounded incremental discovery5–10,
sau đó TTM/events/PE/PB/sector/history; chưa periodic unattended refresh/next100/cluster.
Các entry dưới là lịch sử.

Financial DGC/GMD09/10/2026: **REFERENCE REVIEW COMPLETE / ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-dgc-gmd-review-v1/report.md). DGC37facts cho EPS7.402/EMZ13,817568/F5/9/M−1,919528; GMD35facts cho EPS3.839/EMZ9,305095, Fnull với6/9signals và Mnull vì thiếu depreciation2024; GMD2024PDF terminal download failure giữ nguyên. FY2025 cohort30/300referencecells(10%):EPS10/Z10/F5/M5/PE0/PB0,10/50mã có reference, production0. DGC audit ngoại trừ và restatedTA2023 (CafeF còn số cũ; mechanical sensitivity F5→4) giữ explicit lineage;50providerMATCH/21NO_PROVIDER/1VINTAGE_DIFFERENCE, canonicalnull.188unique OCRpages mới;3sandboxfailed records và3successfulretry, reservations376mới/651total,757pagescache.125pins/independentDecimal/23tests/compile/fullworkflowverifyPASS,0network mới. PIT exact publication/human acceptance/TTM/sector/scale gates còn đóng. Branch `research/financial-data`, frozenV1 doctor branch mismatch chưa đổi policy. Next: bounded GMD2024 recovery và publication/human acceptance, không tự100/cluster. Các entry dưới là lịch sử.

Documentation09/10/2026: **FINANCIAL INDICATOR HANDBOOK COMPLETE**.
[Handbook](research/FINANCIAL_INDICATORS_AND_DATA_GUIDE.md), [report/self-review](../artifacts/reports/financial-indicators-handbook-v1/report.md). Đã gom6financial families, EPS/TTM/valuation variants,9Fsignals/8Mcomponents, data dictionary/nguồn/kỳ/notes/PIT/QA/code và11market features. Existing contract/source note/runbook đã có nền tảng nhưng chưa bảng tra cứu liền mạch. Ghi rõ M accruals dùngTAcuối năm trong code khác average-assets của paper; không đổi runtime/formula/inputs/gates. Documentation và synthetic arithmetic examples được kiểm offline; các entry dưới là tiến độ data trước đó.

Publication discovery MWG/VHC08/10/2026: **DISCOVERY COMPLETE / ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-mwg-vhc-publication-review-v1/report.md). MWG official PostAPI liên kết BCTC FY2025 với23/03/2026 và FY2024 với24/03/2025; distinct PDF hashes, version association chưa accepted. FY2025 images/content/geometry46/46khớp, full fingerprint45/46 vì digital signature annotation; FY2024 official higher resolution chưa all-page equivalence. VHC2/2official PDFs khớp cache, chưa publication date. Giải trình30/03/2026 chỉ document date; landing-page date không được propagate. VHC notice No85 đề09/04/2025 nhưng explicit publication10/04/2025. Signed-at proxy chỉ là đề xuất reference riêng; runtime/DATE_ONLY/inputs/counters/gates không đổi. Latest references24/300, production0. Next: exact-version publication acceptance và VHC disclosure date; chưa date-overlay/crawl100.

Financial MWG/VHC F/M review08/10/2026: **REFERENCE CALCULATION COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Report/worklog/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-mwg-vhc-fm-review-v1/report.md). Full OCR101trang FY2024 cache, bổ sung26facts/mã vào v2 riêng; MWG F4/9/M−1,417454, VHC F7/9/M−2,863853; EPS/Z không đổi. Mỗi mã có4/6groups reference; latest cohort24/300FY2025cells(8%):EPS8/Z8/F4/M4/PE0/PB0,8/50symbols có ít nhất một reference.290pins/inventories và independent18Fsignals/16Mratios/8valuesPASS;23testsPASS/compilePASS. Provider50MATCH/22NO_PROVIDER/2VHC2024 signed-expense flags, canonical null. Exact-PDF publication FY2025+support FY2024 vẫn thiếu; human acceptance pending, all gatesfalse/production0.0acquisition requests/download mới; manual primary-web discovery riêng có candidate links chưa accepted. Exact-hash extraction selector là local bounded workaround, chưa production CLI scheduling. Next: publication/human/sign-basis acceptance rồi review DGC/GMD notes từ cache; không tự wave acquisition/100. Plan năm giai đoạn/market-only giữ nguyên; các entry dưới là lịch sử stage trước.

Financial MWG/VHC template review08/10/2026: **OFFLINE REFERENCE REVIEW COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Report/worklog — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-mwg-vhc-template-review-v1/report.md). User FullOcr46MWG/64VHCpages và tạo blank templates; agent đối chiếu18ảnh, điền11facts/mã trong input riêng, chạy4EPS/Z references. Latest FY2025 assessment20/300cells (EPS8/Z8/F2/M2),8/50symbols với ít nhất một reference. EPS printed rounding2/2, balance identities2/2, provider18MATCH/4NO_PROVIDER_FIELD; independent60pins/2reviewinventories/report PASS,23testsPASS/compilePASS. Không network/OCR mới; publication exact-PDF MWG/VHC thiếu, F/M còn chưa-review/history/semantics; tất cả gates đóng. VHC EPS current-vintage có caveat quỹ phúc lợi chưa duyệt; không gọi final-revision/TTM EPS.

Financial user run inspection08/10/2026: **INTEGRITY PASS / COLLECTION PARTIAL / NO NEW NUMERICAL REFERENCES**.
[Report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-user-run50-review-v1/report.md), [runbook](crawl/FINANCIAL_READINESS_USER_GUIDE.md). User Run `data/financial/user_workflow50_v1`:150 listings,91PDF mới,109vintages;2025 cóPDF41/50mã,2024 có27/50,2023 chưa tải.44PDF failure jobs (28timeout/14live404/2known404),123pendingPDF jobs;229attempts/947,97MB,17PDFattempts còn lại. OCR4PDF DGC/GMD/64trang mới, không có review/calculation mới; baseline6mã/16ô FY2025 giữ nguyên. Acquisition routing/cache/recovery cần hoàn thiện; không sửa code/config đã frozen, không mở financial cluster.

Financial local user handoff08/10/2026: **WORKFLOW HANDOFF COMPLETE / FINANCIAL ACCEPTANCE PARTIAL**.
[Runbook](crawl/FINANCIAL_READINESS_USER_GUIDE.md), [report/tests/self-review — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-user-workflow50-v2/report.md).
Một runner PowerShell/Python: doctor/plan/audit/acquire/extract/run/template/review/verify; frozen50, FY2025 task matrix300 ô, history2023–2025. Durable network counters/access latch, OS lock, bounded OCR, immutable receipts/reports và human-attested reference calculator EPS/Z/F/M. Handoff QA không network: dùng lại cache, OCR mới16 trang MWG, replay2 PHP references; không mở cluster hoặc gọi PE annual là TTM. Bulk TTM/PB/sector adapters còn gap.

Financial scale validation08/10/2026: **MEASUREMENT COMPLETE / ACCEPTANCE PARTIAL**.
[Report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-scale-validation50-v1/report.md),
[50-symbol assessment — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-scale-validation50-v1/per-symbol.csv).
Đã kiểm50 annual listings:44 consolidated candidates,5 annual unlabeled,1 annual
listing gap.12 PDFs text-tested,11 predominantly scan/unreadable; code OCR294pages
cho4 mã mới. PHP/VCS/VEA/PAN tính8 EPS/Z references; PHP/PAN có DATE_ONLY exact-PDF
publication. Còn full F/M/TTM/PB, VCS/VEA publication, provider reconciliation,
scope/fiscal/sector layouts và unattended/resume integration.27/35 OCR statement
cells khớp visual review. Gates financial/cluster/research/next100 vẫnfalse.
Market-only và plan năm giai đoạn giữ nguyên; các đoạn dưới là kết quả stage trước.

Financial reference integration08/10/2026: **OFFLINE INTEGRATION COMPLETE / ACCEPTANCE PARTIAL**.
[Report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/cafef-financial-reviewed-integration-v1/report.md),
[config](../configs/data/financial_trial_integration_v1.json).15/900 ô annual có reference:
FPT9 ô2023–2025, ACV6 ô2025; thêm3 FPT TTM/valuation bridge values, tổng18 trong50.
VNM/PVS controls ngoài cohort. ACV có arithmetic nhưng thiếu auxiliary date-PIT và
TTM/event basis; không gọi6 metrics của ACV là production/PIT-ready. Strict0/900,
không accepted HTML facts mới, không network/PDF/OCR mới. Bước tiếp theo: review
notes/publication/vintage cho wave Regular PHP/VCS/VEA/PAN, đóng ACV/FPT gaps và
template10 mã financial-sector; chưa tự chạy wave/100 hoặc mở financial cluster.

Financial CafeF-first trial50,08/10/2026: **BOUNDED RUN COMPLETE / CANDIDATE DATA PARTIAL**.
[Report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/cafef-financial-trial50-v1/report.md),
[PowerShell active](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md). Đã thử đúng50/50 mã,
600 base +120 gap requests;588/600 base parse được,12 HTTP302 BVH giữ lỗi.
720 attempts/162.610.642 bytes,1.646/1.950 wire statement-periods (84,41%),
169.448 raw candidate cells gồm overlapping/out-of-target columns. QA reference
trong mẫu50 chỉ có FPT/ACV:29/30 matches,1 difference; không suy accuracy toàn50.
Journal/cache compact, sealed run verified;0 PDF/OCR mới,0 accepted facts và0/900
strict tasks-ready trong lượt này. Prior arithmetic reference pilot giữ lineage riêng.
Next: exact document/template QA cho gaps/units/scope/notes, publication/PIT/revisions/
share events và cost review trước100 mã. Giữ plan financial năm giai đoạn, market-only
workstream và tất cả financial/cluster/research/full-universe gates false.

Financial source review08/10/2026: **PAIRED BENCHMARK COMPLETED; SOURCE QA PARTIAL**.
[Report/log và cleanup — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-source-benchmark-v1/report.md),
[engineering selection](../configs/data/financial_source_selection_v1.json).
297 bounded attempts trên9 mã gồm6 KBS page12 diagnostics; CafeF164/186 kỳ-báo cáo
wire hiện diện, KBS98/186;78 so với213 requests MAIN. CafeF72/78 numeric reference
matches; KBS0/78 theo header,213 cross-year signature alerts không được relabel.
KBS JSON parse nhanh hơn nhưng chưa đủ QA kỳ/giá trị. CafeF cũng còn6 HTTP302 ở BVH,
16 wire gaps khác,5 numeric differences và1 unmapped cell. Reference matches không
phải PIT/production acceptance. Đề xuất CafeF-first cho flow mới; runner50 cũ chưa
đổi nguồn/tham số và không nên rerun nguyên config để giải quyết blockers này.
Next: adapter CafeF-first và gap queue, original-document QA cho units/scope/notes/
publication/revisions, rồi thử lại bounded50. Cold archives giữ exact bytes của run
cũ; active transitive reference inputs/reports và trial epoch registry còn local.
Market-only workstream và financial/cluster/research gates giữ nguyên.

Financial live trial50, 07/10/2026: **COLLECTION PARTIAL / ENGINEERING TARGETS NOT_MET**.
[Report kết quả/log — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip),
[runbook](crawl/FINANCIAL_TRIAL_50_USER_GUIDE.md). Đã thử50/50 mã,300/300 base responses
parse được;90 history responses thiếu Head. FY2025 có ba statement wire headers rõ
trên50 mã, Q4/2025 đạt0/50 vì duplicate headers.409 requests/113.538.490 bytes;
8 PDF/604 text pages,555 low-text pages,0OCR,0accepted facts,0/900 strict task-ready.
Next: đóng quý/history contract, numeric templates/ground truth, PIT/notes/events
và đo ledger/verify cost trước trial100. Market-only workstream giữ nguyên.

Lineage chuẩn bị: [implementation/testing report — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip),
[planning report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-crawl-50-plan-v1/report.md),
[plan50](../configs/data/financial_crawl_50_plan_v1.json). Reports cũ giữ nguyên trạng
thái tại thời điểm bàn giao. Financial/cluster/full-universe gates vẫn đóng.

Financial user crawler update 06/10/2026: [report/log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-crawl-user-v1/report.md),
[hướng dẫn bàn giao](crawl/FINANCIAL_CRAWLER_USER_GUIDE.md), execution plan v9.
Runner mới không cần pilot artifacts: config mẫu chạy clean4 mã với12 structured
responses/4 PDF/343 text pages/1 selected OCR page. Batch10 mã có30 structured
responses/8.720 wire cells/2.180 target2025 cells; replay32 cache hits,0 network/
text/OCR/new checkpoints và exports byte-identical. Structured quarter FPT có
duplicate period columns,654 cells bị quarantine khỏi target coverage; raw giữ nguyên.
Discovery4 mã ghi hai CafeF404 FPT/VNM, exact issuer/mirror URLs trong config bàn giao.
Crawler handoff COMPLETE ở bounded candidate collection; mới0 accepted facts,
financial/cluster/full-universe gates vẫnfalse. Market-only workstream không thay đổi.

Financial automation update 05/10/2026: [report quá trình — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-batch-flow-v1/report.md),
[runbook](crawl/README.md), execution plan v8/config batch v6. Latest run
`batch_flow_v9_final`, replay v10:10 mã có10 PDF candidates,691 embedded-text pages,
32 unique prefix OCR pages. Acquisition/extraction/checkpoint/queue/reference adapters
đã nối thành runner; resume từ run gần nhất lần theo exact external receipt/manifest.
HTTP404 DGC được ghi lại; nguồn official discovery tạo candidate riêng, không source
priority/value acceptance. Intermediate replay v6 phát hiện resume lineage bug, đã
sửa và thêm regression test. Final replay0 network/text/OCR/new checkpoints;
hai reference adapters và queue tái lập.132 financial tests/compile/smoke PASS;
full301/302 PASS với frozen M2-PREP DECISIONS checksum error cũ.
Sáu mã mới chưa có numeric facts được nghiệm thu; four-symbol calculation coverage
giữ nguyên. OCR prefix không bao phủ thuyết minh. Engineering COMPLETE ở10 mã;
FIN-D5 acceptance/financial/research/full-universe gates vẫn pending/false.
Next: pilot semantic/PIT/TTM/event closure, ground-truth template parsers và batch
20–30 với acceptance/cost thresholds được review trước khi mở accepted-data scale.

Financial update 05/10/2026: [pilot ba mã/report và log — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-three-symbol-pilot-v1/report.md).
Latest `three_symbol_pilot_v3`/replay v4, execution plan v7. Có 158 annual facts được
visual review riêng; không cộng trực tiếp vào matrix v12. VNM/PVS/ACV có 5/6/6 annual
reference families với arithmetic. F VAS PVS=7, ACV=4; VNM 8/9 known signals, total null.
Ba mã có M sensitivity/Z/EPS annual; P/E/P/B dùng raw close 28/08 và annual 2025 snapshot,
không current TTM/book equity. VNM thêm reported TTM EPS≈4.727,57, P/E≈13,18;
annual và interim publication là mirrored-exchange DATE_ONLY, primary vẫn pending.
PVS H1 parent profit/bonus-share restatement chưa có FY bridge; ACV reviewed H1 công bố
03/09 là future tại cutoff 28/08, bản Q2 unaudited đã tải nhưng EPS scope chưa nghiệm thu.
Auxiliary publication dates VNM/ACV còn thiếu. Quotes VNM/PVS lưu riêng dưới financial,
không sửa canonical market/M2. FIN-D4 annual reference slice hoàn thành, acceptance PARTIAL;
FIN-D5 pending. Strict tasks 0/120; financial/research/full-universe gates false.

Financial update 04/10/2026: [FPT acceptance/ESOP report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-fpt-acceptance-v2/report.md).
Latest acceptance_v5, equity_review_v1 và execution plan v6: sáu metric families có
reference values từ 24/08/2026. F/M/Z dùng annual 2025; EPS/PE dùng TTM đến 30/06/2026;
P/B là latest June equity + verified gross ESOP capital increment, không current net equity.
Bank proceeds = registered capital increase = 108.193.010.000 VND; registration effective
16/07, công bố 17/07. Tại 28/08, gross-capital P/B ≈ 3,1404; previous reported-equity
P/B ≈ 3,1489 giữ riêng. Phí, cash classification và subsequent movements chưa đủ evidence.
FPT reference handoff complete; FIN-D4 four-symbol closure vẫn PARTIAL, FIN-D5 pending.
Không tăng readiness 153/1.176/date 138/task 0/120 hoặc mở financial/research/scale gates.
Các update bên dưới là lineage, không phải latest blockers đã được giải quyết.

Financial update 04/10/2026: [FPT TTM/share-event report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-ttm-valuation-v1/report.md).
Latest supplemental slice: `fpt_ttm_valuation_v3`, execution plan v5.
14 issuer PDFs mới, 50 selected OCR pages; 6 accounting QA và 13 artifact checks PASS.
Reported-numerator/share-days TTM EPS ≈ 5.570,36 từ 24/08/2026; P/E/P/B reference
28/08 ≈ 13,14/3,15. P/B dùng current common count 1.714.326.422 và latest reported
parent equity 39.851.463.524.930 VND tại 30/06; chưa event-adjusted equity.
FTEL bridge chỉ đủ parent earnings; total-NI/revenue bridge chưa approved.
Interim reserve và historical issuance-date basis giữ blockers; strict normalized
TTM/event-adjusted P/B null. FIN-D4 PARTIAL_REFERENCE_TTM, FIN-D5 pending.
Readiness 153/date 138/task 0/120 không tăng vì slice riêng. Market-only protocol
và financial/research/scale gates giữ nguyên. Phần dưới là lineage các đợt trước.

Financial update 03/10/2026: [source research/VAS report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-source-research-v1/report.md).
`source_completion_v5` là latest financial handoff. KBS trả15 JSON trên bốn mã;
4.796 wire cells chưa accepted. Thêm17 annual observations và13 H1 facts riêng;
readiness v12 đạt 153/1.176, date v6 có 138 date references; strict task v8 vẫn 0/120.
Hai transcription errors CFO/noncurrent debt 2024 đã có exact-PDF correction.
FPT2021–25 F-score VAS=4/6/6/7/3; strict F vẫn sáu known signals/totalnull.
M2024/25 có eight-ratio sensitivity, strictnull. Reported P/E/P/B20/03/2026≈14,30/3,48,
event coverage pending. H12026 EPS2.967 khả dụng24/08/2026; FTEL scope/reserve/share
bridge chặn latest TTM. EPS/Z flowv9 giữ revision handling. Các phần dưới là lineage
từng đợt. FIN-D2/3/4 PARTIAL, FIN-D5 pending; financial/research gates vẫnfalse.

## Cập nhật 2026-10-23 — Commit/push dashboard theo yêu cầu owner

Owner yêu cầu commit/push phần dashboard và handoff cần thiết trên branch
`m2-clustering-experiment`. Phạm vi 14 files: app/theme/test, dependency,
Git attributes, README/docs/changelog và 4 files handoff hiện hành. Không
đưa C8 gửi riêng, `.venv`, các legacy deletions/archive, notebook/report M2
hoặc thư mục models chưa tracked ngoài phạm vi dashboard vào commit.

Pre-commit validation: 22/22 dashboard tests PASS; full gate chạy 272 tests,
271 PASS và 1 ERROR do thiếu immutable Financial PIT evidence
`artifacts/financial_pit/fin-pit-1a-20261004T015420Z-continuation-preflight-v2/next_network_proposal.json`.
Đây là blocker cũ đã ghi nhận, không sửa test hoặc tạo evidence thay thế.
Compileall, `node --check web/app.js`, staged diff check PASS. Staged CSV bytes
khớp working copy và cả 3 hashes trong staged manifest; C8/venv không staged.
Self-review: dashboard scope PASS, toàn repository gate PARTIAL vì thiếu
Financial PIT evidence. Remote trước commit `6aadc1d0`, local `6a78a626`,
ahead 2 / behind 0; push thông thường, không force hoặc sửa lịch sử.

## Cập nhật 2026-10-23 — Bàn giao dashboard qua Git, dữ liệu gửi riêng

Owner xác nhận gửi riêng ba file C8 (`manifest.json`,
`canonical/feature_snapshots.jsonl`, `canonical/securities.jsonl`) dưới
`artifacts/cafef_primary/cafef-c8-complete-only-v2/`. Các file tiếp tục bị
ignore; không upload hoặc thay nội dung. Hướng dẫn cài đặt/chạy/verify offline
được đặt ngay START HERE tại [docs README](README.md); root README có link.

Thêm `.gitattributes -text` cho handoff hiện hành để bảo toàn checksum trên
Windows/Linux; pin pandas 2.3.3 cùng Streamlit 1.66.1 trong extra dashboard.
Người chia sẻ vẫn cần add/commit các file code/theme/config/docs và bộ handoff
hiện hành trước khi push. Phiên này không stage/commit/push hoặc sửa legacy
deletions ngoài phạm vi.

Validation/self-review: **PASS** — 22/22 dashboard tests; compileall; config
TOML parse; scoped diff check. Git clean filter với `core.autocrlf` lần lượt
true/false/input đều giữ đúng blob bytes của labels/profiles, hashes nguồn
khớp manifest. Không đổi runtime/model/data. Chưa thử clone/install mới trên
máy người nhận; hướng dẫn yêu cầu bộ C8 đúng lineage, không dùng bộ cũ 2026.

## Cập nhật 2026-10-23 — Cố định trục thanh khoản/beta, bỏ Stock Detail

Theo yêu cầu owner, mọi snapshot dùng X=`liquidity_21`, Y=`beta_126`. X symlog
với constant cố định 1.000.000.000 VND, Y tuyến tính; không chọn trục bằng
correlation hoặc thay theo từng snapshot. X lấy raw VND từ ticker JSONL, chỉ
nhãn trục quy đổi tỷ VND/phiên; tooltip giữ VND gốc. Giá trị zero giữ nguyên,
không epsilon/zero-fill/clipping. Missing đúng một trong hai tọa độ được báo
rõ, không dùng feature momentum cũ để quyết định row có được vẽ hay không.

Lựa chọn mô tả từ 168 monthly cluster profiles/84 snapshot: Cluster 0 có
liquidity và beta cao hơn Cluster 1 ở 84/84 tháng (60/60 development, 24/24
holdout). Median profile liquidity 307,46 tỷ so với 5,18 tỷ VND/phiên; beta
1,244 so với 0,383. Đây là mô tả profile, không phải feature importance hoặc
khẳng định mọi ticker của hai nhóm tách hoàn toàn trong 2D.

Đã bỏ phần chọn Chế độ xem và toàn bộ renderer Chi tiết cổ phiếu. Người dùng
xem ticker features trong bảng thành viên có tìm kiếm/phân trang; helper query
offline được giữ để bảo toàn source-consistency assertions. Các tests UI cũ
được migrate sang member table, bao gồm đủ 8 features và trạng thái MISSING.
Ô tìm kiếm có viền 1px cùng focus ring xanh. Lệnh chạy app giữ nguyên.

Validation: **22/22 targeted dashboard tests PASS**, bao gồm UI tại development
và holdout, cặp trục cố định, giữ zero thật, đủ 8 ticker features và các trạng
thái missing. `compileall` và `node --check web/app.js` PASS. Browser QA xác
nhận trục liquidity/beta, viền ô tìm kiếm và không còn Chế độ xem/Chi tiết cổ
phiếu. Source artifacts không thay đổi; không rerun full suite cho thay đổi UI
này (blocker evidence Financial PIT cũ đã ghi ở phần validation trước).

Self-review M3-B: **PASS** — chỉ đổi presentation/read-only queries; không có
fit/predict, network hoặc ghi artifact trong dashboard. SHA-256 labels và
profiles khớp trạng thái trước sửa. Git trước/sau: local `6a78a626`, remote
branch `m2-clustering-experiment` `6aadc1d0`, ahead 2 / behind 0; giữ nguyên
11 modified, 15 deleted và 6 untracked entries đã có. Không commit/push và
không xử lý các legacy deletions ngoài phạm vi.

## Cập nhật 2026-10-23 — Thiết kế lại giao diện M3-B theo ảnh owner

Giữ entry point `m3_dashboard.py`, bố cục bộ lọc trái / nội dung Market phải,
nền sáng và các panel bo góc. Bốn thẻ tổng quan lấy trực tiếp size/profile của
snapshot đang chọn. Biểu đồ scatter dùng `mom_252` và `mom_63` từ từng ticker,
màu theo assignments M2; giữ toàn bộ outliers, không tạo PCA/projection/model mới.
Các đám điểm không được ép giống tọa độ minh họa trong ảnh owner.

Tên hiển thị thay cho Cụm + số: **Dẫn đầu thanh khoản** là nhóm có liquidity_21
profile cao hơn; **Đại trà** là nhóm còn lại khi có nhiều thành viên hơn. Thiếu
hoặc bằng liquidity thì dùng Nhóm A/B; nếu nhóm còn lại không lớn hơn thì dùng
Thanh khoản thấp hơn. Quy tắc chỉ mô tả snapshot, không đổi label/membership,
không phải M3-A ranking hoặc khuyến nghị. Raw labels vẫn có trong provenance.
Audit cả 84 snapshot hiện hành xác nhận nhóm có liquidity cao hơn nhỏ hơn về size.

Bảng members có ticker, tên công ty, đủ 8 ticker features, tìm theo ticker/tên,
phân trang và chọn 10/25/50/100 rows. Company names đọc bằng unique security_id
từ `canonical/securities.jsonl`: 1.522 rows, checksum khớp C8 manifest; chỉ là tên
tham chiếu, không nâng historical identity/PIT. Null giữ MISSING. Số thực trong
bảng được định dạng để dễ đọc; Stock Detail giữ precision nguồn.

`.streamlit/config.toml` đặt light theme cho native controls/canvas; cần restart
Streamlit nếu đang chạy trước khi thêm theme. Không thêm dependency hoặc frontend
riêng. Lệnh chạy giữ nguyên: `.\.venv\Scripts\python.exe -m streamlit run .\m3_dashboard.py`.
Kiểm tra UI mới: đổi ngày, chọn từng tên nhóm, tìm FPT, đổi page size, chuyển trang
và so sánh feature/member count với nguồn. Bộ targeted mở rộng có 21 tests PASS;
giữ/migrate toàn bộ assertions cũ khi thay layout/column names, thêm kiểm tra tên
theo profile, raw scatter values, tìm kiếm và phân trang. Full-suite blocker
Financial ở ghi chú stage trước không thuộc thay đổi UI này.

Browser visual QA PASS ở desktop theo ảnh mẫu với light theme: snapshot
2025-12-31 có 1.410 mã, Dẫn đầu thanh khoản 26 và Đại trà 1.384. Thử chuyển nhóm,
next page (11–20 / 1.384, trang 2/139), tìm AAA (1/1) và reset search đều đúng.
Ảnh giao diện thật lưu local tại `tmp/m3_dashboard_redesign.jpg`; không phải mockup.

## Cập nhật 2026-10-23 — M3-B Market-only Streamlit

Entry point duy nhất: [`m3_dashboard.py`](../m3_dashboard.py), visualization
read-only trên `m2-final-handoff-v1`, manifest version 2.0.0. Tên thư mục không
đồng nghĩa bộ legacy 22 snapshot. Dashboard không sửa artifacts, gọi model,
tính lại features/clustering hoặc nâng historical identity/research readiness.
Bộ dữ liệu đến tháng 08/2026 là legacy và không được đọc trong M3-B hiện hành.

### Data contract

- Labels: 75.801 rows, gồm 45.646 development + 30.155 holdout.
- Profiles: 168 monthly + 6 summary rows. `MEDIAN_DEVELOPMENT_60M`,
  `MEDIAN_HOLDOUT_24M`, `MEDIAN_OVERALL_84M` được giữ trong source, không phải
  decision dates và không dùng thay monthly profile.
- Feature source: 179.880 rows / 120 snapshot, 2016-01-29–2025-12-31.
- Selector: đúng 84 manifest dates; 60 development 2019-01-31–2023-12-29 và
  24 holdout 2024-01-31–2025-12-31. Không tạo cluster cho 2016–2018 hoặc nội suy
  ngày/gap. Không áp systemic gap của bộ legacy lên bộ hiện hành.
- Join one-to-one: labels `(snapshot_date, security_id)` bằng features
  `(as_of_date, security_id)`. Không duplicate key, ticker ambiguity/mismatch.
  Cả 75.801 assignments có feature row và đủ 8 numeric finite values.
- Có 104.079 feature-only rows trên toàn file, gồm 50.115 ở các ngày M2. Source
  rộng hơn membership; không thêm các row này vào cluster universe. Audit trước
  implementation xác nhận không bỏ sót market-ready row tại 84 ngày M2.
- Labels khớp aligned assignments gốc, profiles khớp số liệu/member counts nguồn;
  ba handoff CSV cùng 84 model hashes/mirrors đã được kiểm tra. Feature hash
  `ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e` khớp
  C8/development/holdout hiện hành. Sai khác hash của bộ cũ đã được giải quyết.

Schema labels:
`snapshot_date, security_id, ticker, cluster_label, membership_period`.

Schema profiles:
`snapshot_date, cluster_label, size, size_ratio, membership_period, mom_21,
mom_63, mom_126, mom_252, vol_63, mdd_126, beta_126, liquidity_21`.

<details>
<summary>Exact schema 34 fields của feature JSONL</summary>

```text
adjustment_basis, as_of_date, available_at, beta_126, canonical_run_id,
data_mode, data_version, downside_vol_63, eligibility, feature_complete,
feature_version, historical_identity_ready, history_calendar_days,
history_observations, history_start_date, liquidity_21, listing_age_days,
lookback_observations, market_feature_ready, mdd_126, missing_count,
mom_126, mom_21, mom_252, mom_63, na_reason, ram_63, research_ready,
security_id, ticker, universe_segment, vendor_run_id, vol_126, vol_63
```

Dashboard chỉ chọn ngày, identity và 8 Market features; không triển khai logic
availability hoặc Financial từ các field khác đã có trong source JSONL.

</details>

### Chạy trên Windows

1. Mở PowerShell:

   ```powershell
   cd <thư-mục-gốc-dự-án>
   ```

2. Dùng Python >=3.11. Tạo virtualenv nếu chưa có, cài extra `dashboard` của
   project (Streamlit pin 1.66.1). Phiên implementation đã cài extra vào `.venv`:

   ```powershell
   if (!(Test-Path ".venv\Scripts\python.exe")) { python -m venv .venv }
   .\.venv\Scripts\python.exe -m pip install -e ".[dashboard]"
   .\.venv\Scripts\python.exe -m streamlit --version
   ```

3. Khởi chạy:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run .\m3_dashboard.py
   ```

4. Mở [http://localhost:8501](http://localhost:8501). Lần đầu cần đọc/xác minh
   source 234 MB. Đổi selectors dùng cache in-memory. **Đọc lại dữ liệu** xóa
   cache dashboard và reset date/ticker. Cache tự invalidate theo size/mtime/ctime
   source hoặc code; loader offline không cache. Đọc khi source đang đổi sẽ bị chặn.
5. Dừng bằng **Ctrl+C** ở PowerShell.

Nếu lỗi môi trường, kiểm tra `Get-Location`, `Test-Path .\m3_dashboard.py`,
`.\.venv\Scripts\python.exe --version` và Streamlit version trước khi sửa code.
Không thay methodology để xử lý environment error.

### Checklist kiểm tra thủ công

- **Overview:** chọn `2019-01-31`. Dẫn đầu thanh khoản (source label 0): 12 members,
  size_ratio `0.0182926829268292`; Đại trà (source label 1): 644 members,
  size_ratio `0.9817073170731708`.
  Mở hai member lists. Bảng 8 features phải có nhãn **CLUSTER PROFILE**.
- **Holdout:** đổi sang `2025-12-31`. Dẫn đầu thanh khoản: 26 members; Đại trà: 1.384;
  tổng 1.410. Selector chỉ có 84 ngày M2, không có năm 2026.
- **Stock Detail/date change:** chọn FPT, `2025-12-31`: security_id
  `KBS:HOSE:FPT`, Dẫn đầu thanh khoản (source label 0), giai đoạn `holdout`, đủ 8 features.
  Đổi sang `2019-01-31`: FPT thuộc Đại trà (source label 1), features đổi theo snapshot.
- **Missing/error:** không sửa source thật để thử lỗi. Tests bên dưới dùng
  fixture tạm cho unknown ticker/date, missing cluster/feature row, null,
  malformed session state và tamper. UI hiện trạng thái rõ, không crash/zero-fill.
- **Provenance/reset:** mở Data source / snapshot / version để xem nguồn,
  version, audit counts; thử nút Đọc lại dữ liệu.
- **Source comparison:** từ repository root chạy:

  ```powershell
  Import-Csv ".\M2\artifacts\m2-final-handoff-v1\m2_cluster_labels_for_m3.csv" |
      Where-Object { $_.ticker -eq "FPT" -and $_.snapshot_date -eq "2025-12-31" }

  Get-Content ".\artifacts\cafef_primary\cafef-c8-complete-only-v2\canonical\feature_snapshots.jsonl" |
      Select-Object -Skip 50519 -First 1 |
      ConvertFrom-Json |
      Select-Object as_of_date, security_id, ticker, mom_21, mom_63, mom_126, mom_252, vol_63, mdd_126, beta_126, liquidity_21
  ```

  Labels row ở dòng 74801 (tính cả header), feature row ở dòng 50520 của source
  hiện hành. Kiểm tra ngày/identity của row vừa mở trước khi so sánh:

  | Feature | FPT, 2025-12-31 |
  |---|---:|
  | mom_21 | -0.008281367081487079 |
  | mom_63 | 0.03637059556397837 |
  | mom_126 | -0.09133035242078935 |
  | mom_252 | -0.25055833135062255 |
  | vol_63 | 0.31045166899069365 |
  | mdd_126 | -0.2239070145700931 |
  | beta_126 | 0.5259396975653587 |
  | liquidity_21 | 564969927952.381 |

### Kiểm thử M3-B và giới hạn

18 targeted tests PASS, gồm AppTest với dữ liệu thật/fixture: import/load,
schema/hash/lineage, uniqueness/many-to-many, official selector, Overview
development/holdout, ticker feature equality, missing/malformed states, cache
invalidation và reset. Server Streamlit startup PASS ở port thử 8517:
`HTTP 200 /_stcore/health = ok`; đã dừng sau kiểm tra. Không có browser visual QA;
dùng checklist trên để demo trên trình duyệt thật.

Full repository gate chạy 268 tests: 262 PASS, 6 errors ở Financial continuation.
Năm errors do thiếu thư mục tạm `.tmp`; sau tạo thư mục môi trường và rerun nhóm
11 tests, 10 PASS và còn một error do thiếu immutable evidence
`artifacts/financial_pit/fin-pit-1a-20261004T015420Z-continuation-preflight-v2/next_network_proposal.json`.
Vì vậy full gate chưa PASS; không sửa/xóa assertion hoặc dựng evidence thay thế.
Lỗi này nằm ngoài đường đọc M3-B. Log full run: `tmp/m3_full_suite.log` (local,
ignored). Compile, TOML/JSON parse và Markdown links mới PASS. Diff check trên
files của task PASS; global diff còn CRLF/trailing whitespace trong handoff và
báo cáo đã được owner cập nhật trước task, giữ nguyên byte/hash của các file đó.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_m3_dashboard.py" -v
.\.venv\Scripts\python.exe -m compileall -q src tests scripts run.py m3_dashboard.py
```

Sandbox của phiên này chặn Windows asyncio/socketpair loopback; AppTest/server
PASS ngoài sandbox. Đây là environment limitation, không đổi code/methodology.
Handoff chưa pin trực tiếp feature path/hash; dashboard verify qua manifests
C8/development/holdout. Model là reference only, dashboard không load model files.
Transition Screen và kiến trúc backend/frontend riêng không thuộc stage này.

**FINANCIAL NOT IMPLEMENTED YET.** Dừng ở M3-B Market-only; next step là owner
chạy manual checklist, không tự mở Financial/M3-A/backtest.

## Hiện tại 2026-10-22 — Nhiệm vụ 11 hoàn tất trên dữ liệu mới, báo cáo đầy đủ

Người dùng đã chạy xong notebook `11_final_holdout_execution.ipynb`. Bộ
`M2/artifacts/m2-final-holdout/` ghi complete: 24/24 tháng 2024–2025, không
skip, 30.155 assignments, 48 profiles, 24 model và 23 cặp thời gian nội bộ.
Chỉ KMeans Baseline/sklearn/K=2; quyết định đóng băng lúc 12:57:06, mở holdout
15:49:06 và hoàn tất 15:50:31 ngày 22/10/2026 (UTC+7).

Nguồn C8 feature SHA-256
`ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`
khớp lineage Task 10. Median Silhouette holdout 0,949324 so với development
0,940837 (delta +0,008487); ARI median 0,843260, Persistence 99,370574%,
Migration 0,629426%. Giữ cảnh báo 24/24 tháng Balance <0,05, cụm nhỏ 22–41 mã;
khoảng cách tâm cụm chủ yếu theo thanh khoản, không suy hiệu quả đầu tư.

[Báo cáo Nhiệm vụ 11](../M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md)
được mở rộng theo mẫu A/B/C với bảng 24 tháng, so sánh Dev/Holdout, biểu đồ
84 mốc, temporal/universe, hồ sơ mean/median và giới hạn diễn giải. Bản xuất
tự động gốc giữ tại `report_auto.md` trong artifact để đối chiếu provenance.
Chỉ cập nhật report/checksum và metadata revision; model, numerical outputs,
input, code và timestamps thực nghiệm giữ nguyên. Rerun bộ complete chỉ verify
và nạp artifacts, không refit. Nhiệm vụ 12/M3 chưa thực hiện trong lần này;
audit/generator 12–13 lịch sử cần context riêng. Các mục dưới đây là lịch sử.

## Lịch sử 2026-10-22 — Chuẩn bị nhiệm vụ 11 trên dữ liệu mới, chưa chạy holdout

Người dùng yêu cầu hướng dẫn chạy nhiệm vụ 11 sau khi đồng bộ Git và giải nén
lại dữ liệu mới. Tạo notebook `11_final_holdout_execution.ipynb`, config
`m2_final_holdout.json`, module `final_holdout.py` và các kiểm thử bằng fixture.
Không khôi phục số liệu/model/outputs holdout cũ, không tạo tên có hậu tố.

Quyết định Task 10 hiện hành: FROZEN_FOR_HOLDOUT, KMeans Baseline/sklearn/K=2,
timestamp `2026-10-22T05:57:06+00:00`, nguồn C8 feature SHA-256
`ab1a34a83857e78e304dbeea85f05fd3e1fd1f7d93ed89bbcee4731646da740e`.
Config mới chỉ được tạo khi chưa có đầu ra; pin đúng chín development inputs
hiện tại, không tái gán hash cho bất kỳ evidence holdout cũ nào. Chín hash khớp
Git bytes. Preflight kiểm chứng 60 model và 70 input refs mà không đọc feature
holdout. Giữ nguyên 60 tháng development / 24 tháng holdout, threshold 100,
seed 42/n_init 10/max_iter 300, Robust Scaling per snapshot, không retune.

Người dùng chạy Bước 2 trong notebook để thực thi holdout thật. Các bước 3–7
hiển thị và kiểm chứng outputs; không fit thêm. Bộ complete chỉ được verify
khi chạy lại; run dở hoặc checksum đổi bị chặn. Kết quả sẽ nằm ở
`M2/artifacts/m2-final-holdout/`, models `M2/models/holdout/`, báo cáo
`M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`. Hiện chưa có các đầu ra đó.
Audit 12 và generator bàn giao 13 lịch sử vẫn phải dùng context riêng, không
tự động tiếp tục sau nhiệm vụ 11. Các mục trước bên dưới là lịch sử.


## Hiện tại 2026-10-22 — Tên chuẩn PCA + K-Means và xóa toàn bộ nhiệm vụ 11

Theo yêu cầu mới nhất, giữ bộ PCA + K-Means 6–9 đã khôi phục từ Git và đổi tên
không có hậu tố phiên bản: notebook `06_pca_kmeans.ipynb`, các notebook 07–09
`*_pca_kmeans.ipynb`, config `m2_pca_market_only.json`, artifacts
`m2-task6-pca-kmeans/`, freeze `m2-task6-pca-freeze/`, đánh giá
`m2-evaluation-pca-kmeans/`, bốn báo cáo `*PCA_KMeans.md`. Models vẫn ở
`M2/models/pca_kmeans/`. Kế hoạch và notebook 10 dùng các đường dẫn này.

Đã cập nhật metadata đường dẫn và checksum theo thứ tự phụ thuộc; sửa ba hash
báo cáo 7–9 không khớp manifest đã phát hiện ở lần kiểm tra trước. Manifest nhiệm
vụ 6 ghi `storage_migration` và hash manifest trước đổi tên. Các file khoa học và source snapshot PCA giữ nguyên bytes; toàn bộ payload số của 120 bản model PCA
(60 bản trong artifacts và 60 bản mirror) giữ nguyên. Không fit lại hoặc dùng
holdout. Bộ PCA vẫn complete, 60 tháng, 45.646 assignments, K=2, PCA 2 chiều.

Yêu cầu xóa nhiệm vụ 11 đến sau yêu cầu đổi tên/thay thế: đã xóa toàn bộ bản cũ,
bản mới và các file trung gian vừa chuyển tên của Task 11, bao gồm notebook,
config, implementation/helpers, kiểm thử riêng, artifacts/model/report. Không
backup. Task 12/13 giữ lại như lịch sử; script dừng trước mutation do thiếu
đầu vào Task 11. Nguồn C8 mới và kết quả riêng K-Means/Ward/Task 10 giữ nguyên.

Các mục bên dưới là ghi chú tại thời điểm trước, không thay đổi yêu cầu hiện tại.
Phạm vi đồng bộ GitHub: đổi tên PCA 6–9, sửa checksum báo cáo và xóa Task 11 theo yêu cầu owner.


## Cập nhật 2026-10-22 — Nhiệm vụ 11 V2 hoàn tất và có báo cáo đầy đủ

Holdout thật đã chạy xong: KMeans Baseline/sklearn/K=2 trên 24/24 tháng
2024–2025, không skip; 28.110 assignments, 48 profiles, 24 model và 23 cặp
tháng nội bộ. Manifest `m2-final-holdout` ghi `complete`; freeze timestamp
đứng trước lúc mở holdout. Không chạy Ward/PCA hoặc retune bằng kết quả ngoài mẫu.

Median Silhouette 0,945927 so với development 0,931935 (delta +0,013992);
ARI median 0,849616, Persistence 99,358974%, Migration 0,641026%. Vẫn giữ
cảnh báo 24/24 tháng Balance <0,05, cụm nhỏ 22–41 mã; không suy hiệu quả đầu tư.

Báo cáo Nhiệm vụ 11 V2 (`../M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`, đã xóa nhiệm vụ 11)
đã được viết đầy đủ theo bố cục A/B/C của mẫu cũ, kèm bảng, biểu đồ 84 mốc và
biện luận từ số liệu thực tế. Bản tự động gốc được giữ tại `report_auto.md`
trong artifact; chỉ cập nhật report/checksum và metadata ghi nhận sửa báo cáo.
Numerical artifacts, model, input, source code và quyết định Task 10 không đổi.
Rerun xác minh/nạp lại bộ complete, không refit; Task 12/M3 chưa thực hiện ở đây.

## Cập nhật 2026-10-22 — Nhiệm vụ 11 V2 đã chuẩn bị, chưa mở holdout thật

Đã chuẩn bị `11_final_holdout_execution.ipynb`, config
`m2_final_holdout.json` và runner `experiments/final_holdout.py` theo kế hoạch:
60 development/24 holdout 2024–2025, universe tối thiểu 100 mã theo tháng,
chỉ KMeans Baseline/sklearn/K=2 từ quyết định Task 10 V2, giữ seed=42,
n_init=10, max_iter=300, Robust Scaling độc lập; không chạy comparator/quét K.

Gate đã kiểm chứng 60 model và development inputs; chưa đọc feature holdout.
Đã khôi phục đúng LF của selected-model exports để khớp byte hash đã freeze,
thêm Git attributes bảo toàn định dạng và pin development inputs theo Git bytes.
JSON/CSV values và quyết định Task 10 không đổi. Bộ legacy V1 và source runner
legacy giữ nguyên. Đầu ra V2, model `holdout` và báo cáo V2 chưa được tạo.

Notebook trình bày đúng bảy bước. Bước 2 do người dùng thực hiện mới mở holdout;
run complete được verify-only khi chạy lại. Run dở/failed hoặc checksum đổi
phải dừng và giữ evidence. Test dùng fixture giả riêng, không fit dữ liệu thật.

## Cập nhật 2026-10-22 — Báo cáo PCA V2 đầy đủ và đồng bộ Git

Theo yêu cầu owner, bốn báo cáo chính Nhiệm vụ 6–9 PCA + K-Means tên hậu tố
`_v2.md` trong `M2/reports/` đã được thay bằng bản đầy đủ có bố cục A/B/C,
bảng chi tiết và biểu đồ. Không giữ bản trùng `_v2_day_du.md` trong active tree;
các bản trước vẫn có trong Git history. Đường dẫn tại [START HERE](README.md).

Checksum báo cáo trong manifest Task 6–9 cùng tham chiếu metadata phụ thuộc
được cập nhật. Model, scaler/PCA, CSV/JSONL, biểu đồ, source snapshot và toàn bộ
kết quả/quyết định Task 10 giữ nguyên. Notebook đánh giá 7–9 kiểm tra checksum
báo cáo đầy đủ trước khi tái sử dụng, không ghi đè bằng phần tóm tắt tự động.

Đã lấy hai commit `2d8ac27` và `3caf7c9` từ Git: KMeans 4/7/8/9 đã làm lại và
Task 10 V2 đã chọn **KMeans_Baseline, K=2**, trạng thái `FROZEN_FOR_HOLDOUT`;
PCA và Ward là comparator. Các báo cáo mới phản ánh trạng thái này, không
thực thi lại Task 10 hoặc mở holdout V2. Các ghi chú cũ bên dưới giữ bối cảnh
tại thời điểm được viết.

## Cập nhật 2026-10-21 — nhánh K-Means M2 trên C8 v2

Nhiệm vụ 4, 7, 8 và 9 của **K-Means** đã chạy lại trên 60 development snapshot 2019–2023 từ `cafef-c8-complete-only-v2`; Global K=2 giữ theo quyết định Nhiệm vụ 3. Nhiệm vụ 4 fit lại bằng scikit-learn, có 29.907 assignments, 120 profiles, 60 model/scaler. Output active đúng tên kế hoạch ở `M2/artifacts/m2-task4-kmeans-baseline-v1/` và `M2/models/kmeans/`.

Nhiệm vụ 7 xuất `M2/artifacts/m2-evaluation-kmeans/quality_summary.csv` từ 60 diagnostics; median Silhouette 0,931935, Davies-Bouldin 0,396416, balance 0,023814. Nhiệm vụ 9 đọc 59 cặp tháng, xuất 236 transitions và 944 feature drift rows; median ARI 0,768741, NMI 0,624996, persistence 98,9313%, migration 1,0687%. Bốn báo cáo đúng tên trong `M2/reports/`; đã đối chiếu offline schema, checksum, metrics và biểu đồ. Các chỉ số này chỉ phản ánh cluster quality và temporal stability, không phải portfolio performance.

Nhiệm vụ 8 K-Means hiển thị 3 bảng (4×10, 9×4, 60×5) trong notebook và xuất radar, heatmap, báo cáo từ 60 snapshot mới; đã đối chiếu offline bảng với nguồn và scaler. Artifact K-Means dùng tiếp gồm `cluster_profiles.csv` 120 dòng, `cluster_profile_members.csv` 29.907 dòng và `profile_scaler_reference.csv` 960 dòng ở `M2/artifacts/m2-evaluation-kmeans/`, được đồng bộ từ Task 4. Manifest Task 4 có hash nguồn C8; 18 file giải nén khớp ZIP trong Downloads. ZIP không gồm hai output lớn mà C8 manifest liệt kê (`canonical/normalized_expansion.jsonl`, `canonical/prices_daily.jsonl`); K-Means dùng feature snapshots có hash hợp lệ. Không sửa Nhiệm vụ 1–3 hoặc nhánh Ward/PCA. So sánh ba model/holdout không thuộc lần chạy này.

Gate: targeted clustering/runner/protocol 29 tests PASS, synthetic smoke PASS, compile PASS và offline checks K-Means Task 4/7/8/9 PASS. Full repository suite chạy 234 tests, còn 5 errors ở holdout/ingestion evidence ngoài nhánh K-Means; không sửa các nhánh đó trong lần chạy này.


## Cập nhật 2026-10-21 — PCA V2 thay bộ cũ trong active Git tree

Nhiệm vụ 6–9 PCA + K-Means với dữ liệu mới đã hoàn tất: 60 tháng development
2019-01-31–2023-12-29, 29.907 assignments, Global K=2 và PCA 2 chiều. Các mục
ngày trước bên dưới là lịch sử, không phải kết quả tái xác nhận cho bộ V2.

- Notebook active: `06_pca_kmeans.ipynb`,
  `07_cluster_quality_evaluation_pca_kmeans.ipynb`,
  `08_cluster_profiling_pca_kmeans.ipynb`,
  `09_temporal_stability_pca_kmeans.ipynb` trong `M2/notebooks/`.
- Artifact: `M2/artifacts/m2-task6-pca-freeze/`,
  `M2/artifacts/m2-task6-pca-kmeans/`,
  `M2/artifacts/m2-evaluation-pca-kmeans/`; 60 model mới trong
  `M2/models/pca_kmeans/`, config `configs/experiments/m2_pca_market_only.json`.
- Theo yêu cầu owner, xóa bộ PCA cũ 15 tháng khỏi active tree: bốn notebook
  không có hậu tố V2, config `m2_task6_pca.json`, artifact
  `m2-task6-pca-kmeans-v1` và `m2-evaluation-pca-kmeans`. Git history là archive.
  Backend PCA/K-Means và các phương án khác vẫn được giữ.
- Task 9 đã chạy chính thức: manifest `complete`, đủ 59 cặp tháng, ba CSV
  59×10/236×6/944×7, hai biểu đồ và báo cáo V2. Median ARI 0,743427,
  NMI 0,592307, persistence 98,827471%, migration 1,172529%.

Task 10 mới chỉ được chuẩn bị đường dẫn V2 và guard cùng nguồn/cùng 60 tháng;
chưa chạy lại hoặc quyết định phương án thắng. Task 10–13 lịch sử và runner
`final_holdout.py` giữ nguyên context cũ; không xem kết quả đó là holdout/handoff
cho V2. Audit Task 12 lịch sử cần checkout cũ có đầy đủ bằng chứng PCA cũ.
Giữ code backend được source snapshot/holdout manifest tham chiếu để bảo toàn
khả năng kiểm chứng bằng chứng lịch sử; config V2 chỉ định output mới tường minh.

## Cập nhật 2026-10-21 — Nhiệm vụ 7 PCA + K-Means trên bộ dữ liệu V2

Đã thực thi đánh giá chất lượng từ diagnostics của Nhiệm vụ 6 V2: đúng 60 tháng
development 2019-01-31–2023-12-29, Global K=2, PCA 2 chiều. Nhiệm vụ 7 chỉ đọc
diagnostics và metadata kiểm tra nguồn; không fit model, không mở holdout.

- Notebook đã chạy đủ hai bảng và năm biểu đồ:
  [07_cluster_quality_evaluation_pca_kmeans.ipynb](../M2/notebooks/07_cluster_quality_evaluation_pca_kmeans.ipynb).
- Bộ mới nằm trong M2/artifacts/m2-evaluation-pca-kmeans/; chỉ có một CSV
  quality_summary.csv đúng 5 dòng × 7 cột, mọi n_total/n_available bằng 60,
  kèm năm PNG và manifest checksum. Bộ đánh giá cũ 15 tháng đã được đưa về Git history.
- Median Silhouette 0,939741; DB 0,383600; CH 1177,053847; Inertia 81023,955397;
  Balance 0,023814. Có 50/60 tháng Balance < 0,05, toàn bộ 60 tháng đạt rubric
  phân cụm bất đối xứng; ba singleton tại 2021-10-29, 2022-01-28, 2022-02-28.
- [Báo cáo Nhiệm vụ 7 V2](../M2/reports/Bao_cao_M2_Nhiem_vu_7_Chat_luong_cum_PCA_KMeans.md)
  trình bày phán quyết A/B/C và giới hạn suy luận. Silhouette cao không chứng minh
  hai chế độ cân bằng, nguyên nhân dòng tiền hoặc hiệu quả đầu tư.

Đã kiểm tra thực thi notebook, schema, thống kê, biểu đồ và checksum; toàn bộ
artifact/model Nhiệm vụ 6 V2 và bộ legacy được bảo toàn. Bàn giao quality metrics
cho Nhiệm vụ 10 với điều kiện các phương án dùng cùng dữ liệu/cửa sổ development.
Chưa thực hiện Nhiệm vụ 8–10 V2 trong phiên đánh giá này.

### Nhiệm vụ 8 PCA + K-Means V2 đã được người dùng chạy

Đã chuẩn bị [08_cluster_profiling_pca_kmeans.ipynb](../M2/notebooks/08_cluster_profiling_pca_kmeans.ipynb)
để người dùng tự chạy trên 120 hồ sơ/60 tháng của Nhiệm vụ 6 V2. Đã kiểm tra
ba bảng đúng kích thước 4×10, 9×4, 60×5; dùng scaler đã lưu của đúng tháng,
Radar/Heatmap và dropdown 60 tháng. Chỉ giới hạn hiển thị Z ở ±3, giữ Z thật
trong bảng/Heatmap và bằng chứng; không fit lại hoặc đọc holdout.

Người dùng đã chạy notebook: task8_manifest.json ghi complete, đủ 60 tháng/120
hồ sơ, Primary Driver là liquidity_21, chênh lệch Mean Robust Z C0−C1 = 240,887454.
Hai PNG, bằng chứng và báo cáo Nhiệm vụ 8 tên hậu tố v2 đã được kiểm tra checksum.
Kết quả ở M2/artifacts/m2-evaluation-pca-kmeans/; manifest và CSV Nhiệm vụ 7
được bảo toàn. Các kết luận vẫn giữ nhãn trung tính, không suy chi phí thực thi từ
thanh khoản trung bình hoặc coi cụm thanh khoản thấp hơn là dưới market median.

### Nhiệm vụ 9 PCA + K-Means V2 đã hoàn tất

Đã chuẩn bị [09_temporal_stability_pca_kmeans.ipynb](../M2/notebooks/09_temporal_stability_pca_kmeans.ipynb)
đã được người dùng chạy. Bước đầu chuẩn hóa artifact Task 6 đã có sang ba CSV phẳng
đúng 59×10, 236×6, 944×7; ARI/NMI giữ nguyên, transition dùng nhãn aligned xuyên
chuỗi, drift có hai đầu tâm cụm gốc thật và được đối chiếu mapping đã lưu.
Phần đánh giá đọc ba CSV để tạo bốn bảng và hai biểu đồ; không fit hoặc mở holdout.

Đã kiểm tra toàn luồng và rerun trong thư mục tạm, cùng checksum và bảng số liệu;
đã có CSV/ảnh/báo cáo Task 9 chính thức với manifest `complete`. Đích là
M2/artifacts/m2-evaluation-pca-kmeans/ và báo cáo Nhiệm vụ 9 hậu tố v2.
Notebook 7 chỉ kiểm tra CSV thuộc Task 7, cho phép ba CSV Task 9 dùng chung thư mục;
không thay số liệu hoặc manifest của Task 7/8.

Khi bàn giao Task 10 cần thống nhất mẫu số tỷ lệ Entry/Exit giữa các phương án:
bản PCA V2 dùng (Entry+Exit)/n_common; các notebook legacy có công thức khác.
Không đồng nhất tỷ lệ membership này hoặc migration với turnover/chi phí danh mục.

## Cập nhật 2026-10-04 — nhiệm vụ 11 Final Holdout đã thực thi

Người dùng yêu cầu thực hiện nhiệm vụ 11 sau khi tự chạy Task 10. Quyết định active
freeze `KMeans_Baseline`, K=2 lúc `2026-10-04T08:01:06+00:00`; holdout mở lúc
`2026-10-04T08:14:18.565783+00:00` sau kiểm tra gate/model hashes. C8 và Task 10
giữ nguyên. Đây là single winning method, monthly independent fitting/scaling;
không chạy comparators hoặc quét K.

- 7/7 holdout snapshots; universe 253–905 mã mỗi tháng; 4.624 assignments, 14 profiles,
  7 fitted models, 6 cặp temporal, 24 transitions và 96 feature drift rows; không skip.
- Median Silhouette 0,952683 so với Development 0,755722; Delta +0,196961.
  DB 0,431560; ARI 0,895529; NMI 0,791375; Persistence 99,5835%; Migration 0,4165%.
- Balance median 0,021445, cụm nhỏ 10–19 mã. Phân rã bình phương khoảng cách hai
  centroid cho thấy liquidity median đóng góp 99,9980%; Silhouette cao cần đọc
  cùng cảnh báo mất cân bằng/phân tách thanh khoản, không suy hiệu quả đầu tư.
- Gap reset giữ đúng; không nối 2025-01-24 với 2026-02-27 và không nối qua skip.

Mở `M2/notebooks/11_final_holdout_execution.ipynb`, chọn kernel Python M2 rồi Run All;
root tự tìm từ repo hoặc thư mục notebook. Core ở `src/delta_t1/experiments/final_holdout.py`,
config `configs/experiments/m2_final_holdout_v1.json`; output `M2/artifacts/m2-final-holdout-v1/`,
model `M2/models/holdout/`, report `M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout.md`.
Rerun chỉ kiểm tra checksum/nạp evidence, không fit lại. Không sửa decision/input
sau khi đã mở holdout. 11 targeted tests đã qua, gồm frozen gate, tamper, late data,
skip/reset, label permutation, kiểm chứng scaler/nhãn/profile từ C8 và verify-only rerun.
Synthetic smoke/compile đã qua. Stage tiếp theo là Task 12; chưa thực hiện Task 12/M3.

## Cập nhật 2026-10-04 — chuẩn hóa lại PCA notebooks nhiệm vụ 6–9 về v1

Bốn notebook `06_pca_kmeans`, `07_cluster_quality_evaluation_pca_kmeans`,
`08_cluster_profiling_pca_kmeans`, `09_temporal_stability_pca_kmeans` đã chạy trên
development và lưu output. Theo yêu cầu mới của người dùng, bộ sửa lỗi trước đó
mang tên v2 đã thay thế bộ v1 cũ và dùng các đường dẫn chuẩn:
`M2/artifacts/m2-task6-pca-kmeans-v1/`, `M2/artifacts/m2-evaluation-pca-kmeans/`
và `M2/models/pca_kmeans/`. Chạy 06 → 07 → 08 → 09 từ repo root hoặc thư mục
notebook. Notebook 06 kiểm chứng trực tiếp bộ hiện hành, không phụ thuộc file cũ.
Manifest giữ lineage gốc và ghi rõ migration theo ADR-051; không đổi model/số liệu.

Giữ 15 snapshot, 5.615 assignments, Global K=2 và fixed PCA=4; toàn bộ model/scaler
được tái dùng và kiểm chứng, không refit. Explained variance median 96,8639%, min
93,6424%. ARI median 0,798251, NMI 0,661313, Persistence 98,5618%, Migration
1,4382%. Transition probabilities dùng cùng aligned IDs: C0 giữ 80,9045% trên
199 lượt, C1 giữ 99,3053% trên 4.606 lượt; tỷ lệ tổng hợp che bớt khác biệt giữa cụm.
Drift giữ tọa độ gốc thật, không có placeholder `value_from=0`.

Không mở nhiệm vụ 10/final holdout/backtest. Kiểm chứng số chiều trên development
không tạo bằng chứng preregistration trước run v1; giới hạn này được giữ ở ADR-050.

Notebook/code/output nhiệm vụ 10 không bị sửa hoặc chạy lại trong migration này.
Các đường dẫn PCA mà notebook 10 đang đọc nay chứa bộ kết quả đã sửa; kết quả
Task 10 lưu từ lần chạy trước vẫn là kết quả lịch sử, cần người dùng tự chạy lại.
Bản sao khôi phục trước replacement ở `tmp/pca_notebook_repair/pca_before_replacement.zip`
đã kiểm tra checksum, nằm ngoài artifacts active và được Git ignore.

Kiểm tra sau replacement: bốn notebook chạy thành công, 19 targeted tests qua;
51 file số liệu/model/biểu đồ giữ nguyên từng byte so với bộ sửa v2, chỉ config và
manifest đổi metadata/đường dẫn. Toàn bộ 24 file Task 10 được đối chiếu vẫn nguyên
checksum. Các thư mục v2, file legacy và report Task 6 tên cũ đã được loại khỏi active tree.

## Lineage và phạm vi

Nhánh active: `m1-cafef-primary-experiment`.

Lineage trước R1: C7 `0fe5ddf724618a418331785e35c36e030cfc00ea` → C8 implementation `d60c8cba49c90b3b36c346dfea463a1e4f659ee1` → C8-VERIFY `e149198986345bb02610e53d8a330f641b89df22`. R1 chỉ hợp nhất repository; không thay methodology, dữ liệu hoặc kết quả C8.

Nguồn market active là CafeF `TradeHistoryNew`. `AdjustPrice × 1000` được dùng như `adj_close` với `adjustment_basis=vendor_adjusted`; không tuyên bố split-only hoặc total-return.

## Kết quả bất biến

C8 = `EXECUTED_AND_VERIFIED`. C8-VERIFY đã xác minh offline 19/19 output hash, upstream C5/C7/identity hashes và năm source ZIP. Không network request, supplemental acquisition, clustering hoặc backtest được thực hiện.

| Gate | Tổng | C5 baseline | C7 complete expansion |
|---|---:|---:|---:|
| Candidate | 952 | 500 | 452 |
| `feature_complete` | 922 | 490 | 432 |
| `market_feature_ready_v2` | 905 | 490 | 415 |
| `latest253_complete` | 922 | 490 | 432 |
| `latest253_incomplete` | 30 | 10 | 20 |
| `historical_identity_ready` | 0 | 0 | 0 |
| `research_ready` | 0 | 0 | 0 |

Tradability được báo riêng: 675 `ACTIVE`, 276 `OBSERVED_ZERO_VOLUME`, 1 `UNKNOWN`. 47 securities chưa market-ready. 148/600 expansion securities còn `DEFERRED_EXPANSION_ACQUISITION`.

Proposed `MARKET_ONLY_EXPERIMENTAL_UNIVERSE` có đúng 905 rows thỏa `market_feature_ready_v2=true`. Đây không phải final research universe, canonical production universe hoặc historically identity-verified universe. Zero volume là observation thật và không tự loại khỏi market readiness.

Cho M2-PREP, khái niệm cần freeze là `market_experiment_eligible(t) = market_feature_ready_v2(t)` theo từng snapshot. Con số 905 chỉ mô tả snapshot mới nhất `2026-08-28`; không được dùng như terminal-universe filter cho các tháng trước và không phải alias của legacy `eligibility` hay strict `research_ready`.

## Invariant còn hiệu lực

- Snapshot chung: `2026-08-28`; observation muộn hơn giữ làm evidence nhưng không vào feature/readiness.
- Không ffill, bfill, interpolate, missing-to-zero, synthetic OHLC/return hoặc timeline compression.
- Null activity component làm total tương ứng null; không zero-fill.
- Full-history audit và latest-253 audit độc lập.
- Non-authoritative calendar gap giữ `CALENDAR_UNCERTAIN`; không đổi thành confirmed missing.
- Historical identity và financial PIT vẫn fail-closed; không promote trong R1.
- C8 baseline tái lập C5, security-level readiness diff rỗng.

Full-history status: 934 `INCOMPLETE`, 18 `UNCERTAIN_BOUNDARY`, 0 complete. Đây chủ yếu phản ánh conservative calendar/boundary evidence, không phủ định 905 market-ready rows.

## Repository sau R1

R1 bỏ 192 file planning/history/config/runner/module/test superseded khỏi active tree. Git history là archive; không tạo archive copy. Active tree giữ:

- C8 runner, C8 verifier, C8 config, C8 implementation/tests và compact verification artifact;
- C6 expansion + supplemental contracts/runners/consolidation để xử lý 148 deferred rows khi có stage riêng;
- CafeF source semantics, generic promotion/reconciliation và Product Layer;
- C5 builder vì C8 lineage/test vẫn phụ thuộc;
- minimal KBS/Vnstock compatibility path còn được generic integration dùng;
- machine-readable R1 artifact tại `artifacts/repository/r1-consolidation-v1/`.

Hai đường dẫn C1 cũ còn xuất hiện trong frozen C8 provenance/config hash fields chỉ là Git-history identifiers; chúng không phải active input path.

## M1-REPORT

Artifact `artifacts/reports/m1-market-foundation-v1/` và notebook
`notebooks/eda/M1_CAFEF_MARKET_FOUNDATION.ipynb` là lớp report/inspection
offline trên evidence C8 đã verify. Report tái tính và assert toàn bộ headline,
feature coverage, source/exchange composition, 30 latest-253 incomplete rows,
47 market-readiness exclusions và 80 monthly snapshots từ `2020-01-31` đến
`2026-08-28`. Notebook chỉ đọc explicit immutable report directory; business
logic và integrity checks nằm trong generator.

Readiness theo tháng có các đoạn gián đoạn lớn và zero-readiness periods. M2-PREP phải giải thích chúng trước khi freeze development/validation windows; D1 chỉ ghi nhận evidence, không diễn giải nguyên nhân và không thay methodology.

**M1 MARKET DATA FOUNDATION: COMPLETE FOR MARKET-ONLY EXPERIMENT PREPARATION.**
Strict research gate vẫn `NOT READY`; `historical_identity_ready=0` và
`research_ready=0`.

## Kiểm chứng offline

```powershell
.venv\Scripts\python.exe scripts\build_m1_market_foundation_report.py --verify-existing
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

Không rerun `run_cafef_c8_complete_only.py` hoặc C8 verifier-generator để kiểm chứng artifact đã tồn tại. R1 exact-inventory verifier thuộc frozen R1 tree và đương nhiên không đại diện cho current tree sau M1/D1. Heavy artifact và năm ZIP phải giữ nguyên hash.

## M2-PREP

Artifact `artifacts/experiments/m2-prep-v1/` đã audit eligibility, 80 snapshot, implementation, feature/preprocessing, algorithms, metrics và literature mà không chạy clustering. Kết quả cuối là **`MANUAL_REVIEW_REQUIRED`**; không tạo `configs/experiments/m2_market_only_v1.json`.

Hai discontinuity hệ thống được giải thích từ evidence hiện có:

- `2023-05` đến `2023-10`: session `2023-05-15` có trong calendar của cả ba exchange nhưng thiếu VNINDEX row; strict `beta_126` làm toàn bộ cross-section chưa complete cho tới khi gap ra khỏi 126-return window. Phân loại: benchmark/calendar propagation, không phải clustering result.
- `2025-02` đến `2026-01`: canonical market có 0 equity price row ở open session `2025-02-03`; strict `mom_252` cần 253 real prices nên toàn bộ cross-section fail cho tới khi gap ra khỏi window. Không impute hoặc timeline-compress.

Latest snapshot vẫn tái lập đúng `market_experiment_eligible=905/952`, với membership tính độc lập ở từng tháng; historical identity và research readiness vẫn bằng 0.

## M2-PREP-REVIEW

Owner review ngày `2026-09-26` đã chấp thuận các đề xuất Protocol v1 trong
`docs/plans/DELTA_UNIFIED_PROJECT_PLAN.md` làm input cho M2-R1:

- development `2023-11-30 → 2025-01-24`;
- sealed holdout `2026-02-27 → 2026-08-28`;
- minimum `120` eligible securities mỗi snapshot, thấp hơn thì skip với reason;
- đúng 8 market features của M1;
- không winsorize/clipping; RobustScaler theo snapshot là default và z-score là sensitivity;
- `k=2..8`, chọn một global `k` trên development bằng median Silhouette, tie-break bằng median Davies–Bouldin;
- PCA chỉ là comparator, component count được chọn trên development theo ngưỡng cumulative explained variance `>=90%` rồi freeze;
- C8 feature snapshot `1.6.0` là active M2 input contract, registry `1.5.0` giữ legacy compatibility;
- Dynamic Clustering vẫn `NOT APPROVED`; `portfolio_evaluation.enabled=false`.

Quyết định này giải quyết owner-review gate của M2-PREP nhưng không sửa artifact
`m2-prep-v1`, không tự tạo final config và không làm M2-R1 thành `PASS`. Artifact
M2-PREP tiếp tục giữ status lịch sử `MANUAL_REVIEW_REQUIRED`; stage active chuyển
sang M2-R1 để materialize quyết định thành contract có thể kiểm thử.

## Stage tiếp theo

### Nhánh financial độc lập — 2026-10-02

Owner giao market-only cho nhóm khác và yêu cầu session này triển khai financial
trong `SourceCode-CafeF`. Financial raw coverage pilot đã IMPLEMENTED/EXECUTED,
nhưng stage giữ **PARTIAL** vì coverage failures; không đánh dấu PIT resolved.
Runner: `scripts/run_cafef_financial_pilot.py`; config:
`configs/data/cafef_financial_pilot_v1.json`; collector:
`src/delta_t1/ingestion/cafef_financial.py`.

Evidence local `data/financial/cafef_raw_pilot_v1/run-20261002T155840Z-652f827b/`:
72 logical calls, 24 streams, exact hashes/offline replay PASS. FPT/VNM có 19/20
quý mỗi KQKD/CDKT (thiếu Q2-2024), PVS/ACV có 20/20. FPT/VNM/PVS có 5/5 năm;
ACV có 4/5 do annual page 2 overlap. LCTT không trả group ở summary cho cả bốn mã.
Period presence không chứng minh đủ đầu vào score. PIT NOT_READY; không canonical
financial, không bật financial features và không thay market artifacts/protocol.

Validation: 59 targeted CafeF tests PASS (gồm 9 financial tests); full suite chạy
177 tests có 176 PASS và 1 ERROR tại immutable M2-PREP verifier do
`docs/DECISIONS.md` có owner-review edits từ trước session (HEAD hash khớp frozen
manifest, working tree không khớp). Không rewrite historical manifest để làm PASS.
Compile và dry-run PASS. Self-review giữ null/zero, raw evidence, finite limits,
pagination failure, access stop và research isolation.

Financial update 03/10/2026: detail remediation acquisition và report COMPLETE;
historical financial readiness vẫn PARTIAL, PIT NOT_READY. 108 calls cho 88 detail
pages/20 document lists, 19.644 cell observations; annual presence 60/60,
quarterly presence 225/240. ACV annual 2021 recovered qua detail. Có PDF cho cả
11 unique quarterly gaps, nhưng chưa tự động trích toàn bộ scanned PDFs. Đã QA
45 PDF sample facts FPT/VNM, tìm được weighted shares và EPS version differences.
Private `analysis_v2` xuất CSV/candidate checklist và 1.047 numeric comparisons
khớp, không promote unit/scope/PIT. 69 targeted CafeF tests và compile PASS;
full suite snapshot 185 tests vẫn chỉ lỗi immutable M2-PREP docs hash đã biết.
[Report quá trình — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip).

Financial next stage: hoàn thiện document extraction/taxonomy và verified
fact-to-document vintage/timing trước canonical PIT hoặc calculators. Market
next stage bên dưới thuộc nhánh nhóm market-only.

Financial evidence update 03/10/2026: thêm 30 PDF và issuer listing; all-document
text index v2 có 41 PDF/3.101 trang, OCR v3 có 198 trang thuộc 11 gap documents.
Thêm 85 visual-validated observations, tổng 130 cùng evidence cũ; 10 arithmetic
checks PASS. Có CFO YTD evidence cho 11 gap periods và BS/IS Q2-2024 FPT/VNM,
nhưng không tự biến thành full quarter/PIT coverage. Annual document candidates
24/28 mã-năm 2019–2025; VNM 2019/2020/2021/2025 full VAS còn thiếu. Annual report
VNM 2025 tải được chứa IFRS tables và VAS audit extract, không đóng full-VAS gap.
Checklist 1.176 mục: 813 raw-present/55 missing/308 note-review-required.
[Report v2 — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-remediation-v2/report.md) và
[financial contract](research/FINANCIAL_FEATURE_CONTRACT.md) là handoff hiện hành.
Financial targeted 30 tests PASS, compile/synthetic smoke PASS; full suite
197/198 PASS, một lỗi M2-PREP DECISIONS checksum đã biết. Stage PARTIAL,
financial_features_allowed=false; chưa canonical/score/backtest hoặc mở rộng universe.

Financial pilot closure update 03/10/2026: FPT annual core 2019–2025 đạt 49/49 ô
được visual-verified; OCR thêm 108 trang, tổng 306. Overlay hiện hành
`data/financial/pilot_readiness_v4` có 107 document-verified/PIT-pending, 713
raw-unverified, 302 note-review và 54 missing trên 1.176 ô. Giữ riêng số liệu
2020 reclassified và EPS 2024 restated; correction run sửa hai numerator về VND.
FPT có document inputs cho 4/9 nhóm F-Score mỗi năm 2021–2025, chưa tính signal.
Config `configs/data/financial_pilot_closure_v1.json`; [report hiện hành — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-pilot-closure-v1/report.md).
Stage PARTIAL; PIT NOT_READY. 5 tests mới/compile/synthetic smoke PASS;
full suite 202/203 PASS trước final unit/hash hardening, lỗi M2-PREP cũ không đổi.
Next financial stage: hoàn thiện FPT notes/mapping và publication-version
evidence; sau đó mở workflow sang ba mã pilot còn lại. Không crawl 1.000 mã.

Financial execution update 03/10/2026: [plan Section 26](plans/DELTA_UNIFIED_PROJECT_PLAN.md)
đã được triển khai đợt đầu. FIN-D1 COMPLETE với `task_readiness_v3` 120 rows;
FIN-D2/3 PARTIAL, FIN-D4/5 pending. OCR thêm 352 trang, tổng 658; review thêm
82 observations EPS/PPE/debt/expense/shares. Bảy annual EPS rounding checks PASS;
FPT EPS recompute có annual input presence 2021–2025 đạt 5/5, chưa compatible
vintage/PIT acceptance. FPT core vẫn 49/49, F-Score presence vẫn 4/9 nhóm mỗi năm.
Overlay hiện hành `pilot_readiness_v6`: 133 document-verified/PIT-pending, 703 raw,
286 note-review, 54 missing trên 1.176 cells. Thu issuer HTML và original audited
FPT 2025 PDF: exact attachment/date 19/03/2026, DATE_ONLY, available_at null;
không gán publication này cho annual-report vintage. 21 targeted tests, compile,
synthetic smoke PASS; full suite trước final instant-field extension 208/209 PASS,
còn lỗi M2-PREP frozen DECISIONS checksum đã biết. Exact inventory/PDF/image hashes
PASS. [Execution report — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-execution-v1/report.md),
config `configs/data/financial_execution_plan_v1.json`; features false, PIT NOT_READY.
Next financial stage: nghiệm thu FPT notes/mappings và publication history, sau
đó xử lý ba mã pilot còn lại, full VAS VNM và quarter/TTM trước expansion.

**M2-R1 — PROTOCOL FREEZE v1**: tạo `configs/experiments/m2_market_only_v1.json`, ADR/decision artifact, validation và tests cho toàn bộ quyết định Protocol v1 đã được owner review. Không chạy real clustering, không mở holdout, không sửa market-only runner/input adapter và không mutate C8/M1/M2-PREP evidence. Sau khi M2-R1 PASS, exact next stage là **M2-R2 — MARKET-ONLY RUNNER ADAPTER**.

### Financial FIN-D2 continuation — 03/10/2026

Handoff hiện hành: [workflow runbook](crawl/README.md),
[report — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip).
Thêm 40 observations, 7 accounting QA records PASS; overlay pilot_readiness_v7 có
135 document-verified/PIT-pending, 703 raw, 284 note-review và 54 missing.
FPT Z annual input presence 2024–2025 đạt 7/7 sau EBIT reconciliation;
EPS 2021–2025 giữ 3/3, mọi task_ready false/computed_value null. Workflow_v4 có
1.224 unique field-year cells, 140 external requirements; reuse 460 OCR pages và
27 annual PDF candidates. VNM full-VAS gaps giữ riêng, không coi candidate đủ scope.
22 financial targeted tests/compile/synthetic smoke PASS; full suite 211/212 PASS
trước final framework-gap/cap hardening, lỗi M2-PREP frozen DECISIONS checksum cũ.
FIN-D2 PARTIAL/PIT NOT_READY; chưa unattended multi-symbol full-universe pipeline.
Next: đóng ordinary-income/debt/PPE/net-receivables/issuance/common-equity mappings
và accounting QA theo vintage, rồi publication/quarters/TTM và pilot closure.
Owner thông báo nhóm market đã bắt đầu cluster; workstream này chỉ xử lý financial,
không audit/certify lại tiến độ clustering hoặc thay market methodology.

### Financial date-PIT handoff hiện hành — 03/10/2026

[Report hiện hành — archive](../artifacts/archives/financial-history-20261023/artifacts/reports/financial-date-pit-v1/report.md) thay handoff
financial v7 bên trên. Owner đã duyệt dùng ngày: từ phiên exchange quan sát được
đầu tiên sau publication_date; thiếu giờ không còn chặn date-PIT daily/monthly.
10 exact PDFs có publication evidence; 11 prefix exceptions chưa đóng. Phát hiện
ACV2022 candidate là VEAM và loại đúng hash, giữ raw/candidate ACV2022 khác.
Latest pilot_readiness_v10: 139 verified/699 raw/284 note/54 missing trên 1.176 ô;
date_pit_v4: 124 cells có exact-vintage date references. FPT 139/294 value và
124/294 date cells; Z2024–25 7/7, EPS2021–25 3/3 value/date inputs. Chưa score
acceptance: task_readiness_v6 giữ 120 task_ready=false. Workflow_v6: 1.224 cells,
140 external requirements, 26 PDF candidates, 488 OCR pages reused.
28 targeted tests/compile/synthetic smoke PASS; full 217/218 PASS, lỗi M2-PREP
immutable DECISIONS checksum cũ. FIN-D2/3/4 PARTIAL, FIN-D5 pending. Calendar observed
không authoritative; chưa unattended full-universe financial pipeline.
Next: đóng FPT semantic/joint-vintage QA, revision/publication exceptions, statements
ba mã còn lại/full VAS VNM, quarters/YTD/TTM/share events, rồi bounded scale gate.
Market clustering do nhóm khác phụ trách; workstream này không sửa market protocol.

### Financial executable reference flow — handoff mới nhất 03/10/2026

[Report — archived](../artifacts/archives/project-cleanup-20261019-v1/superseded-reports.zip): chạy code từ
cached PDF/OCR → 22 parsed cells → reviewed-reference/accounting QA → date-PIT →
EPS/EM-Z reference outputs. FPT2024 original EPS 4.944/Z 6,843186 tại 17/03/2025;
FPT2025 EPS 5.216/Z 7,106292 tại snapshot 28/08/2026. EPS2024 tại snapshot này bị
chặn vì known revised comparative 4.292 trong original2025 chưa mapped; không dùng
số cũ hoặc backfill số mới. Latest reference_flow_v6, deterministic replay v5/v6.
36 task/decision rows: 5 QA-pass executions/4 unique task-years, 6 unavailable,
1 revision blocked, 24 F/M/PE/PB outside calculators. Chín targeted tests/compile/
synthetic smoke PASS; full 226/227 PASS, frozen M2-PREP checksum cũ còn lỗi.
Value/date coverage giữ 139/124 cells; không có feature production promotion.
Reference slice chạy được; tổng FIN-D2 PARTIAL, full-universe pipeline chưa đạt.
Next: revised-comparative acceptance, F/M semantics/inputs, TTM/share basis và
unseen-template pilot trước scale. Market-only work không thay đổi.

## M2 Nhiệm vụ 1 — protocol freeze

Owner đã phê duyệt và khóa protocol market-only v1 trong
`configs/experiments/m2_market_only_v1.json`: 15 development snapshots
`2023-11-30..2025-01-24`, 7 holdout snapshots niêm phong
`2026-02-27..2026-08-28`, minimum eligibility 120, 8 market features,
fail-closed missing, no clipping/winsorization, Robust Scaling theo từng snapshot
và `k_range=2..8`. Global K chỉ được chọn trên development bằng
cluster-quality metrics; `portfolio_evaluation.enabled=false`. PCA chỉ là
comparator độc lập, không phải preprocessing chung. Chưa fit model,
không mở holdout, không backtest và không thay data/evidence.

Acceptance gate sau khi phục hồi đúng immutable C5 local artifact: C5 manifest
SHA-256 `869512c66fceee02f9b5801af3c24724309b508013a607158085dd7e9b50d256`,
20/20 C5 output hashes khớp và full repository suite 173/173 tests pass.
Ba file recovery WIP untracked ngoài active R1 tree được giữ nguyên trong
`tmp/full_recovery_wip_20260926/`; không phục hồi recovery stack superseded.

## M2 Nhiệm vụ 2 — runner preparation/testing

Runner market-only đã có adapter xác minh checksum và đọc trực tiếp
`canonical/feature_snapshots.jsonl` của C8 mà không đi qua strict historical-identity
gate dành cho M3. Adapter chỉ tạo alias in-memory
`market_feature_ready_v2 = market_feature_ready` cho C8 v2, không mutate artifact;
legacy `eligibility` không được dùng thay thế.

Snapshot `2023-11-30` tái lập đúng 142 securities eligible. Runner kiểm tra
đúng 8 feature là numeric finite, skip khi `n_eligible < 120`, và output được
common `build_snapshot` interface chấp nhận. Terminal-universe guard dùng snapshot
membership độc lập, không retrospective-filter. Nhiệm vụ này không chạy
Global K, không mở holdout và không backtest.

## M2 Nhiệm vụ 3 — Global K selection (Completed & Approved)

Đã chạy hoàn tất 105 lượt K-Means (15 development snapshots nhân 7 cấu hình `k=2..8`).
105/105 lượt chạy hội tụ và tính đủ 5 metrics.
Cấu hình K = 2 đạt median Silhouette cao nhất (0.7557), median Davies-Bouldin thấp nhất (0.5219)
và Calinski-Harabasz cao nhất (316.39). Nhóm đã phê duyệt chính thức Global K = 2 (ADR-049),
khóa `k: 2` vào `configs/experiments/m2_market_only_v1.json`.
Hiện tượng cụm nhỏ (8-21 mã) siêu thanh khoản được ghi nhận và phân tích đầy đủ.

## Stage tiếp theo

## FIN-PIT-2 — document linkage và semantic extraction

FIN-PIT-2 đã chạy offline trên immutable FIN-PIT-1 artifact với gate `PARTIAL`.
Stage xử lý 32 document unique-content và 40 linkage candidates, nhận diện 4 primary
financial reports và 2 supporting explanatory documents. Ba báo cáo năm 2022 của
PVS có text layer đủ evidence đạt `SEMANTIC_READY`; 29 report candidates còn lại bị
quarantine do scan/semantic chưa đủ và không có OCR engine trong environment.

Kết quả candidate gồm 220 facts (216 balance-sheet instant semantic-ready, 4
unresolved), 220 taxonomy candidates chưa final-promote, 6 linkage `VERIFIED`, 34
`AMBIGUOUS`, 0 conflict. Cả 7 revision groups vẫn giữ `revision_relation=UNKNOWN`.
Timing được preserve ở cấp report candidate: 4 `A_EXACT_TIMESTAMP`, 28
`B_OFFICIAL_DATE_D1`; không tạo timestamp giả. Artifact nằm tại
`artifacts/financial_pit/fin-pit-2-semantic-extraction-v1/`.

FIN-PIT-2 không ghi canonical financial row, không bật financial feature và không
tự mở FIN-PIT-3. Phần scan cần một OCR run riêng có engine/version/page/confidence
provenance trước khi có thể nâng coverage.

## FIN-PIT-2-R1 — OCR remediation

FIN-PIT-2-R1 đã chạy offline bằng Tesseract OCR `v5.4.0.20240606` trên đúng 26
tài liệu scan/mixed chưa phân loại chắc chắn. Preflight review 32 tài liệu, chọn 209
trang; 205 trang đạt OCR quality gate và 4 trang `LOW_CONFIDENCE` bị loại khỏi
semantic evidence. Raw PDF và timing handoff không đổi.

Gate là `PARTIAL`. OCR tăng document classified từ 6 lên 32, linkage `VERIFIED`
từ 6 lên 27 và giảm `AMBIGUOUS` từ 34 xuống 4. Đồng thời evidence mới phát hiện 9
`CONFLICT` scope giữa disclosure candidate và nội dung attachment; các conflict này
được giữ fail-closed. Quarantine giảm 29 xuống 26, semantic-ready reports tăng 3 lên
6, fact candidates tăng 220 lên 242 nhưng semantic-ready facts giữ 216. Unit verified
tăng 9 lên 30; scope verified tăng 6 lên 29; assurance verified tăng 3 lên 8.

Q2/Q3 duration vẫn chưa đủ evidence để promote: 0 `STANDALONE`, 0 `YTD`, 26 facts
duration `UNKNOWN`. Cả 7 revision groups tiếp tục `UNKNOWN`; timing vẫn 4
`A_EXACT_TIMESTAMP` và 28 `B_OFFICIAL_DATE_D1`. Artifact nằm tại
`artifacts/financial_pit/fin-pit-2-r1-ocr-remediation-v1/`. Stage không ghi canonical
row, không bật financial feature và không tự mở FIN-PIT-3; nếu mở stage sau chỉ được
review một verified subset được freeze rõ.

**M2 Nhiệm vụ 4 — CHẠY PHƯƠNG ÁN A: K-MEANS BASELINE**: Đóng gói và hoàn thiện
kết quả K-Means chính thức với Global K = 2 trên 15 development snapshots, chuẩn bị cho
Nhiệm vụ 5 (Ward) và Nhiệm vụ 6 (PCA + K-Means). Không mở holdout và không backtest.



### Portable financial replay — 24/10/2026

Kiểm thử Git export phát hiện nhiều financial source pins cũ còn phụ thuộc LF/CRLF.
Đã thêm frozen-source-v2 giữ exact bytes toàn bộ16trackedsource/config/scriptpins từ
checkpoint819cd82, không bỏ bất kỳ hashcheck nào. Overlay chỉ áp src/scripts/configs;
raw/data pins vẫn kiểm tại path gốc. Review outputv2 giữ bảnv1 nguyên vẹn; explicitLF
cho reviewscript giữ checksum ổn định khi checkout. Đây là packaging/provenancefix,
không thay phép tính, sourcefacts hoặc model. Lệnh Verify hiện dùng overlay/reviewv2.


### Execution58 verification và phạm vi còn lại

27 targeted tests PASS (8tests mới + financial/integration/clustering regression),
compileall PASS; synthetic smoke `run-20261024T021711Z-30619c75` PASS. Independent
C review kiểm lại scalers, weights, nearest-centroid, inertia, raw profile means và
centroids cho5593assignments/7models PASS. RerunC giữ nguyên bytes và timestamps
của numericaloutputs, khôngrefit; comparison idempotent và coverage9213/5593 PASS.
C kế thừa financialfull10fixedcohort, còn selection/survivorshipbias. Sourcefacts
không tự accepted, khôngclaimPIT hoặcnewholdout. Fullsuitegate vẫn PARTIAL;
lượtstage58 có log `.tmp/dual-combined-full-suite.log` và summaryJSON cùngprefix.


C2025 separation driver bổ sung: market block chiếm96,11% phần tách centroid,
financial3,89%, dù inputblockvariance cân bằng50/50. Đây là kết quả geometry thực tế,
không phải đặt weight sai; dominant features là mom126, mom252, mdd126, mom63 vàvol63.
Không đổi preprocessing hoặc weight sau khi xem kết quả. Queue cụm nhỏC2025 gồm
DNN/GTD/NVP/TVH/VEC/VIC; giữ evidence, chưa source-fact accept hoặc quarantine.


### Execution58 final gate — 24/10/2026

Fullsuite timeout 240.1giây, ít nhất254testlines kết thúcok,
không FAIL/ERROR trước timeout. Cuối log ở financial_crawl_trial fixture50;
không diễn giải timeout thành suitePASS hoặc xác định nguyên nhân treo.
Targeted27tests/compile/smoke/independentCverification đềuPASS. A/Bsourceartifacts giữnguyên.
Execution58 đã hoàn tất chạy và đối chiếu ở phạm vi descriptive reference; quality
REVIEW_REQUIRED và PIT/M3gates false. Không tự thay preprocessing sau kết quả.
