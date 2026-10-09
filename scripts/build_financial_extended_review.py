"""Seal additional visual review; reviewed values are never OCR auto-acceptance."""
import argparse, copy, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import encoded,digest,immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory

def build(output):
    out=ROOT/output;out.mkdir(parents=True,exist_ok=False)
    source=ROOT/'data/financial/pilot_readiness_v11';verify_inventory(source)
    rows=json.loads((source/'readiness.json').read_bytes())['rows']
    pubs=json.loads((ROOT/'data/financial/pilot_publication_review_v1/publications.json').read_bytes())['documents']
    docs={p['year']:p for p in pubs if p['symbol']=='FPT'}
    facts=[]
    def add(year,field,value,cache,page,unit='VND',semantics='INSTANT',evidence=None):
        base=next(f for r in rows if r['symbol']=='FPT' and r['year']==year for f in r['document_evidence']
                  if f['pdf_sha256']==docs[year]['pdf_sha256'])
        f=copy.deepcopy(base);image=ROOT/'data/financial'/cache/f'page-{page:02}.png'
        f.update(item=field,value=value,unit=unit,pdf_page=page,image_path=str(image),
            image_sha256=digest(image.read_bytes()),period_semantics=semantics,
            period_start=f'{year}-01-01' if semantics=='ANNUAL' else None,
            period_end=f'{year}-12-31',derivation=evidence,vintage=f'CURRENT_ANNUAL_{year}')
        facts.append(f)
    stems={y:Path(docs[y]['pdf_path']).stem for y in [2023,2024]}
    mains={y:f'fpt_annual_ocr_v1/{stems[y]}' for y in stems}
    mains[2025]='fpt_original_2025_main_ocr_v1/00-FPT-2025'
    notes={y:f'fpt_full_notes_ocr_v1/{stems[y]}' for y in stems}
    notes[2025]='fpt_original_2025_notes_ocr_v1/00-FPT-2025'
    for year,gross,allowance,debt in [(2023,9057647206985,912156645080,208074996962),
        (2024,10537019113380,619531925859,501111537075),(2025,12734600596550,586166744274,1903789988184)]:
        add(year,'gross_short_term_trade_receivables',gross,mains[year],8 if year==2025 else 9)
        add(year,'all_short_term_receivables_allowance',allowance,mains[year],8 if year==2025 else 9,
            evidence={'rule':'ABSOLUTE_REPORTED_ALLOWANCE', 'trade_specific_allocation':'UNKNOWN'})
        add(year,'noncurrent_loans_and_finance_leases',debt,mains[year],10 if year==2025 else 11,
            evidence={'rule':'BALANCE_CODE_338_NONCURRENT_ONLY','current_portion_excluded':True})
    add(2023,'selling_expense',5242551906960,mains[2023],13,semantics='ANNUAL')
    add(2023,'administrative_expense',6625373638359,mains[2023],13,semantics='ANNUAL')
    add(2025,'net_tangible_ppe',15359168484059,notes[2025],44)
    for year,page,value in [(2023,44,1872583701234),(2024,46,2045988798970),(2025,44,2336379408073)]:
        add(year,'tangible_owned_ppe_depreciation_in_year',value,notes[year],page,semantics='ANNUAL',
            evidence={'rule':'OWNED_TANGIBLE_PPE_CURRENT_YEAR_DEPRECIATION','excludes':'leased PPE, intangibles and goodwill'})
    add(2025,'outstanding_common_shares',1703507121,notes[2025],51,'SHARES')
    add(2025,'parent_common_equity',36480193944772,notes[2025],53,
        evidence={'rule':'PARENT_EQUITY_NOTE_PLUS_COMMON_SHARE_NOTE','common_share_note_page':51,
                  'equity_code_410':43745290747539,'nci':7265096802767,
                  'funding_code_430_excluded':2750000000})
    checks=[dict(check='PARENT_COMMON_EQUITY_BRIDGE',passed=43745290747539-7265096802767==36480193944772),
        dict(check='OWNED_PPE_COST_LESS_ACCUMULATED',passed=29122042372002-13762873887943==15359168484059)]
    for f in facts:
        if digest(Path(f['pdf_path']).read_bytes())!=f['pdf_sha256']:raise ValueError('PDF changed')
    immutable_write(out/'facts.json',encoded(dict(facts=facts,checks=checks,financial_features_allowed=False,
        unresolved=['trade-specific allowance allocation','ordinary-income strict reconciliation','leased-asset depreciation scope'])))
    immutable_write(out/'builder.py',Path(__file__).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return dict(facts=len(facts),checks=len(checks))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    print(json.dumps(build(p.parse_args().output)))
