"""Seal explicit exact-page ESOP review, including unresolved accounting fields."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from delta_t1.ingestion.cafef_financial import digest, encoded, immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory
from delta_t1.ingestion.financial_date_pit import next_session
from delta_t1.experiments.financial_ttm_valuation import file_hash


def build(output):
    prior = ROOT / 'data/financial/fpt_valuation_review_v1'
    runs = [prior, *(ROOT / 'data/financial' / x for x in [
        'fpt_events_ocr_v1', 'fpt_esop_evidence_ocr_v2', 'fpt_registration_ocr_v1',
        'fpt_parent_equity_ocr_v1', 'fpt_parent_equity_text_v1'])]
    for run in runs:
        verify_inventory(run)
    old = json.loads((prior / 'review.json').read_bytes())
    policy = json.loads((ROOT / 'configs/data/financial_date_pit_v1.json').read_bytes())
    calendar_path = ROOT / policy['calendar_path']
    if file_hash(calendar_path) != policy['calendar_sha256']:
        raise ValueError('calendar changed')
    calendar = [json.loads(line) for line in calendar_path.read_text(encoding='utf8').splitlines()]
    supplements = 'data/financial/issuer_supplement_v1/'
    event_run = ROOT / supplements / 'run-2026-10-04T102005.134843-0000-df8bfaf5'
    registration_run = ROOT / supplements / 'run-2026-10-04T153532.015435-0000-dea50cc2'
    parent_run = ROOT / supplements / 'run-2026-10-04T153640.297941-0000-af9bcd5c'
    cards_path = ROOT / 'data/financial/fpt_publication_cards_v1/cards.json'
    cards = json.loads(cards_path.read_bytes())['cards']

    def evidence(run, index, folder, page, pub, publication_page):
        verify_inventory(run)
        d = json.loads((run / 'inventory.json').read_bytes())['requests'][index]
        if d['status'] != 'DOWNLOADED' or file_hash(d['path']) != d['sha256']:
            raise ValueError('source PDF changed')
        card = [c for c in cards if c['attachment_url'] == d['url'] and c['publication_date'] == pub]
        if len(card) != 1:
            raise ValueError('exact issuer publication card missing')
        def image(page):
            base = ROOT / 'data/financial' / folder
            paths = list(base.glob(f'page-{page:02}.png')) or list(base.glob(f'page-{page}.png'))
            if len(paths) != 1:
                raise ValueError('page image missing')
            return dict(image_path=str(paths[0]), image_sha256=file_hash(paths[0]), pdf_page=page)
        usable, status = next_session(pub, 'HOSE', calendar)
        if usable is None:
            raise ValueError(status)
        return dict(pdf_path=d['path'], pdf_sha256=d['sha256'], source_url=d['url'],
                    **image(page), publication_evidence=image(publication_page),
                    publication_card=card[0], publication_cards_sha256=file_hash(cards_path),
                    publication_date=pub, usable_from_date=usable, available_at=None,
                    validation_status='VALUE_UNIT_PERIOD_VISUALLY_VERIFIED')

    manager = evidence(event_run, 1, 'fpt_events_ocr_v1/01-FPT-2026', 5, '2026-06-26', 1)
    staff = evidence(event_run, 2, 'fpt_esop_evidence_ocr_v2/02-FPT-2026', 12, '2026-06-26', 1)
    staff_result = evidence(event_run, 2, 'fpt_esop_evidence_ocr_v2/02-FPT-2026', 3, '2026-06-26', 1)
    registration = evidence(registration_run, 0, 'fpt_registration_ocr_v1/00-FPT-2026', 3, '2026-07-17', 2)
    parent_payables = evidence(parent_run, 0, 'fpt_parent_equity_ocr_v1/00-FPT-2026', 30, '2026-08-21', 1)
    parent_capital = evidence(parent_run, 0, 'fpt_parent_equity_ocr_v1/00-FPT-2026', 32, '2026-08-21', 1)
    bank_total = 23020000000 + 85173010000
    snapshot = dict(old['latest_balance'], symbol='FPT')
    event = dict(symbol='FPT', event_id='ESOP_2026', currency='VND', issue_price=10000,
                 before_common_shares=1703507121, new_common_shares=10819301,
                 after_common_shares=1714326422, gross_bank_proceeds=bank_total,
                 bank_confirmation_date='2026-06-25',
                 bank_components=[dict(value=23020000000, common_shares=2302000, evidence=manager),
                                  dict(value=85173010000, common_shares=8517301, evidence=staff)],
                 registered_capital_before=17035071210000,
                 registered_capital_after=17143264220000,
                 registered_capital_increase=108193010000,
                 registration_effective_date='2026-07-16', registration_publication_date='2026-07-17',
                 cash_treatment='BALANCE_CLASSIFICATION_NOT_SEPARATELY_DISCLOSED',
                 verified_advance_liability=None, actual_issuance_fee=None,
                 evidence=[manager, staff, staff_result, registration, parent_payables, parent_capital],
                 historical_common_share_effective_basis='UNRESOLVED_DIFFERENT_EVENT_DATE_TYPES',
                 accounting_discovery=dict(parent_other_payables=143204484997,
                     parent_other_payables_includes_esop=None,
                     parent_reported_capital_at_june30=17035071210000,
                     statement_scope='SEPARATE_PARENT_DISCOVERY_ONLY',
                     consolidated_parent_equity_from_separate_statement_allowed=False))
    checks = [dict(name=name, passed=passed) for name, passed in [
        ('BANK_COMPONENT_SUM', bank_total == 108193010000),
        ('STAFF_PROCEEDS_SHARES_PRICE', 85173010000 == 8517301 * 10000),
        ('MANAGER_PROCEEDS_SHARES_PRICE', 23020000000 == 2302000 * 10000),
        ('COMMON_SHARE_INCREMENT', 1703507121 + 10819301 == 1714326422),
        ('REGISTERED_CAPITAL_INCREMENT', 17143264220000 - 17035071210000 == bank_total),
        ('PRE_BALANCE_CASH_POST_BALANCE_CAPITAL', '2026-06-25' < snapshot['balance_date'] < '2026-07-16'),
        ('UNKNOWN_FEES_AND_CLASSIFICATION_RETAINED', event['actual_issuance_fee'] is None
         and event['verified_advance_liability'] is None)]]
    if not all(c['passed'] for c in checks):
        raise ValueError('accounting checks failed')
    review = dict(snapshot=snapshot, event=event, checks=checks,
                  financial_features_allowed=False, research_ready=False,
                  input_manifest_sha256={str(r): file_hash(r / 'manifest.json') for r in runs},
                  publication_cards_path=str(cards_path), publication_cards_sha256=file_hash(cards_path))
    out = (ROOT / output).resolve()
    if not out.is_relative_to(ROOT / 'data'):
        raise ValueError('review under data only')
    out.mkdir(parents=True, exist_ok=False)
    immutable_write(out / 'review.json', encoded(review))
    immutable_write(out / 'builder.py', Path(__file__).read_bytes())
    immutable_write(out / 'manifest.json', encoded({'files': {p.name: file_hash(p) for p in out.iterdir()}}))
    return dict(output=str(out), checks=len(checks))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    print(json.dumps(build(p.parse_args().output)))
