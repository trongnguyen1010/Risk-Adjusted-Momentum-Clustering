"""Inventory/verify/restore-map for exact same-volume archival of historical trees."""
import argparse,csv,hashlib,json,os,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'artifacts/repository/financial-history-storage-20261023';A=R/'artifacts/archives/financial-history-20261023'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  while b:=s.read(1024*1024):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def safe(rel):
 p=Path(rel)
 if p.is_absolute() or '..' in p.parts or ':' in rel or '\\' in rel:raise ValueError(rel)
 target=R/p
 if not target.resolve().is_relative_to(R) or target.resolve()==R:raise ValueError(rel)
 for x in [target,*target.parents]:
  if x==R:break
  if x.exists() and (x.is_symlink() or getattr(x.stat(),'st_file_attributes',0)&0x400):raise ValueError('reparse '+rel)
 return target
def inventory(root):
 result=[];stack=[root]
 while stack:
  with os.scandir(stack.pop()) as entries:
   for e in entries:
    st=e.stat(follow_symlinks=False)
    if e.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:raise ValueError('reparse')
    if e.is_dir(follow_symlinks=False):stack.append(Path(e.path))
    elif e.is_file(follow_symlinks=False):result.append([Path(e.path).relative_to(root).as_posix(),st.st_size,st.st_mtime_ns,st.st_ino,st.st_dev])
 return sorted(result)
def anchor_files():
 anchors={};paths=[]
 for n in ['dataset-result-ref.json','delivery-result-ref.json']:
  ref=read(R/'artifacts/reports/financial-dstock-remaining-v1'/n);folder=R/ref['path'];assert sha(folder/'manifest.json')==ref['manifest_sha256'];paths.append(folder/'manifest.json')
  for name,h in read(folder/'manifest.json').items():assert sha(folder/name)==h;paths.append(folder/name)
  if (folder/'input-pins.json').exists():
   for name,h in read(folder/'input-pins.json').items():assert sha(R/name)==h;paths.append(R/name)
 H=R/'data/handoffs/financial-reference-2016-2025';m=read(H/'handoff-manifest.json')
 for n,h in m['files'].items():assert sha(H/n)==h['sha256'];paths.append(H/n)
 paths.append(H/'handoff-manifest.json')
 for p in set(paths):anchors[p.relative_to(R).as_posix()]=sha(p)
 for name in ['history_dstock_recovery_v3','history_dstock_recovery_v4']:
  contract=read(R/'data/financial'/name/'contract.json')
  for n,h in contract.get('boundary_pins',{}).items():assert sha(R/n)==h,n;anchors[n]=h
 return anchors
def plan():
 if (O/'plan.json').exists():raise ValueError('Plan exists; do not reset')
 ref=read(R/'artifacts/reports/financial-dstock-remaining-v1/dataset-result-ref.json');f=R/ref['path'];pins=read(f/'input-pins.json');anchors=anchor_files();text='\n'.join(anchors)+'\n'+(f/'features.csv').read_text(encoding='utf-8-sig')
 keep_data=set(re.findall(r'data/financial/([^/\s,\"]+)',text))
 keep_data.update(['history_dstock_metadata_review_v1','history_template_contract_v1','history_precision_review_v1','history_recovery_readiness_v1'])
 keep_data.update(p.name for p in (R/'data/financial').iterdir() if p.is_dir() and any(w in p.name.lower() for w in ['epoch','boundary','registry']))
 keep_reports=set(re.findall(r'artifacts/reports/([^/\s,\"]+)',text))|{'financial-dstock-remaining-v1','financial-dstock-gap-recovery-v1','financial-one-gap-review-v1','financial-cafef-pilot5-execution-v1','financial-indicators-handbook-v1','financial-cafef-rediscovery-v2','m1-market-foundation-v1'}
 targets=[];kept=[]
 for base,keep in [('data/financial',keep_data),('artifacts/reports',keep_reports)]:
  for p in sorted((R/base).iterdir()):
   if not p.is_dir():continue
   rel=p.relative_to(R).as_posix()
   if p.name in keep:kept.append(dict(path=rel,reason='CURRENT_INPUT_OR_PROVENANCE_CONTROL' if base.startswith('data') else 'CURRENT_REPORT_OR_CONTROL'));continue
   dest=A/rel;assert not dest.exists();safe(rel);safe(dest.relative_to(R).as_posix());inv=inventory(p);st=p.stat();key=sha_string(rel)[:16]
   invpath=O/'inventories'/(key+'.json');dump(invpath,inv)
   # Preserve inventory and directory identity; pin manifests for content fallback.
   metadata={}
   for q in p.iterdir():
    if q.is_file() and q.suffix in {'.json','.jsonl','.md','.ps1'}:metadata[q.relative_to(p).as_posix()]=sha(q)
   for sub in ['network']:
    if (p/sub).is_dir():
     for q in (p/sub).rglob('*'):
      if q.is_file():metadata[q.relative_to(p).as_posix()]=sha(q)
   targets.append(dict(source=rel,destination=dest.relative_to(R).as_posix(),inventory=invpath.relative_to(R).as_posix(),inventory_sha256=sha(invpath),directory_inode=st.st_ino,device=st.st_dev,files=len(inv),bytes=sum(x[1] for x in inv),metadata_hashes=metadata))
   if len(targets)%25==0:print(json.dumps(dict(phase='INVENTORY',trees=len(targets))),flush=True)
 dump(O/'plan.json',dict(version='financial-history-storage-v1',archive_root=A.relative_to(R).as_posix(),targets=targets,kept=kept,anchors=anchors,before_data_folders=len(list((R/'data/financial').glob('*/'))),before_report_folders=len(list((R/'artifacts/reports').glob('*/')))))
 print(json.dumps(dict(phase='PLANNED',move_trees=len(targets),kept_trees=len(kept),files=sum(x['files'] for x in targets),bytes=sum(x['bytes'] for x in targets))),flush=True)
def sha_string(s):return hashlib.sha256(s.encode()).hexdigest()
def verify_tree(row,dest):
 assert sha(R/row['inventory'])==row['inventory_sha256'];actual=inventory(dest);assert actual==read(R/row['inventory']),row['source'];st=dest.stat();same=st.st_ino==row['directory_inode'] and st.st_dev==row['device']
 for n,h in row['metadata_hashes'].items():assert sha(dest/n)==h,(row['source'],n)
 if not same:
  # Some Windows provider moves can give the directory a new ID. Accept only
  # complete cryptographic coverage from a manifest pinned BEFORE the move.
  assert 'manifest.json' in row['metadata_hashes'],'Unpinned directory ID change'
  obj=read(dest/'manifest.json');members=obj.get('files',obj);assert isinstance(members,dict)
  assert {x[0] for x in actual} <= set(members)|{'manifest.json'},'Incomplete content proof'
  for n,h in members.items():assert re.fullmatch('[0-9a-f]{64}',h) and sha(dest/n)==h,n
 return same
def check(source):
 p=read(O/'plan.json');matches=[x for x in p['targets'] if x['source']==source]
 if len(matches)!=1:raise ValueError('Exact planned source required')
 row=matches[0];dest=safe(row['destination']);assert dest.is_dir();verify_tree(row,dest)
 print('PASS archive inventory and content proof: '+source)
def verify():
 p=read(O/'plan.json');rows=[];fallbacks=[]
 for row in p['targets']:
  source=safe(row['source']);dest=safe(row['destination']);assert not source.exists() and dest.is_dir(),row['source']
  if not verify_tree(row,dest):fallbacks.append(row['source'])
  rows.append(dict(original_prefix=row['source'],archive_prefix=row['destination'],availability='ARCHIVED_TREE_EXACT_RESTORE',files=row['files'],bytes=row['bytes']))
 for n,h in p['anchors'].items():assert sha(R/n)==h,n
 dump(A/'availability.json',dict(version='financial-history-storage-v1',prefixes=rows))
 result=dict(status='PASS_EXACT_SAME_VOLUME_ARCHIVAL',trees_moved=len(rows),data_folders_before=p['before_data_folders'],data_folders_after=len(list((R/'data/financial').glob('*/'))),report_folders_before=p['before_report_folders'],report_folders_after=len(list((R/'artifacts/reports').glob('*/'))),files_archived=sum(x['files'] for x in rows),bytes_archived=sum(x['bytes'] for x in rows),current_anchors_verified=len(p['anchors']),directory_id_unchanged_trees=len(rows)-len(fallbacks),complete_prepinned_content_manifest_fallbacks=fallbacks,file_sizes_and_mtimes_unchanged=True,metadata_and_network_hashes_unchanged=True,current_dataset_unchanged=True,storage_bytes_reclaimed_claim=False,network_requests=0,model_refit=False)
 dump(O/'verification.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['plan','verify','check']);parser.add_argument('--source');args=parser.parse_args()
 if args.mode=='check':check(args.source)
 else:globals()[args.mode]()
