import json,unittest
from delta_t1.experiments.financial_history20_probes import tasks,inspect


class FinancialTemplateProbeTests(unittest.TestCase):
    def members(self):
        return [dict(registry_id=f'R{i}',symbol=f'S{i}',provider_partition_id=f'PROVISIONAL:R{i}',status='CURRENT_PROFILE_OBSERVED') for i in range(15)]

    def body(self,symbol='S0',group='TN',code='1'):
        return json.dumps(dict(isSuccess=True,value=dict(templace=[dict(code=group,data=[dict(code=code,name='Asset')])],
            data=[dict(code=group,data=[dict(symbol=symbol,year=2025,quater=4,type='H',time='2025',data=[dict(code=code,value='123')])])]))).encode()

    def test_exact_bound_and_existing_groups(self):
        rows=tasks(self.members());self.assertEqual(len(rows),180)
        self.assertEqual(len({r['id'] for r in rows}),180)
        self.assertEqual({r['mode'] for r in rows},{'NAM','QUY'})
        self.assertTrue(all(r['page']==1 and 'apiweb.cafef.vn/api/' in r['url'] for r in rows))

    def test_duplicate_or_unreviewed_partition_blocks(self):
        rows=self.members();rows[-1]=rows[0]
        with self.assertRaises(ValueError):tasks(rows)
        rows=self.members();rows[0]['status']='PENDING'
        with self.assertRaises(ValueError):tasks(rows)

    def test_probe_preserves_unaccepted_scope_unit_and_json_replay(self):
        row=inspect(self.body(),dict(symbol='S0',statement='CDKT',mode='NAM',group='TN'),'source')
        self.assertEqual(row,json.loads(json.dumps(row)))
        self.assertEqual(row['cell_count'],1);self.assertFalse(row['accepted']);self.assertFalse(row['pit_ready'])
        self.assertEqual(row['scope_status'],'UNRESOLVED')

    def test_issuer_and_group_mismatch_fail_closed(self):
        task=dict(symbol='S0',statement='CDKT',mode='NAM',group='TN')
        for body in [self.body(symbol='OTHER'),self.body(group='NV')]:
            with self.assertRaises(ValueError):inspect(body,task,'source')

    def test_empty_series_remains_distinct_from_successful_numeric_candidate(self):
        body=json.dumps(dict(isSuccess=True,value=dict(templace=[],data=[]))).encode()
        row=inspect(body,dict(symbol='S0',statement='CDKT',mode='NAM',group='TN'),'source')
        self.assertEqual(row['status'],'EMPTY_PROVIDER_SERIES');self.assertEqual(row['cell_count'],0)

    def test_unknown_cell_label_is_counted_without_acceptance(self):
        payload=json.loads(self.body());payload['value']['templace'][0]['data']=[]
        row=inspect(json.dumps(payload).encode(),dict(symbol='S0',statement='CDKT',mode='NAM',group='TN'),'source')
        self.assertEqual(row['unmapped_cells'],1);self.assertFalse(row['accepted'])


if __name__=='__main__':unittest.main()
