"""Build a portable Kaggle input from the audited local checkpoint; zero network."""
from __future__ import annotations
import argparse,hashlib,json,shutil,sys,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import resume_corporate_actions_v1 as runner

GUIDE='''# Chạy corporate actions C8 v2 trên Kaggle

## Phạm vi và thời gian

Dùng một tài khoản Kaggle. Scope 1.522 mã, window 2019-01-31..2025-12-31;
20 mã đã xử lý, 1.502 mã còn lại. Mỗi batch mặc định tối đa 150 mã/90 phút,
dừng ở ranh giới mã nên có thể vượt budget bằng thời gian xử lý một mã cuối.
Đây không phải cam kết hoàn tất toàn universe trong 1–2 giờ. Ước tính toàn phần còn
lại theo lượt đo local khoảng 17–24 giờ, chưa tính verification/gaps.

Giữ minimum interval 2 giây, không dùng nhiều tài khoản/IP để vượt giới hạn nguồn.
Ba workers dùng chung limiter/blocked-host/request budget trong một process.
Các process hoặc máy độc lập không tự chia sẻ limiter này; chia shard không đồng
nghĩa được phép nhân tổng tải lên nguồn. Không có cam kết hạ delay 0,25 giây.
Kaggle chỉ chuyển nơi chạy; GPU không giúp giảm network wait. HTTP 401/403/429 hoặc
challenge dừng host theo policy; không tự reset blocked state.

## 1. Tải hai file

`delta-ca-kaggle.zip` là input bundle (code đang làm local, canonical securities,
checkpoint, cache/raw và observations cũ). `DELTA_Corporate_Actions_Kaggle.ipynb`
là notebook đã cấu hình. Không cần git clone, push code, tải SQLite 527 MB hoặc giá 4 GB.
Code chỉ dùng Python standard library trong workflow này, không cần pip install/GPU.

## 2. Tạo input Dataset private

Trên Kaggle chọn Create → New Dataset, upload `delta-ca-kaggle.zip`, đặt tên tùy ý
và giữ Private. Không upload cả repository, .venv, .git hoặc credentials.

## 3. Tạo notebook

Tạo Python Notebook, import/upload file `.ipynb` đã cung cấp. Thêm Dataset private
vừa tạo vào Input. Trong Session options bật Internet, chọn Accelerator=None (CPU).
Nếu Internet không bật được, kiểm tra trạng thái xác minh/quyền của tài khoản;
không tiếp tục crawl khi network đang bị vô hiệu hóa.

## 4. Chạy batch đầu

Chạy các cells theo thứ tự. Cell setup tự tìm input ZIP, verify bootstrap manifest
và file hashes, giải nén vào `/kaggle/working/delta-ca`. Preflight phải báo scope=1522,
pending=1502, next=ACL. Batch mặc định MAX_SECURITIES=150, MAX_SECONDS=5400,
MAX_REQUESTS=4000. Không hạ delay. Theo dõi processed count và physical_requests.
Notebook có WORKERS=3, EXCHANGES=[] (toàn pending scope), SHARD_COUNT=1,
SHARD_INDEX=0. Lần đầu đổi MAX_SECURITIES=3 để smoke trên Kaggle IP; kiểm source
limitations trước khi tăng lên 150. Nếu nguồn block, giữ artifact và dừng nguồn,
không đổi tài khoản/IP để tiếp tục request bị chặn.

Có thể đặt EXCHANGES=['UPCOM'] để chỉ giao việc UPCOM, nhưng canonical scope vẫn
1.522 mã. Hoặc chia cân bằng theo SHARD_COUNT/SHARD_INDEX, index bắt đầu từ 0.
Ownership tính từ toàn canonical scope nên không dịch chuyển khi pending giảm.
Giữ nguyên shard count/index qua các batch; không để các process dùng cùng shard.
Đây là phân công job, không phải hướng dẫn vượt quota/tạo nhiều Kaggle accounts.

Để Kaggle thực thi một version đầy đủ, dùng Save Version → Save & Run All.
Lượt này chạy từ clean session: cần attach input ZIP/state trước khi lưu version.
Exit code 2 là PARTIAL dự kiến, không phải coverage complete; code khác 0/2 cần đọc lỗi.
Không đồng thời chạy interactive và saved version cho cùng batch.

## 5. Lưu kết quả và tiếp tục

Cell cuối tạo `/kaggle/working/delta-ca-state-sNNN-of-NNN.zip` và bảng tiến độ. Tải ZIP về máy
sau mỗi batch. Khi notebook version đã hoàn tất, output cũng có thể được attach làm
Input của notebook tiếp theo. Với session mới, attach state ZIP gần nhất, chạy lại
notebook: nó ưu tiên state ZIP, kiểm manifest, tự chọn checkpoint/batch tiếp theo.
Không cần copy lại code hoặc sửa ticker list. Cùng session có thể chạy lại các cells
chọn checkpoint → dry-run → collection → export; tên batch mới được cấp tự động.

Kaggle docs hiện mô tả CPU notebook session tối đa 12 giờ và 20 GB autosaved ở
`/kaggle/working`; không dùng một batch 17 giờ. Lưu version/output mỗi batch.
Nếu session bị dừng giữa mã, giữ toàn bộ workspace/state: script dùng progress
snapshot và sealed child manifests; unfinished raw không đủ provenance không được
gán source/timestamp giả để reuse. Chỉ upload lại state ZIP sau khi có bản export.

## 6. Nhận kết quả về local

Giữ state ZIP của từng shard, không ghi đè checkpoint cũ. Output mới ở `outputs/batch_cNNN_sNNN_NNN/`:
`batch_results.json`, `resume_state.json`, `checkpoints/`, `source_receipts/`, manifest.
`processed` nói về bounded source checks; `coverage` vẫn INCOMPLETE khi identity,
terms, timing/revisions chưa đủ. Không build price series hoặc backtest trong notebook.
Notebook export includes code/canonical/cache cũ và outputs mới để có thể resume.
Khi ghép nhiều shard, không cộng trực tiếp processed count vì 20 mã bootstrap chung;
phải union theo canonical identity/scope và verify manifests, giữ raw của mọi shard.
Các process độc lập không chia sẻ host-stop state. Nếu một process báo block/rate limit,
dừng các job khác gọi cùng nguồn; không đổi server/tài khoản để retry request bị chặn.

Nguồn Kaggle: [Notebooks](https://www.kaggle.com/docs/notebooks),
[Datasets](https://www.kaggle.com/docs/datasets),
[Terms](https://www.kaggle.com/terms). Giới hạn/UI có thể thay đổi; kiểm lại session options.
'''

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def build(checkpoint,output):
    state,scope=runner.verified_checkpoint(checkpoint)
    output.mkdir(parents=True,exist_ok=False)
    project=output/'project';project.mkdir()
    shutil.copytree(ROOT/'src',project/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (project/'scripts').mkdir()
    shutil.copyfile(ROOT/'scripts/resume_corporate_actions_v1.py',project/'scripts/resume_corporate_actions_v1.py')
    profile=Path('configs/data/corporate_actions_kaggle_v1.json')
    (project/profile).parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/profile,project/profile)
    canonical=Path('artifacts/cafef_primary/cafef-c8-complete-only-v2/canonical/securities.jsonl')
    (project/canonical).parent.mkdir(parents=True)
    shutil.copyfile(ROOT/canonical,project/canonical)
    portable=project/'checkpoints/bootstrap';portable.mkdir(parents=True)
    shutil.copyfile(checkpoint/'scope.csv',portable/'scope.csv')
    origin=digest(checkpoint/'manifest.json')
    portable_state={k:v for k,v in state.items() if k not in {'source_root','upstream_checkpoint','verified_collections'}}
    portable_state.update(origin_checkpoint_manifest_sha256=origin,reference_format='CHECKPOINT_RELATIVE_CACHE_OR_REPO_REFERENCE_V1')
    (portable/'resume_state.json').write_text(runner.base.json_text(portable_state),encoding='utf-8')
    copied=set()
    def payload(source,sha):
        source=Path(source)
        if digest(source)!=sha:raise ValueError('SOURCE_PAYLOAD_CHECKSUM_MISMATCH')
        dest=portable/'payloads'/f'{sha}.bin'
        if sha not in copied:
            dest.parent.mkdir(exist_ok=True);shutil.copyfile(source,dest);copied.add(sha)
        return dest
    entries=[]
    for entry in runner.legacy.read_jsonl(checkpoint/'source_receipts/index.jsonl'):
        raw=runner.resolve_reference(entry['archive_path'],checkpoint)
        dest=payload(raw,entry['source_hash'])
        entries.append(dict(entry,archive_path=dest.relative_to(portable).as_posix()))
    (portable/'source_receipts').mkdir()
    (portable/'source_receipts/index.jsonl').write_text(runner.legacy.dump_jsonl(entries),encoding='utf-8')
    observations=runner.legacy.read_jsonl(checkpoint/'normalized_observations/all_observations.jsonl')
    for observation in observations:
        for evidence in observation.get('source_evidence',[]):
            if evidence.get('path'):
                dest=payload(runner.resolve_reference(evidence['path'],checkpoint),evidence['source_hash'])
                evidence['original_archive_path']=evidence['path']
                evidence['path']='@repo/'+dest.relative_to(project).as_posix()
    (portable/'origin_observations.jsonl').write_text(runner.legacy.dump_jsonl(observations),encoding='utf-8')
    (portable/'provenance').mkdir()
    for original,name in [('manifest.json','origin_manifest.json'),('coverage.json','origin_coverage.json'),('rights_report.json','origin_rights_report.json')]:
        shutil.copyfile(checkpoint/original,portable/'provenance'/name)
    files={p.relative_to(portable).as_posix():digest(p) for p in portable.rglob('*') if p.is_file()}
    (portable/'manifest.json').write_text(runner.base.json_text(dict(artifact_type='corporate-action-c8-v2-checkpoint',schema_version='1.2.0',status='PARTIAL',
        origin_checkpoint_manifest_sha256=origin,portable_derivation=True,source_values_and_timestamps_unchanged=True,files=files)),encoding='utf-8')
    (project/'KAGGLE_SETUP.md').write_text(GUIDE,encoding='utf-8')
    manifest=dict(version='ca-kaggle-portable-v1',minimum_request_interval_seconds=2,scope_count=len(scope),
        pending_count=len(state['pending_securities']),origin_checkpoint_manifest_sha256=origin,
        files={p.relative_to(project).as_posix():digest(p) for p in project.rglob('*') if p.is_file()})
    (project/'bundle_manifest.json').write_text(runner.base.json_text(manifest),encoding='utf-8')
    manifest_sha=digest(project/'bundle_manifest.json')
    archive=output/'delta-ca-kaggle.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in project.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(project).as_posix())
    cells=[]
    def md(text):cells.append(dict(cell_type='markdown',metadata={},source=text.splitlines(keepends=True)))
    def code(text):cells.append(dict(cell_type='code',execution_count=None,metadata={},outputs=[],source=text.splitlines(keepends=True)))
    md('# DELTA — Corporate actions C8 v2 trên Kaggle\n\nCPU + Internet ON. Một batch 90 phút; script không gọi model. Toàn universe không được cam kết hoàn tất trong 1–2 giờ. Đọc KAGGLE_SETUP.md đi kèm.')
    code('''from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, zipfile
WORK = Path('/kaggle/working/delta-ca')
EXPECTED_MANIFEST_SHA = '''+repr(manifest_sha)+'''
archives = list(Path('/kaggle/input').rglob('delta-ca-state*.zip'))
if len(archives) > 1:
    raise RuntimeError('Chỉ attach một state ZIP gần nhất để tránh chọn nhầm checkpoint.')
if not archives:
    archives = list(Path('/kaggle/input').rglob('delta-ca-kaggle.zip'))
if len(archives) != 1:
    raise RuntimeError('Attach Dataset chứa một input ZIP hoặc một state ZIP gần nhất.')
if not (WORK / 'bundle_manifest.json').exists():
    if WORK.exists() and any(WORK.iterdir()):
        raise RuntimeError('Workspace không rỗng và chưa có bundle manifest; giữ evidence, không ghi đè.')
    WORK.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archives[0]) as z:
        if hashlib.sha256(z.read('bundle_manifest.json')).hexdigest() != EXPECTED_MANIFEST_SHA:
            raise RuntimeError('Bootstrap manifest mismatch')
        for info in z.infolist():
            if not (WORK / info.filename).resolve().is_relative_to(WORK.resolve()):
                raise RuntimeError('ZIP path escape')
        z.extractall(WORK)
if hashlib.sha256((WORK/'bundle_manifest.json').read_bytes()).hexdigest() != EXPECTED_MANIFEST_SHA:
    raise RuntimeError('Workspace bootstrap manifest changed')
manifest = json.loads((WORK/'bundle_manifest.json').read_text())
for name, expected in manifest['files'].items():
    path = (WORK/name).resolve()
    if not path.is_relative_to(WORK.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise RuntimeError('File integrity mismatch: '+name)
os.chdir(WORK)
print('Bundle verified:', manifest['version'], 'Python:', sys.version.split()[0])
''')
    md('## Chọn checkpoint và giới hạn batch\n\nMặc định tối đa 150 mã hoặc 90 phút, dừng giữa các mã. Không giảm delay; không đồng thời chạy hai notebook cho cùng workspace/batch.')
    code('''MAX_SECURITIES = 150
MAX_SECONDS = 5400
MAX_REQUESTS = 4000
WORKERS = 3
EXCHANGES = []  # [] = full pending scope; hoặc ['UPCOM'], ['HOSE'], ['HNX']
SHARD_COUNT = 1
SHARD_INDEX = 0  # zero-based; ownership frozen against full canonical scope
outputs = WORK/'outputs'
outputs.mkdir(exist_ok=True)
prefix = f'batch_c{SHARD_COUNT:03}_s{SHARD_INDEX:03}_'
existing = sorted(outputs.glob(prefix+'*'))
checkpoint = WORK/'checkpoints/bootstrap'
for candidate in reversed(existing):
    if (candidate/'manifest.json').exists() or list((candidate/'checkpoints').glob('state-*.json')):
        checkpoint = candidate
        break
number = max([int(p.name.split('_')[-1]) for p in existing] + [0]) + 1
output = outputs/f'{prefix}{number:03}'
command = [sys.executable, 'scripts/resume_corporate_actions_v1.py',
           '--checkpoint', str(checkpoint), '--output', str(output),
           '--max-securities', str(MAX_SECURITIES), '--max-requests', str(MAX_REQUESTS),
           '--max-seconds', str(MAX_SECONDS), '--workers', str(WORKERS),
           '--shard-count', str(SHARD_COUNT), '--shard-index', str(SHARD_INDEX)]
if EXCHANGES:
    command += ['--exchange', *EXCHANGES]
preflight = subprocess.run(command+['--dry-run'], capture_output=True, text=True, check=True)
state = json.loads(preflight.stdout)
print({k:v for k,v in state.items() if k != 'next_securities'})
print('Next:', state['next_securities'][:5], 'Output:', output)
''')
    code('''if state['assigned_pending_count']:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1, env={**os.environ, 'PYTHONUTF8':'1'})
    for line in process.stdout:
        print(line, end='', flush=True)
    returncode = process.wait()
    if returncode not in (0, 2):
        raise RuntimeError(f'Collector stopped with error {returncode}; giữ workspace để recover.')
    print('Batch finished; PARTIAL không đồng nghĩa coverage complete.')
else:
    print('Đã xử lý hết pending list; còn phải đánh giá data/identity/PIT coverage.')
''')
    code('''from IPython.display import FileLink, display
for candidate in sorted(outputs.glob('batch_*')):
    path = candidate/'resume_state.json'
    if path.exists():
        status = json.loads(path.read_text())
        print(candidate.name, 'processed=', len(status['processed_securities']),
              'pending=', len(status['pending_securities']), 'next=', status['next_security'])
export = Path(f'/kaggle/working/delta-ca-state-s{SHARD_INDEX:03}-of-{SHARD_COUNT:03}.zip')
shutil.make_archive(str(export.with_suffix('')), 'zip', root_dir=WORK)
print('Download và giữ state ZIP sau mỗi batch. Attach ZIP này cho session tiếp theo.')
display(FileLink(str(export)))
''')
    md('## Kết thúc\n\nLưu version/output, tải delta-ca-state.zip. Session tiếp theo attach state ZIP gần nhất và chạy notebook từ đầu. Các fields/identity/PIT unresolved vẫn cần review; notebook không chạy price adjustment hoặc backtest. [Kaggle docs](https://www.kaggle.com/docs/notebooks) · [Terms](https://www.kaggle.com/terms).')
    notebook=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.11')),
                  nbformat=4,nbformat_minor=5)
    (output/'DELTA_Corporate_Actions_Kaggle.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'KAGGLE_SETUP.md').write_text(GUIDE,encoding='utf-8')
    summary=dict(zip_path=str(archive),zip_bytes=archive.stat().st_size,zip_sha256=digest(archive),bootstrap_manifest_sha256=manifest_sha,
        cached_payloads=len(copied),receipt_entries=len(entries),prior_observations=len(observations),pending=len(state['pending_securities']),network_requests=0)
    (output/'export_manifest.json').write_text(runner.base.json_text(summary),encoding='utf-8')
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(build(args.checkpoint,args.output),ensure_ascii=False,indent=2))
