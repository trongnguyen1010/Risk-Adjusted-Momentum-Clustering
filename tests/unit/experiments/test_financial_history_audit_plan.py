import unittest
from delta_t1.experiments.financial_history_audit_plan import choose_samples,FIELDS,CHECKS


class HistoryAuditPlanTests(unittest.TestCase):
    def fixture(self):
        rows=[];checks=[]
        for symbol in ['AAA','BBB','CCC','DDD','EEE']:
            for year in [2014,2018,2024]:
                for mode,q in [('NAM',0),('QUY',3)]:
                    key=[symbol,year,q,mode,'H']
                    for i,field in enumerate(sorted(FIELDS)):
                        statement='LCTT' if field=='operating_cash_flow' else 'KQKD' if field in ['net_revenue','gross_profit','cost_of_goods_sold'] else 'CDKT'
                        rows.append(dict(symbol=symbol,year=year,quarter=q,mode=mode,provider_type='H',field=field,statement=statement,
                                         source_path=symbol+str(year)+mode,source_sha256='source',template_sha256='template'))
                    checks.extend(dict(period=key,check=name,status='RAW_EQUALITY') for name in CHECKS)
        return rows,checks

    def test_deterministic_sample_independent_of_order(self):
        rows,checks=self.fixture();symbols=['AAA','BBB','CCC','DDD','EEE']
        first,n=choose_samples(rows,checks,[],symbols,'frozen-seed')
        second,n2=choose_samples(rows[::-1],checks[::-1],[],symbols[::-1],'frozen-seed')
        self.assertEqual(first,second);self.assertEqual(n,n2)
        self.assertEqual(len(first),6);self.assertEqual(len({r['symbol'] for r in first}),3)
        self.assertTrue(all(r['preferred_era_present'] for r in first))

    def test_arithmetic_pass_never_means_document_audit_pass(self):
        rows,checks=self.fixture();samples,_=choose_samples(rows,checks,[],['AAA'],'seed')
        self.assertEqual({r['status'] for r in samples},{'INDEPENDENT_DOCUMENT_REVIEW_PENDING'})

    def test_known_displacement_and_failed_accounting_excluded(self):
        rows,checks=self.fixture();checks=[dict(r,status='RAW_DIFFERENCE') if r['period'][0]=='AAA' and r['period'][1]==2018 else r for r in checks]
        samples,_=choose_samples(rows,checks,[dict(symbol='AAA',year=2014)],['AAA'],'seed')
        self.assertNotEqual(next(r for r in samples if r['mode']=='NAM')['year'],2014)
        self.assertTrue(all(r.get('year')!=2018 for r in samples))

    def test_missing_coverage_not_hidden_by_sampler(self):
        samples,n=choose_samples([],[],[],['AAA'],'seed')
        self.assertEqual(n,0);self.assertEqual(len(samples),2)
        self.assertTrue(all(r['status']=='NO_ARITHMETIC_CLEAN_COHORT' for r in samples))


if __name__=='__main__':unittest.main()
