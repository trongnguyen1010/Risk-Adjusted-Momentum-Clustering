import unittest
from delta_t1.experiments.financial_reference_cohorts import select_values,compute_cohort,price_after_publication,snapshot_ratio,dependency_dates


class ReviewedReferenceCohortTests(unittest.TestCase):
    def cohort(self,pdf='A'):
        return dict(id='COHORT-'+pdf,symbol='X',year=2025,source_report_year=2025,primary_pdf_sha256=pdf,input_scope='CONSOLIDATED',
            variant_clearance='EXISTING_NONFINANCIAL_REFERENCE_VARIANTS',eps_basis='REPORTED_NOTE_NO_RESERVE_NORMALIZATION_CLAIM',
            eps_numerator_field='reported_eps_numerator',period_months=12,fiscal_period_end='2025-12-31')

    def fact(self,field,value,year=2025,pdf='A',fid=None):
        return dict(id=fid or f'{pdf}-{year}-{field}',symbol='X',year=year,field=field,value=str(value),unit='VND',provenance=dict(pdf_sha256=pdf))

    def metric(self,result,family):return next(r for r in result['metrics'] if r['family']==family)

    def test_report_vintages_do_not_select_latest_or_mix_numerator_denominator(self):
        facts=[self.fact('reported_eps_numerator',100,pdf='A'),self.fact('weighted_average_basic_shares',10,pdf='A'),
               self.fact('reported_eps_numerator',80,pdf='B'),self.fact('weighted_average_basic_shares',20,pdf='B')]
        a=self.metric(compute_cohort(facts,self.cohort('A')),'EPS');b=self.metric(compute_cohort(facts,self.cohort('B')),'EPS')
        self.assertEqual(a['value'],'10');self.assertEqual(b['value'],'4');self.assertFalse(a['strict_pit_ready'])
        self.assertEqual(a['eps_numerator_field'],'reported_eps_numerator')

    def test_eps_never_aliases_total_parent_profit(self):
        facts=[self.fact('parent_net_profit',500),self.fact('weighted_average_basic_shares',10)]
        row=self.metric(compute_cohort(facts,self.cohort()),'EPS')
        self.assertIsNone(row['value']);self.assertIn(dict(field='reported_eps_numerator',year=2025),row['missing_inputs'])

    def test_primary_field_conflict_is_not_averaged(self):
        facts=[self.fact('reported_eps_numerator',100),self.fact('reported_eps_numerator',200,fid='conflict'),self.fact('weighted_average_basic_shares',10)]
        result=compute_cohort(facts,self.cohort());self.assertEqual(len(result['conflicts']),1);self.assertIsNone(self.metric(result,'EPS')['value'])

    def test_auxiliary_bridge_only_imports_declared_field_year_and_pdf(self):
        cohort=self.cohort();cohort['auxiliary_fields']=[dict(pdf_sha256='B',field='total_assets',year=2023)]
        values,ids,_,_=select_values([self.fact('total_assets',100,2023,'B'),self.fact('reported_eps_numerator',999,pdf='B')],cohort)
        self.assertEqual(values,{('total_assets',2023):'100'})

    def test_closing_debt_uses_stocks_and_does_not_substitute_reclassification_flow(self):
        facts=[self.fact('noncurrent_loans_and_finance_leases',100),self.fact('debt_reclassification_flow',30)]
        self.assertNotIn(('long_term_debt_including_current_portion',2025),select_values(facts,self.cohort())[0])
        facts.append(self.fact('current_portion_original_long_term_debt',20))
        values,ids,_,d=select_values(facts,self.cohort());self.assertEqual(values['long_term_debt_including_current_portion',2025],'120')
        self.assertEqual(len(d[0]['dependency_ids']),2)

    def test_pe_and_pb_have_independent_required_inputs(self):
        price=dict(raw_close='20',trade_date='2026-08-28')
        pe=self.metric(compute_cohort([self.fact('reported_eps_numerator',100),self.fact('weighted_average_basic_shares',10)],self.cohort(),price),'PE')
        self.assertEqual(pe['value'],'2')
        facts=[self.fact('total_equity',300),self.fact('noncontrolling_equity',100),self.fact('common_shares',10)]
        pb=self.metric(compute_cohort(facts,self.cohort(),price),'PB');self.assertEqual(pb['value'],'1')
        self.assertTrue(all('weighted_average' not in x for x in pb['dependency_ids']))

    def test_pb_uses_outstanding_shares_not_eps_weighted_average(self):
        facts=[self.fact('total_equity',300),self.fact('noncontrolling_equity',100),self.fact('common_shares',10),
            self.fact('reported_eps_numerator',100),self.fact('weighted_average_basic_shares',100)]
        pb=self.metric(compute_cohort(facts,self.cohort(),dict(raw_close='20',trade_date='2026-08-28')),'PB')
        self.assertEqual(pb['value'],'1');self.assertTrue(pb['annual_pe_not_ttm']);self.assertIsNone(pb['strict_current_pb'])

    def test_date_only_reference_never_same_day_or_unknown_publication(self):
        price=dict(trade_date='2026-03-31')
        self.assertFalse(price_after_publication(price,'2026-03-31'));self.assertFalse(price_after_publication(price,None))
        self.assertTrue(price_after_publication(dict(trade_date='2026-04-01'),'2026-03-31'))

    def test_no_annualization_no_eps_basis_alias(self):
        cohort=self.cohort();cohort['period_months']=9
        with self.assertRaises(ValueError):compute_cohort([],cohort)
        cohort=self.cohort();cohort['eps_numerator_field']='parent_net_profit'
        with self.assertRaises(ValueError):compute_cohort([],cohort)

    def test_noncalendar_book_date_preserved_and_negative_pe_not_forced_positive(self):
        cohort=self.cohort();cohort['fiscal_period_end']='2025-09-30'
        result=compute_cohort([self.fact('reported_eps_numerator',100),self.fact('weighted_average_basic_shares',10)],cohort,dict(raw_close='20',trade_date='2026-08-28'))
        self.assertEqual(self.metric(result,'PE')['book_date'],'2025-09-30')
        self.assertIsNone(snapshot_ratio('PE','20','-1')['value'])

    def test_primary_publication_does_not_fill_unknown_auxiliary_publication(self):
        facts={'a':self.fact('total_assets',100,pdf='A'),'b':self.fact('total_assets',90,2024,'B')}
        row=dict(value='4',dependency_ids=['a','b']);out=dependency_dates(row,facts,{'A':'2026-03-31','B':None})
        self.assertFalse(out['all_financial_dependency_publication_dates_referenced'])
        self.assertIsNone(out['latest_financial_dependency_publication_date_reference'])
        self.assertEqual(out['unknown_dependency_publication_pdf_hashes'],['B'])


if __name__=='__main__':unittest.main()
