"""Bounded cohort discovery and PDF scale probe, separate from fact acceptance."""
import json
from collections import Counter
from pathlib import Path

from .cafef_financial_trial import verify as verify_trial
from .financial_batch_flow import verify_flow, verify_pins
from ..ingestion.cafef_financial import digest, encoded, immutable_write
from ..ingestion.financial_batch_evidence import inside, seal
from ..ingestion.financial_compact_trial import CompactTrialTransport
from ..ingestion.financial_documents import consolidated_rows, verify_inventory
from ..ingestion.financial_trial_transport import TrialBudgetError
from ..ingestion.sources.base import AccessControlError, RateLimitError

VERSION='financial-scale-probe-v1'
CLOSED=dict(financial_features_allowed=False,research_ready=False,financial_cluster_allowed=False,
            full_universe_allowed=False,unattended_numeric_acceptance_allowed=False,next_100_allowed=False)


def validate(c, members):
    if c.get('version')!=VERSION or any(c.get(k) is not False for k in CLOSED):
        raise ValueError('scale probe contract required')
    if c['symbols']!=[m['ticker'] for m in members] or len(members)!=50:
        raise ValueError('exact frozen50 membership required')
    if len(set(c['pdf_symbols']))!=len(c['pdf_symbols']) or not set(c['pdf_symbols'])<=set(c['symbols']):
        raise ValueError('PDF sample outside cohort')
    if not set(c['prior_year_symbols'])<=set(c['pdf_symbols']):
        raise ValueError('history must belong to PDF sample')
    b=c['budgets']
    bounds={'max_logical_requests':(1,90),'max_transport_attempts':(1,100),
            'max_pdf_download_attempts':(0,20),'max_response_bytes':(1,25000000),
            'max_total_downloaded_bytes':(1,250000000),'max_wall_seconds':(1,3600),
            'max_attempts_per_request':(1,2),'min_seconds_between_transport_attempts':(2,30),
            'timeout_seconds':(1,30)}
    if any(type(b.get(k)) is not int or not lo<=b[k]<=hi for k,(lo,hi) in bounds.items()):
        raise ValueError('bounded acquisition required')
    if not 1<=c['max_documents']<=24 or c['year']!=2025 or c['max_pdf_pages']>250:
        raise ValueError('probe scope exceeded')
    if set(c['approved_hosts'])!={'cafef.vn','cafefnew.mediacdn.vn'}:
        raise ValueError('probe uses CafeF paths only')


def annual_candidates(body, year):
    return [r for r in consolidated_rows(body,year) if r['Quarter']==5]


def acquire(root, config_path, output, network=False, *, factory=CompactTrialTransport):
    root=Path(root).resolve();cfg=inside(root,config_path,'configs')
    c=json.loads(cfg.read_bytes());verify_pins(root,c['input_pins']);verify_pins(root,c['code_pins'])
    trial=inside(root,c['trial_run'],'data');verify_trial(root,c['trial_run'])
    members=json.loads((trial/'plan.json').read_bytes())['members'];validate(c,members)
    seed=inside(root,c['seed_flow'],'data');verify_flow(root,c['seed_flow'])
    prior=json.loads((seed/'results.json').read_bytes())
    cache={}
    for r in prior['listings']+[d['acquisition'] for d in prior['documents']]:
        if r['status']=='COMPLETE':
            cache[r['request']['url']]=r['payload']
    out=inside(root,output,'data');out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'config.json',cfg.read_bytes())
    for path in c['code_pins']:immutable_write(out/'code'/path,inside(root,path).read_bytes())
    transport=factory(root,out,c);records=[];documents=[];stopped=False

    def fetch(url,symbol,year,kind):
        nonlocal stopped
        row=dict(url=url,symbol=symbol,year=year,kind=kind)
        if url in cache:
            p=inside(root,cache[url]['path'],'data');body=p.read_bytes()
            if digest(body)!=cache[url]['sha256']:raise ValueError('seed raw changed')
            row.update(status='CACHED',path=p.relative_to(root).as_posix(),sha256=digest(body),bytes=len(body))
        elif stopped:
            row.update(status='DEFERRED_GLOBAL_STOP');records.append(row);return row,None
        elif not network:
            row.update(status='DEFERRED_OFFLINE');records.append(row);return row,None
        else:
            transport.context=dict(kind=kind,symbol=symbol,year=year)
            try:
                body,status=transport.get(url)
                if kind=='pdf' and not body.startswith(b'%PDF'):raise ValueError('invalid PDF signature')
                p=out/'raw'/(digest(body)+('.pdf' if kind=='pdf' else '.json'))
                if not p.exists():immutable_write(p,body)
                row.update(status='DOWNLOADED',path=p.relative_to(root).as_posix(),sha256=digest(body),bytes=len(body))
            except (AccessControlError,RateLimitError,TrialBudgetError) as e:
                stopped=True;row.update(status='GLOBAL_STOP',error=str(e));records.append(row);return row,None
            except (ValueError,OSError) as e:
                row.update(status='FAILED',error=str(e));records.append(row);return row,None
        records.append(row);return row,body

    discoveries=[]
    jobs=[(s,c['year']) for s in c['symbols']]+[(s,c['year']-1) for s in c['prior_year_symbols']]
    for symbol,year in jobs:
        url=f'https://cafef.vn/du-lieu/Ajax/PageNew/FileBCTC.ashx?Symbol={symbol.lower()}&Type=1&Year={year}'
        receipt,body=fetch(url,symbol,year,'list');rows=[];error=None
        if body is not None:
            try:rows=annual_candidates(body,year)
            except (ValueError,KeyError,TypeError) as e:error=str(e)
        discoveries.append(dict(symbol=symbol,year=year,receipt=receipt,candidates=rows,
            status='INVALID_LISTING' if error else 'FOUND' if rows else 'NO_CONSOLIDATED_ANNUAL_CANDIDATE',
            error=error, publication_status='LISTING_DATE_NOT_ACCEPTED_AS_PUBLICATION'))
    # Preserve all discovered vintages. The sample order bounds downloads only;
    # it never establishes a value/reconciliation priority.
    for symbol in c['pdf_symbols']:
        for d in [x for x in discoveries if x['symbol']==symbol]:
            for row in d['candidates']:
                if len(documents)>=c['max_documents']:break
                receipt,_=fetch(row['Link'],symbol,d['year'],'pdf')
                documents.append(dict(symbol=symbol,year=d['year'],provider_report=row,
                    listing_path=d['receipt'].get('path'),listing_sha256=d['receipt'].get('sha256'),
                    acquisition=receipt, acceptance='UNREVIEWED_EXACT_DOCUMENT_CANDIDATE'))
    result=dict(version=VERSION,trial_run=c['trial_run'],seed_flow=c['seed_flow'],
        discoveries=discoveries,documents=documents,requests=records,
        transport_state=transport.state, discovery_counts=dict(Counter(r['status'] for r in discoveries)),
        acquisition_counts=dict(Counter(r['status'] for r in records)),new_pdf_facts_accepted=0,**CLOSED)
    immutable_write(out/'results.json',encoded(result));seal(out)
    return result


def verify(root,run):
    root=Path(root).resolve();out=inside(root,run,'data');verify_inventory(out)
    c=json.loads((out/'config.json').read_bytes());verify_pins(root,c['input_pins']);verify_pins(root,c['code_pins'])
    r=json.loads((out/'results.json').read_bytes());count=0
    for q in r['requests']:
        if q['status'] in ['DOWNLOADED','CACHED']:
            if digest(inside(root,q['path'],'data').read_bytes())!=q['sha256']:raise ValueError('external raw changed')
            count+=1
    if any(r.get(k) is not False for k in CLOSED):raise ValueError('probe gate violation')
    return dict(status='PASS',verified_raw_records=count,gates_closed=True)
