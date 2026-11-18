import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from delta_t1.ingestion.cafef_financial import encoded
from delta_t1.ingestion.financial_requirements import export_requirements
from delta_t1.ingestion.financial_supplement import collect
from delta_t1.ingestion.sources.base import AccessControlError


class FinancialRequirementsTests(unittest.TestCase):
    @patch("delta_t1.ingestion.financial_requirements.verify")
    def test_baseline_zero_and_tangible_ppe_distinct(self, _):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / "raw_run"; (source / "raw").mkdir(parents=True)
            (source / "config.json").write_bytes(encoded({"symbols": ["FPT"]}))
            (source / "manifest.json").write_bytes(encoded({}))
            facts=[]
            for code, name, value in [("221", "Tài sản cố định hữu hình", 0), ("220", "Tài sản cố định", 999)]:
                facts.append(dict(symbol="FPT",year=2019,quarter=0,provider_statement="bsheet",provider_item_code=code,
                                  item_name=name,display_number_candidate=value,raw_path="evidence.html",raw_sha256="sha"))
            (source / "raw/a.parsed.json").write_bytes(encoded({"facts": facts}))
            policy = root / "policy.json"
            policy.write_bytes(encoded({"contract_version":"financial-evidence-policy-v1","symbols":["FPT"],"financial_features_allowed":False,
                                        "financial_pit_gate":"NOT_READY","annual_document_start_year":2019,"annual_document_end_year":2019}))
            result=export_requirements(source,policy,root/"out")
            rows={r["field"]:r for r in result["rows"]}
            self.assertEqual(rows["net_tangible_ppe"]["candidate_values"], ["0"])
            self.assertEqual(rows["fixed_assets"]["candidate_values"], ["999"])
            self.assertEqual(rows["ppe_depreciation_excluding_amortization"]["presence_status"],"DOCUMENT_NOTE_REVIEW_REQUIRED")
            self.assertTrue(all(r["available_at"] is None and r["financial_features_allowed"] is False for r in result["rows"]))

    def config(self):
        return {"approved_hosts":["www.ptsc.com.vn"],"max_bytes":100,"financial_features_allowed":False,
                "requests":[{"symbol":"PVS","year":2020,"kind":"pdf","url":"https://www.ptsc.com.vn/a.pdf"},
                            {"symbol":"PVS","year":2021,"kind":"pdf","url":"https://www.ptsc.com.vn/b.pdf"}]}

    def test_supplement_access_boundary_stops_entire_run(self):
        class Client:
            calls=0
            def get(self,url):
                self.calls+=1; raise AccessControlError("403")
        with tempfile.TemporaryDirectory() as tmp:
            client=Client(); _,result=collect(self.config(),Path(tmp),client=client)
            self.assertEqual(client.calls,1)
            self.assertEqual([r["status"] for r in result["requests"]],["HARD_STOP","NOT_REQUESTED_HARD_STOP"])

    def test_supplement_rejects_unapproved_and_path_injection(self):
        for key,value in [("url","https://evil.example/a.pdf"),("symbol","../escape"),("kind","exe")]:
            config=self.config();config["requests"][0][key]=value
            with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):collect(config,Path(tmp))

if __name__=="__main__":unittest.main()
