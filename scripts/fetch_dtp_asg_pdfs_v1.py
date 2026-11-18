"""Fetch exactly three scoped public PDFs after a pinned saved-page diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from delta_t1.ingestion.corporate_action_target_documents import validate_saved_public_article,ScopedPdfTransport
from delta_t1.ingestion.corporate_action_sources import SourceLimitation,now
from collect_dtp_asg_documents_v1 import safe
sha=lambda b:hashlib.sha256(b).hexdigest()


def run(output,collect=False):
    if output.exists():raise FileExistsError('REFUSE_OVERWRITE')
    inputs={}
    def pin(path,expected=None):
        body=path.read_bytes();digest=sha(body)
        if expected and digest!=expected:raise ValueError('INPUT_HASH_MISMATCH')
        inputs[path.relative_to(ROOT).as_posix()]=digest
        return body
    c=json.loads(pin(ROOT/'configs/data/corporate_action_dtp_asg_followup_v1.json'))
    prior=ROOT/'tmp/ca_dtp_asg_documents_20261102_v2'
    pm=json.loads(pin(prior/'manifest.json',c['prior_acquisition_manifest_sha256']))
    rel='configs/data/corporate_action_dtp_asg_documents_v1.json';base=json.loads(pin(ROOT/rel,pm['inputs_verified'][rel]))
    body=pin(prior/'raw/response-0001.bin',c['dtp_saved_page_sha256'])
    diagnostic=validate_saved_public_article(body,base,c)
    # Source response was HTTP200 with full article. All six keywords are only
    # in three pinned CF7 script tags; no challenge, script or form is executed.
    docs=[];output.mkdir(parents=True);transport=ScopedPdfTransport(output,base,c);stops=set()
    urls=sorted({l['url'] for l in diagnostic['public_pdf_links']})+[base['asg_prospectus_copy']]
    if collect:
        for url in urls:
            ticker='ASG' if url==base['asg_prospectus_copy'] else 'DTP';host=urlsplit(url).hostname
            if host in stops:
                docs.append({'ticker':ticker,'url':url,'status':'SKIPPED_HOST_STOP'});continue
            try:
                pdf,receipt=transport.fetch(url,binary=True)
                docs.append({'ticker':ticker,'url':url,'status':'PUBLIC_PDF_RECEIVED','receipt':receipt,
                    'role':'ISSUER_PROSPECTUS_COPY_ON_MARKET_ARCHIVE' if ticker=='ASG' else 'ISSUER_DOCUMENT_COPY_ON_BROKER_DISCLOSURE','size_bytes':len(pdf)})
            except SourceLimitation as exc:
                stops.add(host);docs.append({'ticker':ticker,'url':url,'status':'SOURCE_STOP','reason':str(exc)})
    def dump(name,value):
        with (output/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    dump('saved_article_diagnostic.json',diagnostic);dump('requests.json',transport.requests);dump('documents.json',docs)
    summary={'stage':c['stage'],'status':'PDFS_ACQUIRED_REVIEW_PENDING' if any(d['status']=='PUBLIC_PDF_RECEIVED' for d in docs) else 'PARTIAL',
        'network_request_attempts':len(transport.requests),'successful_pdf_documents':sum(d['status']=='PUBLIC_PDF_RECEIVED' for d in docs),
        'stopped_hosts':sorted(stops),'tls_verification':True,'follow_redirects':False,'page_retries':0,'captcha_executions':0,
        'one_asg_prospectus_max_bytes':c['one_asg_prospectus_max_bytes'],'other_pdf_max_bytes':c['normal_pdf_max_bytes'],
        'prior_truncated_pdf_used_as_evidence':False,'canonical_build':False,'accepted_fields':0,'hnx_network_requests':0}
    dump('summary.json',summary)
    for name,digest in inputs.items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError('INPUT_CHANGED')
    code=[Path(__file__),ROOT/'scripts/collect_dtp_asg_documents_v1.py',ROOT/'src/delta_t1/ingestion/corporate_action_target_documents.py',ROOT/'src/delta_t1/ingestion/corporate_action_sources.py']
    dump('manifest.json',{'artifact_type':'dtp-asg-scoped-pdf-followup-v1','created_at':now(),'inputs_verified':inputs,
        'files':{p.relative_to(output).as_posix():sha(p.read_bytes()) for p in output.rglob('*') if p.is_file()},
        'code_hashes':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in code},'network_request_attempts':len(transport.requests),'canonical_build':False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--collect',action='store_true')
    a=p.parse_args();run(a.output.resolve(),a.collect)
