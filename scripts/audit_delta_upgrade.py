"""D0/R0: pinned, offline inventory and descriptive diagnostics; never fit a model."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'web/backend')]
from app.indicators import IndicatorReferences, FAMILIES, availability, cohort_key
from app.repository import TerminalRepository


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream, 'sha256').hexdigest()


def table(path, rows):
    if not rows:return
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def audit(root, output):
    import numpy as np
    root=Path(root);output=Path(output)
    if output.exists():raise ValueError('Audit output already exists; use a new version, never overwrite evidence.')
    output.mkdir(parents=True)
    refs=IndicatorReferences(root)
    repo=TerminalRepository(root/'data/web/delta-intelligence-v1')
    pins={'configs/product/indicator_reference_v1.json':digest(root/'configs/product/indicator_reference_v1.json'),
          'data/web/delta-intelligence-v1/manifest.json':digest(root/'data/web/delta-intelligence-v1/manifest.json'),
          'data/web/delta-intelligence-v1/terminal.sqlite':repo.manifest['database_sha256']}
    for relative in ('scripts/audit_delta_upgrade.py','web/backend/app/indicators.py','web/backend/app/repository.py'):
        pins[relative]=digest(root/relative)
    ledger=[];full6=[];observation_links=[];identities={}
    for package in refs.load():
        source=package['source']
        pins[source['file']]=source['file_sha256'];pins[source['manifest']]=source['manifest_sha256']
        for item in source.get('supplements',[]):pins[item['file']]=item['sha256']
        groups={}
        for row in package['rows']:groups.setdefault((row['symbol'],cohort_key(row)),[]).append(row)
        for row in package['rows']:
            if not row.get('value'):continue
            dependency_text=row.get('dependency_ids') or row.get('verification_ids') or '[]'
            try:dependencies=sorted(json.loads(dependency_text))
            except (ValueError,TypeError):dependencies=[dependency_text]
            # Same pilot observation appears in two delivery packages. Match its
            # cohort, dependency provenance, variant and bases, never ticker+FY alone.
            identity=json.dumps([row['symbol'],row['family'],cohort_key(row),row.get('variant') or source.get('variant'),
                dependencies,row.get('input_period') or None,row.get('price_date') or row.get('snapshot_date') or None,row.get('price_basis') or None,row.get('balance_date') or None,row.get('share_basis') or None],sort_keys=True)
            key=hashlib.sha256(identity.encode()).hexdigest()
            if key in identities and identities[key]!=row['value']:raise ValueError('Conflicting same-identity values; no source priority allowed')
            duplicate=key in identities;identities[key]=row['value']
            observation_links.append(dict(observation_id=key,source_run=source['id'],ticker=row['symbol'],family=row['family'],cohort=cohort_key(row),
                                          duplicate_delivery=duplicate,value=row['value'],identity_provenance=identity))
        for (ticker,cohort),rows in groups.items():
            if len({r['family'] for r in rows})!=len(rows):raise ValueError('Duplicate source family')
            by={r['family']:r for r in rows}
            for family in FAMILIES:
                row=by.get(family,{})
                ledger.append(dict(ticker=ticker,period=row.get('input_period') or row.get('year') or rows[0]['year'],
                    period_kind=row.get('period_kind') or 'UNKNOWN',variant=row.get('variant') or source.get('variant') or 'UNKNOWN',
                    source_run=source['id'],vintage=row.get('snapshot_date') or row.get('pdf_sha256') or row.get('primary_pdf_sha256') or cohort,
                    cohort=cohort,family=family,value_present=bool(row.get('value')),value=row.get('value') or '',status=availability(row),
                    missing_inputs=row.get('missing_inputs') or 'UNKNOWN',evidence_ref=row.get('evidence_ref') or source['file'],source_sha256=source['file_sha256']))
            full6.append(dict(ticker=ticker,source_run=source['id'],cohort=cohort,year=rows[0]['year'],
                              numeric_families=len([r for r in rows if r.get('value')]),full6=all(by.get(f,{}).get('value') for f in FAMILIES)))
    geometry=[];fitted_geometry=[];correlations=[];tiny=[];sizes=[];price_trace=[]
    catalog=repo.catalog()
    evidence_path='artifacts/reports/dual-cluster-review-v1/financial-outlier-input-review.csv'
    evidence=list(csv.DictReader((root/evidence_path).open(encoding='utf-8-sig')))
    pins[evidence_path]=digest(root/evidence_path)
    lookup={}
    for row in evidence:lookup.setdefault((row['symbol'],row['year']),[]).append(row)
    financial_path='data/financial/financial_full10_baseline_v1/results/4d521e71139a48340d3d/snapshots.json'
    financial_models=json.loads((root/financial_path).read_bytes());pins[financial_path]=digest(root/financial_path)
    pointer_path='artifacts/reports/combined-reference-v1/result-ref.json'
    combined_pointer=json.loads((root/pointer_path).read_bytes());pins[pointer_path]=digest(root/pointer_path)
    combined_path=combined_pointer['path']+'/snapshots.json'
    combined_models=json.loads((root/combined_path).read_bytes());pins[combined_path]=digest(root/combined_path)
    feature_path='data/financial/financial_full10_baseline_v1/results/4d521e71139a48340d3d/features.csv'
    financial_sources={(r['symbol'],r['year']):r for r in csv.DictReader((root/feature_path).open(encoding='utf-8-sig'))}
    pins[feature_path]=digest(root/feature_path)
    for kind,dataset in catalog['datasets'].items():
        for day in dataset['dates']:
            data=repo.snapshot(kind,day);points=data['points'];fields=dataset['features'];n=len(points)
            matrix=np.array([[p['features'].get(f,np.nan) for f in fields] for p in points],dtype=float)
            if kind=='market':
                model_path=('M2/models/final_selected_model_v2/' if day[:4]<'2024' else 'M2/models/holdout/')+day+'.json'
                frozen=json.loads((root/model_path).read_bytes());pins[model_path]=digest(root/model_path)
            else:frozen=(financial_models if kind=='financial' else combined_models)[day if kind=='financial' else day[:4]]
            for j,field in enumerate(fields):
                values=matrix[:,j];finite=values[np.isfinite(values)]
                q=np.quantile(finite,[0,.01,.25,.5,.75,.99,1]);iqr=q[4]-q[2]
                tails=np.abs((finite-q[3])/(iqr if iqr else 1))
                geometry.append(dict(kind=kind,date=day,feature=field,n=n,missing_fraction=float(1-len(finite)/n),
                    zero_fraction=float(np.mean(finite==0)),minimum=q[0],p01=q[1],q1=q[2],median=q[3],q3=q[4],p99=q[5],maximum=q[6],
                    iqr=iqr,near_zero_iqr=bool(iqr<=1e-12*max(1,abs(q[3]))),robust_tail_max=float(tails.max()),
                    diagnostic='DESCRIPTIVE_ROBUST_TAIL_NOT_REFITTED_MODEL_SCALER'))
                scaler=frozen.get('scaler',frozen.get('scalers',{}))[field]
                transformed=(finite-scaler['center'])/scaler['scale']*scaler.get('weight',1)
                fitted_geometry.append(dict(kind=kind,date=day,feature=field,center=scaler['center'],scale=scaler['scale'],weight=scaler.get('weight',1),
                    minimum=float(transformed.min()),p01=float(np.quantile(transformed,.01)),median=float(np.median(transformed)),p99=float(np.quantile(transformed,.99)),maximum=float(transformed.max()),
                    fitted_metric='FROZEN_SCALER_PARAMETERS_NOT_REFITTED'))
            with np.errstate(invalid='ignore',divide='ignore'):corr=np.corrcoef(matrix,rowvar=False)
            for i,a in enumerate(fields):
                for j,b in enumerate(fields):
                    if i<j:correlations.append(dict(kind=kind,date=day,a=a,b=b,pearson=float(corr[i,j]) if np.isfinite(corr[i,j]) else '',status='OBSERVED' if np.isfinite(corr[i,j]) else 'UNDEFINED_CONSTANT_OR_MISSING'))
            counts=Counter(p['cluster'] for p in points);threshold=max(10,int(np.ceil(.01*n)))
            sizes.append(dict(kind=kind,date=day,n=n,sizes=json.dumps(dict(counts)),largest_share=max(counts.values())/n,
                singleton_count=sum(v==1 for v in counts.values()),tiny_count=sum(v<threshold for v in counts.values()),
                effective_k=float(np.exp(-sum(v/n*np.log(v/n) for v in counts.values()))),tiny_threshold=threshold))
            for p in points:
                if counts[p['cluster']]>=threshold:continue
                rows=lookup.get((p['ticker'],day[:4]),[])
                tiny.append(dict(kind=kind,date=day,ticker=p['ticker'],cluster=p['cluster'],size=counts[p['cluster']],
                    features=json.dumps(p['features'],sort_keys=True),source_evidence=json.dumps(rows,ensure_ascii=False),
                    financial_selected_source=json.dumps(financial_sources.get((p['ticker'],day[:4]),{}),ensure_ascii=False),
                    arithmetic_verdict='PASS_SELECTED_INPUT_REPLAY' if rows else 'NOT_IN_EXISTING_REPLAY_QUEUE',
                    source_verdict='REVIEW_PENDING_ORIGINAL_STATEMENT_OR_MARKET_SEMANTICS',sector_taxonomy='UNAVAILABLE_VERSIONED_TAXONOMY',
                    next_action='Review units/scope/denominators/year-pair and original statements' if kind=='financial' else 'Review price/volume observations, stale data and share events; no automatic exclusion'))
                if kind!='financial':
                    observed=repo.query('SELECT * FROM prices WHERE ticker=? AND date<=? ORDER BY date DESC LIMIT 252',(p['ticker'],day))
                    values=[r['adj_close'] for r in observed if r['adj_close'] is not None]
                    price_trace.append(dict(kind=kind,date=day,ticker=p['ticker'],observations=len(observed),zero_volume=sum(r['volume']==0 for r in observed),
                        null_volume=sum(r['volume'] is None for r in observed),last_observed_date=observed[0]['date'] if observed else '',
                        last_adj_close=observed[0]['adj_close'] if observed else '',last_raw_close=observed[0]['raw_close'] if observed else '',
                        adjusted_min=min(values) if values else '',adjusted_max=max(values) if values else '',distinct_adj_prices=len(set(values)),
                        share_event_evidence='NOT_IN_PRESENTATION_INDEX_REVIEW_PENDING',verdict='DESCRIPTIVE_FLAGS_ONLY_NO_REPAIR_OR_EXCLUSION'))
    table(output/'indicator-coverage.csv',ledger)
    table(output/'package-observation-links.csv',observation_links)
    table(output/'full6-cohorts.csv',full6)
    table(output/'missing-input-backlog.csv',[r for r in ledger if not r['value_present']])
    table(output/'geometry.csv',geometry);table(output/'fitted-scaled-geometry.csv',fitted_geometry);table(output/'correlations.csv',correlations)
    table(output/'snapshot-sizes.csv',sizes);table(output/'tiny-source-trace.csv',tiny)
    table(output/'tiny-market-price-trace.csv',price_trace)
    # Preserve existing separation evidence rather than recomputing fitted metrics.
    driver='artifacts/reports/dual-cluster-review-v1/separation-drivers.csv'
    pins[driver]=digest(root/driver)
    (output/'baseline-separation-drivers.csv').write_bytes((root/driver).read_bytes())
    (output/'input-pins.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
    summary=dict(stage='D0_R0',status='PASS_INVENTORY_WITH_OPEN_SOURCE_REVIEW',coverage=refs.coverage(),snapshots=len(sizes),
        ledger_rows=len(ledger),unique_numeric_observations=len(identities),duplicate_numeric_deliveries=sum(r['duplicate_delivery'] for r in observation_links),
        tiny_member_observations=len(tiny),source_review_closed=False,model_fits=0,network_requests=0,
        limitations=['Unknown reasons remain unknown; missing ledger families are not inferred missing-input facts.',
                     'Pilot5 subset is not added to reviewed85 coverage.',
                     'Arithmetic replay is not independent source-fact review; all tiny members remain queued.',
                     'No versioned sector taxonomy, historical identity, share-event acceptance or financial PIT evidence added.'])
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps({p.name:digest(p) for p in output.iterdir() if p.is_file()},indent=2),encoding='utf-8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='artifacts/reports/delta-upgrade-d0-r0-v1')
    args=parser.parse_args()
    print(json.dumps(audit(ROOT,ROOT/args.output),ensure_ascii=False,indent=2))
