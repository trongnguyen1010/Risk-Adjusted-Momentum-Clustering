import argparse,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_source_completion import export
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();r=export(ROOT,a.config,a.output)
    print(json.dumps(dict(status=r['status'],provider_cells=r['provider_cells'],
        f_score=[(x['year'],x['decision_date'],x['vas_reference']['value']) for x in r['f_score']],
        m_score=[(x['year'],x['gross_trade_reference']['value'],x['conditional_range']) for x in r['m_score']],
        valuation={k:r['reported_valuation'][k] for k in ['pe','pb','bvps']})))
