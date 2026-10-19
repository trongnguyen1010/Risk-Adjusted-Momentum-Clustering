import copy
import json
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path

from delta_t1.experiments.financial_provider_validation import (
    SYMBOLS, jobs, reference_decisions, tcbs_candidates, validate_config, acquire, probe_ssi, digest)
from delta_t1.experiments.financial_cafef_pilot import PilotTransport
from delta_t1.ingestion.financial_compact_trial import read_compact
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[3]


def fact():
    return dict(id='BRC:debt:2025',symbol='BRC',field='debt',year=2025,value='24141566184',
                unit='VND',framework='VAS',scope='ISSUER_NO_SUBSIDIARIES',
                review_status='REVIEWED_REFERENCE_ONLY',provenance=dict(pdf_path='reviewed.pdf',pdf_page=7))


def comparison(observed='1175123567', status='MAPPING_OR_VINTAGE_CONFLICT'):
    return dict(reference_id='BRC:debt:2025',symbol='BRC',field='debt',year='2025',
                expected='24141566184',observed=observed,status=status,raw_code='320')


class SelectionTests(unittest.TestCase):
    def test_brc_shift_uses_reviewed_pdf_without_mutating_api(self):
        raw = comparison(); before = copy.deepcopy(raw)
        selected, decisions = reference_decisions([fact()], [raw])
        self.assertEqual(raw, before)
        self.assertEqual(selected[0]['value'], '24141566184')
        self.assertEqual(decisions[0]['decision'], 'QUARANTINE_API_USE_REVIEWED_PDF')
        self.assertFalse(selected[0]['canonical_accepted'])

    def test_match_corroborates_but_does_not_promote_provider(self):
        selected, decisions = reference_decisions([fact()], [comparison('24141566184', 'MATCH')])
        self.assertEqual(decisions[0]['decision'], 'PDF_CORROBORATED_BY_API')
        self.assertEqual(selected[0]['selected_source'], 'PINNED_REVIEWED_PDF_REFERENCE')

    def test_wrong_identity_stale_expected_and_false_match_rejected(self):
        for change in [dict(symbol='VNM'),dict(expected='0'),dict(status='MATCH')]:
            row = dict(comparison(), **change)
            with self.assertRaises(ValueError): reference_decisions([fact()], [row])

    def test_pdf_without_review_or_wrong_framework_rejected(self):
        for change in [dict(review_status='OCR_CANDIDATE'),dict(provenance={}),dict(framework='IFRS'),
                       dict(scope='STANDALONE'),dict(value='NaN')]:
            with self.assertRaises(ValueError): reference_decisions([dict(fact(), **change)], [])

    def test_missing_api_retains_reviewed_reference_and_no_zero_filling(self):
        selected, _ = reference_decisions([fact()], [])
        self.assertEqual(selected[0]['selection_reason'], 'PDF_NOTE_OR_DERIVED_REFERENCE')
        self.assertEqual(len(selected), 1)
        self.assertEqual(reference_decisions([], []), ([], []))


class ProviderTests(unittest.TestCase):
    def test_plan_is_30_jobs_only_15_observed_routes_enabled(self):
        tasks = jobs()
        self.assertEqual(len(tasks), 30)
        self.assertEqual({x['symbol'] for x in tasks}, set(SYMBOLS))
        self.assertEqual(sum(x['url'] is not None for x in tasks), 15)
        self.assertTrue(all(x['url'] is None for x in tasks if x['provider']=='SSI'))

    def test_raw_magnitude_never_infers_unit_or_scope(self):
        row = tcbs_candidates(json.dumps([dict(ticker='BRC',year=2025,quarter=0,asset=125.7)]), jobs()[0])[0]
        self.assertEqual(row['numeric_value'], '125.7')
        self.assertEqual(row['unit_status'], 'UNVERIFIED_NO_MULTIPLIER_INFERRED')
        self.assertFalse(row['canonical_accepted'])

    def test_identity_duplicates_and_nonfinite_rejected(self):
        bad = [dict(ticker='VNM',year=2025,asset=1)]
        duplicate = [dict(ticker='BRC',year=2025,asset=1)] * 2
        for body in [json.dumps(bad),json.dumps(duplicate),'[{"ticker":"BRC","year":2025,"asset":NaN}]']:
            with self.assertRaises(ValueError): tcbs_candidates(body, jobs()[0])

    def test_frozen_caps_and_closed_gates(self):
        config = json.loads((ROOT/'configs/data/financial_provider_validation_v1.json').read_bytes())
        validate_config(config)
        for key in ['research_ready','financial_cluster_allowed']:
            with self.assertRaises(ValueError): validate_config(dict(config, **{key:True}))
        config['budgets']['max_attempts_per_request'] = 2
        with self.assertRaises(ValueError): validate_config(config)

    def test_403_latches_new_campaign_and_resume_does_not_reset_it(self):
        config = json.loads((ROOT/'configs/data/financial_provider_validation_v1.json').read_bytes())
        calls = []
        class Opener:
            def open(self, request, timeout):
                calls.append(request.full_url)
                raise HTTPError(request.full_url,403,'blocked',None,None)
        def transport(root, output, cfg):
            return PilotTransport(root,output,cfg,opener=Opener(),sleep=lambda _:None)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            acquire(root,config,transport_class=transport)
            before=(root/config['output_root']/'network/transport.jsonl').read_bytes()
            acquire(root,config,transport_class=transport)
            self.assertEqual(before,(root/config['output_root']/'network/transport.jsonl').read_bytes())
            state = read_compact(root/config['output_root']/'network')['state']
            self.assertTrue(state['boundary'])
            self.assertEqual(state['transport_attempts'], 1)
            self.assertEqual(len(calls), 1)

    def test_ssi_rejects_unpinned_package_before_transport(self):
        config = json.loads((ROOT/'configs/data/financial_provider_validation_v1.json').read_bytes())
        with tempfile.TemporaryDirectory() as folder:
            wheel=Path(folder)/config['output_root']/'discovery/vietfin-0.2.0-py3-none-any.whl'
            wheel.parent.mkdir(parents=True);wheel.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'wheel pin'):
                probe_ssi(Path(folder),config,transport_class=lambda *args: self.fail('transport before pin check'))

    def test_ssi_boundary_never_retries_or_sends_placeholder_headers(self):
        config = json.loads((ROOT/'configs/data/financial_provider_validation_v1.json').read_bytes())
        calls=[]
        class Opener:
            def open(self, request, timeout):
                calls.append(request)
                self_headers={key.lower():value for key,value in request.header_items()}
                if any(key.startswith('x-fiin') for key in self_headers):
                    raise AssertionError('placeholder headers sent')
                raise HTTPError(request.full_url,403,'blocked',None,None)
        def transport(root, output, cfg):
            return PilotTransport(root,output,cfg,opener=Opener(),sleep=lambda _:None)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            wheel=root/config['output_root']/'discovery/vietfin-0.2.0-py3-none-any.whl'
            wheel.parent.mkdir(parents=True)
            with zipfile.ZipFile(wheel,'w') as pack:
                pack.writestr('vietfin/providers/ssi/utils/equity_search.py',
                    'https://fiin-core.ssi.com.vn/Master/GetListOrganization?language=vi')
                pack.writestr('vietfin/providers/ssi/utils/equity_fundamental_income.py',
                    'https://fiin-fundamental.ssi.com.vn/FinancialStatement/')
            body=wheel.read_bytes()
            expected='ae1fb8418a09c2afbbe3f7b957b49e13cb9f826e94b856666c56cb5d83505fa4'
            with patch('delta_t1.experiments.financial_provider_validation.digest',
                       side_effect=lambda data: expected if data==body else digest(data)):
                first=probe_ssi(root,config,transport_class=transport)
                second=probe_ssi(root,config,transport_class=transport)
            self.assertEqual(len(calls),1)
            self.assertTrue(first['counters']['boundary'])
            self.assertEqual(second['status'],'SSI_TERMINAL_CACHE_NO_NETWORK')
