import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("abb_aas_runner",ROOT/"scripts/review_abb_aas_lifecycle_v1.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class AasDiscoveryTests(unittest.TestCase):
    def test_only_public_same_issuer_paths_and_search_are_allowed(self):
        for url in ["https://aas.com.vn/thong-tin-co-dong/notice/","https://www.aas.com.vn/Content/Archive/FileAttact/a.pdf","https://aas.com.vn/?s=nghi+quyet+2024"]:
            self.assertTrue(module.aas_url(url))
        for url in ["https://www.hnx.vn/a.pdf","http://aas.com.vn/a.pdf","https://aas.com.vn/wp-admin/","https://user:pass@aas.com.vn/wp-content/uploads/a.pdf","https://aas.com.vn:444/wp-content/uploads/a.pdf","https://aas.com.vn/wp-content/uploads/%2e%2e/%2e%2e/wp-admin/a.pdf","https://aas.com.vn/?token=key"]:
            self.assertFalse(module.aas_url(url))
    def test_pdf_links_are_observed_not_inferred_and_encoded_without_external_hosts(self):
        html='<a href="/wp-content/uploads/2024/NQ 18.2024.pdf">NQ 18.2024</a><a href="https://other.example/NQ.pdf">external</a><a href="javascript:open()">click</a>'
        result=module.pdf_links(html,"https://aas.com.vn/thong-tin-co-dong/notice/")
        self.assertEqual(1,len(result));self.assertIn("NQ%2018.2024.pdf",result[0]["url"])
    def test_resolution_selection_does_not_prefer_cover_letter_over_matching_resolution(self):
        links=[{"url":"https://aas.com.vn/wp-content/uploads/CV254A.pdf","label":"CV 254A"},{"url":"https://aas.com.vn/wp-content/uploads/NQ18.2024.pdf","label":"NQ 18.2024"}]
        self.assertEqual(links[1],module.select_resolution_pdf(links,18))
    def test_multiple_possible_resolution_files_require_review(self):
        links=[{"url":"https://aas.com.vn/wp-content/uploads/NQ18.2024.pdf","label":"NQ 18.2024"},{"url":"https://aas.com.vn/wp-content/uploads/NQ18.2024-new.pdf","label":"NQ 18.2024 sửa"}]
        self.assertIsNone(module.select_resolution_pdf(links,18))
    def test_one_attachment_is_only_a_discovery_candidate_not_field_acceptance(self):
        link={"url":"https://aas.com.vn/wp-content/uploads/document.pdf","label":"download"}
        self.assertEqual(link,module.select_resolution_pdf([link],20))
    def test_unsupported_attachment_is_not_fetched_by_source_transport(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            t=module.AasPublicTransport(Path(folder))
            with self.assertRaises(ValueError):t.fetch("https://example.com/a.pdf")
            self.assertEqual([],t.requests)


if __name__=="__main__":unittest.main()
