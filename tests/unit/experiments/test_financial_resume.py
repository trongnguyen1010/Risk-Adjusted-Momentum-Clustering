import tempfile
import unittest
from pathlib import Path

from delta_t1.experiments import financial_resume as a
from delta_t1.experiments import financial_user_workflow as f


class MetadataAdapterTests(unittest.TestCase):
    def test_inherited_hash_from_sealed_reservation_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'data/run/extract/inherited-failed'
            f.write_new(p/'reservation.json',f.encoded(dict(pdf_sha256='a'*64)))
            f.write_new(p/'result.json',f.encoded(dict(status='EXTRACTION_FAILED',pages=[])))
            f.seal(p); before={x:x.read_bytes() for x in p.iterdir()}
            with a.inherited_metadata(root,'data/run'):
                self.assertEqual(f.load(p/'result.json')['pdf_sha256'],'a'*64)
            self.assertNotIn('pdf_sha256',f.load(p/'result.json'))
            for x,b in before.items(): self.assertEqual(x.read_bytes(),b)

    def test_tampered_reservation_fails_and_loader_restores_after_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'data/run/extract/inherited-failed'
            f.write_new(p/'reservation.json',f.encoded(dict(pdf_sha256='a'*64)))
            f.write_new(p/'result.json',f.encoded(dict(status='EXTRACTION_FAILED')))
            f.seal(p); (p/'reservation.json').write_bytes(b'{}'); original=f.load
            with self.assertRaises(ValueError):
                with a.inherited_metadata(root,'data/run'): f.load(p/'result.json')
            self.assertIs(f.load,original)

    def test_current_result_never_infers_missing_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'data/run/extract/current'
            f.write_new(p/'result.json',f.encoded(dict(status='EXTRACTION_FAILED')))
            with a.inherited_metadata(root,'data/run'):
                self.assertNotIn('pdf_sha256',f.load(p/'result.json'))


if __name__=='__main__': unittest.main()
