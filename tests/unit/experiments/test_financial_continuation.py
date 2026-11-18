import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from delta_t1.experiments import financial_continuation as n
from delta_t1.experiments import financial_user_workflow as f
from delta_t1.ingestion.financial_compact_trial import CompactTrialTransport
from tests.unit.experiments import test_financial_user_workflow as fixtures


class Pdf(io.BytesIO):
    status=200
    read1=io.BytesIO.read


class Opener:
    def __init__(self, status=200): self.calls=0; self.status=status
    def open(self, request, timeout):
        self.calls+=1
        if self.status!=200: raise HTTPError(request.full_url,self.status,'test',{},None)
        return Pdf(b'%PDF-recovered fixture')


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.branch=patch.object(n,'branch',return_value='research/financial-data')
        self.branch.start(); self.addCleanup(self.branch.stop)
        fixtures.UserWorkflowTests.fixture(self)
        for name in ['src/delta_t1/experiments/financial_continuation.py',
                     'scripts/financial_continue.py', 'scripts/financial_continue.ps1']:
            f.write_new(self.root/name,b'# frozen fixture code\n')
        _,c,_=f.open_run(self.root,'data/user')
        f.acquire(self.root,'data/user',False,300)
        job=dict(kind='pdf',symbol='S001',year=2024,url='https://cafefnew.mediacdn.vn/fail.pdf',
            listing_name='consolidated annual',status='FAILED',error='bounded transport attempts exhausted')
        job['job_key']=f.job_key(job)
        receipt=Path('data/user/receipts')/(job['job_key']+'-0123')/'receipt.json'
        f.write_new(self.root/receipt,f.encoded(job)); f.seal((self.root/receipt).parent)
        self.d=dict(version=n.VERSION,expected_branch='research/financial-data',parent_run='data/user',
            run='data/next',successor_config='configs/next.json',recovery_job_key=job['job_key'],
            recovery_receipt=receipt.as_posix(),recovery_receipt_sha256=f.digest(f.encoded(job)),
            max_recovery_attempts=1,**f.CLOSED)
        self.path='configs/continue.json'
        f.write_new(self.root/self.path,f.encoded(self.d))

    def tx(self, opener):
        return lambda root,out,c,state: CompactTrialTransport(root,out,c,state,opener=opener,sleep=lambda _:None)

    def prepare(self): return n.prepare(self.root,self.path)

    def test_prepare_and_cache_replay_preserve_parent_and_gates(self):
        old={p:p.read_bytes() for p in (self.root/'data/user').rglob('*') if p.is_file()}
        self.prepare()
        for p,b in old.items(): self.assertEqual(p.read_bytes(),b)
        opener=Opener()
        self.assertEqual(f.acquire(self.root,'data/next',False,300,self.tx(opener))['completed_jobs'],0)
        self.assertEqual(opener.calls,0)
        report=f.report(self.root,'data/next')
        self.assertEqual(report['available_pdf_vintages'],1)
        self.assertEqual(report['production_ready_symbols'],0)
        self.assertFalse(report['financial_cluster_allowed'])
        with self.assertRaises(ValueError): self.prepare()

    def test_recovery_is_one_shot_and_keeps_failed_parent_receipt(self):
        self.prepare(); opener=Opener()
        r=n.recover(self.root,self.path,True,self.tx(opener))
        self.assertEqual(r['status'],'DOWNLOADED'); self.assertEqual(r['counters']['pdf_download_attempts'],1)
        self.assertEqual(f.receipts(self.root/'data/next')[self.d['recovery_job_key']]['status'],'DOWNLOADED')
        self.assertEqual(f.load(self.root/self.d['recovery_receipt'])['status'],'FAILED')
        self.assertEqual(n.recover(self.root,self.path,True,self.tx(opener))['status'],'RECOVERY_ALREADY_RESERVED')
        self.assertEqual(opener.calls,1)
        self.assertEqual(f.verify(self.root,'data/next')['status'],'VERIFIED')

    def test_offline_plan_does_not_consume_retry(self):
        self.prepare(); opener=Opener()
        self.assertEqual(n.recover(self.root,self.path,False,self.tx(opener))['status'],'RECOVERY_PLANNED')
        self.assertEqual(opener.calls,0)
        self.assertEqual(n.recover(self.root,self.path,True,self.tx(opener))['status'],'DOWNLOADED')

    def test_boundary_retry_and_global_budget_remain_latched(self):
        self.prepare(); opener=Opener(403)
        self.assertEqual(n.recover(self.root,self.path,True,self.tx(opener))['status'],'GLOBAL_STOP')
        self.assertTrue(f.transport_state(self.root/'data/next')['boundary'])
        n.recover(self.root,self.path,True,self.tx(opener))
        f.acquire(self.root,'data/next',True,1,self.tx(opener))
        self.assertEqual(opener.calls,1)

    def test_inherited_deadline_and_counters_are_not_reset(self):
        _,c,_=f.open_run(self.root,'data/user')
        out=self.root/'data/user/transport/0001'; out.mkdir(parents=True)
        tx=CompactTrialTransport(self.root,out,c,utc=lambda:1)
        # Reserve conservative costs without I/O; even an expired parent may be
        # snapshotted offline, but its recovery cannot get a fresh deadline.
        tx.state.update(logical_requests=1,transport_attempts=1,pdf_download_attempts=1,
            requests={'old':dict(attempts=1)},reserved_bytes=100)
        tx.event('START_OR_RESUME')
        self.prepare(); state=f.transport_state(self.root/'data/next')
        self.assertEqual(state['created_at'],1); self.assertEqual(state['reserved_bytes'],100)
        opener=Opener()
        r=n.recover(self.root,self.path,True,self.tx(opener))
        self.assertEqual(r['status'],'GLOBAL_STOP'); self.assertEqual(opener.calls,0)
        self.assertEqual(r['counters']['stop_reason'],'WALL_TIME_CAP')

    def test_branch_and_receipt_drift_fail_before_network(self):
        self.branch.stop()
        with patch.object(n,'branch',return_value='wrong'):
            with self.assertRaisesRegex(ValueError,'branch mismatch'): self.prepare()
        self.branch.start()
        (self.root/self.d['recovery_receipt']).write_bytes(b'{}')
        with self.assertRaises(ValueError): self.prepare()

    def test_http404_is_not_eligible_for_recovery(self):
        p=self.root/self.d['recovery_receipt']; job=f.load(p)
        # Replace fixture and seal before preparation; real evidence is immutable.
        job['error']='HTTP 404; no redirect/workaround'
        p.write_bytes(f.encoded(job)); (p.parent/'manifest.json').unlink(); f.seal(p.parent)
        self.d['recovery_receipt_sha256']=f.digest(p.read_bytes())
        (self.root/self.path).write_bytes(f.encoded(self.d))
        with self.assertRaisesRegex(ValueError,'transient'): self.prepare()

    def test_crash_reservation_cannot_create_a_second_recovery_epoch(self):
        self.prepare()
        job=f.load(self.root/self.d['recovery_receipt'])
        f.write_new(self.root/'data/next/recovery/crashed/request.json',f.encoded(dict(
            job=job,parent_sha256=self.d['recovery_receipt_sha256'])))
        opener=Opener()
        self.assertEqual(n.recover(self.root,self.path,True,self.tx(opener))['status'],'RECOVERY_ALREADY_RESERVED')
        self.assertEqual(opener.calls,0)

    def test_crash_after_committed_recovery_finalizes_without_second_download(self):
        self.prepare(); opener=Opener()
        with patch.object(n,'publish_recovery',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError): n.recover(self.root,self.path,True,self.tx(opener))
        self.assertEqual(f.receipts(self.root/'data/next')[self.d['recovery_job_key']]['status'],'FAILED')
        n.recover(self.root,self.path,True,self.tx(opener))
        self.assertEqual(f.receipts(self.root/'data/next')[self.d['recovery_job_key']]['status'],'DOWNLOADED')
        self.assertEqual(opener.calls,1)

    def test_pdf_attempt_cap_survives_continuation_without_new_io(self):
        _,c,_=f.open_run(self.root,'data/user')
        out=self.root/'data/user/transport/0001'; out.mkdir(parents=True)
        tx=CompactTrialTransport(self.root,out,c)
        tx.state['pdf_download_attempts']=1
        tx.event('START_OR_RESUME')
        self.prepare(); opener=Opener()
        r=n.recover(self.root,self.path,True,self.tx(opener))
        self.assertEqual(r['status'],'GLOBAL_STOP')
        self.assertEqual(r['counters']['stop_reason'],'PDF_ATTEMPT_CAP')
        self.assertEqual(opener.calls,0)

    def test_exact_hash_scope_and_per_document_failure_are_exposed(self):
        self.prepare(); run,c,_=f.open_run(self.root,'data/next')
        sha=f.document_index(self.root,run,c)[0]['sha256']
        def fake(*args):
            docs=f.document_index(self.root,run,c)
            self.assertEqual([x['sha256'] for x in docs],[sha])
            out=run/'extract/fake'
            f.write_new(out/'result.json',f.encoded(dict(status='EXTRACTION_FAILED',pages=[])))
            f.seal(out)
            return dict(status='BATCH_COMPLETE')
        with patch.object(f,'extract',side_effect=fake):
            self.assertEqual(n.extract(self.root,self.path,sha)['status'],'EXTRACTION_FAILED')
        with self.assertRaises(ValueError): n.extract(self.root,self.path,'unknown')


if __name__=='__main__': unittest.main()
