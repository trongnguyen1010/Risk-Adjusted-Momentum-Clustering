import unittest
from delta_t1.experiments.financial_history_batch_audit import select_issuers


class BatchAuditSelectionTests(unittest.TestCase):
    def profiles(self):
        return [dict(symbol=f'S{i}',registry_id=f'R{i}',exchange=e,proposed_company_type='Regular') for i,e in enumerate(['HOSE','HNX','UPCOM']*3)]

    def test_each_exchange_and_permutation_invariance(self):
        rows=self.profiles();a=select_issuers(rows,[],'seed')
        self.assertEqual(a,select_issuers(rows[::-1],[],'seed'));self.assertEqual({r['exchange'] for r in a},{'HOSE','HNX','UPCOM'})

    def test_already_reviewed_issuer_and_unsupported_template_are_not_pass_samples(self):
        rows=self.profiles();rows[0]['proposed_company_type']='Bank'
        a=select_issuers(rows,['S1'],'seed');self.assertNotIn('S0',[r['symbol'] for r in a]);self.assertNotIn('S1',[r['symbol'] for r in a])

    def test_empty_stratum_is_not_filled_from_other_exchange(self):
        with self.assertRaises(ValueError):select_issuers([r for r in self.profiles() if r['exchange']!='UPCOM'],[],'seed')

    def test_duplicate_ticker_is_identity_ambiguity(self):
        rows=self.profiles();rows[1]['symbol']=rows[0]['symbol']
        with self.assertRaises(ValueError):select_issuers(rows,[],'seed')


if __name__=='__main__':unittest.main()
