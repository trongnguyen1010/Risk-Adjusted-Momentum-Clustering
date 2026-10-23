import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from delta_t1.experiments import financial_pdf_ocr_bridge_v2 as bridge
from delta_t1.ingestion.cafef_financial import encoded, digest


class ControllerTests(unittest.TestCase):
    def test_prepare_then_run_keeps_both_results_and_reuses_registered_pages(self):
        from pypdf import PdfWriter
        w=PdfWriter();w.add_blank_page(width=100,height=100);b=io.BytesIO();w.write(b);pdf=b.getvalue()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def put(p,v):
                f=root/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(v);return digest(v)
            def js(p,v):return put(p,encoded(v))
            pdfsha=put('doc.pdf',pdf);imsha=put('page.png',b'image');put('preview.png',b'preview')
            job=dict(pdf_path='doc.pdf',pdf_sha256=pdfsha,pdf_page=1,image_path='page.png',image_sha256=imsha)
            childsha=js('child.json',dict(jobs=[job]));js('campaign/registrations/a.json',dict(config_path='child.json',config_sha256=childsha,jobs=[job]))
            parentsha=js('parent.json',dict(output_root='campaign'))
            for p in ['src/delta_t1/experiments/financial_pdf_ocr_bridge_v2.py','scripts/financial_pdf_ocr_bridge_v2.py','src/delta_t1/experiments/financial_pdf_ocr_bridge.py']:put(p,b'source')
            js('selection.json',dict(version='financial-pdf-ocr-bridge-v1',selection_method='VISUAL_PAGE_SELECTION_REQUIRES_REVIEW',output_root='controller',pdf_path='doc.pdf',pdf_sha256=pdfsha,parent_ocr_config='parent.json',parent_ocr_config_sha256=parentsha,pages=[1],selection_evidence='preview.png'))
            prepared=bridge.run(root,'selection.json',False)
            self.assertEqual(prepared['new_planned_pages'],0)
            with patch.object(bridge,'render_prepare') as render,patch.object(bridge,'coordinate',return_value=dict(status='PARTIAL',charged_pages=1)) as coord:
                bridge.run(root,'selection.json',True)
                bridge.run(root,'selection.json',True)
                self.assertEqual(bridge.run(root,'selection.json',False),prepared)
                render.assert_not_called();self.assertEqual(coord.call_count,2)
            self.assertEqual(len(list((root/'controller/controller-results').glob('*/result.json'))),2)

    def test_duplicate_registered_page_is_not_charged_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'campaign/registrations';folder.mkdir(parents=True)
            child=root/'child.json';child.write_bytes(encoded({}));sha=digest(child.read_bytes())
            r=dict(config_path='child.json',config_sha256=sha,jobs=[dict(pdf_sha256='PDF',pdf_page=1)])
            for name in ['a','b']:(folder/(name+'.json')).write_bytes(encoded(r))
            with self.assertRaisesRegex(ValueError,'duplicate registered'):bridge.registered_pages(root,'campaign','PDF')
