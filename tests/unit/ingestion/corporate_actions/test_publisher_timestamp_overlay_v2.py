"""V2 guards: source scopes, archive provenance và timestamp boundaries."""
import copy
from datetime import datetime
import gzip
import hashlib
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import base64

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.ingestion.corporate_actions import publisher_timestamp_overlay_v2 as v2
from tests.unit.ingestion.corporate_actions import test_publisher_timestamp_overlay as fixtures


class PublisherTimestampOverlayV2Tests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.PublisherTimestampOverlayTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.root = self.f.root
        packet = json.loads((self.root / "packet.json").read_bytes())
        packet["rows"][-1]["review_value"] = "ORS"
        packet["rows"].append({"row_id": "3.ratio", "event_id": "3", "field": "ratio", "field_scope": "ORIGINAL_TERMS", "review_value": "100:12"})
        self.packet_ref = self.f.write_json("packet.json", packet)
        self.f.policy["baseline_packets"] = [self.packet_ref]
        self.f.policy["baseline_rows"] = 4
        self.f.execute()
        self.original_base = {f.name: f.read_bytes() for f in (self.root / "output").iterdir()}
        self.approval = {"owner_message": "hãy thực hiện", "purpose": v2.PURPOSE, "approved_groups": []}
        self.policy = {"policy_id": "SYNTHETIC-V2", "status": "OWNER_APPROVED", "activated": True,
            "purpose": v2.PURPOSE, "DATE_ONLY_enabled": False, "canonical_build": False,
            "strict_research_gate_opened": False, "exact_ticker": "ORS", "baseline_rows": 4,
            "new_field_count": 2, "carry_forward_count": 2,
            "base_runtime_ref": self.f.write("runtime.py", b"SYNTHETIC VERSION PIN"),
            "base_artifact": {"directory": "output", "manifest_sha256": hashlib.sha256((self.root / "output/manifest.json").read_bytes()).hexdigest()},
            "baseline_packets": [self.packet_ref], "groups": []}
        self.mapping = []
        self.source_state = {}
        self.add_group("2", "ticker", "ORS", v2.LIVE, "2021-06-02T16:55:48+07:00")
        self.add_group("3", "ratio", "100:12", v2.ARCHIVE, "2024-06-11T11:18:31+07:00")
        self.save_mappings()

    def save_mappings(self):
        self.policy["field_mappings_ref"] = self.f.write_json("new_mapping.json", self.mapping)
        prior = [{k: x[k] for k in ["row_id", "event_id", "field", "value"]} for x in self.mapping]
        self.policy["prior_proposed_mappings_ref"] = self.f.write_json("new_prior.json", prior)
        self.policy["owner_approval_ref"] = self.f.write_json("new_approval.json", self.approval)

    def add_group(self, event, field, value, profile, timestamp):
        row_id = event + "." + field
        title, url, publisher = "SYNTHETIC notice " + event, "https://example.test/" + event, "Synthetic publisher " + event
        text = "SYNTHETIC ORS " + field + " " + value
        g = {"event_id": event, "timestamp": timestamp, "field_count": 1,
             "publication_source": publisher, "publisher": publisher, "profile": profile,
             "field_locators": {row_id: {"selector": "p", "ordinal": 0, "text_sha256": hashlib.sha256(text.encode()).hexdigest()}},
             "evidence": {"article_url": url, "headline": title}}
        self.policy["groups"].append(g)
        self.approval["approved_groups"].append({"event_id": event, "timestamp": timestamp,
            "field_count": 1, "publication_source": publisher, "row_ids": [row_id]})
        self.mapping.append({"row_id": row_id, "event_id": event, "field": field, "exact_ticker": "ORS",
            "field_scope": "ORIGINAL_TERMS", "value": value,
            "field_scope_provenance": {"packet_ref": self.packet_ref, "row_id": row_id},
            "proposed_source_published_at": timestamp})
        self.source_state[event] = {"text": text, "published": timestamp, "modified": timestamp,
                                    "publisher": publisher, "url": url, "title": title}
        self.refresh_group(event)

    def refresh_group(self, event):
        g = next(x for x in self.policy["groups"] if x["event_id"] == event)
        s = self.source_state[event]
        ld = {"@type": "NewsArticle", "headline": s["title"], "mainEntityOfPage": {"@id": s["url"]},
              "publisher": {"name": s["publisher"]}, "datePublished": s["published"], "dateModified": s["modified"]}
        html = '<script type="application/ld+json">' + json.dumps(ld) + '</script>'
        for attr, value in [('property="article:published_time"', s['published']), ('property="article:modified_time"', s['modified']), ('itemprop="datePublished"', s['published'])]:
            html += '<meta ' + attr + ' content="' + value + '">'
        html += '<p>' + s["text"] + '</p>'
        body = html.encode()
        article_ref = self.f.write("source" + event + ".html", body)
        g["evidence"]["article_ref"] = article_ref
        if g["profile"] == v2.LIVE:
            receipt = self.f.receipt("source" + event + ".receipt.json", article_ref, g["evidence"]["article_url"])
            g["evidence"]["article_receipt_ref"] = receipt
        else:
            receipt = self.make_archive(g, body)
        row = next(x for x in self.mapping if x["event_id"] == event)
        row.update(source_ref=article_ref, source_receipt_ref=receipt)

    def make_archive(self, g, payload):
        e = g["evidence"]
        digest = base64.b32encode(hashlib.sha1(payload).digest()).decode()
        capture = "2024-06-16T02:08:25Z"
        http = b'HTTP/1.1 200 OK\r\nContent-Length: ' + str(len(payload)).encode() + b'\r\n\r\n' + payload
        header = ("WARC/1.0\r\nWARC-Type: response\r\nWARC-Target-URI: " + e["article_url"] +
                  "\r\nWARC-Date: " + capture + "\r\nWARC-Payload-Digest: sha1:" + digest +
                  "\r\nContent-Length: " + str(len(http)) + "\r\n\r\n").encode()
        raw = gzip.compress(header + http + b'\r\n\r\n', mtime=0)
        raw_ref = self.f.write("archive.warc.gz", raw)
        filename = "crawl-data/CC-MAIN-2024-26/segments/1.2/warc/CC-MAIN-20240611000000-20240617000000-00001.warc.gz"
        record = {"offset": "0", "length": str(len(raw)), "url": e["article_url"], "status": "200",
                  "filename": filename, "timestamp": "20240616020825", "digest": digest}
        index_ref = self.f.write("index.bin", (json.dumps(record) + '\n').encode())
        index_url = "https://index.commoncrawl.org/SYNTHETIC"
        ir = self.f.receipt("index.receipt.json", index_ref, index_url)
        r = {"status": 206, "method": "GET", "url": "https://data.commoncrawl.org/" + filename,
             "raw_path": raw_ref["path"], "sha256": raw_ref["sha256"], "bytes": len(raw),
             "Range": "bytes=0-" + str(len(raw) - 1), "headers": {"Content-Range": "bytes 0-" + str(len(raw) - 1) + "/999999"},
             "target_record": record, "index_ref": index_ref, "archive_capture_at": capture,
             "derived_HTML_sha256": e["article_ref"]["sha256"]}
        rr = self.f.write_json("archive.receipt.json", r)
        e.update(warc_ref=raw_ref, archive_receipt_ref=rr, index_ref=index_ref,
                 index_receipt_ref=ir, index_url=index_url, capture_at=capture)
        return rr

    def execute(self):
        self.save_mappings()
        self.f.write_json("policy_v2.json", self.policy)
        return v2.run("policy_v2.json", "output_v2", self.root)

    def test_carry_forward_immutable_and_source_boundaries(self):
        s = self.execute()
        self.assertEqual((4, 0, 2, 2), (s["admitted_rows"], s["held_rows"], s["new_admitted_rows"], s["carried_rows_unchanged"]))
        clocks = [("2021-06-02T16:55:47+07:00", 0), ("2021-06-02T16:55:48+07:00", 1),
                  ("2024-01-16T14:50:59+07:00", 1), ("2024-01-16T14:51:00+07:00", 3),
                  ("2024-06-11T11:18:30+07:00", 3), ("2024-06-11T04:18:31Z", 4)]
        for clock, count in clocks:
            self.assertEqual(count, len(v2.eligible_fields("output_v2", clock, root=self.root)))
        self.assertEqual(self.original_base, {f.name: f.read_bytes() for f in (self.root / "output").iterdir()})
        actual = [json.loads(x) for x in (self.root / 'output_v2/field_availability.jsonl').read_bytes().splitlines()]
        old = [json.loads(x) for x in self.original_base['field_availability.jsonl'].splitlines()]
        self.assertEqual(old[:2], actual[:2])
        self.assertTrue(all(x['usable_from_date'] is None and not x['strict_research_eligible'] for x in actual))

    def test_archive_capture_after_publication_does_not_become_publication(self):
        self.execute()
        rows = v2.eligible_fields('output_v2', '2024-06-11T11:18:31+07:00', root=self.root)
        row = next(x for x in rows if x['event_id'] == '3')
        self.assertEqual('2024-06-11T11:18:31+07:00', row['available_at'])
        self.assertEqual(v2.ARCHIVE, row['evidence_profile'])
        self.assertFalse(row['historical_content_at_publication_certified'])

    def test_inactive_and_other_gates_rejected(self):
        for key, value in [('activated', False), ('status', 'MANUAL_REVIEW_REQUIRED'), ('DATE_ONLY_enabled', True), ('purpose', 'STRICT_RESEARCH'), ('canonical_build', True), ('strict_research_gate_opened', True)]:
            with self.subTest(key=key):
                old = self.policy[key];self.policy[key] = value
                with self.assertRaisesRegex(ValueError, 'SCOPED_OWNER_APPROVAL'):self.execute()
                self.policy[key] = old
                self.assertFalse((self.root/'output_v2').exists())

    def test_missing_group_approval_and_wrong_scope_rejected(self):
        original = copy.deepcopy(self.approval)
        for key, value in [('timestamp', '2021-06-02T16:55:47+07:00'), ('field_count', 2), ('row_ids', ['2.foreign'])]:
            self.approval = copy.deepcopy(original);self.approval['approved_groups'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'OWNER_APPROVAL_GROUP_SCOPE'):self.execute()
        self.approval = copy.deepcopy(original);self.approval['approved_groups'].pop()
        with self.assertRaisesRegex(ValueError, 'APPROVAL_GROUP_SET'):self.execute()

    def test_modified_later_and_missing_offset_rejected(self):
        for key, value in [('modified', '2021-06-03T16:55:48+07:00'), ('published', '2021-06-02T16:55:48')]:
            with self.subTest(key=key):
                before = self.source_state['2'][key];self.source_state['2'][key] = value;self.refresh_group('2')
                with self.assertRaises(ValueError):self.execute()
                self.source_state['2'][key] = before

    def test_wrong_publisher_or_title_rejected(self):
        for key, value in [('publisher', 'Other source'), ('title', 'Other notice')]:
            before = self.source_state['2'][key];self.source_state['2'][key] = value;self.refresh_group('2')
            with self.assertRaisesRegex(ValueError, 'ARTICLE_IDENTITY'):self.execute()
            self.source_state['2'][key] = before

    def test_scoped_field_text_hash_and_negative_ordinal_rejected(self):
        loc = self.policy['groups'][0]['field_locators']['2.ticker']
        original = copy.deepcopy(loc)
        loc['text_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'FIELD_TEXT_HASH'):self.execute()
        loc.update(original);loc['ordinal'] = -1
        with self.assertRaisesRegex(ValueError, 'FIELD_LOCATOR'):self.execute()

    def test_value_scope_or_scope_provenance_changes_rejected(self):
        original = copy.deepcopy(self.mapping)
        for key, value in [('value', 'OTHER'), ('field_scope', 'REVISION'), ('exact_ticker', 'ORS_PREFIX')]:
            self.mapping = copy.deepcopy(original);self.mapping[0][key] = value
            with self.assertRaisesRegex(ValueError, 'REVIEWED_FIELD'):self.execute()
        self.mapping = copy.deepcopy(original);self.mapping[0]['field_scope_provenance']['row_id']='3.ratio'
        with self.assertRaisesRegex(ValueError, 'REVIEWED_FIELD'):self.execute()

    def test_duplicate_or_extra_mapping_rejected(self):
        self.mapping.append(copy.deepcopy(self.mapping[0]))
        self.policy['field_mappings_ref'] = self.f.write_json('new_mapping.json', self.mapping)
        self.f.write_json('policy_v2.json', self.policy)
        with self.assertRaisesRegex(ValueError, 'MAPPING_COUNT'):
            v2.run('policy_v2.json', 'output_v2', self.root)

    def test_duplicate_prior_mapping_rejected(self):
        ref = self.policy['prior_proposed_mappings_ref']
        proposed = json.loads((self.root/ref['path']).read_bytes())
        proposed.append(copy.deepcopy(proposed[0]))
        self.policy['prior_proposed_mappings_ref'] = self.f.write_json(ref['path'], proposed)
        self.f.write_json('policy_v2.json', self.policy)
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_PROPOSED_MAPPING'):
            v2.run('policy_v2.json', 'output_v2', self.root)

    def test_duplicate_approval_group_rejected(self):
        self.approval['approved_groups'].append(copy.deepcopy(self.approval['approved_groups'][0]))
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_APPROVAL_GROUP'):self.execute()

    def test_wrong_profile_and_carry_count_rejected(self):
        self.policy['groups'][0]['profile'] = 'HTTP206_AS_LIVE200'
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_EVIDENCE_PROFILE'):self.execute()
        self.policy['groups'][0]['profile'] = v2.LIVE
        self.policy['carry_forward_count'] = 1
        with self.assertRaisesRegex(ValueError, 'CARRY_FORWARD'):self.execute()

    def test_access_denied_receipt_stops_live_profile(self):
        g=self.policy['groups'][0];rr=g['evidence']['article_receipt_ref'];r=json.loads((self.root/rr['path']).read_bytes());r['status']=403
        g['evidence']['article_receipt_ref']=self.f.write_json(rr['path'],r)
        self.mapping[0]['source_receipt_ref']=g['evidence']['article_receipt_ref']
        with self.assertRaisesRegex(ValueError,'HTTP_RECEIPT_BINDING'):self.execute()

    def test_archive_status_range_target_index_and_capture_rejected(self):
        g=self.policy['groups'][1];e=g['evidence'];rr=e['archive_receipt_ref'];original=json.loads((self.root/rr['path']).read_bytes())
        cases=[('status',200),('Range','bytes=1-2'),('archive_capture_at','2024-06-17T02:08:25Z')]
        for key,value in cases:
            r={**original,key:value};e['archive_receipt_ref']=self.f.write_json(rr['path'],r)
            with self.subTest(key=key),self.assertRaises(ValueError):v2._archive(g,self.root,{})
        r=copy.deepcopy(original);r['target_record']['url']='https://example.test/foreign'
        e['archive_receipt_ref']=self.f.write_json(rr['path'],r)
        with self.assertRaises(ValueError):v2._archive(g,self.root,{})

    def test_archive_bad_digest_and_derived_payload_rejected(self):
        g=self.policy['groups'][1];e=g['evidence']
        e['article_ref']=self.f.write('different.html',b'wrong body')
        with self.assertRaisesRegex(ValueError,'ARCHIVE_PAYLOAD'):v2._archive(g,self.root,{})

    def test_archive_corrupt_gzip_rejected(self):
        g=self.policy['groups'][1];e=g['evidence'];body=bytearray((self.root/e['warc_ref']['path']).read_bytes());body[0]=0
        e['warc_ref']=self.f.write(e['warc_ref']['path'],bytes(body))
        r=json.loads((self.root/e['archive_receipt_ref']['path']).read_bytes());r['sha256']=e['warc_ref']['sha256']
        e['archive_receipt_ref']=self.f.write_json('archive.receipt.json',r)
        with self.assertRaises((ValueError,OSError,EOFError)):v2._archive(g,self.root,{})

    def test_base_hash_tampering_and_path_escape_rejected(self):
        self.policy['base_artifact']['manifest_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'INPUT_HASH'):self.execute()
        self.policy['base_artifact']['directory']='../outside'
        with self.assertRaisesRegex(ValueError,'PATH_OUTSIDE_ROOT'):self.execute()

    def test_immutable_output_and_consumer_purpose_guards(self):
        self.execute();before=(self.root/'output_v2/manifest.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'IMMUTABLE_OUTPUT'):self.execute()
        self.assertEqual(before,(self.root/'output_v2/manifest.json').read_bytes())
        for purpose in ['STRICT_RESEARCH','CANONICAL']:
            with self.assertRaisesRegex(ValueError,'NOT_APPROVED'):v2.eligible_fields('output_v2',self.f.time,root=self.root,purpose=purpose)
        for clock in ['2024-06-11','2024-06-11T11:18:31']:
            with self.assertRaises(ValueError):v2.eligible_fields('output_v2',clock,root=self.root)

    def test_rehashed_extra_admission_or_value_cannot_bypass_consumer(self):
        self.execute();f=self.root/'output_v2/field_availability.jsonl';rows=[json.loads(x) for x in f.read_bytes().splitlines()];rows[0]['value']='tampered'
        f.write_text('\n'.join(json.dumps(x) for x in rows),encoding='utf-8')
        mf=self.root/'output_v2/manifest.json';m=json.loads(mf.read_bytes());m['files'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest();mf.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'CONTENT_DIFFERS'):v2.eligible_fields('output_v2','2024-06-12T00:00:00Z',root=self.root)

    def test_offline_build_and_read(self):
        with patch('socket.socket',side_effect=AssertionError('NETWORK_FORBIDDEN')):
            self.execute();self.assertEqual(4,len(v2.eligible_fields('output_v2','2024-06-12T00:00:00Z',root=self.root)))


if __name__ == '__main__':
    unittest.main()
