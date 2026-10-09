"""Explicit financial retention: inventory, verified cold archives, exact restore.

Reports and active dependencies stay local. Archived bytes are preserved unchanged;
physical pruning is done by the PowerShell launcher after verification.
"""
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path, PurePosixPath


def sha_file(path):
    sha=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):sha.update(chunk)
    return sha.hexdigest()


def safe_root(workspace,name):
    if not re.fullmatch('[A-Za-z0-9_-]+',name):raise ValueError('invalid financial root name')
    workspace=Path(workspace).resolve()
    base=(workspace/'data/financial').resolve()
    if not base.is_relative_to(workspace/'data'):raise ValueError('financial base outside workspace data')
    target=(base/name).resolve()
    if target.parent!=base or target==base:raise ValueError('target outside financial directory')
    return target


def files(folder):
    """scandir uses Windows directory metadata; refuse symlinks and reparse points."""
    folder=Path(folder)
    if folder.is_symlink() or getattr(folder.stat(),'st_file_attributes',0)&0x400:
        raise ValueError('reparse root requires review')
    stack=[str(folder)];output=[]
    while stack:
        directory=stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                info=entry.stat(follow_symlinks=False)
                if entry.is_symlink() or getattr(info,'st_file_attributes',0)&0x400:
                    raise ValueError('reparse entry requires review')
                if entry.is_dir(follow_symlinks=False):stack.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    output.append(dict(path=Path(entry.path).relative_to(folder).as_posix(),
                                       bytes=info.st_size,mtime_ns=info.st_mtime_ns))
    return sorted(output,key=lambda row:row['path'])


def financial_refs(text):
    text=re.sub('/+','/',text.replace('\\','/'))
    return set(re.findall(r'data/financial/([A-Za-z0-9_-]+)',text))


def inventory(workspace,active_plan='configs/data/financial_execution_plan_v9.json'):
    workspace=Path(workspace).resolve();base=workspace/'data/financial';items=[];graph={}
    for folder in sorted(base.iterdir()):
        if not folder.is_dir():continue
        rows=files(folder);refs=set()
        for row in rows:
            path=PurePosixPath(row['path'])
            if (path.suffix=='.json' and path.name!='manifest.json' and not path.name.endswith('.ocr.json')
                and not set(path.parts[:-1])&{'raw','tasks','ledger','code','pdf-jobs','text'}):
                refs.update(financial_refs((folder/row['path']).read_text(encoding='utf-8-sig')))
        graph[folder.name]=refs-{folder.name}
        items.append(dict(name=folder.name,files=len(rows),bytes=sum(r['bytes'] for r in rows),dependency_roots=sorted(graph[folder.name])))
    seeds={'trial-epochs','source_benchmark_20261008_v1'};pending=[workspace/active_plan];seen=set()
    integration=workspace/'configs/data/financial_active_integration_v1.json'
    if integration.is_file():pending.append(integration)
    while pending:
        file=pending.pop().resolve()
        if file in seen:continue
        if not file.is_relative_to(workspace/'configs'):raise ValueError('active policy outside configs')
        seen.add(file);text=file.read_text(encoding='utf-8-sig');seeds.update(financial_refs(text))
        pending.extend(workspace/p for p in re.findall(r'configs/data/[A-Za-z0-9_.-]+\.json',text)
                       if (workspace/p).is_file() and (workspace/p).resolve() not in seen)
    keep=set(seeds);pending=list(seeds)
    while pending:
        name=pending.pop()
        for dep in graph.get(name,set()):
            if dep not in keep:keep.add(dep);pending.append(dep)
    # The completed trial50 is a closed source benchmark, never an active reference
    # calculator dependency. Keep its epoch pointer; exact resume requires restore.
    closed='crawl_50_live_20261007_v1'
    other_consumers=[name for name,refs in graph.items() if closed in refs and name!='trial-epochs' and name in keep]
    if closed in keep and not other_consumers and safe_root(workspace,closed).is_dir():
        run=safe_root(workspace,closed)
        status=json.loads((run/'results.json').read_bytes())
        if (run/'manifest.json').is_file() and status['accepted_facts']==0 and not status['trial_totals']['boundary']:
            keep.remove(closed)
    for item in items:item['action']='KEEP_ACTIVE_DEPENDENCY' if item['name'] in keep else 'ARCHIVE_INACTIVE'
    return dict(roots=len(items),files=sum(r['files'] for r in items),bytes=sum(r['bytes'] for r in items),
                active_seeds=sorted(seeds),policy_configs=sorted(p.relative_to(workspace).as_posix() for p in seen),items=items)


def checked_member(name):
    path=PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in ('','..','.') or ':' in part or '\\' in part for part in path.parts):
        raise ValueError('unsafe archive member')
    if str(path)!=name:raise ValueError('noncanonical archive member')
    return path


def archive_root(workspace,name,archive_dir):
    workspace=Path(workspace).resolve();target=safe_root(workspace,name)
    destination=Path(archive_dir).resolve()
    if not destination.is_relative_to(workspace/'artifacts/archives'):raise ValueError('archive outside archive area')
    destination.mkdir(parents=True,exist_ok=True);archive=destination/(name+'.zip')
    listing=files(target);entries={}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as pack:
        for row in listing:
            relative=row['path'];checked_member(relative);sha=hashlib.sha256();size=0
            with (target/relative).open('rb') as source,pack.open('files/'+relative,'w',force_zip64=True) as sink:
                while chunk:=source.read(1024*1024):sha.update(chunk);size+=len(chunk);sink.write(chunk)
            if size!=row['bytes']:raise ValueError('source changed while archiving')
            entries[relative]=dict(sha256=sha.hexdigest(),bytes=size,mtime_ns=row['mtime_ns'])
        pack.writestr('archive-manifest.json',json.dumps(dict(version='financial-cold-archive-v1',original_root='data/financial/'+name,
            files=entries),ensure_ascii=False,sort_keys=True,separators=(',',':')))
    verified=verify_archive(archive)
    return dict(name=name,archive=archive.relative_to(workspace).as_posix(),archive_sha256=sha_file(archive),
        original_files=len(entries),original_bytes=sum(r['bytes'] for r in entries.values()),archive_bytes=archive.stat().st_size,
        verified=True,original_manifest_sha256=entries.get('manifest.json',{}).get('sha256'),manifest=verified)


def verify_archive(archive):
    with zipfile.ZipFile(archive) as pack:
        manifest=json.loads(pack.read('archive-manifest.json'))
        if manifest['version']!='financial-cold-archive-v1':raise ValueError('wrong archive contract')
        expected={'archive-manifest.json'}|{'files/'+name for name in manifest['files']}
        if len(pack.namelist())!=len(expected) or set(pack.namelist())!=expected:raise ValueError('archive inventory mismatch')
        for name,entry in manifest['files'].items():
            checked_member(name);sha=hashlib.sha256();size=0
            with pack.open('files/'+name) as stream:
                while chunk:=stream.read(1024*1024):sha.update(chunk);size+=len(chunk)
            if sha.hexdigest()!=entry['sha256'] or size!=entry['bytes']:raise ValueError('archive checksum mismatch')
    return manifest


def verify_before_prune(workspace,record):
    workspace=Path(workspace).resolve();archive=(workspace/record['archive']).resolve()
    if not archive.is_relative_to(workspace/'artifacts/archives') or sha_file(archive)!=record['archive_sha256']:
        raise ValueError('archive pin changed')
    manifest=verify_archive(archive);folder=safe_root(workspace,record['name'])
    if manifest['original_root']!='data/financial/'+record['name']:raise ValueError('archive/source identity mismatch')
    current=files(folder)
    if {row['path'] for row in current}!=set(manifest['files']):raise ValueError('source inventory changed')
    for row in current:
        entry=manifest['files'][row['path']]
        if row['bytes']!=entry['bytes'] or sha_file(folder/row['path'])!=entry['sha256']:
            raise ValueError('source changed; pruning forbidden')
    return dict(status='PRUNE_READY',name=record['name'],absolute_path=str(folder),archive_sha256=record['archive_sha256'])


def restore(workspace,archive,expected_sha256=None):
    workspace=Path(workspace).resolve();archive=Path(archive).resolve()
    if not archive.is_relative_to(workspace/'artifacts/archives'):raise ValueError('archive outside archive area')
    if expected_sha256 is not None and sha_file(archive)!=expected_sha256:raise ValueError('archive pin changed')
    manifest=verify_archive(archive)
    root=PurePosixPath(manifest['original_root'])
    if len(root.parts)!=3 or root.parts[:2]!=('data','financial'):raise ValueError('unsafe original root')
    target=safe_root(workspace,root.name)
    target.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(archive) as pack:
        for name,entry in manifest['files'].items():
            path=checked_member(name);file=target.joinpath(*path.parts);file.parent.mkdir(parents=True,exist_ok=True)
            with pack.open('files/'+name) as source,file.open('xb') as sink:
                while chunk:=source.read(1024*1024):sink.write(chunk)
            os.utime(file,ns=(entry['mtime_ns'],entry['mtime_ns']))
    return dict(status='RESTORED_VERIFIED_ARCHIVE',root=str(target),files=len(manifest['files']))
