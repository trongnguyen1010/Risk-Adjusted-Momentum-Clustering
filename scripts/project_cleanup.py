"""Plan/pack/check a bounded cleanup. Pruning uses the reviewed PowerShell manifest.

Raw/canonical/source code is never selected. Archives retain exact original paths.
"""
import argparse,hashlib,json,os,re,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
OUT=R/'artifacts/repository/project-cleanup-20261023'
ARC=R/'artifacts/archives/project-cleanup-20261023'
COLD=[
 'financial-acquisition-first50-qa-v1','financial-acquisition-first50-v1',
 'financial-acquisition-total100-qa-v1','financial-acquisition-total1100-additional300-v1',
 'financial-acquisition-total1400-additional300-v1','financial-acquisition-total1522-additional122-v1',
 'financial-acquisition-total200-v1','financial-acquisition-total500-v1',
 'financial-coverage-diagnosis-v1','financial-recovery-readiness-v1']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(name):
 q=PurePosixPath(name)
 if q.is_absolute() or '..' in q.parts or ':' in name or '\\' in name:raise ValueError(name)
 p=R.joinpath(*q.parts);resolved=p.resolve()
 if resolved==R or not resolved.is_relative_to(R):raise ValueError(name)
 for x in [p,*p.parents]:
  if x==R:break
  if x.exists() and (x.is_symlink() or getattr(x.stat(),'st_file_attributes',0)&0x400):raise ValueError('reparse:'+name)
 return p
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(p):return json.loads(p.read_bytes())
def plan():
 if (OUT/'plan.json').exists():raise ValueError('Immutable cleanup plan already exists; use check or restore')
 texts=[];scan=[];pinned_refs=set()
 pin_pattern=re.compile(r'(?:artifacts/reports/[^/"\s]+|\.tmp/[^"\s]+)')
 def scan_pins(p):
  # Keep only path matches; joining every historical pin map wastes memory.
  with p.open('r',encoding='utf-8-sig',errors='replace') as stream:
   tail=''
   while chunk:=stream.read(1024*1024):
    chunk=tail+chunk.replace('\\\\','/')
    pinned_refs.update(pin_pattern.findall(chunk));tail=chunk[-1024:]
 for root in ['src','scripts','tests','configs','docs','artifacts/reports']:
  for p in (R/root).rglob('*'):
   if p.is_file() and p.suffix in {'.py','.ps1','.json','.md'} and p!=Path(__file__):
    text=p.read_text(encoding='utf-8-sig',errors='replace').replace('\\\\','/')
    texts.append(text);scan.append(p.relative_to(R).as_posix())
 # Scan pin/manifest/control metadata, not 600k raw/candidate/receipt payloads.
 for base,dirs,files in os.walk(R/'data'):
  dirs[:]=[d for d in dirs if d not in ['raw','candidates','receipts','network','__pycache__']]
  for n in files:
   if n not in {'input-pins.json','source-pins.json','manifest.json','config.json','implementation-pins.json','source-result-ref.json'}:continue
   p=Path(base)/n;scan_pins(p);scan.append(p.relative_to(R).as_posix())
   if len(scan)%2000==0:print(json.dumps(dict(phase='PIN_SCAN',metadata_files=len(scan))),flush=True)
 text='\n'.join(texts);text_refs=set(pin_pattern.findall(text));targets=[];held=[]
 runtime='\n'.join(p.read_text(encoding='utf-8-sig',errors='replace').replace('\\\\','/') for base in ['src','scripts','tests','configs'] for p in (R/base).rglob('*') if p.is_file() and p.suffix in {'.py','.ps1','.json'} and p!=Path(__file__))
 for name in COLD:
  rel='artifacts/reports/'+name;p=safe(rel)
  if not p.exists():continue
  if rel in runtime or rel in pinned_refs:held.append(dict(path=rel,reason='RETAINED_RUNTIME_OR_FROZEN_PIN_REFERENCE'));continue
  targets.append(dict(path=rel,kind='COLD_REPORT_EXACT_ARCHIVE'))
 for p in (R/'.tmp').iterdir():
  if not p.is_file():continue
  rel=p.relative_to(R).as_posix()
  if rel in text_refs or rel in pinned_refs or p.name in runtime:held.append(dict(path=rel,reason='REFERENCED_SCRATCH_HELPER_OR_LOG'));continue
  targets.append(dict(path=rel,kind='UNREFERENCED_SCRATCH_EXACT_ARCHIVE'))
 files=[]
 for t in targets:
  p=safe(t['path']);members=sorted(x for x in p.rglob('*') if x.is_file()) if p.is_dir() else [p]
  for x in members:
   rel=x.relative_to(R).as_posix();safe(rel);files.append(dict(path=rel,sha256=sha(x),bytes=x.stat().st_size,kind=t['kind']))
 cache=[]
 for base in ['src','tests','scripts','__pycache__','.pytest_cache','.tmp/history-tests']:
  p=R/base
  if not p.exists():continue
  for x in p.rglob('*'):
   if x.is_file() and (x.suffix=='.pyc' or base in {'.pytest_cache','.tmp/history-tests'}):
    rel=x.relative_to(R).as_posix()
    if rel not in pinned_refs and rel not in text_refs:cache.append(dict(path=rel,bytes=x.stat().st_size,sha256=sha(x),kind='REGENERABLE_INTERPRETER_TEST_CACHE'))
 anchors={}
 for refpath in ['artifacts/reports/financial-dstock-remaining-v1/dataset-result-ref.json','artifacts/reports/financial-dstock-remaining-v1/delivery-result-ref.json']:
  ref=read(R/refpath);p=R/ref['path']/'manifest.json';assert sha(p)==ref['manifest_sha256'];anchors[p.relative_to(R).as_posix()]=sha(p)
 for name in ['financial-dstock-gap-recovery-v1','financial-dstock-remaining-v1','financial-one-gap-review-v1']:
  p=R/'artifacts/reports'/name/'evidence-manifest.json'
  if p.exists():
   anchors[p.relative_to(R).as_posix()]=sha(p)
   obj=read(p)
   for n,h in obj.get('files',obj).items():
    target=R/n if 'files' in obj else p.parent/n
    assert sha(target)==h,(name,n)
 result=dict(status='PLANNED_NOT_PRUNED',targets=targets,archive_files=files,cache_files=cache,held=held,scanned_metadata_files=len(scan),archive_bytes=sum(x['bytes'] for x in files),cache_bytes=sum(x['bytes'] for x in cache),anchors=anchors)
 dump(OUT/'plan.json',result);print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in result.items() if k not in ['anchors','held']},ensure_ascii=False),flush=True)
def pack():
 p=read(OUT/'plan.json');ARC.mkdir(parents=True,exist_ok=True);z=ARC/'historical-reports-and-scratch.zip'
 if z.exists():raise ValueError('Archive exists; use check, do not overwrite')
 with zipfile.ZipFile(z,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for row in p['archive_files']:
   path=safe(row['path']);assert sha(path)==row['sha256'];out.write(path,row['path'])
 check()
def check():
 p=read(OUT/'plan.json');z=ARC/'historical-reports-and-scratch.zip'
 with zipfile.ZipFile(z) as pack:
  assert pack.testzip() is None
  assert set(pack.namelist())=={x['path'] for x in p['archive_files']}
  for row in p['archive_files']:
   assert hashlib.sha256(pack.read(row['path'])).hexdigest()==row['sha256']
 for n,h in p['anchors'].items():assert sha(safe(n))==h,n
 result=dict(status='VERIFIED_READY_FOR_PRUNE',archive=z.relative_to(R).as_posix(),archive_sha256=sha(z),plan_sha256=sha(OUT/'plan.json'),files=len(p['archive_files']),cache_files=len(p['cache_files']),archive_bytes=z.stat().st_size)
 dump(OUT/'ready.json',result);print(json.dumps(result),flush=True)
def restore():
 p=read(OUT/'plan.json');ready=read(OUT/'ready.json');z=safe(ready['archive']);assert sha(z)==ready['archive_sha256']
 assert sha(OUT/'plan.json')==ready['plan_sha256'],'Cleanup plan changed'
 with zipfile.ZipFile(z) as pack:
  for row in p['archive_files']:
   target=safe(row['path']);raw=pack.read(row['path']);assert hashlib.sha256(raw).hexdigest()==row['sha256']
   if target.exists():assert sha(target)==row['sha256'];continue
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 print('RESTORED exact archive paths; regenerable caches are not restored.')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['plan','pack','check','restore']);args=a.parse_args();globals()[args.mode]()
