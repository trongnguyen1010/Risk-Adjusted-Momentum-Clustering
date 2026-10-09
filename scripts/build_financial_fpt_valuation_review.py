"""Seal exact-PDF FPT EPS/share-event review; value transcription remains explicit."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.ingestion.financial_date_pit import next_session


def build(output):
    indexes = ['fpt_valuation_text_v1', 'fpt_valuation_history_text_v1']
    ocr_runs = ['fpt_events_ocr_v1', 'fpt_policy_ocr_v1', 'fpt_history_events_ocr_v1',
        'fpt_history_notes_ocr_v1', 'fpt_history_eps_ocr_v1', 'fpt_history_publication_ocr_v1',
        'fpt_interim_ocr_v1', 'fpt_original_2025_notes_ocr_v1', 'fpt_original_2025_main_ocr_v1']
    runs = [ROOT/'data/financial'/s for s in indexes + ocr_runs]
    for run in runs: verify_inventory(run)
    docs = {name: json.loads((ROOT/'data/financial'/name/'index.json').read_bytes())['documents']
            for name in indexes}
    current = ROOT/'data/financial/issuer_supplement_v1/run-2026-10-03T152611.162837-0000-4c13f702/00-FPT-2026.pdf'
    annual = ROOT/'data/financial/issuer_supplement_v1/run-2026-10-03T045409.716988-0000-516cea03/00-FPT-2025.pdf'
    annual_hash = '630f61f6ef9f07d5c593c3bf8f65bad1d56ecbb091921296ed5c4e830ea070a4'
    current_hash = '45636554f28c7e6c2f38458b9a22410ed1f67e80627d672b827019a67f299df8'
    def source(pdf, sha, folder, page, publication_date, publication_page=None, publication_folder=None):
        pdf = Path(pdf)
        if digest(pdf.read_bytes()) != sha: raise ValueError('PDF changed')
        def image_evidence(folder, page):
            directory=ROOT/'data/financial'/folder
            paths = list(directory.glob(f'page-{page:02}.png')) or list(directory.glob(f'page-{page}.png'))
            if len(paths)!=1: raise ValueError('exact page image missing')
            p=paths[0]
            return dict(image_path=str(p),image_sha256=digest(p.read_bytes()),pdf_page=page)
        evidence=image_evidence(folder,page)
        publication_evidence=image_evidence(publication_folder or folder, publication_page or page)
        usable,status=next_session(publication_date,'HOSE',calendar)
        if not usable: raise ValueError(status)
        return dict(pdf_path=str(pdf),pdf_sha256=sha,**evidence,
            publication_date=publication_date,publication_evidence=publication_evidence,
            usable_from_date=usable,date_pit_status=status,available_at=None,
            validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED',financial_features_allowed=False)
    policy=json.loads((ROOT/'configs/data/financial_date_pit_v1.json').read_bytes())
    cp=ROOT/policy['calendar_path']
    if digest(cp.read_bytes())!=policy['calendar_sha256']: raise ValueError('calendar changed')
    calendar=[json.loads(l) for l in cp.read_text(encoding='utf8').splitlines()]
    def new(index, i, folder, page, pub):
        d=docs[index][i]
        return source(d['pdf_path'],d['pdf_sha256'],folder,page,pub)
    annual_e=source(annual,annual_hash,'fpt_original_2025_notes_ocr_v1/00-FPT-2025',55,'2026-03-19',
        1,'fpt_original_2025_main_ocr_v1/00-FPT-2025')
    h1_e=source(current,current_hash,'fpt_interim_ocr_v1/00-FPT-2026',56,'2026-08-21',1)
    prior_doc=docs['fpt_valuation_history_text_v1'][0]
    prior_e=source(prior_doc['pdf_path'],prior_doc['pdf_sha256'],'fpt_history_notes_ocr_v1/00-FPT-2025',
        55,'2025-08-20',1,'fpt_history_publication_ocr_v1/00-FPT-2025')
    def period(start,end,profit,numerator,weighted,deduction,**e):
        return dict(symbol='FPT',period_start=start,period_end=end,parent_profit=profit,
            reported_eps_numerator=numerator,weighted_basic_shares=weighted,
            reported_deduction=deduction,numerator_unit='VND',share_unit='SHARES',
            deduction_policy='ACTUAL_REPORTED_DEDUCTION' if deduction is not None else 'NOT_ESTIMATED_NOT_DEDUCTED',
            statement_scope='CONSOLIDATED',accounting_framework='VAS',
            share_basis_id='FPT_COMMON_INCLUDING_2025_BONUS_222176999',**e)
    periods=dict(
        fy=period('2025-01-01','2025-12-31',9376127629501,8865959921832,1699740091,510167707669,**annual_e),
        current_ytd=period('2026-01-01','2026-06-30',5054958601533,5054958601533,1703507121,None,**h1_e),
        prior_ytd=period('2025-01-01','2025-06-30',4431763974648,4431763974648,1695910625,None,**prior_e))
    scope=new('fpt_valuation_text_v1',4,'fpt_events_ocr_v1/04-FPT-2026',2,'2026-03-18')
    comparison=source(current,current_hash,'fpt_interim_ocr_v1/00-FPT-2026',18,'2026-08-21',1)
    scope_bridge=dict(parent_earnings_unchanged=True,h1_parent_profit_comparison_equal=True,
        comparable_fields=['parent_profit','reported_eps_numerator'],
        total_consolidated_profit_or_revenue_bridge_approved=False,
        usable_from_date=max(scope['usable_from_date'],comparison['usable_from_date']),
        prior_h1_original_parent_profit=4431763974648,current_pdf_prior_h1_parent_profit=4431763974648,
        issuer_statement=scope,numeric_comparison=comparison)
    snapshot=dict(symbol='FPT',exchange='HOSE',balance_date='2025-12-31',common_shares=1703507121,
        **source(annual,annual_hash,'fpt_original_2025_notes_ocr_v1/00-FPT-2025',51,'2026-03-19',
            1,'fpt_original_2025_main_ocr_v1/00-FPT-2025'))
    common=dict(symbol='FPT',exchange='HOSE',validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED')
    corrected=new('fpt_valuation_history_text_v1',3,'fpt_history_events_ocr_v1/03-FPT-2025',3,'2025-05-12')
    bonus=new('fpt_valuation_history_text_v1',1,'fpt_history_events_ocr_v1/01-FPT-2025',1,'2025-07-25')
    esop_notice=new('fpt_valuation_text_v1',0,'fpt_events_ocr_v1/00-FPT-2026',2,'2026-06-26')
    esop_result=new('fpt_valuation_text_v1',1,'fpt_events_ocr_v1/01-FPT-2026',3,'2026-06-26')
    capital=new('fpt_valuation_text_v1',3,'fpt_events_ocr_v1/03-FPT-2026',3,'2026-07-10')
    after=source(current,current_hash,'fpt_interim_ocr_v1/00-FPT-2026',61,'2026-08-21',1)
    cash=new('fpt_valuation_text_v1',5,'fpt_policy_ocr_v1/05-FPT-2026',3,'2026-05-19')
    plan=new('fpt_valuation_text_v1',8,'fpt_policy_ocr_v1/08-FPT-2026',3,'2026-07-31')
    events=[
        dict(common,event_id='ESOP_2025_CORRECTED',event_type='ACTUAL_COMMON_ISSUANCE',
            publication_date='2025-05-12',effective_not_before='2025-05-09',effective_not_after='2025-06-30',
            before_common_shares=1471069183,new_shares=10260939,after_common_shares=1481330122,
            correction='Issuer typing-error amendment; retain original notice, never backfill correction',evidence=[corrected]),
        dict(common,event_id='BONUS_2025',event_type='ACTUAL_COMMON_ISSUANCE',
            publication_date='2025-08-20',effective_not_before='2025-07-22',effective_not_after='2025-07-28',
            before_common_shares=1481330122,new_shares=222176999,after_common_shares=1703507121,
            share_basis_adjustment='Disclosed additive 222176999 adjustment to prior weighted shares; not inferred factor',
            evidence=[bonus,prior_e]),
        dict(common,event_id='ESOP_2026',event_type='ACTUAL_COMMON_ISSUANCE',
            publication_date='2026-08-21',known_notice_publication_date='2026-06-26',
            effective_not_before='2026-06-24',effective_not_after='2026-07-16',
            before_common_shares=1703507121,new_shares=10819301,after_common_shares=1714326422,
            effective_dates=dict(issuance_result='2026-06-24',capital_resolution='2026-07-03',reviewed_subsequent_event='2026-07-16'),
            evidence=[esop_notice,esop_result,capital,after]),
        dict(common,event_id='CASH_DIVIDEND_2026',event_type='CASH_DIVIDEND',publication_date='2026-05-19',
            record_date='2026-05-29',payment_date='2026-06-10',cash_per_share=1000,
            balance_reflection='Included in H1 parent-equity rollforward; do not deduct again',evidence=[cash]),
        dict(common,event_id='BONUS_2026_PLAN',event_type='APPROVED_PLAN',publication_date='2026-07-31',
            ratio='0.10',actual_new_shares=None,effective_not_before=None,effective_not_after=None,
            evidence=[plan,after])]
    equity_e=source(current,current_hash,'fpt_interim_ocr_v1/00-FPT-2026',50,'2026-08-21',1)
    balance=dict(balance_date='2026-06-30',parent_equity=39851463524930,
        noncontrolling_equity=1144217283327,total_equity=40995680808257,
        reported_common_shares=1703507121,parent_equity_basis='TT99_REPORTED_PARENT_EQUITY_ALL_COMMON_CAPITAL',
        cash_dividend_already_reflected=1703507121000,
        capital_reclassification=381750000000,
        capital_reclassification_effect_on_total_parent_equity=0,
        reclassification_is_esop_cash_proceeds=False,evidence=equity_e,
        share_note=source(current,current_hash,'fpt_interim_ocr_v1/00-FPT-2026',51,'2026-08-21',1))
    checks=[dict(name='FY_EPS_NUMERATOR',passed=9376127629501-510167707669==8865959921832),
        dict(name='2025_BONUS_WEIGHTED_SHARE_BRIDGE',passed=1473733626+222176999==1695910625),
        dict(name='2025_COMMON_SHARE_ROLLFORWARD',passed=1471069183+10260939+222176999==1703507121),
        dict(name='2026_COMMON_SHARE_ROLLFORWARD',passed=1703507121+10819301==1714326422),
        dict(name='H1_PARENT_PLUS_NCI_EQUITY',passed=39851463524930+1144217283327==40995680808257),
        dict(name='H1_PARENT_EQUITY_ROLLFORWARD',passed=36482943944772+5054958601533+83457993017-1703507121000-66389893392==39851463524930)]
    if not all(x['passed'] for x in checks):raise ValueError('reviewed bridge failed')
    review=dict(periods=periods,scope_bridge=scope_bridge,initial_share_snapshot=snapshot,
        share_events=events,latest_balance=balance,checks=checks,
        limitations=['Disclosure/charter/accounting dates differ; no historical acceptance inside unresolved interval',
            'Event ledger is bounded issuer evidence, not exhaustive exchange/registrar coverage',
            'Latest reported equity is a June snapshot; post-June proceeds/fees bridge not finalized',
            'Unestimated interim reserve and period allocation prohibit normalized TTM EPS claim'],
        financial_features_allowed=False,research_ready=False,
        input_manifest_sha256={str(r):digest((r/'manifest.json').read_bytes()) for r in runs})
    out=ROOT/output
    if not out.resolve().is_relative_to(ROOT/'data'):raise ValueError('review output under data only')
    out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'review.json',encoded(review));immutable_write(out/'builder.py',Path(__file__).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return dict(output=str(out),checks=len(checks),share_events=len(events))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True)
    print(json.dumps(build(p.parse_args().output)))
