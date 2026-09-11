"""Create deterministic SYNTHETIC fixtures. Weekdays here are NOT a Vietnam calendar."""
import csv
import json
import math
from datetime import date, timedelta
from pathlib import Path


def generate(root):
    root = Path(root)
    target = root / "examples" / "synthetic"
    target.mkdir(parents=True, exist_ok=True)
    days = []
    day = date(2024, 1, 1)
    while day <= date(2025, 6, 30):
        if day.weekday() < 5:
            days.append(day.isoformat())
        day += timedelta(days=1)
    end_dates = {max(d for d in days if d[:7] == month) for month in {d[:7] for d in days}}
    tables = {key: [] for key in ('securities','prices_daily','benchmark_daily','trading_calendar','corporate_actions','risk_free_rate')}
    for ex in ['HOSE', 'HNX']:
        for d in days:
            tables['trading_calendar'].append(dict(exchange=ex,trade_date=d,is_open='true',is_month_end=str(d in end_dates).lower(),close_at=d+'T15:00:00+07:00',decision_at=d+'T18:00:00+07:00'))
    for i in range(12):
        ticker, sid, ex = f'SYN{i:02d}', f'SYNTHETIC-{i:02d}', 'HOSE' if i < 6 else 'HNX'
        tables['securities'].append(dict(security_id=sid,ticker=ticker,company_name='Synthetic Company '+str(i),exchange=ex,listing_date=days[0],valid_from=days[0],available_at=days[0]+'T00:00:00+07:00',currency='VND',price_unit='VND',identity_status='synthetic'))
        for t,d in enumerate(days):
            close = round((20000+i*1500)*math.exp((0.00015+i*0.000015)*t + 0.02*math.sin(t/11+i)),4)
            tables['prices_daily'].append(dict(security_id=sid,ticker=ticker,exchange=ex,trade_date=d,raw_open=close,raw_high=close*1.01,raw_low=close*.99,raw_close=close,adj_close=close,volume=100000+i*1000,traded_value=close*(100000+i*1000),trading_status='normal',adjustment_basis='synthetic',available_at=d+'T17:00:00+07:00'))
    for t,d in enumerate(days):
        tables['benchmark_daily'].append(dict(index_id='VNINDEX',trade_date=d,close=1000*math.exp(.0002*t+.015*math.sin(t/9)),available_at=d+'T17:00:00+07:00'))
    tables['risk_free_rate'].append(dict(date=days[0],tenor='synthetic_annual',annual_rate=0,available_at=days[0]+'T00:00:00+07:00'))
    jobs = []
    for table, rows in tables.items():
        headers = sorted({k for row in rows for k in row}) or ['event_id','security_id','event_type']
        with (target/(table+'.csv')).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        jobs.append(dict(id=table,table=table,provider='csv',path='examples/synthetic/'+table+'.csv',source='synthetic_fixture',allow_empty=table=='corporate_actions'))
    config=dict(synthetic=True,jobs=jobs,features=dict(benchmark_id='VNINDEX',rf_annual=0,accepted_adjustments=['synthetic'],required_features=['mom_21','mom_63','mom_126','mom_252','vol_63','sharpe_63','mdd_126','beta_126','liquidity_21']))
    (root/'configs').mkdir(parents=True,exist_ok=True)
    (root/'configs/demo.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    return root/'configs/demo.json'


if __name__=='__main__':
    print(generate(Path(__file__).resolve().parents[1]))
