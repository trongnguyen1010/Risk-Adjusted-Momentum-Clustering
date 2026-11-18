"""Streaming replay of the existing compact journal format; no counter reset."""
import hashlib,json
from pathlib import Path
from .cafef_financial import digest
from .financial_compact_trial import CompactTrialTransport


def read_stream(folder):
    path=Path(folder)/'transport.jsonl';previous=None;requests={};cache={};count=0;consumed=0;torn=0;prefix=hashlib.sha256();last=None
    with path.open('rb') as stream:
        for line in stream:
            if not line.endswith(b'\n'):torn=len(line);break
            event=json.loads(line)
            if event['index']!=count+1 or event['previous_sha256']!=previous:raise ValueError('compact journal chain mismatch')
            state=event['state'];detail=event['detail'];requests.update(state.get('requests',{}));cache.update(state.get('cache',{}))
            if detail.get('request_key') and detail.get('request_snapshot'):requests[detail['request_key']]=detail['request_snapshot']
            if event['action']=='CACHE_COMMIT':cache[detail['url']]=detail['record']
            previous=digest(line.rstrip(b'\n'));prefix.update(line);consumed+=len(line);count+=1;last=state
    if last is None:raise ValueError('compact journal has no durable state')
    state=dict(last,requests=requests,cache=cache)
    for key in ['logical_requests','transport_attempts','downloaded_bytes','reserved_bytes','pdf_download_attempts','text_pages','reserved_text_pages']:
        if type(state.get(key)) is not int or state[key]<0:raise ValueError('invalid cumulative counters')
    if state['logical_requests']!=len(requests) or state['transport_attempts']!=sum(r['attempts'] for r in requests.values()):raise ValueError('compact request counters mismatch')
    return dict(state=state,events=count,last_sha256=previous,prefix_bytes=consumed,prefix_sha256=prefix.hexdigest(),torn_tail_bytes=torn)


class StreamingTransport(CompactTrialTransport):
    def __init__(self,root,output,config,seed,**kwargs):
        output.mkdir(parents=True,exist_ok=True)
        self.old=read_stream(output) if (output/'transport.jsonl').exists() else None
        if self.old and self.old['torn_tail_bytes']:raise ValueError('torn journal requires explicit review')
        CompactTrialTransport.__init__(self,root,output,config,resume_state=self.old['state'] if self.old else seed,**kwargs)

    def event(self,action,**detail):
        if action=='START_OR_RESUME' and self.old:self.index,self.previous=self.old['events'],self.old['last_sha256']
        return super().event(action,**detail)
