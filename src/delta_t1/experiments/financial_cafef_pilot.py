"""Bounded five-issuer annual reference workflow, with durable acquisition replay.

Reviewed inputs are immutable evidence packages. Structured candidates remain
separate; calculators come from the existing feature registries.
"""
import csv
import io
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

from ..ingestion.cafef_financial import digest, encoded, immutable_write, now
from ..ingestion.cafef_financial_deep import parse_report, report_url
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import CompactTrialTransport, read_compact
from ..features.financial_reference import calculate
from ..features.financial_vas_reference import (calculate_disclosed_basic_eps,
    calculate_vas_f_score, calculate_vas_m_score, calculate_reported_valuation, M_FIELDS)
from .financial_user_workflow import exclusive as run_lock

VERSION = 'financial-cafef-pilot5-execution-v1'
SYMBOLS = ['BRC', 'FPT', 'MWG', 'GMD', 'VNM']
FAMILIES = ['EPS', 'PE', 'PB', 'F_SCORE', 'M_SCORE', 'Z_SCORE']
CLOSED = dict(financial_features_allowed=False, financial_cluster_allowed=False,
              research_ready=False, full_universe_allowed=False, next_100_allowed=False)
LIVING_SOURCES={'configs/data/financial_active_integration_v1.json','docs/crawl/sources/CAFEF.md'}
IMPLEMENTATION=['src/delta_t1/experiments/financial_cafef_pilot.py',
    'src/delta_t1/ingestion/cafef_financial_deep.py','src/delta_t1/features/financial_reference.py',
    'src/delta_t1/features/financial_vas_reference.py','src/delta_t1/ingestion/financial_compact_trial.py',
    'src/delta_t1/features/registry.py','src/delta_t1/ingestion/financial_pilot_readiness.py',
    'src/delta_t1/ingestion/financial_trial_transport.py','scripts/financial_cafef_pilot.py',
    'scripts/financial_cafef_pilot.ps1']


def read(path):
    return json.loads(Path(path).read_bytes())


def projection(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_bytes(encoded(value))
    os.replace(temp, path)


def csv_data(rows, fields=None):
    fields = fields or list(rows[0]) if rows else fields or ['status']
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (list, dict)) else v
                         for k, v in row.items()})
    return output.getvalue().encode('utf-8-sig')


def pins(root, values, snapshot_root=None):
    for relative, expected in values.items():
        if digest(inside(root, relative).read_bytes()) != expected:
            if snapshot_root and relative in LIVING_SOURCES:
                snapshot=Path(snapshot_root)/(expected+'.bin')
                if snapshot.exists() and digest(snapshot.read_bytes())==expected:
                    continue  # Exact frozen version, never waive a cache/file hash.
            raise ValueError('evidence hash mismatch: ' + relative)


def validate(root, config):
    if (config.get('version') != VERSION or config.get('executable') is not True or
            config.get('symbols') != SYMBOLS or config.get('families') != FAMILIES or
            any(config.get(k) is not False for k in CLOSED)):
        raise ValueError('exact executable pilot5 contract and closed gates required')
    caps = {'max_logical_requests': 250, 'max_transport_attempts': 350,
            'max_pdf_download_attempts': 16, 'max_response_bytes': 3_000_000,
            'max_total_downloaded_bytes': 500_000_000, 'max_wall_seconds': 21600,
            'max_attempts_per_request': 2, 'timeout_seconds': 25}
    for key, cap in caps.items():
        if type(config['budgets'].get(key)) not in [int, float] or not 0 < config['budgets'][key] <= cap:
            raise ValueError('invalid pilot budget: ' + key)
    if config['budgets']['min_seconds_between_transport_attempts'] < 2:
        raise ValueError('spacing below frozen minimum')
    if config['approved_hosts'] != ['apiweb.cafef.vn']:
        raise ValueError('only already-observed dedicated API host enabled; legacy EPS remains blocked')
    pins(root, config['source_pins'], inside(root,config['output_root'],'data')/'source-snapshots')
    return config


class PilotTransport(CompactTrialTransport):
    """Continue the same compact journal without resetting counters or deadline."""
    def __init__(self, root, output, config, **kwargs):
        self.resume_ledger = read_compact(output) if (output / 'transport.jsonl').exists() else None
        if self.resume_ledger and self.resume_ledger['torn_tail_bytes']:
            raise ValueError('torn journal retained: explicit recovery review required')
        super().__init__(root, output, config,
                         resume_state=self.resume_ledger['state'] if self.resume_ledger else None, **kwargs)

    def event(self, action, **detail):
        if action == 'START_OR_RESUME' and self.resume_ledger:
            self.index = self.resume_ledger['events']
            self.previous = self.resume_ledger['last_sha256']
        return super().event(action, **detail)


def tasks():
    return [dict(id=s+'-'+statement, symbol=s, statement=statement, mode='NAM',
                 url=report_url(s, statement)) for s in SYMBOLS for statement in ['CDKT','KQKD','LCTT']]


def added_tasks(run):
    from urllib.parse import urlsplit, parse_qs
    result=[]
    for path in sorted((run/'request-additions').glob('*.json')):
        for task in read(path)['requests']:
            query=parse_qs(urlsplit(task['url']).query)
            if task['statement']=='ISSUER_PDF':
                proof=read(inside(run.parents[2],task['observed_link_path']))
                if task['symbol']!='VNM' or task['url'] not in [x['href'] for x in proof['links']]:
                    raise ValueError('issuer supplement lacks observed link')
                result.append(task)
                continue
            if task['statement']=='PRICE':
                uri=urlsplit(task['url'])
                if (uri.scheme!='https' or uri.netloc!='cafef.vn' or
                    uri.path!='/du-lieu/Ajax/PageNew/TradeHistoryNew.ashx' or
                    query.get('Symbol')!=[task['symbol']] or task['symbol'] not in SYMBOLS or
                    query.get('PageSize')!=['30'] or not 1<=int(query.get('PageIndex',['0'])[0])<=10):
                    raise ValueError('price request outside small pilot observation')
                result.append(task)
                continue
            if task['statement']=='PDF':
                uri=urlsplit(task['url'])
                root=run.parents[2]
                disclosure=read(inside(root,task['disclosure_path']))['Data']['BctcList']
                matching=[r for r in disclosure if r['Id']==task['provider_id'] and
                          r['Symbol']==task['symbol'] and urlsplit(r['LinkFile']).path==uri.path]
                if uri.netloc=='cafef1.mediacdn.vn':
                    proof=read(inside(root,task['observed_alias_path']))
                    if proof['observed_viewer_url']!=task['url']:
                        raise ValueError('no exact observed viewer URL')
                if (uri.scheme!='https' or uri.netloc not in ['cafefnew.mediacdn.vn','cafef1.mediacdn.vn'] or
                    not uri.path.startswith('/Images/Uploaded/DuLieuDownload/BCTC/') or
                    task['symbol'] not in SYMBOLS or not matching):
                    raise ValueError('invalid linked public document')
                result.append(task)
                continue
            if task['statement']=='DISCLOSURE':
                uri=urlsplit(task['url'])
                if (uri.scheme!='https' or uri.netloc!='cafef.vn' or
                    uri.path!='/du-lieu/ajax/ajaxcongbothongtin.ashx' or
                    query.get('symbol')!=[task['symbol']] or task['symbol'] not in SYMBOLS or
                    query.get('pagesize')!=['20'] or query.get('pageindex')!=['1']):
                    raise ValueError('invalid narrowly scoped disclosure request')
                result.append(task)
                continue
            if (task['symbol'] not in SYMBOLS or task['statement'] not in ['CDKT','KQKD','LCTT'] or
                    task['mode']!='NAM' or query.get('TypeTime')!=['NAM'] or
                    task['url'] != report_url(task['symbol'],task['statement'],group=task['group'])):
                raise ValueError('supplemental task outside dedicated annual scope')
            result.append(task)
    return result


def prepare(root, config, run):
    run.mkdir(parents=True, exist_ok=True)
    contract = run / 'execution-contract.json'
    if contract.exists():
        if read(contract) != config:
            raise ValueError('frozen executable contract changed')
    else:
        immutable_write(contract, encoded(config))
    graph = encoded(dict(
        requests=tasks(), metrics=[dict(symbol=s, family=f) for s in SYMBOLS for f in FAMILIES],
        target_year=2025, supporting_years=[2024, 2023], baseline_old_cohort='32/300'))
    if (run/'task-graph.json').exists():
        if (run/'task-graph.json').read_bytes() != graph:
            raise ValueError('task graph changed')
    else:
        immutable_write(run/'task-graph.json',graph)
    (run / 'network').mkdir(exist_ok=True)
    (run / 'reviews').mkdir(exist_ok=True)
    snapshot=run/'source-snapshots'
    snapshot.mkdir(exist_ok=True)
    for relative,sha in config['source_pins'].items():
        if relative not in LIVING_SOURCES:continue
        path=snapshot/(sha+'.bin')
        if path.exists():
            if digest(path.read_bytes())!=sha:raise ValueError('frozen source snapshot tampered')
        else:
            body=inside(root,relative).read_bytes()
            if digest(body)!=sha:raise ValueError('cannot snapshot already changed source')
            immutable_write(path,body)
    if not (run / 'network/transport.jsonl').exists():
        PilotTransport(root, run / 'network', config)
    if not (run/'execution-state.json').exists():
        projection(run/'execution-state.json',dict(stage='P0_FROZEN',status='IN_PROGRESS',
            counters=read_compact(run/'network')['state'],required_family_cells=30,**CLOSED))


def acquire(root, config, run):
    effective=dict(config,approved_hosts=['apiweb.cafef.vn','cafef.vn','cafefnew.mediacdn.vn',
                                         'cafef1.mediacdn.vn','d8um25gjecm9v.cloudfront.net'])
    transport = PilotTransport(root, run / 'network', effective)
    for task in tasks()+added_tasks(run):
        key = digest(task['url'].encode())
        receipt = run / 'network' / (key + '.receipt.json')
        if receipt.exists():
            old = read(receipt)
            if old['status'] == 'FRESH_ACQUIRED':
                pins(root, {old['path']: old['sha256']})
            continue
        is_pdf=task['statement'] in ['PDF','ISSUER_PDF']
        transport.context = dict(kind='pdf' if is_pdf else 'listing',
                                 symbol=task['symbol'], report=task['statement'])
        transport.b=dict(config['budgets'],max_response_bytes=25_000_000 if is_pdf else 3_000_000)
        try:
            # Any prior attempt without a receipt is kept as an interrupted task.
            # Never silently retry a successful response lost before cache commit.
            previous = [r for r in transport.state['requests'].values() if r['url'] == task['url']]
            if previous:
                raise ValueError('INTERRUPTED_REQUEST_REQUIRES_REVIEW')
            body, status = transport.get(task['url'])
            raw = run / 'network' / (key + ('.pdf' if is_pdf else '.json'))
            immutable_write(raw, body)
            result = dict(task, status='FRESH_ACQUIRED', http_status=status,
                          path=raw.relative_to(root).as_posix(), sha256=digest(body), bytes=len(body))
            transport.commit_cache(task['url'], result)
        except Exception as error:
            result = dict(task, status='ACCESS_BLOCKED' if transport.state['boundary'] else
                          'BUDGET_DEFERRED' if transport.state['budget_stop'] else 'ACQUISITION_FAILED',
                          error=str(error))
        immutable_write(receipt, encoded(result))
        if transport.state['boundary'] or transport.state['budget_stop']:
            break
    return read_compact(run / 'network')['state']


def reviewed(root, run):
    packages = sorted((run / 'reviews').glob('*.json'))
    if not packages:
        return [], [], {}, []
    package = read(packages[-1])
    if package.get('version') != 'pilot5-reviewed-inputs-v1':
        raise ValueError('reviewed input schema required')
    pins(root, package['source_pins'])
    facts = package['facts']
    seen = set()
    for f in facts:
        key = (f['symbol'], f['field'], f['year'])
        if key in seen or f['symbol'] not in SYMBOLS or f['year'] not in [2023,2024,2025]:
            raise ValueError('duplicate/out-of-scope reviewed fact')
        seen.add(key)
        if f['review_status'] != 'REVIEWED_REFERENCE_ONLY' or not f.get('provenance'):
            raise ValueError('unreviewed fact')
        if f.get('framework')!='VAS' or f.get('scope') not in ['CONSOLIDATED','ISSUER_NO_SUBSIDIARIES']:
            raise ValueError('reviewed scope/framework incompatible')
        expected='SHARES' if f['field'] in ['weighted_average_basic_shares','weighted_average_diluted_shares','common_shares'] else (
            'INDICATOR' if f['field']=='parent_common_equity_issuance_verified' else
            None if f['field']=='vendor_basic_eps' else 'VND')
        if expected and f['unit']!=expected:raise ValueError('reviewed field unit incompatible')
        if not Decimal(f['value']).is_finite():
            raise ValueError('nonfinite reviewed fact')
    return facts, package.get('qa', []), package.get('valuation', {}), [dict(
        path=packages[-1].relative_to(root).as_posix(), sha256=digest(packages[-1].read_bytes()))]


def compute(facts, valuation, variants):
    rows, details, dependencies = [], [], []
    for symbol in SYMBOLS:
        fs = [f for f in facts if f['symbol'] == symbol]
        values = {(f['field'], f['year']-2025):f['value'] for f in fs}
        current = {k:v for (k,o),v in values.items() if o == 0}
        eps = calculate_disclosed_basic_eps(current.get('eps_adjusted_earnings_numerator'),
                                            current.get('weighted_average_basic_shares'), 12)
        fscore = calculate_vas_f_score(values)
        if fscore['value'] is None:
            known=[r['value'] for r in fscore['signals'].values() if r['value'] is not None]
            fscore=dict(fscore,interval=[sum(known),sum(known)+9-len(known)])
        mscore = calculate_vas_m_score(values, 'GROSS_SHORT_TERM_TRADE')
        zscore = calculate('Z_SCORE', current)
        val = valuation.get(symbol, {})
        pe_pb = dict(pe=None, pb=None, status='VALUATION_BASIS_UNRESOLVED')
        if val:
            if val['price_basis'] != 'RAW_UNADJUSTED_CLOSE' or val['price_date'] <= val['publication_date']:
                raise ValueError('adjusted/future-publication valuation rejected')
            pe_pb = calculate_reported_valuation(val['raw_price'], eps['value'],
                current.get('parent_common_equity'), current.get('common_shares'))
        calculations = dict(EPS=eps, PE=dict(pe_pb,value=pe_pb['pe']), PB=dict(pe_pb,value=pe_pb['pb']),
            F_SCORE=fscore, M_SCORE=mscore, Z_SCORE=dict(zscore, value=(
                zscore['value']['em_z_double_prime_reference'] if zscore['value'] else None)))
        for family, result in calculations.items():
            required = required_keys(family)
            ids = [f['id'] for f in fs if (f['field'], f['year']-2025) in required]
            if family in ['PE','PB'] and val:
                ids.append('PRICE:'+symbol+':'+val['price_date'])
            missing = [dict(field=f, year=2025+offset) for f,offset in sorted(required-values.keys())]
            if family in ['PE','PB'] and not val:
                missing.append(dict(field='dated_raw_price_and_basis', year=2025))
            status = 'RECOMPUTED_REFERENCE' if result['value'] is not None else 'PARTIAL'
            row = dict(symbol=symbol, family=family, year=2025, variant=variants[family],
                status=status, value=result['value'], unit='VND/share' if family=='EPS' else
                'points/9' if family=='F_SCORE' else 'ratio', dependency_ids=ids,
                formula_version='existing-feature-registry/1.0.0', input_period='2025-01-01/2025-12-31',
                price_date=val.get('price_date') if family in ['PE','PB'] else None,
                price_basis=val.get('price_basis') if family in ['PE','PB'] else None,
                raw_price=val.get('raw_price') if family in ['PE','PB'] else None,
                share_basis=val.get('share_basis') if family in ['PE','PB'] else None,
                balance_date='2025-12-31',
                temporal_status=val.get('temporal_status','NUMERICAL_REFERENCE_ONLY'),
                strict_pit_ready=False, production_ready=False)
            rows.append(row)
            details.append(dict(symbol=symbol,family=family,result=result,valuation=val if family in ['PE','PB'] else None))
            dependencies.append(dict(symbol=symbol,family=family,dependency_ids=ids,missing=missing,
                next_action='REVIEW_EXACT_NOTE_OR_DECLARED_VALUATION_BASIS' if missing else 'REPLAY_AND_QA'))
    return rows, details, dependencies


def required_keys(family):
    from ..ingestion.financial_pilot_readiness import SIGNALS
    if family == 'F_SCORE':
        return {('net_profit' if f=='income_before_extraordinary_items' else f,o)
                for req in SIGNALS.values() for f,o in req}
    if family == 'M_SCORE':
        return {(f,o) for f in M_FIELDS for o in [0,-1]} | {('net_profit',0),('operating_cash_flow',0)}
    fields = dict(EPS=['eps_adjusted_earnings_numerator','weighted_average_basic_shares'],
        PE=['eps_adjusted_earnings_numerator','weighted_average_basic_shares'],
        PB=['parent_common_equity','common_shares'],
        Z_SCORE=['current_assets','current_liabilities','total_assets','retained_earnings',
                 'document_reconciled_ebit','total_equity','total_liabilities'])
    return {(f,0) for f in fields[family]}


def export(root, config, run):
    facts, qa, valuation, review_pins = reviewed(root, run)
    rows, details, dependencies = compute(facts, valuation, config['primary_metric_variants'])
    candidates, audit = [], []
    for path in sorted((run/'network').glob('*.receipt.json')):
        r = read(path)
        audit.append({k:r.get(k) for k in ['id','symbol','statement','url','status','sha256','error']})
        if r['status'] == 'FRESH_ACQUIRED':
            pins(root, {r['path']: r['sha256']})
            if r['statement'] in ['DISCLOSURE','PDF','PRICE','ISSUER_PDF']:
                continue
            try:
                candidates += parse_report(inside(root,r['path']).read_bytes(),r['symbol'],r['statement'],r['mode'],r['id'])
            except (ValueError,KeyError,TypeError) as error:
                audit[-1]['error'] = 'PARSE_ERROR: '+str(error)
    ledger = read_compact(run/'network')
    counter = {k:ledger['state'][k] for k in ['logical_requests','transport_attempts','downloaded_bytes',
                    'reserved_bytes','pdf_download_attempts','created_at','boundary','budget_stop']}
    checked = {s:len({(r['field'],r['year']) for r in qa if r['symbol']==s and
                      r.get('status')=='MATCH' and r.get('independent') is True}) for s in SYMBOLS}
    computed = sum(r['value'] is not None for r in rows)
    # Live acquisition, QA and operational verification are separate completion gates.
    live = {r['symbol'] for r in audit if r['status']=='FRESH_ACQUIRED' and not r.get('error')
            and r['statement'] in ['CDKT','KQKD','LCTT']}
    summary = dict(status='PARTIAL_WITH_RESULTS', target=30, recomputed_cells=computed,
        qa_comparison_counts=checked, complete_symbols=[s for s in SYMBOLS if
            sum(r['symbol']==s and r['value'] is not None for r in rows)==6],
        fresh_structured_symbols=sorted(live), operating_acceptance='PENDING_VERIFY', **CLOSED)
    summary['metric_values_sha256']=digest(encoded(rows))
    summary['qa_checked_recomputed_cells']=sum(r['value'] is not None and checked[r['symbol']]>=20 for r in rows)
    implementation={p:digest(inside(root,p).read_bytes()) for p in IMPLEMENTATION}
    semantics = dict(rows=rows, details=details, facts=facts, qa=qa, candidates=candidates,
                     review_pins=review_pins, journal_sha256=ledger['prefix_sha256'],implementation_pins=implementation)
    key = digest(encoded(semantics))[:20]
    output = run/'results'/key
    if output.exists():
        verify_result(root, output)
    else:
        output.mkdir(parents=True)
        immutable_write(output/'metrics.csv',csv_data(rows))
        immutable_write(output/'metric-variants.csv',csv_data([dict(symbol=d['symbol'],family=d['family'],
            result=d['result']) for d in details]))
        immutable_write(output/'metric-dependencies.json',encoded(dependencies))
        price_inputs=[dict(id='PRICE:'+s+':'+v['price_date'],symbol=s,field='raw_close',
            value=v['raw_price'],unit='VND/share',price_date=v['price_date'],
            basis=v['price_basis'],provenance=dict(source=v['price_source'],row=v['price_source_row']))
            for s,v in valuation.items()]
        immutable_write(output/'metric-inputs.jsonl',b''.join(encoded(f).rstrip()+b'\n' for f in facts+price_inputs))
        immutable_write(output/'field-coverage.csv',csv_data([dict(symbol=s,field=f,year=2025+o,
            status='REVIEWED' if any(x['symbol']==s and x['field']==f and x['year']==2025+o for x in facts)
            else 'BASIS_UNRESOLVED') for s in SYMBOLS for f,o in sorted(set.union(*(required_keys(f) for f in FAMILIES)))]))
        immutable_write(output/'source-audit.csv',csv_data(audit))
        immutable_write(output/'structured-candidates.json',encoded(candidates))
        immutable_write(output/'qa.csv',csv_data(qa))
        immutable_write(output/'exceptions.csv',csv_data([dict(symbol=d['symbol'],family=d['family'],
            status='BASIS_UNRESOLVED',missing=d['missing']) for d in dependencies if d['missing']]))
        immutable_write(output/'quarantined-cells.json',encoded([q for q in qa if q['status']!='MATCH']))
        deviations=read(run/'policy-deviations.json') if (run/'policy-deviations.json').exists() else []
        immutable_write(output/'policy-deviations.csv',csv_data(deviations,['policy','status','reason','resolution']))
        package=read(inside(root,review_pins[0]['path'])) if review_pins else {'source_pins':{}}
        fresh_paths={r['path'] for r in [read(p) for p in (run/'network').glob('*.receipt.json')]
                     if r['status']=='FRESH_ACQUIRED'}
        docs=[dict(path=p,sha256=sha,acquisition='FRESH_ACQUIRED' if p in fresh_paths else 'REUSED_VERIFIED_CACHE') for p,sha in
              package['source_pins'].items() if p.lower().endswith('.pdf')]
        immutable_write(output/'document-index.json',encoded(docs))
        immutable_write(output/'ocr-manifest.json',encoded([dict(path=p,sha256=sha,acquisition='REUSED_VERIFIED_CACHE')
            for p,sha in package['source_pins'].items() if p.endswith(('.png','.ocr.json'))]))
        immutable_write(output/'cache-manifest.json',encoded(package['source_pins']))
        immutable_write(output/'raw-manifest.json',encoded([read(p) for p in sorted((run/'network').glob('*.receipt.json'))]))
        immutable_write(output/'costs.json',encoded(dict(scripted=counter,new_ocr_pages=0,
            ocr_note='No automatic OCR acceptance; existing reviewed images reused',
            browser_requests='NOT_INSTRUMENTED_NOT_INCLUDED',reviewed_fact_count=len(facts),
            reused_documents=len(docs),unique_field_comparisons=checked,
            manual_review_note='Previous visual reviews reused; per-fact provenance retained. New review timing not instrumented.')))
        immutable_write(output/'summary.json',encoded(summary))
        immutable_write(output/'calculation-details.json',encoded(details))
        immutable_write(output/'replay-semantics.json',encoded(semantics))
        immutable_write(output/'report.md',report_text(summary,rows,dependencies).encode())
        immutable_write(output/'manifest.json',encoded(dict(files={p.name:digest(p.read_bytes())
            for p in output.iterdir() if p.is_file()}, review_pins=review_pins,
            source_pins=config['source_pins'],implementation_pins=implementation)))
    projection(run/'execution-state.json',dict(stage='P3_P4',latest_result=output.relative_to(root).as_posix(),
        **summary,counters=counter,pending_dependencies=[d for d in dependencies if d['missing']]))
    return dict(summary,output=output.relative_to(root).as_posix())


def report_text(summary, rows, dependencies):
    lines=['# Pilot CafeF 5 mã — FY2025','', '**'+summary['status']+'**. '
           +str(summary['recomputed_cells'])+'/30 family cells đã tính lại; QA và operational acceptance được ghi riêng.','',
           '| Mã | EPS | PE | PB | F | M | Z |','|---|---:|---:|---:|---:|---:|---:|']
    for s in SYMBOLS:
        vals=[next(r['value'] for r in rows if r['symbol']==s and r['family']==f) for f in FAMILIES]
        lines.append('|'+s+'|'+'|'.join('—' if v is None else format(Decimal(str(v)),'.6f') for v in vals)+'|')
    lines += ['', 'Các phép tính dùng practical variants đã khai báo; financial/research/cluster gates giữ false.',
        'PE annual và PB book snapshot có ngày giá và basis riêng; không gọi là current TTM hoặc historical production-ready.',
        '', 'Dependencies chưa đóng:']
    lines += ['- '+d['symbol']+' '+d['family']+': '+json.dumps(d['missing'],ensure_ascii=False)
              for d in dependencies if d['missing']]
    return '\n'.join(lines)+'\n'


def verify_result(root, output):
    manifest = read(output/'manifest.json')
    for name, expected in manifest['files'].items():
        if digest((output/name).read_bytes()) != expected:
            raise ValueError('result tamper: '+name)
    pins(root,manifest['source_pins'],output.parents[1]/'source-snapshots')
    pins(root,manifest.get('implementation_pins',{}))
    for r in manifest['review_pins']:
        pins(root,{r['path']:r['sha256']})
        pins(root,read(inside(root,r['path']))['source_pins'])
    semantics = read(output/'replay-semantics.json')
    ledger=read_compact(output.parents[1]/'network')
    if ledger['prefix_sha256']!=semantics['journal_sha256']:
        raise ValueError('current journal differs from selected result; regenerate offline report')
    for r in read(output/'raw-manifest.json') if (output/'raw-manifest.json').exists() else []:
        if r['status']=='FRESH_ACQUIRED':pins(root,{r['path']:r['sha256']})
    if semantics['review_pins']:
        package=read(inside(root,semantics['review_pins'][0]['path']))
        if package['facts']!=semantics['facts'] or package['qa']!=semantics['qa']:
            raise ValueError('review package/result mismatch')
    rows,details,_ = compute(semantics['facts'],{
        d['symbol']:d['valuation'] for d in semantics['details'] if d.get('valuation')},
        {r['family']:r['variant'] for r in semantics['rows']})
    if rows != semantics['rows'] or details != semantics['details']:
        raise ValueError('offline calculator replay mismatch')
    return dict(status='VERIFIED',recomputed_cells=sum(r['value'] is not None for r in rows),
                metric_values_sha256=digest(encoded(rows)),new_network=0,new_ocr=0)


def main(root, config_path, action, network=False):
    root=Path(root).resolve()
    config=validate(root,read(inside(root,config_path,'configs')))
    run=inside(root,config['output_root'],'data')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()
    if action=='doctor':
        checks=dict(expected_branch=branch==config['expected_branch'],renderer=bool(shutil.which('pdftoppm')),
            ocr_script=(root/'scripts/ocr_financial_pages.ps1').exists(),
            reviewed_cache=bool(list((run/'reviews').glob('*.json'))),source_pins=True)
        if checks['reviewed_cache']:reviewed(root,run)
        return dict(status='PASS' if all(checks.values()) else 'PARTIAL_DOCTOR',checks=checks,
            branch=branch,python=sys.executable,pdftoppm=shutil.which('pdftoppm'),
            ocr_script=(root/'scripts/ocr_financial_pages.ps1').exists(),
            reviewed_cache_packages=len(list((run/'reviews').glob('*.json'))),
            network_default=False,legacy_eps_access='BLOCKED_INHERITED_LATCH',**CLOSED)
    if branch!=config['expected_branch']:
        raise ValueError('unexpected branch; preserve local changes')
    if action=='plan':
        requests=tasks()+added_tasks(run)
        state=read_compact(run/'network')['state'] if (run/'network/transport.jsonl').exists() else None
        return dict(status='PLANNED',requests=requests,caps=config['budgets'],counters=state,
            metric_dependencies=read(run/'execution-state.json').get('pending_dependencies',[]) if (run/'execution-state.json').exists() else [],
            required_family_cells=30,network_opt_in_required=True)
    run.mkdir(parents=True,exist_ok=True)
    with run_lock(run):
        prepare(root,config,run)
        if action=='verify':
            state=read(run/'execution-state.json')
            result=verify_result(root,inside(root,state['latest_result'],'data'))
            state.update(stage='P5_PARTIAL',operating_acceptance='OFFLINE_REPLAY_VERIFIED')
            if (result['recomputed_cells']==30 and all(n>=20 for n in state['qa_comparison_counts'].values())
                    and set(state['fresh_structured_symbols'])==set(SYMBOLS)):
                state.update(status='GOAL_ACHIEVED',stage='P5_GOAL_ACHIEVED')
            projection(run/'execution-state.json',state)
            return result
        if action in ['run','resume'] and network:
            acquire(root,config,run)
        return export(root,config,run)
