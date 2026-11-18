"""Evaluate existing score calculators against all cached annual input partitions.

Results remain computation diagnostics until input quality is accepted. No
synthetic shares, proxy EBIT, partial F-score, new source acquisition or fitting.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.features.financial_reference import calculate
from delta_t1.features.financial_vas_reference import calculate_vas_f_score, calculate_vas_m_score, calculate_disclosed_basic_eps


def run(output):
    output = ROOT/output
    if output.exists():raise ValueError('Immutable output exists; select another version')
    source=ROOT/'data/financial/history_api_input_review1522_v1/jobs/a4585089037bb3d9e5f2/symbols'
    pins, counts, missing = {}, Counter(), Counter()
    results=[];symbols=set();partitions=0
    for index, folder in enumerate(sorted(source.iterdir()),1):
        path=folder/'field-inputs.json'
        if not path.is_file():continue
        body=path.read_bytes();sha=hashlib.sha256(body).hexdigest()
        manifest=json.loads((folder/'manifest.json').read_bytes())
        if manifest['field-inputs.json']!=sha:raise ValueError('Input checksum mismatch: '+str(path))
        pins[path.relative_to(ROOT).as_posix()]=sha
        by_period=defaultdict(dict);ticker=None
        for row in json.loads(body):
            ticker=row['symbol']
            if row.get('value') is not None:by_period[int(row['year']),row['provider_type']][row['field']]=row['value']
        symbols.add(ticker)
        for (year, provider), current in sorted(by_period.items()):
            if not 2016<=year<=2025:continue
            partitions+=1
            window={(field,offset):value for offset in [0,-1,-2] for field,value in by_period.get((year+offset,provider),{}).items()}
            f=calculate_vas_f_score(window)
            m=calculate_vas_m_score(window,'GROSS_SHORT_TERM_TRADE')
            z=calculate('Z_SCORE',current)
            eps=calculate_disclosed_basic_eps(current.get('eps_adjusted_earnings_numerator'),current.get('weighted_average_basic_shares'),12)
            evaluated={'EPS':eps,'F_SCORE':f,'M_SCORE':m,'Z_SCORE':z,
                'PE':{'value':None,'status':'MISSING_DATED_PRICE_AND_SHARE_EVENT_BASIS'},
                'PB':{'value':None,'status':'MISSING_PARENT_COMMON_EQUITY_COMMON_SHARES_AND_DATED_PRICE'}}
            for family,result in evaluated.items():
                counts[family+':'+result['status']]+=1
                if result.get('value') is not None:counts[family+':NUMERIC_PENDING_SOURCE_ACCEPTANCE']+=1
                for field in result.get('missing',[]):missing[family+':'+str(field)]+=1
                if family=='EPS' and result.get('value') is None:
                    for field in ('eps_adjusted_earnings_numerator','weighted_average_basic_shares'):
                        if field not in current:missing['EPS:'+field]+=1
                for signal in result.get('signals',{}).values():
                    for field in signal.get('missing',[]):missing['F_SCORE:'+str(field)]+=1
                results.append(dict(symbol=ticker,year=year,provider_type=provider,family=family,
                    value=json.dumps(result.get('value')),status=result['status'],known_signals=result.get('known_signals'),
                    details=json.dumps(result,ensure_ascii=False),released_to_product=False,
                    source_acceptance='UNVERIFIED_UNIT_SCOPE_VINTAGE; calculation alone is not acceptance'))
        if index%200==0:print(f'Evaluated {index} cached symbols',flush=True)
    output.mkdir(parents=True)
    with (output/'score-attempts.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]),lineterminator='\n');w.writeheader();w.writerows(results)
    summary=dict(symbols=len(symbols),annual_provider_partitions=partitions,calculator_evaluations=len(results),
                 results=dict(counts),missing_inputs=dict(missing),new_scores_released_to_product=0,
                 note='Existing reviewed values remain available separately. Source EPS is quoted, not recomputed.',
                 strict_pit_ready=False,research_ready=False)
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    for rel in ['scripts/calculate_cached_financial_scores.py','src/delta_t1/features/financial_reference.py','src/delta_t1/features/financial_vas_reference.py']:
        pins[rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    (output/'input-pins.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='missing_inputs'},ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='data/financial/financial_score_attempt_v1/results/cache-calculators-v1')
    run(p.parse_args().output)
