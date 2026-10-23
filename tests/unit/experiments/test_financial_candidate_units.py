import copy,json
import unittest
from delta_t1.experiments.financial_candidate_units import annotate,verify_display_proof
from delta_t1.ingestion.cafef_financial import digest


class CandidateUnitTests(unittest.TestCase):
    def fixture(self,value='1000000000',static=False):
        template=[dict(code='10',name='Doanh thu thuần về bán hàng và cung cấp dịch vụ',static=static)]
        candidate=dict(statement='KQKD',group='KQKD',raw_code='10',label=template[0]['name'],
                       field='net_revenue',value=value,template_sha256=digest(json.dumps(template,ensure_ascii=False,sort_keys=True,default=str).encode()))
        return candidate,dict(value=dict(templace=template))

    def test_raw_currency_not_scaled_from_display_or_magnitude(self):
        for value in ['1','1000000000','-10','0',None]:
            candidate,payload=self.fixture(value);result=annotate(candidate,payload)
            self.assertEqual(result['unit_value'],value)
            self.assertEqual(result['unit_multiplier'],'1')
            self.assertFalse(result['accepted']);self.assertFalse(result['pit_ready'])

    def test_static_and_unknown_formatter_not_proven(self):
        for static in [True,None]:
            candidate,payload=self.fixture(static=static)
            self.assertIsNone(annotate(candidate,payload)['provider_raw_unit'])

    def test_eps_is_not_monetary_unit(self):
        candidate,payload=self.fixture();candidate.update(raw_code='70',label='Lãi cơ bản trên cổ phiếu (Đồng/1 cổ phiếu)',field='vendor_basic_eps')
        self.assertIsNone(annotate(candidate,payload)['provider_raw_unit'])

    def test_template_or_label_change_is_not_accepted(self):
        candidate,payload=self.fixture();payload['value']['templace'][0]['name']='different'
        with self.assertRaisesRegex(ValueError,'template'):annotate(candidate,payload)
        candidate,payload=self.fixture();candidate['field']='net_profit'
        self.assertIsNone(annotate(candidate,payload)['provider_raw_unit'])

    def test_unsupported_contract_cannot_approve_values(self):
        with self.assertRaisesRegex(ValueError,'reference-only'):
            verify_display_proof(dict(version='financial-cafef-unit-contract-v1',canonical_acceptance_allowed=True),{})

    def test_nonfinite_or_boolean_amount_rejected(self):
        for value in ['NaN','Infinity',True]:
            candidate,payload=self.fixture(value)
            with self.assertRaises(ValueError):annotate(candidate,payload)


if __name__=='__main__':unittest.main()
