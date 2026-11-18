import copy,json,unittest
from delta_t1.experiments.financial_scale_probe import CLOSED,VERSION,annual_candidates,validate


def config():
    symbols=['S'+str(i) for i in range(50)]
    return dict(version=VERSION,symbols=symbols,pdf_symbols=symbols[:4],prior_year_symbols=symbols[:2],
        year=2025,max_documents=24,max_pdf_pages=250,approved_hosts=['cafef.vn','cafefnew.mediacdn.vn'],
        budgets=dict(max_logical_requests=90,max_transport_attempts=100,max_pdf_download_attempts=20,
            max_response_bytes=25000000,max_total_downloaded_bytes=250000000,max_wall_seconds=3600,
            max_attempts_per_request=1,min_seconds_between_transport_attempts=2,timeout_seconds=25),**CLOSED)


class ScaleProbeTests(unittest.TestCase):
    def test_bounded_exact_membership(self):
        c=config();members=[dict(ticker=s) for s in c['symbols']];validate(c,members)
        for field,value in [('symbols',list(reversed(c['symbols']))),('pdf_symbols',['OUTSIDE']),
                            ('prior_year_symbols',['OUTSIDE']),('financial_cluster_allowed',True),('year',2026)]:
            broken=copy.deepcopy(c);broken[field]=value
            with self.assertRaises(ValueError):validate(broken,members)

    def test_request_bytes_spacing_and_pdf_caps(self):
        c=config();members=[dict(ticker=s) for s in c['symbols']]
        for key,value in [('min_seconds_between_transport_attempts',1),('max_pdf_download_attempts',21),
                          ('max_total_downloaded_bytes',250000001),('max_logical_requests',91)]:
            broken=copy.deepcopy(c);broken['budgets'][key]=value
            with self.assertRaises(ValueError):validate(broken,members)

    def test_consolidated_annual_vintages_preserved_without_priority(self):
        rows=[dict(id='b',Year=2025,Quarter=5,Name='BCTC hợp nhất kiểm toán',Link='b.pdf'),
              dict(id='a',Year=2025,Quarter=5,Name='BCTC hợp nhất sửa đổi',Link='a.pdf'),
              dict(id='q',Year=2025,Quarter=2,Name='BCTC hợp nhất',Link='q.pdf'),
              dict(id='p',Year=2025,Quarter=5,Name='BCTC riêng',Link='p.pdf')]
        x=annual_candidates(json.dumps(dict(Success=True,Data=rows)).encode(),2025)
        self.assertEqual([r['id'] for r in x],['a','b'])

    def test_bad_envelope_and_duplicate_report_id_rejected(self):
        for body in [b'{"Success":false,"Data":[]}',b'[]',json.dumps(dict(Success=True,Data=[
            dict(id='x',Year=2025,Quarter=5,Name='hợp nhất'),
            dict(id='x',Year=2025,Quarter=5,Name='hợp nhất')])).encode()]:
            with self.assertRaises(ValueError):annual_candidates(body,2025)


if __name__=='__main__':unittest.main()
