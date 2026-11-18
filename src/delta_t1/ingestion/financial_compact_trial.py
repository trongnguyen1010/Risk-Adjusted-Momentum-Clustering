"""Compact durable trial journal; reuse existing finite transport reservations."""
import json
import os
from pathlib import Path

from .cafef_financial import digest, now
from .financial_trial_transport import TrialTransport


def read_compact(folder):
    path=Path(folder)/'transport.jsonl'
    raw=path.read_bytes(); lines=raw.splitlines(keepends=True)
    events=[]; previous=None; requests={}; cache={}; consumed=0
    for index,line in enumerate(lines):
        if not line.endswith(b'\n'):
            if index!=len(lines)-1:raise ValueError('torn journal interior')
            break  # Only a final interrupted write is ignored, never appended to.
        event=json.loads(line)
        if event['index']!=len(events)+1 or event['previous_sha256']!=previous:
            raise ValueError('compact journal chain mismatch')
        state=event['state'];detail=event['detail']
        requests.update(state.get('requests',{}));cache.update(state.get('cache',{}))
        if detail.get('request_key') and detail.get('request_snapshot'):
            requests[detail['request_key']]=detail['request_snapshot']
        if event['action']=='CACHE_COMMIT':cache[detail['url']]=detail['record']
        events.append(event);previous=digest(line.rstrip(b'\n'));consumed+=len(line)
    if not events:raise ValueError('compact journal has no durable state')
    state=dict(events[-1]['state'],requests=requests,cache=cache)
    counters=['logical_requests','transport_attempts','downloaded_bytes','reserved_bytes',
              'pdf_download_attempts','text_pages','reserved_text_pages']
    if any(type(state.get(k)) is not int or state[k]<0 for k in counters):raise ValueError('invalid cumulative counters')
    if state['logical_requests']!=len(requests) or state['transport_attempts']!=sum(r['attempts'] for r in requests.values()):
        raise ValueError('compact request counters mismatch')
    return dict(state=state,events=len(events),last_sha256=previous,
        prefix_bytes=consumed,prefix_sha256=digest(raw[:consumed]),torn_tail_bytes=len(raw)-consumed)


class CompactTrialTransport(TrialTransport):
    """Keep TrialTransport hard-stop/deadline/byte/retry logic, changing storage only."""
    def event(self,action,**detail):
        self.state.setdefault('cache',{})
        self.index+=1
        state={k:v for k,v in self.state.items() if k not in ('requests','cache')}
        if action=='START_OR_RESUME':
            state.update(requests=self.state['requests'],cache=self.state['cache'])
        if detail.get('request_key'):
            detail['request_snapshot']=self.state['requests'][detail['request_key']]
        row=dict(index=self.index,at=now(),action=action,previous_sha256=self.previous,
                 state=state,detail=detail)
        raw=json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
        with (self.output/'transport.jsonl').open('ab') as stream:
            stream.write(raw+b'\n');stream.flush();os.fsync(stream.fileno())
        self.previous=digest(raw)
        self.journal.append(dict(index=self.index,action=action))

    def commit_cache(self,url,record):
        self.state['cache'][url]=record
        self.event('CACHE_COMMIT',url=url,record=record)
