"""Create immutable execution plan v8 from verified batch engineering evidence."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from delta_t1.experiments.financial_batch_flow import verify_flow

if __name__=='__main__':
    active='data/financial/batch_flow_v9_final';replay='data/financial/batch_flow_v10_replay'
    for r in [active,replay]:verify_flow(ROOT,r)
    result=json.loads((ROOT/active/'results.json').read_bytes())
    rr=json.loads((ROOT/replay/'results.json').read_bytes())
    if result['engineering_status']!='COMPLETE' or rr['engineering_status']!='COMPLETE' or rr['metrics']['new_checkpoints']:
        raise ValueError('engineering/replay gate not satisfied')
    c=json.loads((ROOT/'configs/data/financial_execution_plan_v7.json').read_bytes())
    c['version']='financial-execution-plan-v8'
    c['report']='artifacts/reports/financial-batch-flow-v1/report.md'
    c['latest_runs'].update(batch_engineering=active,batch_replay=replay)
    c['stage_status']['FIN-D5']='BOUNDED_ENGINEERING_COMPLETE_ACCEPTED_DATA_EXPANSION_PENDING'
    c['automation_policy']='configs/data/financial_batch_flow_v6.json'
    c['automation_scope']=dict(symbols=result['symbols'],years=[2025],
        engineering_status='COMPLETE_10_SYMBOL_OFFLINE_RESUME_VERIFIED',
        unattended_numeric_acceptance_allowed=False,scale_to_market_universe_allowed=False,
        current_unique_pdf_pages=691,current_unique_ocr_prefix_pages=32,
        reference_adapter_symbols=['FPT','VNM','PVS','ACV'],
        new_symbols_numeric_acceptance=0,
        next=['Close pilot feature-specific semantic/PIT/TTM/events',
              'Visually reviewed ground truth and parser QA per new template',
              'Independent thresholds and cost review before 20-30-symbol candidate batch',
              'Historical security/sector, usable history and separate financial protocol'])
    c['batch_manifest_sha256']={r:digest((ROOT/r/'manifest.json').read_bytes()) for r in [active,replay]}
    immutable_write(ROOT/'configs/data/financial_execution_plan_v8.json',encoded(c))
    print('financial-execution-plan-v8: engineering complete; acceptance/scale gates closed')
