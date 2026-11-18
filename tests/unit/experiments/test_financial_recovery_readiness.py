import tempfile
import unittest
from pathlib import Path

from delta_t1.experiments import financial_recovery_readiness as f
from delta_t1.ingestion.cafef_financial import digest


class ReadinessTests(unittest.TestCase):
    def test_receipts_require_exact_path_hash_and_preserve_provider_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'raw.pdf';p.write_bytes(b'%PDF-test')
            inv=[dict(path='raw.pdf',sha256=digest(p.read_bytes()),bytes=p.stat().st_size)]
            meta=root/'inventory.json'
            f.put(meta,dict(documents=[dict(path=str(p),sha256=inv[0]['sha256'],symbol='AAA',year=2020,
                      identity_status='LIST_FILENAME_CONFLICT',provider_report=dict(Link='https://source.org/a.pdf',Name='report'))]))
            cache,_=f.resolve_cache(root,inv,[meta])
            self.assertEqual(len(cache['entries']),1)
            row=cache['entries'][0]
            self.assertEqual(row['hints']['identity_status'],'LIST_FILENAME_CONFLICT')
            self.assertIsNone(row['published_at']);self.assertFalse(row['accepted'])
            self.assertEqual(cache['unresolved_paths'],[])
            p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'bytes changed'):f.resolve_cache(root,inv,[meta])

    def test_no_filename_inference_or_hash_only_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'AAA-2020.pdf';p.write_bytes(b'%PDF-')
            inv=[dict(path=p.name,sha256=digest(p.read_bytes()),bytes=p.stat().st_size)]
            m=root/'result.json';f.put(m,dict(path='elsewhere.pdf',sha256=inv[0]['sha256'],url='https://x.org/a.pdf'))
            cache,_=f.resolve_cache(root,inv,[m])
            self.assertEqual(cache['entries'],[]);self.assertEqual(cache['unresolved_paths'],[p.name])

    def test_multiple_hashes_same_url_stay_conflicted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);inv=[];rec=[]
            for name in ['a','b']:
                p=root/(name+'.pdf');p.write_bytes(('%PDF-'+name).encode())
                row=dict(path=p.name,sha256=digest(p.read_bytes()),bytes=p.stat().st_size);inv.append(row)
                rec.append(dict(path=p.name,sha256=row['sha256'],url='https://x.org/report.pdf'))
            m=root/'inventory.json';f.put(m,rec)
            cache,_=f.resolve_cache(root,inv,[m]);self.assertEqual(len(cache['url_vintage_conflicts']),1)

    def test_consecutive_periods_not_endpoint_span_and_no_pit_promotion(self):
        reg={'id':dict(ticker='AAA')}
        rows=[dict(registry_id='id',symbol='AAA',year=y,research_ready='False',strict_pit_ready='False') for y in [2016,2017,2020,2021,2022,2025]]
        c=f.coverage(rows,reg)[0]
        self.assertEqual(c['longest_consecutive'],3);self.assertEqual(c['observed_periods'],6)
        self.assertFalse(c['full10']);self.assertFalse(c['research_ready'])
        with self.assertRaisesRegex(ValueError,'duplicate'):f.coverage(rows+[rows[0]],reg)
        rows[0]['strict_pit_ready']='True'
        with self.assertRaisesRegex(ValueError,'promotion'):f.coverage(rows,reg)

    def test_queue_is_dependency_count_not_pdf_approval(self):
        reg={'id':dict(ticker='AAA')}
        cov=[dict(registry_id='id',symbol='AAA',observed_periods=9,missing_years=[2019],full10=False)]
        gaps=[dict(registry_id='id',year=2019,reasons='HELD')]
        cache=dict(entries=[dict(hints=dict(symbol='AAA',year=2019),sha256='x')])
        q,s=f.recovery_queue(cov,gaps,cache,reg)
        self.assertEqual(s['annual_dependencies'],1);self.assertEqual(q[0]['cache_candidate_hashes'],['x'])
        self.assertFalse(q[0]['download_authorized']);self.assertFalse(q[0]['pdf_required_confirmed'])
        self.assertIsNone(s['confirmed_pdf_count']);self.assertFalse(s['guarantee'])
        reg['id2']=dict(ticker='AAA')
        q,_=f.recovery_queue(cov,gaps,cache,reg)
        self.assertEqual(q[0]['cache_candidate_hashes'],[])


if __name__=='__main__': unittest.main()
