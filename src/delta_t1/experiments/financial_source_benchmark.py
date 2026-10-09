"""Paired bounded provider benchmark: coverage, sampled QA and observed costs."""
import csv
import io
import json
import re
import statistics
import time
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from ..ingestion.cafef_financial import digest, encoded, immutable_write, now
from ..ingestion.cafef_financial_detail import detail_url
from ..ingestion.financial_batch_evidence import inside, seal
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.financial_source_compare import (COMMON, REPORTS, BenchmarkTransport,
                                                  kbs_request, parse_cafef, parse_kbs)
from ..ingestion.sources.base import AccessControlError


def validate_config(c):
    if c.get('version')!='financial-source-benchmark-v1' or not isinstance(c.get('symbols'),dict) or not 1<=len(c['symbols'])<=10:
        raise ValueError('bounded benchmark config required')
    if any(not re.fullmatch('[A-Z][A-Z0-9]{1,7}',symbol) or kind not in ['Regular','Bank','Securities','Insurance'] for symbol,kind in c['symbols'].items()):
        raise ValueError('invalid benchmark symbols/types')
    if any(c.get(k) is not False for k in ['financial_features_allowed','financial_cluster_allowed','research_ready']):
        raise ValueError('closed gates required')
    limits={'max_attempts':450,'max_response_bytes':3_000_000,'max_total_bytes':150_000_000,'max_seconds':3600,
            'kbs_annual_max_pages':6,'kbs_quarter_max_pages':18,'kbs_control_max_pages':9}
    if any(type(c.get(k)) is not int or not 1<=c[k]<=limit for k,limit in limits.items()):raise ValueError('invalid benchmark cap')
    if type(c.get('interval_seconds')) not in (int,float) or not 2<=c['interval_seconds']<=60:raise ValueError('invalid request interval')
    if set(c.get('approved_hosts',[]))!={'cafef.vn','kbbuddywts.kbsec.com.vn'}:raise ValueError('approved hosts required')
    if c['annual_years']!=list(range(2021,2026)) or c['quarter_years']!=[2024,2025]:raise ValueError('frozen comparison years required')
    if len(set(c['history_symbols']))!=len(c['history_symbols']) or not set(c['history_symbols'])<=set(c['symbols']):raise ValueError('invalid history sample')


def coverage(cells, config):
    present = {(r['provider'],r['symbol'],r['report'],r['year'],r['quarter']) for r in cells
               if r['unambiguous'] and r['raw_value'] is not None and r['numeric_status']!='INVALID_NUMERIC_VALUE'}
    rows = []
    for provider in ['CAFEF','KBS']:
        for symbol in config['symbols']:
            years = config['annual_years'] if symbol in config['history_symbols'] else [2025]
            quarters = [(y,q) for y in config['quarter_years'] for q in range(1,5)] if symbol in config['history_symbols'] else [(2025,4)]
            for year,quarter in [(y,0) for y in years]+quarters:
                for report in REPORTS:
                    rows.append(dict(provider=provider,symbol=symbol,report=report,year=year,quarter=quarter,
                        present=(provider,symbol,report,year,quarter) in present, verified=False))
    return rows


def qa(cells, references):
    grouped = defaultdict(set)
    for row in cells:
        if row['quarter']==0 and row['field'] and row['unambiguous'] and row['comparison_value'] is not None:
            grouped[(row['provider'],row['symbol'],row['year'],row['field'])].add(row['comparison_value'])
    rows = []
    for provider in ['CAFEF','KBS']:
        for ref in references:
            values = grouped[(provider,ref['symbol'],ref['year'],ref['field'])]
            eps = ref['field'] in {'vendor_basic_eps','vendor_diluted_eps'}
            tolerance = Decimal('0.5' if eps else '1500')
            differences = [Decimal(v)-Decimal(ref['value']) for v in sorted(values)]
            status = ('MISSING_OR_UNMAPPED' if not values else 'MULTIPLE_CANDIDATE_VALUES' if len(values)>1 else
                      'MATCH_WITHIN_TOLERANCE' if abs(differences[0])<=tolerance else 'VALUE_DIFFERENCE_REVIEW_REQUIRED')
            rows.append(dict(provider=provider,**ref, candidate_values=sorted(values), status=status,
                             difference=str(differences[0]) if len(differences)==1 else None,
                             tolerance=str(tolerance),scope_vintage_verified=False))
    return rows


def write_csv(path, rows):
    if not rows: return
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,list(rows[0]));writer.writeheader()
    writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
    immutable_write(path,stream.getvalue().encode('utf-8-sig'))


def run(root, config_path, output, execute_network=False, *, transport_class=BenchmarkTransport):
    root=Path(root).resolve(); source=inside(root,config_path,'configs'); c=json.loads(source.read_bytes())
    validate_config(c)
    out=inside(root,output,'data');out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'config.json',source.read_bytes())
    for name in ['src/delta_t1/ingestion/financial_source_compare.py','src/delta_t1/experiments/financial_source_benchmark.py']:
        immutable_write(out/'code'/Path(name).name,(root/name).read_bytes())
    refs=[]; pins={}; checked=set()
    for path in c['ground_truth_paths']:
        file=inside(root,path,'data'); pins[path]=digest(file.read_bytes()); obj=json.loads(file.read_bytes())
        for fact in obj['facts'] if isinstance(obj,dict) else obj:
            field=fact.get('field',fact.get('item'))
            if field not in COMMON or fact['year'] not in [2024,2025] or fact['symbol'] not in c['symbols']: continue
            ref=dict(symbol=fact['symbol'],year=fact['year'],field=field,value=str(fact['value']),
                     reference_path=path,pdf_sha256=fact['pdf_sha256'],pdf_page=fact['pdf_page'])
            refs.append(ref)
            for kind in ['pdf','image']:
                p=fact.get(kind+'_path')
                if p:
                    file=inside(root,p,'data'); expected=fact[kind+'_sha256']
                    if file not in checked:
                        if digest(file.read_bytes())!=expected: raise ValueError('ground truth source hash mismatch')
                        checked.add(file);pins[file.relative_to(root).as_posix()]=expected
    immutable_write(out/'reference-inputs.json',encoded(dict(source_pins=pins,references=refs)))
    cells=[]; requests=[]; stopped=False; started=time.monotonic()
    transport=transport_class(out,c)
    def acquire(job, cohort='MAIN'):
        nonlocal stopped
        record=dict(job,cohort=cohort,at=now(),status='NOT_EXECUTED',network_seconds=None,parse_seconds=None)
        if not execute_network or stopped: requests.append(record);return [],record
        try:
            body,duration=transport.get(job)
            path='raw/'+digest(body)+('.html' if job['provider']=='CAFEF' else '.json')
            if not (out/path).exists():immutable_write(out/path,body)
            record.update(network_seconds=duration,bytes=len(body),path=path,sha256=digest(body))
            parse_began=time.monotonic()
            parsed,details=(parse_cafef if job['provider']=='CAFEF' else parse_kbs)(body,dict(job,path=path,sha256=digest(body)),c['symbols'][job['symbol']])
            record.update(details,parse_seconds=time.monotonic()-parse_began)
            if cohort=='MAIN': cells.extend(parsed)
        except AccessControlError as exc:
            stopped=True;record.update(status='HARD_STOP',error=str(exc));parsed=[]
        except (ValueError,KeyError,TypeError) as exc:
            record.update(status='ERROR',error=str(exc));parsed=[]
            if any(t in str(exc) for t in [' cap','time cap']): stopped=True
        requests.append(record)
        with (out/'progress.jsonl').open('a',encoding='utf8') as stream:stream.write(json.dumps(record,ensure_ascii=False)+'\n')
        print(json.dumps({k:record.get(k) for k in ['provider','symbol','report','period','page','year','quarter','cohort','status']},ensure_ascii=False),flush=True)
        return parsed,record
    # Alternating provider cohorts per symbol/report; fresh traffic on both sides.
    for index,(symbol,kind) in enumerate(c['symbols'].items()):
        for report,statement in REPORTS.items():
            for period in ['year','quarter']:
                def cafe():
                    anchors=([(2025,0),(2021,0)] if period=='year' else [(2025,4),(2024,4)]) if symbol in c['history_symbols'] else [(2025,0 if period=='year' else 4)]
                    for y,q in anchors:
                        acquire(dict(provider='CAFEF',symbol=symbol,report=report,statement=statement,period=period,year=y,quarter=q,url=detail_url(symbol,statement,y,q)))
                        if stopped: break
                def kbs():
                    max_pages=(c['kbs_annual_max_pages'] if period=='year' else c['kbs_quarter_max_pages']) if symbol in c['history_symbols'] else c['kbs_control_max_pages']
                    targets={(y,0) for y in c['annual_years']} if period=='year' else {(y,q) for y in c['quarter_years'] for q in range(1,5)}
                    if symbol not in c['history_symbols']:targets={(2025,0 if period=='year' else 4)}
                    observed=set()
                    for page in range(1,max_pages+1):
                        parsed,record=acquire(kbs_request(symbol,report,period,page,1))
                        observed.update((r['year'],r['quarter']) for r in parsed if r['unambiguous'] and r['raw_value'] is not None)
                        if stopped or record['status'] in ['END_OF_SERIES','ERROR'] or targets<=observed:break
                for collect in ([cafe,kbs] if index%2==0 else [kbs,cafe]):
                    if not stopped:collect()
            if stopped:break
        if stopped:break
    if not stopped and 'FPT' in c['symbols']:
        for report in REPORTS:
            for period in ['year','quarter']:acquire(kbs_request('FPT',report,period,1,12),'LEGACY_PAGE12_DIAGNOSTIC')
    periods=coverage(cells,c); comparisons=qa(cells,refs); provider_stats={}
    for provider in ['CAFEF','KBS']:
        selected=[r for r in requests if r['provider']==provider and r['cohort']=='MAIN']
        latency=[r['network_seconds'] for r in selected if r['network_seconds'] is not None]
        parse=[r['parse_seconds'] for r in selected if r['parse_seconds'] is not None]
        p=[r for r in periods if r['provider']==provider]; q=[r for r in comparisons if r['provider']==provider]
        observed=sum(r['present'] for r in p)
        provider_stats[provider]=dict(requests=len(selected),request_statuses=dict(Counter(r['status'] for r in selected)),
            downloaded_bytes=sum(r.get('bytes',0) for r in selected),network_seconds=sum(latency),
            median_network_seconds=statistics.median(latency) if latency else None,parse_seconds=sum(parse),
            median_parse_seconds=statistics.median(parse) if parse else None,
            targeted_statement_periods=len(p),present_statement_periods=observed,
            requests_per_observed_statement_period=len(selected)/observed if observed else None,
            qa_counts=dict(Counter(r['status'] for r in q)))
    result=dict(version=c['version'],network_executed=execute_network,engineering_status='PLANNED' if not execute_network else 'HARD_STOP' if stopped and transport.state['boundary'] else 'PARTIAL' if stopped or any(r['status']=='ERROR' for r in requests) else 'COMPLETE',
        collection_seconds=time.monotonic()-started,source_summary=provider_stats,requests=requests,transport_totals=transport.state,
        wire_cells=len(cells),accepted_facts=0,financial_features_allowed=False,financial_cluster_allowed=False,research_ready=False,
        methodology_status='SOURCE_SELECTION_ENGINEERING_BENCHMARK_NOT_CANONICAL_MERGE',measurement_limits=['NINE_SYMBOL_PURPOSIVE_SAMPLE','ONE_FRESH_PASS_NOT_LONG_TERM_LATENCY','LATEST_PROVIDER_VINTAGES_NOT_PIT','REGULAR_ONLY_NUMERIC_CROSSWALK'])
    immutable_write(out/'results.json',encoded(result));immutable_write(out/'candidates.json',encoded(cells))
    immutable_write(out/'coverage.json',encoded(periods));immutable_write(out/'qa.json',encoded(comparisons))
    write_csv(out/'coverage.csv',periods);write_csv(out/'qa.csv',comparisons)
    seal(out);verify_inventory(out)
    return result
