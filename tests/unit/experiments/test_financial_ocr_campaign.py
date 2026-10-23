import unittest
import json
from pathlib import Path
import tempfile
from delta_t1.experiments.financial_ocr_campaign import budget_check, coordinate
from delta_t1.experiments.financial_history_documents import put
from delta_t1.experiments.financial_selected_ocr import snapshot
from delta_t1.ingestion.cafef_financial import digest, encoded


class OCRCampaignTests(unittest.TestCase):
    def setUp(self):
        self.limits=dict(created_at=100,campaign_pages=12000,per_pdf_pages=40)
        self.batches={'pilot5':dict(created_at=100,page_cap=1000)}

    def record(self,folder,pages,pdf='same',batch='pilot5'):
        return dict(output_root=folder,batch_id=batch,
                    jobs=[dict(id='p'+str(p),pdf_sha256=pdf,pdf_page=p) for p in pages])

    def test_per_pdf_cap_across_multiple_runs(self):
        records=[self.record('one',range(1,28)),self.record('two',range(28,42))]
        with self.assertRaisesRegex(ValueError,'per-PDF'):budget_check(records,{},self.limits,self.batches,200,True)

    def test_same_page_different_ids_cannot_be_reocrd(self):
        records=[self.record('one',[1]),self.record('two',[1])]
        records[1]['jobs'][0]['id']='renamed'
        with self.assertRaisesRegex(ValueError,'duplicate PDF page'):
            budget_check(records,{},self.limits,self.batches,200,True)

    def test_interrupted_reservation_stays_charged(self):
        record=self.record('one',[1,2]);job=record['jobs'][0]
        reservations={('one','p1'):dict(job=job,charged_pages=1)}
        result=budget_check([record],reservations,self.limits,self.batches,200,True)
        self.assertEqual(result['charged_pages'],1)
        self.assertEqual(result['planned_total_pages'],2)
        self.assertEqual(result['pending_pages'],1)

    def test_unknown_or_altered_reservation_rejected(self):
        record=self.record('one',[1]);job=record['jobs'][0]
        for reservations in [{('one','unknown'):dict(job=job,charged_pages=1)},
                             {('one','p1'):dict(job=dict(job,pdf_page=2),charged_pages=1)},
                             {('one','p1'):dict(job=job,charged_pages=0)}]:
            with self.assertRaisesRegex(ValueError,'reservation'):
                budget_check([record],reservations,self.limits,self.batches,200,True)

    def test_batch_and_campaign_caps_are_separate(self):
        records=[self.record('one',[1,2],'a'),self.record('two',[1,2],'b')]
        for limits,batches,error in [(dict(self.limits,campaign_pages=3),self.batches,'campaign'),
                                     (self.limits,{'pilot5':dict(created_at=100,page_cap=3)},'batch')]:
            with self.assertRaisesRegex(ValueError,error):budget_check(records,{},limits,batches,200,True)

    def test_deadline_cannot_be_reset_by_resume_or_new_batch(self):
        record=self.record('one',[1]);job=record['jobs'][0]
        with self.assertRaisesRegex(ValueError,'batch deadline'):
            budget_check([record],{},self.limits,self.batches,100+259201,True)
        charged={('one','p1'):dict(job=job,charged_pages=1)}
        # Completed old work stays verifiable; it is never executed again.
        budget_check([record],charged,self.limits,self.batches,100+259201,False)
        fresh={'pilot5':dict(created_at=90*86400,page_cap=1000)}
        with self.assertRaisesRegex(ValueError,'campaign deadline'):
            budget_check([record],{},self.limits,fresh,100+90*86400+1,True)

    def test_later_config_cannot_forget_imported_reservations(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ['src/delta_t1/experiments/financial_ocr_campaign.py','scripts/financial_ocr_campaign.py']:
                put(root/name,b'fixture code pin')
            limits=dict(self.limits,per_pdf_pages=1)
            def fixture(name,page):
                path='configs/'+name+'.json';out='data/financial/history_selected_ocr_'+name
                job=dict(id='p'+str(page),pdf_sha256='same',pdf_page=page)
                child=dict(jobs=[job],max_ocr_pages=1,campaign_anchor=100,output_root=out)
                put(root/path,child);sha=digest((root/path).read_bytes())
                put(root/out/'contract.json',dict(pins={path:sha}))
                put(root/out/'reservations'/(job['id']+'.json'),dict(job=job,charged_pages=1))
                put(root/out/'pages'/(job['id']+'.json'),dict(job=job,status='OCR_CANDIDATE_ONLY'))
                snapshot(root,root/out,False)
                return dict(config_path=path,config_sha256=sha,batch_id='pilot5')
            first=fixture('one',1)
            def config(path,record):
                put(root/path,dict(version='financial-ocr-campaign-v1',output_root='coordinator',
                                  limits=limits,batches=self.batches,runs=[record]))
            config('first.json',first)
            coordinate(root,'first.json','snapshot')
            before=(root/'data/financial/history_selected_ocr_one/reservations/p1.json').read_bytes()
            second=fixture('two',2)
            config('later.json',second)  # Intentionally omits the first completed run.
            with self.assertRaisesRegex(ValueError,'per-PDF'):
                coordinate(root,'later.json','snapshot')
            self.assertEqual((root/'data/financial/history_selected_ocr_one/reservations/p1.json').read_bytes(),before)
            self.assertEqual(len(list((root/'coordinator/registrations').glob('*.json'))),1)


if __name__=='__main__':unittest.main()
