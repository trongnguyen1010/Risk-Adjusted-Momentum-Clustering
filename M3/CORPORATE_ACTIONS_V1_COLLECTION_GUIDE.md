# Hướng dẫn thu thập corporate actions V1 cho M3 Q11

## Lệnh hiện hành V6: phục hồi616mã, còn456mã, pause tách khỏi Playwright

V5 lỗi đã khép đúng PythonPID12040, bảo toàn616query đã đạt và PLCpartial;
không phải userpause của V5. V6 dùng lại616,thu456mã từ PLCpage1,ORS80/85 vẫnHOLD.
Chỉ dùng public supervisor này, không chạy V5 hoặc privateworker:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_recovery_pausefix_v6.py"
```

Supervisor giữ terminal; worker thu thập chạy ẩn trong processgroup/no-console
riêng, headless Chrome/min4s/oneworker. **Ctrl+C một lần** chỉ gửi pause marker,
không đóng driver/browser. Chờ worker hoàn tất thao tác đang chạy, ghi checkpoint
và in **OUTPUT_ZIP** rồi mới đóng terminal. Nhấn thêm Ctrl+C cũng không phải lệnh
force-kill. Nếu đang preflight/copy phải chờ kiểm tra/copy/gói evidence đạt.
Hoặc từ terminal khác chạy cùng publicCLI với `--pause`.

Sau `PAUSED_BY_USER_VERIFIED_CHECKPOINT`, dùng lại cùng lệnh đầu tiên để tiếp tục.
Source/error/crash/unsealed/stalelock vẫn cần review, không auto retry/kill hoặc
tự skip mã. Nếu lỗi/thiếuZIP,giữ output/lock và gửi thông báo. Không chạy private
`run_vsdc_recovery_pausefix_worker_v6.py` trực tiếp. `--check` chỉ kiểm tra offline.

Terminal hiển thị phase/rawhash/preparation và **sao chép checkpoint0/616→616/616**
(cập nhật mỗi10query),sau đó616/1072scopedqueries. Luôn kèmoriginal1073/ORSHOLD1,
còn456/24pendingbatches. Hếtscope vẫn originalunresolvedORS1; không markORScomplete.
ETA sau5query V6 mới. Preparation không copy616query lần nữa; user-run mới copy
exact evidence, nên bước mở đầu và đónggói ZIP vẫn có thể mất vài phút/dung lượng.

Giữsource/TLS/privacy/identity/parser/hash gates;thêmworkerconsoleisolation và
browserhandle_sigintFalse. 26targetedcases/compileall/smoke PASS,gồm **realWindows
Ctrl+C riêng với Chromeabout:blank** (khôngVSDC):driver sống đến khi nhậnmarker,
đóngcontext/browser/manager bình thường. Đây không bảo đảm mọi lỗi driver đều
resumable. Nativecloseproof/closedcrashsnapshot giữ riêng,không sửaV5state.

Carry1.618business/34.422context/activeupper8.769,523s,bao gồm thời gian treo đến
khi khép PID+1s. Caps global5400/89094/8hactive,batch100/1660/20phút,query20pages/
400rows/98context/78assets/180s,operation15s/HTML2MB,max100segments không đổi.
Batch032 còn khoảng103s active budget; nếu xử lý vượtcap thì STOP,không tựreset.
Giữ tất cả ancestors/preparation/snapshot để kiểm tra continuation.

```text
data/corporate_actions/work/vsdc_recovery_pausefix_v6/run-<UTC>/state
data/corporate_actions/work/vsdc_recovery_pausefix_v6/run-<UTC>/delta-vsdc-recovery-pausefix.zip
```

Preparation `data/corporate_actions/work/vsdc_recovery_pausefix_preparation_20261103_v6/`;
validation `data/corporate_actions/work/vsdc_recovery_pausefix_validation_20261103_v6/`.
2.460protected files;agent chỉlocaltest1browserabout:blank,0sourceVSDCrequests,
chưa chạy456mã. **Bước tiếp:** user chạyV6local,gửiOUTPUT_ZIP khi xong/pause/lỗi,
offline review trước ORSgap/7+418 hoặc bất kỳcanonical/PIT/identity/history claim.

## Sự cố hiện tại: V5 chưa finalize sau Ctrl+C — chưa được chạy lại/đổi nhánh

Run `run-20261103T140146003064Z` mất Playwright driver sau Ctrl+C, chưa có
PAUSED/result/root ZIP. Đã xác minh616completequeries (575import+41new), PLC
page1/3 làpartial, còn456scopedqueries +ORS HOLD1. External --pause marker đã
gửi nhưng chưa có acknowledgement. Giữ terminal/output/lock; không relabel
PAUSED, xóa lock, đổi nhánh hoặc replay lệnhV5 để thử tiếp.

Hướng dẫn Ctrl+C bên dưới không bảo đảm safe pause trên Windows khi Playwright
driver nhận tín hiệu dừng. Cần xử lý session lỗi và explicit recovery/version
mới với interruption tests; chưa có lệnh recovery cho sự cố này. Review snapshot:
`data/corporate_actions/work/vsdc_v5_ctrlc_incident_review_20261103_v1/`.

## Lệnh hiện hành V5: giữ575 mã đã đạt, thu497 mã, ORS80/85 HOLD riêng

V5 dùng lại575query đã review, không tải lại. ORS giữ nguyên80/85rows trong
evidence HOLD, không tính là hoàn tất. Chỉ497mã khác được thu bằng Chrome ẩn,
min4s giữa business request starts qua trang/mã, một worker. Một lệnh chạy hết
26pendingbatches, không chạy song song V4/pilot hoặc lượtV5 khác.

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_recovery_ors_hold_v5.py"
```

Progress bắt đầu **575/1.072 scoped queries**, còn497, luôn kèm **phạm vi gốc
1.073 / ORS HOLD1 (80/85)**. Mẫu số1.072 chỉ là scope được chạy; ORS không bị
xóa khỏi inventory hoặc tính complete. Counter chỉ tăng sau full query seal/
reparse/validate/context close. ETA lấy mẫu sau5query V5 mới. Khi hết scope vẫn
status `PASS_SCOPED_QUERIES_WITH_ORS_HOLD_REVIEW_REQUIRED`, original unresolved1;
batch030 chưa fully complete theo inventory gốc.

Tạm dừng bằng **Ctrl+C một lần**, chờ `OUTPUT_ZIP` rồi mới đóng terminal. Hoặc
chạy cùng lệnh trên với `--pause` từ terminal khác. Chỉ status
`PAUSED_BY_USER_VERIFIED_CHECKPOINT` cho tiếp tục bằng cùng lệnh đầu tiên.
Completed queries được copy nguyên evidence để bỏ qua; query dở thu lại từ
page1/context mới. Giữ preparation và tất cả ancestor runs; không xóa/đổi tên
output hoặc active.lock. Source/error/crash/unsealed/stale lock vẫn STOP/review,
không auto retry hoặc tự skip thêm mã. Gửi OUTPUT_ZIP kể cả lỗi/dừng; nếu chưa
có ZIP thì gửi nguyên thông báo, giữ output/lock.

Cumulative costs1.514business/32.092context/7.148,281s được giữ, gồm failedAPP/
ORS và diagnostics cũ. Caps global5.400/89.094/8hactive; batch100/1.660/20phút;
query20pages/400rows/98context/78assets/180s,operation15s/HTML2MB,max100segments.
Không reset budget qua version/pause. Full source/preparation files được hash
ở preflight và copy; trong source checks dùng fullSHA256 sealedV4ZIP+manifest,
old protected/runtime/parents. Không lưu raw response/fullDOM/cookie/token/HAR.

Preflight/import575query có thể mất thời gian và dung lượng; terminal có banner
kiểm tra offline trước khi request đầu tiên. Root ZIP chứa575prefix/query mới,
ORS hold evidence và logs; chờ OUTPUT_ZIP sau acquisition hoặc pause.

```text
data/corporate_actions/work/vsdc_recovery_ors_hold_v5/run-<UTC>/state
data/corporate_actions/work/vsdc_recovery_ors_hold_v5/run-<UTC>/delta-vsdc-recovery-ORS-HOLD.zip
```

Preparation `data/corporate_actions/work/vsdc_recovery_ors_hold_preparation_20261103_v5/`;
validation `data/corporate_actions/work/vsdc_recovery_ors_hold_validation_20261103_v5/`.
26 targetedcases/compileall/smoke PASS,2.451protectedfiles. Orphan V4 preflight lock đã được review
PID/output và archive nguyên bytes, không thêm auto-clearing lock. Agent chưa
gọi source/browser hoặc chạy497mã; V4 STOP và575checkpoint giữ nguyên.

**Bước tiếp theo:** user chạy V5 local, gửi OUTPUT_ZIP khi xong hoặc dừng/lỗi để
review coverage/source/cache. Sau đó xử lý ORS gap và nhóm7+418 riêng. Các lệnh
V4/pilot phía dưới là lịch sử, không chạy lại. Acquisition không tự promote
owner/canonical/PIT/identity/full-history hoặc chứng nhận không còn sự kiện thiếu.

## Trạng thái mới nhất: V4 đã STOP tại ORS — không chạy lại lệnh cũ

Run `run-20261103T112801286796Z` đã lưu575/1.073completequeries,còn498. ORS có
80rows ở4trang đầu nhưng footerbáo85; trang5 trảHTTP200/emptylist/body33bytes,
nên parser STOP vì count/list mismatch. Đây không phảiuserpause,không tựresume.
GiữZIP/checkpoint/output;không sửastatus/xóa lock hoặc đổiIP để replay.

Bước tiếp đềxuất:prepare recovery versionmới reuse575queries,giữ ORS80/85
source-count-gap HOLD riêng,tiếp tục497mã khác màkhông markORScomplete. Cần
scopedcontract/tests mới,không giảmlỏngfullquerygate;chưa build/run recovery này.
Review `data/corporate_actions/work/vsdc_recovery4s_stop_review_20261103_v4/`.
LệnhV4 phía dưới làlịchsử sauSTOP,không cólệnh tiếp tục mới ởstage review này.

## Lệnh hiện hành V4: recovery 4 giây cho 1.053 mã/53 batch còn lại

V4 giữ nguyên 20 query đã review (15 V3 +5 pilot), không tải lại. Chạy một lệnh
local cho toàn bộ 1.053 mã còn lại, bắt đầu proposed-003; Chrome chạy ẩn,
một worker, min4s giữa business request starts cả trang/mã. Không chạy kèm
V3/diagnostic/pilot hoặc một lượt V4 khác.

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_recovery4s_v4.py"
```

Terminal bắt đầu **20/1.073**, còn1.053. Batch numbering giữ gốc **2/54**:
batch1 đã đủ20query, còn53batch. Counter chỉ tăng sau query đủ trang/đóngcontext/
seal ZIP/reparse/validate. ETA xuất hiện sau5query V4 mới, không dùng tốc độ2s
của prefix cũ; chỉ làước tính. Logs human/JSONL và importedprefix nằm trong ZIP.

**Tạm dừng:** nhấn Ctrl+C một lần, chờ `OUTPUT_ZIP` rồi mới đóng terminal.
Hoặc chạy từ terminal khác:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_recovery4s_v4.py" --pause
```

Chỉ `PAUSED_BY_USER_VERIFIED_CHECKPOINT` cho tiếp tục bằng cùng lệnh đầu tiên.
Runner kiểm tra ancestor ZIP/hash/runtime/config/costs/progress rồi tạo run mới,
copy nguyên completed queries để bỏ qua. Query dở thu lại từ page1/context mới.
Giữ tất cả run cũ và preparation, không xóa/đổi tên output hoặc active.lock.
Source/error/crash/unsealed/stale lock cần review, không auto-retry/error-resume.
Nếu STOP hoặc BLOCKED, gửi thông báo và OUTPUT_ZIP nếu có.

Seed costs45business/1.155context/159,719sactive gồm cả failedAPP/diagnostic;
giữ cumulative caps global5.400/89.094/8hactive,batch100/1.660/20phútactive,
query20pages/400rows/98context/78assets/180s,operation15s/HTML2MB,max100segments.
Imported15query2s +5query4s giữ provenance riêng, không relabel thành4s.
Early safe diagnostics từng trang/source/TLS/privacy/access gates và original
fullhash giữ nguyên;không headedfallback/customidentity/detail/promotion.

```text
data/corporate_actions/work/vsdc_recovery4s_v4/run-<UTC>/state
data/corporate_actions/work/vsdc_recovery4s_v4/run-<UTC>/delta-vsdc-recovery4s.zip
```

Preparation `data/corporate_actions/work/vsdc_recovery4s_preparation_20261103_v4/`;
validation `data/corporate_actions/work/vsdc_recovery4s_validation_20261103_v4/`.
44 targeted tests (10 V4 mới), compileall/synthetic smoke PASS; 1.851 protected
files, imported prefix/costs được xác minh offline. Không cần chạy lại pilot.
Agent chỉ chuẩn bị offline, chưa chạy source/browser hoặc recovery. `--check`
chỉ kiểm tra offline. Scope7+418 ngoài lượt vẫn theo dõi; không đổi canonical/
owner/PIT/identity/history. Các lệnh V3/pilot phía dưới là lịch sử, không chạy lại.

**Bước tiếp theo:** user chạy V4 local, gửi OUTPUT_ZIP khi xong hoặc dừng/lỗi để
offline review coverage/cache/source. Pilot4s chưa bảo đảm ổn định cả lượt;
giữ bằng chứng khi có lỗi để xử lý, không tự bỏ mã thất bại.

## Trạng thái mới nhất: pilot 4s đã review PASS — chưa có lệnh recovery

Run `run-20261103T111211552864Z` đủ APP/APS/ARM/ART/ASG: 150 rows/11 pages,
11 HTTP 200; request starts cách 4,422–5,922 giây qua cả pages/tickers. ZIP/
runtime/receipts/reparse/progress review PASS, không ghi nhận access/error
markers. Tổng hợp với 15 checkpoint cũ đã có 20 query snapshots được review;
còn **1.053 mã/53 batches (proposed-003–055)** trong scope đã chọn.

Giữ output và không chạy lại các lệnh V3/diagnostic/pilot phía dưới. Bước tiếp
đề xuất là chuẩn bị recovery min4s dùng lại 20 query đã review, giữ source costs/
budgets và mixed2s/4s provenance, early diagnostics và verified pause. Stage
review chưa build/run recovery. Pilot nhỏ không xác định 2s là nguyên nhân cũ
hoặc bảo đảm ổn định toàn lượt. Review JSON tại
`data/corporate_actions/work/vsdc_five_query4s_live_review_20261103_v1/`.

## Lệnh hiện hành: pilot 5 mã đủ trang, min 4 giây

Chỉ APP, APS, ARM, ART, ASG — các mã pending tiếp theo sau 15 checkpoint V3.
Thu đủ các trang mỗi mã; inventory hiện có dự kiến 11 list requests/150 rows.
Chrome chạy ẩn, một worker, context/process mới cho từng mã. Min 4 giây giữa
business request starts áp dụng cả giữa các trang và các mã, không cộng thêm
4 giây sau mỗi response. Asset requests vẫn theo Chrome và source guards.

Chạy local **một lần**:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_five_query4s_pilot_v1.py"
```

Terminal/logs hiển thị 0/5→5/5 và trang đang hoàn tất. Counter chỉ tăng sau khi
query đã đủ trang, đóng context, seal ZIP và kiểm tra đạt. Chờ OUTPUT_ZIP, gửi
đường dẫn dù PASS hoặc STOP. Không chạy lại/xóa output để thử tiếp; pilot ngắn
không resume, CLI chặn existing run/concurrent/stale lock. Nếu chưa có ZIP hoặc
báo BLOCKED, giữ output/lock và gửi thông báo để review. `--check` chỉ offline.

Safe diagnostics từng trang lưu receipt/hash/size/cấu trúc/marker labels trước
DOM wait; không archive full response/DOM/cookie/token/HAR. Public fragments
chỉ lưu sau privacy/source/parser gates. Mọi source/access/layout/privacy/
integrity/budget/cleanup lỗi vẫn STOP, không retry/headed fallback/custom identity.
Caps global 30 business requests/490 context attempts/600 giây active; query
20 pages/400 rows/98 context attempts/78 assets/180 giây; operation 15 giây,
HTML 2 MB. Original hash checker và 15 checkpoint V3 giữ nguyên.

Self-review preparation PASS: 249 VSDC tests (11 mới), compileall/smoke/CLI offline,
1.630 protected files. Gói tại
`data/corporate_actions/work/vsdc_five_query4s_preparation_20261103_v1/`;
kiểm tra tại `data/corporate_actions/work/vsdc_five_query4s_validation_20261103_v1/`.
Agent chưa chạy source/browser hoặc recovery 1.058 mã.

**Bước tiếp theo:** user-run pilot, offline review pacing/coverage/source evidence;
nếu đạt mới đề xuất recovery ở 4s, dùng lại 15 checkpoint và pilot queries được
review đạt. Mẫu nhỏ này không chứng minh nguyên nhân lỗi 2s hoặc bảo đảm ổn định
cho toàn lượt. Các lệnh diagnostic/V3 bên dưới là lịch sử, không chạy lại.

## Trạng thái mới nhất: APP diagnostic đã review PASS — chờ recovery preparation

Run `run-20261103T104801448029Z` mở được APP: HTTP 200, selector xuất hiện,
trang đầu 20/43 rows, không thấy challenge/error markers; ZIP/runtime/fragment/
receipts review PASS. Lỗi cũ không tái hiện, nguyên nhân quá khứ chưa xác định.
Đây chỉ là trang đầu; APP chưa được credit hoàn tất, còn 1.058 full queries.

Không chạy lại diagnostic hoặc V3 cũ. Giữ output, 15 checkpoint V3 vẫn nguyên.
Bước tiếp theo đề xuất là chuẩn bị recovery version riêng dùng lại 15 query,
bắt đầu từ APP trang 1, giữ source gates và cumulative budgets, thêm early safe
diagnostics. Chưa có lệnh recovery ở stage này. Review tại
`data/corporate_actions/work/vsdc_app_diagnostic_live_review_20261103_v1/`.

## Lệnh hiện hành: chẩn đoán riêng APP một lần

Đã chuẩn bị pilot riêng để ghi nhận phản hồi trước khi chờ vùng kết quả bị lỗi.
Pilot chỉ mở trang đầu APP một lần bằng Chrome ẩn; chưa tiếp tục 54 batch và
không thay đổi 15 checkpoint đã đạt. Chạy local:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_app_diagnostic_v1.py"
```

Chờ OUTPUT_ZIP, gửi đường dẫn khi hoàn tất hoặc STOP. Pilot có thể STOP nếu
trang tiếp tục lỗi; evidence chẩn đoán vẫn được đóng ZIP khi xử lý lỗi bình thường.
Không chạy lại/xóa output để thử tiếp; CLI chặn lần chạy thứ hai. Nếu terminal
báo BLOCKED hoặc chưa có ZIP, giữ output/lock và gửi nguyên thông báo để review.
`--check` chỉ kiểm tra offline, không mở browser/gọi nguồn.

Giới hạn một business GET, 79 context attempts/78 assets, 180 giây active,
operation 15 giây, HTML 2 MB. Giữ source/TLS/privacy/access gates; không tự retry,
chuyển trang, tải detail hoặc đổi headed/profile/identity. Diagnostic lưu receipt,
hash/kích thước phản hồi, structural counts và marker labels cố định trước
selector; không lưu raw response/full DOM/title/text tùy ý hay cookie/token/HAR.
Chỉ public result fragment hợp lệ mới lưu như policy cũ. First page PASS không
có nghĩa toàn query hoàn tất; full-query completion credit luôn 0.

Self-review preparation PASS: 238 VSDC tests (14 mới), compileall/synthetic smoke,
CLI offline hai cwd, 1.587 protected files. Agent chưa mở browser/gọi nguồn.
Preparation ở `data/corporate_actions/work/vsdc_app_diagnostic_preparation_20261103_v1/`;
validation ở `data/corporate_actions/work/vsdc_app_diagnostic_validation_20261103_v1/`.

**Bước tiếp theo:** user-run pilot, offline review OUTPUT_ZIP rồi mới đề xuất
recovery dùng lại 15 checkpoint và giữ cumulative budgets. Probe mới có thể
không tái hiện lỗi cũ; hash/flags chỉ cung cấp bằng chứng giới hạn. Các lệnh V3
phía dưới vẫn bị STOP gate, chưa có lệnh recovery ở stage này.

## Trạng thái mới nhất: V3 đã STOP tại APP — chờ chẩn đoán

Run `run-20261103T102550498846Z` đã xác minh 15/1.073 mã, còn 1.058. APP trả
HTTP 200 nhưng thiếu vùng kết quả mà collector chờ trong 15 giây. Body lỗi chưa
được lưu nên chưa xác định trang lỗi/layout/challenge hoặc nguyên nhân khác.
Review ZIP/checkpoints PASS, giữ nguyên 15 query đã đạt. Đây là source/layout
STOP, **không phải user pause**; cùng lệnh V3 bên dưới sẽ từ chối chạy tiếp.
Giữ tất cả output, không sửa status/xóa run hoặc active.lock để chạy lại.

Bước tiếp theo đề xuất: pilot chẩn đoán APP riêng với safe response evidence;
sau review mới chuẩn bị recovery dùng lại 15 checkpoint và giữ cumulative budgets.
Chưa chuẩn bị recovery hoặc tự retry. Review JSON ở
`data/corporate_actions/work/vsdc_remaining54_headless_live_review_20261103_v1/`.

## Lệnh hiện hành V3: chạy 54 batch bằng Chrome ẩn, có tiến độ và tạm dừng/tiếp tục

Phạm vi proposed-002–055: **54 batch, 1.073 mã**, không chạy lại batch001/pilots.
Chrome chạy ẩn, một worker, giữ tối thiểu 2 giây giữa các request starts. Mỗi mã
dùng browser process/context mới; theo dõi qua terminal. Bảy mã large HOLD và
418 mã (414 archived-exhausted + 4 unverified) nằm ngoài lượt này, vẫn được giữ
trong inventory 1.522 mã.

Chạy lần đầu hoặc tiếp tục sau tạm dừng hợp lệ bằng cùng lệnh:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_remaining54_headless_v3.py"
```

Terminal hiển thị đã xong/tổng 1.073, phần trăm, số còn lại, mã/trang đang thu,
batch 1–54, thời gian chạy và ETA tạm tính. Batch 1 là proposed-002, batch 54 là
proposed-055. Số mã đã xong chỉ tăng sau khi query đủ trang, seal/reparse/validate
đạt. ETA xuất hiện sau 5 mã hoàn tất, dùng trung bình 20 query gần nhất trừ thời
gian query hiện tại; không tính thời gian người dùng nghỉ. Đây là ước tính, chưa
kiểm chứng thời gian chạy toàn lượt. Logs `progress.log`/`progress.jsonl` nằm
trong ZIP; đường dẫn được in ở OUTPUT_PROGRESS_LOG/OUTPUT_PROGRESS_JSONL.

**Tạm dừng:** nhấn Ctrl+C một lần, chờ thao tác browser hiện tại kết thúc/timeout,
lưu checkpoint và in OUTPUT_ZIP rồi mới đóng terminal. Hoặc từ terminal khác:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_remaining54_headless_v3.py" --pause
```

Chỉ status `PAUSED_BY_USER_VERIFIED_CHECKPOINT` cho chạy tiếp bằng cùng lệnh.
Runner xác minh toàn bộ predecessor ZIP/hash/runtime/config/costs/logs, tạo run
mới, copy nguyên query đã đạt và bỏ qua. Query dở thu lại từ trang 1 với context
mới. Giữ tất cả run cũ; không xóa/đổi tên output hoặc active.lock. Source/access/
layout/privacy/integrity/budget/disconnect/cleanup errors STOP cần review trước
khi xử lý tiếp. Gửi OUTPUT_ZIP kể cả partial/error. Crash, tắt nguồn, output chưa
seal hoặc stale lock cũng cần review. Không chạy đồng thời V1/V2/pilot hoặc hai
lượt V3; exclusive lock chặn hai lượt V3. V2 run đã có không tự import sang V3.

Caps cộng dồn qua pause, gồm partial attempts: global 5.400 business requests/
89.094 context attempts/8 giờ active; batch 100/1.660/20 phút active; query
20 trang/400 rows/98 context attempts/78 assets/180 giây; operation 15 giây,
HTML 2 MB, một worker, tối đa 100 segments. Min 2 giây áp dụng giữa các request
starts qua trang/mã/batch; không ngủ thêm 2 giây sau response. Source/API/
anti-bot/login/challenge/RetryAfter/TLS boundaries đều STOP. Giữ nguyên source
gates và original full SHA256 mỗi check; không tự retry hoặc đổi browser mode.

```text
data/corporate_actions/work/vsdc_remaining54_headless_v3/run-<UTC>/state
data/corporate_actions/work/vsdc_remaining54_headless_v3/run-<UTC>/delta-vsdc-headless54.zip
```

ZIP mới nhất chứa evidence của tất cả query đã đạt, query dở hiện tại và logs;
mỗi query có ZIP/manifest/validation riêng. Root ZIP được đóng gói sau acquisition
hoặc pause; chờ OUTPUT_ZIP trước khi đóng terminal. Copy evidence tránh tải lại
query đã đạt, đồng thời tốn thêm dung lượng qua các segments; giữ ancestors để
xác minh lineage. `--check` chỉ kiểm tra offline, không mở browser/gọi nguồn.
Preparation ở
`data/corporate_actions/work/vsdc_remaining54_headless_preparation_20261103_v3/`;
validation `data/corporate_actions/work/vsdc_remaining54_headless_validation_20261103_v3/`.

Self-review preparation PASS: 224 VSDC tests (23 mới), compileall/synthetic smoke,
CLI offline hai cwd, 1.125 protected files. Agent chưa chạy 54 batch; live V3
pause và sustained headless toàn lượt vẫn chờ xác minh. **Bước tiếp theo:** user
chạy lệnh local trên, gửi OUTPUT_ZIP khi xong hoặc dừng/lỗi để review coverage/
cache/source, rồi mới đề xuất detail acquisition và 7+418 mã riêng. List discovery
không approve owner/canonical/PIT/identity/full-history. Các lệnh V2/pilot phía
dưới là lịch sử; dùng lệnh V3 ở đầu tài liệu cho lượt hiện hành.

## Headless/progress pilot đã review PASS — bước tiếp là chuẩn bị54batch chạyẩn

Run `run-20261103T093821365887Z` đủA32/AAA/IDJ35/51/24rows,cùngdata/JS/cache với
headedbaseline,7HTTP200,no sourceerrors. Frozenlaunch/runtime/browserreceipts xác
nhậnheadlessTrue,mộtChrome/3freshclosedcontexts. Log22events hiểnthịđúng0/3→1/3→
2/3→3/3,percent/remaining/ticker/page/FINALstatus;counter khôngtăng khiquerycònthu.
ZIP56members/55hashes/protected1040/receipt/12tests/compileall PASS.Review:
`data/corporate_actions/work/vsdc_headless_progress2s_live_review_20261103_v1/`.

ETA hiệnđúng côngthức nhưngdaođộng/tăngkhiqueryđangchạy,mẫu3mãkhôngđủđểdựbáo
1073mã. Bản54batch cầnwarmup đủcompletedqueries vàổnđịnhETA theoquerydurations.
Acquisition17.359s,profile20.094s gồm preflight,ZIP1.047s bênngoài;khôngclaim speedup
hoặc gộpwindow nhưsameCLIwalltime. Pilot đãxong,không chạy lại/xóaoutput.

Bước tiếpđềxuất:prepare bản54batch headless/progress mới,min2s,checkpoint/tạmdừng/
tiếptục nhưV2. Bản54chạyẩn chưađượcbuild/chạyởstage review này. Lệnh headedV2
bên dưới vẫn làlịchsử/currentheadedrunner,khôngtựbiến thànhheadless. Agentkhông
gọi nguồn/browsers hoặcđổi progress/cache/owner/canonical/PIT/identity/history;
scope1073mã/7+418ngoài lượt vẫn giữ nguyên.

## Headless/progress pilot lịch sử:đã chạy vàreview

Đây làphép thử3mã A32/AAA/IDJ, chưa chạy54batch. Chrome headless không hiện cửa
sổ; mộtprocess/ba phiên sạch riêng,một worker,giữ2s vàoriginalhash/sourcechecks.
Chưa kếtluận nguồn chấpnhậnheadless trước pilot. Không chạyđồngthời chain/pilotkhác;
nếu54V2 đangchạy hãypause vàchờ thoát/lưuZIP trước,không xóa lock.

Chạy đúng một lần local:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_headless_progress2s_pilot_v1.py"
```

Terminal in completed/total,phầntrăm,cònbao nhiêumã,mã/trang đangthu,batch,elapsed
vàETA tạmtính. Ví dụminhhọa sau mãđầu đạt:

```text
[1/3 mã | 33.3% | Còn 2] Đã kiểm tra mã A32 | Batch 1/1 | Đã chạy 00:00:05 | ETA tạm tính 00:00:10
```

Sốliệuvídụ khôngphải kếtquảlive. Mã đangthu chưađược cộng;counter chỉtăng sau
fullquery checks/contextclose/completequery persist. PAGE_COMPLETE chỉlàtrangđã
kiểmtra. ETA từaverage elapsed/completed,đầu lượt ghi đangtính;không dùngETA3mã
đểước lượng1073mã. Lượt nàybatch1/1,total3. Chỉ saupilotPASSmới prepare bản54batch
cùng tiếnđộvàpause/continuation. 100%query vẫn cóthểFINAL STOP nếucleanup lỗi.

Logs `progress.log` và `progress.jsonl` nằm trongstate vàZIP. Console in
OUTPUT_PROGRESS_LOG/OUTPUT_PROGRESS_JSONL đểxem lại;theodõi terminal thayvìChrome.
Kết thúcsource còn bướcđónggói;chờ OUTPUT_ZIP trước khiđóng terminal. Gửi OUTPUT_ZIP
và OUTPUT_PACKAGING_TIMINGS kểcảpartial/error;không cần gửilog riêng vìZIP đãcó.

```text
data/corporate_actions/work/vsdc_headless_progress2s_pilot_v1/run-<UTC>/state
data/corporate_actions/work/vsdc_headless_progress2s_pilot_v1/delta-vsdc-headless-progress2s-<UTC>.zip
data/corporate_actions/work/vsdc_headless_progress2s_pilot_v1/delta-vsdc-headless-progress2s-<UTC>.packaging.json
```

Caps12business/246context-global,4pages/82context/78assets-query,operation15s/
query90s/run240s/HTML2MB,min2s sharedstarts/oneworker. DefaultheadlessChromeidentity/
strictTLS/freshnonpersistentcontexts,noauth/cookie/profile import-export/customUA/
headers/proxy/directPOST/replay. Nếuheadless bị403/challenge/429/RetryAfter/TLS/
layout/privacy/budget/cleanup lỗi thìSTOP,không headedfallback/login/giảidentity/
retry/ratefallback. Khôngrerun/xóaoutput. Pilotngắn Ctrl+C giữpartial/noresume;
V2 hiệncó vẫn cópause/continuation. `--check` chỉoffline,không mởbrowser.

Preparation `data/corporate_actions/work/vsdc_headless_progress2s_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_headless_progress2s_validation_20261103_v1/`.
Preparation self-review PASS:201 VSDC tests (12 mới),compileall/smoke/CLI check từ
hai cwd,1040protectedoldfiles giữ nguyên. Mock tests kiểmtraheadlessTrue/noheaded
fallback,22progress events/15hashcallbacks,ETA/logs/counter vàerrorstatus;chưa
thực hiệnliveheadlessaccess,không dùngmock thaychosource gate.
Stage chưa gọiVSDC/mởbrowser. Bước tiếp:reviewheadlessaccess/data/progress,từđó
prepare54batch headless/progress/pausecontinuation nếuđạt. Source/history/PIT/
identity/owner/canonical/progress vàscope7+418 ngoài lượt giữnguyên.

## Full-hash pilot đã review — đề xuất bắt đầu54batch V2 hiện có

Run `run-20261103T091151545258Z` đủA32/AAA/IDJ35/51/24,cùngdata/JS/cache,7HTTP200,
không sourceboundaries. OneChrome/3freshclosedcontexts,compile1lần/15fullhashchecks
960files. Same-set2pairscalibration0.1715→0.1485s (~13.41%) chohash,cònacquisition
chỉ15.531→15.328s,tiếtkiệm0.203s/~1.31%. Chưa cóend-to-endgain đángkể;không
ngoại suy39%offlinebenchmark sangtotalcollection hoặcactualETA.

Review `data/corporate_actions/work/vsdc_fasthash2s_live_review_20261103_v1/`:
ZIP55members/54payloadhashes/protected960/runtime/packagingreceipt và8tests/
compileall PASS. Profile17.734s gồm preflight/compile/calibration;ZIP0.578s bênngoài,
subtotal18.312s,chưa phải entireCLIwalltime vàkhông cùng acquisitionwindow15.328s.
Khôngrerun/xóaoutput pilot. V2/frozencheckpoints/owner/PIT/identity/progress khôngđổi.

Bước tiếp đềxuất:dùnglệnh54-batch V2 cópause/continuation ởmục V2 bên dưới,
giữ2s;không cần thêm cácpilot nhỏ hoặc migrate hash/browser chỉvìsample này.
Stage review không tựchạy54batch hoặc chuẩn bịbulkversion mới. Scope vẫn1073mã,
7largeHOLD và414+4 ởngoài;chưa tải detail hoặcapprove canonical/history.

## Full-hash pilot lịch sử:đã chạy vàreview

Mục tiêu là đo thời gian thực tế sau khi thay cách kiểm tra hash, chưa chạy54batch.
Pilot A32/AAA/IDJ dự kiến7requests danh sách, một Chrome/ba phiên sạch tuần tự như
pilot vừa review. Vẫn fullread/SHA256 mỗi file mỗi check; không cache/dedup hoặc bỏ
checks. Interval vẫn2s, không đổi54-batch V2 hay checkpoint cũ.

Chạy đúng một lần local, không chạy đồng thời chain/pilot khác:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_fasthash2s_pilot_v1.py"
```

Script kiểm tra offline trước, compile hash plan rồi đo đối chứng hash cũ/mới2pairs
AB/BA trên cùng tập file, sau đó mới mở Chrome lấy danh sách. Phần đối chứng không
gọi nguồn. Để Chrome riêng tự thao tác; không click/login/giải challenge. Default
visible Chrome/strictTLS/fresh nonpersistent contexts, không import/export auth/
cookie/profile hoặc customUA/headers/proxy/directPOST/session replay.

Caps vẫn12business/246context-global,4pages/82context/78assets-query,operation15s/
query90s/run240s/HTML2MB,một worker. Min2s giữa starts qua page/mã, pace remaining
delay. Hash/calibration/source/access/layout/privacy/budget/disconnect/cleanup lỗi
dừng cả pilot, không retry/reference fallback/relaunch/rate fallback/resume. Gửi
OUTPUT_ZIP kể cảpartial/error; không chạy lại/xóaoutput/force. Đây làshort pilot
không resume; `--check` chỉoffline, không mởbrowser hoặc chạycalibration.

Console in OUTPUT_STATE,OUTPUT_ZIP vàOUTPUT_PACKAGING_TIMINGS. ZIP chứa
`hash_calibration.json`, `timings.json`, full-hash counters và public evidence.
Acquisitionelapsed so với shared2s15.531s, không gồm preflight/compile/calibration;
profileelapsed rộng hơn, packagingreceipt cạnhZIP đo seal/hash/ZIP riêng. Gửi cả
path OUTPUT_PACKAGING_TIMINGS đểreview phần đóng gói; receipt không nằm trong ZIP
đang được đo và không tính thời gian hash ZIP đểviết chínhreceipt.

```text
data/corporate_actions/work/vsdc_fasthash2s_pilot_v1/run-<UTC>/state
data/corporate_actions/work/vsdc_fasthash2s_pilot_v1/delta-vsdc-fasthash2s-<UTC>.zip
data/corporate_actions/work/vsdc_fasthash2s_pilot_v1/delta-vsdc-fasthash2s-<UTC>.packaging.json
```

New protected set có thêm evidence; same-set calibration giúp so localhashcost,
nhưng source baseline còn historical/unpaired. Chưa hứa39% giảm totalcollection.
Preparation: `data/corporate_actions/work/vsdc_fasthash2s_preparation_20261103_v1/`;
validation: `data/corporate_actions/work/vsdc_fasthash2s_validation_20261103_v1/`.
Preparation self-review PASS:189 VSDC tests (8 mới),compileall/smoke/CLI check từ
hai cwd;960protectedoldfiles giữ nguyên,compiledchecker verify offline đầy đủ.
Fixtures xác nhận compile1lần/15callbacks,mutation stop trước request tiếp theo,
calibration failure không fallback vàsame parsed data;chưa live sourcepilot.
Bước tiếp: offline review ZIP/data/calibration/timing trước đề xuất version54batch.
Stagepreparation chưa gọiVSDC/mởbrowser; progress/cache/owner/canonical/PIT/identity/
history vàscope7+418 ngoài lượt không thay đổi.

## Offline hash optimization đã chạy — chưa đổi lệnh acquisition V2

Stageoffline đãthử cách compileđườngdẫn/expectedhash,giảm lặp Path/is_file nhưng
vẫn mở/đọc/toànfile SHA256 mỗi lần. Không cachebytes/digest/size/mtime,không bỏ
filetrùnghash hoặcgiảm sốcheck. Trên protected765/864files,8pairedroundsAB/BA
warmcache cho median0.293→0.179s và0.325→0.198s,giảm khoảng39% riêng hashcheck;
candidate nhanh hơn8/8pairs cả2cohort. Compiler cost/fineprofile ghi riêng.

Đãtest phát hiện sửa bytes dù giữsize+mtime,atomicreplace,lastbyte/delete/append/
truncate/type/unreadable file,duplicatehashfiles vàfullread mỗicheck. Chỉmutate
temporaryfixtures;old evidence/source/runtime giữ nguyên. Agentkhông mởbrowser/
gọiVSDC. Benchmark cóoutput nênkhông chạy lại đểghiđè:
`data/corporate_actions/work/vsdc_hash_fastpath_offline_benchmark_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_hash_fastpath_offline_validation_20261103_v1/`.
Self-review PASS:181 VSDC tests (12 mới),compileall/synthetic smoke;864oldfiles và
V2/2s/1s/shared runtime/manifests/tests/C8/owner/MBS proposal bất biến. Candidate
chỉoffline-only,không được collector hiệncó import hoặc chạy trongsourceguard.

Đây chưa phải39% giảm thời gianthu thập;interval2s cóthể hấp thụlocalCPU savings.
Candidate chưađược tíchhợp vào54batch,pause/checkpoint/ZIP/sourcepolicy khôngđổi;
lệnhV2 ởdưới vẫn làlệnh hiệncó. Bước tiếpđềxuất:prepare pilot riêng cócandidate
hash ởsame2s vàtiming,review end-to-end trướcđổi bulkversion. Stageoffline dừng
ởevidence;không cólệnhsource mới hoặccredit progress/detail/owner/PIT/identity.

## Shared-Chrome pilot đã review — đúng dữ liệu, chưa nhanh hơn

Run `run-20261103T084428264720Z`:mộtChrome/3freshclosedcontexts,đủA32/AAA/IDJ
35/51/24rows,cùngJS/cache/data với2s,7business200,no sourceerrors. Acquisition
15.531s so với2sbaseline15.235s,chênh+0.296s/~1.94%;mẫu chưa cho thấy speedup.
Historicalcomparison chưa paired,khác profiler/protectedset/system/network nên
không kết luận shareChrome làm chậm nói chung. Không rerun/xóaoutput pilot.

Timing đã kiểm tra:pacing8.171s;15protectedhash calls3.313s;pagecalls exclusive
2.499s;lifecycle1.297s. Profile17.031s gồm preflight/setup,khác acquisitionelapsed;
ZIPseal/hash0.516s ởpackagingreceipt bênngoài. Profile+ZIP17.547s làsubtotal,
chưa gồm toàn bộstartup/receipt hashing/terminal walltime. ZIP54members/53hashes/
protected864/receipt hashes/13tests/compileall PASS.Review:
`data/corporate_actions/work/vsdc_shared_browser2s_live_review_20261103_v1/`.

54-batch V2 vẫn nguyên2s/pause/continuation,lệnh ởmục V2 dưới đây. Chưa áp shared
browser từpilot nhỏ. Nếu cần tốiưu tiếp,bước đề xuất làoffline profiling/hash
optimization cókiểm thửequivalence/phát hiệnartifact bịsửa;không tự bỏ hashgates.
Giảm hashwork có thể tăng remaining2s wait,chưa hứa tiết kiệm3.313s/3mã.
Stage review không chạy nguồn hoặc sửa bulk version;progress/cache/owner/PIT/
identity/history và7+418scope giữ nguyên.

## Shared-Chrome pilot lịch sử:đã chạy vàreview

Pilot riêngA32/AAA/IDJ,dự kiến7request lấy danh sách. MởChrome một lần,tạo phiên
sạch riêng cho mỗi mã vàđóng phiên cũ trước chuyển mã;không dùngprofile/cookie/
cache/storage của phiên trước. Khoảng nghỉ vẫn2s,một worker,các hash/source/ZIP
checks giữ nguyên. Chưa thay54-batch V2. Không chạy đồng thời vớichain hoặcpilot
khác;nếuchain đang chạy hãy pause/chờ thoát sạch trước. Không xóa stale lock.

User chạy đúng một lần local:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_shared_browser2s_pilot_v1.py"
```

ĐểChrome riêng tự thao tác,không click/login/giải challenge. Default visibleChrome/
strictTLS/fresh nonpersistent contexts;không cookie/token/profile/auth import-export,
customheaders/UA/proxy hoặc directPOST/replay. Caps12business/246context-global,
4pages/82context/78assets-query,operation15s/query90s/run240s/HTML2MB. Min2s áp
dụng giữa request starts qua cảpage/mã,không ngủ thêm2s sauresponse. Source/access/
layout/privacy/budget/disconnect/cleanup errors STOP toànpilot,no retry/relaunch/
resume/fallback. Gửi OUTPUT_ZIP kể cảpartial/error;không chạy lại/xóaoutput.

Console in OUTPUT_STATE,OUTPUT_ZIP vàOUTPUT_PACKAGING_TIMINGS. ZIP có
`timings.json`:thời gian preflight,hash,mởbrowser/phiên,tảipage1/next,pacing,
parse/lưu evidence vàcleanup. Inclusive spans có thể chứa nhau;dùng exclusive sums
để cộng thời gian. Browser calls gồm network/render/guard work,không tách riêng
server latency. Acquisition elapsed so với2s baseline15.235s;timings elapsed còn
gồm preflight/setup nên không so hai window như cùng đại lượng.

ĐóngZIP cuối lượt được đo trong `.packaging.json` cạnhZIP,ngoài sealed state,kèm
ZIP/state hashes. Gửi cảpath OUTPUT_PACKAGING_TIMINGS đểreview;duration này
không nằm trong chínhZIP đang đo vàkhông bao gồm hash đọcZIP đểviết receipt.

```text
data/corporate_actions/work/vsdc_shared_browser2s_pilot_v1/run-<UTC>/state
data/corporate_actions/work/vsdc_shared_browser2s_pilot_v1/delta-vsdc-shared-browser2s-<UTC>.zip
data/corporate_actions/work/vsdc_shared_browser2s_pilot_v1/delta-vsdc-shared-browser2s-<UTC>.packaging.json
```

`--check` chỉoffline,không mởbrowser. Đây làshort pilot khôngresume;Ctrl+C tạo
partial review thay vì resume. Chưa biết sẽnhanh hơnbao nhiêu,historicalbaseline
khác protectedset/system/networkload. Repeat không credit/query/detail/owner/
canonical/PIT/identity/history. Preparation/validation:
`data/corporate_actions/work/vsdc_shared_browser2s_preparation_20261103_v1/` và
`data/corporate_actions/work/vsdc_shared_browser2s_validation_20261103_v1/`.
Preparation self-review PASS:169 VSDC tests (13 mới),gồm actual driver lifecycle
với mocked Playwright,one launch/three fresh contexts,no relaunch/cleanup failures,
same parsed data vàtiming accounting;compileall/smoke/CLI check từ hai cwd đạt.
Protected864 old files/C8/owner/MBS bất biến;chưa dùng live browser/source.
Bước tiếp:review ZIP/isolation/timings so2s trước đềxuất version54batch tốiưu;
không tự tốiưu hash/ZIP hoặc thu7+418 ngoài scope trongpilot này.

## Pilot1s đã review xong — không chạy lại;đề xuất dùng V2 ở2s

Run `run-20261103T082730656572Z` đủA32/AAA/IDJ35/51/24rows, cùng parsed data/IDs/
titles/JS/cache với2s,7business200,không source errors. Thời gian15.235s→14.719s,
chỉ nhanh hơn0.516s/~3.39%. Actualintervals1.265–4.093s:minimum1s không đồng nghĩa
mỗi request thực tế cách đúng1s hoặc lượt dài nhanh gấp đôi. Chưa phân rã browser/
network/render/integrity overhead. ZIP53members/52hashes/protected788 và11tests/
compileall PASS;agent không gọi nguồn hoặc đổi code. Evidence:
`data/corporate_actions/work/vsdc_three_query_speed1s_live_review_20261103_v1/`.

Đề xuất bước tiếp:chạy54batch bằng lệnh V2 cópause/continuation ởmục bên dưới,
giữ2s. Lệnh1s bên dưới là lịch sử, không rerun/xóaoutput. Chưa áp1s cho bulk hoặc
thử thấp hơn;sample không tăng progress/cache hay approval owner/canonical/PIT/
identity/history. Nếu cần tối ưu tiếp,review timing của lượt thực tế trước.

## Pilot1s lịch sử:đã chạy vàreview

Pilot riêngA32/AAA/IDJ, dự kiến7request lấy danh sách, để so với reviewed2s15.235s.
Chưa đổi54batch V2 đang dùng2s. Không chạy pilot đồng thời54batch; nếu54batch đang
chạy, chủ động pause và chờ lưu ZIP/thoát trước. Active/uncleanchain lock chặn pilot.

Chạy đúng một lần local:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_three_query_speed1s_pilot_v1.py"
```

Khoảng nghỉ tối thiểu1s giữa business starts, shared qua page/mã, chỉ chờ remaining
delay, không cộng thêm1s sauresponse. Caps giữ nguyên:4pages/query/12business-global,
82context-query/78assets-query/246context-global,operation15s/query90s/run240s/
HTML2MB,một worker. Visible Chrome riêng/fresh ephemeral session/default identity/
strict TLS; không click/login/giải challenge, không export/import profile/cookie/
token/auth hoặc customUA/headers/proxy/session replay. Pilot ngắn không có resume.

HTTP/access/redirect/challenge/Retry-After/TLS/transport/layout/budget lỗi STOP
cả pilot; không tự retry/fallback2s hoặc thayinterval. Gửi OUTPUT_ZIP kể cả partial/
error; không rerun/xóaoutput/force. `--check` chỉ offline, không mở browser.
Public rendered fragments/parsed pages/safe ledgers/hash-only HTTP bodies lưu vào:

```text
data/corporate_actions/work/vsdc_three_query_speed1s_pilot_v1/run-<UTC>/state
data/corporate_actions/work/vsdc_three_query_speed1s_pilot_v1/delta-vsdc-three-query-speed1s-<UTC>.zip
```

Đủ3query consistent/7business200/no source boundaries vàinterval>=1s mới đạt
gate mẫu. Review offline so pages/IDs/titles/cache/JS/ledgers/timing với2s trước
khi đề xuất bulk-rate version mới. Không guarantee2x tốc độ hoặc sustained1s;
không auto-promote1s cho54batch/checkpoints hiện có. Repeat không tăng coverage
hoặc detail-cache, không thay owner/canonical/PIT/identity/history gates.

Preparation: `data/corporate_actions/work/vsdc_three_query_speed1s_preparation_20261103_v1/`;
validation: `data/corporate_actions/work/vsdc_three_query_speed1s_validation_20261103_v1/`.
Self-review preparation PASS:156 VSDC tests (11 mới, gồm1s allowed/0.999s refused,
shared interval vàsame mock data với2s), compileall/smoke/CLI check từ hai cwd;
pin788 old files. Chưa chạy thử nguồn1s, không dùng mock làm live-speed evidence.
Bước tiếp là user-run pilot một lần vàreview ZIP so với2s;54batch vẫn2s đến khi
có evidence/review vàversion mới. Chưa thu nhóm7+418 ngoài scope.

## Lệnh hiện hành V2: chạy54 batch, có thể tạm dừng và tiếp tục

Chỉ discovery danh sách cho batch002–055/1.073 mã; batch001 đã đạt không chạy lại.
7 mã large HOLD và418 mã (414 archived-exhausted +4unverified) nằm ngoài scope này.
Chưa tải detail, chưa chứng nhận đủ lịch sử hoặc approve canonical/owner/PIT/identity.

Chạy lần đầu hoặc tiếp tục sau khi chủ động tạm dừng bằng cùng một lệnh:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_remaining54_resumable_v2.py"
```

Để tạm dừng: nhấn Ctrl+C một lần, chờ chương trình lưu checkpoint/ZIP và in
OUTPUT_ZIP rồi mới đóng terminal. Ctrl+C là yêu cầu cooperative pause; có thể
phải chờ browser operation hiện tại kết thúc hoặc timeout. Nếu browser/source
phát lỗi trong lúc chờ thì status vẫn STOP, không trở thành pause có thể resume.
Hoặc mở terminal thứ hai, gửi yêu cầu dừng:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_remaining54_resumable_v2.py" --pause
```

Chỉ khi kết quả là `PAUSED_BY_USER_VERIFIED_CHECKPOINT` mới được chạy tiếp cùng
lệnh. Runner xác minh toàn bộ predecessor evidence/runtime/ZIP/lineage và costs,
tạo run mới, bỏ qua query đã hoàn tất kể cả trong batch chưa xong. Query dở thu
lại từ trang1 trong fresh browser, không ghép pages cũ. Giữ tất cả run cũ; không
xóa/đổi tên output/lock hoặc tự sửa config. Có exclusive lock chống chạy hai lượt.

Source/HTTP/access/layout/privacy/integrity/budget STOP không cho tự chạy lại;
gửi OUTPUT_ZIP để review. Mất điện/đóng cưỡng bức có thể chưa seal ZIP hoặc để stale
active.lock; trường hợp đó cũng cần review, chưa có tự động phục hồi sau crash.
Không login/click/giải challenge trong Chrome riêng của script. Giữ máy thức.

Min2s giữa request starts, một worker; cap global5.400business/89.094context/8h
active và mỗi batch100business/1.660context/20phút active cộng dồn cả partial
attempts qua các lần pause. User off-time không tính; tối đa100segments. Query
20pages/400rows/98context/78assets/180s, operation15s/HTML2MB. TLS strict/default
Chrome/fresh sessions; không cookie/token/profile/auth export/import hay replay.

Mỗi run có `state/` và `delta-vsdc-resumable54.zip` dưới
`data/corporate_actions/work/vsdc_remaining54_resumable_v2/run-<UTC>/`.
ZIP mới tự chứa evidence của tất cả query đã đạt cùng partial query trong lượt;
copy lại artifacts để không tải nguồn lại, do đó tốn thêm dung lượng qua mỗi pause.
`--check` chỉ kiểm tra offline, không mở browser. V1 bên dưới là lịch sử; dùng lệnh
V2 ở trên. Chưa chạy acquisition trong stage preparation này.

Preparation self-review PASS:145 VSDC tests (15 mới), có mô phỏng đủ54 batch,
multi-pause/continuation, partial-query restart, source-error/tampering/crash locks,
cumulative budgets; compileall/smoke/CLI check từ hai cwd đạt. Pin765 old files;
V1/C8/owner/MBS proposal bất biến. Live pause/continuation chưa thực hiện.
Evidence: `data/corporate_actions/work/vsdc_remaining54_resumable_validation_20261103_v2/`.

Bước tiếp: user chạy local, gửi OUTPUT_ZIP khi cần review hoặc khi hoàn tất54
batch; agent review coverage/cache/source toàn lượt rồi đề xuất detail và nhóm7+418
riêng. Không tự tiếp tục sang stage thu nhóm ngoài scope.

## V1 đã được V2 thay thế:54 batch không hỗ trợ resume

Theo đính chính mới nhất: chạy proposed-002–055, tổng54 batch/1.073 mã. Không
giới hạn11 batch. Batch001 đã review, không chạy lại. Đây là phần discovery
danh sách còn nằm trong các batch thông thường, không phải tải mọi bài chi tiết
hoặc chứng nhận đủ lịch sử toàn1.522 mã. Bảy large-query HOLD vẫn xử lý riêng;
414 archived-exhausted và4 unverified vẫn được theo dõi.

Chạy đúng một lần trên terminal local:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_remaining54_chain_v1.py"
```

Giữ máy thức và terminal mở; để cửa sổ Chrome riêng tự thao tác, không login/click
hoặc giải challenge. Min2s giữa các request lấy danh sách, shared qua pages/mã/batch,
không phải2s/mã. Ước lượng cũ2.839 requests chỉ riêng pacing đã khoảng95phút;
Chrome, tải trang và kiểm tra ZIP làm thời gian thực dài hơn, không có ETA bảo đảm.
Script tự nối batch sau khi kiểm tra batch trước; không cần nhập lệnh mỗi20 mã.

Mỗi batch có immutable state, ZIP và automated validation. Console in BATCH_START/
BATCH_VALIDATED; cuối lượt in OUTPUT_STATE/OUTPUT_BATCH_ZIPS/OUTPUT_ZIP. ZIP tổng
đã chứa public fragments, receipts, parsed pages, ledger, manifests và validation
của các batch; không cần gửi54 ZIP riêng. Bất kỳ lỗi nguồn/access/layout/privacy/
integrity/budget đều STOP cả lượt và giữ partial output. Gửi OUTPUT_ZIP kể cả lỗi;
không chạy lại/xóa output hoặc force/resume. Không tự đổi interval hoặc fallback.

```text
data/corporate_actions/work/vsdc_remaining54_chain_v1/run-<UTC>/state
data/corporate_actions/work/vsdc_remaining54_chain_v1/run-<UTC>/batch_zips
data/corporate_actions/work/vsdc_remaining54_chain_v1/delta-vsdc-remaining54-chain-<UTC>.zip
```

Caps: global5.400business/89.094context/8h; mỗi batch100business/1.660context/20phút;
query20pages/400rows/98context/78assets/180s, operation15s/HTML2MB; một worker.
Context caps tính browser request attempts, không đồng nghĩa packet/bandwidth.
Default Chrome identity/strict TLS/fresh ephemeral sessions; không export/import
cookies/token/auth/profile, không custom UA/headers, không direct POST/session replay.
`--check` chỉ kiểm tra offline, không mở browser. Acquisition do user chạy local.

Preparation self-review PASS:130 VSDC tests (13 mới, có mô phỏng đủ54 batch),
compileall/synthetic smoke/CLI check từ project và working directory khác. Pin743
old files/runtime/manifests; C8 securities/owner/MBS proposal không thay đổi.
Evidence: `data/corporate_actions/work/vsdc_remaining54_chain_validation_20261103_v1/`.

Baseline detail-cache27731 và known-list28276 riêng biệt. Cross-batch dedup giữ
mọi title/query membership; discovery mới không tự thành downloaded detail/event
identity. Canonical/owner/PIT/identity/history gates giữ nguyên. Nếu chạy hết và
review đạt thì nhóm pending thông thường mới được cập nhật; chưa credit trước run.
Bước tiếp: review ZIP offline, đối chiếu source/cache/coverage toàn lượt, sau đó
đề xuất thu detail bổ sung. Stage preparation dừng tại đây. Các lệnh/đề xuất11 batch
hoặc pilots bên dưới là lịch sử, không phải lệnh hiện hành.

## Speed2s đã chạy vàreview PASS — không chạy lại

Run `run-20261103T072216826201Z`:A32/AAA/IDJ35/51/24,cùng parsed data/cache với4s,
7business200.Observed intervals2.172–2.297s,elapsed15.235s vs28.328s(~46.22% lower),
same context/assets/block counts.No source boundaries/errors. Đây là small-sample
evidence,không certify long220-query sustained rate hoặc2x speed.Evidence:
`data/corporate_actions/work/vsdc_three_query_speed2s_live_review_20261103_v1/`.
ZIP CRC/53members/52hashes/protected673,10tests/compileall PASS.

Lệnh2s bên dưới là lịch sử,không rerun/xóaoutput để vượtguard.Same-query repeat
không new progress:pending1080/24reviewed snapshots/414+4tracked/7HOLD,catalog27731
details/28276known-list không đổi.50candidate links đã biết,no first-discovered IDs.
Bước tiếp đề xuất:prepare one exact11-batch local chain proposed002..012,220queries,
min2s/per-batch validation/checkpoints/ZIP,whole-run STOP,no retries/rate fallback/
details hoặc tựchạy54remaining batches.Chưa cólệnh11batch trongstage review này.

## Thử2 giây trên A32/AAA/IDJ — user-run một lần trước11batch

Đã chuẩn bị version riêng,chưa gọi nguồn. Chỉ giảm minimum giữa business starts
4→2s,trên cùng3 query đã complete để so sánh tốc độ. Không giảm pending1080,không
chạy11batch hoặc tải bài chi tiết trong pilot. Chrome/Playwright hiện đã có.

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_three_query_speed2s_pilot_v1.py"
```

Chạy đúng một lần,để Chrome riêng tự thao tác,không login/click/solve challenge.
Default browser identity/ephemeral public session/strict TLS,no cookie/profile/token/
auth import/export hoặc custom headers/UA/proxy.Minimum2s shared pages/tickers;
không2s/mã hoặc extra2s sauresponse. Max4pages/query/12business-global,82context-
query/78assets-query/246context-global,operation15s/query90s/run240s/HTML2MB,1worker.
Caps giữ nguyên;context attempts không low-level packets/assets bandwidth guarantee.

HTTP/access/redirect/challenge/Retry-After/TLS/transport/layout/budget lỗi STOP cả
lượt,no retry/interval negotiation/fallback4s or8s. Gửi OUTPUT_ZIP cảpartial/error;
không rerun/xóaoutput hoặc force/resume. Safe metadata/public rendered fragments và
hash-only HTTP bodies,không raw full HTTP/cookie/HAR/profile. Pin baseline4s28.328s/
7business/rows35-51-24 vàlatest known-list28276/detail-cache27731,không event approval.

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_three_query_speed2s_pilot_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_three_query_speed2s_pilot_v1\delta-vsdc-three-query-speed2s-<UTC>.zip
```

`--check` chỉoffline,no browser/network.171 targeted tests(10 mới),compileall/smoke/
CLI check PASS,protect673 old files. Preparation:
`data/corporate_actions/work/vsdc_three_query_speed2s_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_three_query_speed2s_validation_20261103_v1/`.
Bước tiếp:review ZIP vàtimings/data/source failures trước chọninterval vàprepare
runner11batch.Phương án11batch chưa cólệnh ởstage này,no guaranteed2x/sustained rate.

## Batch001 đã review PASS20 mã — không chạy lại

Run `run-20261103T065700177618Z` complete20 query lists,853 rows/unique IDs và54
business200.ACB đủ10pages,total/ranges/IDs nhất quán.Interval4.14–4.281s,elapsed
223.859s(~3m44s).400 IDs códetail cache,453 new candidate links chưa detail-fetched.
Không approve source terms/identity/PIT từ list.Updated overlay24 query snapshots
completed/pending1080;414archived-exhausted/4unverified/7largeHOLD giữ riêng.

Evidence `data/corporate_actions/work/vsdc_browser_batch001_live_review_20261103_v1/`.
ZIP CRC/336 members/335hashes/runtime/protected318 và41checkpoints PASS;14tests/
compileall PASS.No new source requests/browser launches từagent.Original batch
plan/run/parents bất biến.Lệnh bên dưới là lịch sử,không rerun/xóaoutput hoặc resume.

Known-discovery overlay28276 IDs,reusable-detail27731 IDs tách riêng,545 known
uncached candidates chưa được authorize tải.Năm mươi bốn proposed batches còn lại
chưa chạy được tự động.Bước tiếp đề xuất:prepare exactbatch0024s với latest known-
discovery/cache sets vàsame STOP/privacy,review sau run.Không có lệnhbatch002 trong
stage này,không auto-chain hoặc tải toàn bộ details.414refresh/check và4diagnostics
tiếp tụctracked trước any1522-wide completion claim.

## Batch001 fixed20 mã — local4s,chạy đúng một lần

Đã chuẩn bị runner cho AAM,ABB,ABC,ABI,ABR,ABT,ACB,ACC,ACE,ACL,ACM,ACV,ADC,ADP,
ADS,AFX,AGF,AGG,AGM,AGP. Chỉ đọc đủ danh sách thông báo của mỗi query trong fresh
browser session,đối chiếu cache/gom provider IDs;chưa tải bài chi tiết hoặc batch khác.
Archived estimate54 list requests,không phải54events hoặc54 guaranteed live count.

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_browser_batch001_v1.py"
```

Để Chrome riêng tự thao tác20 mã lần lượt;không tự login/click/solve challenge.Khi
xong script đóng browser.Cùng Playwright1.57/Chrome installed,default identity/TLS/
nonpersistent session,không cookie/profile/token import/export hoặc UA/header/proxy
workaround.Khoảng cách tối thiểu giữa business starts4s,chung pages/tickers;không4s/mã hoặc
sleep thêm4s sauresponse.54requests có lower-bound212s từstart đầu đếnstart cuối,
actual run có thêm browser/processing/source delays;không hứa thời gian cố định.

Caps100 business/global,20 pages/query(400rows),98 context attempts/query,78 assets/
query,1660 context/global,operation15s/query180s/run1200s,HTML2MB,1worker.Caps không
low-level physical packets/bandwidth guarantee.Unknown/ambiguous next button hoặc
changed total/duplicate/overlap/layout mismatch/source HTTP/redirect/Retry-After/
access/challenge/TLS/transport/timeout/budget errors STOP cảbatch.No retry/resume/
rate fallback hoặc tự chuyểnbatch002.Không xóa output để vượt rerun guard.

Snapshot mỗi trang,query-start/query-complete/final checkpoints,partial ZIP giữ
phần đã thu.Global dedup provider IDs giữ memberships/titles,cache27731 downloaded-
detail IDs tách known-discovery27823 IDs.Không gọi link mới là new verified events.
Rendered public fragments là evidence,full HTTP bodies chỉhash/size,không raw HTTP
archive/cookie/HAR/profile.New-detail fetch luônfalse;không áp giá MBS/canonical.

Gửi OUTPUT_ZIP cảkhi báo lỗi/partial,không chạy lại ngay:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_browser_batch001_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_browser_batch001_v1\delta-vsdc-browser-batch001-<UTC>.zip
```

`--check` chỉoffline,không mở browser/gọi nguồn.Không batch/ticker/force/resume/interval
override flags.161 targeted tests(14 batch),compileall/smoke/CLI check PASS,protect318
old files.Caps mới chưa live-test cho20 mã;pending1.100 giữ nguyên đếnreview.
Preparation `data/corporate_actions/work/vsdc_browser_batch001_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_browser_batch001_validation_20261103_v1/`.
Bước tiếp:review ZIP20query/cache/dedup/budgets trước query-completion credit và
batch tiếp.414 archived-exhausted/4unverified/7largeHOLD vẫn theo dõi riêng.

## Speed4s đã chạy/review PASS — không chạy lại

Run `run-20261103T063424932059Z` lấy đủ A32/AAA/IDJ35/51/24,cùng parsed pages/IDs/
titles/cache flags với reviewed8s baseline;7 business200. Observed intervals4.328–
4.422s,elapsed28.328s so với52.11s(~45.64% lower). Context/assets/block counts giữ
nguyên. Đây là sample comparison,không guaranteed2x hoặc long-run rate certification.
Evidence: `data/corporate_actions/work/vsdc_three_query_speed4s_live_review_20261103_v1/`.
ZIP CRC/52 members/51 hashes/protected250 PASS;10 tests/compileall PASS.

Lệnh4s dưới đây là lịch sử,không chạy lại/xóa output để vượt guard. Same-query repeat
không làm pending1.100 giảm;50 candidate links đã có trong8s run,0 details mới.414
archived-exhausted/4unverified/cache27.731/owner choices vẫn giữ nguyên.
Bước tiếp đề xuất:prepare first executable fixed-scope discovery batch4s,giữ same
STOP/cache/privacy và review mỗi local run. Chưa có lệnh batch mới;không tự chain55
proposed batches hoặc download details/approve MBS price.

## Thử interval4 giây: cùng A32/AAA/IDJ — chạy local đúng một lần

Đã chuẩn bị version riêng,chưa gọi nguồn. Chỉ giảm minimum giữa business request
starts8→4s,cả lúc chuyển mã; giữ nguyên mọi caps/source/privacy/STOP. Đây là speed
repeat trên3 query đã complete,không thu thêm mã mới hoặc giảm pending1.100.

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_three_query_speed4s_pilot_v1.py"
```

Chrome local mở riêng tuần tự,để script tự thao tác,không tự login/click hoặc solve
challenge. Fresh default browser identity/TLS/ephemeral session,không profile/cookie/
token/auth import/export hoặc custom headers/UA/proxy. Chỉ danh sách,max4 pages/query,
12 business/global,82 context attempts/query/78 assets/query/246 context/global,
operation15s/query90s/run240s/HTML2MB. Counts không low-level packets; assets thiếu
Content-Length không measured bandwidth cap. Pace=max(0,4-elapsed_since_last_start),
không sleep thêm4s sauresponse; các assets không chịu business interval.

Mọi HTTP/access/redirect/challenge/Retry-After/TLS/transport/layout/budget lỗi dừng
cả lượt,không retry hoặc auto fallback8s. Gửi OUTPUT_ZIP kể cả lỗi/partial,không
chạy lại hoặc xóa output để vượt guard;không interval/force/resume/fallback flags.

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_three_query_speed4s_pilot_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_three_query_speed4s_pilot_v1\delta-vsdc-three-query-speed4s-<UTC>.zip
```

ZIP giữ same public rendered fragments/safe metadata/timings/cache flags và experiment
baseline8s52.11s/7 business,không raw full HTTP/cookie/HAR/profile. Không hứa2x tốc độ;
fresh totals/assets/runtime có thể đổi. Cần review interval>=4s cùng source/layout và
so sánh before/after trước cân nhắc dùng4s cho batch. Bản8s và250 protected files
giữ nguyên,không new downloaded-detail IDs/price approval/canonical changes.

147 targeted tests(10 mới),compileall/smoke/CLI check PASS.`--check` chỉ offline,
không mở Chrome/gọi nguồn. Preparation:
`data/corporate_actions/work/vsdc_three_query_speed4s_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_three_query_speed4s_validation_20261103_v1/`.
Bước tiếp:review ZIP cả3 mã và timings,rồi mới chuẩn bị executable batch có interval
đã kiểm chứng; không tự chạy55 proposed batches hoặc tải bài chi tiết.

## Pilot A32/AAA/IDJ đã review PASS — không chạy lại

Run `run-20261103T061831245900Z` đã lấy đủ A32=35/35,AAA=51/51,IDJ=24/24;7 business
responses200.110 unique provider IDs,60 cached detail IDs và50 new candidate links,
không tải bài chi tiết. Live sample không có cross-query duplicate; reconstruction
giữ query memberships/titles/cache flags đúng,branch collision có offline tests.
Evidence: `data/corporate_actions/work/vsdc_three_query_browser_live_review_20261103_v1/`.
ZIP CRC/51 members/50 payload hashes/protected181 PASS;12 tests/compileall PASS.

Lệnh pilot dưới đây là lịch sử bàn giao,không chạy lại/xóa output để vượt guard.
Pagination pending còn1.100 sau4 reviewed snapshots(MBS/A32/AAA/IDJ).1.093 normal
queries vẫn trong55 proposed batches,7 large-scope HOLD.414 archived-exhausted và4
unverified vẫn được theo dõi riêng,không bị bỏ khỏi1.522 hoặc coi đủ event history.

Bước tiếp đề xuất: chuẩn bị executable batch discovery đầu tiên,giữ fixed scope/
cache reuse/global dedup/STOP;review ZIP trước lượt tiếp. Refresh/check414 và4diagnostics
vẫn là work items riêng trước whole-universe completion. Chưa có lệnh batch mới;
pilot PASS không bật bulk/detail downloads hoặc yêu cầu duyệt giá MBS.

## Pilot kiểm chứng ba mã A32/AAA/IDJ — chạy local đúng một lần

Đã lập plan bổ sung và chuẩn bị pilot đại diện UPCOM/HOSE/HNX. Lượt này chỉ đọc đủ
danh sách của3 query,đối chiếu cache và gom provider IDs mới; không tải bài chi tiết,
không áp giá MBS hoặc chạy bulk. Chrome/Playwright hiện đã có,không cần cài thêm.

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_three_query_browser_pilot_v1.py"
```

Để Chrome riêng tự thao tác,từng mã lần lượt; không tự login/click/solve challenge.
Mỗi query dùng fresh nonpersistent context,default browser identity; không profile/
cookie/token/auth import/export,custom headers/UA/proxy hoặc TLS bypass. Tối đa4 list
pages/query,12 business/global; archived estimate7 requests không tính assets. Shared
business interval8s xuyên các browser,operation15s/query90s/global240s;82 context
attempts/query,78 assets/query,246 context attempts/global,HTML2MB. Assets thiếu
Content-Length không measured bandwidth cap; counts không phải physical packets.

Same source/layout/access/challenge/redirect/Retry-After/TLS/transport/budget STOP;
một query lỗi thì cả lượt dừng,không retry hoặc mở mã tiếp theo. Fresh total>80/stale/
overlap/changed count đều không PASS. Query rỗng/layout chưa verified không NO_EVENT.
ZIP partial giữ fragment và ledgers của phần đã chạy; merged dedup chỉ gồm completed
queries. Provider ID có thể thuộc nhiều query,giữ memberships/titles; chưa verified
security/event identity. Cache27.731 IDs không biến43 list IDs thành acquired details.

Gửi OUTPUT_ZIP kể cả partial/error,không chạy lại/xóa output để vượt guard:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_three_query_browser_pilot_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_three_query_browser_pilot_v1\delta-vsdc-three-query-browser-<UTC>.zip
```

`--check` chỉ offline,không mở browser/gọi nguồn. Không có batch/force/resume/ticker
override flags. 137 targeted tests (12 mới),compileall/smoke/CLI check PASS,protect181
old files. Plan/preparation:
`data/corporate_actions/work/vsdc_supplement_plan_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_supplement_plan_validation_20261103_v1/`.

Baseline1.104 queries,MBS completed nên pending1.103;1.096 normal gồm3 pilot,7 large
queries giữ scope HOLD. 55 proposed batches cho1.093 normal ngoài pilot chỉ là plan,
không chạy được từ CLI này. Bước tiếp: agent review offline ZIP cả3 mã và cache/dedup
trước khi chuẩn bị executable batch đầu tiên. Không phải yêu cầu duyệt giá MBS.

## MBS supplement đã chạy và review PASS — không chạy lại

Run `run-20261103T055821608254Z` đọc đủ63/63 rows trong4 pages,unique IDs/total/ranges
khớp, lấy detail187243; cả5 responses200. Detail ghi record25/09/2025,rights100:12,
explicit issuance price10.000 đồng/cổ phiếu,bonus100:03. Khớp HNX record/rights/price;
không suy ex-date hoặc PIT từ VSDC update label. Đây là primary terms corroboration,
chưa owner approval/canonical.43 IDs mới so với cache,1 detail mới,không43 new events.

Review và bản xem:
`data/corporate_actions/work/vsdc_mbs_browser_supplement_live_review_20261103_v1/xem_ket_qua_MBS.html`.
ZIP CRC/32 members/31 hashes/120 old files PASS,19 tests/compileall PASS. Hai prior
VSDC pagination gaps đã được khép; residual HNX/issuer-history/revision-scope còn,
giữ MANUAL_REVIEW_REQUIRED/HOLD,không đổi unsigned10000 proposal hoặc45 choices.

Lệnh supplement bên dưới chỉ là lịch sử,không chạy lại/xóa output để vượt guard.
Bước tiếp đề xuất: chuẩn bị batched plan cho1.104 affected queries,deduplicate IDs/
reuse cached article bodies; kiểm chứng nhóm nhỏ nhiều ticker trước bulk. Review
giá MBS riêng với residual revision scope,không tự approve hoặc tải42 candidate
details khác từ kết quả này. Chưa có lệnh acquisition mới hoặc full-history freeze.

## MBS supplement: đọc đủ query và bài187243 — chạy local một lần

Đã chuẩn bị offline; không cần cài thêm Chrome/Playwright trong môi trường hiện tại.
Lượt mới đọc tối đa4 trang danh sách MBS trong cùng fresh session, kiểm tra stable
total/ranges/IDs, rồi mở duy nhất bài187243 nếu candidate có trong list và chưa có
trong audited cache. Prior40 links giữ nguyên làm evidence; fresh reread nhằm kiểm
tra snapshot consistency, không tải lại known article bodies.

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_mbs_browser_supplement_v1.py"
```

Chạy đúng một lần, để Chrome riêng tự thao tác; không tự login/click/solve challenge.
Script sẽ đóng browser khi xong. Fresh default browser session không import/export
cookie/profile/token/auth, không custom UA/headers hoặc bỏ TLS. Mọi HTTP/redirect/
access/challenge/Retry-After/TLS/timeout/layout/budget lỗi đều STOP, không retry.

Max5 business requests (4 list +1 detail),160 context attempts gồm tối đa155 asset/
blocked external attempts; shared business8s, operation15s, run150s, HTML2MB. Đây không
phải5 physical packets hoặc whole-browser bandwidth cap. Chỉ first-party static assets,
không detail khác/mã khác/attachment hoặc sửa đổi tự fetch. Fresh total>80 hoặc list
mismatch dừng. Fragment public không private/executable được lưu; full HTTP body chỉ
hash/size, không archive whole DOM/HTTP/cookie/HAR. Detail title/content/source-time và
text preview để review, không tự approve giá10000/record date/PIT/revisions/canonical.

Gửi file OUTPUT_ZIP kể cả lỗi/partial, không chạy lại/xóa output để vượt guard:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_browser_supplement_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_browser_supplement_v1\delta-vsdc-mbs-browser-supplement-<UTC>.zip
```

`--check` chỉ offline, không mở browser/gọi nguồn; không có force/resume flag.
Protect120 old files/pinned parents và reuse27.730 cache IDs. 125 targeted tests
(19 supplement), compileall/synthetic smoke/CLI check PASS; live supplement chưa test.
Preparation `data/corporate_actions/work/vsdc_mbs_browser_supplement_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_mbs_browser_supplement_validation_20261103_v1/`.
Bước tiếp sau user-run: review offline full-query và nội dung bài187243 để xác minh
event/date/terms/price và xác định revision evidence còn thiếu. Không tự promote field
hoặc mở bulk1.104 queries từ collection output.

## HTML pilot đã chạy và review PASS — không chạy lại

Run `run-20261103T052324145483Z` đã lấy page1/page2 qua Chrome UI, GET200/POST200.
Range1–20/21–40, cùng total63,40 IDs không trùng. Page2 thêm20 provider IDs mới so
với audited cache; chưa phải verified events hoặc detail documents. Còn23 rows chưa
đọc. Candidate187243 có title hints quyền mua/cổ phiếu thưởng MBS; chưa tải detail
hoặc xác minh record date, giá10000/revisions. Không approve từ title/list timestamp.

Review ZIP/state/19 payload hashes/87 protected files và scope budgets PASS;55 context
attempts gồm2 business và53 assets/external,1 external bị chặn,54 admissions. 16 tests
và compileall PASS. Evidence:
`data/corporate_actions/work/vsdc_mbs_browser_html_live_review_20261103_v1/`.
Lệnh pilot bên dưới chỉ là lịch sử bàn giao, không chạy lại/xóa output để vượt guard.

Bước tiếp đề xuất: chuẩn bị bounded MBS supplement đọc đủ4 pages trong cùng fresh
session và candidate187243 detail; preserve evidence cũ và reuse cached details.
Fresh list reread có mục đích kiểm tra snapshot consistency, không tải lại known
article bodies. Cần review terms/date/price/revision trước owner choice. Chưa có lệnh
supplement mới, chưa mở bulk1.104 queries hoặc certify full history/identity/PIT.

## Pilot MBS đọc thẻ HTML sau browser render — user-run 03/11/2026

Có thể lấy link/title/provider IDs từ thẻ HTML trong #divGlSearchArticles. Collector
HTTP cũ chưa tải được fragment trang2; pilot này để browser tải qua nút phân trang
thông thường rồi đọc DOM sau render. Chưa phải full history hoặc approved MBS fields.

Đã tìm thấy Playwright1.57 và Chrome local; không cần cài thêm trong môi trường hiện
tại. Chạy đúng một lần, script sẽ mở một cửa sổ Chrome riêng và tự thao tác:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_vsdc_mbs_browser_html_pilot_v1.py"
```

Để script thực hiện navigation và click, không tự login/click trong cửa sổ pilot.
Fresh non-persistent context không lấy profile/cookie cá nhân; dùng browser identity
mặc định và session tự tạo bởi public site, không spoof UA/headers hoặc bỏ TLS.
Nếu site yêu cầu login/challenge hoặc có HTTP/TLS/timeout/layout lỗi, pilot dừng.
Không solve CAPTCHA, retry hoặc thử profile khác. Chrome pilot được đóng khi kết thúc.

Giới hạn hai trang MBS, không trang3/4 hoặc bài chi tiết. Browser cần JS/CSS/assets:
tối đa 2 business requests, 78 asset/blocked external attempts, 80 context attempts
tổng. Không hiểu đây là 2 physical requests. Chỉ first-party HTTPS static assets;
host ngoài bị chặn. Business interval8s, operation15s, run90s kiểm tra trước requests/
operations, HTML cap2MB. Response asset khai báo size vượt cap cũng dừng; không claim
đo bandwidth assets thiếu Content-Length. Không background long crawl hoặc polling.

ZIP giữ exact rendered HTML fragment public, link lists/ranges/IDs, HTTP body hash/
size (không full raw HTTP/whole DOM), safe metadata/network ledger, runtime/provenance.
Không cookie/token values, profile, HAR, screenshot hoặc traces. Fragment có private/
executable content bị từ chối trước archive. Luôn resumable=false, actual run chặn
rerun; không có force/resume flags. V1/V2 và 87 old protected files giữ nguyên.

Gửi file tại OUTPUT_ZIP, kể cả partial/error. Không chạy lại ngay hoặc xóa output:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_browser_html_pilot_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_browser_html_pilot_v1\delta-vsdc-mbs-browser-html-<UTC>.zip
```

`--check` chỉ kiểm tra offline, không mở browser/gọi nguồn. 106 targeted tests (16
browser HTML), compileall/synthetic smoke/CLI check PASS; live browser path chưa test.
Preparation `data/corporate_actions/work/vsdc_mbs_browser_html_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_mbs_browser_html_validation_20261103_v1/`.
Bước tiếp: review offline ZIP để xác minh UI page2, range/total/IDs và scope/budget.
Chỉ sau live PASS mới lập plan bổ sung; không mở bulk1.104 queries từ preparation.

## V2 đã chạy và review — vẫn HTTP 400, không chạy lại

Run `run-20261103T050150450791Z` có GET 200/page1 20/63 rows, POST page2 400/body
rỗng. POST construction đã có X-Requested-With XMLHttpRequest, GET không có; thêm
riêng header này chưa sửa được lỗi. ZIP integrity/STOP/49 old hashes PASS, 16 tests
và compileall PASS. Không có details/observations/canonical changes hoặc new source
requests từ agent. Evidence review:
`data/corporate_actions/work/vsdc_mbs_pagination_live_review_20261103_v2/`.

Lệnh V2 bên dưới là lịch sử bàn giao; không chạy lại hoặc xóa output để vượt guard.
Không có V3 header profile được chuẩn bị. Bước tiếp đề xuất là bounded browser-UI
MBS pilot qua nút phân trang thông thường, lưu rendered page2 list và metadata tối
thiểu, không cookie/token/auth values hoặc challenge bypass. Cần reviewable browser
access/user-run capture path; chưa có lệnh browser pilot, chưa mở bulk 1.104 queries.

## VSDC MBS pilot V2 — chạy local đúng một lần, 03/11/2026

Đã chuẩn bị và kiểm thử offline, chưa gọi nguồn. V2 chỉ thêm observed functional
`X-Requested-With: XMLHttpRequest` vào POST trang 2. Evidence là Request Headers user
chép từ public UI; đây chưa là proven fix HTTP 400. GET trang 1, URL/body/JSON
Content-Type/research UA/Accept giữ nguyên; không cookie/auth hoặc header rotation.

Chạy đúng một lần từ PowerShell, bất kỳ working directory:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\probe_vsdc_mbs_pagination_v2.py"
```

Scope MBS, tối đa hai requests GET trang1 → POST trang2, một worker, interval 8s,
timeout 15s, run budget 90s kiểm tra trước request/sau shared delay, response 2MB.
Strict default TLS/NoRedirect; mọi HTTP/access/challenge/Retry-After/TLS/timeout/
layout mismatch dừng, không retry hoặc thay profile. Page2 cần range/total khớp và
IDs không trùng page1. Không gọi trang3/4/details/mã khác, không observation/canonical.

Gửi file tại OUTPUT_ZIP kể cả partial/error/HTTP400. Không chạy lại, không xóa output
để vượt guard, không resume. V1 không thay đổi; V2 dùng output riêng:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_pagination_pilot_v2\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_pagination_pilot_v2\delta-vsdc-mbs-pagination-v2-<UTC>.zip
```

ZIP giữ raw/receipts/timing/runtime/TLS/provenance/browser evidence/construction logs;
construction được ghi trước urllib handlers, chưa phải full wire capture. Bảo vệ 49
old files và parent manifests, reuse 27.730 cached IDs. `--check` chỉ offline, không
tạo run hoặc gọi nguồn. Không có force/resume flag. 90 targeted tests (16 V2),
compileall/synthetic smoke/CLI check PASS.

Bước tiếp sau user-run: agent review offline ZIP, kể cả partial. Chỉ sau live PASS mới
xem xét plan bổ sung có budget; chưa mở batch 1.104 queries hoặc approve MBS price.

## Hoàn tất đối chiếu metadata — candidate header cho diagnostic V2

Request Headers user gửi: X-Requested-With XMLHttpRequest; Content-Type JSON UTF-8.
Collector request construction không có X-Requested-With, đã xác minh bằng offline
injected opener không network. URL/POST/payload và parsed JSON charset khớp. Đây
là khác biệt cụ thể, chưa chứng minh HTTP 400 do header hoặc live fix.
Evidence: `data/corporate_actions/work/vsdc_mbs_request_metadata_comparison_20261103_v2/`.

Bước tiếp đề xuất là chuẩn bị V2 diagnostic riêng, thêm đúng observed AJAX header
vào page2 POST, giữ mọi budget/TLS/UA/STOP và không cookie/auth/retry/details. Không
sửa V1 đã freeze hoặc xóa rerun guard. Chưa có lệnh V2 để chạy; không mở bulk từ
metadata comparison. Live V2 cần HTTP200 cùng range/total/IDs đúng mới PASS pilot.

## Đã nhận metadata POST trang 2 thành công — còn xác minh Request Headers

User gửi đúng URL MBS, POST, 200 OK, payload SearchKey 4/CurrentPage 2; URL/method/
payload semantics khớp sealed collector POST 400. Content-Type `text/html; charset=utf-8`
chưa rõ section; không dùng để thay request Content-Type JSON. Đối chiếu PARTIAL tại
`data/corporate_actions/work/vsdc_mbs_request_metadata_comparison_20261103_v1/`.
Chỉ còn cần hai dòng ở Headers → Request Headers: Content-Type, X-Requested-With
(hoặc xác nhận không có). Không cần gọi lại trang 2 nếu request vẫn còn trong Network,
không gửi Cookie/token/auth hoặc full HAR. Chưa chạy lại collector hoặc mở bulk.

## Capture request MBS — chờ browser access hoặc input thủ công

Tool hiện báo “Local browser use is disabled in Work settings”. Chưa có request
capture; không coi manual “21–40 / 63” là HTTP 200 hoặc nguyên nhân đã được xác định.
Baseline và template chưa điền: `data/corporate_actions/work/vsdc_mbs_request_comparison_preparation_20261103_v1/`.

Nếu thu metadata thủ công trong Chrome:

1. Mở đúng URL MBS đã dùng; nhấn F12, chọn Network rồi Fetch/XHR.
2. Reload đúng một lần để về trang 1, rồi bấm nút trang 2 đúng một lần.
3. Chọn request search tương ứng với lần bấm. Trong Headers → General lấy Request
   URL, Request Method, Status Code. Trong Request Headers chỉ lấy Content-Type
   và tên các headers khác. Trong Payload lấy JSON của request.
4. Gửi metadata dạng text theo template JSON; field chưa biết giữ null. Không gửi
   full HAR, Copy as cURL, Cookie/Authorization/token values. Nếu request chứa dữ
   liệu nhạy cảm ngoài SearchKey/CurrentPage thì bỏ phần đó và mô tả tên field.

Chỉ quan sát request do UI tạo; không Replay XHR, Edit and Resend hoặc sửa request.
Collector không chạy lại trong bước này. Cần metadata trước khi kết luận cách sửa.

## User báo trang 2 MBS hoạt động trên UI — 03/11/2026

User xác nhận “21–40 / 63 bản ghi”. Đây là manual UI observation, chưa là captured
HTTP response. Collector POST vẫn HTTP 400 trong run đã review; không chạy lại hoặc
xóa output/guard. Chưa biết khác biệt gây lỗi, chưa mở batch bổ sung 1.104 queries.
Evidence: `data/corporate_actions/work/vsdc_mbs_browser_manual_observation_20261103_v1/`.

Bước tiếp đề xuất là đối chiếu metadata một request trang 2 thành công từ browser
(URL/method/payload/Content-Type/status/tên headers) với collector. Không cần full HAR,
giá trị cookie/token/auth, và không replay hoặc thay headers để thử phỏng đoán.

## Kết quả pilot VSDC MBS — đã review 03/11/2026, không chạy lại

Run `run-20261103T043616143951Z` đã được user thực hiện. GET trang 1 HTTP 200,
20/63 rows; POST trang 2 HTTP 400 với body rỗng. ZIP/state/hashes/runtime và sáu
old states đã kiểm tra offline, PASS integrity/STOP nhưng FAIL truy cập trang 2.
Không có detail fetch hoặc new observations/canonical fields. Formatting compact
JSON/charset chưa giải quyết lỗi trong run này; chưa biết nguyên nhân server.

Review: `data/corporate_actions/work/vsdc_mbs_pagination_live_review_20261103_v1/`.
Lệnh pilot bên dưới là lịch sử bàn giao, không phải yêu cầu chạy lại. Không xóa
output để vượt rerun guard. Batch bổ sung 1.104 queries chưa được mở.

Bước tiếp đề xuất là kiểm tra một lần trang 2 bằng nút trên giao diện public VSDC
trong browser thông thường, để phân biệt hành vi UI và collector. Không thử nhiều
profile hoặc vượt login/challenge/access control. Nếu UI thành công, cần đối chiếu
request context trước pilot mới; nếu UI cũng lỗi, giữ STOP và xem xét hỗ trợ từ nguồn
hoặc evidence thay thế được chấp nhận.

## Pilot VSDC MBS trang 2 — bàn giao user-run 03/11/2026

Đã chuẩn bị offline, chưa gọi VSDC. Pilot kiểm tra pagination trước khi lập batch
bổ sung 1.104 queries. Chỉ MBS, tối đa hai requests: GET fresh trang 1 rồi POST trang 2.
Không article detail fetch hoặc approve giá MBS trong pilot này.

Chạy đúng một lần bằng PowerShell, từ bất kỳ working directory nào:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\probe_vsdc_mbs_pagination_v1.py"
```

Một worker/shared delay 8s/timeout 15s/response 2MB/run budget 90s. GET phải xác minh
query echo MBS và public source JS contract; POST dùng cùng URL/query, compact JSON
SearchKey 4/CurrentPage 2 và Content-Type application/json;charset=utf-8 đúng như JS.
Giữ User-Agent hiện hành, strict default TLS/NoRedirect; không cookie/auth hoặc
đổi host/header/IP để tiếp tục sau lỗi. Formatting này chưa là proven fix HTTP 400.

Nếu page 1 không có trang 2 thì PARTIAL và dừng. Nếu POST 200, parser chỉ chấp nhận range
21–min(40,total), total khớp fresh page 1 và IDs không trùng; không tự gọi page 3/4.
HTTP 400/401/403/429/redirect/challenge/Retry-After/TLS/timeout/layout mismatch
đều dừng toàn pilot, không thử request khác. Old bootstrap/4 shards deferred flags
và HNX VTZ STOP giữ nguyên; pilot dùng run mới, không có --resume hoặc force flag.

Script in OUTPUT_STATE và OUTPUT_ZIP. Gửi đúng ZIP được in, kể cả exit2/partial/
HTTP 400; không chạy lại khi lỗi. Fresh rerun bị chặn sau bất kỳ run thật nào để chờ
review. `--check` chỉ kiểm tra offline, không tạo run hoặc gọi nguồn.

Output:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_pagination_pilot_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vsdc_mbs_pagination_pilot_v1\delta-vsdc-mbs-pagination-<UTC>.zip
```

ZIP giữ raw/receipts/hashes/monotonic timing, source contract cũ+fresh nếu có,
runtime/TLS/checkpoints/final state, lists vàcache-ID snapshot. Chỉ là discovery
rows, chưa phải new events/full history/PIT/identity/bulk approval. Không gọi OpenAI.

Preparation `data/corporate_actions/work/vsdc_mbs_pagination_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_mbs_pagination_validation_20261103_v1/`.
74 targeted tests (12 mới), compileall/synthetic smoke/CLI check/self-review PASS;
0 source requests trong stage chuẩn bị. Bước tiếp: user chạy và agent review ZIP
offline. Sau live PASS mới chuẩn bị scope/budget bổ sung; không mở bulk từ pilot này.

## VSDC pagination audit toàn C8 — 03/11/2026, chưa mở acquisition

Đã xác minh collection thiếu phần list ở nhiều query, không chỉ MBS. Full inventory C8 v2
1.522 queries/1.529 response snapshots: 1.104 query lists chưa đọc hết (486 UPCOM/357 HOSE/
261 HNX), 414 query lists exhausted chỉ trong snapshot, 4 unverified (DTR/KAI/LPS/PCB).
Không dùng 905 latest-ready làm scope hoặc coi query exhaustion là event history complete.

Initial POST page 2 của A32/AAA/AAM/SSI nhận HTTP 400; 12 ledger copies chỉ là 4 physical requests.
Sau đó bootstrap và 4 shards giữ deferred_post_hosts=vsdc.vn, runner chặn POST trang 2 bằng
PAGINATION_DEFERRED_AFTER_ARCHIVED_HTTP_400. Tất cả 1.104 query incomplete có guard check
evidence. MBS plan 20 pages/100 details, nên page 2 không dừng vì limit 20 details. Empty 400
body không giải thích server cause; saved source JS request shape chưa chứng nhận live fix.

Danh sách phạm vi và bản xem dễ đọc:
`data/corporate_actions/work/vsdc_pagination_scope_audit_20261103_v2/`.
`supplement_candidates.jsonl` chứa 1.104 queries, không phải lệnh bulk. Tổng 52.819 row
slots ngoài phần list đã đọc có thể trùng giữa queries hoặc ngoài security/kỳ cần thu;
không gọi là 52.819 events hoặc requests cần chạy. Known URLs đã có raw được reuse, không tải lại.
62 targeted tests (8 mới), compileall, synthetic smoke và self-review PASS.

Bước tiếp: chuẩn bị bounded user-run pagination pilot cho MBS, giữ strict TLS/STOP/budget,
chỉ sau pilot mới đóng gói phạm vi bổ sung cho mọi affected query với cache-first dedup và lọc
security/date. Không xoá deferred guard hoặc resume HNX STOP. Processed/SOURCE_PARTIAL
chưa là complete coverage; PIT/identity/canonical/45 choices giữ nguyên manual review.

## MBS revision cache review — đã thực hiện offline 03/11/2026, còn HOLD

Kết luận hiện hành: **chưa đề nghị owner duyệt giá** vì cache thiếu phần lịch sử
cần rà. Giá 10.000 VND/CP vẫn có primary quote trong HNX581051, không bị bác bỏ.
Chưa thấy linked revision/giá đối nghịch trong 20 VSDC documents và 2 HNX detail bodies
đã kiểm tra; điều này không chứng nhận không có revision ngoài cache.

Raw VSDC query ghi 20/63 rows; phần đã lưu dừng ở 24/10/2025, sau target record 25/09/2025.
43 query rows ngoài trang đầu chưa có trong snapshot, không phải 43 events. Có 4 docs
đúng cổ phiếu MBS, 16 docs thuộc security khác, chủ yếu trái phiếu. VSDC193811 là đợt
record 03/04/2026/ratio 2:1, không dùng để quyết định đợt 12% năm 2025. HNX 3 list articles
chỉ trong CORPORATE_NEWS/window 26/05–31/12/2025, không bao phủ mọi group/issuer/later notice.

Bản xem kết luận mới:
`data/corporate_actions/work/mbs_revision_cache_review_20261103_v2/ket_luan_ra_cache_MBS.html`.
JSON/raw copies/hashes/receipt joins nằm cùng artifact. Bản xem bằng chứng giá cũ
giữ nguyên; bản kết luận mới nói rõ vì sao chưa gỡ điều kiện revision review.
Không gọi nguồn/approve/apply, không sửa queue/45 choices hoặc VTZ STOP/resumable=false.
73 targeted tests (11 mới), compileall, synthetic smoke và self-review PASS.

Bước tiếp đề xuất: chuẩn bị bounded user-run VSDC pilot riêng cho MBS, ưu tiên lịch
sử quanh 25/09/2025 chưa cache; chưa mở pilot hoặc chạy request trong stage này. Giữ
strict TLS/access STOP, không resume HNX hoặc suy PIT/identity/readiness từ giá đã quan sát.

## Review offline HNX components và queue version mới — 03/11/2026

Đã đối chiếu năm components với 56 distinct VCI payloads của MBS/TNG, giữ 67 SDK
occurrences. Cả năm có unique counterpart candidate khớp component/cả hai ngày/
economic term; không tự certify historical identity/event hoặc PIT.

| Article/component | Counterpart | Kết quả đối với missing queue |
|---|---|---|
| TNG497771 CASH 400 VND/CP | ex 19/01/2024, record 22/01/2024 | Ngoài queue; corroboration |
| TNG523090 STOCK 8% | ex 12/07/2024, record 15/07/2024 | Đã có ngày; không gán sang RIGHTS 10% |
| MBS575367 CASH 1.200 VND/CP | ex 19/08/2025, record 20/08/2025 | Ngoài queue; corroboration |
| MBS581051 BONUS 3% | ex 24/09/2025, record 25/09/2025 | Ngoài queue; corroboration |
| MBS581051 RIGHTS 12% | ex 24/09/2025, record 25/09/2025 | Một price field có evidence 10.000 VND/share chờ owner |

Output `data/corporate_actions/work/hnx_component_queue_review_20261103_v1/`:
`observation_payload_review.jsonl` ghi đầy đủ comparisons/counterparts;
`missing_event_fields_review_v2.jsonl` giữ 602 original payloads và mọi missing fields;
`field_tasks_review_v2.jsonl` ghi 1.373 tasks; `selected_25_field_tasks_review_v2.jsonl`
ghi subset 10 mã; `unsigned_mbs_price_proposal.jsonl` là một đề xuất chưa ký/áp dụng.

Một task pending evidence và 1.372 tasks chưa có matching evidence từ năm observations
này, không phủ nhận old cache/owner evidence. Selected 25 tasks: 1 pending/24 chưa có
evidence mới. Canonical missing counts không giảm trước approval/application.
45 owner choices cũ không merge hoặc thay đổi. MBS proposal kèm quote primary unit,
receipts/hashes và conditions xác nhận payload/component/both dates/revision conflicts;
không dùng file này như signed production decision. PIT/identity giữ manual review.

Validation `data/corporate_actions/work/hnx_component_queue_review_validation_20261103_v1/`.
74 targeted tests (12 mới), compileall, synthetic smoke và self-review PASS.
Bước tiếp đề xuất: owner review một MBS price choice. VTZ diagnostic nếu muốn phải
scope/approve riêng; checkpoint STOP/resumable=false không đổi. Không có lệnh HNX
để chạy trong stage này; agent đã dừng sau offline review.

## HNX cached parser remediation — đã thực hiện offline03/11/2026

Đã sửa hai extraction defects trên bốn details đã lưu; không cần chạy terminal
hoặc tải lại. Parser opt-in `components-v2` nhận explicit “nhận thêm” allocation,
tách mixed article chỉ bằng complete unique recognized `* heading:` blocks;
giữ ambiguity nếu thiếu/unknown/duplicate/conflicting boundaries. Required terms,
exact receipt/list/title joins, metadata flags vàrevision handling giữ nguyên.

| Article | Legacy | Version mới |
|---|---|---|
| TNG523090 | Thiếu ratio/RATIO_PARSE_AMBIGUITY | STOCK_DIVIDEND ratio0.08 |
| MBS581051 | OTHER/MIXED_OR_UNKNOWN_EVENT_TYPE | BONUS_SHARE0.03; RIGHTS_ISSUE0.12,price10.000VND/share |
| TNG497771/MBS575367 | CASH_DIVIDEND | Fields/observationIDs giữ nguyên |

Bốn cached articles: extractionPASS2→4, observations4→5 sourcecomponents,
reviews14→13 (10metadataREVIEW/3missingpaymentINFO); không phải5new canonicalevents.
TNGstock8% không map vào selectedrights10%; MBSprice candidate cầnowner review.
Không PIT/identity/canonical promotion hoặc apply45choices.

VTZ network cause chưa xác định: HTTP200 headers rồibody read timeout15s; không
thấy401/403/429 nhưng không suy nguồn đã ổn định. Giữ STOP vàresumable=false;
không tăng timeout/retry hoặc chạy bốn mã còn lại. Old preparation runtime pins
đã stale sau code change; không sửa artifact cũ đểresume.

Code `scripts/corporate_actions/reparse_hnx_cached_components_v2.py`, config
`configs/data/corporate_actions/hnx_cached_parser_remediation_v2.json`, output
`data/corporate_actions/work/hnx_cached_parser_remediation_20261103_v1/`.
Legacy parser default vẫn tái lập observations/reviews cũ; source-before snapshot
nằm trong output để kiểm tra runtime ZIP. 124 targeted tests (11 mới), compileall,
synthetic smoke và self-review PASS. Stage đã dừng sau offline remediation.

## HNX local supplement 10 mã — bàn giao chuẩn bị 03/11/2026

**Lượt này đã chạy và STOP; không chạy lại lệnh bên dưới hoặc dùng `--resume`.**
ZIP `delta-hnx-local-supplement10-20261103T025523779036Z.zip` có15 request attempts:
14 complete HTTP200 responses; VTZ profile GET nhận200 headers rồi read timeout,
chưa có complete body/hash. Không thấy401/403/429, không kết luận nguyên nhân.
`resumable=false` giữ nguyên. HKT/PGN/TIG/VEF chưa attempt. Guard STOP đúng contract.

Đã lưu10 discovered articles, bốn details/bốn observations trên TNG/MBS; hai cash
articles extraction PASS, hai còn REVIEW_REQUIRED;14 review rows (12 REVIEW/2 INFO).
MBS581051 raw có mixed bonus100:03 + rights100:12 vàgiá10.000đồng/CP, còn parserOTHER.
TNG523090 raw có100:8 allocation nhưng ratio chưa parse; không khớp selected rights
payload10%. Có thể tiếp tục stage offline từ cache, không cần tải lại các bài này.
Không apply fields/PIT/identity/canonical. CRC/hashes/runtime/replay/TLS vàshared
delay8.000–8.016s PASS. Review:
`data/corporate_actions/work/hnx_local_supplement10_review_20261103_v1/`.

Phần còn lại ghi contract/lệnh bàn giao trước khi chạy, không phải approval chạy
lại. Không chạy lại PVS/ACV hoặc resume các Kaggle shards bị source STOP.

Tất cả mã lấy từ C8 v2 inventory 1.522 mã và queue
`tmp/ca_supplement_plan_20261102_v1/missing_event_fields_602.jsonl`.
Mỗi dòng dưới đây là một selected SDK payload, chưa phải canonical event;
date hint là SDK `public_date` được xem ở +07:00, chỉ dùng tìm kiếm.

| Mã | Sàn | Date hint | Fields cần bổ sung | Publication window |
|---|---|---|---|---|
| VE3 | HNX | 2024-11-25 | ex_date, record_date, rights_subscription_price | 2024-07-28–2025-03-25 |
| TNG | HNX | 2024-04-23 | ex_date, record_date, rights_subscription_price | 2023-12-25–2024-08-21 |
| IDJ | HNX | 2023-05-25 | ex_date, record_date, rights_subscription_price | 2023-01-25–2023-09-22 |
| MBS | HNX | 2025-09-23 | rights_subscription_price | 2025-05-26–2025-12-31 |
| RGG | UPCOM | 2022-12-26 | rights_subscription_price | 2022-08-28–2023-04-25 |
| VTZ | HNX | 2025-06-17 | ex_date, record_date | 2025-02-17–2025-10-15 |
| HKT | HNX | 2024-10-25 | ex_date, record_date, rights_subscription_price | 2024-06-27–2025-02-22 |
| PGN | HNX | 2024-05-28 | ex_date, record_date, rights_subscription_price | 2024-01-29–2024-09-25 |
| TIG | HNX | 2025-05-15 | ex_date, record_date, rights_subscription_price | 2025-01-15–2025-09-12 |
| VEF | UPCOM | 2023-09-26 | ex_date, record_date, rights_subscription_price | 2023-05-29–2024-01-24 |

Cả 10 mã chưa có discovery/detail trong bốn cumulative HNX ZIP mới nhất và các
local pilot được kiểm tra; vẫn pending trong checkpoint cũ. Đã verify/reparse137
VSDC raw và đối chiếu prior normalized evidence; không tìm thấy supported dated
field anchor cho selected payloads. Đây là lý do request mới, không phải PIT hoặc
historical identity. RGG2025 có raw hỗ trợ, được giữ offline, không chọn tải lại.
Các payload khác của cùng ticker không tự trở thành scope của job.

Một lệnh PowerShell chạy từ bất kỳ working directory nào:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" -X utf8 "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\collect_hnx_local_supplement10_v1.py"
```

Giới hạn: một worker; shared delay8s giữa mọi requests, kể cả đổi mã/stage;
timeout15s/response2MB; tối đa hai list pages (20 rows/page), hai observed detail
articles/mã, tổng50 requests/job. Chọn candidates theo event-type title hint,
khoảng cách date hint rồi article ID; giữ selected IDs trong checkpoint. Không
fallback article ngoài observed discovery hoặc tự mở rộng cửa sổ khi rỗng.
Timer1.200s/lượt/2.400s cộng dồn kiểm tra trước request và sau delay; request đang
chạy chịu socket timeout. Không cam kết lịch sử đầy đủ hoặc resolve đủ25 fields.

401/403/429/challenge/Retry-After/access/TLS/timeout dừng toàn job. Không đổi host/header/
IP/account, retry hay redirect. Known layout/data/parser issues được giữ review/
quarantine theo contract, không coi là không có sự kiện. TLS validated intermediate
và strict verification giữ nguyên. Checkpoint sau từng request/work unit; raw,
receipts, monotonic timing, parser reviews và hashes nằm trong ZIP full/partial.

Output mới tại:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\hnx_local_supplement10_v1\run-<UTC>\state
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\hnx_local_supplement10_v1\delta-hnx-local-supplement10-<UTC>.zip
```

Gửi đúng file in sau `OUTPUT_ZIP`, kể cả script trả exit2/partial. Không chạy lặp
nếu lỗi; fresh invocation thứ hai bị chặn để chờ review. `--check` chỉ offline.
`--resume <absolute-state-path>` chỉ dành cho sealed state mới có `resumable=true`,
cùng runtime/contract, không source STOP/inflight; luôn xuất run/ZIP mới, không
reset job budgets hoặc sửa old artifacts. Partial/inflight sau kill hoặc access
STOP không tự retry; cần review trước. Không force-resume Kaggle state.

Preparation:
`data/corporate_actions/work/hnx_local_supplement10_preparation_20261103_v3/`.
Validation:
`data/corporate_actions/work/hnx_local_supplement10_validation_20261103_v2/`.
Offline85 tests/compileall/smoke/CLIcheck PASS; source requests và applied fields0.
Source public clock semantics/timezone và historical identity chưa certified;
không gỡ review flags/approve45 choices, canonical/factors/backtest/readiness.
PIT/identity/source-selection/final freeze vẫn MANUAL_REVIEW_REQUIRED.

## ACV local: UPCOM và cổ tức cổ phiếu — chuẩn bị03/11/2026

User-run đã được review:3HTTP200,bài573433,ratio0.6458,ex07/08/2025 vàrecord
08/08/2025. Hai metadataREVIEW vàmộtINFO vềpayment_date thiếu đượcgiữ nguyên.
Review tại `data/corporate_actions/work/hnx_acv_local_pilot_review_20261103_v1/`.
Không cần chạy lại cùngpilot đểxácnhận success; chưa làapprovalbulk.

Tiếp sau PVS, dùng ACV để kiểm tra UPCOM và một noncash action. Cache cũ có
bài573433 đăng30/07/2025; lượt này tìm lại trong window ngày đăng2025-07-01 đến
2025-08-31, rồi chỉ tải đúng bài đó nếu freshly observed. Tối đa3 requests:
profile GET, một list POST/page20rows, một detail POST; delay8giây, timeout15giây.
Không mở thêm page hoặc lấy bài khác nếu không tìm thấy known ID.

Chạy trong terminal PowerShell, không cần API key:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\probe_hnx_acv_local_v1.py"
```

Gửi ZIP ở dòng OUTPUT_ZIP, kể cả khi status STOPPED/PARTIAL. File mới sẽ ở
`data/corporate_actions/work/hnx_acv_local_pilot_v1/`; không cần chạy lại PVS.
Thêm `--check` chỉ kiểm tra offline. Script không gọi OpenAI/LLM; gặp lỗi access
thì dừng, không tự chạy lặp. Strict TLS và checkpoint cũ giữ nguyên. Parser chỉ
tạo review preview; thiếu payment date hoặc PIT/identity chưa xác minh vẫn giữ
review, không tự điền ngày hoặc promote readiness.

## PVS local: kiểm tra một trang danh sách và một detail — 03/11/2026

Kết quả user-run đã review: ZIP20261103T021025418311Z có3HTTP200, tìm/tải đúng
bài537190 vàparse1observation. Bài ghi700VND/CP,cácngàyex/record/payment đầyđủ;
hai review còn lại vềsourcepublication semantics/timezone vàhistoricalidentity.
Review tại `data/corporate_actions/work/hnx_pvs_local_pilot_review_20261103_v1/`.
Không cần chạy lại cùngpilot chỉđể xácnhận success;chưa phảiapprovalbulk.

HLA trả 0 thông báo chỉ là kết quả query trong group CORPORATE_NEWS, publication
range 2019-01-31–2025-12-31 và filter HLA/UPCOM. Không chứng nhận toàn bộ nguồn
không có dữ liệu HLA. Pilot mới dùng PVS quanh sample đã biết, ngày đăng
2024-10-01 đến 2024-11-30. Tối đa 3 requests: profile, list page 20 rows và một
article detail.

User chạy lệnh này trong terminal PowerShell; không cần API key hoặc cài SDK:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv\Scripts\python.exe" "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\probe_hnx_pvs_local_v1.py"
```

Log có DISCOVERY_STARTED/DISCOVERY_SAVED, DETAIL_STARTED nếu tìm thấy candidate,
cuối có OUTPUT_ZIP. Gửi ZIP để review kể cả status STOPPED/PARTIAL; không tự chạy
lặp khi access failure. ZIP mới ở `data/corporate_actions/work/hnx_pvs_local_pilot_v1/`.
Nếu cần check offline trước, thêm `--check`: không có request hoặc output mới.

TLS được xác minh với pinned intermediate cũ và existing trusted root; delay
8 giây, timeout 15 giây/request, shared cap 3 requests/run 120 giây. Không retry,
redirect, đổi host hoặc resume shard cũ. Ngay cả khi access PASS, parser output
chỉ là review preview, không canonical/freeze readiness. Script không gọi
OpenAI; agent chat/review vẫn dùng usage.

## Kết quả mới nhất ABB/AAS — 02/11/2026

Đã xử lý false positive ABB bằng checker chỉ cho một exact public article và
inert-script hash đã kiểm tra; default source guards giữ nguyên. Fresh GET PASS,
candidate giá10000 VND/share/record10/11/2021/rights5:1 được củng cố,không là
candidate mới hoặc accepted field. Không mở exception cho toàn bộ website.

AAS đã có original nghị quyết18 PDF3 trang,khớp planned stock dividend4%;primary
issuer notice20 báo tạm dừng cùng phương án. OriginalĐHĐCĐ01 vàPDF20 còn thiếu;
rights100% không được nhận nhãn tạm dừng từ stock-dividend notice. Không suy
ex/record date hoặc backdate PIT. Stage7 acquisition requests,HNX0,no bulk.
Current findings `tmp/ca_abb_aas_findings_20261102_v1/`,56 tests/compileall/smoke
PASS; xem nhật ký mới vàCurrent status để đọc timeline,limits vàmetadata manifest
anomaly đã được giữ nguyên/kiểm tra bằng raw receipts vànew file index.

## Supplemental source plan và pilot — đã thực hiện 02/11/2026

Plan `tmp/ca_supplement_plan_20261102_v1/` giữ riêng195 supported price rows,
49 additional reviews,602 missing-field payloads trên332 mã,và182 coverage mã.
602 rows có1373 missing field tasks chưa có proposal:482 ex,481 record,410 price;
không cộng thành số sự kiện. Các date gaps cần kiểm tra PLAN/EXECUTED/CANCELLED,
không chỉ tìm ngày rồi điền vào tất cả rows.

Current stage result `tmp/ca_supplement_pilot_review_20261102_v1/stage_summary.json`
vàpilot_findings.json. Formal pilot5 network attempts,3 documents accepted;raw
ABB HTTP200 cũng được lưu nhưng source gate dừng do recaptcha keyword. Offline
body có candidate10000 VND/share/record10/11/2021/ratio5:1;không auto approve hoặc
gọi tiếp ABB PDF. FIT6-page scan còn primary unit gap;unit ở residual placement
không được mượn sang. AAS draft2025 báo cáo tạm dừng phương án2024,gợi ý cần
lifecycle review và nghị quyết gốc. AGF page1 có20/31 links,chưa complete coverage;
AGG bị SSL verify fail,HNX không gọi lại. Chưa đủ source gates cho bulk.

Không cần chạy lại thu thập toàn bộ. Dừng tại source-specific gaps ghi trong
findings,không tự build canonical/tính factors hoặc đổi PIT/identity/Q11.

## Kiểm tra raw sau reconciliation — đã thực hiện 02/11/2026

Current output: `tmp/ca_raw_evidence_review_20261102_v4/`. Mở summary.json để xem
số liệu,price_proposal_reviews.jsonl để xem từng giá đề xuất,raw_article_reviews.jsonl
để xem quotes/ratio legs và raw paths. date_proposal_reviews.jsonl và
ratio_conflict_reviews.jsonl giữ kết luận ngày/xung đột. Các output diagnostic
v1/v2/v3 không là current result; giữ nguyên để truy vết kiểm tra kỹ thuật.

244 price proposals được kiểm tra:195 có raw support về ticker/record/giá/unit/
tỷ lệ,24 thiếu explicit unit,22 cầnterm/component review,3 cầnrevision review
(SZC,VTR,HVN sửa lịch).195 thuộc162 mã, chưa human-accepted. Trong99 rows trước
có ratio warning,76 có đủ raw support theo checker mới; warning cũ không bị xóa.
36 conflicts chia23 provider-rounding candidates,1 source-precision candidate,
10 component-sum candidates,2 explicit yearly-component cases. Chưa áp dụng
tolerance hoặc tự gộp events.6 ex-date proposals chỉ1 có official raw explicit
date,5 dựa sibling;7 record-date proposals có6 official,1 sibling. Time-hint
event matching vẫn provisional, PIT/historical identity chưa được xác minh.

remaining_field_queue_by_ticker.json gom1630 field tasks trên427 mã; queue không
dedup thành canonical events hoặc đánh dấu resolved khi mới có đề xuất. File
missing_vci_coverage_queue.json giữ182 mã coverage-open. Stage dùng0 network
requests;không có canonical/price-factor writes. Self-review và34 tests/compileall/
synthetic smoke PASS. Kết quả vẫn PARTIAL_MANUAL_REVIEW_REQUIRED.

## Đối chiếu offline sau full VCI — đã thực hiện 02/11/2026

Stage preview đã hoàn thành, không cần chạy lại crawl. Output mới ở
`tmp/ca_offline_reconciliation_20261102_v1/`. summary.json ghi số liệu,
reconciliation_candidates.jsonl giữ2179 original SDK payloads C8 noncash cùng
field alternatives/proposals,source_evidence_used.jsonl giữ raw locators/hashes,
missing_vci_tickers_archived_inventory.json theo dõi182 mã chưa có VCI rows.
Manifest pin output; self-review/hash checks tại
`tmp/ca_offline_reconcile_validation_20261102_v1/self_review.json`.

488 rows thiếu ex/record có6 ex_date proposals và7 record_date proposals;
654 rights rows có244 price proposals,410 chưa có một giá trị đề xuất. Chỉ1/6
ex_date proposals có official explicit ex_date support;5 dựa SDK sibling.
244 price proposals có raw VSDC verified nhưng99 vẫn cảnh báo parse ratio,3
có dấu hiệu correction, toàn bộ PIT chưa verified. Đây là hàng chờ kiểm tra,
không phải đã bổ sung thành công các trường vào corporate_actions.

Technical preview PASS,data readiness PARTIAL_MANUAL_REVIEW_REQUIRED. Không có
accepted canonical fills, không tính factor/price series/backtest. Việc tiếp theo
cần tách riêng: review event identity/revision và raw/PDF terms, nhất là482
missing-ex rows/410 missing-price rows chưa có single-value proposal. Không tự
đổi chính sách PIT/identity/price basis để biến preview thành bảng dùng backtest.

## Kết quả local đầy đủ — đã audit offline 02/11/2026

Run20261102T024517019426Z đã acquire đủ84 query windows,14028 SDK rows,11202
distinct whole-row payloads;2826 duplicate excess được giữ nguyên. CRC/425 root
hashes/252 commit hashes/426 local-vs-ZIP file equality PASS. Distinct payloads
không là canonical event count.385 distinct payloads của pilot nằm trong full
run, không cộng388 pilot rows vào tổng. Nguyên nhân lỗi account/device cũ không
được suy ra từ việc local key hiện tại acquire thành công.

1522 returned tickers chỉ1340 khớp C8 v2;182 outside và182 C8 chưa có row.
Trong C8,2179 stock dividend/bonus/rights candidate payloads có488 thiếu ex/record;
VCI export không có rights subscription price. Chỉ dividend query group, chưa
certify split/reverse-split coverage. PIT/revisions/historical identity vẫn open;
không tự convert17:00Z thành actual publication time. Snapshot có payment date
tới2030 và một SDT cohort nhiều payout dates, cần giữ evidence để review.

Technical acquisition PASS, data quality/coverage PARTIAL. Không chạy lại crawl
hoặc build canonical/adjustment/backtest trong audit stage. Báo cáo/inventory:
`tmp/ca_vci_local_full_audit_20261102_v1/`. Next work riêng là đối chiếu offline
VSDC/HNX/VCI và review thiếu trường; Q11 price basis chưa được freeze.

## Handoff local VCI — chuẩn bị 02/11/2026, dependency/live gate pending

User chọn local thay vì gửi hỗ trợ. Dùng .venv-vci riêng đã có Python3.12/pip;
SDK Windows5.2.1 chưa cài vì automatic approval review lỗi capacity không thực
thi escalated download. Không phải package đã được xác nhận thiếu hoặc bị đánh
giá unsafe. Lệnh để người dùng tự cài và chạy:
`tmp/vci_local_handoff_20261102_v1/CHAY_LOCAL.txt`.

Runner `scripts/run_vci_calendar_local_v1.py` hỏi key bằng getpass (ký tự ẩn),
chỉ một key/lượt, stdin cho child; không gửi key qua chat/câu lệnh. Chỉ tài khoản
mà người dùng có quyền sử dụng và còn suất thiết bị laptop; không luân phiên key
để vượt hạn mức. Local không tự giải quyết lỗi đăng ký thiết bị ở tài khoản cũ.
State SDK riêng cố định data/corporate_actions/private/vnstock_vci_local_v1,
không đưa vào ZIP/chia sẻ hoặc xóa để retry. Giữ nguyên .venv market4.0.7.

--check chỉ verify frozen bundle/config/scope và SDK version, không đọc key hoặc
login. Khi chạy thật giữ cùng 84 windows/1522 inventory/8s/cap/budget và fail-closed
như monthly handoff, không đổi PIT/identity/canonical. Kết quả mới ở
data/corporate_actions/work/vci_local_v1; gửi OUTPUT_ZIP được in cuối lượt.
Không dùng ZIP Kaggle auth-error0 dòng để resume. Chỉ --resume ZIP budget-stop
đã verify; SDK auth/source/schema/cap failure vẫn stop. Native Windows SDK/auth
chưa test; 20 targeted tests/compileall/synthetic smoke và fake SDK chỉ chứng minh
orchestration, không chứng minh tài khoản/key khác được cấp quyền hoặc có dữ liệu.

## VCI hiện dừng vì DEVICE_LIMIT — kiểm tra trong phiên tương tác

Diagnostic V2 đã được user chạy và kiểm tra: SDK5.2.1, authenticated=false,
tier=guest, có local ID nhưng chưa có bằng chứng đăng ký server-side. api_base
null không phải sai endpoint; API_KEY env false không phải thiếu Secret vì key
qua stdin. Vẫn chưa giải thích web0/SDK1. Handoff diagnostic dưới đây là evidence
đã chạy, không chỉ thị lặp lại. Monthly tiếp tục BLOCKED tại auth; cần đối chiếu
đăng ký thiết bị có thẩm quyền, không tự retry/gỡ/profile/guest fallback.

Diagnostic hiện hành là V2:
`tmp/vnstock_environment_diagnostic_v2_20261102_v1/CHAY_CELL_V2.txt`.
Thay toàn bộ nội dung cell diagnostic cũ, chỉ chạy cell đó và gửi ZIP
delta-vnstock-env-v2-*.zip. V1 bị overall status ghi đè account status, không dùng
việc thiếu account data trong ZIP V1 để kết luận guest/sai key. Metadata host
OTHER_OR_UNAVAILABLE cũng không chứng minh sai endpoint. Không đổi key/profile
hoặc gỡ thiết bị dựa vào những nhãn này.

Monthly ZIP 015050 và020431 đều SDK_LOGIN/DEVICE_LIMIT,0/84 tháng và0 dòng,
không tự retry. Ảnh web0 và lỗi SDK báo1 vẫn chưa được giải thích. Handoff
`tmp/vci_monthly_repeat_device_limit_20261102_v1/CHAY_CELL_NAY.txt` chỉ diagnostic:
trong monthly notebook đang mở, thêm code cell cuối, dán toàn file và chạy riêng
cell đó. Không chạy lại các cell khác/Run All/Save & Run All hoặc cài SDK. Không
nhập API key/Secret mới. Nếu phiên đã tắt, chưa chạy: session mới không phải máy
đã lỗi. Tải ZIP delta-vnstock-env-*.zip gửi kiểm tra; chưa certify fix hoặc source
acceptance. Script không gọi login/calendar, nhưng SDK status có thể refresh
licensing; không claim0 HTTP. ZIP chỉ allowlisted metadata, không SDK auth store.

## Notebook thu thập VCI theo tháng — handoff 02/11/2026

Sau successful pilot V3, dùng notebook mới
`tmp/vci_calendar_monthly_20261102_v1/DELTA_VCI_Monthly_2019_2025.ipynb`.
Import vào Kaggle, CPU và Internet ON, Add-ons > Secrets > bật VNSTOCK_API_KEY,
Save Version > Save & Run All. Lần đầu không cần Dataset hoặc ZIP HNX/VSDC.
Chỉ một notebook; không dán key vào cell. Nếu gặp DEVICE_LIMIT, giữ ZIP để review
thiết bị ở trang tài khoản, không tự đổi định danh hoặc tài khoản để tiếp tục.

Notebook đã bật thu thập, không cần sửa True/False. Có 84 khoảng, đầu là riêng
31/01/2019, tiếp theo từng tháng tới hết 12/2025. API lấy nhóm dividend (cổ tức
và phát hành) toàn thị trường; C8 v2 1522 mã là inventory đối chiếu, không claim
historical identity. Giữ SDK exports toàn bộ và review cho mã ngoài scope,
thiếu ex/record (applicability chưa đánh giá), thiếu cash fields, duplicate trong
và giữa các tháng. Không xóa dòng/đoán ngày/tự normalize timezone/nhập canonical.

Log có QUERY_STARTED rồi QUERY_SAVED cùng month/rows/completed/total. Kết thúc
COLLECTION_EXPORTS_READY_FOR_REVIEW và completed_window_count=84 chỉ nghĩa là
đã lưu tất cả cửa sổ truy vấn; không chứng nhận dữ liệu lịch sử đầy đủ/revisions.
Mỗi tháng có sdk_export.json, query.json, review.json và commit.json. Cấp root
có plan/scope/pilot_gate, cross_window_review, result và manifest. Output mới
`/kaggle/working/delta-vci-state-<UTCstamp>.zip` chỉ chứa state của collector.
SDK exports không phải original HTTP bytes, underlying HTTP count chưa đo.

Delay 8s trước mỗi query, cap20000, session1800s, parent watchdog3600s. Thời gian
chờ tối thiểu cho 84 query là 672s, chưa gồm install/login/network/ghi/export;
không cam kết thời gian hoặc coverage. Nếu STOPPED_TIME_BUDGET, tải ZIP mới
nhất, upload thành Dataset private rồi attach đúng một ZIP delta-vci-state-*.zip
vào notebook, chạy lại không sửa code. Verify checksum/config/scope/commit trước
auth, copy byte cũ sang thư mục mới và skip tháng đã commit. Không xóa ZIP cũ.
Nếu lỗi auth/source/schema/cap/timeout/integrity thì dừng và gửi ZIP để review;
không tự retry hoặc thu hồi thiết bị. Giữ HNX source-stop và các artifact cũ.

Code/config/tests đã verify offline; chưa chạy live full-period acquisition.
Source/PIT/identity/canonical acceptance vẫn MANUAL_REVIEW_REQUIRED ở stage sau.

## Pilot VCI độc lập sau source-stop HNX — 02/11/2026

**Hiện HNX acquisition đang STOP sau 403 ở lượt 2.** Các hướng dẫn chạy HNX bên
dưới là lịch sử vận hành, không phải chỉ thị retry. User không dùng phương án gửi
câu hỏi/liên hệ nguồn. Không sửa resumable=false hoặc giảm delay/đổi IP để chạy lại.

Trong archive VSDC V3, 670/754 mã HNX pending có 4652 observations; 84 mã chưa có
trong stream này. Tất cả 4652 thiếu ex_date, nên không tự coi là đã thay thế HNX.
3279 record_date nằm trong kỳ nghiên cứu chỉ là inventory, không chứng minh đúng
ex_date window; timestamp UPDATE vẫn không phải publication đã xác minh.

Phương án đang chuẩn bị là API calendar của nguồn VCI qua SDK được tài liệu hoá.
Notebook hiện hành:
`tmp/vci_calendar_pilot_v3_20261102_v1/DELTA_VCI_Calendar_Pilot_V3.ipynb`.
V1/V2 dừng setup; auth diagnostic xác định VNSTOCK_AUTH_PROTOCOL của SDK5.0.1,
action update library. Official package index hiện list 5.2.1 latest; V3 pin
direct official Linux wheel + SHA256, không dựa heading docs 5.0.1 đã cũ. Giữ
secret hiện tại và bật quyền cho notebook V3. Lượt V3 đầu gặp DEVICE_LIMIT vì
thiết bị Windows đã chiếm 1/1 suất; lượt ZIP 20261102T012739941192Z sau đó đã
đăng nhập và xuất dữ liệu thành công. V3 giữ redacted SDK code/message/action
nếu còn lỗi, không auto retry.
Chỉ dùng một notebook, CPU/Internet ON, không cần Dataset input hoặc HNX state.
Đăng nhập [trang tài khoản Vnstock](https://www.vnstocks.com/account) để lấy key,
thêm Kaggle Secret VNSTOCK_API_KEY và bật quyền cho notebook. Không đưa key vào
code/chat. Import notebook và Save & Run All. Cài riêng vnstock==5.2.1 trên Kaggle;
không nâng cấp .venv của repository hoặc thay market adapter pin.

Pilot thử ba tháng 02/2019, 11/2024 và 08/2025, nghỉ 8s giữa logical calls, process
timeout 180s sau bước install, không outer retry. Khi SDK báo lỗi, schema/source
metadata không khớp hoặc kết quả chạm cap 20000, dừng để review. ZIP cuối chỉ gồm
execution report và SDK exports; không gồm auth cache, key hoặc SDK stdout/stderr.
Nếu install/auth fail thì chưa claim có dữ liệu; status/result phản ánh stage thực.

Theo [tài liệu Reference](https://www.vnstocks.com/docs/vnstock/tham-chieu-reference),
calendar có ex_right_date/record_date và trường sự kiện. Theo
[cấp quyền](https://www.vnstocks.com/docs/vnstock/tham-khao/cap-quyen-va-gioi-han),
route cần tài khoản Cộng đồng hoặc cấp phù hợp. Nguồn SDK này độc lập với endpoint
HNX đang từ chối; thư viện không tự cấp quyền dữ liệu của bên thứ ba. Pilot thật
đã trả 388 dòng/336 ticker trong ba tháng mẫu (67/133/188 dòng), 272 DIV và 116 ISS.
272 dòng cash có value>0/ex/record/payout; 8 dòng ISS thiếu ex/record. Giữ nguyên
3 dòng payload trùng (VIC/GAS/VC3). Nhóm dividend gồm cổ tức và phát hành theo
tài liệu SDK; phải phân loại ISS trước canonical. Public_date có ở 388 dòng nhưng
mọi ngày đều xuất cùng giờ 17:00Z; không coi đó là giờ công bố thật. Đổi UTC+7
để review khớp hai mẫu PVS cash700/ex2024-11-13 và ACV ratio0.6458/ex2025-08-07;
chưa áp dụng normalization/PIT policy. 327 ticker khớp inventory C8 v2 1522 mã,
9 ticker ngoài scope giữ evidence. Chưa chứng minh đầy đủ 2019-2025, revisions
hoặc dữ liệu cho mọi mã; access/export PASS, overall PARTIAL, chưa chạy bulk.
Audit: `tmp/vci_pilot_v3_success_audit_20261102_v1/audit.json`.
SDK exports không phải original HTTP bytes; logical calls không được ghi là số
HTTP requests thực tế. Review những giới hạn này trước bulk/source acceptance.
PIT/identity/source priority/canonical/final freeze không được tự promote.

## Kaggle cho phần bổ sung HNX — handoff 02/11/2026

User đã duyệt thu thập V5; bốn state lượt 1 dừng sau một giờ do budget, không lỗi
nguồn. Đã xử lý 273/1117 mã, còn 844 mã. Notebook V5 gốc trong gói cũ giữ nguyên
False để bảo toàn handoff lịch sử; dùng notebook resume mới ở đoạn dưới cho lượt 2.

Theo yêu cầu chạy tới hết phần còn lại, import bốn notebook
`tmp/hnx_kaggle_resume_to_completion_20261102_v1/DELTA_HNX_Resume_Shard_0.ipynb`
đến Shard_3.ipynb. Mặc định RUN_COLLECTION=True, MAX_SECONDS=21600 là deadline
chung; MAX_REQUESTS=1000 cho mỗi chặng. Khi chạm request budget, notebook tự xuất
state ZIP, nghỉ 8 giây và resume trong cùng phiên. Không cần upload thủ công giữa
các chặng. Chạy hết pending thì dừng; source/SSL/integrity/unknown/user stop vẫn
dừng ngay. Deadline gồm thời gian điều phối; chặng đang chốt/export có thể thêm
overhead. Phiên bị nền tảng dừng hoặc vượt 6 giờ vẫn cần resume sau, không đảm bảo
mọi nguồn/mã sẽ thành dữ liệu đã duyệt.

Mỗi notebook gắn Dataset state V5 mới nhất đúng shard (ví dụ
delta-hnx-state-s1-round1), chỉ một state/shard, CPU và Internet ON, Save & Run All.
Tên Dataset không cần thêm vào code. Giữ SHARD_INDEX/root/hash pin; không cần ZIP
code mới hoặc chỉnh code trong state. Bootstrap byte-identical V5, wrapper nhúng
trong notebook mới, code pin và batch resume contract cũ giữ nguyên. Log mới có
BẮT ĐẦU CHẶNG và session_chunk/pending_tickers_count; kết thúc không còn pending
in NO_PENDING_TICKERS_REVIEWS_REMAIN. Quarantined và field reviews vẫn chờ review.

Gói hiện hành nằm ở `tmp/hnx_kaggle_export_20261102_v5/`: `delta-hnx-kaggle.zip`
và `DELTA_HNX_Shard_0.ipynb` đến `DELTA_HNX_Shard_3.ipynb`. Đây là gói mới riêng
cho HNX detail, không dùng notebook/bootstrap collector cũ. Giữ 4 shard và 20 mã
cũ tại local; không cần upload chúng để thu thập phần HNX mới. Một số bài local đã
có có thể được collect lại như snapshot mới, không xóa hoặc overwrite bản trước.

V5 giữ intermediate GlobalSign đã pin và verify offline tới root vốn trusted;
không tắt SSL hoặc hạ strict flags. V2 preflight user đã gửi là BLOCKED_TLS, chưa
collect gì. V3 Shard 3 đã SSL PASS nhưng dừng ở AAV empty-query DOM; V4 sửa
case exact này, lưu scope review và không tự certify không có historical event.
V5 thêm quarantine mã lỗi rồi chuyển mã khác, giữ evidence và partial data.
Bản V5 cần Dataset input V5 và notebook V5 cùng manifest pin; tạo
notebook mới chỉ gắn Dataset V5, giữ RUN_COLLECTION=False theo yêu cầu hiện tại.
ZIP cũ giữ làm evidence; pin cũ không restore vào V5. Nếu thiếu OpenSSL CLI,
trusted root hoặc validation fail, script vẫn dừng và export diagnostics.

| Index | All-market assignment | Bootstrap trong assignment | HNX/UPCOM bổ sung |
|---|---:|---:|---:|
| 0 | 381 | 6 | 280 |
| 1 | 381 | 5 | 280 |
| 2 | 380 | 4 | 279 |
| 3 | 380 | 5 | 278 |
| Tổng | 1.522 | 20 | 1.117 |

Không cộng bootstrap 20 vào cả bốn shard. Owner mã đã collect giữ theo actual
batch_results; index mới là work assignment, không promote historical identity.
Raw gộp/canonical reconciliation là stage sau; hiện chỉ có một ownership index chung.

1. Tạo Dataset **Private** trên Kaggle, upload `delta-hnx-kaggle.zip`. Có thể Kaggle
   giữ ZIP hoặc giải nén thành files; notebook hỗ trợ cả hai. Không upload .venv,
   .git, credentials, market prices hoặc toàn bộ raw cũ.
2. Tạo notebook Python bằng Import/Upload từng file `.ipynb` đã cung cấp. Add Input
   Dataset vừa tạo. Chọn CPU/Accelerator=None, bật Internet trong Session options.
   Quota và số notebook được chạy đồng thời lấy từ giao diện/account của bạn,
   không mặc định hai tài khoản tương ứng bốn IP. Terms hiện hành yêu cầu một
   account/person; chưa có bằng chứng ngoại lệ tài khoản cũ/two-phone verification.
3. Giữ `RUN_COLLECTION=False` ở lần đầu, chạy **Save Version → Save & Run All**.
   Notebook chỉ kiểm environment và một public HTTPS HNX request; export state ZIP
   dưới `/kaggle/working/delta-hnx-state-sN-<timestamp>.zip`. Trong state, xem
   `kaggle_runs/shard_N/run-.../preflight/environment.json` và `result.json`.
4. Nếu `PASS_CURRENT_ENVIRONMENT_ONLY`, có thể đổi `RUN_COLLECTION=True`, giữ
   nguyên `SHARD_INDEX`, Save & Run All. Nếu `BLOCKED_PREFLIGHT`, không collect;
   gửi state ZIP/log để kiểm tra trust-store/chain; không tắt SSL hoặc tự thêm CA
   chưa xác minh. V5 đã kèm intermediate verified, không cần user cài certificate.
   Preflight PASS hiện tại không tái dựng môi trường Kaggle cũ.
5. Notebook V5 gốc mặc định mỗi run tối đa 1.000 requests hoặc 3.600 giây. Notebook
   resume mới ở đầu hướng dẫn dùng deadline chung 21.600 giây và tự nối chặng
   1.000 requests; một worker, actual interval 8 giây mỗi job. Tăng concurrency
   chỉ trong hạn mức được phép.
   Không có shared limiter/host-stop giữa notebook, nên 8 giây chỉ kiểm soát từng
   job và tải trung bình, không bảo đảm global spacing. Khi một job gặp source
   block/rate-limit/challenge, dừng các notebook HNX còn lại; không đổi IP retry.
6. Sau mỗi saved run, tải **state ZIP** về. Run tiếp trên session mới: attach một
   state gần nhất **đúng shard** làm Input, có thể giữ input Dataset ban đầu.
   Notebook ưu tiên state, verify checksum và giữ fixed work root để references
   không gãy. Nó tự resume completed units, dùng output mới và export ZIP mới.
   Không attach hai state cùng shard hoặc đổi SHARD_INDEX. Mã lỗi được quarantine,
   resume skip để chờ review; source/access/SSL/integrity stop non-resumable không
   tự reset. Nếu saved session bị cưỡng bức dừng
   trước export, giữ notebook output/workspace; không claim đã có state ZIP đầy đủ.
7. Gửi bốn state ZIP sau thu thập về local để audit/import theo ownership và
   provenance. Đợt này chỉ bổ sung nhóm CORPORATE_NEWS/title candidates HNX;
   review PIT/identity/terms còn mở, không phải final `corporate_actions`.

Lỗi riêng mã (profile/list/article/data layout; typed timeout; plain HTTP
404/410/500/502/503/504) ghi `collection_issues.csv` rồi chuyển mã khác, không tự
retry URL đó. Good observations đã đọc trước lỗi giữ nguyên. `quarantined_tickers`
là mã chờ kiểm tra, không nằm trong handled hoặc pending; resume không tự thử lại.
HTTP 401/403/429/challenge/Retry-After, SSL/DNS/unknown transport, checksum/config/
IO lỗi vẫn stop nguồn/run; user phải giữ các safeguards và dừng các job cùng nguồn.

Offline audit xác nhận 1.106 HNX TLS failed receipts (276/278/277/275), không HTTP
response, trong khi VSDC/HOSE vẫn trả 200. Chưa xác định do Kaggle, CA image,
server certificate chain hoặc route; historical environment metadata chưa có.
31.174 request receipt occurrences gồm 31.142 physical requests và 32 cache hits;
đừng coi cache receipts là network requests mới. Four supplied notebook pages
không đọc được qua web tool; không suy chúng private hay đã kiểm runtime trên đó.

Tham khảo: [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks),
[Kaggle Terms](https://www.kaggle.com/terms),
[Kaggle Docker image](https://github.com/Kaggle/docker-python),
[Python SSL](https://docs.python.org/3/library/ssl.html).

## Bổ sung thông báo chi tiết HNX — batch V1 (01/11/2026)

Runner mới đọc C8 v2 cố định từ repository, source assignment HNX/UPCOM
1.117 mã trong 1.522 rows; không dùng 905 làm historical universe. Chỉ thu thập
nhóm CORPORATE_NEWS, title candidates trong publication-list window 2019–2025,
giữ mọi list rows. Chưa đầy đủ các nhóm tin/revisions/historical identity, không
tự merge vào canonical. Raw/candidate cũ giữ nguyên. Live integration PVS/ACV
đã tạo 9 observations với 7 requests mới, tái sử dụng 2 detail samples.

Chạy trong PowerShell đã activate `.venv`, tại repository:

```powershell
$hnxOut = "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\hnx_supplement_$(Get-Date -Format yyyyMMdd_HHmmss)"
python "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\collect_hnx_announcements_batch_v1.py" --max-requests 1000 --max-seconds 3600 --output $hnxOut
Get-Content -LiteralPath "$hnxOut\result.json" -Raw
```

Đây là một run có ngân sách, không cam kết hoàn thành toàn scope trong một giờ.
Lô 9 observations cũ giữ làm evidence; code/config contract đã thay đổi nên không
seed/resume trực tiếp lô cũ qua strict contract guard. Seed/resume chỉ khi contract
vẫn khớp; không xóa hoặc sửa hash/stop để ép chạy.
Một worker, shared interval tối thiểu 2 giây, TLS verification, no redirect/retry.
Thêm `--dry-run` để chỉ xem plan, không tạo output/network. Có thể chọn source work
subset bằng `--tickers PVS ACV` hoặc `--exchange HNX`/`--exchange UPCOM`; đây không
phải research-sample filter. Không chạy đồng thời các bản để né host limits.

Nếu `resumable: true` và còn pending tickers, chạy tiếp sang output mới:

```powershell
$hnxPrevious = $hnxOut
$hnxOut = "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\hnx_supplement_$(Get-Date -Format yyyyMMdd_HHmmss)"
python "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\collect_hnx_announcements_batch_v1.py" --resume-from $hnxPrevious --max-requests 1000 --max-seconds 3600 --output $hnxOut
Get-Content -LiteralPath "$hnxOut\result.json" -Raw
```

Resume giữ nguyên scope/date/source/code contract, verify các artifacts được tham
chiếu và không tải lại completed work. `seed-batch` cho phép mở rộng work scope từ
lô nhỏ đã verify, vẫn giữ C8/source/date/code contract; không kết hợp seed và resume.
Không đổi code giữa các lượt resume. Ctrl+C tạo checkpoint khi có thể; kill đột ngột
phục hồi completed sealed steps từ journal. Unit chưa seal giữ raw, có thể phải
acquire lại unit đó; không overwrite hoặc xóa evidence cũ. Lỗi riêng mã được
quarantine rồi tiếp tục; global source/access/SSL/integrity stop (`resumable: false`)
phải review, không tự retry/bypass.

Output: `observations.jsonl`, `review_queue.csv`, `collection_issues.csv`, `raw/` (detail và list receipts),
`work/` immutable units, `progress.jsonl`, `checkpoint.json`, `request_log.jsonl`,
`result.json`, `manifest.json`. `handled_tickers` là xử lý xong candidate work đã
discover, không chứng nhận full history; kiểm tra `discovery_page_limit_tickers`.
`source_history_coverage` vẫn INCOMPLETE_NOT_CERTIFIED.

Review không phải lỗi đồng nghĩa và không phải file signed approval:

| Review | Xử lý trong acquisition | Gate còn mở |
|---|---|---|
| Public time unverified | Giữ raw clock, minute precision, unknown timezone, exact provider ID và cả list/detail receipts | Chưa accepted PIT; cần semantic/timezone/version evidence và policy đã duyệt |
| Historical identity chưa certified | Giữ ticker/exchange là source context; không gán verified historical security_id | Cần hồ sơ interval niêm yết/chuyển sàn riêng |
| Payment date absent (INFO) | Giữ null; không lấy ex/record date thay thế | Không là required term theo contract hiện tại; stock entitlement không tự suy cash payment date |
| Missing/conflicting required term | Giữ observation và review, không tự đoán | Không tự approve event hoặc research readiness |

## Upgrade hiện hành — multi-source completion 1.2.0

Work unit: `UPGRADE_CORPORATE_ACTIONS_V1_MULTI_SOURCE_COMPLETION`.
Chạy `collect --multi-source` để dùng contract 1.2.0. Giữ nguyên các workflow 1.0/1.1
ở phần sau; không migrate hoặc overwrite artifacts cũ.

### Thu thập và bổ sung theo field

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py collect --multi-source --universe M3/collection/scope_v1.csv --start 2019-01-31 --end 2025-12-31 --max-pages 2 --max-details 8 --max-requests 40 --output M3/collection/multi-001 --dry-run
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py collect --multi-source --universe M3/collection/scope_v1.csv --start 2019-01-31 --end 2025-12-31 --max-pages 2 --max-details 8 --max-requests 40 --output M3/collection/multi-001
```

Config thực thi:
[`corporate_actions_multisource_v1.json`](../configs/data/corporate_actions_multisource_v1.json).
Budget là giới hạn toàn run, không phải mỗi source. Input scope vẫn cần historical
identity interval/ISIN evidence để event đạt data verification; `--tickers` chỉ hỗ trợ
discovery, không tạo security ID giả.

Mỗi source tạo observation riêng gồm values/raw values, source URL/hash, raw terms,
published/observed time và parse status. Reconciliation mới ghép fields; không đòi
một source chứa mọi field. VSDC có thể cung cấp type/record-date/ratio; HNX hoặc HOSE
cung cấp ex-date; IR bổ sung subscription terms. Matching cần ticker/exchange/component
type và record-date khớp duy nhất, hoặc explicit reference có evidence. Không ghép
theo ticker và ngày gần nhau; collision nhiều announcement/tranche giữ review.
Cash và stock components vẫn là hai event IDs, cùng group khi cùng ex-date.

Để bổ sung IR/vendor/official evidence theo field, dùng JSONL. Mỗi row có source_type,
source_url, raw_terms, source_published_at nếu biết, và object `values`. Phải có ticker,
exchange, event_type và record-date/reference đủ để link; chỉ thêm field tìm được.
Không fill zero cho field chưa biết. Xem
[example bị khóa chống nhập production](templates/corporate_actions_field_observation.example.jsonl).
Thay toàn bộ ví dụ bằng evidence thật; `is_example=true` bị validator từ chối.

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py replay --collection M3/collection/multi-001 --field-input M3/collection/ir_supplement.jsonl --output M3/collection/multi-supplement-001
```

IR và vendor manual inputs đi qua cùng normalization, matching, reconciliation và
field review. `ISSUER_IR` cần reviewer xác nhận website/wording chính thức; `CAFEF`,
`VNDIRECT` hoặc `VENDOR` là secondary. Vendor-only field không được xem là authoritative.
Tỷ lệ `15%` và `0.15` được so sau normalization; `64.58%` và `6458%` giữ nguyên hai
raw values và conflict, không tự chọn VSDC thắng. Rule tự chọn source priority vẫn tắt.

### Review đúng field

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py review-report --collection M3/collection/multi-001 --output M3/collection/field-reviews-001.csv
```

Queue 1.2.0 dùng `review_id`, `event_id`, `conflicting_field`, `review_reason`,
`observations` và recommended check. Object observations giữ từng nguồn, raw/normalized
value, observation ID và timing. Chỉ đọc field đang thiếu/conflict; không bắt buộc
review lại toàn event vì một field có vấn đề. Các fields không conflict giữ kết quả.

Chỉ sửa các cột review, không sửa immutable evidence:

| Cột | Điền thế nào |
|---|---|
| `review_status` | PENDING, APPROVED, REJECTED hoặc NEEDS_MORE_EVIDENCE. |
| `chosen_observation_id` | Copy đúng ID chứa giá trị được nguồn authoritative xác nhận. |
| `reviewed_by`, `reviewed_at` | Người review và thời điểm thực, không trước collection/observation. |
| `review_decision` | USE_OBSERVATION để chọn field; USE_REVISION để chọn correction rõ lineage; ACKNOWLEDGE_TIMING_LIMITATION chỉ ghi nhận warning; REJECT_EVENT đi cùng REJECTED. |
| `review_note` | Lý do, đoạn/source evidence; có thể ghi "USE_VSDC_VALUE: ...". |

Ví dụ ratio conflict: chọn observation VSDC có literal `64.58%`, ghi USE_OBSERVATION
và note xác nhận; observation vendor `6458%` vẫn được lưu là loser evidence. Không
nhập lại một giá trị mới trong queue. Nếu không có observation nào đủ đúng, bổ sung
evidence vào run mới bằng replay; APPROVED không tự sinh missing field hoặc identity.

### Hai dimension verification và PIT

`event_data_verification=VERIFIED` nói identity, matching và required fields đã pass;
`verification_status=AUTO_VERIFIED/MANUALLY_VERIFIED` trong **contract 1.2.0** chỉ có
nghĩa này. `pit_timing_verification` độc lập: COMPLETE hoặc PARTIAL.

Một event terms đúng nhưng thiếu historical public timestamp không bị gọi là data
invalid. Nó có thể nằm trong ledger với PIT PARTIAL được ghi rõ. **Điều này không
promote historical research/M3 eligibility và không cho phép backtest dùng knowledge
ở thời điểm trước khi thông tin được biết.** Downstream vẫn phải kiểm version,
PIT status và `available_at <= decision_at`; quyết định readiness/basis cuối cần review.

Mỗi field chọn được authoritative evidence có public timestamp sẽ giữ timestamp đó;
nếu chỉ có first observation thì dùng actual observed_at và flag field timing incomplete.
Composite available_at không sớm hơn knowledge time của field bắt buộc được biết muộn
nhất. Không gán timestamp VSDC cho ex-date mới lấy từ HNX. Manual input không được
backdate observed_at: tool dùng thời điểm import thực tế, giữ file input nguyên gốc.
HOSE calendar postedDate là **event date theo route/UI**, không phải publication time.

### Revision và effective record

Partial evidence input có thể khai báo `revision_status=CORRECTION`, `revision_of`
(list source URLs hoặc observation IDs), `revision_number`. Bản gốc không bị ghi đè.
Queue `__revision__` yêu cầu USE_REVISION với signed decision. Chỉ chấp nhận correction
authoritative có linkage rõ, required fields đầy đủ và chuỗi supersession không còn
nhánh/cycle unresolved. Không chọn latest chỉ bằng publication date hoặc source tier.
Revision chỉ có một số fields mà chưa chứng minh phần còn lại tiếp tục có hiệu lực
vẫn review; không tự inherit terms bị thiếu. Thay đổi component type/matching chưa rõ
cũng giữ review. Canonical lưu effective_revision_id và toàn bộ revision lineage;
available_at của bản sửa không bị lùi về bản gốc.

### Build, provenance và coverage

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py validate --collection M3/collection/multi-001
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py build --collection M3/collection/multi-001 --reviews M3/collection/field-reviews-001.csv --output artifacts/corporate_actions/corporate-actions-multi-001
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py coverage --collection M3/collection/multi-001 --reviews M3/collection/field-reviews-001.csv --output M3/collection/field-coverage-001.json
```

Canonical giữ `field_provenance` cho từng field: status, selected observation IDs,
mọi source/raw/normalized value/hash/timing, reconciliation rule. Ví dụ ex-date có
source HNX, ratio có source VSDC; primary_source_url chỉ là compatibility metadata,
không đại diện cho authority của tất cả fields. `observations.jsonl` giữ source facts
nguyên trạng, `event_decisions.jsonl` giữ dispositions và schema 1.2.0 giữ PIT/review lineage.

Report đếm verified type/ex-date/terms/identity, PIT complete, review, missing fields;
`source_completeness_matrix.csv` đo fields thực sự parse được từ collected evidence.
Các số của matrix là source observations, không phải universe completeness. Field
completion rate không bao gồm identity/PIT certification. NO_EVENT_CONFIRMED vẫn cần
full-window/all-types attestation độc lập; 0 event hoặc 100% source hit trong pilot
không chứng minh đã rà hết lịch sử. `--attestation` dùng coverage CSV legacy; overall
coverage pass vẫn fail-closed nếu identity/PIT/required fields còn thiếu.

### HOSE/UPCOM audit và pilot thực

HOSE homepage có JS shell **nhưng public sources tồn tại**. Audit không gửi credentials:

| Route official đã kiểm | Kết quả |
|---|---|
| api.hsx.vn/n/api/v1/News/NewsFeed và NewsByCateFeed/21 | RSS public HTTP 200. |
| api.hsx.vn/q/api/v1/search, indexName=securities | Search public HTTP 200; lấy unique exact ticker/ISIN/provider ID. |
| api.hsx.vn/n/api/v1/1/news và news/{id} | JSON public HTTP 200. |
| api.hsx.vn/n/api/v1/1/news/securities/{id}/3 | Event calendar public HTTP 200; adapter hiện hành. |
| api.hsx.vn/m/api/v1/1/mediafiles/1/{newsId} | Official media-file discovery HTTP 200. |
| staticfile.hsx.vn/Uploads/... | Official PDF download HTTP 200; text-based PDF adapter optional pypdf, scan/no text layer → manual, không OCR trong stage. |

Để kiểm PDF URL official đã biết, field-input row có `document_url` và ticker; transport
vẫn giới hạn approved hosts/budget/size, giữ response/hash. Không crawl toàn archive
hoặc theo URL IR bất kỳ. Source audit evidence nằm tại `tmp/ca_multi_source_audit/`.
HNX trang ACV công khai `_market_code='UC'`; cùng backend ChangePageTHQ dùng UC cho
UPCOM và NY cho listed, adapter kiểm stock/market context trước khi phân trang.

Pilot FPT/HOSE, PVS/HNX, ACV/UPCOM: 34 network requests, 24 observations. Parse lại
archive sau khi hỗ trợ alias CP và tỷ lệ locale `100:64,58` dùng **0 request mới**.
Trong envelope 2019–2025 giữ 17 event candidates; 11 verified ex-date, 9 verified
required terms; 0 auto-verified vì 0 historical identity verified và PIT đều partial.
Source hit 6/6 cặp source/ticker được thử chỉ là hit trong budget. IR/CafeF/VNDirect
không có live observations trong pilot, không được ghi là live-tested.

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py replay --collection M3/collection/multi-001 --reparse --output M3/collection/multi-reparsed-001
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py replay --collection M3/collection/multi-001 --universe M3/collection/scope_verified.csv --output M3/collection/multi-identity-001
```

Replay giữ prior snapshot/hash và có thể đổi reviewed scope hoặc bổ sung field evidence
trong run mới. Không sửa raw/canonical cũ, không recompute M2 hoặc kéo M2 lookback.
Audit runtime vẫn xác nhận envelope `2019-01-31..2025-12-31`; exact required end chưa
freeze vì remote runner có thể chốt valuation sau segment. Engine bắt đầu cash, chưa
có series-construction seed contract được approved, nên stage không tự thêm buffer.
Exact next work unit khi mở collection đầy đủ là
`COLLECT_AND_VERIFY_FULL_CORPORATE_ACTIONS_V1_UNIVERSE`; không tự thực hiện stage đó.

## Tham chiếu các workflow trước

Work unit tham chiếu 1.1.0: `BUILD_SEMIAUTOMATIC_CORPORATE_ACTIONS_V1_COLLECTION_PIPELINE`.
Lệnh `collect` **thực sự tải dữ liệu public**, khác `init-template` chỉ tạo CSV trống.
Bạn không phải nhập hoặc duyệt lại mọi event: chỉ review những candidate nằm trong
`manual_review_queue.csv`. Coverage toàn universe/window là gate riêng, không được
suy từ số candidate hoặc một pilot nhỏ. Không tạo price series/return/NAV, không đổi
price basis, M2 hoặc M3 engine; Q11 vẫn `STILL_OPEN`.

CLI giữ tại `scripts/collect_corporate_actions_v1.py`; adapters ở
`src/delta_t1/ingestion/corporate_action_sources.py`, candidate/review workflow ở
`src/delta_t1/ingestion/corporate_action_collection.py`. Validator manual 1.0.0 vẫn
giữ nguyên ở `corporate_actions_v1.py`; canonical mới dùng contract **1.1.0** tại
`src/delta_t1/schemas/corporate_actions_collection_v1.json`. Không sửa artifact 1.0.0
đã build; migrate bằng run mới. Đây là data ingestion riêng, chưa nối vào engine.
Root checkout hiện tại chứa trực tiếp `src`, `scripts`, `M3`; không tạo thêm tầng
`SourceCode` lồng bên trong. Mọi thay đổi nằm trong checkout này; không sửa `TaiLieu`.

## A. Chạy thu thập tự động

Mở PowerShell tại root repository. Có thể bắt đầu với ticker mà chưa chuẩn bị CSV:

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py --help
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py collect --tickers GMX --exchange HNX --start 2025-07-01 --end 2025-12-31 --max-pages 2 --max-details 6 --max-requests 10 --output M3/collection/auto-pilot-001
```

Lệnh này query VSDC theo ticker, tải thông báo, tải lịch quyền HNX và cross-check.
Không tự tạo security ID từ ticker. Khi dùng `--tickers`, identity còn unresolved;
candidate phải được bổ sung mapping lịch sử trước khi đủ điều kiện canonical.

Để có `AUTO_VERIFIED`, chuẩn bị scope từ historical identity evidence bằng
[scope template](templates/corporate_actions_scope_v1_template.csv), gồm
`security_id,ticker,exchange,isin,valid_from,valid_to,identity_status,identity_source_url`.
Interval là `[valid_from, valid_to)`. Một identity VERIFIED cần đủ ISIN, ID, interval
hợp lệ và URL evidence; tool so identity từ thông báo với mapping này. Không tự
promote `historical_identity_ready` hoặc `research_ready` của M1/M2.

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py collect --universe M3/collection/scope_v1.csv --start 2019-01-31 --end 2025-12-31 --output M3/collection/auto-run-001 --dry-run
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py collect --universe M3/collection/scope_v1.csv --start 2019-01-31 --end 2025-12-31 --output M3/collection/auto-run-001
```

`--dry-run` không gọi network và không tạo output artifact. Default budget là 2
pages/source/ticker, 10 detail pages/ticker, 30 requests toàn run, interval ≥2 giây,
timeout 15 giây và response ≤2 MB. Config thực thi là
[`corporate_actions_semiautomatic_v1.json`](../configs/data/corporate_actions_semiautomatic_v1.json).
Các override phải nằm trong hard limits; không tự biến pilot thành crawl toàn lịch sử.
Long crawl chạy local sau source/pilot review, không continuously poll.

VSDC search lọc ticker/nghiệp vụ; không đồng nhất publication range với ex-date range.
V1 đọc các announcement trong budget rồi lọc theo ex-date rõ ràng. Missing ex-date
được giữ trong queue, kể cả record-date gợi ý ngoài window; không suy ex-date để lọc.
Publication trước window và revision sau window có thể cần cho event trong window.
Do đó bounded search không chứng minh đã thu đủ hoặc đã tìm hết corrections.

## B. Nguồn được hỗ trợ và kết quả

| Nguồn | Adapter và trạng thái |
|---|---|
| VSDC | IMPLEMENTED + TESTED live: public ticker search, bounded pagination và HTML notice; source coverage PARTIAL. |
| HNX | IMPLEMENTED + TESTED live: lịch quyền HNX listed equities, pagination, explicit ex/record/payment dates; thiếu terms/public timing trong calendar. |
| HOSE | NOT_IMPLEMENTED: homepage pilot trả JavaScript shell, chưa có stable adapter được xác minh; dùng manual evidence. |
| HNX UPCOM | NOT_IMPLEMENTED: chưa tự suy market code hoặc reuse listed-equity route. |
| Issuer IR/vendor | Manual supplement; chưa có crawler chung cho các website phân tán. |

HTTP 401/403/429 hoặc challenge dừng host, không retry/bypass login, anti-bot hoặc
paywall. Redirect không được theo ngầm. Layout/content thay đổi sinh limitation,
không diễn giải response rỗng thành không có event. Lỗi lưu trong `source_checks.json`.

Output của một collection run:

- `raw/response-*.bin`, `requests.json`: archive bounded response, URL/method/body,
  status, fetched time và SHA-256. Không crawl/download attachment PDF/OCR tự động.
- `raw_candidates.jsonl`: parsed candidates gốc và evidence, giữ cả components.
- `corporate_actions_candidates.csv`, `candidates.jsonl`: normalized values,
  validation issues, source authority và classification.
- `manual_review_queue.csv`: chỉ những candidate chưa đủ điều kiện auto.
- `out_of_window.jsonl`: candidate có ex-date rõ nằm ngoài window; vẫn giữ evidence.
- `plan.json`, `scope.csv`, `source_checks.json`, `manifest.json`: scope/budget,
  source limitations và checksums; không overwrite run.

## C. AUTO_VERIFIED được quyết định thế nào?

Tất cả structural gates phải pass: identity interval/ISIN phù hợp, event type rõ,
ex-date và required terms đầy đủ, source authoritative, normalization xác định,
timestamp có evidence, không duplicate/conflict/revision/mixed ambiguity unresolved.
Secondary không bắt buộc. VSDC và HNX chỉ ghép khi ticker/exchange/type/record-date
khớp duy nhất; field mâu thuẫn giữ cả hai giá trị để review.

`confidence_score` là heuristic chất lượng collection, không phải xác suất đúng hoặc
tín hiệu lịch sử: 0.95 khi mọi gate pass, 0.99 nếu có cross-check, tối đa 0.4 khi review,
0 khi invalid. Score cao không thay thế gate.

VSDC mẫu hiện có timestamp "Cập nhật" không ghi timezone; HNX calendar không có
public timestamp. Tool giữ text này, không tự đặt timezone hay lùi knowledge về ngày
thông báo. Khi timing chưa đủ, dùng `FIRST_OBSERVED_AT_ONLY` tại fetched time và review.
Nếu HNX bổ sung ex-date còn thiếu, composite available time không sớm hơn thời điểm
field đó được biết. Không lấy timestamp VSDC gán ngược cho ex-date vừa thấy ở HNX.

Pilot live ngày 01/11/2026: 9 requests, scope GMX/HNX nửa cuối 2025, 3 candidates
được giữ (hai event có ex-date trong window và một missing-ex-date chưa loại được).
Các candidate đều MANUAL_REVIEW; không giả AUTO_VERIFIED để làm đẹp kết quả. Đây
không phải production coverage hoặc historical identity certification.

## D. Review thủ công đúng queue

Tạo một bản queue để chỉnh sửa; giữ collection run nguyên vẹn:

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py review-report --collection M3/collection/auto-run-001 --output M3/collection/reviews-001.csv
```

Mỗi row có reason, candidate values, conflicting values nếu có, hai source URLs và
recommended check. Chỉ sửa năm cột review; không sửa ID, evidence hoặc candidate values:

| Field | Cách xử lý |
|---|---|
| `review_status` | `PENDING`, `APPROVED`, `REJECTED`, `NEEDS_MORE_EVIDENCE`. |
| `reviewed_by` | Người thực sự review. |
| `reviewed_at` | Thời điểm review thực, ISO timestamp có timezone, không trước collection. |
| `review_decision` | `USE_CANDIDATE` khi approve; `REJECT_CANDIDATE` khi reject. |
| `review_note` | Lý do và source/đoạn evidence; ví dụ "USE_VSDC_VALUE: official notice xác nhận 64.58%; vendor formatting sai". |

Đối chiếu ticker/security interval, loại quyền, ex-date, amount/ratio, source authority,
duplicate/tranche, mixed component và correction. Không đoán event từ price jump.
Với conflict giữa hai candidate, approve row chứa giá trị có evidence và reject row
còn lại bằng decision có chữ ký; không xóa row. Approve một row khi alternatives còn
pending không đủ để promote. Không chọn source winner tự động.

`APPROVED` chỉ resolve soft review khi structural fields đã đủ. Nó không tự điền term,
identity hoặc ex-date, và không override source authority. Nếu thiếu/sai các field đó,
thu thêm evidence, nhập manual supplement và tạo run mới. Revisions và OTHER còn
quarantine; chưa có automatic effective-revision/PIT selection. Bản gốc được correction
tham chiếu cũng bị giữ review; correction chưa link rõ khiến các originals liên quan
chưa thể chứng minh effective, nên không tự promote.

## E. Manual evidence fallback

Dùng event template 1.0.0 ở phần legacy bên dưới, nhập **chỉ trường hợp cần bổ sung**:

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py collect --universe M3/collection/scope_v1.csv --start 2019-01-31 --end 2025-12-31 --manual-input M3/collection/manual_supplement_v1.csv --output M3/collection/auto-run-002
```

Manual rows đi qua cùng normalization, validation, deduplication và review. Gắn
MANUAL_EVIDENCE_INPUT; không bypass pipeline vì CSV do người nhập. Muốn đổi giá trị
phải có source evidence và run mới, không sửa `candidates.jsonl` hoặc manifest cũ.

## F. Validate và build canonical 1.1.0

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py validate --collection M3/collection/auto-run-001
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py build --collection M3/collection/auto-run-001 --reviews M3/collection/reviews-001.csv --output artifacts/corporate_actions/corporate-actions-v1-semi-run-001
```

Validate collection kiểm checksum và tái lập classification, không tuyên bố coverage.
Build chỉ xuất AUTO_VERIFIED/MANUALLY_VERIFIED vào `corporate_actions_v1.jsonl`;
mọi quyết định, rejected/unresolved records giữ trong `candidate_decisions.jsonl` và
review snapshot. MANUAL_REVIEW/INVALID/REJECTED không được downstream tiêu thụ.
`PASS` của build nói về disposition của candidate đã thu, không chứng minh event completeness.

Contract 1.1.0 giữ các field 1.0.0 và thêm `secondary_source_type`, `normalized_terms`,
`confidence_score`, năm review fields, `updated_at`, `source_evidence`, `field_sources`,
`verification_limitations`, `revision_number`, `is_latest_revision`. Hai revision fields
giữ null khi chưa biết, không giả một bản là latest. `verified_by/verified_at` legacy
không bị gán giả thành người review auto; dùng status và review fields mới.

## G. Coverage và replay

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py coverage --collection M3/collection/auto-run-001 --reviews M3/collection/reviews-001.csv --output M3/collection/coverage-semi-001.json
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py replay --collection M3/collection/auto-run-001 --output M3/collection/auto-replay-001
```

`replay` dùng raw parsed evidence đã archive để reclassify thành run mới, không network;
không phải crawl lại hoặc tự download lại source. Giữ run cũ, hash và replay lineage.

Coverage có source_checked_vsd/hose/hnx/ir, candidate/verified/manual/invalid/rejected
counts, last_checked_at và hai lớp status. `coverage_status` là NOT_YET_REVIEWED,
NO_EVENT_CONFIRMED, HAS_VERIFIED_EVENTS hoặc MANUAL_REVIEW_REQUIRED;
`completeness_status` là COVERAGE_COMPLETE hoặc COVERAGE_INCOMPLETE.
"Source checked" chỉ xác nhận đã đọc trong budget, không nói đã exhaust archive.

Bounded collector không tự xác nhận full-window completeness, kể cả không tìm thấy
event. Để chứng nhận đã rà đủ window, cung cấp coverage attestation theo header legacy:

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py coverage --collection M3/collection/auto-run-001 --reviews M3/collection/reviews-001.csv --attestation M3/collection/coverage_v1.csv --output M3/collection/coverage-attested-001.json
```

NO_EVENT_CONFIRMED cần full-window/all-types source log, reviewer/time và identity
đủ evidence; event_count=0 tự nó không đủ. HAS_VERIFIED_EVENTS vẫn có thể đi kèm
COVERAGE_INCOMPLETE. Parser/access errors phải được rà trong source_checks, không được
biến thành bằng chứng không có event. Đừng ký attestation khi chưa kiểm được archive.

## H. Điều kiện chuyển work unit

Chỉ bàn giao series khi required universe/window được owner xác nhận, coverage pass,
required terms đủ, canonical checksums đã verify, không còn unresolved review hoặc
exception đã được owner review rõ. Boundary M3/runtime và Q11 vẫn cần quyết định riêng.
Task này dừng ở collection; next work unit hiện tại là
`COLLECT_AND_VERIFY_CORPORATE_ACTIONS_V1`.

## Tham chiếu: scope window và workflow manual legacy 1.0.0

Các bước dưới đây giữ tương thích cho CSV/template và artifacts 1.0.0. Trong workflow
semiautomatic, dùng chúng để chuẩn bị supplement/attestation; ưu tiên build bằng
`--collection` để giữ classification/review lineage 1.1.0.

## Phạm vi ngày và ticker cần thu thập

Audit ngày 01/11/2026 đối chiếu kế hoạch M3 hiện hành
[`KE_HOACH_M3_SCHEMA_GITHUB_INPUT_OUTPUT.md`](KE_HOACH_M3_SCHEMA_GITHUB_INPUT_OUTPUT.md)
(mục 3.9, 7.1, 11.5) và remote commit
`1330765530afaaad4dbefcb61a6a72af839e6ecd` của `feature/indicators-v1`:

- Development: 60 decision snapshots `2019-01-31 → 2023-12-29`.
- Holdout: 24 decision snapshots `2024-01-31 → 2025-12-31`.
- Engine reference bắt đầu bằng cash, execution là phiên sau decision; event chỉ
  cần cho những return interval/holding có thực, từ sau giá mua/mark đầu tiên tới
  valuation cuối. Không cần kéo lookback momentum của M2 vào Q11.
- Cửa sổ **thu thập ban đầu** trong
  [`configs/data/corporate_actions_v1.json`](../configs/data/corporate_actions_v1.json)
  là `2019-01-31 → 2025-12-31`, inclusive theo `ex_date`. Đây là envelope theo
  decision/segment dates, có buffer đầu kỳ ngắn trước execution đầu tiên. Không
  khẳng định ngày execution đầu tiên khi chưa pin calendar/schedule thực tế.
- Publication có thể trước cửa sổ, payment có thể sau cửa sổ: vẫn giữ evidence
  cho event có ex-date trong cửa sổ. Không lọc theo publication/payment year.
- **`MANUAL_REVIEW_REQUIRED`:** runner `scripts/run_m3.py` trên remote reference
  lấy `end_date` từ next decision execution hoặc `calendar[-1]`, có thể vượt
  segment end; còn kế hoạch local quy định valuation không vượt segment end.
  Vì vậy exact minimum window cho runtime hiện tại chưa thể freeze. Không sửa
  runner, không tự cộng buffer tới một ngày 2026 tùy chọn. Nếu owner giữ runtime
  vượt segment, cần xác định calendar/schedule pin và thu thêm tới actual last
  valuation. Nếu owner giữ boundary trong segment, envelope hiện tại bao phủ
  giai đoạn 2019–2025. Đây là review riêng, không chặn xây công cụ nhập dữ liệu.
- Final Evaluation sau `2025-12-31` chưa có exact dates; chưa nằm trong config này.

Tạo **scope CSV do chủ dự án xác định**, header `security_id,ticker,exchange`, từ
historical candidate pool/execution scope của M3. Không xuất ngược từ latest ticker
membership, không chọn ticker bằng lợi nhuận và không tự xem 905 mã M2 là final
historical universe. Một `security_id` có nhiều ticker/exchange interval được ghi
thành các identity row riêng; tool so coverage theo cả ba field và không tự join.
Identity phải được reviewer đối chiếu source theo interval trước khi event VERIFIED.
Tool không promote historical identity hoặc `research_ready` của M1/M2.

## Bước 1 — Tạo template và hàng đợi kiểm tra

Mở PowerShell tại root repository. Lưu scope thực vào
`M3/collection/scope_v1.csv`, sau đó chạy:

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py --help
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py init-template --output M3/collection/events_v1.csv --universe M3/collection/scope_v1.csv --coverage-output M3/collection/coverage_v1.csv
```

Event template chỉ có header, không có dữ liệu giả. Coverage queue có từng identity
trong scope, mặc định `review_status=NOT_YET_REVIEWED`. Nếu chỉ cần event template:

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py init-template --output M3/collection/events_v2.csv
```

Header có sẵn tại [event template](templates/corporate_actions_v1_template.csv) và
[coverage template](templates/corporate_action_coverage_v1_template.csv).
Không đổi header hoặc thêm `is_example`; ví dụ nằm riêng trong `tests/fixtures`.
Command từ chối overwrite; lần tiếp theo chọn tên/version mới.

## Bước 2 — Mở nguồn chính trước

Thứ tự tìm evidence do owner yêu cầu:

1. [VSDC](https://vsdc.vn/vi/): tìm mã chứng khoán, khoảng ngày và nghiệp vụ thực
   hiện quyền; mở thông báo và attachment gốc.
2. [HOSE](https://www.hsx.vn/) hoặc [HNX](https://hnx.vn/): tìm công bố/sự kiện của
   mã trên exchange tương ứng, đặc biệt thông tin ngày giao dịch không hưởng quyền.
3. Website chính thức/IR của doanh nghiệp: nghị quyết, thông báo và đính chính.
4. CafeF, VNDirect hoặc vendor khác: phát hiện ứng viên và cross-check bổ sung.

Đây là thứ tự **tra cứu thủ công**, không phải automatic source-priority policy.
Nguồn có conflict vẫn bị giữ review dù nằm cao hơn trong danh sách. Cố gắng có một
primary authoritative source và một secondary cross-check; secondary không bắt buộc.
Primary type chọn `VSDC`, `HOSE`, `HNX`, `ISSUER_IR`; `VENDOR` không đủ để VERIFIED.
Tool kiểm domain đối với VSDC/HOSE/HNX; reviewer tự xác minh website IR thực sự của
issuer. Việc gắn source type không chứng minh tính đúng của nội dung thông báo.

## Bước 3 — Đọc đúng thông tin trên thông báo

Ghi ticker, pháp nhân/security, exchange tại thời điểm đó; loại quyền; ngày công bố,
timestamp public nếu có; ngày giao dịch không hưởng quyền; ngày đăng ký cuối cùng;
ngày thanh toán; cash amount VND/share; số cổ phiếu mới/cũ; giá đăng ký mua VND/share.
Lưu đoạn điều khoản gốc và URL trực tiếp tới thông báo, kèm URL attachment trong
`raw_terms` hoặc `notes` nếu cần nhiều nguồn chứng minh các field khác nhau.

Phân biệt năm mốc: `announcement_date` là ngày thông báo, `available_at` là thời điểm
thông tin thực sự đã public, `ex_date` là ngày giao dịch không còn quyền, `record_date`
là ngày chốt danh sách, `payment_date` là ngày thanh toán. Không dùng ex-date hoặc
record-date thay cho public timestamp. Có thể tham khảo định nghĩa ex-date tại
[thuật ngữ HNX](https://www.cn.hnx.vn/vi-vn/thuat-ngu.html).

## Bước 4 — Điền các field

Mở CSV bằng Excel/LibreOffice, đặt cột ngày/ID/tỷ lệ là **Text**; lưu CSV UTF-8,
delimiter dấu phẩy. Dùng dấu chấm thập phân, không có dấu phân tách hàng nghìn.
Ô có dấu phẩy/newline phải được CSV writer của ứng dụng quote đúng.

| Field | Cách điền |
|---|---|
| `event_id` | ID ổn định do người thu thập cấp cho một component của một event; không tái dùng cho event khác. |
| `event_group_id` | Cùng security và ex-date dùng một group; mixed rights có nhiều row và event ID riêng. |
| `security_id`, `ticker`, `exchange` | Identity lịch sử từ scope/evidence; exchange là `HOSE`, `HNX`, `UPCOM`. Không sinh security ID bằng current ticker. |
| `event_type` | `CASH_DIVIDEND`, `STOCK_DIVIDEND`, `BONUS_SHARE`, `STOCK_SPLIT`, `REVERSE_SPLIT`, `RIGHTS_ISSUE`, `OTHER`. |
| `announcement_date` | `YYYY-MM-DD` theo thông báo; thiếu thì review. |
| `available_at` | ISO timestamp có giờ và timezone, ví dụ `2024-01-02T09:00:00+07:00`, chỉ khi có evidence. |
| `available_at_evidence` | Ghi nơi thấy timestamp, trang/đoạn hoặc file evidence; không tự gán 00:00/17:00 khi nguồn chỉ có ngày. |
| `ex_date`, `record_date`, `payment_date` | `YYYY-MM-DD`; không suy ex-date bằng cách trừ một phiên từ record-date. |
| `cash_dividend_per_share` | Số VND/share thực trong thông báo, ví dụ `1500`; không nhập `15%` mệnh giá vào đây. |
| `stock_dividend_ratio` | Cổ phiếu cổ tức mới / cổ phiếu cũ; `15%` hoặc `0.15`. |
| `bonus_ratio` | Cổ phiếu thưởng mới / cổ phiếu cũ; `64.58%` hoặc `0.6458`. |
| `split_multiplier` | Tổng số cổ phiếu sau / trước split; split `2`, reverse split `0.5`; không phải tỷ lệ phát hành thêm. |
| `rights_ratio` | Cổ phiếu có quyền mua mới / cổ phiếu cũ, ví dụ `7%` hoặc `0.07`. |
| `rights_subscription_price` | Giá đăng ký mua VND/share; chỉ ghi `0` nếu nguồn ghi rõ miễn phí, không zero-fill missing. |
| `currency` | `VND`, bắt buộc cho cash và rights issue. Không hỗ trợ tự đổi ngoại tệ. |
| `ratio_semantics` | Nếu nhập `10:3`, bắt buộc `OLD:NEW`: 10 cũ nhận 3 mới, kết quả `0.3`. Nếu decimal tỷ lệ mới/cũ có thể ghi `DECIMAL_NEW_PER_OLD`; split decimal dùng `NEW_TOTAL_PER_OLD`. |
| `primary_source_type`, `primary_source_url` | Loại nguồn và URL trực tiếp của thông báo official/IR; không chỉ ghi homepage cho event. |
| `primary_source_published_at` | ISO timestamp có timezone nếu có; nếu chỉ có ngày thì `YYYY-MM-DD`, không giả chính xác timestamp. |
| `secondary_source_url` | URL bổ sung; có thể để trống. Evidence cho field khác cần mô tả trong raw terms/notes. |
| `raw_terms` | Giữ nguyên đoạn nguồn, cả tỷ lệ hiển thị và semantics; tool không sửa nội dung này. |
| `notes` | Hạn chế, cách đọc điều khoản, tham chiếu evidence khác; bắt buộc với OTHER. |
| `conflict_notes` | Ghi cả hai giá trị, nguồn và field mâu thuẫn; có nội dung thì luôn review. |
| `verification_status` | Mặc định người nhập nên ghi `MANUAL_REVIEW`; chỉ ghi `VERIFIED` sau review đủ evidence. Tool có thể hạ status; không tự nâng status. `INVALID` giữ row sai rõ ràng. |
| `verified_by`, `verified_at` | Reviewer và thời điểm xác minh có timezone; bắt buộc để VERIFIED. |
| `identity_status`, `identity_source_url` | `UNVERIFIED` hoặc `VERIFIED` và URL chứng minh identity interval. Attestation này không promote strict historical research gate. |
| `revision_status`, `revision_of_event_id` | `ORIGINAL` cho bản gốc; `CORRECTION`, `CANCELLED`, `UNRESOLVED` cho sửa/hủy/chưa rõ, link ID bản trước nếu biết. Revisions luôn review trong V1. |
| `created_at`, `schema_version` | Thời điểm nhập thực tế có timezone; `1.0.0`. Không backdate collection. |
| `source_hash` | SHA-256 lowercase 64 ký tự của evidence đã lưu nếu có; để trống nếu không archive. Tool chỉ kiểm format, không download/recompute source file. |

Các field tài chính không thuộc event type phải để trống. Không gộp cash và stock
terms vào một row. Tất cả required terms thiếu đều review, không tự thay bằng zero.
`normalization_inputs` chỉ xuất hiện ở canonical JSONL do tool tạo để giữ cách nhập
gốc của các số; không có cột tương ứng trong CSV.

Ví dụ **chỉ minh họa, không phải dữ liệu thật**; bổ sung các field common ở bảng trên
bằng evidence thật trước khi nhập. Không sao chép URL synthetic của unit tests:

| Event type | Field nhập | Kết quả normalization |
|---|---|---|
| `CASH_DIVIDEND` | `cash_dividend_per_share=1500`, `currency=VND` | `1500` VND/share |
| `STOCK_DIVIDEND` | `stock_dividend_ratio=15%` | `0.15` |
| `BONUS_SHARE` | `bonus_ratio=10:3`, `ratio_semantics=OLD:NEW` | `0.3` |
| `RIGHTS_ISSUE` | `rights_ratio=7%`, `rights_subscription_price=10000`, `currency=VND` | `0.07`, `10000` VND/share |

Tỷ lệ trên 100% không mặc nhiên sai: V1 giữ normalization đúng literal rồi review.
Ví dụ `6458%` thành `64.58`, **không** tự biến thành `0.6458`; nếu nguồn khác ghi
`64.58%`, ghi conflict. Không suy mệnh giá, unit multiplier hoặc điều khoản từ magnitude.

## Bước 5 — Xử lý thiếu, conflict, mixed events và revisions

- Không có ex-date: để trống, ghi notes và `MANUAL_REVIEW`; tìm thông báo exchange
  bổ sung. Không suy từ record-date.
- Nguồn chỉ có ngày công bố: giữ ngày ở `primary_source_published_at`, để trống
  `available_at` nếu chưa có evidence timestamp. Tool không áp date-to-time policy.
- Nguồn biết sau event: ghi đúng public timestamp thực tế, không lùi về ex-date.
  V1 flag `LATE_OR_INTRADAY_KNOWLEDGE_PIT_REVIEW`; future consumer cần kiểm
  `available_at <= decision_at`, không coi ledger VERIFIED là đủ cho mọi decision.
- Nguồn mâu thuẫn/tỷ lệ bất thường: giữ raw terms và ghi `conflict_notes`. Không
  average, không tự chọn nguồn. Có thể giữ hai row candidate khác ID, cùng key;
  tool sẽ đánh dấu cả hai. Khi giải quyết bằng review riêng, giữ bundle cũ và
  evidence conflict; tạo run mới cùng resolution note, không xóa lịch sử bất lợi.
- Mixed event: cash và stock cùng ex-date thành hai row, cùng `event_group_id`,
  khác `event_id`, khác type. Một component unresolved khiến toàn group quarantine.
  Nếu nghi còn thiếu component trong thông báo, chưa đánh dấu group VERIFIED.
- Hai event cùng type/security/ex-date: V1 giữ duplicate/review, kể cả có thể là hai
  tranche hợp lệ; chưa tự sum/merge hoặc chọn một tranche.
- Đính chính/hủy: giữ nguyên run gốc, tạo CSV/run mới gồm bản trước và revision;
  link `revision_of_event_id`, ghi revision status, public time mới và raw terms
  mới. Tool quarantine revision lẫn bản trước được link, kể cả ex-date đã đổi.
  V1 chưa có automatic revision resolution hoặc PIT version selection; đòi hỏi
  review riêng trước khi dùng series. Không giả bản sửa đã được biết ở ngày bản gốc.
- `OTHER`: bắt buộc notes và manual review; chưa áp adjustment cho loại chưa hỗ trợ.

Không có chức năng suy event từ price jump trong V1. Nếu tự lập danh sách nghi vấn,
phải ghi `CANDIDATE_ONLY`, `NOT_EVENT_EVIDENCE` và tìm official evidence trước khi nhập.

## Bước 6 — Validate

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py validate --input M3/collection/events_v1.csv --output M3/collection/validation_v1.json
```

Không sửa input. `PASS` chỉ nói những row đã nhập đạt contract; **không** nói đã thu
đủ ticker/event. Header-only CSV có thể PASS với 0 row, vẫn chưa có coverage.
Exit code `0` là pass, `2` là review/invalid/error. Lần validate tiếp dùng output mới
hoặc bỏ `--output` để chỉ đọc kết quả trên màn hình.

## Bước 7 — Đọc lỗi và sửa dựa trên nguồn

Mỗi issue có `row` (số dòng CSV, header là dòng 1), `event_id`, `field`, `code`,
`severity`. Với ô multiline, `row` là logical record, không phải physical text line.

| Nhóm code | Cách xử lý |
|---|---|
| `CSV_HEADER`, `CSV_WIDTH`, `SCHEMA_VALUE`, `SCHEMA_VERSION` | Dùng đúng header/version, quote ô có dấu phẩy; sửa format dựa trên nguồn. |
| `REQUIRED_FIELD`, `REQUIRED_EVIDENCE`, `NOT_HUMAN_VERIFIED`, `REVIEW_ATTESTATION_REQUIRED` | Bổ sung evidence/reviewer hoặc giữ manual review. |
| `INVALID_NUMBER`, `UNUSUAL_RATIO_GT_100_PERCENT`, `SPLIT_DIRECTION` | Kiểm dấu chấm, `%`, chiều ratio/split; không đoán lại giá trị. |
| `DATE_ORDER`, `AVAILABLE_BEFORE_PUBLICATION`, `COLLECTION_BEFORE_AVAILABILITY`, `TIMESTAMP_WITH_TIMEZONE_REQUIRED` | Đối chiếu năm mốc và timezone; giữ public time thực. |
| `SOURCE_CONFLICT`, `TERM_CONFLICT`, `DUPLICATE_EVENT_ID`, `DUPLICATE_EVENT_KEY` | Review evidence; không deduplicate hoặc giải quyết conflict ngầm. |
| `GROUP_IDENTITY_DATE_CONFLICT`, `SAME_DAY_GROUP_MISMATCH`, `UNRELATED_TERM_MIXED_ROW`, `INCOMPLETE_OR_UNRESOLVED_EVENT_GROUP` | Tách component đúng row, giữ đúng group/security/ex-date. |
| `AUTHORITATIVE_SOURCE_REQUIRED`, `SOURCE_AUTHORITY_URL_MISMATCH`, `HISTORICAL_IDENTITY_UNVERIFIED` | Tìm nguồn official/identity evidence đúng; không dùng vendor làm authority. |
| `REVISION_REQUIRES_REVIEW`, `REVISION_TARGET_REQUIRES_REVIEW`, `OTHER_REQUIRES_REVIEW`, `LATE_OR_INTRADAY_KNOWLEDGE_PIT_REVIEW` | Giữ quarantine để review riêng; không cố sửa input chỉ để pass. |

## Bước 8 — Build bundle mới

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py build --input M3/collection/events_v1.csv --output artifacts/corporate_actions/corporate-actions-v1-run-001
```

Bundle gồm `input.csv` nguyên byte, `corporate_actions_v1.jsonl` chỉ chứa VERIFIED,
`review_queue.json` giữ raw + normalization + issues của row chưa đạt,
`validation.json` và `manifest.json` chứa SHA-256 của từng output, input, module,
schema. Bundle PARTIAL vẫn được tạo để không mất evidence, command trả exit `2`.
Không có giá/feature/return output. Không overwrite bundle; sửa data tạo `run-002`.

Không archive website tự động. URL có thể đổi/mất nội dung, reviewer attestation
không phải xác minh online của tool. Nên lưu PDF/text/screenshot và tính SHA-256:

```powershell
Get-FileHash -Algorithm SHA256 M3/collection/evidence/notice.pdf
```

Điền lowercase digest vào `source_hash`, ghi đường dẫn evidence trong notes. Để
trống hash nếu chưa lưu; đừng hash URL rồi gọi đó là content hash. Giữ bản gốc.

## Bước 9 — Xác nhận và xem coverage

Với mỗi identity trong `coverage_v1.csv`, kiểm toàn bộ cửa sổ và cả sáu event types
cùng OTHER/revisions có liên quan. Ghi `reviewed_start_date`, `reviewed_end_date`,
`reviewed_event_types=ALL_V1`, `primary_source_type`, `primary_source_url`,
`coverage_evidence` (trang/phân trang/khoảng tìm kiếm và log đã rà, URL bổ sung),
`reviewer`, `last_checked_at` có timezone sau ngày kết thúc cửa sổ. Chỉ khi đã rà
đủ mới đổi `review_status=REVIEWED`; mặc định là `NOT_YET_REVIEWED`.

Không có kết quả tìm kiếm chưa chứng minh không có event: nếu archive thiếu hoặc
không rà được đủ trang/ngày, giữ chưa reviewed hoặc `MANUAL_REVIEW`. Một thông báo
riêng lẻ không chứng minh coverage toàn giai đoạn. V1 yêu cầu attestation thủ công
và không tự xác nhận tính đầy đủ của archive.

```powershell
.venv\Scripts\python.exe scripts/collect_corporate_actions_v1.py report --input M3/collection/events_v1.csv --coverage M3/collection/coverage_v1.csv --universe M3/collection/scope_v1.csv --output M3/collection/coverage_report_v1.json
```

Report có `ticker`, identity, required start/end, event/verified/manual/invalid counts,
`last_checked_at`, `coverage_status`, reasons và input/scope/coverage hashes.
Nó đọc lại đúng CSV đã validate; không fit/recompute market data. Không có ticker
trong ledger vẫn phải xuất hiện nhờ scope độc lập. Scope rỗng hoặc sai identity bị chặn.

| Coverage status | Ý nghĩa |
|---|---|
| `NOT_YET_REVIEWED` | Chưa có attestation hợp lệ cho cả cửa sổ, kể cả đã có vài verified events. |
| `NO_EVENT_CONFIRMED` | Đã rà đủ cửa sổ/tất cả event types với source log và reviewer; không có event trong scope window. |
| `HAS_VERIFIED_EVENTS` | Có event VERIFIED và attestation rà đủ cả cửa sổ; không còn event unresolved trong cửa sổ. |
| `MANUAL_REVIEW_REQUIRED` | Còn event invalid/review, attestation thiếu/sai, hoặc coverage identity trùng. |

`coverage_pass=true` chỉ khi mọi identity trong scope thuộc hai trạng thái confirmed,
không có event/coverage identity ngoài scope. Nó không chứa trạng thái `COMPLETE`
suy từ event count. Missing ex-date được tính là unresolved cho scope, không bị rơi
khỏi report vì filter ngày. Hash trong report giúp pin đúng các file cho review sau.

## Bước 10 — Điều kiện bàn giao dữ liệu

Chưa chuyển sang xây price-only series cho đến khi:

1. Owner xác nhận scope identity theo thời gian, execution/valuation boundary và
   exact required window; khác biệt runner/kế hoạch nêu trên được review riêng.
2. Mỗi scope identity có full-window attestation và `coverage_pass=true` trên đúng
   input version; không bỏ row conflict/revision để làm pass.
3. Bundle canonical tương ứng được build/kiểm hash, toàn bộ mixed components đủ
   evidence, source conflicts và revisions có quyết định review phù hợp.
4. Owner review Q11/methodology của work unit sau; coverage pass không owner-approve Q11.

Status của task tạo công cụ:

```text
CORPORATE_ACTION_COLLECTION_PIPELINE = READY (khi tests/verification pass)
CORPORATE_ACTION_DATA_COVERAGE = NOT_YET_COMPLETE
M3_EXACT_RUNTIME_WINDOW = MANUAL_REVIEW_REQUIRED
PRICE_ONLY_SERIES = NOT_BUILT
M2_IMPACT = NONE
Q11_STATUS = STILL_OPEN
NEXT_WORK_UNIT = COLLECT_AND_VERIFY_CORPORATE_ACTIONS_V1
```

Fixtures tại `tests/fixtures/corporate_actions_v1/` là synthetic, chỉ phục vụ unit/CLI
tests; không đưa chúng vào production hoặc dùng để tuyên bố coverage M3 thực.
Không chạy backtest, clustering hoặc sửa `raw_close`/`adj_close` trong workflow này.
# Tiếp tục C8 v2 bằng Python local — checkpoint 01/11/2026

Kaggle: `scripts/package_corporate_actions_kaggle_v1.py` tạo ZIP + notebook +
`KAGGLE_SETUP.md`. Bản export hiện tại ở `tmp/ca_kaggle_export_20261101_v3/`.
Notebook dùng CPU/Internet ON, kiểm bootstrap checksum và restore state ZIP; mặc định
3 thread workers trong một process, 150 mã hoặc 90 phút mỗi batch. Nên smoke 3 mã
trên Kaggle trước. Các output ZIP có suffix shard để tránh ghi đè.

Resume có thêm `--exchange UPCOM` hoặc `--shard-count N --shard-index I` (0-based),
chỉ phân công work; scope vẫn 1.522 mã. Giữ shard count/index qua resume và dùng output
riêng. Không nhân thread count hoặc giảm delay để coi đó là provider permission;
per-host limiter/blocked state chỉ chia sẻ trong một process, không giữa các máy.
Min interval 2 giây; 401/403/429/challenge vẫn stop, không đổi IP/tài khoản để bypass.
Không cam kết toàn universe verified trong 1–2 giờ. Xem `KAGGLE_SETUP.md` trong export.

Lượt đã seal dừng tại ACG: 20/1.522 mã được xử lý có giới hạn; mã tiếp theo ACL.
Coverage vẫn INCOMPLETE. Chạy từ repository root trong PowerShell:

```powershell
.venv\Scripts\python.exe scripts/resume_corporate_actions_v1.py --checkpoint tmp/ca_c8_v2_checkpoint_20261101_v5 --output tmp/ca_c8_v2_resume_003 --max-securities 1522 --max-requests 100000
```

Script chạy foreground trên máy, không gọi model. Bỏ qua processed securities, verify
scope với C8 v2, dùng cache khi checksum hợp lệ và giữ timestamp gốc. Không cần agent
poll trong lúc tải. Với budget hiện tại, thời gian còn lại tham khảo khoảng 17–24 giờ;
đây là lượt source collection có giới hạn, không bảo đảm data/identity coverage complete.

Output phải là directory mới. Progress snapshot được lưu sau từng mã; Ctrl+C giữ
finished evidence và seal partial batch. Nếu tiến trình bị đóng đột ngột, dùng directory
batch làm `--checkpoint` cho directory output mới; script verify durable progress và
sealed child manifests. Raw của mã bị ngắt chưa đủ receipt metadata không được tự tin
reuse. Exit code 2 nghĩa PARTIAL, cần đọc `batch_results.json`/`resume_state.json`.
Thêm `--dry-run` để kiểm tra pending securities mà không network hoặc tạo output.

## Pilot KBS local và thư mục corporate actions — cập nhật03/11/2026

Kết quả mới: pilot 6 mã đều 0 rows. Đã chẩn đoán trực tiếp DXG bằng 1 public GET,
HTTP 200/raw `[]`; không gọi page 2 vì page 1 rỗng. Chưa có bằng chứng SDK làm
mất rows, cũng không chứng minh KBS không có history ở endpoint/filter khác.
Không mở bulk route này chỉ vì SDK-export status là READY. Raw/receipts/ZIP ở
`data/corporate_actions/work/kbs_raw_dxg_v1/`; review ở
`data/corporate_actions/work/kbs_raw_dxg_review_20261103_v1/`.
Current ZIP có hậu tố `-metadata-v2.zip`, sửa offline nhãn manifest sang public
HTTP bytes; không thay raw/receipts hoặc gọi lại KBS. ZIP đầu vẫn được giữ.
Runner `scripts/corporate_actions/probe_kbs_raw_dxg_v1.py` đã chạy; người dùng
không cần chạy lại chẩn đoán vừa hoàn tất. `--check` chỉ xác minh offline
config/endpoint evidence/baseline hashes. Public diagnostic không cần API key.

Đã sửa lỗi phân biệt tên Python method `reference.company.events` vànative route
`fundamental.company.events` doSDK5.2.1 công bố. Nếu lượt đầu dừng
`STOPPED_SOURCE_OR_ROUTE_MISMATCH`,chạy lại cùng lệnh sau khi code được cập nhật;
ZIP cũ giữ nguyên,run mới tự tạo thư mục/ZIP mới. Không tắt route/source guards.

Các runner hiện hành được truy cập trong `scripts/corporate_actions/`; cấu hình
ở `configs/data/corporate_actions/`; dữ liệu vẫn thuộc `data/corporate_actions/`.
Code/config cũ có hardlink giữ đường dẫn ban đầu cho manifest/imports. Artifact
cũ có đường truy cập tập trung ở `data/corporate_actions/work/legacy_tmp/`, qua
junction trỏ về old immutable directory. Không xóa các compatibility links.
`legacy_sources/` giữ source byte cũ; hãy chạy wrapper cùng tên ở thư mục cha.

Pilot KBS lấy mẫu GSP,DTP,ASG,KPF,LCG,DXG qua Vnstock5.2.1 đã cài ở `.venv-vci`.
Đây là một SDK call/mã,8giây giữa các call, tối đa480giây cho worker; chưa crawl
toàn bộ C8 hoặc chứng minh đã lấy đủ2019–2025. Không tính giá điều chỉnh, không
áp dụng quyết định nguồn, không gọi HNX hoặc tái mở KPF issuer đangSTOP.

Chạy trong terminal PowerShell:

```powershell
& "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\.venv-vci\Scripts\python.exe" "C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\corporate_actions\run_kbs_events_pilot_v1.py"
```

Khi hỏi API key: nhấn Enter để dùng đăng nhập local đã lưu, hoặc nhập key ẩn.
Không gửi key vào chat. Script giữ stable SDK auth home của VCI local; không
đổi device store hoặc tự xóa/đăng ký lại thiết bị khi lỗi. Không cần cài lại SDK.
Lệnh thêm `--check` chỉ kiểm tra offline package/files, không kiểm tra đăng nhập.

Log thu thập có `QUERY_STARTED`, rồi `QUERY_SAVED` với ticker/số rows. Cuối cùng
có dòng `OUTPUT_ZIP:` và đường dẫn đầy đủ. Gửi lại đúng ZIP đó để kiểm tra. Nếu
có lỗi vẫn lấy ZIP; không tự chạy lặp liên tục khi gặp auth/access/rate-limit.
InputError riêng một mã được ghi quarantine và chuyển mã khác; lỗi nguồn hoặc
source/route metadata không xác minh được sẽ dừng. Không có outer retry/fallback.

Output:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\kbs_pilot_v1
```

ZIP gồm `plan.json`, `runtime.json`, `result.json`, `queries/<ticker>.json`,
`sdk_exports/<ticker>.json`, `execution.json`, `manifest.json` theo những bước đã
chạy được. Mỗi export là JSON matrix `columns` + `dtypes` + `data`, giữ duplicate
columns và float precision của Python. Đây là SDK-export, không phải raw HTTP
hoặc bảng canonical16trường. `column_profile` chỉ thống kê null/non-null, không
chứng nhận tên cột là giá quyền mua, PIT hoặc semantically complete. Private auth
store/login replies/log tùy ý củaSDK không được đóng gói. Không có CSV cầnimport.

Sau khi nhậnZIP mới so sánh fields/coverage với nguồn hiện tại; chưacó kết luận
KBS tốt hơn hoặc source pilot PASS trước khi user chạy thật. Gói45 field choices
tiếp tụcMANUAL_REVIEW_REQUIRED,không suy approval từ yêu cầu thử nguồn mới.

