import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("supplement_plan",ROOT/"scripts/plan_corporate_action_supplement_v1.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class FakeTransport:
    fail=False
    def __init__(self,root,**kwargs):self.requests=[];self.root=root
    def fetch(self,url,binary=False):
        self.requests.append({"url":url})
        if self.fail:raise module.SourceLimitation("SOURCE_ACCESS_LIMITATION: HTTP 403/challenge; no retry")
        return (b"%PDF-fixture" if binary else "<html>Official test notice</html>"),{"source_hash":"fixture"}


class SupplementPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.c=json.loads(module.CONFIG.read_text(encoding="utf-8"));self.config=self.root/"config.json"
        self.patcher=patch.object(module,"CONFIG",self.config);self.patcher.start()
        self.save()
    def tearDown(self):self.patcher.stop();self.temp.cleanup()
    def save(self):self.config.write_text(json.dumps(self.c),encoding="utf-8")
    def plan(self):
        root=self.root/"plan";root.mkdir()
        body=json.dumps(self.c).encode();(root/"pilot_plan.json").write_bytes(body)
        (root/"manifest.json").write_text(json.dumps({"config_sha256":module.sha(self.config.read_bytes()),"files":{"pilot_plan.json":module.sha(body)}}),encoding="utf-8")
        return root
    def test_pilot_refuses_hnx_even_for_public_document(self):
        self.c["samples"][0]["url"]="https://www.hnx.vn/public.pdf";self.save()
        with self.assertRaises(ValueError):module.config()
    def test_pilot_refuses_credentials_nonstandard_port_redirects_and_low_delay(self):
        original=json.loads(json.dumps(self.c))
        for url in ["https://user:pass@vsdc.vn/vi/ad/1","https://vsdc.vn:444/vi/ad/1"]:
            self.c=json.loads(json.dumps(original));self.c["samples"][0]["url"]=url;self.save()
            with self.assertRaises(ValueError):module.config()
        self.c=original;self.c["follow_redirects"]=True;self.save()
        with self.assertRaises(ValueError):module.config()
        self.c["follow_redirects"]=False;self.c["interval_seconds"]=.25;self.save()
        with self.assertRaises(ValueError):module.config()
    def test_no_automatic_bulk_canonical_or_field_approval(self):
        for flag in ["bulk_collection_allowed","canonical_build","automatic_field_approval","hnx_requests_allowed"]:
            self.c[flag]=True;self.save()
            with self.assertRaises(ValueError):module.config()
            self.c[flag]=False
    def test_duplicate_url_and_path_traversal_sample_id_are_refused(self):
        self.c["samples"][1]["url"]=self.c["samples"][0]["url"];self.save()
        with self.assertRaises(ValueError):module.config()
        self.c["samples"]=self.c["samples"][:1];self.c["samples"][0]["id"]="../escape";self.save()
        with self.assertRaises(ValueError):module.config()
    def test_access_failure_stops_issuer_alias_and_continues_different_sources(self):
        self.c["samples"]=self.c["samples"][:3];self.save();plan=self.plan()
        class Denied(FakeTransport):fail=True
        result=module.pilot(plan,self.root/"out",transport_factory=Denied)
        self.assertEqual(2,result["network_request_attempts"])
        self.assertEqual("SKIPPED_SOURCE_STOP",result["results"][1]["status"])
        self.assertEqual(0,result["hnx_requests"])
        self.assertFalse(result["bulk_collection_started"])
    def test_received_document_is_not_claimed_to_resolve_fields(self):
        self.c["samples"]=self.c["samples"][:1];self.save()
        result=module.pilot(self.plan(),self.root/"out",transport_factory=FakeTransport)
        self.assertEqual(1,result["public_documents_received"])
        self.assertEqual("NOT_YET_EVALUATED",result["results"][0]["field_sufficiency"])
        self.assertEqual(0,result["accepted_field_changes"])
        with self.assertRaises(FileExistsError):module.pilot(self.root/"plan",self.root/"out",transport_factory=FakeTransport)
    def test_modified_frozen_plan_fails_before_transport(self):
        plan=self.plan();(plan/"pilot_plan.json").write_text("{}",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"PLAN_FILE_HASH_MISMATCH"):module.pilot(plan,self.root/"out",transport_factory=FakeTransport)
        self.assertFalse((self.root/"out").exists())
    def test_manifest_cannot_read_outside_its_plan_folder(self):
        plan=self.plan();p=plan/"manifest.json";m=json.loads(p.read_text(encoding="utf-8"));m["files"]["../config.json"]=module.sha(self.config.read_bytes());p.write_text(json.dumps(m),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"UNSAFE_PLAN_MEMBER"):module.pilot(plan,self.root/"out",transport_factory=FakeTransport)


if __name__=="__main__":unittest.main()
