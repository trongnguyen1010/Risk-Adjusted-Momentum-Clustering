"""Failure-mode tests for history acquisition, pagination, raw provenance and latches."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from delta_t1.experiments.financial_history_pit import (
    PILOT, tasks, page_state, parse_task, HistoryTransport, audit_boundaries,
    cache_inventory, acquire, build_report, verify_report, write)
from delta_t1.ingestion.cafef_financial import digest, encoded
from delta_t1.ingestion.financial_compact_trial import read_compact
from delta_t1.ingestion.sources.base import AccessControlError, RateLimitError


def config():
    return dict(symbols=PILOT,years=list(range(2013,2026)),cache_epoch='history-test',
        approved_hosts=['apiweb.cafef.vn'],boundary_roots=['legacy'],cache_receipt_roots=['legacy'],
        budgets=dict(max_logical_requests=5,max_transport_attempts=10,max_pdf_download_attempts=0,
            max_response_bytes=10000,max_total_downloaded_bytes=100000,max_wall_seconds=259200,
            max_attempts_per_request=2,timeout_seconds=20,min_seconds_between_transport_attempts=2))


class Response:
    status=200
    def __init__(self,body=b'{}'):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read1(self,n):
        data,self.body=self.body[:n],self.body[n:]
        return data
    read=read1


class Opener:
    def __init__(self,code=None):self.calls=0;self.code=code
    def open(self,*args,**kwargs):
        self.calls+=1
        if self.code:raise HTTPError('https://apiweb.cafef.vn/test',self.code,'fixture',{},None)
        return Response()


def report_payload(year=2025,raw='0.25',group='NV',symbol='BRC'):
    return ('{"isSuccess":true,"value":{"templace":[{"code":"'+group+'",'
        '"data":[{"code":"320","name":"Debt"}]}],"data":[{"code":"'+group+'",'
        '"data":[{"symbol":"'+symbol+'","year":'+str(year)+',"quater":0,'
        '"time":"'+str(year)+'","data":[{"code":"320","value":'+raw+'}]}]}]}}').encode()


class HistorySemantics(unittest.TestCase):
    def test_task_identity_and_group_paging(self):
        ts=tasks(config())
        self.assertEqual(len({t['id'] for t in ts}),len(ts))
        self.assertEqual({t['mode'] for t in ts},{'NAM','QUY','LUYKE','CATALOGUE'})
        self.assertTrue(all(t['page']>=1 for t in ts))
        self.assertEqual(len(ts),1100)

    def test_page_repeat_and_nonprogress(self):
        t=dict(kind='REPORT',statement='CDKT',mode='NAM')
        rows=[dict(year=2025,quarter=0,provider_type='HK')]
        first=page_state(t,rows,[])
        self.assertFalse(first['stop'])
        self.assertEqual(page_state(t,rows,[first])['reason'],'PAGINATION_NON_PROGRESS')
        older=page_state(t,[dict(year=2012,quarter=0)], [first])
        self.assertEqual(older['reason'],'TARGET_BOUNDARY_REACHED')

    def test_quarter_boundary_and_empty_are_different(self):
        t=dict(kind='REPORT',statement='LCTT',mode='QUY')
        self.assertTrue(page_state(t,[dict(year=2013,quarter=1)],[])['stop'])
        self.assertFalse(page_state(t,[dict(year=2013,quarter=2)],[])['stop'])
        self.assertEqual(page_state(t,[],[])['reason'],'SOURCE_EXHAUSTED')

    def test_decimal_zero_and_unknown_unit_stay_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'raw.json';p.write_bytes(report_payload())
            t=dict(symbol='BRC',statement='CDKT',mode='NAM',group='NV',kind='REPORT')
            record=dict(path='raw.json',sha256=digest(p.read_bytes()))
            rows=parse_task(root,t,record)
            self.assertEqual(rows[0]['value'],'0.25')
            self.assertFalse(rows[0]['accepted']);self.assertFalse(rows[0]['pit_ready'])
            self.assertEqual(rows[0]['unit_status'],'FIELD_UNIT_REVIEW_REQUIRED')
            encoded(rows)  # Decimal must remain JSON serializable without float conversion.
            p.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'hash'):parse_task(root,t,record)

    def test_group_not_in_response_does_not_borrow_other_group(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'raw.json';p.write_bytes(report_payload(group='TN'))
            t=dict(symbol='BRC',statement='CDKT',mode='NAM',group='NV',kind='REPORT')
            self.assertEqual(parse_task(root,t,dict(path='raw.json',sha256=digest(p.read_bytes()))),[])

    def test_local_cache_cannot_hide_tampered_body(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'legacy').mkdir()
            (root/'raw.json').write_bytes(b'changed')
            write(root/'legacy/x.receipt.json',dict(http_status=200,sha256=digest(b'original'),path='raw.json',
                url='https://apiweb.cafef.vn/api/v2/BCTC/GetReportCDKT'))
            self.assertEqual(len(cache_inventory(root,config())['errors']),1)


class HistoryDurability(unittest.TestCase):
    def transport(self,root,opener,utc=100):
        return HistoryTransport(root,root,config(),opener=opener,sleep=lambda n:None,utc=lambda:utc)

    def test_resume_preserves_attempts_and_created_at(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.transport(root,Opener()).get('https://apiweb.cafef.vn/test')
            t=self.transport(root,Opener(),utc=110)
            self.assertEqual(t.state['created_at'],100)
            self.assertEqual(t.state['transport_attempts'],1)
            self.assertEqual(read_compact(root)['state']['downloaded_bytes'],2)

    def test_boundary_never_retried_after_restart(self):
        for status in [401,403,429]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as d:
                root=Path(d);o=Opener(status)
                with self.assertRaises((AccessControlError,RateLimitError)):
                    self.transport(root,o).get('https://apiweb.cafef.vn/test')
                self.assertEqual(o.calls,1)
                o2=Opener();t=self.transport(root,o2)
                with self.assertRaises(AccessControlError):t.get('https://apiweb.cafef.vn/another')
                self.assertEqual(o2.calls,0)

    def test_imported_latch_is_host_scoped_and_hashed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);legacy=root/'legacy';legacy.mkdir()
            with self.assertRaises(AccessControlError):
                self.transport(legacy,Opener(403)).get('https://apiweb.cafef.vn/test')
            audit=audit_boundaries(root,config(),root/'new')
            self.assertEqual(audit['blocked_hosts'],['apiweb.cafef.vn'])
            self.assertFalse(audit['errors'])

    def test_torn_import_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'legacy').mkdir();(root/'legacy/transport.jsonl').write_bytes(b'{')
            self.assertTrue(audit_boundaries(root,config(),root/'new')['errors'])

    def test_history_resume_rejects_torn_tail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.transport(root,Opener())
            with (root/'transport.jsonl').open('ab') as stream:stream.write(b'{"torn":')
            with self.assertRaisesRegex(ValueError,'torn'):self.transport(root,Opener())

    def test_report_jsonl_and_baseline_are_separate_and_raw_tamper_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);run=root/'run';run.mkdir();(run/'receipts').mkdir();(run/'reports').mkdir()
            (run/'network').mkdir();(root/'baseline').mkdir()
            baseline=b'symbol,family,value\nBRC,EPS,1\n';(root/'baseline/metrics.csv').write_bytes(baseline)
            p=root/'raw.json';p.write_bytes(report_payload())
            task=next(t for t in tasks(config()) if t['symbol']=='BRC' and t['statement']=='CDKT' and t['group']=='NV' and t['mode']=='NAM')
            write(run/'task-plan.json',[task])
            write(run/'receipts'/ (task['id']+'.json'),dict(status='CACHED',task=task,
                record=dict(path='raw.json',sha256=digest(p.read_bytes()))))
            c=dict(config(),baseline_result='baseline')
            result=build_report(root,c,run);out=root/result['output']
            lines=(out/'candidates.jsonl').read_text(encoding='utf-8').splitlines()
            self.assertEqual(len(lines),1);self.assertEqual(json.loads(lines[0])['value'],'0.25')
            self.assertEqual((out/'metrics.csv').read_bytes(),baseline)
            self.assertEqual(verify_report(root,run,result['output'])['status'],'VERIFIED')
            p.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'raw cache changed'):verify_report(root,run,result['output'])

    def test_offline_cache_and_pending_parent_do_not_call_network(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);run=root/'run';run.mkdir();(run/'receipts').mkdir();(run/'network').mkdir()
            ts=tasks(config());ts=[t for t in ts if t['symbol']=='BRC' and t['statement']=='CDKT' and t['group']=='NV' and t['mode']=='NAM'][:2]
            write(run/'task-plan.json',ts);write(run/'cache-index.json',dict(urls={},errors=[]))
            write(run/'source-boundaries.json',dict(blocked_hosts=[],errors=[]))
            import time
            write(run/'contract.json',dict(created_at=time.time()))
            def forbidden(*args,**kwargs):raise AssertionError('offline called network')
            result=acquire(root,config(),run,False,25,transport_factory=forbidden)
            self.assertEqual(result['network_logical_requests_this_call'],0)
            self.assertEqual(list((run/'receipts').iterdir()),[])


if __name__=='__main__':unittest.main()
