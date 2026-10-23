import unittest
from delta_t1.experiments.financial_issuer_html_reference import captured_lines,validate_review


class IssuerHtmlReferenceTests(unittest.TestCase):
    def fixture(self):
        values=dict(total_assets='10000000000',total_capital='10000000000',total_liabilities='4000000000',
            total_equity='6000000000',current_assets='7000000000',noncurrent_assets='3000000000',
            current_liabilities='3000000000',noncurrent_liabilities='1000000000',net_revenue='10000000000',
            cost_of_goods_sold='6000000000',gross_profit='4000000000',profit_before_tax='3000000000',
            reported_operating_profit='3000000000',other_profit='0',net_profit='2400000000',
            current_tax_expense='600000000',deferred_tax_expense='0',finance_income='0',finance_expense='0',
            associate_profit='0',selling_expense='500000000',administrative_expense='500000000',operating_cash_flow='-1000000000')
        fields=[];lines={}
        for i,(name,value) in enumerate(values.items()):
            lines[i*3]='Mã số '+str(i);lines[i*3+1]='2023 VND '+value
            fields.append(dict(field=name,source_code=str(i),localized_value=value,value=value,line_start=i*3,line_end=i*3+1))
        return dict(symbol='PLX',year=2023,scope='CONSOLIDATED',unit='VND',interval='ANNUAL_12_MONTHS',
            source_url='https://www.petrolimex.com.vn/bctn-2023-baocaotaichinh.html',strict_pit_ready=False,fields=fields),lines

    def test_reviewed_same_source_vector_with_unchanged_quality_checks(self):
        review,lines=self.fixture();self.assertEqual(validate_review(review,lines)['operating_cashflow_to_assets'],-0.1)

    def test_wrong_issuer_source_scope_interval_or_pit_never_promoted(self):
        for field,value in [('symbol','CTD'),('scope','SEPARATE'),('unit','BILLION_VND'),('interval','SIX_MONTHS'),('strict_pit_ready',True),('source_url','https://example.com')]:
            review,lines=self.fixture();review[field]=value
            with self.assertRaises(ValueError):validate_review(review,lines)

    def test_transcription_wrong_row_and_absent_year_fail(self):
        review,lines=self.fixture();review['fields'][0]['value']='999'
        with self.assertRaises(ValueError):validate_review(review,lines)
        review,lines=self.fixture();lines[0]='Mã số unexpected'
        with self.assertRaises(ValueError):validate_review(review,lines)
        review,lines=self.fixture();lines[1]=lines[1].replace('2023','2022')
        with self.assertRaises(ValueError):validate_review(review,lines)

    def test_disagreeing_captures_fail_instead_of_source_preference(self):
        with self.assertRaises(ValueError):captured_lines(['L1: 100','L1: 200'])
        self.assertEqual(captured_lines(['L1: 100','L1: 100']),{1:'100'})
