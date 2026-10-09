"""Offline, evidence-pinned scale QA; reference arithmetic never opens a gate."""
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from .financial_batch_flow import verify_pins
from .financial_scale_probe import CLOSED
from ..features.financial_reference import calculate
from ..features.financial_vas_reference import calculate_disclosed_basic_eps
from ..ingestion.cafef_financial import encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside, seal
from ..ingestion.financial_documents import verify_inventory
from ..ingestion.financial_date_pit import next_session
from ..ingestion.financial_ocr_probe import code_cell


def evaluate(document, publication, calendar, decision_date, raw_price=None):
    """Reviewed, homogeneous VAS annual inputs, with separate temporal coverage."""
    if (document['scope']!='CONSOLIDATED' or document['framework']!='VAS'
            or document['unit']!='VND' or document['months']!=12
            or document['period_start']!=f"{document['year']}-01-01"
            or document['period_end']!=f"{document['year']}-12-31"
            or document['company_type']!='Regular'):
        raise ValueError('reviewed calendar-year Regular VAS reference required')
    if any(f.get('review_status')!='VISUALLY_VERIFIED_REFERENCE_ONLY' or not f.get('locator')
           for f in document['facts']):raise ValueError('explicit visual locators required')
    facts={f['field']:Decimal(f['value']) for f in document['facts']}
    if len(facts)!=len(document['facts']) or any(not v.is_finite() for v in facts.values()):
        raise ValueError('duplicate/nonfinite reviewed facts')
    residual=facts['total_assets']-facts['total_liabilities']-facts['total_equity']
    z=None
    if abs(residual)<=Decimal('1') and document['ebit_basis']=='EBT_PLUS_DISCLOSED_EXPENSED_INTEREST_EXCLUDING_ISSUANCE_FEES':
        z=calculate('Z_SCORE',dict(facts,document_reconciled_ebit=facts['profit_before_tax']+facts['interest_expense']))['value']
    eps=calculate_disclosed_basic_eps(facts['eps_numerator'],facts['weighted_basic_shares'],12)
    eps_ok=eps['value'] is not None and eps['rounded']==str(facts['vendor_basic_eps'])
    usable=None;status='EXACT_VINTAGE_PUBLICATION_MISSING'
    if publication is not None:
        if (publication.get('validation_status')!='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED'
                or publication.get('precision')!='DATE_ONLY'
                or publication['pdf_sha256']!=document['pdf_sha256']):
            raise ValueError('publication must identify exact reviewed PDF')
        usable,status=next_session(publication['publication_date'],document['exchange'],calendar)
    eligible=usable is not None and decision_date>=usable
    pe=None
    if eps_ok and Decimal(eps['value'])>0 and raw_price is not None:
        pe=str(Decimal(str(raw_price))/Decimal(eps['value']))
    return dict(symbol=document['symbol'],year=document['year'],balance_residual=str(residual),
        z_reference=z,disclosed_basic_eps_reference=eps if eps_ok else None,eps_rounding_pass=eps_ok,
        pe_annual_arithmetic=pe,pe_ttm=None,pb_current=None,f_full=None,m_full=None,
        date_pit_status=status,usable_from_date=usable,date_eligible_at_snapshot=eligible,
        available_at=None,publication=publication,decision_date=decision_date,
        production_value=None,acceptance='MANUAL_REVIEW_REQUIRED',**CLOSED)


def build(root,config_path,output):
    root=Path(root).resolve();cfg=inside(root,config_path,'configs');c=json.loads(cfg.read_bytes())
    if c['version']!='financial-scale-review-v1' or any(c.get(k) is not False for k in CLOSED):
        raise ValueError('closed reference review required')
    if not 1<=len(c['documents'])<=8:raise ValueError('review cap exceeded')
    verify_pins(root,c['input_pins']);verify_pins(root,c['code_pins'])
    for run in c['sealed_runs']:verify_inventory(inside(root,run,'data'))
    requirements=json.loads(inside(root,c['requirements_path']).read_bytes())
    prices={r['ticker']:r for r in json.loads(inside(root,c['price_excerpt']).read_bytes())}
    calendar=[json.loads(line) for line in inside(root,c['calendar_path']).read_text(encoding='utf8').splitlines()]
    docs=json.loads(inside(root,c['ocr_index']).read_bytes())['documents']
    out=inside(root,output,'data');out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'config.json',cfg.read_bytes());rows=[];qa=[]
    for d in c['documents']:
        ocrdoc=next(x for x in docs if x['symbol']==d['symbol'] and x['year']==d['year'])
        if ocrdoc['pdf_sha256']!=d['pdf_sha256']:raise ValueError('review/ OCR PDF mismatch')
        pages={x['pdf_page']:x for x in ocrdoc['pages']}
        for f in d['facts']:
            ev=pages[f['pdf_page']]
            if c['input_pins'].get(ev['image_path'])!=ev['image_sha256'] or c['input_pins'].get(ev['ocr_path'])!=ev['ocr_sha256']:
                raise ValueError('review image/OCR must be individually pinned')
            spec=f.get('table_profile');ocr=dict(status='NOTE_VISUAL_TRANSCRIPTION_REQUIRED',value=None)
            if spec:
                record=json.loads(inside(root,ev['ocr_path']).read_bytes())
                ocr=code_cell(record,**spec)
            candidates=[r for r in requirements if r['symbol']==d['symbol'] and r['year']==d['year'] and r['field']==f['field']]
            vals=sorted({v for r in candidates for v in r.get('candidate_values',[])})
            match='PROVIDER_FIELD_NOT_AVAILABLE'
            if f.get('provider_semantics')=='COMBINED_INTEREST_AND_ISSUANCE_FEES':match='PROVIDER_SEMANTIC_MISMATCH'
            elif vals:match='MATCH' if len(vals)==1 and Decimal(vals[0])==Decimal(f['value']) else 'NUMERIC_DIFFERENCE_OR_VINTAGE'
            qa.append(dict(symbol=d['symbol'],year=d['year'],field=f['field'],reviewed_value=f['value'],
                provider_values=vals,comparison=match,ocr=ocr,
                ocr_matches_visual=ocr['value'] is not None and Decimal(ocr['value'])==Decimal(f['value']),
                pdf_sha256=d['pdf_sha256'],pdf_page=f['pdf_page'],locator=f['locator'],page_evidence=ev,
                selected_canonical_value=None,**CLOSED))
        p=prices.get(d['symbol']);publication=d.get('publication')
        if publication and publication['evidence_path'] not in c['input_pins']:raise ValueError('publication proof pin missing')
        rows.append(evaluate(d,publication,calendar,c['decision_date'],p['raw_close'] if p else None))
    summary=dict(version=c['version'],symbols=len(rows),numeric_reference_cells=sum(
        (r['z_reference'] is not None)+(r['disclosed_basic_eps_reference'] is not None) for r in rows),
        annual_pe_arithmetic_cells=sum(r['pe_annual_arithmetic'] is not None for r in rows),
        date_covered_symbols=sum(r['date_eligible_at_snapshot'] for r in rows),
        comparison_counts=dict(Counter(r['comparison'] for r in qa)),
        ocr_statement_attempts=sum('table_profile' in f for d in c['documents'] for f in d['facts']),
        ocr_matching_cells=sum(r['ocr_matches_visual'] for r in qa),accepted_canonical_facts=0,**CLOSED)
    immutable_write(out/'references.json',encoded(rows));immutable_write(out/'qa.json',encoded(qa))
    immutable_write(out/'results.json',encoded(summary))
    for path in c['code_pins']:immutable_write(out/'code'/path,inside(root,path).read_bytes())
    seal(out);return summary
