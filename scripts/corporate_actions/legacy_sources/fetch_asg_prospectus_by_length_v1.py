"""One HEAD and one full GET for exact ASG prospectus, maximum64MB, strict TLS."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request,build_opener
from urllib.error import HTTPError,URLError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.sources.base import NoRedirect
from delta_t1.ingestion.corporate_action_sources import SourceLimitation,now
from delta_t1.ingestion.corporate_action_target_documents import ScopedPdfTransport
sha=lambda b:hashlib.sha256(b).hexdigest()


def run(output,collect=False):
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    bp=ROOT/'configs/data/corporate_action_dtp_asg_documents_v1.json';fp=ROOT/'configs/data/corporate_action_dtp_asg_followup_v1.json'
    base=json.loads(bp.read_bytes());follow=json.loads(fp.read_bytes());url=base['asg_prospectus_copy']
    output.mkdir(parents=True);head={'url':url,'method':'HEAD','fetched_at':now()};docs=[];receipts=[];status='OFFLINE_PLAN_ONLY'
    if collect:
        opener=build_opener(NoRedirect())
        try:
            try:response=opener.open(Request(url,method='HEAD',headers={'User-Agent':'DeltaT1Research/0.2 (bounded document research)'}),timeout=30)
            except HTTPError as exc:response=exc
            with response:
                head.update(status=response.code,headers={k:response.headers.get(k) for k in ['Content-Type','Content-Length','Location','Retry-After','ETag']})
            if head['status']!=200 or 'pdf' not in (head['headers']['Content-Type'] or '').lower():raise SourceLimitation('HEAD_SOURCE_OR_FORMAT_STOP')
            declared=int(head['headers']['Content-Length'] or '0')
            if not 0<declared<=64000000:raise SourceLimitation('DECLARED_PDF_SIZE_OUTSIDE_64MB_DOCUMENT_CAP')
            head['declared_length']=declared
            follow=follow|{'one_asg_prospectus_max_bytes':max(5000001,declared),'max_requests':1}
            transport=ScopedPdfTransport(output,base,follow);transport.last=__import__('time').monotonic()
            try:
                body,receipt=transport.fetch(url,binary=True)
                if len(body)!=declared:raise SourceLimitation('HEAD_GET_LENGTH_MISMATCH')
                docs.append({'ticker':'ASG','url':url,'status':'PUBLIC_PDF_RECEIVED','receipt':receipt,'size_bytes':len(body),'role':'ISSUER_PROSPECTUS_COPY_ON_MARKET_ARCHIVE'})
                status='PDF_ACQUIRED_REVIEW_PENDING'
            finally:receipts=transport.requests
        except (SourceLimitation,URLError,OSError,ValueError) as exc:
            status='PARTIAL';head['stage_error']=str(exc)
    def dump(name,value):
        with (output/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    dump('head_receipt.json',head);dump('requests.json',receipts);dump('documents.json',docs)
    summary={'status':status,'network_request_attempts':(1 if collect else 0)+len(receipts),'successful_pdf_documents':len(docs),
        'declared_length':head.get('declared_length'),'maximum_document_bytes':64000000,'tls_verification':True,'follow_redirects':False,
        'canonical_build':False,'accepted_fields':0,'prior_partial_files_used_as_evidence':False}
    dump('summary.json',summary)
    code=[Path(__file__),ROOT/'src/delta_t1/ingestion/corporate_action_target_documents.py',ROOT/'src/delta_t1/ingestion/corporate_action_sources.py']
    dump('manifest.json',{'artifact_type':'asg-exact-prospectus-size-declared-acquisition-v1','created_at':now(),
        'inputs_verified':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [bp,fp]},
        'files':{p.relative_to(output).as_posix():sha(p.read_bytes()) for p in output.rglob('*') if p.is_file()},
        'code_hashes':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in code},'canonical_build':False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--collect',action='store_true');a=p.parse_args();run(a.output.resolve(),a.collect)
