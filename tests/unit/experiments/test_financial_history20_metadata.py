import unittest
from delta_t1.experiments.financial_history20_metadata import select_members


class History20MetadataTests(unittest.TestCase):
    def fixture(self):
        controls=['C0','C1','C2','C3','C4'];rows=[];legacy=[]
        for symbol in controls:rows.append(dict(ticker=symbol,exchange='HOSE',registry_id='CONTROL'+symbol,legacy_security_id='KBS:HOSE:'+symbol))
        quotas=[dict(exchange='HOSE',proposed_company_type='Bank',count=2),dict(exchange='HNX',proposed_company_type='Securities',count=1),dict(exchange='HNX',proposed_company_type='Regular',count=3),dict(exchange='UPCOM',proposed_company_type='Regular',count=3),dict(exchange='HOSE',proposed_company_type='Regular',count=6)]
        i=0
        for quota in quotas:
            for _ in range(quota['count']):
                i+=1;symbol='X'+str(i);exchange=quota['exchange'];sid='KBS:'+exchange+':'+symbol
                rows.append(dict(ticker=symbol,exchange=exchange,registry_id=f'REG{i:03}',legacy_security_id=sid,company_name='Public company',issuer_id='',security_id='',identity_status='PROVISIONAL_CURRENT_DISCOVERY_ONLY'))
                legacy.append(dict(ticker=symbol,exchange=exchange,security_id=sid,proposed_company_type=quota['proposed_company_type']))
        return rows,legacy,quotas,controls

    def test_deterministic_strata_and_provisional_identity(self):
        rows,legacy,quotas,controls=self.fixture();first=select_members(rows,legacy,quotas,controls)
        self.assertEqual(first,select_members(rows[::-1],legacy[::-1],quotas,controls))
        self.assertEqual(len(first),15);self.assertEqual(len({r['exchange'] for r in first}),3)
        self.assertTrue(all(r['security_id']=='' and r['issuer_id']=='' for r in first))
        self.assertTrue(all(r['provider_partition_id'].startswith('PROVISIONAL:') for r in first))
        self.assertTrue(all(r['target_start']=='2013-01-01' and r['target_end']=='2025-12-31' and r['auxiliary_balance_year']==2012 for r in first))

    def test_matching_ticker_without_legacy_identity_is_insufficient(self):
        rows,legacy,quotas,controls=self.fixture();rows[-1]['legacy_security_id']='UNRELATED'
        with self.assertRaises(ValueError):select_members(rows,legacy,quotas,controls)

    def test_ambiguous_registry_row_not_deduplicated_by_ticker(self):
        rows,legacy,quotas,controls=self.fixture();rows.append(dict(rows[-1],registry_id='ANOTHER'))
        with self.assertRaises(ValueError):select_members(rows,legacy,quotas,controls)

    def test_insufficient_stratum_not_filled_with_other_categories(self):
        rows,legacy,quotas,controls=self.fixture();legacy[0]['proposed_company_type']='Regular'
        with self.assertRaises(ValueError):select_members(rows,legacy,quotas,controls)

    def test_classification_still_requires_profile_and_api_evidence(self):
        result=select_members(*self.fixture())
        self.assertEqual({r['classification_status'] for r in result},{'LEGACY_PROPOSAL_PROFILE_AND_API_CHECK_REQUIRED'})

    def test_ambiguous_controls_block_plan(self):
        rows,legacy,quotas,controls=self.fixture();rows.append(dict(rows[0]))
        with self.assertRaises(ValueError):select_members(rows,legacy,quotas,controls)


if __name__=='__main__':unittest.main()
