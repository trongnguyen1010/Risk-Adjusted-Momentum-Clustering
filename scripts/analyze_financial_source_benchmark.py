"""Offline analysis of a sealed paired crawl; no period relabeling or acceptance."""
import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.ingestion.financial_source_compare import parse_cafef, parse_kbs


def analyze(run_path):
    verify_inventory(run_path)
    result=json.loads((run_path/'results.json').read_bytes())
    config=json.loads((run_path/'config.json').read_bytes())
    cells=json.loads((run_path/'candidates.json').read_bytes())
    periods=json.loads((run_path/'coverage.json').read_bytes())
    qa=json.loads((run_path/'qa.json').read_bytes())
    by_symbol=[]
    for symbol in config['symbols']:
        item=dict(symbol=symbol,proposed_type=config['symbols'][symbol])
        for provider in ['CAFEF','KBS']:
            chosen=[r for r in periods if r['symbol']==symbol and r['provider']==provider]
            checks=[r for r in qa if r['symbol']==symbol and r['provider']==provider]
            item[provider]=dict(present=sum(r['present'] for r in chosen),target=len(chosen),
                annual_present=sum(r['present'] for r in chosen if r['quarter']==0),
                quarter_present=sum(r['present'] for r in chosen if r['quarter']!=0),
                qa_counts=dict(Counter(r['status'] for r in checks)),
                missing=[dict(report=r['report'],year=r['year'],quarter=r['quarter']) for r in chosen if not r['present']])
        by_symbol.append(item)
    timing=defaultdict(list);diagnostic=[]
    for request in result['requests']:
        if not request.get('path'):continue
        body=(run_path/request['path']).read_bytes()
        if digest(body)!=request['sha256']:raise ValueError('raw hash changed')
        parse=parse_cafef if request['provider']=='CAFEF' else parse_kbs
        durations=[]
        for _ in range(3):
            began=time.perf_counter()
            parsed,meta=parse(body,request,config['symbols'][request['symbol']])
            durations.append(time.perf_counter()-began)
        if request['cohort']=='MAIN':timing[request['provider']].append(statistics.median(durations))
        else:
            diagnostic.append(dict(symbol=request['symbol'],report=request['report'],period=request['period'],
                page_size=request['page_size'],raw_path=request['path'],sha256=request['sha256'],
                headers=json.loads(body)['Head'],cells=len(parsed),
                ambiguous_cells=sum(not row['unambiguous'] for row in parsed),**meta))
    # Detect values that match another observed CafeF year, without assigning that
    # year to the KBS value. A signature match remains a diagnostic hypothesis.
    cafe=defaultdict(set)
    for row in cells:
        if row['provider']=='CAFEF' and row['quarter']==0 and row['field'] and row['comparison_value'] is not None:
            cafe[row['symbol'],row['report'],row['field'],row['year']].add(row['comparison_value'])
    mismatches=[]
    for row in cells:
        if row['provider']!='KBS' or row['quarter']!=0 or not row['field'] or row['comparison_value'] is None:continue
        value=Decimal(row['comparison_value']);tolerance=Decimal('.5' if 'eps' in row['field'] else '1500')
        matches=sorted({year for (symbol,report,field,year),values in cafe.items()
            if (symbol,report,field)==(row['symbol'],row['report'],row['field'])
            and any(abs(Decimal(other)-value)<=tolerance for other in values)})
        if matches and row['year'] not in matches:
            mismatches.append(dict(symbol=row['symbol'],report=row['report'],field=row['field'],
                kbs_header_year=row['year'],kbs_comparison_value=row['comparison_value'],
                cafef_matching_years=matches,kbs_raw_path=row['source_path'],kbs_sha256=row['source_sha256'],
                status='CROSS_YEAR_SIGNATURE_REVIEW_REQUIRED_NOT_RELABELLED'))
    previous=None;events=0
    for line in (run_path/'transport.jsonl').read_bytes().splitlines():
        row=json.loads(line)
        if row['previous_sha256']!=previous:raise ValueError('journal chain changed')
        previous=digest(line);events+=1
    return dict(source_summary=result['source_summary'],per_symbol=by_symbol,
        parse_timing=dict(method='OFFLINE_3_REPEATS_PER_RESPONSE_MEDIAN_PERF_COUNTER_NO_IO_NO_NETWORK',
            providers={p:dict(responses=len(values),median_seconds=statistics.median(values),
                               sum_median_seconds=sum(values)) for p,values in timing.items()}),
        legacy_page12=diagnostic,cross_year_signature_alerts=mismatches,
        qa_exceptions=[r for r in qa if r['status']!='MATCH_WITHIN_TOLERANCE'],
        verification=dict(raw_inventory='PASS',journal_hash_chain='PASS',journal_events=events,
            manifest_sha256=digest((run_path/'manifest.json').read_bytes())),
        decision='CAFEF_PRIMARY_STRUCTURED_CANDIDATE_KBS_DIAGNOSTIC_ONLY_PENDING_PERIOD_VALUE_QA',
        accepted_facts=0,financial_cluster_allowed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',default='data/financial/source_benchmark_20261008_v1')
    parser.add_argument('--output',default='artifacts/reports/financial-source-benchmark-v1/analysis.json')
    args=parser.parse_args()
    source=(ROOT/args.run).resolve();destination=(ROOT/args.output).resolve()
    if not source.is_relative_to(ROOT/'data/financial') or not destination.is_relative_to(ROOT/'artifacts/reports'):
        parser.error('workspace financial/report paths required')
    output=analyze(source);immutable_write(destination,encoded(output))
    print(json.dumps({k:output[k] for k in ['source_summary','parse_timing','verification']},indent=2))
