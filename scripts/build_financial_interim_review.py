"""Pin H1 statement periods, restated comparison and explicit EPS note."""
import json,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import encoded,digest,immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.ingestion.financial_date_pit import next_session
from delta_t1.features.financial_vas_reference import calculate_period_eps

def build(output):
    source=ROOT/'data/financial/fpt_interim_ocr_v1';cards=ROOT/'data/financial/fpt_publication_cards_v1'
    for run in [source,cards]:verify_inventory(run)
    index=json.loads((source/'index.json').read_bytes());doc=index['documents'][0]
    inventory=json.loads((ROOT/index['source_run']/'inventory.json').read_bytes())
    # Pin the issuer attachment and reviewed listing date, not the URL filename.
    pdf=ROOT/doc['pdf_path'];pdf_hash=digest(pdf.read_bytes())
    if pdf_hash!=doc['pdf_sha256']:raise ValueError('PDF changed')
    entries=inventory['requests'] if 'requests' in inventory else inventory['records']
    acquisition=next(e for e in entries if e.get('sha256')==pdf_hash)
    listing=next(c for c in json.loads((cards/'cards.json').read_bytes())['cards']
        if c['attachment_url']==acquisition['url'] and c['publication_date']==doc['publication_date'])
    policy=json.loads((ROOT/'configs/data/financial_date_pit_v1.json').read_bytes());calendar_path=ROOT/policy['calendar_path']
    if digest(calendar_path.read_bytes())!=policy['calendar_sha256']:raise ValueError('calendar changed')
    calendar=[json.loads(l) for l in calendar_path.read_text(encoding='utf8').splitlines()]
    usable,status=next_session(listing['publication_date'],'HOSE',calendar)
    facts=[]
    def evidence(page):
        p=source/'00-FPT-2026'/f'page-{page:02}.png'
        return dict(image_path=str(p),image_sha256=digest(p.read_bytes()),pdf_page=page)
    def add(year,field,value,page,unit='VND',basis='CURRENT_H1_2026'):
        facts.append(dict(symbol='FPT',year=year,item=field,value=value,unit=unit,
            period_start=f'{year}-01-01',period_end=f'{year}-06-30',period_semantics='H1_YTD',
            statement_scope='CONSOLIDATED',accounting_framework='VAS',consolidation_basis=basis,
            framework_evidence=evidence(19),pdf_path=str(pdf),pdf_sha256=pdf_hash,**evidence(page),
            validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',publication=listing,
            usable_from_date=usable,date_pit_status=status,available_at=None,financial_features_allowed=False))
    for field,value in [('net_revenue',26268500667974),('profit_before_tax',5714236316160),
        ('net_profit',5047128933102),('parent_net_profit',5054958601533),('non_controlling_profit',-7829668431)]:
        add(2026,field,value,18)
    for field,value,unit in [('reported_eps_numerator_before_unestimated_reserve',5054958601533,'VND'),
        ('weighted_average_basic_shares',1703507121,'SHARES'),('weighted_average_diluted_shares',1703507121,'SHARES'),
        ('basic_eps',2967,'VND_PER_SHARE')]:add(2026,field,value,56,unit)
    for field,value in [('net_revenue',23325685794923),('profit_before_tax',4837503416147),
        ('net_profit',4427462420799),('parent_net_profit',4431763974648)]:
        add(2025,field,value,18,basis='H1_2025_PRO_FORMA_FTEL_EQUITY_METHOD_AS_DISCLOSED_2026')
    eps=calculate_period_eps(5054958601533,1703507121,1703507121,6)
    if eps['rounded']['basic']!='2967':raise ValueError('EPS note mismatch')
    result=dict(facts=facts,eps_reference=eps,usable_from_date=usable,
        eps_reserve_status='NOT_YET_ESTIMATED_BY_ISSUER_NOT_A_VERIFIED_ZERO',
        dilution_evidence=evidence(57),comparability_evidence=evidence(18),
        latest_ttm=dict(value=None,status='SCOPE_AND_EPS_BASIS_BRIDGE_REQUIRED',
            reasons=['FTEL full consolidation changed to equity method from 2026-01-01',
                'FY2025 full-year same-scope bridge not reviewed',
                'H1 EPS excludes unestimated welfare reserve; FY2025 EPS deducts reserve',
                'No summing reported EPS with differing weighted shares']),
        financial_features_allowed=False,research_ready=False,
        input_manifest_sha256={str(run):digest((run/'manifest.json').read_bytes()) for run in [source,cards]})
    out=ROOT/output;out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'review.json',encoded(result));immutable_write(out/'builder.py',Path(__file__).read_bytes())
    immutable_write(out/'eps_calculator.py',(ROOT/'src/delta_t1/features/financial_vas_reference.py').read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return dict(facts=len(facts),eps=eps['rounded'],usable_from_date=usable)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);print(json.dumps(build(p.parse_args().output)))
