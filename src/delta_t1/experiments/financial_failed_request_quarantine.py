"""Prove exhausted HTTP500 requests for deferred acquisition review, never retry."""
import json
from ..ingestion.cafef_financial import digest
from .financial_history_documents import read
from ..ingestion.financial_batch_evidence import inside

def validate_failed_request(receipt,request,event,key):
    if receipt['status']!='FAILED_OR_STOPPED' or receipt['task']['url']!=request['url']:raise ValueError('failed receipt/request mismatch')
    if request['kind']!='structured' or request['attempts']!=2:raise ValueError('only exhausted two-attempt API requests can be deferred')
    detail=event['detail']
    if event['action']!='HTTP_ERROR' or detail['http_status']!=500 or detail['request_key']!=key or detail['request_snapshot']!=request:raise ValueError('only proven terminal HTTP500 can be deferred')
    if receipt.get('record') or receipt.get('reason')!='bounded transport attempts exhausted':raise ValueError('unexpected failed receipt evidence')
    return True

def prove_failed_requests(root,batch_root,result,ledger):
    summary=read(inside(root,result)/'summary.json');expected=summary['task_statuses'].get('FAILED_OR_STOPPED',0)
    # Producer/audit pins receipts; validate exact failed receipt hash before classification.
    manifest=read(inside(root,result)/'manifest.json');path=inside(root,result)/'receipt-pins.json';raw=path.read_bytes()
    if digest(raw)!=manifest['receipt-pins.json']:raise ValueError('receipt index hash differs')
    pins=json.loads(raw);terminal={};journal=inside(root,batch_root)/'network/transport.jsonl'
    with journal.open('rb') as f:
        for line in f:
            e=json.loads(line);key=e['detail'].get('request_key')
            if key and e['action'] in ['HTTP_ERROR','TRANSPORT_ERROR','ATTEMPT_COMPLETE']:
                if e['action']=='ATTEMPT_COMPLETE':terminal.pop(key,None)
                else:terminal[key]=e
    proofs=[]
    for key,event in terminal.items():
        request=ledger['state']['requests'][key];tid=digest(request['url'].encode());rel='receipts/'+tid+'.json';p=inside(root,batch_root)/rel;raw=p.read_bytes()
        if pins.get(rel)!=digest(raw):raise ValueError('failed receipt hash differs')
        receipt=json.loads(raw)
        if receipt['status']!='FAILED_OR_STOPPED':raise ValueError('terminal error without failed receipt')
        validate_failed_request(receipt,request,event,key)
        proofs.append(dict(status='DEFERRED_HTTP500_NOT_RETRIED_NOT_ACCEPTED',request_key=key,request=request,terminal_event=event,receipt=dict(path=batch_root+'/'+rel,sha256=digest(raw))))
    if len(proofs)!=expected:raise ValueError('failed request accounting differs')
    return proofs
