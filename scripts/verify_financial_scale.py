"""Offline verification of the sealed scale experiment and exact dependencies."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.experiments.financial_batch_flow import verify_pins
from delta_t1.experiments.financial_scale_probe import verify
from delta_t1.ingestion.financial_batch_evidence import inside
from delta_t1.ingestion.financial_documents import verify_inventory
if __name__=='__main__':
    config=inside(ROOT,'configs/data/financial_scale_review_v1.json','configs')
    c=json.loads(config.read_bytes());verify_pins(ROOT,c['input_pins']);verify_pins(ROOT,c['code_pins'])
    verify(ROOT,'data/financial/scale_probe50_20261008_v1')
    for run in c['sealed_runs']+['data/financial/scale_review4_20261008_v1',
            'data/financial/issuer_supplement_v1/run-2026-10-08T101058.771561-0000-7684a622']:
        verify_inventory(inside(ROOT,run,'data'))
    ledger=inside(ROOT,'data/financial/scale_review4_20261008_v1','data')
    saved=json.loads((ledger/'config.json').read_bytes())
    if saved!=c:raise ValueError('review config drift')
    result=json.loads((ledger/'results.json').read_bytes())
    if any(result[k] is not False for k in ['financial_features_allowed','research_ready','financial_cluster_allowed']):
        raise ValueError('gate promotion forbidden')
    print(json.dumps(dict(status='VERIFIED_OFFLINE',review_summary=result),ensure_ascii=False,indent=2))
