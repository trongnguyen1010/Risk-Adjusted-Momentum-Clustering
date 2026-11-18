"""Export reviewed R1 outputs for explicit, non-promoted presentation. Never fit."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
from statistics import fmean


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def export(root,run_path,output='data/web/delta-r1-preview-v1'):
    root=Path(root).resolve();run=(root/run_path).resolve()
    if not run.is_relative_to(root):raise ValueError('Source run outside project')
    seal=json.loads((run/'manifest.json').read_bytes());summary=json.loads((run/'summary.json').read_bytes())
    if summary['status']!='COMPLETE_R1_DESCRIPTIVE_NOT_PROMOTED' or summary['failures']:raise ValueError('Only complete, non-promoted R1 runs may be previewed')
    if sha(run/'summary.json')!=seal['summary.json']:raise ValueError('Run summary changed')
    base=root/'data/web/delta-intelligence-v1';baseline=json.loads((base/'manifest.json').read_bytes())
    database=base/'terminal.sqlite'
    if sha(database)!=baseline['database_sha256']:raise ValueError('Baseline database changed')
    db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    meta=json.loads(db.execute("SELECT value FROM metadata WHERE key='overview'").fetchone()[0])
    shortlist=json.loads((run/'shortlist.json').read_bytes())
    if sha(run/'shortlist.json')!=seal['shortlist.json']:raise ValueError('Shortlist changed')
    sources={str((run/'manifest.json').relative_to(root)).replace('\\','/'):sha(run/'manifest.json'),
             'data/web/delta-intelligence-v1/manifest.json':sha(base/'manifest.json'),
             'data/web/delta-intelligence-v1/terminal.sqlite':baseline['database_sha256'],
             'src/delta_t1/product/research_preview.py':sha(root/'src/delta_t1/product/research_preview.py')}
    variants={};models=0
    for kind,candidates in shortlist.items():
        variants[kind]={}
        native=[r[0] for r in db.execute('SELECT date FROM snapshots WHERE kind=? ORDER BY date',(kind,))]
        for candidate in candidates:
            recipe,k=candidate['recipe'],candidate['k'];version=f'r1:{recipe}:k{k}:{summary["run_id"]}'
            item=dict(version=version,label=f'R1 {recipe} · k={k} · chưa promote',status='NOT_PROMOTED',recipe=recipe,k=k,
                      frequency=meta['model_configs'][kind]['frequency'],features=meta['model_configs'][kind]['features'],
                      scaling={'P1':'Yeo–Johnson + StandardScaler','P2':'Quantile normal','P3':'Signed log + RobustScaler'}[recipe],
                      source_run=summary['run_id'],snapshots={},strict_pit_ready=False,research_ready=False)
            for day in native:
                relative=f'models/{kind}-{day}-{recipe}-k{k}-s42.json';path=run/relative
                if sha(path)!=seal[relative]:raise ValueError('Source model changed: '+relative)
                sources[path.relative_to(root).as_posix()]=seal[relative]
                model=json.loads(path.read_bytes());fields=item['features']
                if model['feature_order']!=fields:raise ValueError('Feature order mismatch')
                points=[dict(r) for r in db.execute('SELECT * FROM observations WHERE kind=? AND date=? ORDER BY ticker',(kind,day))]
                if model['symbols']!=[p['ticker'] for p in points] or model['security_ids']!=[p['security_id'] for p in points]:raise ValueError('Preview cohort/identity mismatch')
                labels=model['labels'];counts=Counter(labels)
                if len(labels)!=len(points) or {str(i):n for i,n in counts.items()}!=model['metrics']['sizes']:raise ValueError('Assignment counts mismatch')
                profiles=[]
                for profile in model['profiles']:
                    chosen=[json.loads(p['features']) for p,label in zip(points,labels) if label==profile['cluster']]
                    if len(chosen)!=profile['size']:raise ValueError('Profile size mismatch')
                    profiles.append(dict(kind=kind,date=day,**profile,means={f:fmean(p[f] for p in chosen) for f in fields}))
                metrics=dict(model['metrics'],min_cluster_size=min(counts.values()),quality_status='NOT_PROMOTED_SOURCE_USEFULNESS_REVIEW_PENDING')
                snapshot=dict(kind=kind,date=day,n=len(points),k=k,sizes={str(i):n for i,n in counts.items()},metrics=metrics,
                              scope='R1_EX_POST_DESCRIPTIVE_NOT_PROMOTED_NOT_PIT',version=version)
                item['snapshots'][day]=dict(snapshot=snapshot,profiles=profiles,symbols=model['symbols'],security_ids=model['security_ids'],labels=labels,peer_examples=model['peer_examples'])
                models+=1
            variants[kind][version]=item
    db.close()
    payload=dict(version='delta-r1-preview-v1',baseline_database_sha256=baseline['database_sha256'],source_run=summary['run_id'],
                 default='BASELINE_UNCHANGED',promotion_status='NOT_PROMOTED',variants=variants)
    body=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    manifest=dict(version=payload['version'],database_sha256=baseline['database_sha256'],data_sha256=hashlib.sha256(body).hexdigest(),
                  models=models,source_run=summary['run_id'],sources=sources,promotion_status='NOT_PROMOTED')
    encoded=json.dumps(manifest,sort_keys=True,indent=2).encode('utf-8');identity=hashlib.sha256(encoded).hexdigest()[:20]
    target=(root/output/identity).resolve()
    if not target.is_relative_to(root):raise ValueError('Output outside project')
    if target.exists():
        if (target/'manifest.json').read_bytes()!=encoded or sha(target/'presentation.json')!=manifest['data_sha256']:raise ValueError('Immutable preview output conflict')
    else:
        target.mkdir(parents=True);(target/'presentation.json').write_bytes(body);(target/'manifest.json').write_bytes(encoded)
    return dict(manifest=(target/'manifest.json').relative_to(root).as_posix(),manifest_sha256=sha(target/'manifest.json'),
                file=(target/'presentation.json').relative_to(root).as_posix(),file_sha256=manifest['data_sha256'],models=models)
