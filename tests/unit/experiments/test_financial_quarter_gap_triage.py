import importlib.util
import unittest
import csv
import io
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('quarter_triage', Path(__file__).resolve().parents[3] / 'scripts/financial_quarter_gap_triage_v2.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QuarterTriageTests(unittest.TestCase):
    def rows(self, provider='HS'):
        return [dict(provider_type=provider, quarter=q, statement=s, group=g, numeric_cells=1) for q in range(1, 5) for s, g in module.NEEDED]

    def test_complete_headers_never_accept_annual_conversion(self):
        result = module.partition_coverage(self.rows())
        self.assertEqual(result['four_quarters_same_provider_tokens'], ['HS'])
        self.assertFalse(result['annual_conversion_accepted'])

    def test_mixed_provider_tokens_cannot_complete_a_partition(self):
        rows = self.rows()
        rows[0]['provider_type'] = 'K'
        self.assertEqual(module.partition_coverage(rows)['four_quarters_same_provider_tokens'], [])

    def test_blank_provider_and_empty_headers_not_evidence(self):
        self.assertEqual(module.partition_coverage(self.rows(None))['q4_same_provider_tokens'], [])
        rows = self.rows()
        for r in rows:
            if r['group'] == 'HDKD':
                r['numeric_cells'] = 0
        self.assertEqual(module.partition_coverage(rows)['q4_same_provider_tokens'], [])

    def test_missing_balance_sheet_half_cannot_pass(self):
        rows = [r for r in self.rows() if r['group'] != 'NV']
        self.assertEqual(module.partition_coverage(rows)['q4_same_provider_tokens'], [])

    def test_replay_seals_traceable_headers_and_rejects_tampering(self):
        repo = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def write(path, body):
                p = root / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(body)
                return module.digest(body)
            def js(path, value):
                return write(path, module.encoded(value))
            def manifest(path, products):
                m = {n: write(path + '/' + n, body) for n, body in products.items()}
                return dict(path=path, manifest_sha256=js(path + '/manifest.json', m))
            for path in ['scripts/financial_quarter_gap_triage_v2.py', 'src/delta_t1/experiments/financial_annual_gap_audit.py', 'src/delta_t1/experiments/financial_api_input_review.py', 'src/delta_t1/experiments/financial_history_documents.py', 'src/delta_t1/ingestion/cafef_financial.py', 'src/delta_t1/ingestion/cafef_financial_deep.py', 'src/delta_t1/ingestion/financial_batch_evidence.py']:
                write(path, (repo / path).read_bytes())
            f = io.StringIO(newline='')
            w = csv.DictWriter(f, fieldnames=['registry_id', 'after_periods', 'missing_years'])
            w.writeheader()
            w.writerow(dict(registry_id='RID1', after_periods=9, missing_years='[2020]'))
            baseline = manifest('baseline', {'coverage-by-symbol.csv': f.getvalue().encode()})
            audit = manifest('audit', {'target-audit.json': module.encoded([dict(registry_id='RID1', symbol='AAA', year=2020, position='BETWEEN_OBSERVED_ANNUAL_YEARS')])})
            pins = {}
            for statement, groups in module.GROUPS.items():
                periods = [dict(symbol='AAA', year=2020, quater=q, type='HS', time='2020', data=[dict(code='X', value=1)]) for q in range(1, 5)]
                data = periods if statement == 'KQKD' else [dict(code=g, data=periods) for g in groups]
                rawpath = 'raw/' + statement + '.json'
                sha = js(rawpath, dict(isSuccess=True, value=dict(data=data)))
                pins[rawpath] = sha
                for group in groups:
                    # Older quarters are beyond page five: regression for the first audit.
                    for page in [7]:
                        url = module.report_url('AAA', statement, 'QUY', group, page)
                        path = 'cache/receipts/' + module.digest(url.encode()) + '.json'
                        record = dict(path=rawpath, sha256=sha)
                        pins[path] = js(path, dict(task=dict(symbol='AAA', mode='QUY', statement=statement, group=group, page=page, url=url), record=record, status='ACQUIRED' if record else 'NOT_REQUIRED_AFTER_SERIES_STOP'))
            pinsha = js('symbol/input-pins.json', dict(sources=pins))
            symsha = js('symbol/manifest.json', {'input-pins.json': pinsha})
            qa = manifest('qa', {'symbol-manifests.json': module.encoded({'RID1': dict(path='symbol/manifest.json', sha256=symsha)})})
            config = dict(version=module.VERSION, network_allowed=False, pdf_download_allowed=False, annual_conversion_allowed=False, research_promotion_allowed=False, baseline=baseline, audit=audit, qa=qa, output_root='output', report_root='report')
            js('config.json', config)
            result = module.run(root, 'config.json')
            summary = json.loads((root / result['path'] / 'summary.json').read_bytes())
            self.assertEqual(summary['targets'], 1)
            self.assertEqual(summary['four_quarters_same_provider_cases'], 1)
            self.assertEqual(summary['recovered_rows'], 0)
            self.assertFalse(summary['annual_conversion_accepted'])
            sealed = (root / 'report/result-ref.json').read_bytes()
            write('raw/CDKT.json', b'{}')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                module.run(root, 'config.json')
            self.assertEqual((root / 'report/result-ref.json').read_bytes(), sealed)
