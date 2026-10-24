"""Expanded raw-API input review and isolated arithmetic diagnostics; no acceptance.

No network/PDF/OCR. Provider partitions and original source hashes remain intact.
Conditional arithmetic is never a reviewed reference or a financial feature.
"""
import csv
import io
import json
import hashlib
import shutil
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

from .financial_acquisition_overnight import state_file
from .financial_cafef_pilot import FAMILIES, required_keys
from .financial_history_documents import put, read
from .financial_history_qa import ALIASES, MAPPING, norm
from .financial_inventory_qa import csv_body
from .financial_template_candidates import parse_candidates
from ..features.financial_vas_reference import calculate_vas_f_score
from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside

VERSION = 'financial-api-input-review-v1'
# Codes are provider codes, not inferred Vietnamese accounting-code positions.
# Auxiliary fields deliberately do NOT alias weighted shares, parent issuance,
# current debt portion, pure-period PPE depreciation or reconciled EBIT.
EXTRA_ALIASES = [
    ('CDKT', 'TN', '131', 'receivables', 'Phải thu ngắn hạn của khách hàng'),
    ('CDKT', 'TN', '221', 'net_tangible_ppe', 'Tài sản cố định hữu hình'),
    ('CDKT', 'TN', '222', 'owned_tangible_ppe_cost', 'Nguyên giá'),
    ('CDKT', 'TN', '223', 'owned_tangible_ppe_accumulated_depreciation', 'Giá trị hao mòn lũy kế (*)'),
    ('CDKT', 'TN', '224', 'finance_lease_ppe', 'Tài sản cố định thuê tài chính'),
    ('CDKT', 'TN', '227', 'intangible_assets', 'Tài sản cố định vô hình'),
    ('CDKT', 'NV', '411', 'paid_in_capital_amount', 'Vốn góp của chủ sở hữu'),
    ('CDKT', 'NV', '411a', 'common_share_capital_amount', '- Cổ phiếu phổ thông có quyền biểu quyết'),
    ('CDKT', 'NV', '429', 'noncontrolling_interests', 'Lợi ích cổ đông không kiểm soát'),
    ('KQKD', 'KQKD', '1', 'gross_revenue', 'Doanh thu bán hàng và cung cấp dịch vụ'),
    ('KQKD', 'KQKD', '2', 'revenue_deductions', 'Các khoản giảm trừ doanh thu'),
    ('KQKD', 'KQKD', '22', 'finance_income', 'Doanh thu hoạt động tài chính'),
    ('KQKD', 'KQKD', '23', 'finance_expense', 'Chi phí tài chính'),
    ('KQKD', 'KQKD', '27', 'associate_profit', '- Phần lãi/lỗ trong công ty liên doanh, liên kết'),
    ('KQKD', 'KQKD', '30', 'reported_operating_profit', 'Lợi nhuận thuần từ hoạt động kinh doanh'),
    ('KQKD', 'KQKD', '31', 'other_income', 'Thu nhập khác'),
    ('KQKD', 'KQKD', '32', 'other_expense', 'Chi phí khác'),
    ('KQKD', 'KQKD', '40', 'other_profit', 'Lợi nhuận khác'),
    ('KQKD', 'KQKD', '51', 'current_tax_expense', 'Chi phí thuế TNDN hiện hành'),
    ('KQKD', 'KQKD', '52', 'deferred_tax_expense', 'Chi phí thuế TNDN hoãn lại'),
    ('KQKD', 'KQKD', '62', 'noncontrolling_profit', '- Lợi ích của cổ đông thiểu số'),
    ('KQKD', 'KQKD', '71', 'vendor_diluted_eps', 'Lãi suy giảm trên cổ phiếu (Đồng/1 cổ phiếu)'),
    ('LCTT', 'HDKD', 'HDKD_2', 'cashflow_profit_before_tax', 'Lợi nhuận trước thuế'),
    ('LCTT', 'HDKD', 'HDKD_4', 'aggregate_fixed_property_depreciation_amortization', '- Khấu hao TSCĐ và BĐSĐT'),
    ('LCTT', 'HDKD', 'HDKD_8', 'cashflow_interest_adjustment', '- Chi phí lãi vay'),
    ('LCTT', 'HDTC', 'HDTC_31', 'cash_equity_proceeds_group', 'Tiền thu từ phát hành cổ phiếu, nhận vốn góp của chủ sở hữu'),
    ('LCTT', 'HDTC', 'HDTC_37', 'cash_nci_contributions', 'Tiền thu từ vốn góp của cổ đông không kiểm soát'),
]
EXPANDED = {(s, g, code, norm(label)): f for s, g, code, f, label in ALIASES + EXTRA_ALIASES}
FORMULAS = [
    ('ASSETS_CAPITAL', 'total_assets', ['total_capital']),
    ('ASSETS_LIABILITIES_EQUITY', 'total_assets', ['total_liabilities', 'total_equity']),
    ('ASSET_PARTS', 'total_assets', ['current_assets', 'noncurrent_assets']),
    ('LIABILITY_PARTS', 'total_liabilities', ['current_liabilities', 'noncurrent_liabilities']),
    ('GROSS_PROFIT', 'net_revenue', ['cost_of_goods_sold', 'gross_profit']),
    ('NET_REVENUE', 'gross_revenue', ['revenue_deductions', 'net_revenue']),
    ('OTHER_PROFIT', 'other_income', ['other_expense', 'other_profit']),
    ('PRETAX_BRIDGE', 'profit_before_tax', ['reported_operating_profit', 'other_profit']),
    ('AFTERTAX_BRIDGE', 'profit_before_tax', ['net_profit', 'current_tax_expense', 'deferred_tax_expense']),
    ('PROFIT_ATTRIBUTION', 'net_profit', ['parent_net_profit', 'noncontrolling_profit']),
    ('OWNED_PPE_NET', 'net_tangible_ppe', ['owned_tangible_ppe_cost', 'owned_tangible_ppe_accumulated_depreciation']),
]
Z_INPUTS = {'current_assets', 'current_liabilities', 'total_assets', 'retained_earnings',
            'total_equity', 'total_liabilities', 'profit_before_tax', 'interest_expense'}
GATES = dict(accepted=False, strict_pit_ready=False, financial_features_allowed=False)
CODE = ['src/delta_t1/experiments/financial_api_input_review.py',
        'scripts/financial_api_input_review.py',
        'src/delta_t1/experiments/financial_template_candidates.py',
        'src/delta_t1/experiments/financial_history_qa.py',
        'src/delta_t1/experiments/financial_cafef_pilot.py',
        'src/delta_t1/features/financial_vas_reference.py',
        'src/delta_t1/features/financial_reference.py',
        'src/delta_t1/ingestion/financial_pilot_readiness.py']


def csv_rows(raw):
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))


def csv_bytes(rows):
    flattened = [{k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (list, dict)) else v
                  for k, v in r.items()} for r in rows]
    return csv_body(flattened, sorted({k for r in flattened for k in r}) or ['status'])


def map_field(row):
    if row['mapping_status'] != 'UNIQUE_CODE_LABEL_CANDIDATE':
        return None
    return EXPANDED.get((row['statement'], row['group'], row['raw_code'], norm(row.get('label'))))


def resolve(observations):
    """Equal values retain all sources; equality does not establish a vintage."""
    if any(r['value'] is None or r['value_status'] != 'NUMERIC_CANDIDATE' for r in observations):
        return None, 'MISSING_OR_INVALID_OBSERVATION'
    values = {Decimal(r['value']) for r in observations}
    if len(values) != 1:
        return None, 'CONFLICTING_OBSERVATIONS_NO_SELECTION'
    return str(next(iter(values))), 'UNIQUE_VALUE_UNREVIEWED_VINTAGE'


def accounting(values):
    checks = []
    with localcontext() as ctx:
        ctx.prec = 48
        for name, lhs, rhs in FORMULAS:
            if not {lhs, *rhs} <= values.keys():
                checks.append(dict(check=name, status='NOT_EVALUATED_MISSING_INPUTS', difference=None))
                continue
            delta = Decimal(values[lhs]) - sum(Decimal(values[f]) for f in rhs)
            checks.append(dict(check=name, status='RAW_EQUALITY' if delta == 0 else 'RAW_DIFFERENCE', difference=str(delta)))
    return checks


def arithmetic_diagnostics(year, provider_type, data, checks, displaced, regular):
    """Evaluate hypotheses only, with no accepted EBIT/units/scope assertion."""
    current = data.get((year, provider_type), {})
    status = 'MODEL_APPLICABILITY_REVIEW_REQUIRED' if not regular else 'INPUTS_OR_QUALITY_HELD'
    z = dict(family='Z_SCORE', year=year, provider_type=provider_type, value=None, status=status,
             kind='API_CONDITIONAL_ARITHMETIC_NOT_REVIEWED_REFERENCE', **GATES)
    core = {'ASSETS_CAPITAL', 'ASSETS_LIABILITIES_EQUITY', 'ASSET_PARTS', 'LIABILITY_PARTS',
            'GROSS_PROFIT', 'PRETAX_BRIDGE', 'AFTERTAX_BRIDGE'}
    passed = {r['check'] for r in checks if r['status'] == 'RAW_EQUALITY'}
    if regular and not displaced and Z_INPUTS <= current.keys() and core <= passed and not any(r['status'] == 'RAW_DIFFERENCE' for r in checks):
        with localcontext() as ctx:
            ctx.prec = 36
            v = {f: Decimal(current[f]) for f in Z_INPUTS}
            if v['total_assets'] > 0 and v['total_liabilities'] > 0 and v['interest_expense'] >= 0:
                ebit = v['profit_before_tax'] + v['interest_expense']
                score = Decimal('3.25') + Decimal('6.56')*(v['current_assets']-v['current_liabilities'])/v['total_assets'] + Decimal('3.26')*v['retained_earnings']/v['total_assets'] + Decimal('6.72')*ebit/v['total_assets'] + Decimal('1.05')*v['total_equity']/v['total_liabilities']
                z.update(value=str(score), status='CONDITIONAL_ARITHMETIC_ONLY', candidate_ebit=str(ebit),
                    assumptions=['SAME_MONETARY_UNIT_UNVERIFIED', 'SAME_SCOPE_VINTAGE_UNVERIFIED',
                                 'PBT_PLUS_EXPENSED_INTEREST_RECONCILIATION_NOT_ACCEPTED', 'REGULAR_TEMPLATE_NOT_HISTORICAL_SECTOR_PROOF'])
    # Partial F-signals are not a partial score, total, bound or accepted input.
    f = dict(family='F_SCORE', year=year, provider_type=provider_type, value=None, status=status,
             kind='API_SIGNAL_DIAGNOSTICS_NOT_F_SCORE', signals={},
             assumptions=['SAME_MONETARY_UNIT_UNVERIFIED', 'SAME_SCOPE_VINTAGE_UNVERIFIED'], **GATES)
    if regular and not displaced and not any(r['status']=='RAW_DIFFERENCE' for r in checks):
        values = {(field, offset):value for offset in [0, -1, -2]
                  for field, value in data.get((year+offset, provider_type), {}).items()}
        result = calculate_vas_f_score(values)
        f.update(signals=result['signals'], known_signals=result['known_signals'], status='PARTIAL_SIGNAL_ARITHMETIC_ONLY')
        if result['value'] is not None:
            raise ValueError('raw aliases must not manufacture parent issuance/current-debt proof')
    return [z, f]


def family_task(symbol, year, family, partitions, profile, reviewed):
    requirements = sorted(required_keys(family))
    evaluations = []
    for ptype in sorted({p for y, p in partitions if y == year}, key=str):
        missing = [dict(field=f, year=year+offset) for f, offset in requirements
                   if f not in partitions.get((year+offset, ptype), {})]
        evaluations.append(dict(provider_type=ptype, missing_inputs=missing))
    # Never combine partial inputs from different provider_type partitions.
    no_alias = sorted({f for f, _ in requirements if f not in set(EXPANDED.values())})
    refs = [r['id'] for r in reviewed if r['symbol']==symbol and r['year']==year and r['family']==family
            and r['period_kind']=='ANNUAL' and r['value'] is not None]
    return dict(symbol=symbol, year=year, family=family,
        status='EXISTING_REVIEWED_REFERENCE_AVAILABLE' if refs else
               'MODEL_APPLICABILITY_REVIEW_REQUIRED' if family in ['F_SCORE','M_SCORE','Z_SCORE'] and profile!='Regular' else
               'RAW_INPUT_AND_EVIDENCE_REVIEW_REQUIRED',
        reviewed_reference_ids=refs, required_fields_without_direct_api_alias=no_alias,
        partition_input_evaluations=evaluations,
        missing_interpretation='EXACT_ALIAS_NOT_OBSERVED_OR_AMBIGUOUS_IN_ACQUIRED_ANNUAL_PAGES_NOT_PROOF_OF_NONPUBLICATION',
        evidence_blockers=['MONETARY_UNITS', 'SCOPE_FRAMEWORK', 'DOCUMENT_VINTAGE', 'PUBLICATION_AND_HISTORICAL_IDENTITY']+
                          (['DATED_RAW_PRICE_AND_SHARE_EVENT_BASIS'] if family in ['PE','PB'] else []),
        value=None, pdf_supplement_status='UNDECIDED_REVIEW_API_CACHE_FIRST_NO_DOWNLOAD_PLAN', **GATES)


def checkpoint(root, out, job_sha):
    manifest = read(out/'manifest.json')
    for name, sha in manifest.items():
        if digest((out/name).read_bytes()) != sha:
            raise ValueError('checkpoint changed: '+str(out/name))
    pins = read(out/'input-pins.json')
    if pins['job_sha256'] != job_sha:
        raise ValueError('checkpoint belongs to a different job')
    for name, sha in pins['sources'].items():
        if digest(inside(root, name).read_bytes()) != sha:
            raise ValueError('checkpoint input changed: '+name)
    return read(out/'summary.json')


def process_symbol(root, out, member, source_manifest, job_sha, reviewed):
    if out.exists():
        return checkpoint(root, out, job_sha)
    pins = {}
    def pin(path, expected):
        body = inside(root, path).read_bytes()
        if digest(body) != expected:
            raise ValueError('source hash differs: '+path)
        pins[path] = expected
        return body
    sm = json.loads(pin(source_manifest['path'], source_manifest['sha256']))
    qa = Path(source_manifest['path']).parent.as_posix()
    source_pins = json.loads(pin(qa+'/input-pins.json', sm['input-pins.json']))['sources']
    shifts = json.loads(pin(qa+'/displacements.json', sm['displacements.json']))
    qa_findings = json.loads(pin(qa+'/arithmetic-findings.json', sm['arithmetic-findings.json']))
    profile = member['diagnostic_template_family']
    buckets, catalogue = defaultdict(list), {}
    counts = Counter()
    # Verify receipts even when their mode is not selected; then read only annual raw.
    for path, sha in source_pins.items():
        if '/receipts/' not in path:
            continue
        receipt = json.loads(pin(path, sha));task = receipt['task']
        if task['symbol'] != member['symbol'] or Path(path).stem != task['id']:
            raise ValueError('receipt identity differs')
        if task['kind'] != 'REPORT' or task['mode'] != 'NAM':
            continue
        counts['annual_receipts'] += 1
        if not receipt.get('record'):
            counts['annual_receipts_without_record'] += 1
            continue
        rec = receipt['record']
        if source_pins.get(rec['path']) != rec['sha256']:
            raise ValueError('raw not in QA source pin chain')
        body = pin(rec['path'], rec['sha256'])
        rows = parse_candidates(body, task, rec['path'], rec['sha256'])
        counts['annual_raw_responses'] += 1
        for row in rows:
            if not 2012 <= row['year'] <= 2025 or row['quarter'] != 0:
                continue
            counts['annual_candidate_cells'] += 1
            if row['provider_unit'] is None:
                counts['cells_without_provider_unit'] += 1
            labelkey = (row['statement'], row['group'], row['raw_code'], row['label'], row['mapping_status'])
            item = catalogue.setdefault(labelkey, dict(statement=row['statement'], group=row['group'], raw_code=row['raw_code'], label=row['label'],
                mapping_status=row['mapping_status'], field=map_field(row), cells=0, sample_source=row['source_path'], template_sha256=row['template_sha256']))
            item['cells'] += 1
            if profile != 'Regular':
                continue
            field = map_field(row)
            if field:
                counts['mapped_cells'] += 1
                if field not in set(MAPPING.values()):
                    counts['new_field_cells'] += 1
                observation = {k:row[k] for k in ['value','value_status','raw_code','label','source_path','source_sha256',
                    'template_sha256','raw_cell_ordinal','period_occurrence','provider_unit','provider_header']}
                buckets[row['year'], row['provider_type'], field].append(observation)
    resolved, fields, conflicts = defaultdict(dict), [], []
    for (year, ptype, field), observations in sorted(buckets.items(), key=str):
        value, status = resolve(observations)
        fields.append(dict(symbol=member['symbol'], year=year, provider_type=ptype, field=field,
            value=value, status=status, observations=observations, **GATES))
        if value is not None:
            resolved[year, ptype][field] = value
        elif status.startswith('CONFLICTING'):
            conflicts.append(dict(symbol=member['symbol'], year=year, provider_type=ptype, field=field, status=status))
    checks, diagnostics = [], []
    for (year, ptype), values in sorted(resolved.items(), key=str):
        if year < 2013:
            continue
        part = accounting(values)
        checks.extend(dict(symbol=member['symbol'], year=year, provider_type=ptype, **r) for r in part)
        held = any(r['year']==year and r['annual_provider_type']==ptype for r in shifts)
        held = held or any(r['period'][1:5]==[year,0,'NAM',ptype] for r in qa_findings)
        # Do not use anomalous historical comparators for F signal arithmetic.
        comparator_held = any(r['year'] in [year-1,year-2] and r['annual_provider_type']==ptype for r in shifts)
        comparator_held = comparator_held or any(
            r['period'][1] in [year-1,year-2] and r['period'][2:5]==[0,'NAM',ptype] for r in qa_findings)
        comparator_held = comparator_held or any(
            r['status']=='RAW_DIFFERENCE' for offset in [-1,-2]
            for r in accounting(resolved.get((year+offset,ptype),{})))
        computed = arithmetic_diagnostics(year, ptype, resolved, part, held, profile=='Regular')
        if comparator_held:
            computed[1].update(signals={}, known_signals=0, status='COMPARATOR_QUALITY_HELD')
        diagnostics.extend(dict(symbol=member['symbol'], **r) for r in computed)
    tasks = [family_task(member['symbol'], year, family, resolved, profile, reviewed)
             for year in range(2013,2026) for family in FAMILIES]
    zyears = sorted({r['year'] for r in diagnostics if r['family']=='Z_SCORE' and r['value'] is not None and 2016<=r['year']<=2025})
    summary = dict(symbol=member['symbol'], registry_id=member['registry_id'], diagnostic_template_family=profile,
        **counts, resolved_field_keys=sum(len(v) for v in resolved.values()), conflicting_field_keys=len(conflicts),
        conditional_z_rows=sum(r['family']=='Z_SCORE' and r['value'] is not None for r in diagnostics),
        conditional_z_main_years=zyears, conditional_z_full10y=zyears==list(range(2016,2026)),
        known_f_signal_arithmetic=sum(r.get('known_signals',0) for r in diagnostics if r['family']=='F_SCORE'),
        reviewed_reference_rows=sum(r['symbol']==member['symbol'] and r['value'] is not None for r in reviewed),
        new_accepted_metric_rows=0, new_verified_complete10y=False, **GATES)
    products = {'summary.json':encoded(summary), 'input-pins.json':encoded(dict(job_sha256=job_sha, sources=pins)),
        'field-inputs.json':encoded(fields), 'field-inputs.csv':csv_bytes(fields), 'template-labels.json':encoded(list(catalogue.values())),
        'conflicts.json':encoded(conflicts), 'accounting-checks.json':encoded(checks),
        'api-arithmetic-diagnostics.json':encoded(diagnostics), 'metric-tasks.json':encoded(tasks)}
    for name, body in products.items():
        put(out/name, body)
    put(out/'manifest.json', {name:digest(body) for name, body in products.items()})
    return summary


def run(root, config_path):
    root=Path(root);c=read(inside(root,config_path));base=inside(root,c['output_root']);pins={}
    if c['version']!=VERSION or any(c.get(k) is not False for k in ['network_allowed','pdf_download_allowed','ocr_allowed','numeric_acceptance_allowed']):
        raise ValueError('explicit offline diagnostic contract required')
    def pin(item):
        body=inside(root,item['path']).read_bytes();sha=digest(body)
        if sha!=item['sha256']:
            raise ValueError('job input changed: '+item['path'])
        pins[item['path']]=sha
        return body
    for path in CODE+[config_path]:
        body=inside(root,path).read_bytes();pins[path]=digest(body)
    inv=c['inventory'];manifest=json.loads(pin(dict(path=inv['path']+'/manifest.json',sha256=inv['manifest_sha256'])))
    members=csv_rows(pin(dict(path=inv['path']+'/symbols.csv',sha256=manifest['symbols.csv'])))
    symbol_pins=json.loads(pin(dict(path=inv['path']+'/symbol-manifests.json',sha256=manifest['symbol-manifests.json'])))
    reference=c['reviewed_result'];rm=json.loads(pin(dict(path=reference['path']+'/manifest.json',sha256=reference['manifest_sha256'])))
    reviewed=json.loads(pin(dict(path=reference['path']+'/computed-reference-metrics.json',sha256=rm['computed-reference-metrics.json'])))
    if len(members)!=1522 or len({r['symbol'] for r in members})!=1522:
        raise ValueError('exact1522 inventory required')
    job_sha=digest(encoded(pins));job=base/'jobs'/job_sha[:20]
    put(job/'input-pins.json',pins)
    put(job/'mapping-catalogue.json', [dict(statement=s,group=g,raw_code=code,normalized_label=label,field=f)
        for (s,g,code,label),f in sorted(EXPANDED.items())])
    summaries=[];state=base/'pipeline-status.json'
    with patch('urllib.request.OpenerDirector.open',side_effect=RuntimeError('OFFLINE_NO_PDF_NO_OCR')):
        with ThreadPoolExecutor(max_workers=4) as pool:
            def work(m):
                return process_symbol(root,job/'symbols'/m['registry_id'],m,symbol_pins[m['registry_id']],job_sha,reviewed)
            state_file(state,'EXPANDED_API_REVIEW_RUNNING',completed=0,total=len(members),job=job.relative_to(root).as_posix())
            for i,result in enumerate(pool.map(work,sorted(members,key=lambda r:r['symbol'])),1):
                summaries.append(result)
                if i%25==0 or i==len(members):
                    state_file(state,'EXPANDED_API_REVIEW_RUNNING',completed=i,total=len(members),last_symbol=result['symbol'],
                        job=job.relative_to(root).as_posix(),conditional_z_rows=sum(r['conditional_z_rows'] for r in summaries),new_accepted_metric_rows=0)
                    print(json.dumps(dict(completed=i,total=len(members),last_symbol=result['symbol'])),flush=True)
    return consolidate(root,c,job,pins,summaries,reviewed)


def consolidate(root,c,job,pins,summaries,reviewed):
    blockers=[]
    task_count=0;z_count=0;z_symbols=set();check_statuses=Counter()
    label_catalogue={};symbol_manifests={}
    spool=job/'consolidation';spool.mkdir(exist_ok=True)
    columns={
        'metric-tasks.csv':sorted(['symbol','year','family','status','reviewed_reference_ids','required_fields_without_direct_api_alias',
            'partition_input_evaluations','missing_interpretation','evidence_blockers','value','pdf_supplement_status',*GATES]),
        'api-arithmetic-diagnostics.csv':sorted(['family','year','provider_type','value','status','kind','symbol','candidate_ebit','assumptions','signals','known_signals',*GATES]),
        'accounting-checks.csv':['symbol','year','provider_type','check','status','difference'],
    }
    handles={name:(spool/name).open('w',encoding='utf-8',newline='') for name in columns}
    writers={name:csv.DictWriter(handles[name],fieldnames=cols,lineterminator='\n') for name,cols in columns.items()}
    for writer in writers.values():writer.writeheader()
    def append(name,rows):
        for row in rows:
            writers[name].writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    for s in summaries:
        out=job/'symbols'/s['registry_id'];m=read(out/'manifest.json')
        for name,sha in m.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('output changed before consolidate')
        symbol_manifests[s['registry_id']]=dict(path=(out/'manifest.json').relative_to(root).as_posix(),sha256=digest((out/'manifest.json').read_bytes()))
        st=read(out/'metric-tasks.json');task_count+=len(st);append('metric-tasks.csv',st)
        diagnostic_rows=read(out/'api-arithmetic-diagnostics.json');append('api-arithmetic-diagnostics.csv',diagnostic_rows)
        zrows=[r for r in diagnostic_rows if r['family']=='Z_SCORE' and r['value'] is not None]
        z_count+=len(zrows);z_symbols.update(r['symbol'] for r in zrows)
        check_rows=read(out/'accounting-checks.json');append('accounting-checks.csv',check_rows)
        check_statuses.update(r['status'] for r in check_rows)
        for row in read(out/'template-labels.json'):
            key=json.dumps([row[k] for k in ['statement','group','raw_code','label','mapping_status']],ensure_ascii=False)
            entry=label_catalogue.setdefault(key,dict(row,cells=0,symbols=0));entry['cells']+=row['cells'];entry['symbols']+=1
        for family in FAMILIES:
            selected=[t for t in st if t['family']==family and not t['reviewed_reference_ids']]
            blockers.append(dict(symbol=s['symbol'],family=family,unreviewed_years=[t['year'] for t in selected],
                required_fields_without_direct_api_alias=sorted({f for t in selected for f in t['required_fields_without_direct_api_alias']}),
                evidence_ref=(out/'metric-tasks.json').relative_to(root).as_posix(),
                next_action='REVIEW_EXACT_RAW_MAPPING_AND_CACHED_EVIDENCE_NO_AUTOMATIC_PDF',pdf_supplement_status='UNDECIDED',**GATES))
    for handle in handles.values():handle.close()
    summary=dict(status='COMPLETE_EXPANDED_API_INPUT_REVIEW',financial_delivery='PARTIAL_NO_NEW_API_INPUT_ACCEPTANCE',
        symbols=len(summaries),annual_tasks=task_count,old_alias_fields=len(set(MAPPING.values())),expanded_alias_fields=len(set(EXPANDED.values())),
        direct_required_fields_mapped=sorted(set(EXPANDED.values())&{f for family in FAMILIES for f,_ in required_keys(family)}),
        required_fields_without_direct_alias=sorted({f for family in FAMILIES for f,_ in required_keys(family)}-set(EXPANDED.values())),
        annual_raw_responses=sum(s.get('annual_raw_responses',0) for s in summaries),
        annual_candidate_cells=sum(s.get('annual_candidate_cells',0) for s in summaries),
        cells_without_provider_unit=sum(s.get('cells_without_provider_unit',0) for s in summaries),
        newly_mapped_field_cells=sum(s.get('new_field_cells',0) for s in summaries),
        conflicting_field_keys=sum(s['conflicting_field_keys'] for s in summaries),
        accounting_check_statuses=dict(check_statuses),
        conditional_z_arithmetic_rows=z_count,conditional_z_symbols=len(z_symbols),
        conditional_z_symbols_full10y=sum(s['conditional_z_full10y'] for s in summaries),
        known_f_signal_arithmetic=sum(s['known_f_signal_arithmetic'] for s in summaries),
        reviewed_reference_symbols=len({r['symbol'] for r in reviewed if r['value'] is not None}),reviewed_reference_value_rows=sum(r['value'] is not None for r in reviewed),
        new_accepted_metric_rows=0,verified_full10y_symbols=0,network_requests=0,pdf_downloads=0,ocr_pages=0,pdf_download_plan_created=False,
        conditional_arithmetic_is_not_a_metric_acceptance=True,**GATES)
    if task_count!=1522*13*6:raise ValueError('task grid differs')
    products={'summary.json':encoded(summary),'input-pins.json':encoded(pins),'symbol-manifests.json':encoded(symbol_manifests),
        'symbols-readiness.csv':csv_bytes(summaries),'input-blockers.csv':csv_bytes(blockers),
        'template-label-catalogue.csv':csv_bytes(list(label_catalogue.values())),
        'mapping-catalogue.json':(job/'mapping-catalogue.json').read_bytes()}
    manifest={name:digest(body) for name,body in products.items()}
    for name in columns:
        with (spool/name).open('rb') as f:manifest[name]=hashlib.file_digest(f,'sha256').hexdigest()
    result=job/'results'/digest(encoded(manifest))[:20]
    for name,body in products.items():put(result/name,body)
    for name in columns:
        target=result/name
        if target.exists():
            with target.open('rb') as f:
                if hashlib.file_digest(f,'sha256').hexdigest()!=manifest[name]:raise ValueError('sealed CSV differs')
        else:
            with (spool/name).open('rb') as src, target.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
    put(result/'manifest.json',manifest)
    report=inside(root,c['report_root']);import os
    relative=os.path.relpath(result,report).replace('\\','/')
    text=f'''# Mở rộng mapping và kiểm tra input API 1.522 mã

## Kết quả và giới hạn

Đã đọc lại **{summary['annual_raw_responses']:,} raw responses annual**, **{summary['annual_candidate_cells']:,} cells** trong 2012–2025; đánh giá **118.716 tasks annual 2013–2025 × 6 family**. Mapping tăng từ **{summary['old_alias_fields']} lên {summary['expanded_alias_fields']} fields**, thêm **{summary['newly_mapped_field_cells']:,} cells thuộc các field mới**. Annual-only là phạm vi xử lý mới; không tính quarterly/TTM hoặc coverage quarterly là đã hoàn tất.

**Chưa có input API mới nào được chấp nhận thành reference đã kiểm chứng.** Vẫn có {summary['reviewed_reference_symbols']} mã / {summary['reviewed_reference_value_rows']} dòng reference đã review từ stage trước; không chạy lại để cộng thành mã mới. **0 mã đủ bộ 6 chỉ số cho toàn bộ 2016–2025.** Delivery **PARTIAL**; khối lượng mapping/diagnostic hoàn tất không phải hoàn thành goal.

Đã tính **{z_count:,} dòng số học EM Z″ có điều kiện cho {summary['conditional_z_symbols']} mã**, trong đó {summary['conditional_z_symbols_full10y']} mã có arithmetic ở cả 10 năm. Đây **KHÔNG phải số mã Z đã kiểm chứng**: chỉ tính giả thuyết đồng nhất unit/scope/vintage và EBIT=PBT+pure interest còn chờ review. Không gọi candidate EBIT là document-reconciled EBIT. Có {summary['known_f_signal_arithmetic']:,} phép tính signal F thành phần; không cộng thành F-score hoặc điền hai signal thiếu.

## Quá trình thực hiện

1. Pin QA manifest, source receipts/raw hashes và stage33 reference manifest; không sửa nguồn/raw/canonical/registry hoặc bằng chứng cũ.
2. Mở rộng exact statement/group/code/normalized-label aliases. Không map finance income thành provider code21; không dùng aggregate D&A thành owned-PPE period depreciation, accumulated depreciation thành depreciation flow, paid-in capital thành shares, cash group issuance thành parent issuance, hoặc noncurrent loans thành debt including current portion.
3. Replay raw annual qua frozen parser, giữ source/template/period occurrence/cell ordinal. Ambiguous code/label, invalid/missing numeric và provider value conflict không chọn một giá trị để tính. Tách provider_type; không merge HK/K/H hoặc lấy latest thay vintage.
4. Chạy {len(FORMULAS)} accounting checks. Z conditional đòi các core checks đủ và equality, không có check difference, không có suspect displacement hoặc QA finding trong annual partition. F comparators có anomaly được giữ lại. Không coi equality là bằng chứng unit/scope/vintage; không thay annual bằng Q4.
5. Xuất matrix từng mã/năm/family, field observations và blockers. Phân biệt direct alias không có với alias không thấy/ambiguous trong các trang annual đã thu; không kết luận không công bố hoặc buộc tải PDF.
6. Checkpoint có manifest/code/config/source hashes; resume chỉ reuse khi tất cả hash khớp. Job có 4 worker đọc file local, không request mạng; source boundary và acquisition counters không bị reset.

## Những vướng mắc đã xác định

- {summary['cells_without_provider_unit']:,}/{summary['annual_candidate_cells']:,} annual cells không có provider unit. Không nhân hệ số theo độ lớn giá trị hoặc coi tỷ lệ cân bằng là evidence đơn vị.
- {summary['conflicting_field_keys']} field keys có nhiều giá trị trong cùng provider partition, giữ conflict thay vì average hoặc chọn mới nhất.
- Các input chưa có direct alias hợp lệ: **{', '.join(summary['required_fields_without_direct_alias'])}**. Một số là input phải reconcile/derive có evidence, không phải dòng trực tiếp của API; thiếu alias không chứng minh raw/PDF thiếu thông tin.
- EPS: vendor EPS chỉ được inventory, chưa thay recomputed EPS; thiếu numerator đúng note và weighted shares không suy bằng net profit/vendor EPS.
- F: thiếu current portion/parent issuance proof không điền0; M: aggregate depreciation/amortization không thay pure owned PPE depreciation. Z: giữ candidate PBT+interest riêng tới khi EBIT bridge được kiểm chứng.
- P/E/P/B: cần dated raw price, share history/events, exact earnings/book basis. Các dữ liệu đó không được tự lấy current shares hoặc adjusted price để điền.
- Scope, framework, report vintage, publication và historical security identity vẫn là evidence gates. Bank/Securities/UNKNOWN không áp regular-company score model.

## Bàn giao và bước tiếp theo

- [Summary]({relative}/summary.json), [từng mã]({relative}/symbols-readiness.csv).
- [Matrix từng mã/năm/chỉ số]({relative}/metric-tasks.csv), [blockers theo mã/family]({relative}/input-blockers.csv).
- [Số học API có điều kiện và signal diagnostics]({relative}/api-arithmetic-diagnostics.csv): **không dùng cho production/backtest hoặc cộng vào verified metrics**.
- [Accounting checks]({relative}/accounting-checks.csv), [label catalogue]({relative}/template-label-catalogue.csv), [mapping đã áp dụng]({relative}/mapping-catalogue.json).
- [Manifest của checkpoint từng mã]({relative}/symbol-manifests.json); cùng thư mục checkpoint có field-inputs.csv/JSON và source hashes để review từng giá trị.

Ưu tiên review mapping còn chưa khớp và evidence đã cache, sau đó tách rõ field có thể bổ sung bằng API/market/cache với field cần thuyết minh. **Không tải PDF/OCR mới, chưa lập PDF download plan**. Chỉ lên kế hoạch bổ sung sau khi báo owner phạm vi cụ thể. Không mở financial feature/PIT/M3 gate hoặc thay công thức.
'''
    put(report/'report.md',text.encode('utf-8'));put(report/'result-ref.json',dict(path=result.relative_to(root).as_posix(),manifest_sha256=digest((result/'manifest.json').read_bytes())))
    state_file(inside(root,c['output_root'])/'pipeline-status.json',summary['status'],completed=len(summaries),total=len(summaries),
        output=result.relative_to(root).as_posix(),report=(report/'report.md').relative_to(root).as_posix(),financial_delivery=summary['financial_delivery'])
    return dict(summary,output=result.relative_to(root).as_posix())
