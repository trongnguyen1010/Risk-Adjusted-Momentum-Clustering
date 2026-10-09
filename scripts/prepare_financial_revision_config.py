"""Pin bounded original and revised EPS templates and F-score year PDF identities."""
import json, copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'configs/data/financial_reference_flow_v1.json').read_bytes())
config.update(version='financial-reference-flow-v2',stage='FIN-D3_EPS_REVISION_AND_F_SCORE_REFERENCE',
    readiness_run='data/financial/pilot_readiness_v11',max_decision_dates=6,
    decision_dates=['2025-03-14','2025-03-17','2026-03-19','2026-03-20','2026-08-28'])
revised=copy.deepcopy(config['cases'][1])
revised['year']=2024
revised['cells']=[s for s in revised['cells'] if s['field'] in ['eps_adjusted_earnings_numerator','weighted_average_basic_shares','vendor_basic_eps']]
for spec,box in zip(revised['cells'], [[.76,.385,.95,.41],[.79,.43,.95,.455],[.86,.46,.95,.49]]):
    spec['box']=box
config['cases'][0]['eps_revision_cases']=[revised]
facts=json.loads((ROOT/'data/financial/fpt_note_supplement_v1/facts.json').read_bytes())['facts']
config['f_score_original_pdfs']={str(f['year']):f['pdf_sha256'] for f in facts if f['item']=='long_term_borrowings_including_current_portion'}
out=ROOT/'configs/data/financial_reference_flow_v2.json'
if out.exists():raise FileExistsError(out)
out.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
