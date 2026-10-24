"""Bounded R1 sensitivity of frozen A/B/C; independent from product model selection."""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

from ..clustering.reference_preprocessing import prepare, replay
from ..evaluation.reference_scorecard import score


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def dump(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,sort_keys=True,allow_nan=False)


def load_cohorts(root):
    bundle=root/'data/web/delta-intelligence-v1'
    manifest=json.loads((bundle/'manifest.json').read_bytes())
    if sha(bundle/'terminal.sqlite')!=manifest['database_sha256']:raise ValueError('Presentation source checksum mismatch')
    # Verify upstream pins before using the immutable feature copies.
    for relative,pin in manifest['sources'].items():
        if sha(root/relative)!=pin['sha256']:raise ValueError('Upstream source changed: '+relative)
    connection=sqlite3.connect((bundle/'terminal.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    connection.execute('PRAGMA query_only=ON');connection.row_factory=sqlite3.Row
    metadata=json.loads(connection.execute("SELECT value FROM metadata WHERE key='overview'").fetchone()[0])
    groups=defaultdict(list)
    for row in connection.execute('SELECT * FROM observations ORDER BY kind,date,ticker'):
        record=dict(row);record['features']=json.loads(record['features']);groups[row['kind'],row['date']].append(record)
    snapshots=[dict(row) for row in connection.execute('SELECT * FROM snapshots ORDER BY kind,date')]
    connection.close()
    pins={'data/web/delta-intelligence-v1/manifest.json':sha(bundle/'manifest.json'),'data/web/delta-intelligence-v1/terminal.sqlite':manifest['database_sha256']}
    pins.update({p:v['sha256'] for p,v in manifest['sources'].items()})
    for snapshot in snapshots:
        key=snapshot['kind'],snapshot['date'];group=groups[key]
        if len(group)!=snapshot['n'] or len({r['ticker'] for r in group})!=len(group):raise ValueError('Cohort count/identity mismatch')
    return groups,metadata['model_configs'],snapshots,pins


def validate(config):
    fixed=dict(version='delta-upgrade-r1-v1',mode='EX_POST_DESCRIPTIVE_SENSITIVITY_NOT_PIT',screening_years=list(range(2019,2024)),
        recipes=['P1','P2','P3'],k=list(range(2,9)),seed=42,additional_seeds=list(range(9)),n_init=20,max_iter=300,
        shortlist_per_family=2,screening_fit_cap=315,seed_fit_cap=270,combined_block_variance=.5,
        tiny_minimum=10,tiny_fraction=.01,dominant_share=.9,feature_contribution_flag=.8,screening_pass_fraction=.8,median_seed_ari=.8,
        clipping=False,imputation=False,pca=False,new_acquisition=False,research_ready=False,strict_pit_ready=False,backtest_allowed=False,holdout_claim=False)
    for key,value in fixed.items():
        if config.get(key)!=value:raise ValueError('Protocol changed; review required: '+key)
    if config.get('owner_approval',{}).get('status')!='APPROVED':raise ValueError('MANUAL_REVIEW_REQUIRED')


def run(root,config_path='configs/experiments/delta_upgrade_r1_v1.json',recover=None):
    import numpy as np
    import scipy, sklearn
    from sklearn.cluster import KMeans
    from sklearn.metrics import pairwise_distances,adjusted_rand_score,normalized_mutual_info_score
    from threadpoolctl import threadpool_limits
    root=Path(root).resolve();config=json.loads((root/config_path).read_bytes());validate(config)
    groups,models,baseline,pins=load_cohorts(root)
    for relative in [config_path,'src/delta_t1/experiments/upgrade_reference.py','src/delta_t1/clustering/reference_preprocessing.py','src/delta_t1/evaluation/reference_scorecard.py']:
        pins[relative]=sha(root/relative)
    recovery=None
    if recover:
        recovery=(root/recover).resolve()
        if not recovery.is_relative_to(root):raise ValueError('Recovery path outside project')
        previous_pins=json.loads((recovery/'input-pins.json').read_bytes())
        for relative,expected in previous_pins.items():
            if relative!='src/delta_t1/experiments/upgrade_reference.py' and pins.get(relative)!=expected:raise ValueError('Cannot recover changed source/protocol: '+relative)
        for name,expected in json.loads((recovery/'manifest.json').read_bytes()).items():
            if sha(recovery/name)!=expected:raise ValueError('Recovery artifact changed: '+name)
        pins[(recovery/'manifest.json').relative_to(root).as_posix()]=sha(recovery/'manifest.json')
    identity=hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest()[:20]
    out=root/'data/experiments/delta_upgrade_r1_v1/results'/identity
    if out.exists():
        if not (out/'manifest.json').exists():raise ValueError('Incomplete existing run preserved; inspect it before starting a new version')
        for name,expected in json.loads((out/'manifest.json').read_bytes()).items():
            if sha(out/name)!=expected:raise ValueError('Existing result changed: '+name)
        return json.loads((out/'summary.json').read_bytes())
    out.mkdir(parents=True);dump(out/'input-pins.json',pins);dump(out/'protocol.json',config)
    dump(out/'environment.json',dict(python=sys.version,numpy=np.__version__,sklearn=sklearn.__version__,scipy=scipy.__version__,threads=1))
    dump(out/'baseline-p0.json',baseline)
    records=[];failures=[];fit_count=defaultdict(int);prepared={};reference={};saved={};started=time.perf_counter()
    recovered_models=0
    if recovery:
        import shutil
        for path in sorted((recovery/'transforms').glob('*.json')):
            target=out/'transforms'/path.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(path,target)
        for path in sorted((recovery/'models').glob('*.json')):
            body=json.loads(path.read_bytes());tag=path.stem;saved[tag]=body;metrics=body['metrics']
            target=out/'models'/path.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(path,target)
            records.append(dict(kind=body['kind'],date=body['date'],recipe=body['recipe'],k=body['k'],seed=body['seed'],phase=body['phase'],**{f:metrics[f] for f in ('n','largest_share','singleton_count','tiny_count','effective_k','dominant_flag','single_feature_flag','silhouette','silhouette_reference','davies_bouldin','calinski_harabasz','converged')}))
        recovered_models=len(saved)
    def group_data(kind,day):
        cohort=groups[kind,day];fields=models[kind]['features']
        raw=np.array([[r['features'][f] for f in fields] for r in cohort],dtype=float)
        return cohort,fields,raw,8 if kind=='combined' else None
    def transformed(kind,day,recipe):
        key=(kind,day,recipe)
        if key not in prepared:
            cohort,fields,raw,width=group_data(kind,day)
            name=f'transforms/{kind}-{day}-{recipe}.json'
            if (out/name).exists():
                spec=json.loads((out/name).read_bytes());x=replay(raw,spec)
            else:
                x,spec=prepare(raw,recipe,width)
                spec['feature_order']=fields;spec['cohort_sha256']=hashlib.sha256(json.dumps([(r['ticker'],r['security_id']) for r in cohort]).encode()).hexdigest()
                dump(out/name,spec)
            d=pairwise_distances(x);np.fill_diagonal(d,0)
            prepared[key]=(x,d,name)
        return prepared[key]
    def fit(kind,day,recipe,k,seed,phase):
        cohort,fields,raw,width=group_data(kind,day)
        tag=f'{kind}-{day}-{recipe}-k{k}-s{seed}'
        # Full-series evaluation reuses screening seed42 fits, never refits P0.
        if tag in saved:return saved[tag]
        try:
            x,distances,transform_path=transformed(kind,day,recipe)
            ref_key=(kind,day)
            if ref_key not in reference:reference[ref_key]=transformed(kind,day,'P3')[1]
            estimator=KMeans(n_clusters=k,random_state=seed,n_init=config['n_init'],max_iter=config['max_iter'])
            fit_count[phase]+=1
            estimator.fit(x)
            labels=estimator.labels_
            metrics=score(x,labels,fields,distances,reference[ref_key],width)
            metrics.update(converged=bool(estimator.n_iter_<config['max_iter'] and len(set(labels))==k),iterations=int(estimator.n_iter_),inertia=float(estimator.inertia_))
            profiles=[]
            for cluster in sorted(set(labels)):
                rows=raw[labels==cluster]
                profiles.append(dict(cluster=int(cluster),size=len(rows),medians=dict(zip(fields,np.median(rows,axis=0).tolist())),quartiles={f:np.quantile(rows[:,j],[0,.25,.5,.75,1]).tolist() for j,f in enumerate(fields)}))
            # Deterministic representative examples, no stock ranking or investment claim.
            peers=[]
            for ticker in ('FPT','VNM','HPG','QBS','CAD','VTI','JOS','DNN'):
                indices=[i for i,r in enumerate(cohort) if r['ticker']==ticker]
                if not indices:continue
                i=indices[0];same=np.flatnonzero(labels==labels[i]);same=same[same!=i]
                nearest=sorted(same,key=lambda j:(distances[i,j],cohort[j]['ticker']))[:5]
                peers.append(dict(ticker=ticker,cluster=int(labels[i]),rule='Euclidean in saved snapshot recipe space; same-cluster only; ticker tie-break; self excluded',peers=[dict(ticker=cohort[j]['ticker'],distance=float(distances[i,j])) for j in nearest]))
            body=dict(kind=kind,date=day,recipe=recipe,k=k,seed=seed,phase=phase,algorithm='KMeans',transform=transform_path,
                feature_order=fields,symbols=[r['ticker'] for r in cohort],security_ids=[r['security_id'] for r in cohort],
                labels=labels.tolist(),centroids=estimator.cluster_centers_.tolist(),metrics=metrics,profiles=profiles,peer_examples=peers)
            dump(out/f'models/{tag}.json',body)
            saved[tag]=body
            records.append(dict(kind=kind,date=day,recipe=recipe,k=k,seed=seed,phase=phase,**{f:metrics[f] for f in ('n','largest_share','singleton_count','tiny_count','effective_k','dominant_flag','single_feature_flag','silhouette','silhouette_reference','davies_bouldin','calinski_harabasz','converged')}))
            return body
        except Exception as error:
            failures.append(dict(kind=kind,date=day,recipe=recipe,k=k,seed=seed,phase=phase,error=repr(error)))
            return None
    screening={kind:[] for kind in models}
    with threadpool_limits(limits=1):
        for kind in sorted(models):
            days=[s['date'] for s in baseline if s['kind']==kind and int(s['date'][:4]) in config['screening_years'] and (kind=='financial' or s['date'][5:7]=='12')]
            if len(days)!=5:raise ValueError('Expected five native year-end screening snapshots')
            for recipe in config['recipes']:
                for k in config['k']:
                    selected=[fit(kind,day,recipe,k,42,'screening') for day in days]
                    okay=[r for r in selected if r]
                    fraction=sum(r['metrics']['converged'] and not r['metrics']['dominant_flag'] and r['metrics']['tiny_count']==0 for r in okay)/5
                    reference_score=float(np.median([r['metrics']['silhouette_reference'] for r in okay])) if okay else -1.
                    screening[kind].append(dict(recipe=recipe,k=k,unflagged_fraction=fraction,median_reference_silhouette=reference_score,failed_snapshots=5-len(okay)))
            print(f'Screened {kind}; fits={sum(fit_count.values())}',flush=True)
        if fit_count['screening']>config['screening_fit_cap']:raise ValueError('Screening cap exceeded')
        shortlist={kind:sorted(rows,key=lambda r:(-r['unflagged_fraction'],r['k'],-r['median_reference_silhouette'],['P3','P1','P2'].index(r['recipe'])))[:2] for kind,rows in screening.items()}
        dump(out/'screening.json',screening);dump(out/'shortlist.json',shortlist)
        stability=[];adjacent=[];sensitivity=[];decisions={}
        for kind,candidates in shortlist.items():
            prepared.clear();reference.clear()
            for candidate in candidates:
                recipe,k=candidate['recipe'],candidate['k'];aris=[];worst=1.
                days=sorted(day for family,day in groups if family==kind)
                previous=None
                for day in days:
                    result=fit(kind,day,recipe,k,42,'full_series')
                    if result is None:continue
                    if int(day[:4]) in config['screening_years'] and (kind=='financial' or day[5:7]=='12'):
                        seed_results=[result]+[fit(kind,day,recipe,k,seed,'seed_stability') for seed in config['additional_seeds']]
                        for i,left in enumerate(seed_results):
                            for right in seed_results[i+1:]:
                                if left is None or right is None:continue
                                ari=float(adjusted_rand_score(left['labels'],right['labels']));nmi=float(normalized_mutual_info_score(left['labels'],right['labels']))
                                aris.append(ari);worst=min(worst,ari)
                                stability.append(dict(kind=kind,date=day,recipe=recipe,k=k,left_seed=left['seed'],right_seed=right['seed'],ari=ari,nmi=nmi,n=len(left['labels'])))
                    if previous:
                        left=dict(zip(previous['symbols'],previous['labels']));right=dict(zip(result['symbols'],result['labels']));common=sorted(set(left)&set(right))
                        adjacent.append(dict(kind=kind,recipe=recipe,k=k,source=previous['date'],target=day,n=len(common),entered=len(set(right)-set(left)),exited=len(set(left)-set(right)),ari=float(adjusted_rand_score([left[t] for t in common],[right[t] for t in common])) if common else None))
                    previous=result
                    prepared.clear();reference.clear()
                candidate.update(median_pairwise_seed_ari=float(np.median(aris)) if aris else None,worst_seed_ari=worst if aris else None,
                    geometry_candidate=candidate['unflagged_fraction']>=.8,robustness_candidate=bool(aris and np.median(aris)>=.8))
            for day in sorted(day for family,day in groups if family==kind):
                first,second=candidates
                a=saved.get(f'{kind}-{day}-{first["recipe"]}-k{first["k"]}-s42');b=saved.get(f'{kind}-{day}-{second["recipe"]}-k{second["k"]}-s42')
                if a and b:sensitivity.append(dict(kind=kind,date=day,left=f'{first["recipe"]}/k{first["k"]}',right=f'{second["recipe"]}/k{second["k"]}',ari=float(adjusted_rand_score(a['labels'],b['labels'])),n=len(a['labels'])))
            decisions[kind]=dict(status='NOT_PROMOTED_SOURCE_AND_USEFULNESS_REVIEW_OPEN',candidates=candidates,
                r2_required=not any(c['geometry_candidate'] and c['robustness_candidate'] for c in candidates),
                note='2024–2025 retrospective sensitivity, not untouched holdout; no automatic winner or source acceptance.')
            print(f'Validated {kind}; fits={sum(fit_count.values())}',flush=True)
    if fit_count['seed_stability']>config['seed_fit_cap']:raise ValueError('Seed cap exceeded')
    dump(out/'seed-stability.json',stability);dump(out/'adjacent-stability.json',adjacent);dump(out/'preprocessing-sensitivity.json',sensitivity)
    dump(out/'decisions.json',decisions);dump(out/'failures.json',failures)
    with (out/'scorecard.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    summary=dict(status='PARTIAL_R1_NUMERICAL_FAILURES' if failures else 'COMPLETE_R1_DESCRIPTIVE_NOT_PROMOTED',run_id=identity,result_path=out.relative_to(root).as_posix(),
        fits={phase:fit_count[phase] for phase in ('screening','full_series','seed_stability')},recovered_models=recovered_models,saved_models=len(saved),failures=len(failures),duration_seconds=time.perf_counter()-started,
        decisions=decisions,strict_pit_ready=False,research_ready=False,backtest_allowed=False,source_review_closed=False)
    dump(out/'summary.json',summary)
    dump(out/'manifest.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
    return summary
