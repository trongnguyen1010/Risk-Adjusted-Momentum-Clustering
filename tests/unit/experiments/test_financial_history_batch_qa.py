import copy,unittest
from delta_t1.experiments.financial_history_batch_qa import diagnose


class HistoryBatchQATests(unittest.TestCase):
    def row(self,code,label,value,group='TN',statement='CDKT',mode='NAM',quarter=0,year=2025,ptype='HK',mapping='UNIQUE_CODE_LABEL_CANDIDATE'):
        return dict(symbol='X',year=year,quarter=quarter,mode=mode,statement=statement,group=group,raw_code=code,label=label,
            value=None if value is None else str(value),value_status='MISSING' if value is None else 'NUMERIC_CANDIDATE',mapping_status=mapping,
            source_path='raw.json',source_sha256='sha',template_sha256='template',provider_type=ptype,raw_cell_ordinal=1,period_occurrence=0,
            interval='ANNUAL' if mode=='NAM' else 'QUARTER_UNVERIFIED',accepted=False,pit_ready=False)

    def run_rows(self,rows,kind='Regular',payload=None,coverage=None):
        return diagnose(rows,[dict(symbol='X',proposed_company_type=kind)],{'raw.json':payload or {}},coverage or [])

    def test_false_balance_is_flagged_without_rounding_or_acceptance(self):
        rows=[self.row('270','TỔNG CỘNG TÀI SẢN',101),self.row('300','NỢ PHẢI TRẢ',60,'NV'),self.row('400','VỐN CHỦ SỞ HỮU',40,'NV')]
        out=self.run_rows(rows);check=out['arithmetic'][0]
        self.assertEqual(check['status'],'RAW_DIFFERENCE');self.assertEqual(check['difference'],'1')
        self.assertEqual(out['document_queue'][0]['reasons'],['RAW_ACCOUNTING_DIFFERENCE'])
        self.assertTrue(all(not r['accepted'] and not r['pit_ready'] for r in out['mapped']))

    def test_scope_provider_partitions_not_joined_to_manufacture_identity(self):
        rows=[self.row('270','TỔNG CỘNG TÀI SẢN',100,ptype='HK'),self.row('300','NỢ PHẢI TRẢ',60,'NV',ptype='N'),self.row('400','VỐN CHỦ SỞ HỮU',40,'NV',ptype='N')]
        self.assertEqual(self.run_rows(rows)['arithmetic'],[])

    def test_company_type_never_receives_regular_score_mapping(self):
        rows=[self.row('270','TỔNG CỘNG TÀI SẢN',100)]
        for kind in ['Bank','Securities']:
            out=self.run_rows(rows,kind);self.assertEqual(out['mapped'],[]);self.assertEqual(out['arithmetic'],[])

    def test_only_group_number_proves_structural_zero_blank_or_nonzero_kept(self):
        body=dict(value=dict(templace=[dict(code='HDKD',number=1,data=[])]))
        rows=[self.row('HDKD_1',None,0,'HDKD','LCTT',mapping='UNMAPPED_CODE_QUARANTINED'),
              self.row('',None,0,'HDKD','LCTT',mapping='BLANK_CODE_QUARANTINED'),
              self.row('HDKD_1',None,17,'HDKD','LCTT',mapping='UNMAPPED_CODE_QUARANTINED')]
        out=self.run_rows(rows,payload=body)
        self.assertEqual(len(out['structural']),1);self.assertEqual(len(out['unresolved']),2)
        self.assertEqual(len(out['orphans']),1)

    def test_duplicate_vintage_values_are_not_averaged(self):
        rows=[self.row('270','TỔNG CỘNG TÀI SẢN',100),self.row('270','TỔNG CỘNG TÀI SẢN',102),self.row('440','TỔNG CỘNG NGUỒN VỐN',101,'NV')]
        out=self.run_rows(rows);self.assertEqual(len(out['conflicts']),1)
        self.assertEqual(out['arithmetic'][0]['status'],'AMBIGUOUS_OR_MISSING_VALUE')
        self.assertIn('MULTIPLE_PROVIDER_VALUES_REVIEW_VINTAGE',out['document_queue'][0]['reasons'])

    def test_row_displacement_detected_but_source_rows_never_repaired(self):
        rows=[self.row('319','Phải trả ngắn hạn khác',100,'NV'),self.row('320','Vay và nợ thuê tài chính ngắn hạn',200,'NV'),
              self.row('320','Vay và nợ thuê tài chính ngắn hạn',100,'NV',mode='QUY',quarter=4,ptype='N'),
              self.row('321','Other',200,'NV',mode='QUY',quarter=4,ptype='N')]
        original=copy.deepcopy(rows);out=self.run_rows(rows)
        self.assertTrue(out['displacements']);self.assertEqual(out['displacements'][0]['offset'],1)
        self.assertEqual(rows,original);self.assertEqual(out['document_queue'][0]['priority'],1)

    def test_missing_and_zero_differ_future_observations_do_not_enter_qa(self):
        rows=[self.row('270','TỔNG CỘNG TÀI SẢN',None),self.row('440','TỔNG CỘNG NGUỒN VỐN',0,'NV'),
              self.row('270','TỔNG CỘNG TÀI SẢN',999,year=2026)]
        out=self.run_rows(rows);self.assertEqual(len(out['mapped']),2)
        self.assertEqual(out['arithmetic'][0]['status'],'AMBIGUOUS_OR_MISSING_VALUE')

    def test_pending_acquisition_not_enqueued_as_missing_public_data(self):
        gap=dict(symbol='X',year='2015',quarter='2',mode='QUY',statement='LCTT',status='NO_CANDIDATE_IN_ACQUIRED_PAGES',task_accounting_complete='False')
        out=self.run_rows([],coverage=[gap]);self.assertEqual(out['document_queue'],[])
        self.assertEqual(out['missing'][0]['reason'],'ACQUISITION_PENDING_NOT_A_DATA_GAP')
        gap['task_accounting_complete']='True';out=self.run_rows([],coverage=[gap]);self.assertEqual(len(out['document_queue']),1)
        self.assertIn('NOT_PROOF_OF_NONPUBLICATION',out['missing'][0]['reason'])

    def test_ytd_cashflow_stays_duration_unresolved(self):
        row=self.row('HDKD_20','Lưu chuyển tiền thuần từ hoạt động kinh doanh',123,'HDKD','LCTT',mode='LUYKE',quarter=2)
        out=self.run_rows([row]);self.assertEqual(out['mapped'][0]['temporal_status'],'DURATION_AND_STANDALONE_VS_YTD_REVIEW_REQUIRED')
        self.assertFalse(out['summary']['financial_features_allowed'])

    def test_invalid_numeric_token_is_quarantined_and_queued(self):
        row=self.row('270','TỔNG CỘNG TÀI SẢN',None);row['value_status']='INVALID_NUMERIC_QUARANTINED'
        out=self.run_rows([row]);self.assertEqual(out['summary']['invalid_numeric_cells'],1);self.assertEqual(out['mapped'],[])
        self.assertEqual(out['document_queue'][0]['priority'],1)

    def test_nonzero_header_without_label_is_not_discarded_as_zero_scaffolding(self):
        row=self.row('HDKD_1',None,680759314148,'HDKD','LCTT',mapping='UNMAPPED_CODE_QUARANTINED')
        body=dict(value=dict(templace=[dict(code='HDKD',number=1,data=[])]))
        out=self.run_rows([row],kind='Securities',payload=body)
        self.assertEqual(out['structural'],[]);self.assertEqual(len(out['orphans']),1)
        self.assertEqual(out['document_queue'][0]['reasons'],['NONZERO_UNMAPPED_PROVIDER_CODE'])


if __name__=='__main__':unittest.main()
