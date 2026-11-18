"""Pilot source validation against pinned, previously reviewed PDF references.

Provider values never repair themselves by row offset or inferred unit multiplier.
This reference QA stage does not promote financial/research eligibility.
"""
import csv
import io
import json
import importlib.metadata
import zipfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode

from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside
from ..ingestion.financial_compact_trial import read_compact
from .financial_cafef_pilot import (SYMBOLS, CLOSED, PilotTransport, compute, csv_data,
                                    read, reviewed, verify_result)
from .financial_user_workflow import exclusive

VERSION = 'financial-provider-validation-v1'
SOURCE = 'https://raw.githubusercontent.com/vietfin/vietfin/main/src/vietfin/providers/tcbs/utils/equity_fundamental_income.py'
REPORTS = {'balance': 'balancesheet', 'income': 'incomestatement', 'cash': 'cashflow'}


def finite(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def validate_config(config):
    if config.get('version') != VERSION or config.get('symbols') != SYMBOLS:
        raise ValueError('fixed pilot5 config required')
    if any(config.get(key) is not False for key in CLOSED):
        raise ValueError('closed gates required')
    if config.get('providers') != ['TCBS', 'SSI'] or config.get('years') != [2023, 2024, 2025]:
        raise ValueError('frozen provider/year scope required')
    if config.get('approved_hosts') != ['apipubaws.tcbs.com.vn']:
        raise ValueError('only source-observed TCBS host enabled')
    caps = {'max_logical_requests': 15, 'max_transport_attempts': 15,
            'max_response_bytes': 2_000_000, 'max_total_downloaded_bytes': 32_000_000,
            'max_wall_seconds': 1800, 'max_attempts_per_request': 1,
            'max_pdf_download_attempts': 1, 'timeout_seconds': 20}
    for key, cap in caps.items():
        value = config.get('budgets', {}).get(key)
        if type(value) is not int or not 0 < value <= cap:
            raise ValueError('invalid finite cap: ' + key)
    if config['budgets'].get('min_seconds_between_transport_attempts', 0) < 2:
        raise ValueError('request spacing required')


def jobs():
    output = []
    for provider in ['TCBS', 'SSI']:
        for symbol in SYMBOLS:
            for report, endpoint in REPORTS.items():
                output.append(dict(id=f'{provider}:{symbol}:{report}', provider=provider,
                    symbol=symbol, report=report, period='annual', target_years=[2023, 2024, 2025],
                    url=('https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/' + symbol + '/' + endpoint
                         + '?' + urlencode({'yearly': 1, 'isAll': 'True'})) if provider == 'TCBS' else None,
                    status='ROUTE_OBSERVED_UNIT_SCOPE_REVIEW_REQUIRED' if provider == 'TCBS'
                           else 'WHEEL_ROUTE_OBSERVED_REQUIRES_CATALOG_ACCESS_AND_ORGAN_CODE',
                    route_reference=SOURCE if provider == 'TCBS' else
                        'https://vietfin.readthedocs.io/en/latest/reference/equity/fundamental/balance.html',
                    implementation='DIRECT_SOURCE_ROUTE_OBSERVED_IN_VIETFIN_NOT_SDK_EXECUTION'))
    return output


def tcbs_candidates(body, job):
    """Retain raw semantic keys; never infer monetary scale or consolidation."""
    data = json.loads(body, parse_float=str, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    if not isinstance(data, list):
        raise ValueError('TCBS report list required')
    output = []
    seen = set()
    for record in data:
        if (not isinstance(record, dict) or not isinstance(record.get('ticker'), str)
                or record['ticker'].upper() != job['symbol']):
            raise ValueError('provider identity missing/mismatch')
        if type(record.get('year')) is not int:
            raise ValueError('provider year missing')
        if record['year'] not in job['target_years']:
            continue
        for code, value in record.items():
            if code in {'ticker', 'year', 'quarter', 'period'}:
                continue
            key = (record['year'], code)
            if key in seen:
                raise ValueError('ambiguous duplicate provider field/year')
            seen.add(key)
            output.append(dict(provider='TCBS', symbol=job['symbol'], report=job['report'],
                year=record['year'], provider_quarter=record.get('quarter'), raw_code=code,
                raw_value=value, numeric_value=str(finite(value)) if finite(value) is not None else None,
                unit_status='UNVERIFIED_NO_MULTIPLIER_INFERRED', scope_status='UNVERIFIED',
                mapping_status='UNREVIEWED_PROVIDER_SEMANTIC_KEY', canonical_accepted=False))
    return output


def reference_decisions(facts, comparisons):
    refs = {fact['id']: fact for fact in facts}
    if len(refs) != len(facts):
        raise ValueError('duplicate reference IDs')
    grouped = {}
    comparison_decisions = []
    for row in comparisons:
        fact = refs.get(row['reference_id'])
        if fact is None or (row['symbol'], row['field'], int(row['year'])) != (
                fact['symbol'], fact['field'], fact['year']):
            raise ValueError('QA reference identity mismatch')
        if finite(row['expected']) is None or finite(row['expected']) != finite(fact['value']):
            raise ValueError('QA expected value no longer matches PDF reference')
        equal = finite(row['observed']) is not None and finite(row['observed']) == finite(fact['value'])
        if (row['status'] == 'MATCH') != equal:
            raise ValueError('QA status/value inconsistency')
        grouped.setdefault(fact['id'], []).append(row)
        comparison_decisions.append(dict(row, selected_value=fact['value'],
            selected_source='PINNED_REVIEWED_PDF_REFERENCE',
            decision='PDF_CORROBORATED_BY_API' if equal else 'QUARANTINE_API_USE_REVIEWED_PDF',
            pdf_provenance=fact['provenance'], raw_api_preserved=True,
            canonical_accepted=False, strict_pit_ready=False))
    selections = []
    for fact in facts:
        if (fact.get('review_status') != 'REVIEWED_REFERENCE_ONLY' or not fact.get('provenance')
                or finite(fact['value']) is None or fact.get('framework') != 'VAS'
                or fact.get('scope') not in {'CONSOLIDATED', 'ISSUER_NO_SUBSIDIARIES'}):
            raise ValueError('reviewed PDF reference required; a PDF file alone is insufficient')
        candidates = grouped.get(fact['id'], [])
        conflict = any(row['status'] != 'MATCH' for row in candidates)
        selections.append(dict(id=fact['id'], symbol=fact['symbol'], field=fact['field'],
            year=fact['year'], value=fact['value'], unit=fact['unit'], framework=fact['framework'],
            scope=fact['scope'], selected_source='PINNED_REVIEWED_PDF_REFERENCE',
            selection_reason='API_CONFLICT' if conflict else 'API_CORROBORATED' if candidates else 'PDF_NOTE_OR_DERIVED_REFERENCE',
            api_comparisons=len(candidates), provenance=fact['provenance'],
            canonical_accepted=False, strict_pit_ready=False))
    return selections, comparison_decisions


def plan(root, config):
    validate_config(config)
    baseline = verify_result(root, inside(root, config['baseline_result']))
    try:
        installed = importlib.metadata.version('vietfin')
    except importlib.metadata.PackageNotFoundError:
        installed = None
    return dict(status='PLANNED_PROVIDER_COMPARISON_NOT_EXECUTED', jobs=jobs(),
        baseline=baseline, policy='Use already reviewed, pinned PDF facts for reference arithmetic; quarantine conflicting APIs',
        budgets=config['budgets'], target_sdk_version='0.2.0', installed_sdk_version=installed,
        sdk_note='Routes inspected from published wheel; direct public route probes are separate from SDK execution',
        source_observations=source_observations(root,config)[0],
        **CLOSED)


def acquire(root, config, *, transport_class=PilotTransport):
    """New TCBS-only campaign; never resets or reuses CafeF acquisition counters."""
    validate_config(config)
    run = inside(root, config['output_root'])
    run.mkdir(parents=True, exist_ok=True)
    with exclusive(run):
        contract = run / 'acquisition-contract.json'
        if contract.exists() and contract.read_bytes() != encoded(config):
            raise ValueError('frozen acquisition config changed')
        if not contract.exists():
            immutable_write(contract, encoded(config))
        network = run / 'network'
        network.mkdir(exist_ok=True)
        receipts = run / 'receipts'
        receipts.mkdir(exist_ok=True)
        if (network/'transport.jsonl').exists():
            saved=read_compact(network)
            if saved['torn_tail_bytes']: raise ValueError('torn journal requires review')
            if saved['state']['boundary'] or saved['state']['budget_stop'] or len(list(receipts.glob('*.json')))==15:
                return dict(status='TERMINAL_OR_COMPLETE_CACHE_NO_NETWORK',
                    receipts=len(list(receipts.glob('*.json'))),counters=saved['state'],new_network=0)
        transport = transport_class(root, network, config)
        for job in jobs():
            if job['provider'] != 'TCBS':
                continue
            path = receipts / (job['id'].replace(':', '-') + '.json')
            if path.exists():
                continue
            # Same-URL interruptions and terminal failures are not retried.
            if any(row['url'] == job['url'] for row in transport.state['requests'].values()):
                raise ValueError('interrupted request requires review; no duplicate attempt')
            receipt = dict(job)
            try:
                body, status = transport.get(job['url'])
                relative = config['output_root'] + '/raw/' + digest(body) + '.json'
                raw = inside(root, relative)
                if not raw.exists():
                    immutable_write(raw, body)
                receipt.update(raw_path=relative, raw_sha256=digest(body), http_status=status)
                parsed = tcbs_candidates(body, job)
                receipt.update(status='RAW_ACQUIRED_UNIT_SCOPE_MAPPING_UNVERIFIED', raw_path=relative,
                               raw_sha256=digest(body), http_status=status, candidates=parsed)
            except Exception as error:
                receipt.update(status='ACCESS_STOP' if transport.state['boundary'] else
                    'BUDGET_STOP' if transport.state['budget_stop'] else 'REQUEST_OR_PARSE_ERROR', error=str(error))
            immutable_write(path, encoded(receipt))
            if transport.state['boundary'] or transport.state['budget_stop']:
                break
        return dict(status='PARTIAL_PROVIDER_CANDIDATES_ONLY', receipts=len(list(receipts.glob('*.json'))),
                    counters=read_compact(run/'network')['state'], new_pdf=0, new_ocr=0)


def probe_ssi(root, config, *, transport_class=PilotTransport):
    """Probe the wheel-observed SSI route without copying placeholder auth headers."""
    validate_config(config)
    base = inside(root, config['output_root'])
    wheel = base/'discovery/vietfin-0.2.0-py3-none-any.whl'
    expected = 'ae1fb8418a09c2afbbe3f7b957b49e13cb9f826e94b856666c56cb5d83505fa4'
    if digest(wheel.read_bytes()) != expected:
        raise ValueError('published VietFin wheel pin mismatch')
    with zipfile.ZipFile(wheel) as pack:
        lookup_source = pack.read('vietfin/providers/ssi/utils/equity_search.py')
        report_source = pack.read('vietfin/providers/ssi/utils/equity_fundamental_income.py')
    catalog_url = 'https://fiin-core.ssi.com.vn/Master/GetListOrganization?language=vi'
    if catalog_url.encode() not in lookup_source or b'https://fiin-fundamental.ssi.com.vn/FinancialStatement/' not in report_source:
        raise ValueError('SSI endpoints not present in inspected source')
    ssi_config = dict(config, approved_hosts=['fiin-core.ssi.com.vn','fiin-fundamental.ssi.com.vn'],
        cache_epoch='ssi-source-route-pilot5-20261019-v1', budgets=dict(config['budgets'],
            max_logical_requests=16,max_transport_attempts=16,max_total_downloaded_bytes=34_000_000))
    run = base/'ssi'
    run.mkdir(parents=True, exist_ok=True)
    with exclusive(run):
        contract = dict(config=ssi_config,wheel_sha256=expected,latest_year=2025,number_of_periods=3,
            mode='UNAUTHENTICATED_PUBLIC_ROUTE_PROBE_NOT_VIETFIN_SDK_EXECUTION',
            note='Do not forge X-Fiin-Key/User-ID/Seed placeholders, credentials, cookies or tokens')
        contract_path=run/'contract.json'
        if contract_path.exists() and contract_path.read_bytes()!=encoded(contract):
            raise ValueError('SSI probe contract changed')
        if not contract_path.exists(): immutable_write(contract_path,encoded(contract))
        network=run/'network'; network.mkdir(exist_ok=True)
        if (network/'transport.jsonl').exists():
            saved=read_compact(network)
            if saved['torn_tail_bytes']: raise ValueError('torn SSI journal requires review')
            if saved['state']['boundary'] or saved['state']['budget_stop']:
                return dict(status='SSI_TERMINAL_CACHE_NO_NETWORK',counters=saved['state'],new_network=0)
        transport=transport_class(root,network,ssi_config)
        def get_once(key,url):
            receipt=run/(key+'.json')
            if receipt.exists():
                record=read(receipt)
                return inside(root,record['raw_path']).read_bytes() if record.get('raw_path') else None
            if any(x['url']==url for x in transport.state['requests'].values()):
                raise ValueError('SSI interrupted request requires review')
            record=dict(url=url,key=key)
            body=None
            try:
                body,status=transport.get(url)
                path=run/'raw'/(digest(body)+'.bin')
                if not path.exists(): immutable_write(path,body)
                record.update(status='RAW_RECEIVED_NEEDS_FORMAT_UNIT_SCOPE_REVIEW',http_status=status,
                              raw_path=path.relative_to(root).as_posix(),sha256=digest(body))
            except Exception as error:
                record.update(status='ACCESS_STOP' if transport.state['boundary'] else
                    'BUDGET_STOP' if transport.state['budget_stop'] else 'REQUEST_ERROR',error=str(error))
            immutable_write(receipt,encoded(record))
            return body
        catalog=get_once('catalog',catalog_url)
        if catalog is not None and not transport.state['boundary'] and not transport.state['budget_stop']:
            records=json.loads(catalog).get('items',[])
            if not isinstance(records,list): raise ValueError('SSI organization list required')
            for symbol in SYMBOLS:
                matching=[x for x in records if isinstance(x,dict) and x.get('ticker')==symbol]
                if len(matching)!=1 or not isinstance(matching[0].get('organCode'),str):
                    continue
                for report,name in [('balance','BalanceSheet'),('income','IncomeStatement'),('cash','CashFlow')]:
                    url='https://fiin-fundamental.ssi.com.vn/FinancialStatement/Download'+name+'?'+urlencode(
                        dict(language='en',OrganCode=matching[0]['organCode'],Skip=0,Frequency='Yearly',numberOfPeriod=3,latestYear=2025))
                    get_once(symbol+'-'+report,url)
                    if transport.state['boundary'] or transport.state['budget_stop']: break
                if transport.state['boundary'] or transport.state['budget_stop']: break
        return dict(status='PARTIAL_UNAUTHENTICATED_SSI_ROUTE_PROBE',
                    counters=read_compact(network)['state'],accepted_financial_fields=0)


def source_observations(root,config):
    root=Path(root).resolve();base=inside(root,config['output_root'])
    receipts=[read(p) for p in sorted((base/'receipts').glob('*.json'))]
    catalog=read(base/'ssi/catalog.json') if (base/'ssi/catalog.json').exists() else None
    counts=dict(Counter(x['status'] for x in receipts))
    observations=dict(tcbs=dict(receipts=len(receipts),statuses=counts,
        http_404=sum('HTTP 404' in x.get('error','') for x in receipts),
        accepted_fields=0),ssi=dict(catalog_status=catalog.get('status') if catalog else 'NOT_ATTEMPTED',
        error=catalog.get('error') if catalog else None,accepted_fields=0),
        sdk_execution=False,rule='No API values accepted without mapping, unit, scope, period and version QA')
    pins={}
    paths=list((base/'receipts').glob('*.json'))
    paths += [base/p for p in ['acquisition-contract.json','network/transport.jsonl','ssi/contract.json',
              'ssi/catalog.json','ssi/network/transport.jsonl','discovery/package.json',
              'discovery/acquisition.jsonl','discovery/vietfin-0.2.0-py3-none-any.whl']]
    for p in paths:
        if p.is_file(): pins[p.relative_to(root).as_posix()]=digest(p.read_bytes())
    return observations,pins


def review(root, config):
    validate_config(config)
    root = Path(root).resolve()
    baseline_path = inside(root, config['baseline_result'])
    baseline = verify_result(root, baseline_path)
    facts, _, valuation, review_pins = reviewed(root, inside(root, config['baseline_run']))
    if review_pins[0]['path'] != config['review_package']:
        raise ValueError('unexpected reference review version')
    comparisons = list(csv.DictReader(io.StringIO((baseline_path/'qa.csv').read_text(encoding='utf-8-sig'))))
    selections, decisions = reference_decisions(facts, comparisons)
    original = read(inside(root, config['baseline_config']))
    metrics, details, dependencies = compute(facts, valuation, original['primary_metric_variants'])
    prior = list(csv.DictReader(io.StringIO((baseline_path/'metrics.csv').read_text(encoding='utf-8-sig'))))
    for row in metrics:
        old = next(x for x in prior if (x['symbol'], x['family']) == (row['symbol'], row['family']))
        if finite(row['value']) != finite(old['value'] if old['value'] else None):
            raise ValueError('reference metric changed')
    run = inside(root, config['output_root'])
    observations,provider_pins=source_observations(root,config)
    semantic = dict(config=config, baseline=baseline, review_pins=review_pins, selections=selections,
                    decisions=decisions, source_observations=observations, provider_pins=provider_pins,
                    implementation_sha256=digest(Path(__file__).read_bytes()))
    output = run / 'reviews' / digest(encoded(semantic))[:20]
    summary = dict(status='PARTIAL_WITH_VERIFIED_REFERENCE_RESULTS_PROVIDER_BENCHMARK_PENDING',
        selected_facts=len(selections), comparisons=len(decisions),
        api_pdf_matches=sum(x['decision']=='PDF_CORROBORATED_BY_API' for x in decisions),
        quarantined_api_conflicts=sum(x['decision']=='QUARANTINE_API_USE_REVIEWED_PDF' for x in decisions),
        reference_selection_counts=dict(Counter(x['selection_reason'] for x in selections)),
        recomputed_cells=sum(x['value'] is not None for x in metrics), required_cells=30,
        tcbs_ssi_qa_accepted_fields=0, provider_benchmark_status='PARTIAL_NO_VALIDATED_PROVIDER_FIELDS',
        source_observations=observations,
        baseline_metric_values_sha256=baseline['metric_values_sha256'],
        missing=[x for x in dependencies if x['missing']], new_network=0, new_pdf=0, new_ocr=0, **CLOSED)
    if not output.exists():
        output.mkdir(parents=True)
        for name, value in [('summary.json', summary), ('selected-references.json', selections),
                            ('decisions.json', decisions), ('metrics.json', metrics),
                            ('calculation-details.json', details), ('semantic-inputs.json', semantic)]:
            immutable_write(output/name, encoded(value))
        immutable_write(output/'decisions.csv', csv_data(decisions))
        immutable_write(output/'metrics.csv', csv_data(metrics))
        immutable_write(output/'provider-plan.json', encoded(jobs()))
        pins = dict(provider_pins,**{config['baseline_result']+'/manifest.json': digest((baseline_path/'manifest.json').read_bytes()),
                config['review_package']: review_pins[0]['sha256']})
        immutable_write(output/'manifest.json', encoded(dict(files={p.name:digest(p.read_bytes())
            for p in output.iterdir() if p.is_file()}, source_pins=pins,
            implementation_sha256=digest(Path(__file__).read_bytes()))))
    return dict(summary, output=output.relative_to(root).as_posix())


def verify(root, output):
    output = inside(root, output)
    manifest = read(output/'manifest.json')
    for name, expected in manifest['files'].items():
        if digest((output/name).read_bytes()) != expected:
            raise ValueError('review artifact changed: ' + name)
    for relative, expected in manifest['source_pins'].items():
        if digest(inside(root, relative).read_bytes()) != expected:
            raise ValueError('review source changed')
    if digest(Path(__file__).read_bytes()) != manifest['implementation_sha256']:
        raise ValueError('validation implementation changed')
    semantic = read(output/'semantic-inputs.json')
    replay = review(root, semantic['config'])
    if replay['output'] != output.relative_to(root).as_posix():
        raise ValueError('review replay mismatch')
    return dict(status='VERIFIED_PARTIAL', recomputed_cells=replay['recomputed_cells'],
                api_conflicts=replay['quarantined_api_conflicts'], new_network=0)
