"""Standalone financial-only static baseline; never runs market or backtesting."""
import csv,io,json
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean
from .financial_history_documents import read,put
from .financial_api_input_review import csv_bytes
from .financial_acquisition_overnight import state_file
from ..features.financial_exploratory import calculate_core,FEATURES,REGISTRY
from ..features.preprocessing import preprocess
from ..clustering.kmeans import fit_kmeans
from ..evaluation.cluster_metrics import cluster_metrics
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside

CODE=['src/delta_t1/experiments/financial_exploratory.py','scripts/financial_exploratory.py',
      'src/delta_t1/features/financial_exploratory.py','src/delta_t1/features/preprocessing.py',
      'src/delta_t1/clustering/kmeans.py','src/delta_t1/evaluation/cluster_metrics.py']


def validate_mode(c):
    if (c.get('version')!='financial-exploratory-core-v1' or c.get('owner_approval')!='EXPLORATORY_CORE_RATIOS_APPROVED_IN_CURRENT_THREAD'
        or c.get('scope')!='NON_PIT_FINANCIAL_ONLY_REFERENCE' or c.get('portfolio_evaluation_enabled') is not False
        or c.get('research_promotion_allowed') is not False or c.get('network_allowed') is not False):
        raise ValueError('explicit owner-approved reference-only mode required')
    if c['features']!=FEATURES or c['k']!=3 or c['winsor_quantile']!=0 or c['scaling']!='zscore':raise ValueError('frozen exploratory feature/model specification differs')
    REGISTRY.require_cluster_eligible(c['features'])


def eligible_periods(candidates):
    by_year=defaultdict(list);result=[];held=[]
    for row in candidates:by_year[row['year']].append(row)
    for year,rows in sorted(by_year.items()):
        if len(rows)!=1:
            held.append(dict(year=year,reason='MULTIPLE_PROVIDER_PARTITIONS_NO_SOURCE_PRIORITY'));continue
        if not rows[0]['quality_gate']:
            held.append(dict(year=year,reason='ACCOUNTING_FINANCE_BRIDGE_OR_DISPLACEMENT_HELD'));continue
        result.append(rows[0])
    return result,held


def fit_year(rows,c):
    if len(rows)<c['minimum_observations']:return dict(status='SKIPPED_INSUFFICIENT_COMPLETE_CASES',n=len(rows))
    ordered=sorted(rows,key=lambda r:r['registry_id']);vectors,scaler=preprocess(ordered,c)
    fit=fit_kmeans(vectors,c['k'],c['seed'],c['n_init'],c['max_iter'])
    diagnostics=cluster_metrics(vectors,fit)
    assignments=[dict(symbol=r['symbol'],registry_id=r['registry_id'],year=r['year'],cluster_id=label,
        reference_only=True,strict_pit_ready=False,research_ready=False) for r,label in zip(ordered,fit['labels'])]
    profiles=[]
    for label in range(c['k']):
        group=[r for r,l in zip(ordered,fit['labels']) if l==label]
        profiles.append(dict(cluster_id=label,size=len(group),means={f:mean(r[f] for r in group) for f in FEATURES},
            small_cluster_warning=len(group)<10,semantic_label='UNLABELED_FINANCIAL_REFERENCE_CLUSTER'))
    return dict(status='EXPLORATORY_STATIC_KMEANS_FITTED',n=len(ordered),scaler=scaler,centroids=fit['centroids'],
        diagnostics=diagnostics,assignments=assignments,profiles=profiles,fit_scope='THIS_FISCAL_YEAR_CROSS_SECTION_ONLY_NOT_OUT_OF_SAMPLE')


def run(root,config_path):
    root=Path(root);c=read(inside(root,config_path));validate_mode(c);pins={}
    def pin(path,expected=None):
        body=inside(root,path).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('exploratory input changed: '+path)
        pins[path]=sha;return body
    for p in CODE+[config_path]:pin(p)
    t=c['template_result'];tm=json.loads(pin(t['path']+'/manifest.json',t['manifest_sha256']))
    sm=json.loads(pin(t['path']+'/symbol-manifests.json',tm['symbol-manifests.json']))
    template_policy=json.loads(pin(t['path']+'/template-policy.json',tm['template-policy.json']))
    if template_policy['control_match_rows']!=24:raise ValueError('template regression controls no longer match')
    a=c['api_result'];am=json.loads(pin(a['path']+'/manifest.json',a['manifest_sha256']))
    api_sm=json.loads(pin(a['path']+'/symbol-manifests.json',am['symbol-manifests.json']))
    members=list(csv.DictReader(io.StringIO(pin(a['path']+'/symbols-readiness.csv',am['symbols-readiness.csv']).decode())))
    dataset=[];exclusions=[];state=inside(root,c['output_root'])/'pipeline-status.json'
    for index,member in enumerate(sorted(members,key=lambda r:r['symbol']),1):
        symbol=member['symbol'];registry=member['registry_id'];entry=sm[registry]
        m=json.loads(pin(entry['path'],entry['sha256']));directory=Path(entry['path']).parent.as_posix()
        candidates=json.loads(pin(directory+'/candidate-z-and-bridges.json',m['candidate-z-and-bridges.json']))
        candidates=[r for r in candidates if r['year'] in c['years']]
        if member['diagnostic_template_family']!='Regular':
            exclusions.append(dict(symbol=symbol,year=None,reason='NONREGULAR_OR_UNKNOWN_TEMPLATE_NO_SECTOR_ACCEPTANCE'));continue
        eligible,held=eligible_periods(candidates)
        exclusions.extend(dict(symbol=symbol,**r) for r in held)
        if not eligible:
            exclusions.append(dict(symbol=symbol,year=None,reason='NO_ELIGIBLE_PERIODS'));continue
        aentry=api_sm[registry];aim=json.loads(pin(aentry['path'],aentry['sha256']));ad=Path(aentry['path']).parent.as_posix()
        fields=json.loads(pin(ad+'/field-inputs.json',aim['field-inputs.json']))
        by_period=defaultdict(dict)
        for row in fields:
            if row['value'] is not None:by_period[row['year'],row['provider_type']][row['field']]=row['value']
        for period in eligible:
            result=calculate_core(by_period[period['year'],period['provider_type']])
            if result['values'] is None:
                exclusions.append(dict(symbol=symbol,year=period['year'],reason=result['status'],missing=result.get('missing',[])));continue
            dataset.append(dict(symbol=symbol,registry_id=registry,year=period['year'],provider_type=period['provider_type'],
                **result['values'],period_end=str(period['year'])+'-12-31',published_at=None,
                identity_status='CURRENT_REGISTRY_CANDIDATE_NOT_CANONICAL_HISTORICAL_SECURITY_ID',
                dataset_scope='EXPLORATORY_API_REFERENCE_ONLY',unit_scope_vintage_status='SOURCE_TEMPLATE_QA_NOT_INDIVIDUAL_FACT_ACCEPTANCE',
                strict_pit_ready=False,financial_features_allowed=False,research_ready=False,
                source_evidence=ad+'/field-inputs.json',qa_evidence=directory+'/candidate-z-and-bridges.json'))
        if index%100==0:
            state_file(state,'BUILDING_EXPLORATORY_RATIOS',completed=index,total=len(members),feature_rows=len(dataset))
    datasets_by_year=defaultdict(list)
    for row in dataset:datasets_by_year[row['year']].append(row)
    snapshots={};assignments=[];metrics=[]
    for year in c['years']:
        state_file(state,'FITTING_EXPLORATORY_STATIC_BASELINE',year=year,n=len(datasets_by_year[year]),feature_rows=len(dataset))
        result=fit_year(datasets_by_year[year],c);snapshots[str(year)]=result
        assignments.extend(result.get('assignments',[]))
        metrics.append(dict(year=year,status=result['status'],n=result['n'],**result.get('diagnostics',{})))
        print(json.dumps(dict(year=year,status=result['status'],n=result['n'])),flush=True)
    counts=Counter(r['registry_id'] for r in dataset)
    summary=dict(status='COMPLETE_OWNER_APPROVED_EXPLORATORY_FINANCIAL_BASELINE',source_registry_symbols=len(members),
        feature_rows=len(dataset),distinct_registry_candidates=len(counts),candidates_with_all10_annual_periods=sum(v==10 for v in counts.values()),
        fitted_years=[int(y) for y,r in snapshots.items() if r['status']=='EXPLORATORY_STATIC_KMEANS_FITTED'],
        rows_by_year={str(y):len(datasets_by_year[y]) for y in c['years']},features=FEATURES,algorithm='STATIC_KMEANS',k=c['k'],
        exclusion_counts=dict(Counter(r['reason'] for r in exclusions)),strict_pit_ready=False,research_ready=False,m3_backtest_allowed=False,
        original_six_metric_goal='PARTIAL_CONTINUES_IN_PARALLEL_NOT_REPLACED_BY_CORE_RATIOS',
        market_handoff='PENDING_EXTERNAL_TEAM_FILES_NOT_AVAILABLE_ON_THIS_MACHINE',network_requests=0,pdf_downloads=0,ocr_pages=0)
    products={'summary.json':encoded(summary),'feature-registry.json':encoded([REGISTRY.get(f).__dict__ for f in FEATURES]),
        'features.csv':csv_bytes(dataset),'exclusions.csv':csv_bytes(exclusions),'assignments.csv':csv_bytes(assignments),
        'metrics.csv':csv_bytes(metrics),'snapshots.json':encoded(snapshots),'input-pins.json':encoded(pins),'config.json':encoded(c)}
    manifest={n:digest(b) for n,b in products.items()};out=inside(root,c['output_root'])/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    import os
    report=inside(root,c['report_root']);rel=os.path.relpath(out,report).replace('\\','/')
    table='\n'.join('| '+str(r['year'])+' | '+str(r['n'])+' | '+str(r.get('cluster_sizes','—'))+' | '+str(round(r['silhouette'],4) if r.get('silhouette') is not None else '—')+' |' for r in metrics)
    text=f'''# Baseline financial-only thăm dò: core ratios

## Phạm vi owner đã chấp thuận

Owner chọn **chạy baseline thăm dò bằng tỷ số cơ bản; hoàn thiện EPS/P/E/P/B/F/M/Z song song**. Market đang ở máy thành viên khác, chưa có config/artifacts bàn giao. Do đó chạy financial độc lập, không chỉnh market hoặc ghép/backtest giả.

Đã tạo **{len(dataset):,} annual feature rows**, **{len(counts)} current registry candidates** có ít nhất1 kỳ hợp lệ. Có **{summary['candidates_with_all10_annual_periods']} candidates** có cả10 annual periods2016–2025, chưa phải historical-identity/PIT readiness. Fit static K-Means **k=3**, seed42/n_init20/max_iter300, zscore và no winsorization/PCA/imputation. Không chọn k hoặc feature bằng returns hay holdout performance. Mỗi năm fit cross-section riêng; không gọi đây là Dynamic Clustering hoặc đánh giá out-of-sample.

| Năm tài chính | Complete reference rows | Cluster sizes | Silhouette |
|---|---:|---|---:|
{table}

6 features: gross margin, net margin, liabilities/ending assets, current ratio, CFO/ending assets và revenue/ending assets. Turnover dùng ending assets đã ghi rõ, không gọi average-assets turnover. Các features nằm trong registry exploratory riêng, không thay production financial/market registry hoặc mở research gates. Mean feature profiles trong snapshots.json dùng để diễn giải cụm; small/singleton cluster vẫn báo nguyên, không xoá/tune lại để làm đẹp kết quả.

## Kiểm soát input

- Chỉ template Regular đã có controls; từng annual/provider partition phải qua finance bridge, accounting checks và displacement hold từ stage36.
- Có nhiều provider partitions cho cùng mã/năm thì loại rõ, không chọn ưu tiên source. Missing/zero-denominator/invalid giữ exclusion; negative CFO/net margin được giữ nếu hợp lệ.
- Dataset giữ registry ID provisional và evidence refs, không tự phong thành canonical security_id. Period end không được coi là ngày công bố hoặc ngày có thể đầu tư.
- Unit/scope/vintage ngoài controls chưa có individual-fact acceptance; ratio basis là exploratory source hypothesis owner đã cho phép, không biến thành chứng nhận dữ liệu đúng. Không fill ngược lịch sử hoặc dùng số mới làm PIT facts.

## Bàn giao

- [Features thực tế]({rel}/features.csv), [assignments từng mã/năm]({rel}/assignments.csv).
- [Metrics theo năm]({rel}/metrics.csv), [model/scaler/profiles và assignments đầy đủ]({rel}/snapshots.json).
- [Các trường hợp bị loại và lý do]({rel}/exclusions.csv), [summary]({rel}/summary.json), [registered formulas]({rel}/feature-registry.json).

## Trạng thái M2/M3 và sáu chỉ số ban đầu

Đây là **baseline thăm dò đã execute**, không phải final M2 financial research sample hoặc M3-ready dataset. M3 vẫn cần publication/vintage/historical identity và market handoff/calendar/raw-price/share events đúng version, cùng protocol đã freeze. Strict feature set EPS/P/E/P/B/F/M/Z không bị thay bằng core ratios: bundle reference87 rows/11 mã/5 full6 cohorts vẫn giữ, các input weighted shares/current debt portion/issuance/depreciation/valuation còn thiếu vẫn report riêng.

Không download PDF/OCR/network. Bước tiếp theo: review profiles/exclusions và freeze financial protocol sau khi có evidence/PIT và handoff market; không chọn model bằng portfolio returns. Goal final M2/M3 vẫn PARTIAL.
'''
    put(report/'report.md',text.encode());put(report/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    state_file(state,summary['status'],feature_rows=len(dataset),distinct_registry_candidates=len(counts),fitted_years=summary['fitted_years'],output=out.relative_to(root).as_posix(),report=(report/'report.md').relative_to(root).as_posix())
    return dict(summary,output=out.relative_to(root).as_posix())
