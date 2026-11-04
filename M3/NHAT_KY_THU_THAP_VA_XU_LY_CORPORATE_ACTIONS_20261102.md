# DELTA — Nhật ký thu thập và xử lý corporate actions

Ngày tổng hợp: **02/11/2026**. Phạm vi: dữ liệu corporate actions cho DELTA / Risk-Adjusted Momentum Clustering.

Tài liệu ghi lại những việc đã thực hiện, kết quả kiểm tra và kế hoạch tiếp theo. Các mục kế hoạch chưa được thực thi chỉ vì được ghi trong tài liệu này. Các số liệu dưới đây dựa trên artifact đã lưu trong workspace.

### Cập nhật03/11 — Khép V5 lỗi,chuẩn bịV6 isolatedWindows pause/recovery616

NativePID12040/commandV5 được xác minh và khép riêng,không child trực thuộc,
không đụng process khác;archive nguyênlock. Externalclosedcrashsnapshot24.585
sourcefiles giữ616query/PLCpartial,không relabelV5PAUSED. Carry1618/34422 và
activeupper8769,523s(tính cảdriverhang tới khi khép+1s),perbatchcaps giữ nguyên.

V6 publicsupervisor nhậnCtrl+C/SIGBREAK→pausemarker,hiddenworker NEW_PROCESS_GROUP/
NO_WINDOW,stdinDEVNULL,browserhandle_sigintFalse. Hiển thịhash/preflight/copy0/616;
616importrefs giữsourceimmutable,copy khiuser-run. PLCpage1restart,còn456queries,
ORSHOLD80/85. 26targetedcases/compileall/smoke PASS,gồm realownWindowsconsole
CtrlC vớiChromeabout:blank driveralive vànormalclose.0VSDCrequests,1localtestbrowser.

Preparation `data/corporate_actions/work/vsdc_recovery_pausefix_preparation_20261103_v6/`;
validation `data/corporate_actions/work/vsdc_recovery_pausefix_validation_20261103_v6/`.
User-run publicV6CLI ởđầu guide làbước tiếp,chưaexecute456queries. Source/crash/
budgeterrors vẫnSTOP,khôngpromoteowner/canonical/PIT/identity/history hoặcORScomplete.

### Cập nhật 03/11 — V5 Ctrl+C driver disconnect, chưa safe pause

Run `run-20261103T140146003064Z` báo Connection closed while reading from driver
sau Ctrl+C; chưa result/rootZIP/PAUSED, active.lock giữ nguyên. Agent gửi --pause
marker nhưng chưa acknowledgement; nativeprocess state chưa xác nhận reliable.
41newqueryZIPs được revalidate, cộng575import=616complete(PJT cuối);PLCpartial
page1/3,pendingpage2, còn456scoped +ORS HOLD1. Known40.295,102requests complete
mới; chưa certified finalcosts/currentrun. Không thay runtime/state hoặc relabel
PAUSED. Review snapshot `data/corporate_actions/work/vsdc_v5_ctrlc_incident_review_20261103_v1/`.

Mockpause tests chưa bảo đảm Windowschilddriver SIGINT behavior. Bước tiếp cần
khép session lỗi/preserve616+partial rồi explicit recovery vàfix/test pause ở
version mới;chưa execute. Không replayCLI/xóa lock/đổi nhánh trước khi xử lý.

### Cập nhật 03/11 — Chuẩn bị V5 thu497mã và giữ ORS HOLD

V5 mới import nguyên575completequeries, giữ ORS partial80/85 với5reportedslots
chưa giải quyết trong HOLD evidence riêng. Scopedtarget1072=575+497,original1073
bất biến; final scopedPASS vẫn unresolvedORS1,không markORScomplete hoặc nới
full-query gate. Min4s/headless/diagnostics/verifiedpause/sourceSTOP nhưV4;
carry1514business/32092context/7148,281s và per-batch costs,không reset budget.

Preflight kiểm tra fullsource/preparation/copy hashes; sourcechecks fullSHA256
sealedV4ZIP+manifest và old protected/runtime/parents,không cachehash/mtime hoặc
đọc lại24.000raw files sau mỗi request. 26targetedcases/compileall/smoke PASS.
Orphan V4 lockPID15740/run133517 đã review PIDdead/outputabsent,archivebytes
nguyên cùng biên bản,không thêmauto-clearing. Agent0source/browser,chưa thu497.

Preparation `data/corporate_actions/work/vsdc_recovery_ors_hold_preparation_20261103_v5/`;
validation `data/corporate_actions/work/vsdc_recovery_ors_hold_validation_20261103_v5/`.
Bước tiếp user chạy mộtlệnhV5 đầu guide,gửiOUTPUT_ZIP kểcảpause/error đểreview;
giữ tất cả checkpoint/V4STOP/ancestors và ORS evidence,không chạy lệnhcũ.

### Cập nhật 03/11 — V4 STOP tại ORS page5 emptylist

Run `run-20261103T112801286796Z` đã lưu575completequeries (20import+555V4),
còn498;ORS thuộcproposed030 có4pages/80distinctrows nhưng footer85,page5HTTP200
body33bytes/emptylist/nofooter. Parser range/total/IDgate STOP,khôngcreditORS.
KhácAPPtimeout,không thấy403/429/challenge markers;servercause chưa xác định.

Cumulative1.514business/32.092context/7.148,281sactive;V4segment1.469requests,
556browserlaunches. Giữ575checkpoints/ORS80partialrows,detailcache27.731 nguyên,
khôngowner/canonical/PIT/identity/history promotion.Review:
`data/corporate_actions/work/vsdc_recovery4s_stop_review_20261103_v4/`.
Integrity/self-review PASS: ZIP24.005members/576queryZIP,555newqueries reparse
23.133rows/22.258uniqueIDs,1.464pages;hash/runtime/ledgers/diagnostics/progress/
costs đạt,minstartgap4,312s. 3targetedtests/compileall PASS,0agentnetwork/browser.
Bước tiếp đềxuất scopedrecovery reuse575,ORSsource-count-gapHOLD riêng và497mã
khác;khôngmarkORScomplete/giảmgate hoặc replay STOP/đổiIP. Stagechỉoffline review,
chưa sửacode/gọinguồn/build recovery.

### Cập nhật 03/11 — Chuẩn bị recoveryV4 min4s reuse20queries

User giao recovery cho phần còn lại. V4 mới import nguyên15V3query2s+5pilotquery4s
đãreview,giữ ZIP/runtime/config/provenance gốc;không sửa STOP hoặc refetch20mã.
Scope1.053query/53batch proposed003–055,globalprogress20/1073,numberingbatch2/54.
ETA warmup5newV4queries,Chromeẩn/freshcontextperquery/min4s/oneworker.

Seedcost45business/1.155context/159,719s gồmfailedAPP/diagnostic/pilot,khôngreset
budgets.Ctrl+C/--pause cooperativecheckpoint,sameCLIcontinue chỉsealedverified
userpause,giữancestor runs;source/error/crash vẫnSTOP. Safe diagnostics trước
DOMwait vàsource/TLS/privacy/originalhash gates giữnguyên. Agent chỉprepare/test,
chưa mởbrowser/gọinguồn hoặcexecute recovery. Owner/canonical/PIT/identity/history
và7+418outside khôngđổi.

Preparation `data/corporate_actions/work/vsdc_recovery4s_preparation_20261103_v4/`;
validation `data/corporate_actions/work/vsdc_recovery4s_validation_20261103_v4/`.
44 targeted regression tests (10 V4 mới), compileall/smoke PASS; 1.851 protected
files. Chỉ kiểm tra recovery/dependency trực tiếp, không lặp full repository suite.
Bước tiếp user chạy mộtlệnhV4 ởđầu collectionguide,gửiOUTPUT_ZIP kểcảdừng/lỗi
đểoffline review;không chạy lệnhV3/pilot cũ.

### Cập nhật 03/11 — Pilot 4s user-run và offline review PASS

Run `run-20261103T111211552864Z` đủ APP43/APS27/ARM37/ART21/ASG22: 150 unique
list IDs/11 pages, 11 HTTP200, 276 context attempts/265 assets/5 external blocks,
52,359s active; business start gaps 4,422–5,922s qua cả trang/mã. Root ZIP191
members/5 queryZIP/runtime/protected1.630/receipt/reparse/progress23events PASS;
11 targeted tests và compileall đạt. 48 list IDs mới, detail cache27.731 nguyên.

15 V3 +5 pilot =20 query snapshots reviewed, đủ scope proposed-002 qua hai runs;
còn1.053query/53batches proposed-003–055. Tổng source costs có audit riêng của
V3/APP diagnostic/pilot4s là45business/1.155context/159,719s active, chưa import
recovery hoặc reset chi phí. Review:
`data/corporate_actions/work/vsdc_five_query4s_live_review_20261103_v1/`.

Agent0source/browser/codechanges;oldSTOP/prefix/evidence giữ nguyên. Bước tiếp
đề xuất preparation recovery4s reuse20queries/không refetch, giữ cumulative
budgets,diagnostics/progress/verifiedpause;chưa build/run stage tiếp theo. Mẫu
nhỏ không chứng minh2s gây lỗi hoặc sustained4s cho toàn phần còn lại.

### Cập nhật 03/11 — Chuẩn bị pilot 5 full queries ở 4 giây

User chọn thử nhóm nhỏ 4s trước recovery. Đã chuẩn bị APP/APS/ARM/ART/ASG, đủ
trang từng query, dự kiến 11 list requests/150 rows. Min 4s giữa business request
starts qua pages/tickers; fresh headless process/context, một worker. Mỗi trang
ghi safe response diagnostics trước DOM wait; giữ original hash/source/privacy/
TLS gates và 15 checkpoint V3. Migrate literal source assertions chỉ đổi cadence,
thêm headless/safe diagnostic validation; không retry/resume/recovery import.

249 VSDC tests (11 mới), compileall/smoke/CLI offline và 1.630 protected files
PASS. Agent 0 source requests/0 browser launches, chưa chạy pilot live. Gói tại
`data/corporate_actions/work/vsdc_five_query4s_preparation_20261103_v1/`, validation
`data/corporate_actions/work/vsdc_five_query4s_validation_20261103_v1/`.

Bước tiếp: user chạy một lần theo lệnh đầu guide và gửi OUTPUT_ZIP; offline
review rồi mới recovery proposal dùng lại 15 checkpoint và pilot queries đạt.
Mẫu nhỏ khác thời điểm với2s không xác nhận nguyên nhân cũ hoặc sustained access
cho 1.058 mã. Owner/canonical/PIT/identity/history và scope 7+418 giữ nguyên.

### Cập nhật 03/11 — APP diagnostic user-run và offline review PASS

Run `run-20261103T104801448029Z` một GET HTTP 200, APP selector tồn tại, 20/43
rows trang đầu; chưa thu 23 rows còn lại. 51 attempts/50 assets/một external block,
2,750 giây active, body 53.353 bytes; không thấy challenge/error markers. ZIP
17 members/CRC/hash/runtime/protected 1.587 files, reparse fragment và JS contract
giống V3 PASS. 20 IDs đã có trong cache; không tăng full-query completion hoặc
detail/canonical. 14 targeted tests và compileall PASS. Agent 0 source/browser.

Lỗi APP cũ không tái hiện; body cũ thiếu nên chưa xác định nguyên nhân. V3 STOP
và 15 checkpoint giữ nguyên, vẫn còn 1.058 mã. Review artifact:
`data/corporate_actions/work/vsdc_app_diagnostic_live_review_20261103_v1/`.
Bước tiếp đề xuất preparation recovery version riêng, reuse 15 complete queries,
APP từ trang 1, early safe diagnostics và cumulative budgets; chưa build/run
recovery hoặc nới source gates. Không chạy lại diagnostic/V3 cũ.

### Cập nhật 03/11 — Chuẩn bị APP diagnostic một GET

Đã chuẩn bị module/config/CLI riêng, một headless Chrome GET trang đầu APP;
response receipt/hash/size/cấu trúc/marker labels ghi trước selector. Timeout
vẫn giữ evidence an toàn; HTTP/access/error boundaries STOP, không chuyển trang,
retry, resume, detail hoặc headed fallback. Không lưu raw body/full DOM/private
session. Public result fragment chỉ lưu sau source/privacy/parse gates cũ;
full-query credit 0, không import hoặc phục hồi V3 ở stage này.

Self-review PASS: 238 VSDC tests (14 mới), compileall/synthetic smoke, CLI offline
hai cwd và 1.587 protected files. V3 run/ZIP, 15 checkpoint, owner/canonical/PIT/
identity/history giữ nguyên. Agent 0 source requests/0 browser launches. Gói tại
`data/corporate_actions/work/vsdc_app_diagnostic_preparation_20261103_v1/`, kiểm
tra tại `data/corporate_actions/work/vsdc_app_diagnostic_validation_20261103_v1/`.

Bước tiếp: user chạy lệnh APP diagnostic ở đầu collection guide một lần, gửi
OUTPUT_ZIP kể cả STOP; offline review trước recovery proposal. Kết quả mới có
thể khác lần lỗi cũ, hash/flags không chứng minh toàn bộ nguyên nhân quá khứ.

### Cập nhật 03/11 — Review V3 partial STOP tại APP

Run `run-20261103T102550498846Z` dừng sau 15 query AGR–APL; còn 1.058, chưa xong
batch đầu. APP GET HTTP 200 nhưng locator `#divGlSearchArticles` timeout 15 giây.
Chưa có body/DOM/hash lỗi do code chờ selector trước body/challenge check;
không đủ evidence xác nhận block/rate limit hoặc trang nguồn lỗi.

Offline review PASS: root ZIP 444 members/16 query ZIP/15 complete reparses,
478 unique list IDs, 177 IDs mới; detail cache 27.731 giữ nguyên. 33 business/
828 context attempts, 104,610 giây active, min interval 2,25 giây; progress và
1.125 protected files đạt. Source STOP không auto-resume; 15 checkpoint còn
nguyên nhưng chưa có recovery import. Review artifact:
`data/corporate_actions/work/vsdc_remaining54_headless_live_review_20261103_v1/`.

Agent không gọi nguồn/mở browser/sửa code hoặc run. Bước tiếp đề xuất là chuẩn
bị APP diagnostic pilot có safe response evidence, rồi review trước recovery
dùng lại 15 query và giữ cumulative budgets; chưa thực thi stage tiếp theo.

### Cập nhật 03/11 — V3 chạy ẩn 54 batch: preparation PASS

Đã chuẩn bị V3 cho proposed-002–055/1.073 mã/2.839 estimated list requests,
min 2 giây, headless Chrome process/context mới cho mỗi query. Giữ original
hash/source caps/STOP như V2. Progress theo mã/batch/trang, human/JSONL logs và
ETA sau 5 validated queries, trung bình 20 query gần nhất trừ in-flight time;
thời gian người dùng nghỉ không tính. Counter tăng sau seal/reparse/validate.

Ctrl+C hoặc `--pause` lưu checkpoint; cùng lệnh tiếp tục chỉ sau verified user
pause, giữ cumulative budgets và xác minh lineage/progress. Query đã đạt được
copy nguyên evidence để bỏ qua; query dở bắt đầu lại từ trang 1. V1/V2/evidence
cũ bất biến, V2 run không tự import. Self-review PASS: 224 VSDC tests (23 mới),
compileall/synthetic smoke, CLI offline hai cwd và 1.125 protected files.

Agent chỉ chuẩn bị offline, 0 source requests/0 browser launches/0 completion mới.
Chưa kiểm chứng live V3 pause hoặc sustained headless toàn lượt. 7+414+4 mã ngoài
scope vẫn được theo dõi; owner/canonical/PIT/identity/history giữ nguyên. Bước
tiếp: user chạy lệnh V3 đầu collection guide, gửi OUTPUT_ZIP để offline review
coverage/cache/source trước khi đề xuất detail acquisition hoặc nhóm còn lại.

### Cập nhật03/11 — Review headless/progress PASS,đềxuất prepare54batch chạyẩn

User chạy run-20261103T093821365887Z. ReviewofflineheadlessTrue/oneChrome/3fresh
closedcontexts,3query35/51/24/cùngJS/cache/data,7HTTP200,no boundaries.22progress
events/loghuman+JSONL đúngcounter,percent,remaining,page/tickerorder,contextclose
trướcquerycompletion vàFINALstatus. ETA math đúngnhưngdaođộngtrongin-flightquery;
chưa forecastcertificate,mẫunhỏkhônglàETA1073mã. Acquisition17.359s/profile20.094s/
ZIP1.047s làkhácwindow. ZIP56members/55hashes/protected1040/receipt/12tests/compile
PASS.Agent0source/browser/productioncodechanges;oldV2/owner/canonical/PIT/identity/
progress/cache/7+418scope nguyênvẹn.Bước tiếpđềxuấtprepare new54headless/progress/
verifiedpausecontinuation,min2s vàETAổnđịnhsauwarmup;chưa tựbuild/executebulk.

### Cập nhật03/11 — Chuẩn bị pilotheadless vàprogress terminal

User giao xửlýChrome bậtliêntục vàtiếnđộkhódõi. PilotriêngA32/AAA/IDJ/headless2s,
mộtChrome/3freshclosedcontexts,giữoriginalhash/sourcecaps/TLS/privacy/STOP. Thêm
eventprogress/loghuman+JSONL,completed/total/percent/remaining/page/batch/elapsed/
ETA tạmtính;chỉincrement sauvalidate/contextclose/persist. Headlessaccess lỗi STOP,
khôngheadedfallback/UAoverride/retry. Shortpilotnoresume,54V2 pausecontinuation giữ
nguyên. Stageofflinepreparation,chưaVSDC/browserexecution hoặc54headlessversion.
Bước tiếp:user-run một lần,review ZIP/data/headless/progress trướcnâng54batch.
Progress24/pending1080/cache27731/knownlist28276/7+418scope/owner/canonical/PIT/
identity/history giữ nguyên;không dùngETA3mã làmforecast1073mã.

### Cập nhật03/11 — Reviewfullhash pilot PASS,acquisition chỉgiảm1,31%

User chạy run-20261103T091151545258Z. Reviewoffline data35/51/24/JS/cache giống
shared2s,7HTTP200/no boundaries,1browser/3freshclosedcontexts,compile1/15fullhash
checks960files. Same-setcalibration2pairsAB/BA0.1715→0.1485s (~13.41%) nhưng
acquisition15.531→15.328s chỉ0.203s/~1.31%. Sourcehash3.017s,pacing8.280s;
profile17.734s inclpreflight/compiler/calibration,ZIP0.578s,khácwindowacquisition.
ZIP55members/54hashes/protected960/receipt/8tests/compileall PASS.Agent0source/
browser/productioncodechanges;V2/owner/canonical/PIT/identity/progress/7+418scope
giữ nguyên. Bước tiếpđềxuất dừngpilot nhỏ,chuyểnsang54V2 hiệncó2s/pausecontinuation;
không tựmigratehash/browser,crawlthêm hoặcclaim39%totalcrawl ởstage review này.

### Cập nhật03/11 — Chuẩn bị local full-hash2s pilot sau benchmark offline

User giao sourcepilot dùngcandidate fullhash. Tạo versionriêng A32/AAA/IDJ,list-only,
same2s/mộtChrome/3fresh contexts/7expectedbusiness,callbackfrequency vàsource/TLS/
privacy/caps/STOP giữ nguyên. Compileplan một lần nhưngfullread/SHA256 mỗientry/
check,khôngcache/dedup/fallback. Thêm2pairs offlineAB/BA sohashcũ/mới trêncùng
newprotectedset trướcsource;compiler/calibration timing nằm ngoàiacquisitionwindow.
Pin shared2s15.531s/hash3.313s/15calls vàoffline benchmark39%;chưa source/end-to-end
speedclaim. V2/runtime/canonical/owner/PIT/identity/progress/7+418scope giữ nguyên.
Stage chỉoffline preparation/testing;user chạy pilot một lần,gửi ZIP/packagingpath
đểreview data/calibration/timing trước đềxuất version54batch mới.

### Cập nhật03/11 — Offline full-hash candidate giảm khoảng39% chi phícheck

Usergiaobước offlinehashprofiling/optimization. Candidatecompilepaths/expecteddigests,
vẫnopen/fstat/fullread/SHA256 mỗi file mỗi lần;khôngcachemetadata/content/digest,
khôngdedupfiletrùnghash hoặcgiảmchecks. Paired8roundsAB/BA warmcache trên765/
864file cho median0.293347→0.179240s(38.90%) và0.324565→0.198062s(38.98%),
8/8pairs nhanhhơn cả2cohort. Mutationtests chỉ dùngtempfixtures,vẫndetectsame-size/
mtime/replace/lastbyte/delete/type/readfailure/duplicates. Khôngmởbrowser/gọinguồn
hoặcthay54V2/source/runtime/evidence/owner/canonical/PIT/identity/progress.
Benchmark dướiwork/vsdc_hash_fastpath_offline_benchmark_20261103_v1. Khôngngoạisuy
39% sangtotalcrawlETA vìpacing2s cóthểhấp thụsavings. Bước tiếpđềxuất prepare
isolatedsame2s localpilot vàprofile trướcbulk integration;chưa tựthực hiệnởstage này.

### Cập nhật03/11 — Review sharedChrome PASS dữ liệu/lifecycle,chưa speedup

User chạy run-20261103T084428264720Z:mộtChrome/3freshclosedcontexts,3query35/51/24,
cùngdata/cache/JS,7HTTP200,no sourceboundaries. Elapsed15.531s vs2sbaseline15.235s
chênh+0.296s/~1.94%,historicalunpaired comparison chưa chứng minh causal slowdown.
Timingreconciled:pacing8.171s/hash15calls3.313s/pagecalls exclusive2.499s/lifecycle
1.297s;profile17.031s inclpreflight/setup,ZIP0.516s sidecar,khácelapsedwindow.
ZIP54members/53hashes/receipt/protected864/13tests/compileall PASS.Agent0source/
browser/productioncodechanges;V2 không đổi,24/pending1080/cache27731/knownlist28276/
7+418/owner/canonical/PIT/identity/history giữ nguyên.Bước tiếp đề xuất offlinehash
profiling/optimization với mutation-detection trước thay integritycontract;không
auto applysharedbrowser54,crawlthêm hoặc coi hashseconds làguaranteed elapsedsaving.

### Cập nhật03/11 — Chuẩn bị pilot mộtChrome/ba phiên sạch vàtiming profile

User giao bước giảm chi phí browser ngoài interval. PilotA32/AAA/IDJ giữ2s vàsame
source/hash/ZIP checks,một Chrome process/3fresh contexts đóng lần lượt. Thêm nested
inclusive/exclusive timing đểtách hash/runtime/browser/context/page/pacing/archive
vàpackaging receipt ngoài sealedZIP. Context/disconnect/cleanup/source lỗi STOP,
không relaunch/retry/resume. Pin reviewed2s15.235s/1s14.719s;chưa đảm bảo speedup
hoặc sustainedrate. Agent chỉprepare offline,chưa gọiVSDC/mởChrome hoặc đổi54V2.
Progress24/pending1080/cache27731/knownlist28276/7+418scope vàowner/canonical/PIT/
identity/history giữ nguyên. Bước tiếp:user-run local một lần,review ZIP/timings
trước đềxuất54batch tốiưu;không tự tốiưu hash/ZIP hoặc acquisitiontrongstage này.

### Cập nhật03/11 — Review1s PASS dữ liệu, chỉ cải thiện3,39% thời gian

User chạy run-20261103T082730656572Z. Review offline3query35/51/24/7business200,
cùng parsed data/JS/cache với2s vàkhông source boundaries.166attempts/163admissions/
159assets/3externalblocks giốngbaseline. Elapsed15.235→14.719s,tiết kiệm0.516s,
~3.39%;intervals1.265–4.093s. Chưa chứng minh sustained1s/2xspeed hoặc tách được
browser/network/render/integrity overhead. ZIP53members/52hashes/protected788,
11tests/compileall PASS. Agent0source/browser/code changes;repeat không credit,
cache27731/known-list28276/owner/canonical/PIT/identity/7+418scope giữ nguyên.
Bước tiếp đề xuất dùng54batch V2 hiện có2s;không tự chạy hoặc đổi bulkversion
trongstage review. Pilot1s đã xong,không rerun;review timing thực tế nếu tối ưu tiếp.

### Cập nhật03/11 — Chuẩn bị pilot1s riêng, giữ54batch2s

User muốn thử dưới2s; thêm fixed1s A32/AAA/IDJ/list-only cùng caps/privacy/TLS/STOP
như2s, pin reviewed2s15.235s/7business/rows35-51-24 vàV2 artifacts. Không đổi54batch
hoặc checkpoint2s, không retry/fallback/resume hoặc chạy đồng thờichain. Chỉ offline
preparation; user chạy pilot một lần, gửi ZIP để compare dữ liệu/cache/network/timing
với2s trước đề xuất bulk rate. Small sample không chứng nhận sustained1s/2x speed.
Không newcompletioncredit/detail/owner/canonical/PIT/identity hoặc mở scope7+418.

### Cập nhật03/11 — V2 chủ động tạm dừng/tiếp tục từ full-query checkpoint

User yêu cầu bước pause/continuation trước lượt dài. V2 giữ nguyên54 batch/1073
mã và V1 evidence, chỉ cho tiếp tục sau verified user pause; Ctrl+C hoặc CLI
--pause gửi flag, query dở thu lại trang1/fresh context. Query đã seal/reparse đạt
không tải lại dù batch chưa xong. Costs/active time cộng dồn kể cả partial attempts;
source/error/crash/unsealed/stale-lock cases cần review, không tự resume/retry.
Stage chỉ preparation/testing/handoff, chưa mở browser hoặc gọi VSDC; progress
24/pending1080/cache27731/known-list28276 và7+418 ngoài scope giữ nguyên.
Lệnh V2 hiện hành ở đầu collection guide. Bước tiếp là user-run local và offline
review ZIP tổng; chưa chuyển sang thu nhóm7+418 hoặc tải detail.

### Cập nhật03/11 — Chuẩn bị một lượt54 batch theo đính chính của user

Scope hiện hành thay11 batch bằng proposed-002–055, gồm1.073 mã duy nhất/2.839
estimated list requests. Thêm fixed local runner min2s, per-batch checkpoints/ZIP
và offline CRC/hash/reparse/coverage/cache/ledger/pacing validation trước chuyển
batch. Lỗi dừng cả chuỗi; giữ partial evidence, không retry/resume/details hoặc
auto-promote canonical/owner/PIT/identity. Agent chỉ chuẩn bị/kiểm tra offline.

Chưa có source execution hoặc progress credit:24reviewed snapshots/pending1080,
trong đó1073selected+7largeHOLD;414archived-exhausted/4unverified vẫn theo dõi.
Detail cache27731 khác known-list28276. Lệnh user-run hiện hành nằm đầu collection
guide; old11-batch proposals là lịch sử. Bước tiếp sau user run: review ZIP tổng
kể cả partial, cập nhật progress từ evidence rồi đề xuất scope detail bổ sung.

## 1. Mục tiêu và phạm vi dữ liệu

Mục tiêu là chuẩn bị bảng `corporate_actions` có sự kiện, điều khoản và bằng chứng đủ rõ để nghiên cứu điều chỉnh các biến động kỹ thuật của giá. Yêu cầu của người dùng là **không cộng hoặc tái đầu tư cổ tức tiền mặt vào kết quả đầu tư**.

Chính sách hệ số điều chỉnh giá, cách xử lý các thành phần cùng ngày và trường hợp cổ tức tiền mặt vẫn cần được chốt trong Q11. Yêu cầu không tái đầu tư tiền mặt chưa tự quyết định toàn bộ cách điều chỉnh chuỗi giá.

| Nội dung | Phạm vi hiện hành |
|---|---|
| Inventory dùng để kiểm tra coverage | C8 v2, **1.522 mã** |
| Kỳ thu thập VCI | **31/01/2019–31/12/2025** |
| Dữ liệu ban đầu | Bốn shard và checkpoint 20 mã |
| Nguồn đã khai thác | VSDC, HNX, HOSE; bổ sung VCI và tài liệu doanh nghiệp |
| Trạng thái bảng canonical | Chưa build hoặc freeze trong các stage được tổng hợp ở đây |
| Hệ số điều chỉnh giá, price series và backtest | Chưa tạo trong các stage này |

**905 mã là số lượng tại một snapshot market-ready; không dùng số đó thay cho inventory C8 v2 1.522 mã.** Inventory này cũng chưa chứng nhận historical identity hoặc final historical research universe.

## 2. Cách đếm: mã, bản ghi, trường và sự kiện

| Đơn vị | Ý nghĩa |
|---|---|
| Mã / ticker | Ví dụ AAA. Một mã có thể có nhiều thông tin sự kiện qua nhiều năm. |
| Lượt dòng thu thập / occurrence | Một dòng xuất hiện trong một lần xuất dữ liệu. Cùng nội dung có thể xuất hiện ở nhiều tháng. |
| Bản ghi VCI khác nhau / distinct payload | Một bộ giá trị SDK khác nhau trên toàn dòng. Dùng để thống kê, chưa phải định danh sự kiện. |
| Observation | Một ghi nhận từ một nguồn, có parser, raw và provenance riêng. |
| Trường thiếu / field task | Một ô cần xử lý, chẳng hạn `ex_date` hoặc giá quyền mua. |
| Sự kiện canonical | Sự kiện đã được xác định danh tính, thành phần, phiên bản và điều khoản; chưa có số đếm cuối cùng. |

Ví dụ minh họa: AAA có một dòng cổ tức bằng cổ phiếu năm 2020 và một dòng quyền mua năm 2022 thì đó là **một mã, hai bản ghi**. Nếu dòng quyền mua thiếu cả ngày GDKHQ và giá mua, dòng đó tạo **hai field tasks**.

Do đó, **602 bản ghi trên 332 mã** không có nghĩa là 602 mã hoặc 602 sự kiện đã xác nhận. Các bản ghi còn có thể là thành phần của cùng sự kiện, bản cập nhật hoặc phương án chưa thực hiện.

Việc đếm distinct payloads chỉ phục vụ phân tích. Các dòng xuất gốc và mọi occurrence vẫn được giữ nguyên.

## 3. Thu thập ban đầu: bốn shard và checkpoint 20 mã

Đợt ban đầu thu thập từ VSDC/HNX/HOSE, phân thành bốn shard và giữ checkpoint 20 mã đã thu thập trước đó.

Các vấn đề chính được phát hiện:

- Thông tin thời gian trên website có thể là **ngày cập nhật**, chưa chứng minh ngày công bố lần đầu.
- Một số thông báo thiếu số tiền, tỷ lệ, đơn vị hoặc nội dung nằm trong tài liệu đính kèm.
- Có thông báo sửa đổi, hoãn lịch hoặc nhiều thành phần trong cùng một thông báo.
- HNX có 1.106 receipts lỗi xác minh chuỗi chứng chỉ trong đợt kiểm tra ban đầu.
- HOSE đang được khai thác chủ yếu qua lịch sự kiện; lịch chưa thay thế toàn bộ kho thông báo và tài liệu chi tiết.
- Historical identity chưa được xác minh đầy đủ; ticker hiện tại không đủ làm khóa cho toàn bộ lịch sử.

Số lượng dòng trong review queue phải đọc theo đúng đơn vị. Kiểm toán ban đầu xác định PIT queue có thể ghi **một dòng cho từng trường cần kiểm tra**, không phải một dòng cho mỗi thông báo. Không dùng số dòng queue làm số sự kiện còn lỗi.

## 4. Khôi phục metadata thời gian VSDC bằng xử lý offline

Stage `STEP_2_VSDC_TIMING_RECOVERY_V3` đã đọc lại raw đã lưu, không tải lại website.

| Kết quả | Số lượng / kết luận |
|---|---|
| Raw documents khác nhau đã xác minh và parse | **12.175** |
| Raw documents có độ chính xác đến ngày–giờ | **12.175** |
| Nhãn ngữ nghĩa thời gian | **UPDATE** |
| Bằng chứng múi giờ trong nguồn | Chưa có |
| Observation IDs trong stream tổng hợp | **12.609** |
| Network requests của stage | **0** |

Thay đổi được phép là bổ sung `source_timing`; các fields và receipts gốc được giữ nguyên.

**Kết luận:** đã khôi phục được metadata có trong raw. Chưa được chuyển giờ cập nhật thành giờ công bố hoặc tự coi dữ liệu là PIT-ready.

Phân biệt các mốc thời gian:

| Trường / khái niệm | Ý nghĩa |
|---|---|
| `ex_date` | Ngày giao dịch không hưởng quyền — GDKHQ |
| `record_date` | Ngày đăng ký cuối cùng — ĐKCC |
| Ngày công bố | Ngày nguồn thực sự công bố thông tin; cần bằng chứng riêng |
| `fetched_at` | Thời điểm hệ thống tải được dữ liệu |
| `available_at` | Thời điểm dữ liệu được phép sử dụng theo chính sách PIT và bằng chứng đã chấp thuận |

`ex_date` và `record_date` **không phải ngày công bố**. Mốc giờ có sẵn cũng chưa đủ nếu ngữ nghĩa chỉ là UPDATE hoặc chưa xác minh timezone.

## 5. Thu thập bổ sung thông báo HNX trên Kaggle

HNX được thử theo trình tự: kiểm tra truy cập/TLS → discovery → tải detail → parse offline → review → chạy shard có checkpoint và resume.

Vấn đề chuỗi chứng chỉ được xử lý bằng xác minh intermediate với trusted root theo cơ chế của project; không tắt SSL verification. Sau pilot, chạy bổ sung trên bốn shard, giữ ownership và state của từng shard.

Lượt đầu dừng khi hết ngân sách một giờ với `RUN_TIME_BUDGET_EXHAUSTED`, có thể resume. Đây là giới hạn thời gian chạy đã đặt, không tự chứng minh nguồn bị chặn.

Lượt sau gặp lỗi truy cập nguồn, gồm HTTP 403. Kiểm tra bốn state ZIP ghi nhận cumulative:

| Chỉ tiêu HNX | Số lượng |
|---|---:|
| Mã đã handled | 362 |
| Mã pending | 754 |
| Mã quarantine | 1 |
| Tổng scope của các state được kiểm tra | 1.117 |
| Observations tích lũy | **1.622** |

`Handled` là đã xử lý công việc theo collector, không chứng nhận mã có coverage lịch sử đầy đủ. 1.622 observations cũng chưa phải 1.622 accepted canonical events.

Các ZIP lượt sau đã chứa state tích lũy. Không cộng lại observations của lượt đầu vào lượt sau. Sau lỗi truy cập, giữ source stop; không force resume, đổi IP hoặc tiếp tục crawler HNX trong các stage tiếp theo.

## 6. Bổ sung lịch sự kiện VCI theo từng tháng

Sau pilot VCI ba tháng có 388 occurrences / 385 distinct payloads, đợt local đã hoàn thành **84 cửa sổ truy vấn** từ 31/01/2019 đến 31/12/2025.

Mỗi truy vấn lấy nhóm lịch `dividend` theo khoảng thời gian, rồi đối chiếu danh sách mã trả về với inventory C8 v2. Đây không phải chạy một truy vấn cho từng mã. Nhóm trả về có cả cổ tức tiền mặt và các loại phát hành.

| Chỉ tiêu toàn đợt VCI | Kết quả |
|---|---:|
| Cửa sổ hoàn thành | **84/84** |
| SDK row occurrences | **14.028** |
| Distinct whole-row payloads | **11.202** |
| Duplicate excess so với distinct payloads | **2.826** |
| Mã trả về khớp C8 v2 | **1.340** |
| Mã trả về ngoài C8 v2 | **182** |
| Mã trong C8 v2 chưa có dòng VCI | **182** |
| Distinct payloads thuộc C8 v2 | **10.553** |

Hai con số 1.522 — inventory và tổng ticker VCI trả về — bằng nhau về số lượng nhưng **khác tập mã**. Không kết luận đã có đủ dữ liệu cho inventory chỉ từ tổng số ticker.

Toàn bộ 385 distinct payloads của pilot đã có trong đợt đầy đủ; không cộng pilot vào 14.028 dòng.

Audit đã kiểm tra CRC, 425 root manifest hashes, 252 nested commit hashes và sự bằng nhau của 426 local state files với ZIP. Acquisition kỹ thuật PASS; coverage và data readiness vẫn PARTIAL.

Các ngày xuất VCI có dạng giờ `17:00Z`. Date view UTC+7 chỉ dùng cho kiểm tra; chưa coi giờ serialize là giờ công bố thực tế hoặc duyệt chuyển đổi canonical.

Khoảng truy vấn không bảo đảm mọi ngày sự kiện trả về đều nằm trong kỳ. Những dòng có ngày ngoài khoảng được giữ để review, chưa tự sửa hoặc xóa.

### 6.1. Phân loại sơ bộ các payload thuộc C8 v2

| Nhóm theo title | Distinct payloads |
|---|---:|
| Cổ tức tiền mặt | 6.815 |
| Cổ tức bằng cổ phiếu | 1.120 |
| Cổ phiếu thưởng | 405 |
| Quyền mua | 654 |
| Phát hành khác cần phân loại thêm | 1.559 |
| Tổng | **10.553** |

Nhóm ưu tiên là **2.179 payloads noncash** = 1.120 + 405 + 654. Những số lượng thiếu trường ở các stage sau chỉ nói về nhóm này, không phải tất cả 10.553 payloads hoặc toàn bộ dữ liệu các nguồn.

Export VCI không có giá đăng ký mua để dùng trực tiếp cho 654 rights payloads. Chưa có bằng chứng nhóm query này bao phủ đầy đủ chia tách/gộp cổ phiếu; coverage những loại đó vẫn cần kiểm tra riêng.

## 7. Đối chiếu offline VCI với VSDC/HNX/HOSE đã lưu

Runner đã đối chiếu 2.179 payloads ưu tiên với VSDC V3, dữ liệu cũ từ bốn shard/checkpoint và latest cumulative HNX state. Không tải lại nguồn trong stage này.

Nguồn đầu vào có 12.609 VSDC, 9.195 HOSE và 1.647 HNX observation occurrences. Số HNX này bao gồm phần calendar cũ/checkpoint; vì vậy khác 1.622 observations của riêng đợt supplemental HNX. Các source occurrences không cộng thành số canonical events.

| Trường trong nhóm ưu tiên | Thiếu trước đối chiếu | Có một giá trị đề xuất | Chưa có một giá trị đề xuất |
|---|---:|---:|---:|
| Ngày GDKHQ | 488 | 6 | **482** |
| Ngày ĐKCC | 488 | 7 | **481** |
| Giá quyền mua, trong 654 rights payloads | 654 | 244 | **410** |

Các giá trị đề xuất chỉ tạo hàng chờ review, chưa ghi đè fields của VCI hoặc ghi vào canonical.

Quy tắc đối chiếu giữ nguyên giới hạn:

- Dùng ticker, loại và ngày được ghi rõ để tìm ứng viên; ticker join vẫn provisional.
- Time hint và same-title SDK sibling chỉ giúp tìm ứng viên, chưa chứng minh cùng sự kiện.
- Không suy ngày GDKHQ từ ngày ĐKCC.
- Giữ mọi alternative/conflict; không tự chọn nguồn ưu tiên, lấy trung bình hoặc gộp sự kiện.

## 8. Kiểm tra bằng chứng raw của các đề xuất

Đã kiểm tra 244 đề xuất giá, 13 đề xuất field ngày (6 GDKHQ + 7 ĐKCC) và 36 payloads có xung đột tỷ lệ. Các nhóm có giao nhau; tổng union là **284 payloads**, không cộng thành 293 sự kiện.

### 8.1. Kết quả 244 đề xuất giá quyền mua

| Kết luận checker | Số payloads |
|---|---:|
| Raw hỗ trợ mã, ĐKCC, số tiền, đơn vị và tỷ lệ theo comparison của preview | **195** |
| Có số tiền và event anchor, chưa explicit đơn vị đồng/cổ phiếu | **24** |
| Cần làm rõ tỷ lệ hoặc component | **22** |
| Gắn với thông báo sửa lịch, cần revision review | **3** |
| Tổng | **244** |

195 payloads thuộc 162 mã. Trong 99 payloads từng có ratio warning, 76 có raw support theo checker mới. Các cảnh báo và artifact cũ không bị xóa.

Ba revision cases là SZC, VTR và HVN. Việc sửa thời gian thực hiện quyền chưa tự có nghĩa là sửa giá mua hoặc tỷ lệ; cũng chưa cho phép bỏ qua việc kiểm tra phiên bản có hiệu lực.

**Raw support là kết quả kiểm tra bằng chứng, chưa là phê duyệt field, historical identity, PIT hoặc canonical freeze.**

### 8.2. Ngày và xung đột tỷ lệ

- Trong 6 đề xuất GDKHQ: một có ngày ghi trực tiếp trong raw HNX của HDP; năm chỉ dựa vào SDK sibling.
- Trong 7 đề xuất ĐKCC: sáu có ngày ghi trực tiếp trong nguồn chính thức; một chỉ dựa vào SDK sibling.
- Trong 36 ratio conflicts: 23 có dấu hiệu provider rounding, một khác precision ở nguồn, mười có khả năng VCI tách component còn nguồn ghi tổng, hai có explicit yearly components cần review.

Đây là chẩn đoán, chưa áp dụng tolerance hay tự gộp tỷ lệ. Ví dụ cùng ngày, hai dòng cổ tức theo hai năm không được tùy ý coi là hai lần điều chỉnh độc lập nếu thông báo tổng mô tả cùng một đợt phát hành.

## 9. Lập supplemental plan và thử nguồn mới

Đã tách các đầu việc thay vì thu thập lại toàn bộ:

| Nhóm | Phạm vi |
|---|---|
| Có raw support, chờ field review | 195 price payloads |
| Cần kiểm tra giá/đơn vị/tỷ lệ/revision thêm | 49 price payloads |
| Thiếu ít nhất một field chưa có single-value proposal | **602 payloads trên 332 mã** |
| Coverage VCI chưa có dòng | 182 mã riêng |

602 payloads chứa **1.373 field tasks** = 482 GDKHQ + 481 ĐKCC + 410 giá quyền mua. Các nhóm field có giao nhau trên cùng payload.

Không cộng 195, 49, 602 và 182 thành số sự kiện: chúng khác đơn vị và có thể giao nhau. Danh sách 602 giữ cờ lifecycle chưa xác minh để phân biệt phương án, sự kiện đã thực hiện và trường hợp dừng/hủy.

### 9.1. Pilot năm mã, sáu URL dự kiến

Formal pilot có năm request attempts, bốn raw HTTP bodies được lưu, ba tài liệu được transport chấp nhận và một PDF ABB được bỏ qua sau source stop. Có một probe trước đó không nhận được body. Web discovery là hoạt động riêng; underlying HTTP của search không được đo bằng số request acquisition.

| Mẫu | Kết quả thực tế | Giới hạn còn lại |
|---|---|---|
| ABB | Raw HTML đã nhận ghi 10.000 đồng/cổ phiếu, ĐKCC 10/11/2021 và quyền mua 5:1, khớp một missing-price payload | Có thêm **một candidate**. Bộ lọc gặp recaptcha asset và dừng; nghi false positive, chưa sửa gate hoặc gọi thêm host/alias. |
| FIT | Tải và xem đủ sáu trang PDF; đối chiếu ĐKCC và tỷ lệ | Dòng giá primary offer vẫn chỉ ghi 10.000 đồng. Unit ở residual placement không được mượn sang primary offer. Scan cần OCR nếu muốn trích tự động, nhưng OCR không tự bổ sung unit không có trên trang. |
| AAS | Xem đủ hai trang tờ trình năm 2025 có nội dung báo cáo tạm dừng phương án và đề nghị đổi lịch | Tài liệu draft/undated; cần nghị quyết gốc và xác định đúng ratio/event. Chưa điền ngày hoặc kết luận VCI row đã bị hủy. |
| AGF | Trang tìm kiếm VSDC đầu tiên trả 20 links trong 31 records được báo cáo | Chưa lấy trang tiếp và details; chưa chứng minh coverage toàn kỳ hoặc không có sự kiện. |
| AGG | Trang issuer IR gặp lỗi xác minh chứng chỉ | Giữ source stop; chưa có primary evidence hợp lệ từ URL này. |

Một số bản ghi thiếu ngày có thể liên quan phương án chưa thực hiện. Pilot chỉ cung cấp bằng chứng để tiếp tục xác minh khả năng này; chưa cho phép gán nhãn đó cho toàn bộ 482 missing-ex payloads.

### 9.2. Xử lý hai ưu tiên ABB/AAS — đã thực hiện 02/11/2026

Stage này kiểm tra hai mã, gồm một payload ABB và hai payload AAS. Bảy acquisition requests đã thực hiện trong budget tám lượt; HNX không được gọi, không chạy bulk.

**ABB:** đã xác minh hai CAPTCHA markers nằm trong đúng một script helper không có active widget. Checker mới chỉ chấp nhận đúng URL, h1, cấu trúc bài viết và script hash đã kiểm tra. Các challenge thật, HTTP 401/403/429, redirect, widget hoặc template khác tiếp tục bị chặn; shared checker mặc định không được nới cho mọi nguồn.

GET thử lại đúng URL ABB đã nhận HTTP 200. Giá 10.000 đồng/cổ phiếu, ĐKCC 10/11/2021 và quyền mua 5:1 khớp candidate đã lưu. Đây là **một candidate cũ được củng cố**, không phải thêm một sự kiện hoặc tự tăng số accepted rows.

**AAS:** đã tải và xem đủ ba trang PDF nghị quyết 18/2024/AAS/NQ-HĐQT, cùng hai trang công bố nghị quyết 18 và 20 của doanh nghiệp.

| Mốc | Bằng chứng đã có | Kết luận được phép ghi nhận |
|---|---|---|
| 25/03/2024 — nghị quyết ĐHĐCĐ 01/2024 | Được viện dẫn trong nghị quyết 18 và trang công bố 20; chưa lấy bản gốc cuối cùng | Giữ reference; chưa dùng draft thay bản gốc |
| 13/09/2024 — nghị quyết 18 | PDF gốc ba trang | Kế hoạch cổ tức năm 2023 bằng cổ phiếu 4%, tương ứng 25:1; dự kiến quý IV/2024 và còn điều kiện thông báo của cơ quan quản lý |
| 12/11/2024 — nghị quyết 20 | Trang công bố chính thức; public metadata không có PDF đính kèm | Doanh nghiệp thông báo tạm dừng phương án cổ tức theo cùng nghị quyết ĐHĐCĐ; chưa có PDF nghị quyết 20 để xem toàn văn |

Một payload AAS cổ tức bằng cổ phiếu **4%** có thêm primary lifecycle evidence hỗ trợ khả năng đây là phương án được triển khai rồi thông báo tạm dừng. Chưa được coi dòng đó là executed event để tính điều chỉnh. Payload AAS **quyền mua 100%** vẫn unresolved; không chuyển kết luận tạm dừng cổ tức sang loại phát hành khác.

Chưa có ngày GDKHQ/ĐKCC mới được điền. Không xác nhận giờ công bố lịch sử bằng ngày văn bản, PDF signature appearance hoặc ngày ghi trên website. Mọi lifecycle/field proposal vẫn `MANUAL_REVIEW_REQUIRED`.

Self-review ghi nhận một lỗi đóng gói ở manifest metadata mới: entry tự tham chiếu được hash lúc file còn rỗng. Raw và các entry còn lại khớp receipts. Artifact được giữ nguyên; findings có chỉ mục xác minh thay thế riêng, không sửa raw hoặc bỏ qua mismatch raw.

Kết quả: 56 targeted tests, compileall và synthetic smoke PASS. Source gate ABB PASS chỉ cho exact article; data readiness vẫn PARTIAL. Accepted fields, canonical rows và price factors đều bằng 0.

Output hiện hành của stage:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_abb_aas_findings_20261102_v1\stage_summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_abb_aas_findings_20261102_v1\abb_field_proposal.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_abb_aas_findings_20261102_v1\aas_lifecycle_review.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_abb_aas_findings_20261102_v1\missing_documents.json
```

## 10. Tình hình hiện tại: những gì đã và chưa hoàn thành

| Nội dung | Kết luận đến 02/11/2026 |
|---|---|
| Raw và exports | Đã có, giữ nguyên và có provenance/hash |
| Full VCI monthly acquisition | Hoàn thành 84/84 windows |
| Offline reconciliation và raw review | Đã hoàn thành stage, output dùng cho review |
| Giá quyền mua có raw support từ stage trước | 195 payloads |
| Candidate giá mới từ pilot ABB | Một; giữ riêng, chưa cộng vào 195 như accepted data |
| Xử lý source gate ABB sau pilot | PASS cho đúng một public article; candidate giá cũ đã được kiểm tra lại |
| AAS cổ tức 4% | Có nghị quyết triển khai gốc và primary suspension notice; lifecycle chờ review, chưa có ngày thực hiện |
| Field changes được chấp nhận vào canonical trong các stage tổng hợp | **0** |
| Bản ghi `corporate_actions` canonical mới được ghi | **0** |
| Hệ số điều chỉnh / backtest | Chưa tạo |
| PIT, historical identity, Q11, final freeze | Chưa được promote/phê duyệt |
| Readiness cho bổ sung hàng loạt trên mọi nguồn | **PARTIAL / MANUAL_REVIEW_REQUIRED** |

Số field gốc chưa được accepted fill vẫn là 488 GDKHQ, 488 ĐKCC và 654 giá quyền mua trong nhóm ưu tiên. Các số **482 / 481 / 410** là phần chưa có single-value proposal sau đối chiếu; chúng chưa thể được gọi là số thiếu sau canonical repair.

## 11. Việc còn lại sau stage ABB/AAS

**Stage ABB/AAS ở mục 9.2 đã thực hiện.** Kế hoạch ghi trước đó ở mục 11.1–11.2 dưới đây nay được đối chiếu với kết quả thực tế. Việc tiếp tục cần tập trung vào các tài liệu còn thiếu và field/source gaps; chưa chạy lại crawler cho toàn bộ 602 payloads hoặc build canonical.

### 11.1. Ưu tiên 1 — ABB: xác minh bộ lọc CAPTCHA từ raw đã lưu

1. Xác định keyword đang nằm ở form asset hay trang thực sự yêu cầu giải challenge hoặc bị từ chối truy cập.
2. Nếu có đủ bằng chứng là false positive, đề xuất sửa checker theo cấu trúc trang cụ thể; giữ chặn các trường hợp challenge/access denial thực sự.
3. Chạy targeted tests cho cả trang public và trang bị chặn. Chỉ chạy pilot mạng giới hạn sau khi access gate phù hợp; không dùng đổi host/IP hoặc bỏ SSL để tiếp tục.
4. Xuất một field proposal của ABB kèm mã, ĐKCC, tỷ lệ, unit, raw hash và quote. Chưa tự approve canonical.

Đầu ra này đã có ở mục 9.2 cho đúng một URL. Muốn áp dụng cho ABB article khác phải có source-specific evidence/pilot riêng; chưa được dùng exception này cho toàn bộ website.

### 11.2. Ưu tiên 2 — AAS: tìm nghị quyết gốc để làm rõ lifecycle

1. Đối chiếu các tham chiếu trong tờ trình: nghị quyết ĐHĐCĐ năm 2024, nghị quyết triển khai ngày 13/09/2024 và nghị quyết tạm dừng ngày 12/11/2024.
2. Kiểm tra loại phát hành, tỷ lệ, năm cổ tức và định danh đợt phát hành, thay vì chỉ ghép theo ticker/ngày gần nhau.
3. Phân loại ứng viên theo bằng chứng: kế hoạch, đợt đã chốt quyền, thông báo sửa đổi hoặc phương án tạm dừng. Nếu chưa đủ, giữ unresolved.
4. Không tạo `ex_date` cho một phương án chưa chứng minh đã thực hiện; không tự thay final research sample từ kết quả phân loại.

Timeline đã có ở mục 9.2. Còn thiếu bản gốc cuối cùng của nghị quyết ĐHĐCĐ 01/2024 và PDF nghị quyết 20; cần tiếp tục làm rõ riêng phương án quyền mua 100%. Không dùng tờ trình draft hoặc thông báo tạm dừng cổ tức để kết luận thay cho hai đầu việc đó.

### 11.3. Các công việc tiếp sau hai ưu tiên trên

| Nhóm | Việc cần làm | Tiêu chí có kết quả |
|---|---|---|
| FIT và 24 unit cases | Tìm bản chào bán/bản cáo bạch ghi rõ đơn vị cho primary offer; OCR có chọn lọc đối với scan | Có đúng field và đúng vai trò kinh tế, hoặc ghi rõ chưa giải quyết được |
| 22 term cases và 36 conflicts | Review ratio direction, allocation/execution legs, precision, component và revision | Mỗi case có evidence và disposition; không tự áp dụng tolerance/aggregation chưa duyệt |
| AGF và 182 coverage cases | Thử pagination giới hạn, lọc thông báo đúng loại và đúng kỳ trước khi tải details | Báo rõ trang đã đọc, phần chưa đọc và event coverage; không suy NO_EVENT từ thiếu rows |
| AGG | Kiểm tra chuỗi chứng chỉ với trusted roots, giữ nguyên SSL verification | Có kết luận kỹ thuật về trust chain trước acquisition mới; không bypass |

### 11.4. Điều kiện mới được mở thu thập bổ sung hàng loạt

- Source/pilot gate của kênh dự kiến chạy phải có evidence phù hợp.
- Có cơ chế giữ raw, hash, URL, page/reference, checkpoint và source-stop.
- Parser phân biệt đúng component và vai trò giá; không lấy giá xử lý phần dư thay giá primary offer.
- Queue được phân theo nhu cầu dữ liệu và lifecycle; không chạy lại những tài liệu đã có và vẫn dùng được chỉ để tăng số dòng.
- Kết quả phải báo riêng fields tìm thêm, fields còn vướng và coverage chưa chứng minh được.

Sau giai đoạn bổ sung mới chuẩn bị ledger candidate và gói review để tiến tới `corporate_actions`. Thay đổi PIT/historical identity/final canonical freeze hoặc chính sách giá phải được đề xuất rõ và giữ `MANUAL_REVIEW_REQUIRED` đến khi người dùng duyệt.

### 11.5. Kiểm kê cache VSDC trước thu thập mới — đã thực hiện

Người dùng yêu cầu kiểm tra dữ liệu đã lưu trước khi tải bổ sung. Stage này chạy
hoàn toàn offline: **0 network requests**, gồm **0 HNX requests**. Đã đọc 5
manifest, 3.088 request ledgers và xác minh 29.290 phản hồi raw: 1.529 search,
27.761 article responses tương ứng 27.730 provider article IDs. Đơn vị response
là tổ hợp URL/hash, không phải số sự kiện doanh nghiệp.

Trong article cache có 9.181 phản hồi được nhận diện loại quyền ảnh hưởng giá,
15.836 thông báo họp/lấy ý kiến không được nhận diện loại quyền giá và 2.744
chưa phân loại. Đây là kết quả detector, không chứng nhận economic event coverage.
1.461 phản hồi thiếu declared ticker hợp lệ; không lấy ticker từ tên job/folder
để lấp vào. 15.604 phản hồi không có mặt trong stream normalized VSDC trước đó;
điều này không có nghĩa tất cả đều là corporate actions bị parser bỏ sót.

Phân loại **602 distinct VCI SDK payloads / 332 ticker** của queue thiếu trường:

| Nhóm sau kiểm kê | Số payloads | Hướng xử lý đề xuất, chưa thực hiện |
|---|---:|---|
| Giá đã có trong raw và normalized, vướng ratio precision | 18 | Review offline 17 possible provider-rounding và 1 source-precision case; không tự nới tolerance |
| Whole-article HTML có giá, component chưa phân định | 8 | Review/tách đúng phần quyền mua trong bài gộp cổ tức/quyền mua, giữ component khác riêng |
| Chỉ có tài liệu khác hoặc chưa liên kết đúng event | 554 | Kiểm tra event/component/lifecycle và references trước khi kết luận cần tài liệu mới |
| Chưa có document xác định ticker bằng label trong cache VSDC được kiểm kê | 21 | Rà soát identity/coverage và cache các nguồn khác; không suy NO_EVENT |
| Có weak candidate nhưng chưa xác minh liên kết | 1 | Review riêng; tỷ lệ và ngày gần nhau không đủ event identity |
| **Tổng** | **602** | Các nhóm trên không chồng lặp ở cấp payload |

18 payloads thuộc17 ticker;8 mixed-component payloads thuộc7 ticker. Cả8 bài
mixed đều có literal giá ở whole-article text. Audit gốc dùng enum
`MATCHED_CACHED_DOCUMENT_FIELD_NOT_EXPLICIT` cho8 trường hợp này vì extractor
không mở fragment chưa xác minh; **không được đọc enum đó thành kết luận HTML
không có giá**. Findings V2 tách rõ component blocker và giữ literal/provenance.

**Trước/sau approval:** 1.373 field tasks vẫn là 482 ex_date, 481 record_date,
410 rights_subscription_price; accepted fields **0**. Hai nhóm18+8 tạo **26
payloads nên ưu tiên xử lý offline**, chưa là26 field fills được chấp thuận.
49 additional price reviews được kiểm tra riêng, không cộng vào602; toàn bộ
195 prior supported price candidates và các review flags cũ vẫn được giữ.

Trong182 ticker không xuất hiện ở VCI,180 có article VSDC với declared ticker;
PCB/UPS chưa có trong phạm vi này. Có cache không đồng nghĩa có sự kiện đúng kỳ;
không có cache cũng không chứng minh không có sự kiện. All article IDs quan sát
trong cached search đã có raw: **0 observed uncached IDs**. Kết quả đó chỉ nói
về các trang đã lưu, không chứng minh toàn bộ historical pagination đã được đọc.

Kết luận thực hành: **chưa có cơ sở thu thập lại toàn bộ VSDC**. Ưu tiên review
offline26 payloads trên, rồi xác định tài liệu thật sự cần discovery mới. Stage
này không sửa parser/matching production, không điền dữ liệu, không đổi PIT,
historical identity, price policy, canonical hoặc readiness. Tất cả approval
vẫn `MANUAL_REVIEW_REQUIRED`; công việc tiếp theo chưa tự động được thực hiện.

Output hiện hành:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cache_inventory_20261102_v4\summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cache_inventory_20261102_v4\field_cache_audit.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cache_findings_20261102_v2\findings.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cache_findings_20261102_v2\cached_price_match_review_18.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cache_findings_20261102_v2\mixed_component_review_8.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cache_inventory_validation_20261102_v1\self_review.json
```

Findings V2 sửa một câu diễn giải hard-coded của Findings V1 đã trộn số payload
với số field tasks; numeric partition V1 đúng và artifact cũ giữ nguyên. Các
thư mục inventory v1/v2/v3 là lượt kiểm kê đã dừng để tối ưu đọc file Windows,
không có sealed manifest và không được dùng làm kết quả. Inventory V4 được đọc
theo nhóm local có giới hạn và có checkpoint chỉ mục từng phần; không thay delay
hoặc cơ chế truy cập nguồn.

Self-review PASS: kiểm tra lại **32.393 input file hashes**,10 output hashes,
5 code hashes và42 literal price/unit checks;0 integrity/parse issues.48 targeted
tests,compileall và synthetic smoke PASS. Raw/checkpoint/artifact cũ giữ nguyên.

### 11.6. Review offline26 dòng đã có giá trong cache — đã thực hiện

Người dùng yêu cầu bước tiếp theo và hỏi về nhu cầu nguồn bổ sung. Stage chỉ
xử lý18 precision payloads +8 mixed-component payloads đã xác định, không mở
network, không reparse lại toàn bộ cache. Input là sealed Findings V2 và các
raw/hash tương ứng trong sealed cache inventory V4; inventory C8 v2 vẫn1.522.

Đã parse27 raw response versions thành39 component records riêng. Số27 bao gồm
hai raw versions của cùng bài AAN; số39 là component evidence records, không là
số corporate actions cuối cùng. Giữ source URL/hash, full decoded text, section
offsets, price quotes, exact ratio fractions và nguyên bản VCI SDK rows.

Parser preview mới nhận diện phần mục đích chỉ liệt kê tiêu đề và phần nội dung
có điều khoản, hỗ trợ1.1/1.2,b.Thực hiện thiếu space vàheading Quyền mua. Mỗi
loại quyền phải có một section chứa terms duy nhất; ambiguity vẫn fail-closed.
Giữ riêng cổ tức/quyền mua,không lấy đơn vị từ giá cổ phiếu dư cho primary offer.
Shared production parser vàmatching policy chưa được thay đổi trong stage này.

| Kết quả trên26 payloads | Trước | Sau review offline |
|---|---:|---:|
| Mixed-component payloads đã phân định scope quyền mua | 0/8 | 8/8 |
| Supported price candidates trong cohort26 | 0 | 5 |
| Payloads còn cần review tỷ lệ/precision | 18 ban đầu,2 còn nằm trong mixed scope | 20 |
| Payloads còn thiếu unit tại primary price | Chưa phân định từ whole-article text | 1 (ASG) |
| Accepted field changes/canonical rows/price factors | 0 | 0 |

Năm candidate có giá,unit vàratio được hỗ trợ ở cấp dữ liệu:

| Ticker | Ngày ĐKCC theo source/review view | Giá candidate (VND/share) | Kiểm tra ratio |
|---|---|---:|---|
| CIA | 12/09/2019 | 15.000 | Comparison10decimal hiện hành; giữ exact20/37 |
| KPF | 20/01/2021 | 10.000 | Exact |
| LCG | 13/12/2019 | 10.000 | Exact |
| SCI | 28/12/2020 | 10.000 | Exact |
| TIP | 29/04/2022 | 25.000 | Exact; giữ riêng allocation3/2 vàexecution1/1 |

Đây là **5 candidate pending review**, không phải5 dòng canonical đã chấp thuận
hoặc đủ mọi trường để backtest. Trước/sau approval của queue gốc vẫn602 payloads
và1.373 field tasks; không trừ5 đề xuất khỏi queue khi chưa được duyệt.

Nhóm18 ban đầu giữ17 possible provider-rounding và1 source-precision case (DTP).
Hai trường hợp mixed mới chuyển sang ratio review làKOS vàLCG ngàyĐKCC21/10/2021.
Không tự nới tolerance hoặc ghi đè SDK ratio bằng exact source fraction.
ASG cóprimary literal18.000 đồng nhưng không có unit trực tiếp; câu nói về
18.000 đồng/cổ phiếu trong phần xử lý cổ phiếu dư không được mượn để lấp unit.

**Nhu cầu nguồn khác:** cần bổ sung có mục tiêu nếu cache hiện có không chứng minh
được field. ASG là một yêu cầu cụ thể: rà cache nguồn khác, rồi tìm tài liệu
chào bán/bản cáo bạch của doanh nghiệp ghi unit cho primary offer.20 ratio cases
ưu tiên review bằng chứng đã có; không mặc định crawl lại.576 payloads còn lại
trong queue602 và49 price reviews riêng chưa thuộc stage này. Cần review event
link/coverage của chúng trước khi xác định danh sách tài liệu cần thu thập thêm.
Không suy source unavailable hoặc NO_EVENT chỉ từ thiếu cache. HNX vẫn STOP.

Output mới:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cached26_review_20261102_v1\summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cached26_review_20261102_v1\supported_price_candidates.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cached26_review_20261102_v1\remaining_review.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cached26_review_20261102_v1\scoped_component_candidates.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cached26_review_20261102_v1\next_actions.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_cached26_validation_20261102_v1\self_review.json
```

Self-review PASS:34 input hashes,8 output hashes,6 code hashes được kiểm tra lại;
127 section/price/ratio quote checks và5 kiểm tra primary-price/unit độc lập;
nguyên bản SDK/prior flags của26 payloads được bảo toàn.64 targeted tests gồm16
tests mới,compileall vàsynthetic smoke PASS.0 network/HNX,0 accepted fields;
PIT,identity,Q11,price policy vàreadiness giữ nguyên. Stage dừng sau bàn giao;
review/approval hoặc discovery mới là công việc riêng.

### 11.7. Hoàn thiện gói quyết định25 dòng — đã thực hiện, chưa áp dụng

Phạm vi là5 price candidates +20 ratio-review payloads từ stage11.6,không gồm
ASG. Đã rà390 response versions của386 provider article IDs trong scoped VSDC
cache cho23 ticker contexts. Dùng explicit record/component hoặc rights-code
references; title hint chỉ để discovery. Không khẳng định full archive coverage,
historical identity hoặc terminal execution từ việc có thông báo quyền mua.

Kết quả gói25:

| Nhóm quyết định đề xuất | Số payloads | Trạng thái |
|---|---:|---|
| Chọn giá theo comparison hiện hành | 3 | CIA,SCI,TIP; pending owner review |
| Chọn exact source ratio vàgiá theo từng tài liệu cụ thể | 15 | Cần phê duyệt case-specific field selection; không nới tolerance chung |
| Có thông báo sửa đổi/gia hạn liên quan | 6 | Conditional requests sau lineage/change-scope review |
| Tỷ lệ cần thêm bằng chứng gốc | 1 | DTP; chưa chọn tỷ lệ |
| **Tổng** | **25** | **MANUAL_REVIEW_REQUIRED; approved/applied0** |

Ba candidate theo comparison hiện hành:

| Ticker | Ngày ĐKCC source/review view | Giá đề xuất (VND/share) | Source ratio evidence |
|---|---|---:|---|
| CIA | 12/09/2019 | 15.000 | 20/37; comparison10decimal |
| SCI | 28/12/2020 | 10.000 | 1/1 |
| TIP | 29/04/2022 | 25.000 | 3/2 |

Mười lăm case-specific proposals,giữ nguyên SDK ở dữ liệu nguồn:

| Ticker | Ngày ĐKCC | SDK ratio | Exact source ratio đề xuất | Giá (VND/share) |
|---|---|---:|---|---:|
| AAN | 24/10/2025 | 0.85714286 | 6/7 | 15.000 |
| BQP | 17/12/2025 | 0.23333333 | 7/30 | 15.000 |
| DXG | 07/01/2025 | 0.20833333 | 5/24 | 12.000 |
| IJC | 17/09/2025 | 0.66666667 | 2/3 | 10.000 |
| NHH | 03/11/2020 | 0.05807 | 50/861 | 45.000 |
| PGB | 19/03/2025 | 0.19047619 | 4/21 | 10.000 |
| PRE | 16/12/2022 | 0.4341 | 79/182 | 20.000 |
| RGG | 29/08/2025 | 0.11111111 | 1/9 | 10.000 |
| SCL | 20/10/2025 | 0.35714286 | 5/14 | 12.500 |
| SSI | 09/09/2021 | 0.16666667 | 1/6 | 10.000 |
| TEG | 30/08/2021 | 0.66667 | 2/3 | 10.000 |
| TPP | 17/10/2025 | 0.44444444 | 4/9 | 10.000 |
| TSC | 29/03/2022 | 0.33333333 | 1/3 | 10.000 |
| VMK | 04/02/2025 | 0.8018018 | 89/111 | 10.000 |
| LCG | 21/10/2021 | 0.43384636 | 12500000/28812043 | 10.000 |

19 trong20 ratio cases (15 bảng trên +4 conditional cases) consistent
với HALF_UP tại recorded SDK decimal scale bằng exact rational arithmetic.
Đây chỉ là diagnostic toán học,không chứng minh phương pháp biến đổi của provider
hoặc tự loại trừ mọi khác biệt kinh tế. Đề xuất chỉ chọn observed source values
theo đúng từng case khi được duyệt,không tự thay SDK hoặc source priority chung.

Sáu conditional cases có8 cached change documents:

| Ticker/đợt | Bằng chứng thay đổi quan sát được | Điều kiện còn lại |
|---|---|---|
| DXG ĐKCC15/12/2023 | Đính chính tài khoản phong tỏa nhận tiền | Xác nhận liên kết thông báo gốc1579/TB-CNVSDC; giữ account correction riêng |
| GSP ĐKCC23/08/2021 | Hai thông báo gia hạn chuyển nhượng/đăng ký mua | Xác nhận chuỗi1203→1323 vàthông báo tiếp theo |
| SPB ĐKCC20/03/2023 | Điều chỉnh lịch thực hiện quyền,mãMIRSPB231 | Review lineage vàscope lịch; không tự đổi giá/tỷ lệ |
| KOS ĐKCC29/12/2020 | Điều chỉnh lịch,mãMIRKOS201 | Review thông báo3716/TB-VSD vàcác mốc thay đổi |
| KPF ĐKCC20/01/2021 | Điều chỉnh lịch,mãMIRKPF211 | Cùngnotice44/TB-VSD ghi08/01/2021 và07/01/2021; giữ anomaly |
| LCG ĐKCC13/12/2019 | Hai thông báo gia hạn lịch | Review chuỗi1451→310 vàthông báo tiếp theo |

Cả8 documents đều có câu giữ các nội dung khác không thay đổi:1 account
correction và7 schedule changes. Gói có conditional price requests,nhưng vẫn
HOLD_LINKED_CHANGE_REVIEW cho đến khi xác nhận lineage vàscope. Không tự kết
luận hủy đợt phát hành từ expiry của mã quyền hoặc hủy cổ phiếu lẻ. KPF vàLCG2019
vì vậy chuyển từ5 candidate ban đầu sangconditional; artifact cũ được giữ nguyên.

DTP ĐKCC20/12/2021: source ghi33,3333%,tương đương333333/1000000=0.333333;
VCI ghi0.33333333. Giá11.000 đồng/cổ phiếu có bằng chứng,nhưng ratio không được
tự nâng thành1/3. Gói yêu cầu tìm resolution/prospectus hoặc explicit correction
của đúng đợt để xác nhận tỷ lệ. Đây là document request,chưa có network request.

Đã có **18 direct proposals +6 conditional cases +1 evidence hold**,không có
approved fields/canonical rows. Số approved trước/sau0→0,network/HNX0,PIT/identity/
price basis/readiness giữ nguyên. Không tạo reviewer hoặc signature giả; JSON
packet không thể được coi là production signed review CSV.

Output hiện hành:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_decision25_20261102_v2\decision_table.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_decision25_20261102_v2\decision_requests_25.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_decision25_20261102_v2\approval_proposal.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_decision25_20261102_v2\cached_change_review_requests.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_decision25_20261102_v2\missing_document_requests.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_decision25_validation_20261102_v1\self_review.json
```

V1 giữ nguyên là packet trước khi bổ sung narrow-change classification và
conditional requests; dùngV2 để review hiện hành. Self-review PASS:402 input
hashes,8 output hashes,7 code hashes,112 quote checks,26 independent exact ratio-
leg checks vàbảo toàn SDK25 payloads.83 targeted tests gồm19 mới,compileall và
synthetic smoke PASS. Không chạy tiếp stage khác.

**Bước tiếp theo đề xuất:** rà cache/tìm tài liệu issuer có mục tiêu choDTP
(exact offering ratio) vàASG (primary price unit). Việc áp dụng field/source
selections trong packet này cần owner duyệt cụ thể theoAGENTS.md trước; không
suy approval từ yêu cầu lập gói vàkhông tự freeze canonical/research sample.

### 11.8. Bổ sung tài liệu choDTP vàASG — đã thực hiện

Stage chỉ hai target: DTP quyền mua ĐKCC20/12/2021 cần issuer ratio evidence;
ASG quyền mua ĐKCC13/02/2020 cần unit cho primary price. Rà lại sealed cache32
VSDC article responses và5 HOSE normalized rows liên quan trước khi acquisition.
Không sử dụng đợtASG2024 để lấp field chođợt2020. C8 v2 vẫn1.522 mã.

Đã tải **3 PDF hoàn chỉnh,131 trang tổng cộng**. Đã xem14 unique pages liên quan:
DTP toàn bộ4+2 trang;ASG các trang1,103–108,125. Không tuyên bố đọc hết125 trangASG.
Đây là scan: dùng visual transcription kèmPNG/page/hash,không giả OCR text.

| Target | Bằng chứng mới | Trước → sau ở cấp evidence |
|---|---|---|
| DTP ratio | Thông báo2310/2021/TB-CPC1HN ngày02/12/2021,trang2 | Chưa có issuer document → issuer notice xác nhận33,3333% |
| DTP event link | NQ2307/2021/NQ-HĐQT ngày02/12/2021,trang1 | Xác nhậnĐKCC20/12/2021 vàlịch đăng ký mua27/12/2021–17/01/2022 |
| ASG primary unit | Offering prospectus trang104–105 | Primary literal thiếuunit trongVSDC → có18000đồng/cổ phiếu và18000đồng/cổ phần trực tiếp ởprimary offer |
| Approved fields/canonical | Không apply lựa chọn | 0 → 0 |

**DTP:** thông báo chào bán doCPC1 Hà Nội phát hành,tải từwebsite tổ chức tư vấn
ASEANSC được nêu ngay trong văn bản. Trang2 ghiquantity4.057.260 shares,giá11.000
đồng/cổ phiếu,tỷ lệ33,3333%,allocation1right/share và100rights mua33,3333new shares.
Tỷ lệ literal tương đương333333/1000000=0.333333,khớp VSDC. NQ2307 trang1 ghi
ĐKCC20/12/2021;NQ vànotice cùng tham chiếulicense272/GCN-UBCK ngày26/11/2021 và
ngày văn bản02/12/2021. VCI0.33333333 giữ nguyên,không suy1/3 hoặc tuyên bố đã
chứng minh provider transformation. Có proposal chọn observed source ratio
khiowner duyệt,không tự áp dụng.

**ASG:** bản cáo bạch chào bán ra công chúng doASG phát hành,bản copy trênmarket
archiveVietstock. Trang104 mụcprimary offer ghi7.244.987 shares vàgiá18.000đồng/
cổ phiếu. Trang105 ghi approved price18.000đồng/cổ phần theoNQ34/2019/NQ-HĐQT/ASG
ngày27/12/2019,vàallocation1right/share,100rights mua15new shares. Khớp cached
VSDC amount/quantity/ratio vàplannedQ1/2020 period. Đây làunit gắn primary offer,
không mượn từresidual placement. NgàyĐKCC vẫn có provenanceVSDC13/02/2020;
prospectus planned period không chứng nhận actual execution hoặc PIT.

Nguồn tài liệu:

- DTP: https://www.aseansc.com.vn/uploads/2021/12/TB-chao-ban-CP-ra-cong-chung.pdf
- DTP: https://www.aseansc.com.vn/uploads/2021/12/NQ-cua-HDQT-ve-thoi-gian-trien-khai-phuong-an-chao-ban-co-phieu-cho-Co-dong-hien-huu.pdf
- ASG: https://static2.vietstock.vn/data/OTC/2020/BAN%20CAO%20BACH/VN/ASG_Bancaobach_2020.pdf

Acquisition provenance:11 formal attempts gồm3 DNS failures trongsandbox và8
HTTP responses (1 HEAD,7 GET). Web discovery qua search/open là phần riêng,chưa
instrument để claimtotal physical network requests. Giữ nguyên tất cả attempts.
DTP pageHTTP200 có đầy đủ bài vàPDF links nhưng keyword gate gặp6 occurrences
trong3 CF7 reCAPTCHA script tags. Saved-snapshot diagnostic pin exactbody/h1/
script hashes;không execute scripts/CAPTCHA/forms,không retry live page hoặc sửa
shared gate. Chỉ tải2 public PDFs có sẵn trongsnapshot. Default live-page gate
vẫn đánh dấu chính savedHTML đó;PDF HTTP denial/challenge/TLS gates không nới.

ASG prospectus scan37.431.551 bytes,vượt caps5MB và20MB. Các partial files được
giữ nguyên vàkhông parse nhưevidence. Lượt cuốiHEAD xác nhậnlength,fullGET khớp,
hard cap64MB chỉ đúngprospectusURL này;normalPDFs vẫn5MB. Không Range/chia tải,
tắtSSL,đổiIP hoặc vượt login/access control. Không theo SharePoint folder/S3
signed URLs hoặc gửi credentials. HNX không được gọi.

Output hiện hành:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_dtp_asg_evidence_20261102_v1\field_proposals.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_dtp_asg_evidence_20261102_v1\documents_reviewed.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_dtp_asg_evidence_20261102_v1\summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_dtp_asg_evidence_20261102_v1\visual_transcriptions.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_dtp_asg_pdfs_20261102_v1\raw
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_asg_prospectus_20261102_v1\raw\response-0001.bin
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_dtp_asg_validation_20261102_v1\self_review.json
```

Hai target evidence goals đã được bổ sung;owner approval vẫn0,không áp dụng
packet25 hoặc ghi đèsourceSDK/raw. Mọi field selections MANUAL_REVIEW_REQUIRED.
Không thay PIT/historical identity/Q11/price basis/research readiness. Dấu
chữ ký/con dấu nhìn thấy trongscan không làcryptographic signature verification.
Ngày văn bản không tự trở thànhpublication timestamp/available_at.

Kiểm tra:108 targeted tests gồm17 mới vàdefault access regressions,compileall
vàsynthetic smoke PASS. Self-review18 input hashes,28 output hashes,2 code hashes;
3 complete PDFs verified. Independent re-renderASGpage104 vàDTPnoticepage2 khớp
hashPNG gốc;fraction/percent/rights legs vàold-new price/quantity/date checks PASS.
DTP có duplicateInfo-key metadata warnings;raw không sửa và6 rendered pages
được đọc trực tiếp. Không tuyên bố không córevision ngoài phạm vi đã review.

**Bước tiếp theo đề xuất:** hoàn thiện original-to-revision linkage của6 conditional
cases (DXG2023,GSP2021,SPB2023,KOS2020,KPF2021,LCG2019) từcache hiện có,rồi trình
toàn bộ observed-field selections cụ thể choowner duyệt trước application. Stage
này đã dừng,không tự thực hiện bước đó hoặc mởbulk crawl.

### 11.9. Rà sáu chuỗi thông báo sửa đổi — đã thực hiện, còn hai HOLD

Phạm vi: DXG ĐKCC 15/12/2023, GSP 23/08/2021, SPB 20/03/2023, KOS 29/12/2020,
KPF 20/01/2021, LCG 13/12/2019. Đơn vị đếm là sáu VCI SDK payloads/sáu ticker
contexts; không phải toàn bộ corporate actions. Dùng 6 thông báo gốc và 8 thông
báo sửa đổi đã lưu, xác minh hash và tái tạo article text. Không thu thập lại,
không network, không thay C8 v2 inventory 1.522.

| Trường hợp | Bằng chứng sau rà soát | Kết quả |
|---|---|---|
| DXG | Tài khoản cũ khớp original; chỉ đính chính tài khoản, điều khoản khác không đổi | Đề xuất giá 12.000 VND/share và ratio 1/6 |
| SPB | Lịch trước sửa khớp original; gia hạn lịch, điều khoản khác không đổi | Đề xuất giá 20.000 VND/share và ratio 91/190 |
| KOS | Lịch trước sửa khớp original; gia hạn lịch, điều khoản khác không đổi | Đề xuất giá 10.000 VND/share và ratio 5/9 |
| LCG | Original → gia hạn lần một → gia hạn lần hai khớp lịch trước/sau | Đề xuất giá 10.000 VND/share; ratio 3/10 giữ existing-rule evidence |
| GSP | Hai bản gia hạn khớp nhau nhưng chưa nối được với original | HOLD: thiếu thông báo1203/TB-CNVSD hoặc predecessor tương ứng |
| KPF | Các lịch trước sửa khớp original; cùng notice44 lại có hai ngày | HOLD: giữ cả 07/01/2021 và 08/01/2021 |

GSP original kết thúc chuyển quyền 16/09 và nộp tiền 20/09/2021. Bản gia hạn
145371 dẫn notice1203 ngày01/09 với lịch trước sửa kết thúc12/10 và15/10/2021.
Không tự nhảy qua khoảng trống; không kết luận không tồn tại tài liệu ngoài
390 cached responses của packet đã rà. KPF có wording “Hồ sơ đặt mua” ở original
và “Danh sách đặt mua” ở bản sửa; cùng deadline03/03/2021 được kiểm tra lại,
không nhầm đây là thiếu dữ liệu. Date anomaly vẫn độc lập và chưa giải quyết.

Trước: 6 case chờ lineage review. Sau: 4 case có contextual proposals với 7
field requests (4 giá +3 ratio), 2 case HOLD với 3 field requests. Contextual
evidence hỗ trợ 6/8 edges; không tự chứng nhận official notice ID→article binding,
terminal execution hoặc lịch sử identity. Approved/applied fields 0 → 0.
MANUAL_REVIEW_REQUIRED trước mọi field selection; giữ SDK/raw/revision flags,
PIT, giá, features/M2/backtest và readiness như cũ.

Output hiện hành:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_revision6_20261102_v3\case_reviews.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_revision6_20261102_v3\approval_proposal.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_revision6_20261102_v3\followup_evidence_requests.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_revision6_validation_20261102_v1\self_review.json
```

V1/V2 giữ nguyên làm bản trung gian; V3 là kết quả hiện hành sau assertion về
conflicting anchors và wording member deadline. 122 targeted tests (14 mới),
compileall, synthetic smoke và self-review PASS:24 input hashes,5 output hashes,
117 quote checks,6 original price/ratio checks và14 verified raw responses.
Technical review PASS, mức giải quyết dữ liệu PARTIAL.

Bước tiếp theo đề xuất: tìm đúng thông báo GSP1203 và bản gốc KPF44, chỉ cho hai
HOLD này; chưa acquisition trong stage hiện tại. Các lựa chọn đã có evidence sẽ
được trình owner duyệt cụ thể; không tự áp dụng gói25 hoặc hai field DTP/ASG.

### 11.10. Follow-up GSP/KPF — GSP đã nối lịch, KPF còn ngoại lệ

Phạm vi chỉ2 payloads GSP ĐKCC23/08/2021 vàKPF20/01/2021. Đã phát hiện và sửa
nhận định trước: mắt xích GSP đã có trong cache, không phải cần crawl lại. Bài
144289 có tiêu đề chung “Thực hiện quyền mua cổ phiếu”, nhưng body thông báo gia
hạn. Bộ lọc preview trước bỏ sót exact body schedule-extension purpose; nay đã
nhận diện và vẫn yêu cầu before/after continuity, unchanged clause, owner approval.
Giữ nguyên artifact25/revision6 cũ, xuất findings mới có scope reclassification.

Chuỗi GSP từ cache:

| Provider article | Kết thúc chuyển nhượng | Kết thúc đăng ký/nộp tiền |
|---|---|---|
| 143831 — original | 16/09/2021 | 20/09/2021 |
| 144289 — gia hạn, generic title | 12/10/2021 | 15/10/2021 |
| 145371 — gia hạn | 26/10/2021 | 28/10/2021 |
| 145572 — gia hạn | 23/11/2021 | 25/11/2021 |

Cả3 before/after edges khớp. Article145371 dẫn1203/TB-CNVSD ngày01/09/2021 và
lịch predecessor khớp144289. Đây là contextual reference; chưa có signed notice
1203 vàkhông chứng nhận official notice ID→article binding. Đề xuất GSP giá
10000VND/share, exact ratio5/9; SDK0.55556 vàprovenance giữ nguyên. Hai field
requests này vẫn **MANUAL_REVIEW_REQUIRED**, không tự approve hoặc nới tolerance.

KPF: tải PDF HOSE62/TB-SGDHCM ngày13/01/2021 từVietstock market archive,854618
bytes/4 pages. Đã xem cả4 pages:3 trang thông báo và1 trang scan mặt sau gần
trống. Trang1 ghi KPF, ex19/01/2021, record20/01/2021; trang2 primary price10000
đồng/cổ phiếu, rights ratio1:2, quantity36035792; khớp original VSDC. Trang3 có
signature/seal facsimile, không cryptographic verification. Tài liệu không dẫn
VSD44, nên không chọn07/01 hay08/01/2021; không dùng ngàyHOSE13/01 thay thế.
Các mốc này là observations, chưa apply ex-date hoặc các trường khác.

Tìm thêm ở5 public issuer archive pages10/32/22/23/24 theo observed links,
không quét toàn bộ32pages. Linked PDF gia hạn26/02/2021 trảHTTP406; đã STOP
`www.kpf.com.vn`, giữ raw HTML/receipt, không retry/đổi host/IP/header/tắtSSL.
Không dùng denied HTML làm PDF evidence. Không kết luận bản gốc VSD44 không tồn
tại; chỉ chưa tìm được chứng từ giải quyết date anomaly trong phạm vi này.

Trước/sau hai target:0→1 contextual case,2→1 HOLD;2 supported unsigned field
requests và1 held request. Rollup nhóm6 trước:4 contextual/2HOLD; sau:5contextual/
1HOLD,9 supported field requests/1held. Approved/applied fields0→0. C8v2 vẫn1522;
canonical/PIT/identity/price/features/M2/backtest/readiness không đổi.

7 formal requests gồm6HTTP200/1HTTP406:1 complete PDF,5public HTML pages và1
denied document. Search/open/click discovery quaweb tools riêng không instrument
physical source requests, không tính trong7formal. HNX requests0.129 targeted
tests (7mới), compileall, synthetic smoke PASS; self-review45input/8output/4code
hashes,53quotes,6cached raws và3GSP edges. TechnicalPASS/data resolutionPARTIAL.

Output hiện hành:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_gsp_kpf_followup_20261102_v1\summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_gsp_kpf_followup_20261102_v1\case_reviews.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_gsp_kpf_followup_20261102_v1\approval_proposal.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_gsp_kpf_followup_20261102_v1\scope_reclassification.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_gsp_kpf_followup_20261102_v1\kpf_pdf_review.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_gsp_kpf_validation_20261102_v1\self_review.json
```

Bước tiếp theo đề xuất: gộp evidence đã có thành packet lựa chọn field cụ thể
để owner duyệt; giữKPF ngoại lệHOLD, không chặn các trường hợp khác vàkhông tiếp
tục truy cập issuer đangSTOP. Không tự áp dụng packet hoặc mở stage mới.

### 11.11. Hợp nhất gói lựa chọn field để owner duyệt — đã thực hiện

Trước: bằng chứng nằm trong 5 sealed artifacts: cached26, packet25, revision6,
DTP/ASG primary review và GSP/KPF follow-up. Sau: có một gói owner-review chung.
Phạm vi vẫn là 26 distinct SDK payloads thuộc 24 mã đã rà; chưa coi đây là
26 canonical events. C8 v2 inventory 1.522, raw/checkpoint/artifacts cũ giữ nguyên.

| Nhóm | Case | Field requests | Ý nghĩa lựa chọn |
|---|---:|---:|---|
| A — ASG, CIA, LCG 2019, SCI, TIP | 5 | 5 giá | Ratio theo existing comparison rule; không đề xuất thay SDK ratio |
| B — Exact source ratio theo từng case | 19 | 19 giá + 19 ratio | Giá phụ thuộc owner duyệt source ratio của cùng payload; không suy provider rounding |
| C — DTP ĐKCC 20/12/2021 | 1 | 1 giá + 1 ratio | Chọn literal 333333/1000000 = 0.333333, không suy 1/3; giá 11000 VND/share đã có bằng chứng |
| HOLD — KPF ĐKCC 20/01/2021 | 1 | 1 giá giữ lại | Chưa giải quyết ngày VSD44; template chưa cho phép chọn field này |
| Tổng | 26 | 45 đề xuất + 1 giữ lại | Tất cả chưa được phê duyệt/áp dụng |

Hai case DXG và hai case LCG khác record date được giữ riêng, không gộp theo mã.
25 case có đề xuất tương ứng 25 primary-price choices và 20 case-specific ratio
choices. Đây là số đếm trong cohort đã review, không phải tổng số fields thiếu
hoặc đủ trên toàn bộ VCI/C8. Giá là VND/share; ratio là số cổ phiếu mới trên một
cổ phiếu cũ. CIA vẫn giữ SDK 0.5405405405 theo 10-decimal comparison rule, không
tự thay bằng 20/37. ASG có primary unit từ prospectus, không dùng unit của residual placement.

Bảng HTML có 26 dòng với giá trị đề xuất, SDK giữ nguyên và source fractions.
Phần details chứa quotes, hashes, raw paths, PDF pages, revision context, điều
kiện và choice IDs. HTML không tải tài nguyên bên ngoài hoặc chạy script.
JSON packet giữ nguyên các SDK rows; template để trống owner/name/time/signature/
decisions và có artifact type riêng, không import như signed production decisions.
Content ID ràng buộc nội dung và 5 manifest hashes; 45 field choices có IDs riêng.

Approved/applied fields 0 → 0, canonical 0, network 0. PIT/historical identity,
source priority, price basis, revision flags, research readiness và features/M2/
backtest không đổi. HNX và KPF issuer STOP tiếp tục giữ. Stage PASS ở mức lập gói;
mọi lựa chọn vẫn là MANUAL_REVIEW_REQUIRED.

Output hiện hành (V1 giữ nguyên là intermediate, V2 là bản bàn giao):

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_owner_packet26_20261102_v2\approval_review.html
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_owner_packet26_20261102_v2\owner_packet.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_owner_packet26_20261102_v2\owner_review_template.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_owner_packet26_20261102_v2\held_cases.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_owner_packet26_validation_20261102_v1\self_review.json
```

146 targeted tests (17 mới), compileall và synthetic smoke PASS. Self-review độc
lập kiểm tra 56 input/6 output/2 code hashes, 27 original raw article versions,
54 price-ratio checks, 26 SDK rows giữ nguyên, 45 blank field choices/1 HOLD và
26 HTML data rows.
Packet content ID: 01f507f1244783e38f4038990a14d370196151849f9817b60232b5c3cbfb5b0f.

Bước tiếp theo: cần owner duyệt những case/field cụ thể trong đúng gói này theo
AGENTS.md. Chỉ sau khi duyệt mới lập artifact mới cho reconciliation preview theo
lựa chọn được duyệt; chưa apply hoặc tự chuyển stage. KPF tiếp tục HOLD. Gói này
không phê duyệt PIT/identity/final canonical freeze, price-basis/Q11 methodology
hoặc backtest.

### 11.12. Gom thư mục corporate actions và chuẩn bị pilot KBS local — 03/11/2026

Theo yêu cầu mới của người dùng, gom176 file code/config/schema/test/helper/log
vào các thư mục corporate actions và giữ hardlink ở đường dẫn cũ. Hai tên file
cùng tham chiếu một file, không là hai bản dữ liệu độc lập. Tạo161 junction mới:
158 artifact directories và3 thư mục certificates/fixtures. Junction trỏ từ khu
vực corporate actions về thư mục cũ; không di chuyển raw/checkpoint/artifact đã
seal, không sửa đường dẫn trong manifest.78 top-level manifests giữ nguyên hash.

Code chạy nằm ở `scripts/corporate_actions/`, module mới ở
`src/delta_t1/ingestion/corporate_actions/`, cấu hình ở
`configs/data/corporate_actions/`. Artifact cũ được truy cập tập trung tại
`data/corporate_actions/work/legacy_tmp/`. Không xóa đường dẫn tương thích cũ.
Nguồn legacy giữ trong `legacy_sources/`; chạy entrypoint ở thư mục cha.

Đã chuẩn bị `run_kbs_events_pilot_v1.py` để người dùng tự chạy local với SDK
Vnstock5.2.1 đang có. Phạm vi sáu mã GSP,DTP,ASG,KPF,LCG,DXG, một logical SDK
call/mã, cách nhau8giây, worker tối đa480giây. Chỉ lấy rows mà route KBS trả về;
không tuyên bố đủ lịch sử2019–2025, không crawl toàn bộ1522 mã. Không gọi HNX,
không mở lại issuer KPF đangSTOP, không retry/fallback khi lỗi nguồn/access.
InputError riêng từng mã được ghi quarantine và chuyển mã tiếp theo.

Kết quả mới vào `data/corporate_actions/work/kbs_pilot_v1/`; ZIP có metadata,
query receipts và SDK exports dạng JSON matrix, không là raw HTTP hoặc bảng
canonical16trường. Null giữ nguyên; không tự điền trường thiếu, chọn nguồn hay
áp dụng45 đề xuất đang chờ duyệt. Chưa thực hiện thu thập KBS thật trong stage này.

Inventory/operation journals/verification nằm ở
`data/corporate_actions/work/layout_migration_20261103_v1/` và
`data/corporate_actions/work/layout_migration_extra_20261103_v1/`.
Validation ở `data/corporate_actions/work/layout_and_kbs_validation_20261103_v1/`.
Hướng dẫn terminal đầy đủ trong `M3/CORPORATE_ACTIONS_V1_COLLECTION_GUIDE.md`.
424 targeted tests PASS (402 cũ+22 mới), compileall vàsynthetic smoke UTF-8 PASS.
Full repository gate chưa PASS vì thiếu artifacts M2/financial PIT; lỗi loopback
sandbox được kiểm tra riêng bằng5 tests PASS ngoài sandbox, lỗi decode test cũ
được xác minh bằng targeted run UTF-8. Không sửa subsystem ngoài phạm vi.

Bước tiếp theo: người dùng chạy pilot KBS local, gửi ZIP được in ở dòng
`OUTPUT_ZIP:`. Sau đó mới kiểm tra fields/coverage và so sánh nguồn hiện tại;
không suy rằng KBS đầy đủ hơn trước khi xem kết quả thực tế.

### 11.13. Sửa native-route validation sau pilot KBS đầu tiên — 03/11/2026

Người dùng chạy pilot nhận1 logical call choGSP,0rows vàdừng
STOPPED_SOURCE_OR_ROUTE_MISMATCH. ZIP đầu giữ nguyên,CRC/6 file hashes PASS.
Source được xác địnhKBS nhưngold exporter không giữ actual route;không suy
GSP không có sự kiện lịch sử từempty SDK export.

Code ban đầu nhầm tên Python method với native route. Kiểm tra offline danh mục
SDK5.2.1 xác nhận `fundamental.company.events` cóKBS capability. Đã tách
native_route trongconfig,giữsafe observed metadata vàcollector hash. Missing/
wrong route hoặcnguồn khác vẫnSTOP;không nới source/data/PIT/identity policies.
20 targeted tests,compileall/synthetic smoke PASS,0network trongstage sửa.
Evidence ở `data/corporate_actions/work/kbs_route_fix_20261103_v1/`.

Bước tiếp theo: người dùng chạy lại cùng lệnh pilot, gửiZIP mới. Chưa bulk hoặc
build canonical;45field choices vẫnchờreview.

### 11.14. Review pilot KBS sáu mã sau sửa route — 03/11/2026

Lượt mới `delta-kbs-pilot-20261103T012745917685Z.zip` chạy đủGSP,DTP,ASG,KPF,
LCG,DXG. Cả6export đúngsourceKBS/native route,không dừng lỗi route nữa;
0rows/mã,23columns/export,0bản ghi bổ sung và0field được giải quyết. Lượt trước
1logical call/0rows; lượt sau6logical calls/0rows. Đây không làfull-history crawl:
target record dates chỉ dùng làmcontext,không truyền nhưdate filter cho SDK.

Đã kiểm traCRC,16manifest file hashes,6query/export pairs,3runtime code/config
hashes,4SDK hashes vàindependent aggregate6exports/0rows. Giữ nguyênZIP;review
0network/0code changes. Output ở
`data/corporate_actions/work/kbs_pilot_review_20261103_v1/audit.json` vàself_review.json.

SDK_EXPORTS_READY_FOR_REVIEW nghĩa làexport đã lưu,không chứng nhận dữ liệu đủ.
Chưa biết upstream trảrỗng haySDKmapping/filtering vìchưa lưu rawHTTP. Không
kết luận6mã không có sự kiện. Đề xuất tiếp: diagnostic giới hạnmột public KBS
response ởmã có known-event evidence,giữraw/filter/pagination context,trước
khi quyết định có thu thập rộnghay không. Chưa thực hiện stage tiếp trongreview.

### 11.15. Chẩn đoán trực tiếp public KBS response của DXG — 03/11/2026

Đã chuẩn bị runner và thực hiện 1 GET cho DXG, page 1/size 10/không lọc event
type, theo endpoint từ pinned public upstream SDK sources. HTTP 200/application
JSON; raw body 2 bytes `[]`. Dừng ở page 1 rỗng, không gọi page 2, retry hoặc đổi
host/header để né chặn. Không SDK login/API key, không tắt TLS hoặc theo redirect.

Baseline DXG SDK 0 rows; public request 0 rows; 0 bản ghi bổ sung/field resolutions.
Raw response xác nhận endpoint đã thử tự trả rỗng. Chưa có bằng chứng SDK làm mất
rows, chưa xác minh installed native SDK dùng exact endpoint hoặc params; không
khẳng định không có historical events ở endpoint/filter khác. Không bulk/canonical.

Code: `scripts/corporate_actions/probe_kbs_raw_dxg_v1.py`.
Current ZIP: `data/corporate_actions/work/kbs_raw_dxg_v1/delta-kbs-raw-dxg-20261103T013654039987Z-metadata-v2.zip`.
Review: `data/corporate_actions/work/kbs_raw_dxg_review_20261103_v1/`.
Endpoint source evidence: `data/corporate_actions/work/kbs_endpoint_evidence_20261103_v1/`.
ZIP metadata V2 sửa offline nhãn manifest từ SDK export sang public HTTP bytes;
ZIP đầu giữ nguyên, raw/receipts/runtime không đổi và không gọi lại KBS.
Source của lần request đã được snapshot để kiểm tra original runtime hashes.
34 targeted tests, compileall và synthetic smoke PASS; current raw ZIP CRC/7
manifest hashes, baseline 16 manifest hashes và hai upstream source hashes PASS.

Đề xuất tiếp: quay về targeted issuer/VSDC evidence và owner-review fields đang
chờ; chỉ mở stage tìm historical KBS endpoint riêng nếu có documented evidence
mới. Không tự duyệt 45 field choices hoặc chuyển stage trong công việc này.

### 11.16. Thử nguồn VNDIRECT public calendar — 03/11/2026

Theo yêu cầu kiểm tra nguồn khác, đã đọc trang lịch sự kiện công khai DXG của
DStock và hai JS bundles. Chuỗi first-party code xác nhận
`https://api-finfo.vndirect.com.vn/v4/events` với query locale/code, sort và size.
Không dùng chức năng tra cứu quyền theo tài khoản sau đăng nhập làm dataset.

Thực hiện ba API requests, mỗi request 10 rows, cho DXG/locale VN: descending
page 1, ascending page 1 và descending page 3. HTTP 200 cả ba; lưu 30 rows với 30
distinct provider IDs. API báo 68 totalElements, không có nghĩa đã tải đủ 68 hoặc
68 corporate actions cần điều chỉnh giá. Mẫu gồm listed, meeting, stock alert,
hai ISSUE và một KINDDIV; không normalize hoặc dedup thành canonical events.

Hai ISSUE rows có price 12000 và note ghi đ/cp; effectiveDate 2023-12-14/ratio
16.67 và effectiveDate 2025-01-06/ratio 20.83. Đây là provider fields, chưa apply.
30 rows có disclosureDate, chỉ chính xác theo ngày; 6 rows có status và 2 có
prevDate. Không coi effectiveDate là ex_date, registerStartDate là record_date
hoặc tỷ lệ làm tròn là exact fraction. Oldest query result là 2021-11-10; chưa
có full-history coverage 2019–2025. Không thay PIT/identity/source priority hoặc
45 field choices.

Output: `data/corporate_actions/work/vndirect_probe_20261103_v1/` gồm original
HTTP bodies, receipts, audit.json, self_review.json vàmanifest. Trước stage có
0 sample VNDIRECT rows; sau có 30 sample rows/1 ticker/0 canonical fields applied.
Không sửa production code/pipeline; kiểm tra HTTP/JSON/filter/pagination, hashes,
first-party endpoint source và independent aggregate. Không cần full test rerun
cho read-only pilot; các artifact nguồn cũ giữ nguyên.

Đề xuất tiếp: scoped pilot GSP,DTP,ASG,KPF,LCG,DXG để đối chiếu known events với
primary evidence. Chỉ sau source/semantics/coverage review mới đề xuất bulk.
Chưa chạy pilot 6 mã trong stage này.

### 11.17. Chuẩn bị thử HNX local sau Kaggle — chưa gửi request

User yêu cầu kiểm tra local terminal. Đã xác định baseline HLA/UPCOM từng nhận
HTTP403 trên Kaggle và chuẩn bị diagnostic một mã, profile GET rồi disclosure
POST page1/20 rows, tối đa2 requests, cách nhau8 giây, timeout15 giây; strict TLS,
không retry/redirect/alternate host/header/IP/account và không resume state cũ.
C8v2 scope và dry-run PASS; payload POST khớp receipt Kaggle ban đầu.

Automatic approval review từ chối network action vì HNX đang global STOP sau
access-boundary failures. Lệnh chưa được chạy:0 HTTP requests mới, chưa có dữ
liệu local để so sánh. Không đưa lệnh thay thế hoặc thao tác gián tiếp để né
review. Raw/checkpoint/incident artifacts cũ giữ nguyên, không đổi resumable.

Kế hoạch và self-review offline:
`data/corporate_actions/work/hnx_local_recheck_plan_20261103_v1/`.
Bước tiếp theo cần explicit exception cho diagnostic giới hạn này rồi xét duyệt
lại; không tự cho phép bulk/resume hoặc thay methodology. Không sửa production
code, không cần rerun compileall/full suite cho bước chuẩn bị read-only này.

### 11.18. HNX local recheck theo ngoại lệ được user duyệt — 03/11/2026

User đã xác nhận rõ cho phép thử HNX local một lần, tối đa2 requests; gặp lỗi
truy cập thì dừng. Xét duyệt lại được chấp nhận. Không thay global recovery
policy hoặc các resumable flags cũ.

HLA/UPCOM: profile GET vàdisclosure POST page1/20 rows đều HTTP200, request-start
gap8.013069 giây. POST URL/body trùng failed HLA request trên Kaggle trước đây.
Không có SSL verification error,403 hoặcconnection reset trong hai request này.
TLS validated intermediate cũ, CERT_REQUIRED/hostname check vàflags giữ nguyên.

Kết quả queryrỗng:0article IDs,0detail requests,0bản ghi/field canonical được thêm.
So sánh truy cậpHLA:Kaggle403→local200 tại thời điểm thử. Chưa có bằng chứng
causal rằng Kaggle gây lỗi vàchưa chứng minh truy cập ổn định ở tải lớn. Empty
query cũngkhông chứng minh lịch sử không có sự kiện.

Output: `data/corporate_actions/work/hnx_local_recheck_20261103_v1/`.
Đã kiểm tra raw/manifest hashes,prior request equality,C8v2scope,delay,TLS,
2requests đúngngân sách vàincidentartifact giữ nguyên. Không sửa production code,
không cần compileall/full test rerun cho acquisition review bằng code cũ.
Ngoại lệ một lần đãdùng đủ2requests;không thực hiện stage khác.

Bước tiếp đề xuất: một pilot riêng với mã cóknown-event evidence vàdetail page,
trước khi quyết định cóphục hồi thu thập trênlocal haykhông.

### 11.19. Chuẩn bị PVS pilot để user tự chạy terminal — 03/11/2026

User muốnknown-event pilot tiếp theo vàưu tiên tựchạy nếuagent còn dùngusage.
Đã chuẩn bị một CLI khônggọiOpenAI,không liveHNXrequest trongstage này. HLA0
chỉ làqueryempty,không historicalno-event certificate. PVS dùng window ngàyđăng
2024-10-01–2024-11-30 quanhknownsample,max3requests/profile+list+một detail.

Runner `scripts/corporate_actions/probe_hnx_pvs_local_v1.py` dùng sharedbudget
8giây/15giây timeout/120giây tổng;strictTLS,noretry/redirect/sourcefallback hoặc
resumeshard. Detail phải được observed trongsealedlist;parsercũ chạyoffline
reviewonly,không applycanonical/PIT/identity/readiness. ZIP cảkhiSTOPPED/PARTIAL.

41targeted tests (7mới),compileall/synthetic smoke vàoffline CLIcheck PASS;
0livePVSrequests,0newrealobservations/approvedfields. Evidence:
`data/corporate_actions/work/hnx_pvs_local_pilot_preparation_20261103_v1/`.
Output userrun sẽở `data/corporate_actions/work/hnx_pvs_local_pilot_v1/`.
Bước tiếp: user chạy mộtlệnh trongcollectionguide,gửiZIP rồi mớireview;không
agent continuouslypoll hoặc tựchạy sourcejob vìuser đãchọn tựrun đểtiếtkiệm.

### 11.20. Review PVS local pilot do user chạy — 03/11/2026

ZIP `delta-hnx-pvs-local-20261103T021025418311Z.zip` có đủ3requests, tất cảHTTP200:
profileGET,listPOST vàdetailPOST. Một bài537190 đượcdiscover vàtải thànhcông;
offlineparser tạo1reviewobservation,khôngerror/rejection. Nội dunggốc xácnhận
cashdividend700VND/CP,ex13/11/2024,record14/11/2024,payment17/12/2024 vàtickerPVS.
List clock hiểnthị06/11/2024 15:40. Đây làknown sample đượctải mới,không khẳngđịnh
thêm1uniqueevent vào dataset.

Hai review rows làSOURCE_PUBLIC_TIME_UNVERIFIED vàHISTORICAL_IDENTITY_NOT_CERTIFIED.
Cóhour/minute không đồngnghĩa đãverify initialpublication semantics/timezone.
Không đổiPIT/identity/sourcepriority hoặcapplycanonical;khôngcộng/táiđầutưcash
dividend vào bấtkỳpriceseries nào. Extractiongate chỉPASS choarticleđầu vào,
khôngbulkready hoặcfullhistorycoverage.

Đã kiểmtraCRC,28parent+18nested hashes,3runtime hashes,5raw quotes,list/detailID
vàtitlejoin,TLS strict,cácrequeststatus/counts. Configdelay8giây;walltimestamp
gaps8.005746/7.999404giây đượcghi nguyênvẹn,không thaythếmonotonic delay measurement.
Review0network/0codechanges,giữZIPcũ;khôngcầnreruncompileall/fullsuite.
Output `data/corporate_actions/work/hnx_pvs_local_pilot_review_20261103_v1/`.

Bước tiếp đềxuất:pilotgiới hạnUPCOM vàmột rights-issue/stock-dividend article để
kiểmtra kiểu sựkiện khác trướckhiđềxuất localbatch. Chưa tựthực hiện tiếp.

### 11.21. Chuẩn bị ACV/UPCOM và noncash pilot — 03/11/2026

User yêu cầu tiếp tục sau PVS. Giữ cách user tự chạy terminal để tránh agent
theo dõi crawl. Cache discovery đã kiểm tra hash có bài573433/ACV/UPCOM, đăng
30/07/2025 16:59, về cổ tức cổ phiếu. Một ACV pilot đáp ứng cả UPCOM và noncash
action; chưa gọi nguồn hoặc thu thập nhiều mã trong stage này.

Runner `scripts/corporate_actions/probe_hnx_acv_local_v1.py` dùng chung pipeline
cũ với hai whitelist profiles. ACV fixed window ngày đăng2025-07–08, một page,
chỉ known article573433 freshly observed; không gọi detail bằng ID cache nếu
fresh list thiếu nó. Shared cap3 requests,delay8giây,timeout15giây/run120giây,
TLS/source-stop giữ nguyên. Parser phải nhận STOCK_DIVIDEND; thiếu ngày optional
không tự điền, không canonical/PIT/identity approval hoặc resume state cũ.

47 targeted tests (6 mới),compileall/synthetic smoke vàCLIcheck PASS; tests PVS
cũ giữ nguyên. Source PVS trước sửa được snapshot và kiểm tra với runtime hash
trong ZIP PVS; raw/ZIP cũ không sửa.0live HNX requests/0new real observations.
Preparation: `data/corporate_actions/work/hnx_acv_local_pilot_preparation_20261103_v1/`.
Output user-run: `data/corporate_actions/work/hnx_acv_local_pilot_v1/`.
Bước tiếp: user chạy một lệnh trong collection guide, gửi ZIP để review. Chưa
thực hiện live acquisition, chưa chuyển sang bulk.

### 11.22. Review ACV local UPCOM/cổ tức cổ phiếu — 03/11/2026

User đã chạyACV,ZIP20261103T022050948509Z. Cả3requests HTTP200;freshlist tìm đúng
bài573433,detail tải được vàparser tạo1STOCK_DIVIDEND observation. Raw có
OLD:NEW100:64,58 kèmexplicitallocation wording;ratio0.6458,ex07/08/2025,
record08/08/2025,listclock30/07/2025 16:59. Fields khớp knownsample cũ;không
khẳngđịnh thêmuniqueevent vào dataset hoặcapplycanonical.

Hai metadataREVIEW giữ nguyên nhưPVS:source clock semantics/timezone vàhistorical
identity. Dòng thứba làpayment_date missing,severityINFO,vìnguồnkhôngghi ngày
thanh toán/phân bổ. Không đoánngày từrecord/exdate. ExtractiongatePASS chỉcho
article đầu vào;PIT/identity/readiness/canonical chưa được promote.

CRC,28parent+18nested hashes,3runtime hashes,5raw quotes,scope/articlejoin,TLS,
requestcounts/status vàindependent observations PASS. Rawwall gaps8.000698 và
8.009543giây,config8s. Review0network/0productioncodechanges/0field approvals.
Output: `data/corporate_actions/work/hnx_acv_local_pilot_review_20261103_v1/`.

Đề xuất tiếp: bounded supplemental local batch khoảng10mã cònthiếu,giữ checkpoint,
delay vàglobalstop sauaccessfailure. Chưa mởbatch hoặc tựresume cácshard cũ;
PVS/ACV positive pilot không chứng minhbulk uptime/fullhistory.

### 11.23. Review bounded HNX local supplement — PARTIAL/read timeout 03/11/2026

Đã review ZIP user chạy `delta-hnx-local-supplement10-20261103T025523779036Z.zip`.
15 request attempts gồm14 complete HTTP200 responses vàVTZ profile GET nhận200
headers nhưng read timeout trước khi lưu complete body/hash. Không thấy401/403/
429, không xác định nguyên nhânIP/concurrency. Job dừng đúng contract; checkpoint
`resumable=false`, `inflight=VTZ:discovery` giữ nguyên, không retry/resume.

| Đơn vị | Kết quả lượt này |
|---|---:|
| Mã planned / attempted / finished bounded scope | 10 / 6 / 5 |
| Discovery distinct articles / title candidates | 10 / 5 |
| Detail articles / preview observations | 4 / 4 |
| Articles extraction PASS / REVIEW_REQUIRED | 2 / 2 |
| Review rows: REVIEW / INFO | 12 / 2 |
| Canonical fields approved / applied | 0 / 0 |

VE3/IDJ chỉ có meeting/consent titles; RGG query rỗng, không chứng minh historical
absence. TNG/MBS mỗi mã hai details. HKT/PGN/TIG/VEF chưa attempt. Selected25 field
tasks vẫn pending; queue602 payloads/1.373 field tasks không tự giảm từ observations.

Raw MBS581051 chứa bonus100:03, rights100:12, primary price10.000đồng/CP; ex24/09 và
record25/09/2025 cùng rights ratio0.12 khớp selected SDK row theo date view+07.
Parser ghiOTHER/MIXED_OR_UNKNOWN_EVENT_TYPE nên raw price candidate giữ review,
chưa automatic field/event linking/approval. TNG523090 có100:8 với explicit allocation
wording, parser giữRATIO_PARSE_AMBIGUITY; raw stock dividend8% không khớp selected
rights payload10%. Hai cash articles TNG497771/MBS575367 parse400/1.200VND/CP,
không phải hai field resolutions cho selected rights-price needs.

CRC,164 local/ZIP file equality,163 parent hashes,15 nested manifests/93 hashes,
16 runtime hashes,14 complete raw hashes,12 field quotes và4 component quotes PASS.
Replay offline bốn articles khớp observations/results/review queues; strictTLS,
monotonic gaps8.000–8.016s. Review0network/0production code changes/0canonical.
Original ZIP/checkpoint vàPIT/identity flags giữ nguyên;45 owner choices chưa duyệt.

Output `data/corporate_actions/work/hnx_local_supplement10_review_20261103_v1/`.
Status PARTIAL về acquisition/extraction, safety gate PASS. Đề xuất stage riêng
tiếp theo là offline component/ratio parser review từcache; chưa thực hiện.
Không tự mở thêm acquisition hoặc resume các mã còn lại.

### 11.24. Khắc phục HNX parser trên cached raw — 03/11/2026

User yêu cầu xác định nguyên nhân/khắc phục. Đã tái hiện hai code defects:
TNG523090 explicit “được nhận thêm08” không khớp legacy allocation regex;
MBS581051 cóbonus+rights nhưng legacy parser chỉ nhận single event type nênOTHER.
Đã thêm version opt-in components-v2 vàoffline runner/config riêng, giữterms parser
dùng chung/legacy default. Không gọi nguồn hoặc thay source acquisition policy.

TNG lấy được stock_dividend_ratio0.08. MBS tách hai explicitstarheading blocks,
BONUS_SHARE0.03 vàRIGHTS_ISSUE0.12/price10.000VND/share. Không borrow terms giữa
components; unknown/duplicate/conflicting heading vẫnfail-closed. Giữ rawtext
spans/providerarticleID/receipts/hash/originalobserved_at/revision/PIT/identity flags.

| Số liệu | Trước | Sau |
|---|---:|---:|
| Cached detail articles | 4 | 4 |
| Source/component observations | 4 | 5 |
| Articles extraction PASS | 2 | 4 |
| Review rows | 14 | 13 (10REVIEW/3INFO) |
| Selected field tasks chưa approved | 25 | 25 |
| Canonical fields applied | 0 | 0 |

Hai cash articles giữfields/IDs; legacy replay khớp byte observations/reviews cũ.
TNGstock8% không phải selectedrights10%; MBSrightsprice vẫncandidate chưaapprove.
45ownerchoices vàPIT/identity/source-selection/finalfreeze giữMANUAL_REVIEW_REQUIRED.

VTZ xác định lỗi nằm ởbodyread sauHTTP200 headers,timeout15s; externalcause chưa
đủevidence. Không khẳngđịnh lỗiKaggle/IP/concurrency hoặcTLS; không tăngtimeout,
retry/đổihost hoặcresumecheckpointSTOP. Bốn mã chưaattempt tiếp tục chưachạy.
Sourcehashes thay đổi nênoldpreparation runtime pins stale,khôngchỉnhartifact cũ.

Output `data/corporate_actions/work/hnx_cached_parser_remediation_20261103_v1/`
có source-before snapshots, legacy replay, v2 outputs, diagnosis và validation.
124 targeted tests (11 mới), compileall, synthetic smoke và self-review PASS.
Stage PASS về offline parser remediation/PARTIAL về external network diagnosis;
0 network requests. Giữ toàn bộ assertions cũ và checkpoint STOP.

### 11.25. Review năm HNX components với SDK/missing queue — 03/11/2026

Đã pin/verify cached inputs và 84 SDK exports; chỉ đọc 56 distinct MBS/TNG payloads,
67 occurrences. Cả 5 source components có unique counterpart candidate theo existing
category/date_view/term_agreement, cả hai dates cùng economic terms; không nearest
date hoặc giờ publication để chọn/approve event. Không có historical identity/PIT claim.

TNG523090 STOCK 8% khớp payload 55fca741…907c69: ex 12/07/2024, record 15/07/2024 đã
có trong SDK, ngoài missing queue. Selected TNG RIGHTS 10% vẫn thiếu ba fields. MBS581051
BONUS 3% và hai CASH observations cũng khớp payloads ngoài queue, chỉ corroboration.
MBS RIGHTS 12% khớp payload 9b834acc…6e89a với ex 24/09/2025/record 25/09/2025;
raw primary quote “Giá phát hành: 10.000 đồng/cổ phiếu” hỗ trợ một unsigned price choice.
Kèm conditions owner xác nhận exact component/both dates/unit/revision/competing evidence;
chưa ký/approve/apply hoặc merge vào 45 choices cũ.

| Đơn vị | Trước | Sau |
|---|---:|---:|
| Missing queue payloads | 602 | 602 |
| Missing field tasks chưa approve/apply | 1.373 | 1.373 |
| Scoped tasks có evidence mới chờ owner | 0 | 1 |
| Selected 25 tasks có evidence mới / chưa có matching evidence từ lượt này | 0 / 25 | 1 / 24 |
| Old owner choices | 45 | 45 |
| New unsigned price choices riêng | 0 | 1 |
| Approved/applied/canonical fields | 0 | 0 |

Queue version mới append review metadata, giữ mọi original columns và missing_fields;
1.372 tasks chưa có matching evidence từ năm components không có nghĩa cache cũ không
chứa evidence. Không áp giá/cổ tức vào M2/features/adjustment/backtest. VTZ STOP và
immutable ZIP/checkpoint giữ nguyên; 0 network requests.

Output `data/corporate_actions/work/hnx_component_queue_review_20261103_v1/`,
validation/self-review `data/corporate_actions/work/hnx_component_queue_review_validation_20261103_v1/`.
74 targeted tests (12 mới), compileall, synthetic smoke và self-review PASS.
Stage technical PASS/MANUAL_REVIEW_REQUIRED về field choices. Bước tiếp: owner review
riêng một MBS price choice; diagnostic VTZ nếu được giao phải scope/approve riêng.

### 11.26. Rà cache sửa đổi đợt MBS 25/09/2025 — giữ chờ 03/11/2026

Đã rà 20 VSDC documents từ query MBS, exact HNX list 3 articles/hai detail bodies và bốn
cumulative ZIP cũ, không network. Chưa thấy linked revision/cancellation hoặc giá
đối nghịch liên quan trong phần đã rà; không suy điều đó thành “không có sửa đổi”.

VSDC raw search ghi “Hiển thị: 1 - 20 / 63 bản ghi”, oldest date hint 24/10/2025 sau
record 25/09/2025. 43 query rows chưa có trong snapshot trang đầu; không gọi 43 events.
20 docs gồm 4 cổ phiếu MBS và 16 security khác (chủ yếu trái phiếu MBS...). VSDC193811
record 03/04/2026/ratio 2:1 là đợt khác dù cũng giá 10.000 VND/CP. HNX chỉ có CORPORATE_NEWS
26/05–31/12/2025 và một meeting title chưa detail, không certify full archive/issuer history.

Giá 10.000 VND/share trong HNX581051 vẫn raw-supported, nhưng recommendation
HOLD_CACHE_COVERAGE_GAP/ready_to_recommend_owner_price_approval=false. Không gỡ
điều kiện revision review, không sửa/approve/apply proposal hoặc queue. Hai loại câu
“huỷ cổ phiếu lẻ”/“ngày hiệu lực huỷ mã quyền mua” được phân biệt với huỷ cả đợt.

Output `data/corporate_actions/work/mbs_revision_cache_review_20261103_v2/`,
HTML `ket_luan_ra_cache_MBS.html`; validation/self-review ở
`data/corporate_actions/work/mbs_revision_cache_validation_20261103_v1/`.
73 targeted tests (11 mới), compileall, synthetic smoke và self-review PASS.
Giữ immutable inputs/45 owner choices/VTZ STOP. Bước tiếp đề xuất: chuẩn bị bounded
VSDC pilot user-run riêng cho MBS quanh 25/09/2025 để bổ sung phần history còn thiếu;
chưa chuẩn bị/chạy tiếp trong stage này.

### 11.27. Kiểm kê VSDC phân trang toàn C8 — 03/11/2026

User yêu cầu xác định code/config và phạm vi thu thiếu. Đã audit offline 1.529 raw search
snapshots/1.522 C8 queries, giữ mọi old raw/receipts/processed states. Kết quả query latest:

| Query status | Số mã |
|---|---:|
| List chưa đọc hết | 1.104 |
| List exhausted trong snapshot, chưa history certified | 414 |
| Blank/unverified: DTR, KAI, LPS, PCB | 4 |

Affected gồm 486 UPCOM/357 HOSE/261 HNX. Known list URLs đều đã có raw trong cache, 27.730
distinct provider article IDs giữ nguyên. Tổng 52.819 unseen query row slots không là distinct
events/new requests: có trùng query, trái phiếu, họp, ngoài kỳ và identity chưa certified.

Root cause đã trace: bốn HTTP 400 POST page 2 (A32/AAA/AAM/SSI), mỗi receipt lặp 3 parent/
child/replay ledgers, không phải 12 requests. Persistent deferred_post_hosts của bootstrap/
4 shards chặn POST pagination sau đó; cả 1.104 incomplete queries có guard check evidence.
MBS plan max_pages 20/max_details 100 nên không do 20 detail cap. Saved inline JS dùng POST
cùng URL/query và JSON SearchKey/CurrentPage; empty 400 body chưa chứng minh server cause
hoặc corrected protocol đã live PASS. Không gỡ guard/retry/đổi headers/IP trong audit.

Stage xuất all query reviews, full affected continuation inventory và HTML dễ đọc ở
`data/corporate_actions/work/vsdc_pagination_scope_audit_20261103_v2/`.
V2 reuse verified V1 reads và normalize diagnostic suffix, không recompute expensive cache.
Validation/self-review `data/corporate_actions/work/vsdc_pagination_scope_validation_20261103_v3/`.
62 targeted tests (8 mới), compileall, synthetic smoke và self-review PASS.
Không network/approval/application/canonical; old states/45 choices/PIT/identity giữ nguyên.
Bước tiếp đề xuất: chuẩn bị bounded MBS user-run pagination pilot; sau pilot mới lập budget/
plan bổ sung toàn bộ affected queries, chỉ fetch missing details sau ID/hash dedup và scope.
Chưa mở pilot/bulk trong stage audit này.

### 11.28. Chuẩn bị VSDC MBS pagination pilot cho user chạy — 03/11/2026

Đã viết runner/config/preparation riêng, không source requests. Tối đa 2 requests:
fresh GET MBS/page 1 để xác minh query echo/public inline JS, sau đó một POST page 2 cùng
URL/query với compact JSON SearchKey 4/CurrentPage 2 và charset như first-party JS.
Không cookie/auth/đổi User-Agent/host/IP, không gỡ old deferred guard. Chưa claim đã
fix nguyên nhân HTTP 400; cần ZIP user-run để xác minh live profile này.

Một worker/shared 8s/timeout 15s/cap 2MB/run budget 90s; checkpoint mỗi request và final,
ZIP full/partial, luôn resumable=false. HTTP error kể cả 400/access/TLS/timeout/challenge/
Retry-After/layout mismatch dừng toàn pilot. Page 2 phải đúng range/total và IDs không trùng
fresh page 1; không mở page 3/4 hoặc article details. Sáu old states được hash-protect trước
request và cuối run; bootstrap/4 shards VSDC deferred và HNX VTZ STOP giữ nguyên.

Archived baseline MBS 20/63 query rows giữ nguyên; freeze 27.730 cached provider IDs để
đánh dấu reuse nếu nhận page 2, không coi IDs là canonical events. Preparation ở
`data/corporate_actions/work/vsdc_mbs_pagination_preparation_20261103_v1/`,
validation `data/corporate_actions/work/vsdc_mbs_pagination_validation_20261103_v1/`.
74 targeted tests (12 mới)/compileall/synthetic smoke/CLI check/self-review PASS.
0 live/observations/approved/applied/canonical; 45 choices/PIT/identity không đổi.

Lệnh PowerShell và ZIP path tại đầu collection guide. User chạy một lần, gửi OUTPUT_ZIP
kể cả partial; fresh rerun bị chặn để chờ review, không force-resume. Agent dừng sau prep,
không acquisition/polling. Bước tiếp đề xuất: offline review ZIP, sau pilot PASS mới chuẩn
bị batch budget/scope cho affected queries; pilot không tự mở bulk 1.104 queries.

### 11.29. Review pilot live VSDC MBS — 03/11/2026

User đã chạy `run-20261103T043616143951Z`: GET trang 1 HTTP 200, 20/63 rows;
POST trang 2 HTTP 400, body 0 bytes. Public JS contract giữ nguyên, payload đúng
compact JSON/charset đã freeze, hai request cách nhau 8 giây theo monotonic timing.
Không retry/detail fetch/observation/canonical update. Không kết luận server cause
hoặc gọi 43 unseen query row slots là missing events.

Review offline ZIP PASS CRC, 23 unique members khớp state, 22 payload hashes,
raw/receipt/log agreement, runtime/config/preparation provenance, fresh MBS reparse,
sáu old state hashes và old owner packet. Evidence:
`data/corporate_actions/work/vsdc_mbs_pagination_live_review_20261103_v1/`.
Self-review PASS stage review; acquisition trang 2 FAIL, bulk 1.104 queries BLOCKED.
Agent không gọi network và không sửa old evidence hoặc acquisition code.

Bước tiếp đề xuất: một kiểm tra trang 2 trên UI public trong browser thông thường.
Nếu UI thành công, đối chiếu request context trước khi thiết kế pilot mới; nếu UI
cũng lỗi, giữ STOP và xem xét hỗ trợ từ nguồn/evidence thay thế được chấp nhận.
Không tự rerun, đổi profile hoặc vượt access control. Dừng tại review stage.

### 11.30. User báo UI VSDC MBS chuyển được trang 2 — 03/11/2026

User phản hồi “21–40 / 63 bản ghi”. Lưu đúng mức user-reported UI observation;
agent chưa có screenshot/raw/network capture trang 2 và không suy browser HTTP status.
Đối chiếu offline source JS với collector cho thấy URL/payload/Content-Type theo
contract đã lưu; chưa đủ evidence để quy lỗi cookie/header/token/session/User-Agent.
Collector run trước vẫn HTTP 400; không suy website pagination lỗi phổ quát.

Evidence: `data/corporate_actions/work/vsdc_mbs_browser_manual_observation_20261103_v1/`.
Self-review PASS stage ghi nhận manual result; 0 requests từ agent, 0 code/canonical
changes; old evidence/guards giữ nguyên. Bulk 1.104 queries chưa được mở.
Bước tiếp đề xuất: capture metadata tối thiểu của một successful browser page2
request để đối chiếu, loại mọi cookie/token/auth values, không full HAR hoặc replay.
Dừng tại stage ghi nhận, không tự thiết kế/chạy pilot khác.

### 11.31. Chuẩn bị đối chiếu request; browser capture bị chặn — 03/11/2026

User giao capture request thành công. `cua.getTab` trả “Local browser use is disabled
in Work settings”. Không có capture hoặc HTTP status/headers mới; stage comparison
BLOCKED, không thử công cụ browser khác để vượt hạn chế. Chuẩn bị baseline collector
đã verify và template null được đánh dấu UNFILLED/NOT_EVIDENCE:
`data/corporate_actions/work/vsdc_mbs_request_comparison_preparation_20261103_v1/`.
Hướng dẫn thao tác Network metadata tối thiểu nằm đầu collection guide; không yêu cầu
full HAR/Copy as cURL hoặc cookie/token/auth values. Không replay/đổi request.
Self-review PASS preparation only; 0 requests từ agent, 0 collector/canonical changes,
old guards/evidence nguyên vẹn. Bước còn thiếu: successful browser request metadata;
chưa thiết kế hoặc chạy pilot mới và chưa mở batch bổ sung.

### 11.32. Đối chiếu metadata POST 200 user gửi — 03/11/2026

User chép DevTools: URL MBS/POST/200 OK, JSON SearchKey 4/CurrentPage 2. URL, method
và payload semantics khớp sealed collector POST 400. Content-Type text/html user
cung cấp chưa xác định thuộc request/response; giữ unknown, không đổi JSON request.
Chưa có raw browser capture, request headers hoặc causal diagnosis.
Evidence: `data/corporate_actions/work/vsdc_mbs_request_metadata_comparison_20261103_v1/`.
Self-review PASS mức evidence có sẵn, comparison PARTIAL chờ Request Headers
Content-Type/X-Requested-With. 0 agent requests, 0 code/canonical changes, old guards
và evidence nguyên vẹn. Chưa chuẩn bị/chạy pilot mới hoặc mở batch bổ sung.

### 11.33. Request header comparison hoàn tất — 03/11/2026

User xác nhận Request Headers JSON UTF-8 và X-Requested-With XMLHttpRequest.
Offline injected-opener interception frozen PublicTransport: không có X-Requested-With,
0 network; URL/POST/payload/parsed content type khớp. Status browser 200 là user report,
collector 400 có sealed receipts. Không có raw successful browser capture; không
đánh đồng observed header difference với proven cause hoặc fix.
Evidence: `data/corporate_actions/work/vsdc_mbs_request_metadata_comparison_20261103_v2/`.
Self-review PASS comparison stage only, old evidence/runtime/guards/canonical nguyên
vẹn, chưa tạo V2 hoặc mở bulk. Bước tiếp đề xuất: chuẩn bị separately versioned MBS
2-request diagnostic, chỉ thêm observed functional AJAX header vào POST, giữ toàn bộ
budgets/UA/TLS/STOP, không cookie/auth/retry/details. Live validation gate còn thiếu.

### 11.34. Chuẩn bị pilot VSDC MBS V2 — 03/11/2026

User giao thực hiện V2 preparation. Module/config/CLI/output riêng để giữ frozen V1
runtime/artifacts bất biến; reuse V1 parsers và 27.730 cached provider IDs. Chỉ thêm
observed functional X-Requested-With XMLHttpRequest vào page2 POST, dựa trên user-
transcribed DevTools headers. GET/URL/JSON/body/UA/Accept và budgets giữ nguyên;
không cookie/auth/header rotation, không gọi nguồn thật trong phiên chuẩn bị.

Fixed opener kiểm tra scope/method/sequence/header allowlist/body trước network;
record construction trước urllib handlers. max2requests/90s/interval8s/timeout15s/2MB,
strict TLS/NoRedirect, mọi source/layout lỗi STOP, không retry/details/resume/bulk.
49 old files và pinned parent manifests được bảo vệ. ZIP full/partial có raw/receipts/
construction/provenance/runtime/TLS/checkpoints; actual run bất kỳ chặn rerun.

Preparation `data/corporate_actions/work/vsdc_mbs_pagination_preparation_20261103_v2/`;
validation `data/corporate_actions/work/vsdc_mbs_pagination_validation_20261103_v2/`.
90 targeted tests (16 V2, giữ V1 assertions), compileall/synthetic smoke/CLI check PASS.
Self-review chỉ đánh giá preparation; live fix/causal diagnosis chưa chứng minh.
0 source requests/new observations/canonical/approvals/PIT/identity changes.

Bước tiếp: user chạy lệnh V2 một lần đầu collection guide, gửi OUTPUT_ZIP kể cả lỗi.
Review offline raw/layout/range/total/IDs/header construction trước mọi plan bổ sung
1.104 queries. Dừng tại preparation; không tự chạy V2 hoặc mở bulk.

### 11.35. Review live VSDC MBS V2 — 03/11/2026

User chạy `run-20261103T050150450791Z`. GET200/page1 20/63 rows; POST400/body rỗng.
Construction trước urllib handlers xác nhận chỉ POST có X-Requested-With XMLHttpRequest;
UA/Accept/URL/JSON/body giữ nguyên. Hai requests cách nhau 8s, không retry/details.
Thêm riêng header chưa đủ sửa lỗi; không suy proven server cause hoặc header vô can.

Review PASS CRC, 25 ZIP members khớp state, 24 payload hashes, runtime/plan/parent
provenance, raw/receipt/ledger/construction, fresh page1 reparse và 49 protected old
files. 16 regression tests/compileall PASS. Evidence:
`data/corporate_actions/work/vsdc_mbs_pagination_live_review_20261103_v2/`;
validation `data/corporate_actions/work/vsdc_mbs_pagination_live_review_validation_20261103_v2/`.
Self-review PASS review stage, pagination FAIL/bulk BLOCKED. Agent 0 source requests,
0 code/canonical/approval changes; V1/V2 và old guards bất biến.

Bước tiếp đề xuất: chuẩn bị bounded MBS browser-UI pilot, bấm nút phân trang thông
thường và lưu rendered page2 list/minimal metadata. Cần reviewable browser access
hoặc user-run capture path; không guessed profiles/direct POST retry/auth/challenge
bypass. Chưa tạo/chạy pilot mới, không mở bulk 1.104 queries. Dừng tại review stage.

### 11.36. Chuẩn bị pilot public browser-rendered HTML MBS — 03/11/2026

User giao bước tiếp và hỏi đọc thẻ HTML. Đã chuẩn bị runner local mở fresh Chrome,
navigation query MBS và bấm observed page2 button; đọc outerHTML #divGlSearchArticles,
parse links/title/IDs/range/total bằng V1 parser. Không replay POST/invoke AJAX JS;
không custom UA/headers/cookie/profile/auth hoặc TLS bypass. Browser session first-
party tự tạo chỉ ephemeral; không import/export/persist. Artifacts V1/V2 nguyên vẹn.

Budget riêng cho browser: 2 business requests + tối đa78 asset/blocked external
attempts, tổng80 context attempts, business interval8s/operation15s/run90s/HTML2MB.
Static first-party allowlist, external resource block; mọi unknown business/detail/
redirect/HTTP/challenge/TLS/transport/layout/budget lỗi STOP. Không retry/resume/login.
ZIP giữ public rendered fragments + HTTP hash/size không body, metadata/ledger/
runtime/provenance; không coi fragment là raw HTTP. Không export cookie/token/HAR.

Preparation `data/corporate_actions/work/vsdc_mbs_browser_html_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_mbs_browser_html_validation_20261103_v1/`.
Protect87 old files, reuse27.730 cached IDs. 106 targeted tests (16 browser HTML),
compileall/synthetic smoke/CLI check PASS; Playwright1.57/Chrome executable found
offline. 0 browser launches/VSDC requests/new observations/canonical/promotions.
Self-review chỉ PASS preparation, không chứng nhận live browser/layout hoặc cause400.

Bước tiếp: user chạy một lần lệnh đầu collection guide, gửi OUTPUT_ZIP cả lỗi;
agent review offline pair fragments/range/total/nonoverlap/network scope trước plan
bổ sung. Chưa mở bulk1.104 queries/approve MBS price hoặc chứng nhận history/PIT.
Dừng tại preparation, không agent browser acquisition hoặc next-stage execution.

### 11.37. Review live browser HTML MBS — PASS page2,03/11/2026

User chạy `run-20261103T052324145483Z`. Browser GET/POST đều200; exact public
rendered fragments parse ranges1–20/21–40 cùng total63,40 distinct provider IDs.
Page2 có20 IDs mới so với audited cache27.730, không verified new events/details.
Candidate187243 title hints BONUS_SHARE/RIGHTS_ISSUE, list timestamp17/09/2025
14:11:04; chưa detail/record date/terms/price/revisions, không approve giá10000.

Review PASS ZIP CRC/20 unique members khớp state/19 payload hashes/runtime/parents/
87 protected files, safe metadata/ledger/checkpoint. 55 context attempts =2 business
+53 assets/external,54 admissions,1 external block; starts cách8.094s. POST header
names có __vptoken/cookie/origin/referer, không values, không isolated cause400.
HTTP bodies chỉ hash/size, không raw archived; không độc lập rehash body từ ZIP.
16 regression tests/compileall PASS; agent0 new source requests/browser launches/
code/canonical/approval changes. Self-review PASS review stage, full/bulk gates đóng.

Evidence `data/corporate_actions/work/vsdc_mbs_browser_html_live_review_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_mbs_browser_html_live_review_validation_20261103_v1/`.
Bước tiếp đề xuất: chuẩn bị bounded MBS full4-page session + candidate187243 detail,
preserve prior40 links và reuse cached bodies, không trộn list snapshots thành claim
fresh full query. Review exact event/date/price/revisions trước owner choice; chưa mở
bulk1104. Chưa chuẩn bị/chạy supplement trong stage review; dừng tại đây.

### 11.38. Chuẩn bị bounded MBS full-query + detail187243 — 03/11/2026

User giao preparation lượt tiếp. Module/config/CLI/output riêng, reuse old browser
driver nhưng giữ nguồn/artifacts cũ bất biến. Tối đa4 list pages trong cùng fresh
session, stable total/ranges/unique IDs; chỉ exact detail187243 sau query exhaustion,
candidate presence và not-in-cache gate. Prior40 links preserve, không trộn snapshots
thành full fresh list. Detail public title/content/time nodes + text preview giữ nguyên
label, không auto-approve record date/price10000/PIT/revisions/canonical.

Contract max5 business/160 context attempts/155 assets, shared8s/operation15s/run150s/
HTML2MB; default ephemeral browser session, no import/export auth/profile/cookie,
no custom headers/UA/TLS bypass. Mọi HTTP/access/redirect/challenge/Retry-After/TLS/
transport/layout/budget lỗi STOP; no retry/resume/fallback/details khác/attachment fetch.
Pin parents/protect120 old files; reuse27.730 cached provider IDs. ZIP full/partial
giữ rendered public fragments/receipts/logs/runtime/provenance/checkpoint nonresumable.

Preparation `data/corporate_actions/work/vsdc_mbs_browser_supplement_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_mbs_browser_supplement_validation_20261103_v1/`.
125 targeted tests (19 supplement), compileall/synthetic smoke/CLI check PASS. Self-
review chỉ preparation,0 new browser launches/source requests/observations/canonical/
approvals/PIT/identity. Live full-query/detail và terms còn chờ user-run/offline review.
Bước tiếp: user chạy đúng một lần lệnh đầu guide, gửi OUTPUT_ZIP cả lỗi; review trước
field decision/bulk plan. Chưa mở1.104 queries hoặc certify event/revision history.

### 11.39. Review full MBS query và detail187243 — 03/11/2026

User chạy `run-20261103T055821608254Z`,4 pages stable63/63 unique rows và detail187243,
5 business200. Run44.657s,interval8s+,111 context attempts/109 admissions,106 assets/
external,2 external blocked. Review PASS ZIP CRC/32 members/31 hashes/exact state,
runtime/provenance/reparsed rendered fragments/protected120 old files.19 tests/
compileall PASS; agent0 new source requests/browser launches/code changes.

Detail187243 ghi equity MBS/HNX,record25/09/2025,rights100:12 và giá phát hành10.000
đồng/cổ phiếu trong phần quyền mua,bonus100:03 riêng. HNX581051 corroborate record/
rights/price; HNX/previous SDK review cung cấp ex24/09/2025,không suy từ VSDC. VSDC
update label17/09/2025 không PIT.43 IDs mới so với audited cache,1 detail mới,không
gọi43 events hoặc auto-fetch42 candidate bodies khác. Không đổi queue/owner choices.

Review mới khép2 prior VSDC pagination gaps,giữ immutable prior review.4 title flags
historical2022/2021/2020 chưa linked bằng detail; HNX source-group/window/586647
title-only/issuer-history gaps còn. Terms corroboration PASS,field decision vẫn
MANUAL_REVIEW_REQUIRED/HOLD_RESIDUAL_REVISION_SCOPE_REVIEW,không certify no revisions,
không ký/apply10000 proposal/45 choices/canonical/PIT/identity.

Evidence `data/corporate_actions/work/vsdc_mbs_browser_supplement_live_review_20261103_v1/`,
HTML `xem_ket_qua_MBS.html`; validation
`data/corporate_actions/work/vsdc_mbs_browser_supplement_live_review_validation_20261103_v1/`.
Bước tiếp đề xuất: batched plan1.104 affected queries,dedup/reuse cached bodies và
small multi-ticker validation trước broad acquisition. MBS residual revision-scope/
owner decision tách riêng. Dừng tại review,không next-stage execution hoặc bulk.

### 11.40. Cache-first supplement plan và pilot3 mã — preparation03/11/2026

User giao next stage sau làm rõ không yêu cầu duyệt giá MBS. Đã lập inventory cho
baseline1.104 queries,mark MBS completed ở overlay mới nên pending1.103.1.096 normal
gồm pilot A32/AAA/IDJ;7>20-page queries(BID/BVB/HAM/HAN/HCM/S12/VDB) giữ scope HOLD.
1.093 normal ngoài pilot chia55 batches đề xuất,max20 tickers/100 estimated lists,
không executable/authorized. DTR/KAI/LPS/PCB và414 exhausted snapshots theo dõi riêng.

Cache27.731 reusable-detail IDs =27.730 baseline+detail187243 rendered overlay,không
43 MBS discovery IDs. Verify baseline index/overlay hashes,provenance không đổi;
no automatic new detail requests. New pilot list-only3 exchanges,fresh UI sessions,
global dedup provider IDs giữ memberships/titles,không event identity/approval.
Hard cap4 pages/query,12 business/global,shared8s/operation15s/query90s/global240s,
82 context/query/78 assets/query/246 context/global/HTML2MB. Source/access/TLS/layout/
budget errors STOP cả lượt,no retry/resume/fallback/profile/header workaround.

Preparation `data/corporate_actions/work/vsdc_supplement_plan_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_supplement_plan_validation_20261103_v1/`.
Protect181 old files;137 targeted tests (12 mới),compileall/synthetic smoke/CLI check
PASS.0 browser launches/source requests/canonical/owner choice changes trong stage.
Self-review chỉ preparation,live3query chưa chạy. Bước tiếp:user chạy exact CLI đầu
guide một lần,gửi OUTPUT_ZIP cả lỗi;review trước executable batch preparation.
Không tự mở55 batches/bulk/detail fetch hoặc yêu cầu duyệt giá MBS.

### 11.41. Review live A32/AAA/IDJ — PASS03/11/2026

User chạy `run-20261103T061831245900Z`. A32/AAA/IDJ đủ35/51/24 rows,total/ranges/IDs
nhất quán,7 business200.110 distinct provider IDs =60 cache hits +50 new candidates
(15/31/4),0 new detail requests.0 cross-query duplicate trong live sample,không claim
collision branch live-tested;dedup/cache flags reconstructed đúng,branch có mocks.

Review PASS ZIP CRC/51 members/50 payload hashes/exact state/runtime/provenance/
protected181 old files.166 context attempts/163 admissions,159 assets/external,
3 external blocked;business interval8s+,run52.11s.12 tests/compileall PASS,agent0 new
browser launches/source requests/code/canonical/owner changes. Cache remains27.731
reusable-detail IDs,không thêm50 list-only candidates vào downloaded cache.

Reviewed inventory overlay mark4 complete query snapshots(MBS/A32/AAA/IDJ),pending
1.100 =1.093 normal trong55 proposed batches+7 large HOLD. Audit1.104/preparation
không sửa.414 archived-exhausted và4 unverified tiếp tục theo dõi;sum1.522 gồm1.100+
4+414+4,không final history/identity/PIT hoặc detail completeness.
Evidence `data/corporate_actions/work/vsdc_three_query_browser_live_review_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_three_query_browser_live_review_validation_20261103_v1/`.
Bước tiếp đề xuất: prepare executable discovery batch đầu tiên,không bulk chaining/
detail fetching;track414 refresh/coverage checks và4 diagnostics riêng. Dừng tại
review stage,chưa tạo/chạy batch mới hoặc yêu cầu MBS price approval.

### 11.42. Chuẩn bị speed4s pilot riêng,cùng3 query — 03/11/2026

User giao giảm interval thử nghiệm trước batch.New module/config/CLI/output riêng,
cùng A32/AAA/IDJ/list-only/min start interval8→4s,shared cảpage/ticker transitions.
Frozen8s baseline/code/artifacts bất biến;pin parents/protect250 old files. New
business guard tránh inherited8s gate,static gates giữ nguyên. Cùng12 business/
4pages-query/82context-query/78assets-query/246context-global,operation15s/query90s/
run240s/HTML2MB,no details/workers increase/auth/profile/TLS workaround.

HTTP/access/redirect/challenge/Retry-After/TLS/transport/layout/budget failures STOP,
không retry/interval negotiation/fallback8s. Experiment lưu reviewed8s52.11s/7business
và rows35/51/24 làm baseline,không guarantee2x hoặc safe long-run rate. Same-query
repeat không new completion credit:pending1.100 và414+4 riêng/proposed55 batches
giữ nguyên.0 new browser launches/source requests/canonical/owner/PIT changes.

Preparation `data/corporate_actions/work/vsdc_three_query_speed4s_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_three_query_speed4s_validation_20261103_v1/`.
147 targeted tests(10 mới),compileall/synthetic smoke/CLI check PASS.Test4s admitted,
3.999s blocked,cross-browser shared interval,no hidden8s budget.Self-review chỉ
preparation,live4s chưa test.Bước tiếp:user chạy exact CLI đầuguide một lần,gửi
OUTPUT_ZIP cả lỗi;review source/counts/cache/layout/timings trước executable batch.
Dừng tại preparation,không tự bulk/detail execution hoặc áp giá MBS.

### 11.43. Review live speed4s — PASS03/11/2026

User chạy `run-20261103T063424932059Z`. A32/AAA/IDJ35/51/24,cùng parsed pages/IDs/
titles/cache flags với8s baseline,7 business200. Sáu measured business intervals
4.328–4.422s,elapsed28.328s vs52.11s,saved23.782s(~45.64% lower;ratio1.84 trong sample).
166 context attempts/163 admissions,159 assets/external,3 blocked nhưbaseline. Không
source/access/redirect/challenge/Retry-After/TLS/transport/layout lỗi;không safe-rate/
2x guarantee hoặc causal claim từ small sample.

Review PASS ZIP CRC/52 members/51 payload hashes/state/runtime/experiment/parents/
protected250.10 tests/compileall PASS;agent0 new browser launches/source requests/
code/canonical/owner changes. Same-query repeat không new completion credit,pending
1.100/normal1.093/HOLD7 và414+4tracked giữ nguyên.Cache27.731 không tăng,50candidate
links không phải new discoveries hoặc new detail bodies trong lượt này.
Evidence `data/corporate_actions/work/vsdc_three_query_speed4s_live_review_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_three_query_speed4s_live_review_validation_20261103_v1/`.
Self-review PASS review stage.Bước tiếp đề xuất:prepare first fixed-scope executable
discovery batch4s,same STOP/privacy/cache,review từng local run;no auto55-batch chain/
detail downloads hoặc source-field promotion.Chưa tạo/chạy batch trong stage này.

### 11.44. Chuẩn bị executable batch001 fixed20,list-only4s — 03/11/2026

User giao next stage sau giải thích firstbatch20/54estimated requests và4s không
phải4s/mã.Freeze AAM/ABB/ABC/ABI/ABR/ABT/ACB/ACC/ACE/ACL/ACM/ACV/ADC/ADP/ADS/AFX/
AGF/AGG/AGM/AGP,check same proposed-001 vàreviewed pending overlay.Chỉ list discovery,
same-session complete queries,globalprovider-ID dedup/cache flags,memberships/titles.
Cache27731 reusable-details tách known-list27823IDs,new-detail fetchfalse.

New module/config/CLI/output,old runtime/artifacts bất biến.Pin reviewed4s parents,
protect318 files.Globalmin4s,100 business/query20pages(400rows)/98context-query/
78assets-query/1660context-global,operation15s/query180s/run1200s/HTML2MB,1worker.
Normal browser pagination numeric hoặcobserved “>” exact target,không replay/invoke
AJAX;ACB archived10page controls fixture cóprovenance.All source/access/TLS/redirect/
Retry-After/challenge/transport/layout/budget lỗi STOP cảbatch,no retry/resume/profile/
rate fallback/auto batch002.Query start/complete/final checkpoints vàpartial ZIP.

Preparation `data/corporate_actions/work/vsdc_browser_batch001_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_browser_batch001_validation_20261103_v1/`.
161 targeted tests(14 batch),compileall/synthetic smoke/CLI check PASS,0 new browser
launches/source requests/canonical/owner/PIT changes.Preparation không live credit:
pending1.100,414+4track/7largeHOLD giữ nguyên.Bước tiếp:user chạyexact CLI đầuguide
một lần,gửi OUTPUT_ZIP cảpartial/error;review trước batch tiếp/query-completion
credit/details planning.Chưa tự chạybatch hoặc mở55 proposed batches.

### 11.45. Review batch001 live — PASS20 mã,03/11/2026

User chạy `run-20261103T065700177618Z`.20/20 query lists đủ853 rows/unique provider
IDs,54 business200,ACB10pages.Total/ranges/IDs/source echo/JS/reparse đúng;34 numeric
UIclicks,0arrow branch trong live run.Năm mươi ba business intervals4.14–4.281s,
elapsed223.859s.1114context/1094admissions,1060assets/external,20blocked,within caps.

Review PASS ZIP CRC/336members/335payload hashes/exact state/runtime/parents/
protected318,40query start-complete+1final checkpoints.14tests/compileall PASS.Agent
0new browser launches/source requests/code/canonical/owner changes.400cached-detail
IDs/453first-discovered candidate links,0new detail requests;không453verified events.
No cross-query duplicate observed;global dedup reconstructed preserving memberships/
titles/cache flags.Known-list overlay28276,reusable-details27731,545known uncached
candidates chưa authorized.No raw HTTP fullbody claim hoặc historical/PIT/identity.

New reviewed overlay completed query snapshots24,pending1080=1073normal+7largeHOLD;
audit/preparation/states không sửa.Total1522 vẫn1080+24+414archived-exhausted+4unverified.
Batch001 reviewed complete,remaining54proposed batches chưa executable.Evidence:
`data/corporate_actions/work/vsdc_browser_batch001_live_review_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_browser_batch001_live_review_validation_20261103_v1/`.
Bước tiếp đề xuất:prepare exactbatch0024s,same cache/privacy/STOP,carry known-list
28276 riêng reusable-detail27731;review từngrun.Không auto54-batch chain/details
downloads/field promotion,414+4 work items giữtracked.Stage này chỉreview,chưa
chuẩn bị/chạybatch002.

### 11.46. Chuẩn bị speed2s3query trước11batch — 03/11/2026

User giao nextstage kiểm chứng2s. New module/config/CLI/output riêng,cùng A32/AAA/
IDJ,list-only,interval4→2s sharedbusiness starts. Samecaps12business/4pages-query/
82context-query/78assets-query/246context-global,operation15s/query90s/run240s/HTML2MB,
1worker/defaultChrome/TLS/privacy. Guard2s accepted/1.999s refused,no hidden4s/8s;
allsource/access/redirect/challenge/Retry-After/TLS/transport/layout/budget errors
STOP,no retry/interval negotiation/fallback/header/profile/auth workaround.

Pin reviewed4s baseline28.328s/7business/rows35-51-24 vàbatch001 latestprogress1080,
known-list28276 tách reusable-detail27731. Same-queryrepeat,no new completioncredit,
details/owner/canonical/PIT/identity unchanged.Protect673 old files.171 targetedtests
(10mới),compileall/synthetic smoke/CLI check PASS,0new browser launches/source requests.
Preparation `data/corporate_actions/work/vsdc_three_query_speed2s_preparation_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_three_query_speed2s_validation_20261103_v1/`.
Self-review preparation only,live2s unverified.Bước tiếp:user chạy exactCLI đầuguide
một lần,gửi OUTPUT_ZIP cảerror/partial;review source/data/timing trước prepare11batch
với evidence-backed interval.Chưa build/execute11batch hoặc guarantee2x rate.

### 11.47. Review live speed2s — PASS03/11/2026

User chạy `run-20261103T072216826201Z`.3queryA32/AAA/IDJ35/51/24,cùng parsed pages/
IDs/titles/cache flags/JS contract với4s,7business200.Interval2.172–2.297s,elapsed
15.235s vs28.328s(~46.22% reduction),166context/163admissions,159assets,3external
blocked như4s.No source/access/redirect/challenge/Retry-After/TLS/layout/transport
errors.110provider IDs,60cachehit/50already-known uncached links,0new discoveries/
details.No guaranteed2x/sustained-rate claim từsmall repeat.

Review PASS ZIP CRC/53members/52hashes/state/runtime/parents/protected673.10tests/
compileall PASS.Agent0new source requests/browser launches/code/canonical/owner
changes.No completion credit,pending1080/24reviewed snapshots,414+4track/7HOLD,
cache27731/known-list28276 giữ nguyên.No history/identity/PIT hoặc field promotion.
Evidence `data/corporate_actions/work/vsdc_three_query_speed2s_live_review_20261103_v1/`;
validation `data/corporate_actions/work/vsdc_three_query_speed2s_live_review_validation_20261103_v1/`.
Bước tiếp đề xuất:prepare fixed11-batch local002..012chain,220queries/archived586
estimated lists,min2s,per-batch validation/checkpoints/ZIP vàwhole-run STOP,no
retry/fallback/details/auto54batch chain.Stage chỉreview,chưa build/execute11batch.

## 12. Các output và code dùng để tiếp tục

### Bàn giao bounded HNX local supplement 10 mã — 03/11/2026

Đã chuẩn bị code/config/checkpoint và kiểm tra offline, chưa acquisition. Chọn
VE3/TNG/IDJ/MBS/RGG/VTZ/HKT/PGN/TIG/VEF: tám HNX, hai UPCOM, một payload/mã,
25 field tasks từ missing queue. Scope assignment theo C8 v2 đủ1.522 mã.
Queue toàn bộ vẫn602 payloads/332 mã/1.373 field tasks; HNX/UPCOM354 payloads/
197 mã. Before→after selected missing25→25, articles/observations/fields mới0.

Đã verify bốn latest cumulative HNX ZIPs và pending states của10 mã; chưa có
discovery/detail cache cho chúng. Hash/reparse137 raw VSDC và đối chiếu normalized
evidence, không tìm supported dated field anchor cho selected payloads. RGG2025
có raw hỗ trợ nên giữ review offline; chọn RGG2022 chưa có hỗ trợ. Không tải lại
PVS/ACV, không dùng PIT/identity flags để request hoặc đếm pilot thành event mới.

Contract mới một worker/shared8s/timeout15s/2MB, 2 pages + 2 details/mã, 50 requests
cộng dồn;1.200s/lượt/2.400s lineage. Checkpoint mỗi request/work unit, verified
eligible resume sang output mới, ZIP giữ cả partial. Source access/TLS STOP toàn
job, gồm cả network timeout; không retry/fallback hoặc sửa checkpoint Kaggle `resumable=false`.
85 targeted tests (13 mới)/compileall/smoke UTF-8/CLIcheck/self-review PASS;
live access/extraction còn pending. Không áp45 owner choices hoặc canonical.

Preparation hiện hành:
`data/corporate_actions/work/hnx_local_supplement10_preparation_20261103_v3/`;
validation `data/corporate_actions/work/hnx_local_supplement10_validation_20261103_v2/`.
v1/v2 preparation draft giữ nguyên và không dùng để chạy. Lệnh PowerShell và ZIP
path tại đầu collection guide. User chạy terminal rồi gửi OUTPUT_ZIP để review
stage riêng; agent dừng, không polling hoặc tiếp tục acquisition.

Workspace:

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK
```

### Dữ liệu ban đầu và VSDC timing

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\outputs\batch_shard_0
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\outputs\batch_shard_1
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\outputs\batch_shard_2
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\outputs\batch_shard_3
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_c8_v2_checkpoint_20261101_v5
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_vsdc_reparse_20261101_v3\timing_recovery_summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_hnx_round2_four_shard_incident_20261102_v1\audit.json
```

### Full VCI và các stage xử lý

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\data\corporate_actions\work\vci_local_v1\delta-vci-state-local-20261102T024517019426Z.zip
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_vci_local_full_audit_20261102_v1\audit.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_offline_reconciliation_20261102_v1\summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_raw_evidence_review_20261102_v4\summary.json
```

### Danh sách bổ sung và kết quả pilot hiện hành

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_supplement_plan_20261102_v1\well_supported_price_candidates_195.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_supplement_plan_20261102_v1\additional_price_review_49.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_supplement_plan_20261102_v1\missing_event_fields_602.jsonl
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_supplement_plan_20261102_v1\coverage_review_182.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_supplement_source_pilot_20261102_v2\summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_supplement_pilot_review_20261102_v1\stage_summary.json
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\tmp\ca_supplement_pilot_review_20261102_v1\pilot_findings.json
```

Plan có thể giữ status lịch sử `PILOT_PENDING` vì được seal trước khi chạy pilot. Dùng `stage_summary.json` và `pilot_findings.json` để đọc kết quả pilot đã thực hiện; không sửa artifact cũ để đổi status.

### Code chính

```text
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\collect_corporate_actions_v1.py
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\reparse_corporate_action_timing_v3.py
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\collect_hnx_announcements_batch_v1.py
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\run_vci_calendar_local_v1.py
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\reconcile_corporate_action_archives_v1.py
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\review_corporate_action_evidence_v1.py
C:\Users\HP\Downloads\Phân cụm động lượng TTCK\scripts\plan_corporate_action_supplement_v1.py
```

## 13. Kiểm tra đã thực hiện và giới hạn của nhật ký

| Stage | Kiểm tra đã ghi nhận |
|---|---|
| VSDC timing V3 | 106 corporate-action tests, compileall và synthetic smoke PASS; kiểm tra hash/invariants |
| Full VCI audit | CRC, manifest/commit hashes, local/ZIP equality, query bounds và thống kê độc lập |
| Reconciliation preview | 13 targeted tests, compileall, synthetic smoke và self-review PASS |
| Raw evidence review | 34 targeted tests, compileall, synthetic smoke; 1.815 input hashes và 1.855 quotes được kiểm tra |
| Supplement plan/pilot | 8 targeted tests, compileall, synthetic smoke; self-review 41 file hashes; visual review FIT sáu trang/AAS hai trang |
| ABB scoped access/AAS lifecycle | 56 targeted tests, compileall, synthetic smoke PASS; visual review nghị quyết 18 ba trang; raw/receipts và anomaly metadata manifest được kiểm tra riêng |
| VSDC cache audit | 48 targeted tests, compileall/synthetic smoke PASS; 32.393 input hashes, 10 output hashes, 42 price/unit checks; findings18/8 giữ manual review |
| Cached26 offline review | 64 targeted tests, compileall/synthetic smoke PASS;34 input/8 output/6 code hashes,127 quote checks;5 supported candidates và21 pending |
| Decision packet25 | 83 targeted tests,compileall/synthetic smoke PASS;402 input/8 output/7 code hashes,112 quotes,26 ratio-leg checks;unsigned/manual-only |
| DTP/ASG targeted documents | 108 targeted tests,compileall/synthetic smoke PASS;3 complete PDFs,14 reviewed pages,18 input/28 output hashes vàhai independent page re-renders;approved fields0 |
| Sáu chuỗi revision | 122 targeted tests, compileall/synthetic smoke PASS; 24 input/5 output hashes, 117 quotes, 6 original price/ratio checks; 4 contextual proposals/2 HOLD, approved fields0 |
| GSP/KPF follow-up | 129 targeted tests, compileall/synthetic smoke PASS;45input/8output/4code hashes,53quotes; GSP3edges khớp, KPFdate anomaly/HOLD vàHTTP406 STOP, approved fields0 |
| Owner-review packet26 | 146 targeted tests,compileall/smoke PASS;56input/6output/2code hashes,27raw/54fieldchecks,26SDKrows/45pendingchoices/1HOLD;0approved/applied/network |
| Gom thư mục/pilot KBS local | 424 targeted tests,compileall/smoke PASS;176file hashes/161junctions/78manifests/32entrypoints;0KBS requests;full repository gate còn thiếu artifact ngoài phạm vi |

Các kết quả trên chứng minh phạm vi kỹ thuật đã kiểm tra, không tự chứng nhận dữ liệu đã sẵn sàng backtest. Mọi artifact cũ tiếp tục được giữ nguyên. Không có thao tác canonical freeze, tính giá điều chỉnh hoặc chạy backtest chỉ từ việc tạo tài liệu này.
