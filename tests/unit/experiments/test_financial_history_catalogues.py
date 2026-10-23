import unittest
from pathlib import Path
from unittest.mock import patch
from delta_t1.experiments.financial_history_catalogues import jobs,execute,prepare


class PublicCatalogueTests(unittest.TestCase):
    def assignment(self):return dict(members=[dict(registry_id=f'R{i:02}',symbol=f'S{i}',provider_partition_id=f'PROVISIONAL:R{i}') for i in range(15)])

    def test_exact_bounded_assignment_and_deterministic_routes(self):
        a=self.assignment();result=jobs(a);a['members'].reverse()
        self.assertEqual(result,jobs(a));self.assertEqual(len(result),15)
        self.assertEqual(len({r['id'] for r in result}),15)
        self.assertTrue(all(r['url'].startswith('https://web.stockbiz.vn/Stocks/') and r['url'].endswith('/Downloads.aspx') for r in result))

    def test_duplicate_registry_or_ticker_never_deduplicated_silently(self):
        a=self.assignment();a['members'][-1]['registry_id']=a['members'][0]['registry_id']
        with self.assertRaises(ValueError):jobs(a)
        a=self.assignment();a['members'][-1]['symbol']=a['members'][0]['symbol']
        with self.assertRaises(ValueError):jobs(a)

    def test_invalid_symbol_cannot_change_host_or_path(self):
        for symbol in ['../FPT','FPT?x=1','FPT/Downloads.aspx','lowercase']:
            a=self.assignment();a['members'][0]['symbol']=symbol
            with self.assertRaises(ValueError):jobs(a)

    def test_other_universe_size_requires_separate_contract(self):
        a=self.assignment();a['members'].pop()
        with self.assertRaises(ValueError):jobs(a)

    def test_invalid_wave_fails_before_any_config_or_network(self):
        for count in [-1,16,True]:
            with self.assertRaises(ValueError):execute(Path('.'),'missing.json','run',True,count)

    def test_acceptance_flags_and_source_allowlist_fail_before_preparing_jobs(self):
        base=dict(version='financial-history-catalogues-v1',approved_hosts=['web.stockbiz.vn'],network_concurrency=1,max_campaign_days=90,
                  numeric_acceptance_allowed=False,publication_acceptance_allowed=False,research_ready=False)
        for key in ['numeric_acceptance_allowed','publication_acceptance_allowed','research_ready']:
            c=dict(base);c[key]=True
            with patch('delta_t1.experiments.financial_history_catalogues.read',return_value=c):
                with self.assertRaises(ValueError):prepare(Path.cwd(),'config.json')
        c=dict(base,approved_hosts=['cafef.vn'])
        with patch('delta_t1.experiments.financial_history_catalogues.read',return_value=c):
            with self.assertRaises(ValueError):prepare(Path.cwd(),'config.json')


if __name__=='__main__':unittest.main()
