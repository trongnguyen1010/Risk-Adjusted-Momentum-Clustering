"""Exact-byte cold storage for closed, derived CafeF candidates; never raw/journal."""
import argparse,hashlib,json,os,sys,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
O=R/'artifacts/repository/financial-cache-archive-20261023'
A=R/'artifacts/archives/financial-cache-20261023'
TARGETS={'500':'history_acquisition_total500_bulk_v1','800':'history_acquisition_total800_v1','1100':'history_acquisition_total1100_v2','1400':'history_acquisition_total1400_v2'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  while b:=s.read(1024*1024):h.update(b)
 return h.hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(p):return json.loads(p.read_bytes())
def safe(rel):
 q=PurePosixPath(rel)
 if q.is_absolute() or '..' in q.parts or ':' in rel or '\\' in rel:raise ValueError(rel)
 p=R.joinpath(*q.parts);resolved=p.resolve()
 if resolved==R or not resolved.is_relative_to(R):raise ValueError(rel)
 for parent in [p,*p.parents]:
  if parent==R:break
  if parent.exists() and (parent.is_symlink() or getattr(parent.stat(),'st_file_attributes',0)&0x400):raise ValueError('reparse: '+rel)
 return p
def listing(folder):
 rows=[];stack=[folder]
 while stack:
  with os.scandir(stack.pop()) as it:
   for e in it:
    st=e.stat(follow_symlinks=False)
    if e.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:raise ValueError('reparse')
    if e.is_dir(follow_symlinks=False):stack.append(Path(e.path))
    elif e.is_file(follow_symlinks=False):rows.append(dict(path=Path(e.path).relative_to(folder).as_posix(),bytes=st.st_size,mtime_ns=st.st_mtime_ns))
 return sorted(rows,key=lambda x:x['path'])
def anchors():
 result={}
 for n in ['dataset-result-ref.json','delivery-result-ref.json']:
  ref=read(R/'artifacts/reports/financial-dstock-remaining-v1'/n);p=R/ref['path']/'manifest.json';assert sha(p)==ref['manifest_sha256'];result[p.relative_to(R).as_posix()]=sha(p)
 for n in ['handoff-manifest.json','financial-ratios-1172-symbols-2016-2025.csv','securities-1172-symbols.csv','missing-periods-review.csv']:
  p=R/'data/handoffs/financial-reference-2016-2025'/n;result[p.relative_to(R).as_posix()]=sha(p)
 return result
def controls(root):
 paths=[p for p in root.iterdir() if p.is_file()]
 if (root/'network').exists():paths.extend(p for p in (root/'network').rglob('*') if p.is_file())
 return {p.relative_to(R).as_posix():sha(p) for p in paths}
def plan():
 if (O/'plan.json').exists():raise ValueError('Existing plan: do not reset')
 rows=[]
 for label,name in TARGETS.items():
  root=safe('data/financial/'+name);folder=safe('data/financial/'+name+'/candidates')
  status=read(root/'pipeline-status.json');stage=status.get('stage',status.get('phase',''))
  terminal=any(x in stage.upper() for x in ['COMPLETE','DONE','FINISH']) or stage=='PARTIAL_REVIEW_REQUIRED'
  if not terminal:raise ValueError(('nonterminal',name,stage))
  sealed=safe(status.get('detail','')+'/manifest.json')
  if not sealed.is_file():raise ValueError('Terminal status lacks sealed result: '+name)
  members=listing(folder);row=dict(label=label,root=folder.relative_to(R).as_posix(),files=len(members),bytes=sum(x['bytes'] for x in members),closed_stage=stage,archive='artifacts/archives/financial-cache-20261023/cafef-batch-'+label+'-normalized-cache.zip',controls=controls(root))
  dump(O/(label+'-inventory.json'),members);row['inventory_sha256']=sha(O/(label+'-inventory.json'));rows.append(row)
  print(json.dumps(dict(phase='PLANNED',batch=label,files=row['files'],bytes=row['bytes'])),flush=True)
 dump(O/'plan.json',dict(version='financial-derived-cache-archive-v1',scope='CLOSED_CANDIDATE_CACHE_ONLY_RAW_RECEIPTS_JOURNALS_RETAINED',targets=rows,anchors=anchors(),no_network=True))
def target(label):
 p=read(O/'plan.json');row=next(x for x in p['targets'] if x['label']==label);assert sha(O/(label+'-inventory.json'))==row['inventory_sha256'];return p,row
def pack(label):
 p,row=target(label);folder=safe(row['root']);archive=safe(row['archive']);archive.parent.mkdir(parents=True,exist_ok=True)
 if archive.exists():raise ValueError('Archive exists: verify before resume, do not overwrite')
 inv=read(O/(label+'-inventory.json'));assert listing(folder)==inv,'source inventory changed';entries={}
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
  for i,item in enumerate(inv,1):
   source=folder/item['path'];h=hashlib.sha256();size=0
   with source.open('rb') as src,z.open('files/'+item['path'],'w',force_zip64=True) as dst:
    while chunk:=src.read(1024*1024):h.update(chunk);size+=len(chunk);dst.write(chunk)
   assert size==item['bytes'];entries[item['path']]=dict(item,sha256=h.hexdigest())
   if i%2000==0:print(json.dumps(dict(phase='PACKING',batch=label,completed=i,total=len(inv))),flush=True)
  z.writestr('archive-manifest.json',json.dumps(dict(version='financial-derived-cache-archive-v1',original_root=row['root'],files=entries),ensure_ascii=False,separators=(',',':')))
 dump(O/(label+'-packed.json'),dict(archive=row['archive'],archive_sha256=sha(archive),files=len(entries),bytes=row['bytes'],archive_bytes=archive.stat().st_size,plan_sha256=sha(O/'plan.json')))
 verify(label)
def verify(label):
 p,row=target(label);meta=read(O/(label+'-packed.json'));archive=safe(row['archive']);assert sha(archive)==meta['archive_sha256'];assert sha(O/'plan.json')==meta['plan_sha256']
 with zipfile.ZipFile(archive) as z:
  m=json.loads(z.read('archive-manifest.json'));assert m['original_root']==row['root'];assert m['version']=='financial-derived-cache-archive-v1'
  assert set(z.namelist())=={'archive-manifest.json'}|{'files/'+n for n in m['files']}
  assert len(m['files'])==row['files'];assert sum(x['bytes'] for x in m['files'].values())==row['bytes']
  for i,(name,item) in enumerate(m['files'].items(),1):
   q=PurePosixPath(name);assert not q.is_absolute() and '..' not in q.parts and ':' not in name and '\\' not in name
   h=hashlib.sha256();size=0
   with z.open('files/'+name) as s:
    while chunk:=s.read(1024*1024):h.update(chunk);size+=len(chunk)
   assert h.hexdigest()==item['sha256'] and size==item['bytes'],name
   if i%5000==0:print(json.dumps(dict(phase='VERIFYING',batch=label,completed=i,total=row['files'])),flush=True)
 for n,h in {**p['anchors'],**row['controls']}.items():assert sha(safe(n))==h,n
 folder=safe(row['root'])
 if folder.exists():assert listing(folder)==read(O/(label+'-inventory.json')),'source changed after packing'
 dump(O/(label+'-ready.json'),dict(meta,status='ARCHIVE_AND_SOURCE_VERIFIED',root=row['root'],absolute_root=str(folder),controls=row['controls'],anchors=p['anchors']))
 print(json.dumps(dict(phase='READY',batch=label,files=row['files'],archive_bytes=meta['archive_bytes'])),flush=True)
def restore(label):
 p,row=target(label);meta=read(O/(label+'-packed.json'));zpath=safe(row['archive']);assert sha(zpath)==meta['archive_sha256'];assert sha(O/'plan.json')==meta['plan_sha256'];folder=safe(row['root'])
 if folder.exists():raise ValueError('Restore refuses existing destination')
 with zipfile.ZipFile(zpath) as z:
  manifest=json.loads(z.read('archive-manifest.json'));assert manifest['original_root']==row['root']
  for name,item in manifest['files'].items():
   dest=safe(row['root']+'/'+name);dest.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256()
   with z.open('files/'+name) as src,dest.open('xb') as dst:
    while chunk:=src.read(1024*1024):h.update(chunk);dst.write(chunk)
   assert h.hexdigest()==item['sha256'];os.utime(dest,ns=(item['mtime_ns'],item['mtime_ns']))
 print(json.dumps(dict(phase='RESTORED',batch=label,files=row['files'])),flush=True)
def status():
 p=read(O/'plan.json');result=[]
 for row in p['targets']:
  done=(O/(row['label']+'-ready.json')).exists();result.append(dict(batch=row['label'],files=row['files'],source_present=safe(row['root']).exists(),archive_verified=done))
 print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['plan','pack','verify','restore','status']);a.add_argument('--batch',choices=list(TARGETS));arg=a.parse_args()
 if arg.mode in ['plan','status']:globals()[arg.mode]()
 else:
  if not arg.batch:a.error('--batch required')
  globals()[arg.mode](arg.batch)
