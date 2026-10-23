"""Versioned template calibration and reference/model input handoff, offline.

Mapping hypotheses may run on an exact template in staging. Only reviewed
observations are numerical references; no inferred mapping opens a research gate.
"""
import csv
import io
import json
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

from .financial_api_input_review import csv_bytes,accounting,Z_INPUTS
from .financial_history_documents import read,put
from .financial_template_candidates import parse_candidates
from .financial_acquisition_overnight import state_file
from ..features.financial_reference import calculate
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside

FIELDS={'21':'finance_income','22':'finance_expense','23':'interest_expense','24':'associate_profit'}
CODE=['src/delta_t1/experiments/financial_template_contract.py','scripts/financial_template_contract.py',
      'src/delta_t1/experiments/financial_template_candidates.py','src/delta_t1/experiments/financial_api_input_review.py',
      'src/delta_t1/features/financial_reference.py']


def proposed_fields(rows,templates):
    selected=[]
    for row in rows:
        if (row['template_sha256'] in templates and row['statement']=='KQKD' and row['mode']=='NAM'
            and row['raw_code'] in FIELDS and row['mapping_status']=='UNIQUE_CODE_LABEL_CANDIDATE'
            and row['value_status']=='NUMERIC_CANDIDATE' and 2013<=row['year']<=2025 and row['quarter']==0):
            selected.append(dict(row,proposed_field=FIELDS[row['raw_code']],accepted=False,pit_ready=False,
                mapping_status='EXACT_TEMPLATE_STAGING_PROPOSAL_NOT_RESEARCH_ACCEPTANCE'))
    return selected


def finance_bridge(values):
    required={'reported_operating_profit','gross_profit','finance_income','finance_expense',
              'associate_profit','selling_expense','administrative_expense'}
    if not required<=values.keys():return dict(status='MISSING_INPUTS',difference=None)
    v={k:Decimal(values[k]) for k in required}
    delta=v['reported_operating_profit']-(v['gross_profit']+v['finance_income']-v['finance_expense']+v['associate_profit']-v['selling_expense']-v['administrative_expense'])
    return dict(status='EXACT_EQUALITY' if delta==0 else 'DIFFERENCE',difference=str(delta))


def complete_reference_vectors(metrics):
    groups=defaultdict(list);vectors=[]
    for row in metrics:
        if row['value'] is not None and row['period_kind']=='ANNUAL':
            groups[row['symbol'],row['year'],row['cohort_id'],row['input_scope']].append(row)
    for key,rows in sorted(groups.items()):
        by_family=defaultdict(list)
        for row in rows:by_family[row['family']].append(row)
        if set(by_family)!={'EPS','PE','PB','F_SCORE','M_SCORE','Z_SCORE'}:continue
        if any(len({(r['value'],r['variant'],r.get('snapshot_date')) for r in rs})!=1 for rs in by_family.values()):continue
        price_dates={by_family[f][0].get('snapshot_date') for f in ['PE','PB']}
        if len(price_dates)!=1 or None in price_dates:continue
        vectors.append(dict(symbol=key[0],year=key[1],cohort_id=key[2],input_scope=key[3],snapshot_date=next(iter(price_dates)),
            **{family:rs[0]['value'] for family,rs in by_family.items()},
            metric_variants={family:rs[0]['variant'] for family,rs in by_family.items()},
            input_ids=[r['id'] for r in rows],financial_cluster_input_allowed=False,strict_pit_ready=False,
            reason='REFERENCE_VARIANTS_NOT_APPROVED_FINANCIAL_FEATURE_VECTOR'))
    return vectors


def require_cluster_ready(readiness):
    reasons=[name for name in ['financial_protocol_approved','features_cluster_eligible','pit_inputs_verified',
        'historical_identity_verified','development_sample_ready'] if readiness.get(name) is not True]
    if reasons:raise ValueError('FINANCIAL_CLUSTERING_HELD: '+','.join(reasons))


def run(root,config_path):
    root=Path(root);c=read(inside(root,config_path));pins={};base=inside(root,c['output_root'])
    if c['version']!='financial-template-contract-v1' or c.get('network_allowed') is not False or c.get('research_promotion_allowed') is not False:
        raise ValueError('explicit offline staging/reference contract required')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();actual=digest(raw)
        if expected is not None and actual!=expected:raise ValueError('contract input changed: '+path)
        pins[path]=actual;return raw
    for p in CODE+[config_path]:pin(p)
    review=json.loads(pin(c['controls']['path'],c['controls']['sha256']))
    for d in review['documents']:
        for kind in ['pdf','image']:pin(d[kind+'_path'],d[kind+'_sha256'])
    a=c['api_result'];am=json.loads(pin(a['path']+'/manifest.json',a['manifest_sha256']))
    sms=json.loads(pin(a['path']+'/symbol-manifests.json',am['symbol-manifests.json']))
    members=list(csv.DictReader(io.StringIO(pin(a['path']+'/symbols-readiness.csv',am['symbols-readiness.csv']).decode())))
    by_symbol={r['symbol']:r for r in members}
    def load_fields(member,local_pins):
        m=sms[member['registry_id']]
        def checked(path,expected):
            body=inside(root,path).read_bytes()
            if digest(body)!=expected:raise ValueError('symbol input changed: '+path)
            local_pins[path]=expected;return body
        manifest=json.loads(checked(m['path'],m['sha256']));directory=Path(m['path']).parent.as_posix()
        return json.loads(checked(directory+'/field-inputs.json',manifest['field-inputs.json'])),manifest,directory,checked
    controls=[];templates=set();control_cache={}
    for symbol in sorted({r['symbol'] for r in review['controls']}):
        fields,_,_,_=load_fields(by_symbol[symbol],pins);rawpaths={}
        for row in fields:
            if row['field']=='interest_expense':
                for obs in row['observations']:rawpaths[obs['source_path']]=obs['source_sha256']
        rows=[]
        for path,sha in rawpaths.items():
            rows.extend(parse_candidates(pin(path,sha),dict(symbol=symbol,statement='KQKD',mode='NAM',group='KQKD'),path,sha))
        control_cache[symbol]=rows
    # Derive exact template signatures only from calibration issuers.
    for fact in review['controls']:
        if fact['role']!='CALIBRATION':continue
        for row in control_cache[fact['symbol']]:
            if row['year']==fact['year'] and FIELDS.get(row['raw_code'])==fact['field'] and row['value'] is not None and Decimal(row['value'])==Decimal(fact['value']):templates.add(row['template_sha256'])
    if not templates:raise ValueError('no calibrated template')
    for fact in review['controls']:
        rows=[r for r in proposed_fields(control_cache[fact['symbol']],templates) if r['year']==fact['year'] and r['proposed_field']==fact['field']]
        matched=bool(rows) and all(Decimal(r['value'])==Decimal(fact['value']) for r in rows)
        controls.append(dict(fact,status='EXACT_MATCH' if matched else 'HOLD',api_observations=rows))
    holdout_issuers={r['symbol'] for r in controls if r['role']=='INDEPENDENT_ISSUER_VALIDATION'}
    if len(holdout_issuers)<2 or any(r['status']!='EXACT_MATCH' for r in controls):raise ValueError('independent template controls failed')
    policy=dict(version='regular-kqkd-nam-visual-calibration-v1',template_sha256=sorted(templates),raw_code_fields=FIELDS,
        calibration_issuer='ACV',independent_validation_issuers=sorted(holdout_issuers),control_rows=len(controls),control_match_rows=sum(r['status']=='EXACT_MATCH' for r in controls),
        application_scope='EXACT_TEMPLATE_REGULAR_ANNUAL_STAGING_ONLY',canonical_acceptance='MANUAL_REVIEW_REQUIRED_PER_SOURCE_SCOPE_UNIT_VINTAGE',
        inferred_mapping_outside_controls='NOT_ACCEPTED_FOR_RESEARCH',financial_features_allowed=False)
    r=c['reference_result'];rm=json.loads(pin(r['path']+'/manifest.json',r['manifest_sha256']))
    references=json.loads(pin(r['path']+'/computed-reference-metrics.json',rm['computed-reference-metrics.json']))
    references=[row for row in references if row['value'] is not None]
    supplement=json.loads(pin(c['reference_supplement']['path'],c['reference_supplement']['sha256']))
    for row in supplement:
        item=dict(row,id=digest(encoded(row))[:24],period_kind='ANNUAL',variant='EM_Z_DOUBLE_PRIME_REFERENCE',cohort_id='SUPPLEMENT:'+row['pdf_sha256']+':'+str(row['year']),
            evidence_ref=c['reference_supplement']['path'],source_adapter='REVIEWED_REFERENCE_SUPPLEMENT',snapshot_date=None)
        references.append(item)
    vectors=complete_reference_vectors(references)
    job_sha=digest(encoded(pins));job=base/'jobs'/job_sha[:20];put(job/'input-pins.json',pins);put(job/'template-policy.json',policy);put(job/'controls.json',controls)
    state=base/'pipeline-status.json';state_file(state,'RUNNING_EXACT_TEMPLATE_STAGING',completed=0,total=len(members),job=job.relative_to(root).as_posix())
    def process(member):
        out=job/'symbols'/member['registry_id'];local_pins={}
        if out.exists():
            manifest=read(out/'manifest.json')
            for name,sha in manifest.items():
                if digest((out/name).read_bytes())!=sha:raise ValueError('checkpoint changed')
            for path,sha in read(out/'input-pins.json').items():
                if digest(inside(root,path).read_bytes())!=sha:raise ValueError('checkpoint source changed')
            return read(out/'summary.json')
        fields,manifest,directory,checked=load_fields(member,local_pins)
        values=defaultdict(dict);rawpaths={}
        for f in fields:
            if f['value'] is not None:values[f['year'],f['provider_type']][f['field']]=f['value']
            if f['field']=='interest_expense':
                for obs in f['observations']:rawpaths[obs['source_path']]=obs['source_sha256']
        changes=[]
        if member['diagnostic_template_family']=='Regular':
            for path,sha in rawpaths.items():
                raw=checked(path,sha)
                rows=parse_candidates(raw,dict(symbol=member['symbol'],statement='KQKD',mode='NAM',group='KQKD'),path,sha)
                changes.extend(proposed_fields(rows,templates))
        proposed=defaultdict(list)
        for row in changes:proposed[row['year'],row['provider_type'],row['proposed_field']].append(row)
        overlay=defaultdict(dict);conflicts=[]
        for (year,ptype,field),rows in proposed.items():
            vs={Decimal(r['value']) for r in rows}
            if len(vs)==1:overlay[year,ptype][field]=str(next(iter(vs)))
            else:conflicts.append(dict(year=year,provider_type=ptype,field=field,status='CONFLICT_NO_SELECTION'))
        qa_pins=json.loads(checked(directory+'/input-pins.json',manifest['input-pins.json']))['sources']
        anomalies=[]
        for path,sha in qa_pins.items():
            if path.endswith('/displacements.json'):anomalies.extend(json.loads(checked(path,sha)))
        candidates=[]
        for (year,ptype),finance in sorted(overlay.items(),key=str):
            before=values[year,ptype];after=dict(before,**finance);bridge=finance_bridge(after)
            part=accounting(after);passed={r['check'] for r in part if r['status']=='RAW_EQUALITY'}
            core={'ASSETS_CAPITAL','ASSETS_LIABILITIES_EQUITY','ASSET_PARTS','LIABILITY_PARTS','GROSS_PROFIT','PRETAX_BRIDGE','AFTERTAX_BRIDGE'}
            held=any(r['year']==year and r['annual_provider_type']==ptype for r in anomalies)
            quality=bridge['status']=='EXACT_EQUALITY' and core<=passed and not held and not any(r['status']=='RAW_DIFFERENCE' for r in part)
            score=None
            if quality and Z_INPUTS<=after.keys() and Decimal(after['interest_expense'])>=0:
                inputs={f:after[f] for f in ['current_assets','current_liabilities','total_assets','retained_earnings','total_equity','total_liabilities']}
                inputs['document_reconciled_ebit']=str(Decimal(after['profit_before_tax'])+Decimal(after['interest_expense']))
                result=calculate('Z_SCORE',inputs)
                score=result['value']['em_z_double_prime_reference'] if result['value'] else None
            candidates.append(dict(symbol=member['symbol'],year=year,provider_type=ptype,finance_bridge=bridge,
                old_interest_value=before.get('interest_expense'),proposed_interest_value=finance.get('interest_expense'),
                conditional_z=score,quality_gate=quality,status='CONDITIONAL_ARITHMETIC_ONLY' if score else 'INPUT_OR_ACCOUNTING_HELD',
                accepted=False,strict_pit_ready=False,financial_cluster_input_allowed=False,
                reason='UNIT_SCOPE_VINTAGE_EBIT_AND_IDENTITY_NOT_ACCEPTED_OUTSIDE_REVIEWED_CONTROLS'))
        summary=dict(symbol=member['symbol'],registry_id=member['registry_id'],matched_template_field_observations=len(changes),
            annual_partitions=len(candidates),finance_bridge_equalities=sum(r['finance_bridge']['status']=='EXACT_EQUALITY' for r in candidates),
            conditional_z_rows=sum(r['conditional_z'] is not None for r in candidates),conflicting_mapping_keys=len(conflicts),
            new_accepted_metric_rows=0,financial_cluster_input_allowed=False)
        products={'summary.json':encoded(summary),'input-pins.json':encoded(local_pins),'proposed-finance-fields.json':encoded(changes),
            'mapping-conflicts.json':encoded(conflicts),'candidate-z-and-bridges.json':encoded(candidates)}
        for name,body in products.items():put(out/name,body)
        put(out/'manifest.json',{n:digest(b) for n,b in products.items()});return summary
    summaries=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index,summary in enumerate(pool.map(process,sorted(members,key=lambda r:r['symbol'])),1):
            summaries.append(summary)
            if index%50==0 or index==len(members):
                state_file(state,'RUNNING_EXACT_TEMPLATE_STAGING',completed=index,total=len(members),last_symbol=summary['symbol'],job=job.relative_to(root).as_posix())
                print(json.dumps(dict(completed=index,total=len(members),last_symbol=summary['symbol'])),flush=True)
    return finish(root,c,job,policy,controls,references,vectors,summaries)


def finish(root,c,job,policy,controls,references,vectors,summaries):
    candidates=[];symbol_pins={}
    for s in summaries:
        folder=job/'symbols'/s['registry_id'];m=read(folder/'manifest.json')
        raw=(folder/'candidate-z-and-bridges.json').read_bytes()
        if digest(raw)!=m['candidate-z-and-bridges.json']:raise ValueError('candidate output changed')
        candidates.extend(json.loads(raw));symbol_pins[s['registry_id']]=dict(path=(folder/'manifest.json').relative_to(root).as_posix(),sha256=digest((folder/'manifest.json').read_bytes()))
    readiness=dict(financial_protocol_approved=False,features_cluster_eligible=False,pit_inputs_verified=False,
        historical_identity_verified=False,development_sample_ready=False,reference_complete_cohorts=len(vectors),
        numerical_references=len(references),financial_cluster_input_allowed=False,m2_status='MANUAL_REVIEW_REQUIRED_FINANCIAL_PROTOCOL_AND_INPUT_ACCEPTANCE',
        m3_status='HELD_PIT_IDENTITY_METHODOLOGY_AND_EXTERNAL_MARKET_HANDOFF',model_fit_executed=False,
        market_work_owner='EXTERNAL_TEAM_AS_REPORTED_BY_USER_NO_MARKET_CHANGES',
        blockers=['REFERENCE_VARIANTS_NOT_TTM_FEATURE_ACCEPTANCE','PUBLICATION_AND_SOURCE_VINTAGE','HISTORICAL_IDENTITY',
                  'FINANCIAL_CLUSTERING_FEATURE_PROTOCOL_NOT_FROZEN','DEVELOPMENT_HOLDOUT_SAMPLE_NOT_MATERIALIZED'])
    summary=dict(status='COMPLETE_TEMPLATE_STAGING_AND_REFERENCE_INPUT_HANDOFF',symbols=len(summaries),
        template_control_rows=len(controls),control_exact_matches=sum(r['status']=='EXACT_MATCH' for r in controls),
        mapped_template_symbols=sum(r['matched_template_field_observations']>0 for r in summaries),
        annual_partitions=sum(r['annual_partitions'] for r in summaries),finance_bridge_equalities=sum(r['finance_bridge_equalities'] for r in summaries),
        conditional_z_rows=sum(r['conditional_z_rows'] for r in summaries),reference_value_rows=len(references),
        reference_symbols=len({r['symbol'] for r in references}),reference_six_family_cohorts=len(vectors),
        new_accepted_api_metric_rows=0,financial_cluster_ready_symbols=0,model_fit_executed=False,
        network_requests=0,pdf_downloads=0,ocr_pages=0,financial_delivery='PARTIAL_REFERENCE_BUNDLE_READY_RESEARCH_GATES_HELD')
    products={'summary.json':encoded(summary),'template-policy.json':encoded(policy),'controls.json':encoded(controls),
        'reference-metrics.json':encoded(references),'reference-metrics.csv':csv_bytes(references),
        'reference-six-family-vectors.csv':csv_bytes(vectors),'symbols.csv':csv_bytes(summaries),
        'candidate-z-and-bridges.csv':csv_bytes(candidates),'clustering-readiness.json':encoded(readiness),
        'symbol-manifests.json':encoded(symbol_pins),'input-pins.json':(job/'input-pins.json').read_bytes()}
    manifest={n:digest(b) for n,b in products.items()};out=job/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    import os
    report=inside(root,c['report_root']);relative=os.path.relpath(out,report).replace('\\','/')
    text=f'''# Financial: template contract và input handoff cho M2/M3

## Kết quả stage

Đã chốt policy staging theo exact template fingerprint, **{len(controls)} controls / {summary['control_exact_matches']} exact matches**. Calibration ACV; independent issuer validation VNM/GAS. Controls là24 financial-line observations trong cached PDFs FY2025, gồm current2025/comparative2024. Trực quan kiểm lại code21 finance income,22 finance expense,23 interest,24 associate profit. Không dịch hàng theo vị trí hoặc sửa raw.

Đã đánh giá **{len(summaries)} mã**; **{summary['mapped_template_symbols']} mã** có exact template phù hợp, **{summary['annual_partitions']} annual provider partitions**. Có **{summary['finance_bridge_equalities']} finance bridges equality**, **{summary['conditional_z_rows']} dòng Z tính có điều kiện**. Đây là staging arithmetic ngoài controls, chưa phải verified/reference/PIT hoặc feature cho clustering. Unsupported template/Bank/Securities/UNKNOWN không mở mapping doanh nghiệp thường.

Đã hợp nhất **{len(references)} numeric reference rows của {summary['reference_symbols']} mã**, gồm85 rows stage33 và2 Z period keys BRC2024/VNM2024, không cộng duplicate replay. Có **{len(vectors)} cohort vectors đủ6 family cùng năm/scope/vintage và ngày giá PE/PB khớp**. Annual PE/EPS variants vẫn reference, không tự đổi thành TTM/current features.

## Tại sao chưa fit financial model?

**0 mã được mở research clustering gate**. Reference registries hiện `cluster_eligible=false`; financial feature protocol, publication/vintage/identity và development/holdout sample chưa được acceptance/freeze. `require_cluster_ready` fail rõ khi bất kỳ gate còn thiếu; không gọi model để tạo kết quả giả hoàn tất M2. Dynamic methodology review còn NOT APPROVED; static baseline cũng không được dùng data còn unresolved như research sample.

Theo owner, market do thành viên khác thu thập/chạy model. Stage này không sửa runner, dataset, protocol hoặc artifacts market và không tuyên bố đã verify kết quả bên ngoài. Financial handoff giữ đường nối tới snapshot/identity/price basis để ghép về sau; M3 cần source availability và market handoff đúng version.

## File bàn giao

- [Summary]({relative}/summary.json), [policy exact-template]({relative}/template-policy.json), [reviewed controls/provenance]({relative}/controls.json).
- [Reference metrics87 rows]({relative}/reference-metrics.csv), [JSON/provenance]({relative}/reference-metrics.json).
- [Các cohort reference đủ6]({relative}/reference-six-family-vectors.csv): không được đưa thẳng vào model.
- [Readiness từng mã]({relative}/symbols.csv), [candidate Z/finance bridges]({relative}/candidate-z-and-bridges.csv).
- [Financial clustering/M3 readiness và blocker cụ thể]({relative}/clustering-readiness.json).

## Những việc còn chặn mục tiêu

1. Scope/unit/report-vintage acceptance ngoài controls và mapping versions cần review theo evidence; exact fingerprint/bridge equality không đủ tự chứng nhận mọi input.
2. EPS/PE cần đúng numerator/weighted shares/TTM/raw-price/events; PB cần parent common equity và shares; F cần current debt portion và parent issuance; M cần pure owned-PPE depreciation. Không thay bằng field gần giống.
3. Publication evidence và historical identity để tạo PIT feature snapshots, không đẩy comparative/restated facts ngược lịch sử.
4. Freeze protocol financial-only: feature variants, sampling, development/holdout và leakage-safe preprocessing; sau khi gates đạt mới reuse static K-Means runner. Không chọn model bằng return/Sharpe; M3 sau methodology freeze.

Không gọi network, tải PDF hoặc OCR mới; chưa lập PDF supplement plan. Sửa policy canonical/inferred transformation hoặc mở research gates là **MANUAL_REVIEW_REQUIRED** theo AGENTS.md; policy hiện chỉ staging/reference và giữ gates false. Mục tiêu cuối full historical financial clustering/M2/M3 vẫn PARTIAL, không đánh dấu hoàn tất chỉ vì có file bundle.
'''
    put(report/'report.md',text.encode());put(report/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    state_file(inside(root,c['output_root'])/'pipeline-status.json',summary['status'],completed=len(summaries),total=len(summaries),output=out.relative_to(root).as_posix(),report=(report/'report.md').relative_to(root).as_posix())
    return dict(summary,output=out.relative_to(root).as_posix())
