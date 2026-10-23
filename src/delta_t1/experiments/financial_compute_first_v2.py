"""Compute cleared cached references first; screen remaining API inputs without downloads."""
import csv,io,json
from collections import defaultdict,Counter
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from .financial_history_documents import read,put
from .financial_cafef_pilot import required_keys,FAMILIES,reviewed,compute
from .financial_reviewed_batch import run as reviewed_run
from .financial_reference_cohorts import run as cohorts_run
from .financial_scale_review import build as scale_build
from .financial_reference_flow import export as fpt_export
from .financial_inventory_qa import csv_body
from .financial_history_qa import MAPPING
from .financial_acquisition_overnight import state_file
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside

CODE=['src/delta_t1/experiments/financial_compute_first_v2.py','scripts/financial_compute_first_v2.py',
 'src/delta_t1/experiments/financial_cafef_pilot.py','src/delta_t1/experiments/financial_reviewed_batch.py',
 'src/delta_t1/experiments/financial_reference_cohorts.py','src/delta_t1/experiments/financial_scale_review.py',
 'src/delta_t1/experiments/financial_reference_flow.py','src/delta_t1/features/financial_reference.py',
 'src/delta_t1/features/financial_vas_reference.py','src/delta_t1/experiments/financial_history_qa.py',
 'src/delta_t1/ingestion/financial_pilot_readiness.py','src/delta_t1/features/registry.py']

def csv_read(body):return list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))

def metric_row(row,source,reference,kind='ANNUAL',variant=None,cohort=None,scope=None):
    value=row.get('value')
    if value is not None:
        if type(value) is bool or not Decimal(str(value)).is_finite():raise ValueError('invalid calculated metric')
        value=str(value)
    return dict(symbol=row['symbol'],year=int(row['year']),family=row['family'],value=value,status=row.get('status'),
        period_kind=kind,variant=variant or row.get('variant') or row.get('result',{}).get('variant') or source,
        cohort_id=cohort or row.get('cohort_id') or source+':'+row['symbol']+':'+str(row['year']),
        input_scope=scope or row.get('input_scope','DECLARED_IN_REVIEWED_SOURCE'),
        snapshot_date=row.get('snapshot_date') or row.get('price_date') or row.get('decision_date'),
        primary_pdf_sha256=row.get('primary_pdf_sha256') or row.get('pdf_sha256'),
        period_start=row.get('period_start'),period_end=row.get('period_end'),
        input_period=row.get('input_period'),price_basis=row.get('price_basis'),share_basis=row.get('share_basis'),balance_date=row.get('balance_date') or row.get('book_date'),eps_basis=row.get('eps_basis'),
        source_adapter=source,evidence_ref=reference,dependency_ids=row.get('dependency_ids',[]),
        missing_inputs=row.get('missing_inputs',[]),strict_pit_ready=False,financial_features_allowed=False,
        temporal_status=row.get('temporal_status','EXACT_REVIEWED_VINTAGE_REFERENCE_NOT_CURRENT_TTM_OR_BACKTEST_VECTOR'))

def apply_cohort_metadata(rows,cohorts):
    index={c['id']:c for c in cohorts};result=[]
    variants={'EPS':'DISCLOSED_BASIC_EPS_EXACT_ANNUAL_NOTE_REFERENCE','PE':'ANNUAL_REPORTED_BASIS_PE_REFERENCE_NOT_TTM','PB':'DECLARED_BOOK_SHARE_BASIS_PB_REFERENCE','Z_SCORE':'EM_Z_DOUBLE_PRIME_REFERENCE'}
    for row in rows:
        cohort=index[row['cohort_id']];scope=cohort['input_scope']
        if scope!='CONSOLIDATED' or cohort['variant_clearance']!='EXISTING_NONFINANCIAL_REFERENCE_VARIANTS':raise ValueError('uncleared cohort metadata')
        if row.get('input_scope',scope)!=scope:raise ValueError('metric/cohort scope differs')
        if (row['symbol'],row['year'])!=(cohort['symbol'],cohort['year']):raise ValueError('metric/cohort period identity differs')
        item=dict(row,input_scope=scope)
        if not item.get('variant') and not item.get('result',{}).get('variant'):item['variant']=variants.get(row['family'])
        result.append(item)
    return result

def classify_api_task(symbol,year,family,presence,profile,reference_rows):
    required=required_keys(family);catalogue=set(MAPPING.values());found=[];ambiguous=[];unmapped=[];absent=[]
    for field,offset in sorted(required):
        key=(year+offset,field);label=field+'@'+str(year+offset)
        if field not in catalogue:unmapped.append(label);continue
        observations=presence.get(key,[])
        if not observations:absent.append(label)
        elif any(int(x['distinct_value_count'])!=1 for x in observations):ambiguous.append(label)
        else:found.append(label)
    model_held=family in ['F_SCORE','M_SCORE','Z_SCORE'] and profile!='Regular'
    annual=[r for r in reference_rows if r['period_kind']=='ANNUAL' and r['value'] is not None]
    return dict(symbol=symbol,year=year,family=family,status='REVIEWED_REFERENCE_VALUES_AVAILABLE' if annual else 'MODEL_APPLICABILITY_REVIEW_REQUIRED' if model_held else 'API_INPUT_QUALITY_NOT_YET_ESTABLISHED',
        reference_ids=[r['id'] for r in annual],reference_scopes=sorted({r['input_scope'] for r in annual}),
        observed_diagnostic_aliases=found,conflicting_aliases=ambiguous,not_observed_in_current_alias_inventory=absent,
        not_evaluated_by_current_alias_catalogue=unmapped,
        common_blockers=['UNITS_SCOPE_PERIOD_VINTAGE_VALUE_CLEARANCE_REQUIRED','PUBLICATION_AND_HISTORICAL_IDENTITY_NOT_ACCEPTED']+(['RAW_SNAPSHOT_PRICE_AND_SHARE_EVENT_BASIS_REQUIRED'] if family in ['PE','PB'] else []),
        numeric_value=None,strict_pit_ready=False,financial_features_allowed=False,
        absence_interpretation='NOT_FOUND_IN_DIAGNOSTIC_MAPPING_IS_NOT_PROOF_RAW_OR_PDF_LACKS_INPUT')

def summarize_symbols(symbols,metrics):
    by_symbol=defaultdict(list)
    for row in metrics:
        if row['value'] is not None:by_symbol[row['symbol']].append(row)
    result=[]
    for symbol in sorted(symbols):
        rows=by_symbol[symbol];families={r['family'] for r in rows};cohorts=defaultdict(set)
        for r in rows:
            if r['period_kind']=='ANNUAL':cohorts[(r['year'],r['cohort_id'],r['input_scope'])].add(r['family'])
        full=[dict(year=k[0],cohort_id=k[1],input_scope=k[2]) for k,v in cohorts.items() if set(FAMILIES)<=v]
        full_years={r['year'] for r in full}
        result.append(dict(symbol=symbol,reference_families=len(families),families=';'.join(sorted(families)),reference_value_rows=len(rows),
            annual_years=';'.join(map(str,sorted({r['year'] for r in rows if r['period_kind']=='ANNUAL'}))),
            full_six_family_reference_cohorts=json.dumps(full,ensure_ascii=False),has_six_family_reference_cohort=bool(full),
            full_market10y_six_family_reference_history=set(range(2016,2026))<=full_years,
            main_window_families=';'.join(sorted({r['family'] for r in rows if 2016<=r['year']<=2025})),
            production_ready=False,strict_pit_ready=False,next_action='USE_DECLARED_REFERENCE_VALUES_AND_REVIEW_REMAINING_INPUTS' if rows else 'REVIEW_EXISTING_API_AND_MAPPING_BEFORE_DECIDING_ANY_PDF_SUPPLEMENT'))
    return result

def run(root,config_path):
    root=Path(root);c=read(inside(root,config_path));out=inside(root,c['output_root']);pins={};events=[];metrics=[];errors=[];missing=[]
    def pin(p,expected=None):
        body=inside(root,p).read_bytes();sha=digest(body)
        if expected is not None and sha!=expected:raise ValueError('input changed: '+p)
        pins[p]=sha;return body
    def event(stage,**details):
        events.append(dict(at=datetime.now(timezone.utc).isoformat(),stage=stage,**details));state_file(out/'pipeline-status.json',stage,**details);print(json.dumps(events[-1],ensure_ascii=False),flush=True)
    def add(rows,source,ref,**kwargs):
        for raw in rows:
            r=metric_row(raw,source,ref,**kwargs);r['id']=digest(encoded(r))[:24];metrics.append(r)
    def clone_config(item,name):
        config=json.loads(pin(item['path'],item['sha256']));config['output_root']=c['output_root']+'/source-replays/'+name
        path=c['output_root']+'/source-replays/'+name+'-config.json';put(inside(root,path),config);pin(path);return path
    if c.get('version')!='financial-compute-first-v2' or c.get('network_allowed') is not False or c.get('pdf_download_allowed') is not False:raise ValueError('explicit offline/no-PDF contract required')
    for p in CODE+[config_path]:pin(p)
    event('VERIFYING_INPUTS',network_requests=0,pdf_downloads=0)
    inventory=c['inventory_result'];manifest=json.loads(pin(inventory['path']+'/manifest.json',inventory['manifest_sha256']))
    symbols=csv_read(pin(inventory['path']+'/symbols.csv',manifest['symbols.csv']));symbol_manifests=json.loads(pin(inventory['path']+'/symbol-manifests.json',manifest['symbol-manifests.json']))
    if len(symbols)!=1522 or len({s['symbol'] for s in symbols})!=1522:raise ValueError('exact1522 inventory required')
    # Reject accidental network use even inside reused reference adapters.
    with patch('urllib.request.OpenerDirector.open',side_effect=RuntimeError('NETWORK_DISABLED_COMPUTE_FIRST_NO_PDF')):
        try:
            event('RECOMPUTING_PILOT5_FROM_REVIEWED_INPUTS')
            b=c['baseline'];config=json.loads(pin(b['config']['path'],b['config']['sha256']));package=json.loads(pin(b['review']['path'],b['review']['sha256']))
            for p,sha in package['source_pins'].items():pin(p,sha)
            facts,_,valuation,review_pins=reviewed(root,inside(root,b['batch_root']))
            if review_pins!=[b['review']]:raise ValueError('pilot must use exactly pinned review, not an implicit latest review')
            rows,details,dependencies=compute(facts,valuation,config['primary_metric_variants'])
            for row in rows:
                scopes={f['scope'] for f in facts if f['symbol']==row['symbol']}
                if len(scopes)!=1:raise ValueError('mixed pilot input scopes')
                row['input_scope']=next(iter(scopes))
            old=csv_read(pin(b['metrics']['path'],b['metrics']['sha256']));expected={(r['symbol'],r['family']):r['value'] or None for r in old}
            for r in rows:
                previous=expected[r['symbol'],r['family']]
                if (r['value'] is None)!=(previous is None) or (previous is not None and Decimal(str(r['value']))!=Decimal(previous)):raise ValueError('pilot baseline arithmetic changed')
            if sum(r['value'] is not None for r in rows)!=29:raise ValueError('29/30 baseline or VNM F changed')
            path=c['output_root']+'/source-replays/pilot5-recomputed.json';put(inside(root,path),dict(metrics=rows,details=details,dependencies=dependencies));pin(path)
            add(rows,'PILOT5_FY2025',path)
            missing += [dict(source='PILOT5',**d) for d in dependencies if d['missing']]
        except (ValueError,OSError,KeyError,TypeError) as error:errors.append(dict(source='PILOT5',reason=str(error)))
        for item in c['reviewed_sources']:
            name=item['name']
            try:
                event('RECOMPUTING_REVIEWED_COHORT',source=name)
                cp=clone_config(item['config'],name);result=reviewed_run(root,cp,'run') if item['kind']=='HISTORY' else cohorts_run(root,cp,'run')
                rp=result['output'];m=json.loads(pin(rp+'/manifest.json'))
                for p,sha in json.loads(pin(rp+'/input-pins.json',m['input-pins.json'])).items():pin(p,sha)
                filename='annual-metrics.json' if item['kind']=='HISTORY' else 'metrics.json';rows=json.loads(pin(rp+'/'+filename,m[filename]))
                rows=[r for r in rows if r.get('computation')!='UNCHANGED_LEGACY_FY2025_REFERENCE']
                if item['kind']=='COHORT':rows=apply_cohort_metadata(rows,read(inside(root,cp))['cohorts'])
                add(rows,name,rp+'/'+filename)
                missing += [dict(source=name,symbol=r['symbol'],year=r['year'],family=r['family'],missing=r.get('missing_inputs',[]),status=r['status']) for r in rows if r['value'] is None and r.get('missing_inputs')]
                if item['kind']=='HISTORY':
                    quarter=json.loads(pin(rp+'/quarter-period-eps.json',m['quarter-period-eps.json']))
                    for r in quarter:
                        r=dict(r,year=int(r['period_end'][:4]));add([r],name+'_PERIOD',rp+'/quarter-period-eps.json',kind=r.get('interval','EXACT_PERIOD')+str(r.get('months','')))
            except (ValueError,OSError,KeyError,TypeError) as error:errors.append(dict(source=name,reason=str(error)))
        try:
            event('RECOMPUTING_SCALE_CACHED_REVIEW')
            item=c['scale'];pin(item['config']['path'],item['config']['sha256']);path=c['output_root']+'/source-replays/scale'
            if not inside(root,path).exists():scale_build(root,item['config']['path'],path)
            from ..ingestion.financial_documents import verify_inventory
            verify_inventory(inside(root,path));rows=json.loads(pin(path+'/references.json'))
            for r in rows:
                for family,value,variant in [('EPS',(r.get('disclosed_basic_eps_reference') or {}).get('value'),'DISCLOSED_BASIC_EPS_FY_REFERENCE'),('Z_SCORE',(r.get('z_reference') or {}).get('em_z_double_prime_reference'),'EM_Z_DOUBLE_PRIME_REFERENCE'),('PE',r.get('pe_annual_arithmetic'),'ANNUAL_PE_ARITHMETIC_NOT_TTM')]:
                    if value is not None:add([dict(symbol=r['symbol'],year=r['year'],family=family,value=value,status='RECOMPUTED_REVIEWED_REFERENCE',decision_date=r['decision_date'])],'SCALE_CACHE',path+'/references.json',variant=variant,scope='CONSOLIDATED')
        except (ValueError,OSError,KeyError,TypeError) as error:errors.append(dict(source='SCALE_CACHE',reason=str(error)))
        try:
            event('RECOMPUTING_FPT_CACHED_REFERENCE_FLOW')
            item=c['fpt_flow'];pin(item['config']['path'],item['config']['sha256']);path=c['output_root']+'/source-replays/fpt-flow'
            if not inside(root,path).exists():fpt_export(root,inside(root,item['config']['path']),inside(root,path))
            from ..ingestion.financial_documents import verify_inventory
            verify_inventory(inside(root,path));rows=json.loads(pin(path+'/flow.json'))['results']
            for r in rows:
                if r.get('value') is None:continue
                task=r['task'];value=r['value'];family='EPS' if task=='EPS_RECOMPUTE' else task
                if family not in FAMILIES:continue
                if isinstance(value,dict):value=value.get('annual_basic_eps_reference') if family=='EPS' else value.get('em_z_double_prime_reference') if family=='Z_SCORE' else None
                if value is not None:add([dict(r,family=family,value=value)],'FPT_CACHE_FLOW',path+'/flow.json',variant='ORIGINAL_FPT_'+task+'_REFERENCE',cohort='FPT:'+str(r['year'])+':'+str(r.get('pdf_sha256')),scope='CONSOLIDATED')
        except (ValueError,OSError,KeyError,TypeError) as error:errors.append(dict(source='FPT_CACHE_FLOW',reason=str(error)))
    event('SCREENING_ALL1522_API_INPUTS',source_replay_errors=len(errors),computed_reference_rows=sum(r['value'] is not None for r in metrics))
    by_key=defaultdict(list)
    for r in metrics:by_key[r['symbol'],r['year'],r['family']].append(r)
    tasks=[];blockers=[]
    for index,s in enumerate(sorted(symbols,key=lambda r:r['symbol']),1):
        sm=symbol_manifests[s['registry_id']];m=json.loads(pin(sm['path'],sm['sha256']));directory=str(Path(sm['path']).parent).replace('\\','/')
        presence=defaultdict(list)
        for row in csv_read(pin(directory+'/field-presence.csv',m['field-presence.csv'])):
            if row['mode']=='NAM':presence[int(row['year']),row['field']].append(row)
        grouped=defaultdict(lambda:dict(years=set(),unmapped=set(),absent=set(),conflicting=set()))
        for year in range(2013,2026):
            for family in FAMILIES:
                task=classify_api_task(s['symbol'],year,family,presence,s['diagnostic_template_family'],by_key[s['symbol'],year,family]);tasks.append(task)
                if not task['reference_ids']:
                    b=grouped[family];b['years'].add(year)
                    for name,key in [('unmapped','not_evaluated_by_current_alias_catalogue'),('absent','not_observed_in_current_alias_inventory'),('conflicting','conflicting_aliases')]:b[name].update(x.rsplit('@',1)[0] for x in task[key])
        for family,b in grouped.items():blockers.append(dict(symbol=s['symbol'],family=family,years=';'.join(map(str,sorted(b['years']))),not_evaluated_in_qa_alias_catalogue=';'.join(sorted(b['unmapped'])),not_observed_aliases=';'.join(sorted(b['absent'])),conflicting_aliases=';'.join(sorted(b['conflicting'])),diagnostic_template_family=s['diagnostic_template_family'],api_failed_requests=s['failed_requests'],next_action='REVIEW_EXISTING_API_MAPPING_AND_CACHED_REVIEWED_EVIDENCE_FIRST',pdf_supplement_status='NOT_YET_DETERMINED;NO_DOWNLOAD_PLAN_OR_DOWNLOAD',requires_owner_review_before_any_pdf_plan=True))
        if index%100==0:event('SCREENING_ALL1522_API_INPUTS',completed=index,total=len(symbols),last_symbol=s['symbol'])
    inventory=summarize_symbols([s['symbol'] for s in symbols],metrics)
    return finish(root,c,out,pins,events,metrics,tasks,blockers,missing,inventory,errors)

def finish(root,c,out,pins,events,metrics,tasks,blockers,missing,inventory,errors):
    values=[r for r in metrics if r['value'] is not None];annual=[r for r in values if r['period_kind']=='ANNUAL'];families={f:len({r['symbol'] for r in values if r['family']==f}) for f in FAMILIES}
    summary=dict(status='COMPLETE_OFFLINE_COMPUTE_FIRST_ASSESSMENT' if not errors else 'PARTIAL_SOURCE_REPLAY_HELD',symbols_assessed=len(inventory),annual_symbol_year_family_tasks=len(tasks),symbols_with_any_reviewed_reference=sum(r['reference_families']>0 for r in inventory),symbols_without_reviewed_numeric_reference=sum(r['reference_families']==0 for r in inventory),symbols_with_full_six_family_reference_cohort=sum(r['has_six_family_reference_cohort'] for r in inventory),symbols_with_complete10y_six_family_reference_history=sum(r['full_market10y_six_family_reference_history'] for r in inventory),symbols_with_values_by_family=families,reference_value_rows=len(values),distinct_annual_symbol_year_family_keys=len({(r['symbol'],r['year'],r['family']) for r in annual}),source_replay_errors=errors,network_requests=0,pdf_downloads=0,pdf_download_plan_created=False,api_candidates_auto_promoted=0,strict_pit_ready=False,financial_features_allowed=False,full_vector_basis='SIX_FAMILY_REFERENCE_COHORT_IS_NOT_CURRENT_TTM_OR_BACKTEST_READY_VECTOR',alias_absence_is_not_raw_data_absence=True)
    csv_cols=lambda rows:sorted({k for r in rows for k in r})
    def tabular(rows):return [{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows]
    products={'summary.json':encoded(summary),'computed-reference-metrics.json':encoded(metrics),'input-pins.json':encoded(pins),'source-replay-errors.json':encoded(errors),'reviewed-missing-inputs.json':encoded(missing),'process-log.jsonl':b''.join((json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n').encode() for e in events)}
    for name,rows in [('computed-reference-metrics.csv',metrics),('metric-tasks.csv',tasks),('input-blockers.csv',blockers),('symbols-readiness.csv',inventory)]:products[name]=csv_body(tabular(rows),csv_cols(rows))
    manifest={name:digest(body) for name,body in products.items()};result=out/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(result/name,body)
    put(result/'manifest.json',manifest)
    report=inside(root,c['report_root']);relative=result.relative_to(root).as_posix();import os
    rel=os.path.relpath(result,report).replace('\\','/');complete=[r['symbol'] for r in inventory if r['has_six_family_reference_cohort']];some=[r['symbol'] for r in inventory if r['reference_families']>0]
    table='\n'.join('| '+r['symbol']+' | '+r['families'].replace(';',', ')+' | '+r['annual_years'].replace(';',', ')+' | '+('Có' if r['has_six_family_reference_cohort'] else 'Chưa')+' |' for r in inventory if r['reference_families'])
    text=f'''# Compute-first: tính trước từ input đạt yêu cầu, chưa bổ sung PDF

## Kết quả đã chốt

Đã đánh giá **{len(inventory):,} mã**, tương ứng **{len(tasks):,} tasks annual 2013–2025 × 6 family**. Tái tính hoàn toàn offline từ các input đã được review và có bằng chứng đang lưu trên máy. **Không gọi mạng, không tải PDF, không OCR mới và chưa tạo kế hoạch bổ sung PDF.**

- **{summary['symbols_with_any_reviewed_reference']} mã** có ít nhất một family reference có giá trị.
- **{len(complete)} mã** có cohort reference đủ 6 family trong cùng năm/scope/vintage: **{', '.join(complete)}**.
- **{summary['symbols_with_complete10y_six_family_reference_history']} mã** đủ cả 6 family trong toàn bộ cửa sổ market 2016–2025.
- Có **{len(values)} dòng kết quả reference**; **{summary['distinct_annual_symbol_year_family_keys']} khoá annual symbol–year–family** khác nhau. Một số dòng là các snapshot/vintage khác, không được cộng thành mã mới.

| Mã | Family có giá trị | Năm annual đã có reference | Có cohort đủ 6 family |
|---|---|---|---|
{table}

Số mã có giá trị theo family: **{families}**. EPS có thể là annual hoặc kỳ được thuyết minh rõ; P/E annual reference không phải P/E TTM hiện tại. Mỗi dòng giữ kỳ, scope, variant, snapshot giá và evidence riêng. M-score vẫn là sensitivity VAS đã chốt; Z dùng annual EM Z″ +3,25. Không áp mô hình doanh nghiệp thường cho ngân hàng/chứng khoán/template chưa rõ.

## Quá trình thực hiện

1. Xác minh manifest inventory 1.522 mã và hash của từng bảng field presence; không đọc lại/crawl toàn bộ raw từ Internet.
2. Tính lại pilot5 từ reviewed notes, so Decimal với baseline 29/30. VNM F vẫn thiếu input; không suy current portion bằng 0.
3. Tái chạy các calculator đã chốt cho history, ACV/GAS, nhóm PHP/VCS/VEA/PAN và FPT cache flow. Dùng PDF/OCR và reviewed facts đã có, chỉ kiểm hash/replay, không tải hoặc OCR mới.
4. Kiểm scope theo khai báo cohort để nhóm đúng các family của cùng báo cáo. V2 sửa metadata nhóm scope của ACV bị bỏ trống ở một số row; **không đổi giá trị, công thức, input hoặc gate**.
5. Screen từng task theo required keys/aliases hiện có; tách field chưa được mapping đánh giá với alias không thấy trong kỳ. Không coi thiếu alias là raw/PDF thiếu field, không tự nâng API candidate thành input đã xác minh.
6. Gộp blockers theo mã/family và giữ riêng missing inputs của các cohort reviewed. Nguồn bị lỗi sẽ được giữ riêng, không chặn các nguồn đủ evidence.

## File bàn giao

- [Readiness theo từng mã]({rel}/symbols-readiness.csv).
- [Giá trị đã tính lại: CSV]({rel}/computed-reference-metrics.csv), [JSON kèm provenance]({rel}/computed-reference-metrics.json).
- [Task theo mã/năm/family]({rel}/metric-tasks.csv).
- [Blockers theo mã/family]({rel}/input-blockers.csv): **đây chưa phải danh sách tải PDF**.
- [Input còn thiếu trong các cohort reviewed]({rel}/reviewed-missing-inputs.json).
- [Nhật ký quá trình]({rel}/process-log.jsonl), [nguồn replay bị giữ]({rel}/source-replay-errors.json), [summary]({rel}/summary.json).

## Những gì chưa hoàn tất và cần báo trước khi bổ sung

Còn **{summary['symbols_without_reviewed_numeric_reference']} mã** chưa có kết quả reference được chốt trong các nguồn reviewed hiện tại. **Không kết luận tất cả các mã này cần tải PDF**: trước hết còn mapping/API/cached evidence, đơn vị, scope, kỳ và vintage phải được review. Alias inventory của QA chỉ là một phần input catalogue, chưa đủ chứng minh mọi field có/không có trong raw.

Các nhóm input thường cần kiểm tra thêm:

| Family | Input/basis cần làm rõ trước khi tính |
|---|---|
| EPS | Numerator đúng thuyết minh và weighted-average shares; không dùng current shares hoặc chỉ chép EPS từ web |
| P/E | EPS đúng kỳ/TTM, raw price tại snapshot và share basis; annual P/E reference không thay P/E TTM |
| P/B | Parent common equity, common shares và quyền/sự kiện tại ngày định giá |
| F | Tài sản các năm đầu kỳ, issuance của parent và nợ dài hạn gồm current portion; VNM F giữ thiếu |
| M | Receivables, net tangible PPE và depreciation đúng định nghĩa; không thay bằng aggregate D&A |
| Z | EBIT đã reconcile, balance/retained earnings/equity/liabilities cùng basis |

Đã ghi blockers để báo owner; **chưa lập download plan và chưa bổ sung PDF**. Những phần có thể xử lý bằng API/cache sẽ được ưu tiên trước. Nếu cần nguồn thuyết minh/PDF mới, phải báo lại phạm vi và lý do trước khi lên kế hoạch theo yêu cầu của owner.

## Giới hạn sử dụng

Đủ 6 family reference trong một cohort **không đồng nghĩa có vector current-TTM hoặc dữ liệu backtest sẵn sàng**. Các năm, ngày giá, scope và vintage không được trộn. Kết quả reference tách khỏi production/PIT acceptance; financial/research gates vẫn false. Source replay errors: **{len(errors)}**. Baseline pilot FY2025 29/30 được giữ nguyên; không cộng số mới vào baseline để che input VNM F còn thiếu.
'''
    put(report/'report.md',text.encode('utf-8'));put(report/'result-ref.json',dict(path=relative,manifest_sha256=digest((result/'manifest.json').read_bytes())))
    state_file(out/'pipeline-status.json',summary['status'],output=relative,report=(report/'report.md').relative_to(root).as_posix(),symbols_assessed=len(inventory),symbols_with_any_reviewed_reference=summary['symbols_with_any_reviewed_reference'],pdf_downloads=0)
    return dict(summary,output=relative,report=(report/'report.md').relative_to(root).as_posix())
