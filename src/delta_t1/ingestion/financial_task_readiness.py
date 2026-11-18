"""Per-task input preparation; no feature values or eligibility are calculated."""
import json
from pathlib import Path
from .cafef_financial import digest,encoded,immutable_write
from .financial_documents import verify_inventory
from .financial_pilot_readiness import SIGNALS

ANNUAL_TASKS = {
 'M_SCORE': [('document_reconciled_net_receivables',0),('document_reconciled_net_receivables',-1),
   ('net_revenue',0),('net_revenue',-1),('gross_profit',0),('gross_profit',-1),
   ('current_assets',0),('current_assets',-1),('net_tangible_ppe',0),('net_tangible_ppe',-1),
   ('total_assets',0),('total_assets',-1),('ppe_depreciation_excluding_amortization',0),
   ('ppe_depreciation_excluding_amortization',-1),('selling_expense',0),('selling_expense',-1),
   ('administrative_expense',0),('administrative_expense',-1),('current_liabilities',0),
   ('current_liabilities',-1),('document_reconciled_long_term_debt',0),('document_reconciled_long_term_debt',-1),
   ('income_before_extraordinary_items',0),('operating_cash_flow',0)],
 'Z_SCORE': [('current_assets',0),('current_liabilities',0),('total_assets',0),
   ('retained_earnings',0),('document_reconciled_ebit',0),('total_equity',0),('total_liabilities',0)],
 'EPS_RECOMPUTE': [('eps_adjusted_earnings_numerator',0),('weighted_average_basic_shares',0),
                  ('weighted_average_diluted_shares',0)],
 'PE': [('vendor_basic_eps',0),('share_basis_adjustment_history',0)],
 'PB': [('parent_common_equity',0),('historical_common_shares_outstanding',0),
        ('share_basis_adjustment_history',0)]}
ANNUAL_TASKS['F_SCORE'] = sorted({x for requirements in SIGNALS.values() for x in requirements})
EXTERNAL = {
 'PE': ['COMPATIBLE_EPS_TTM_NOT_ANNUAL_EPS','RAW_PRICE_VND_PER_SHARE_AT_DECISION',
        'COMPATIBLE_PRICE_AND_SHARE_BASIS'],
 'PB': ['EQUITY_AND_SHARE_DATE_ALIGNMENT','RAW_PRICE_VND_PER_SHARE_AT_DECISION',
        'COMPATIBLE_PRICE_AND_SHARE_BASIS']}

def matrix(readiness, symbols, years):
    if readiness.get('financial_features_allowed') is not False:
        raise ValueError('input must not grant features')
    lookup={(r['symbol'],r['year'],r['field']):r for r in readiness['rows']}
    rows=[]
    for symbol in symbols:
        for year in years:
            for task, requirements in ANNUAL_TASKS.items():
                inputs=[]
                for field,offset in requirements:
                    source=lookup.get((symbol,year+offset,field),{})
                    inputs.append(dict(field=field,year=year+offset,
                        evidence_status=source.get('evidence_status','MISSING_SEMANTIC_MAPPING'),
                        evidence_references=source.get('document_evidence',[])))
                verified=sum(x['evidence_status']=='DOCUMENT_VALUE_VERIFIED_PIT_PENDING' for x in inputs)
                blockers=list(EXTERNAL.get(task,[]))+['COMPATIBLE_VINTAGES','PUBLICATION_PIT','HISTORICAL_IDENTITY_AND_SECTOR']
                rows.append(dict(symbol=symbol,year=year,task=task,inputs=inputs,
                    verified_input_cells=verified,required_input_cells=len(inputs),
                    annual_input_presence_complete=verified==len(inputs),semantic_blockers=blockers,
                    task_ready=False,computed_value=None,financial_features_allowed=False))
    return dict(rows=rows,financial_features_allowed=False,financial_pit_gate='NOT_READY',
                meaning='Input preparation only; PE/PB require date-level and TTM evidence beyond annual rows')

def export(readiness_run,config_path,output):
    run=Path(readiness_run).resolve();verify_inventory(run)
    c=json.loads(Path(config_path).read_bytes())
    if c.get('financial_features_allowed') is not False:raise ValueError('config cannot approve features')
    result=matrix(json.loads((run/'readiness.json').read_bytes()),c['symbols'],c['score_target_years'])
    result.update(input_manifest_sha256=digest((run/'manifest.json').read_bytes()),config_sha256=digest(Path(config_path).read_bytes()))
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'task_readiness.json',encoded(result))
    immutable_write(out/'analyzer.py',Path(__file__).read_bytes())
    immutable_write(out/'config.json',Path(config_path).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()}}))
    return result
