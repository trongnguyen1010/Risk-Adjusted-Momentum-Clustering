import json,tempfile,unittest
from pathlib import Path
from delta_t1.ingestion.financial_provider_probe import collect
from delta_t1.ingestion.financial_provider_normalize import normalize_kbs,compare_cell
from delta_t1.ingestion.sources.base import AccessControlError


class ProviderTests(unittest.TestCase):
    def request(self):
        return dict(provider='KBS',symbol='FPT',url='https://public.test/?unit=1000',path='raw.json',sha256='hash')
    def payload(self):
        return dict(Head=[dict(YearPeriod=2025),dict(YearPeriod=2024),dict(YearPeriod=2023)],
            Content={'balance':[dict(ReportNormID=3000,Value1=0,Value2=None)]})
    def test_actual_columns_null_and_zero_preserved(self):
        cells=normalize_kbs(self.payload(),self.request())
        self.assertEqual(len(cells),2)
        self.assertEqual(cells[0]['value'],'0')
        self.assertIsNone(cells[1]['value'])
        self.assertIsNone(cells[0]['available_at'])
    def test_eps_is_unit_exception(self):
        p=self.payload();p['Content']['balance'][0]['ReportNormID']=5316
        self.assertIsNone(normalize_kbs(p,self.request())[0]['value'])
    def test_unit_and_header_mismatch_fail(self):
        r=self.request();r['url']='https://public.test/?unit=1'
        with self.assertRaises(ValueError):normalize_kbs(self.payload(),r)
        p=self.payload();p['Content']['balance'][0]['Value4']=1
        with self.assertRaises(ValueError):normalize_kbs(p,self.request())
    def test_rounding_boundary_not_source_priority(self):
        c=normalize_kbs(self.payload(),self.request())[0]
        self.assertEqual(compare_cell(c,500)['status'],'MATCH_WITHIN_THOUSAND_VND_ROUNDING')
        self.assertEqual(compare_cell(c,501)['status'],'VALUE_CONFLICT')
    def test_hard_stop_prevents_later_provider_requests(self):
        class Client:
            calls=0
            def get(self,url):self.calls+=1;raise AccessControlError('HTTP403')
        client=Client();r=self.request()
        c=dict(requests=[r,r],approved_hosts=['public.test'],financial_features_allowed=False,max_bytes=1000)
        with tempfile.TemporaryDirectory() as d:
            result=collect(c,Path(d)/'new',client)
        self.assertEqual(client.calls,1)
        self.assertEqual([r['status'] for r in result['requests']],['HARD_STOP','NOT_REQUESTED_PROVIDER_HARD_STOP'])
