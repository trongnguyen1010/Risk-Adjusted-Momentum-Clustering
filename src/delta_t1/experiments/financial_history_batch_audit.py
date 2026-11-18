"""F3 independent API-pass audit, stratified by current provider exchange."""
import json
from hashlib import sha256

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put
from .financial_history_audit_plan import choose_samples
from .financial_history_qa import csv_body


def select_issuers(profiles,excluded,seed):
    if len({r['registry_id'] for r in profiles})!=len(profiles) or len({r['symbol'] for r in profiles})!=len(profiles):
        raise ValueError('audit profile identity ambiguous')
    selected=[]
    for exchange in ['HOSE','HNX','UPCOM']:
        pool=[r for r in profiles if r['exchange']==exchange and r['proposed_company_type']=='Regular' and r['symbol'] not in excluded]
        if not pool:raise ValueError('no independent regular issuer in required exchange stratum')
        selected.append(min(pool,key=lambda r:sha256((seed+'|issuer|'+exchange+'|'+r['registry_id']).encode()).hexdigest()))
    return selected


def run(root,config_path,action):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-history-batch-audit-v1' or c['seed']!='financial-history-F3-independent-audit-v1':
        raise ValueError('frozen F3 independent sampling contract required')
    def pin(p,expected=None):
        raw=inside(root,p).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('F3 audit input differs: '+p)
        pins[p]=sha;return raw
    for p in [config_path,'src/delta_t1/experiments/financial_history_batch_audit.py','scripts/financial_history_batch_audit.py',
              'src/delta_t1/experiments/financial_history_audit_plan.py']:pin(p)
    qa=c['qa_result'];m=json.loads(pin(qa+'/manifest.json',c['qa_manifest_sha256']))
    candidates=[json.loads(line) for line in pin(qa+'/mapped_candidates.jsonl',m['mapped_candidates.jsonl']).splitlines()]
    checks=json.loads(pin(qa+'/arithmetic.json',m['arithmetic.json']));shifts=json.loads(pin(qa+'/displacements.json',m['displacements.json']))
    pp=c['profiles_result'];pm=json.loads(pin(pp+'/manifest.json',c['profiles_manifest_sha256']))
    profiles=json.loads(pin(pp+'/profiles.json',pm['profiles.json']))
    exclusions=c['excluded_previously_reviewed_issuers'];excluded=[]
    for item in exclusions:
        review=json.loads(pin(item['path'],item['sha256']))
        if not any(f['symbol']==item['symbol'] for f in review['facts']):raise ValueError('audit exclusion lacks pre-existing review evidence')
        excluded.append(item['symbol'])
    chosen=select_issuers(profiles,excluded,c['seed'])
    samples,clean=choose_samples(candidates,checks,shifts,[r['symbol'] for r in chosen],c['seed'])
    by_symbol={r['symbol']:r for r in chosen}
    for sample in samples:
        profile=by_symbol[sample['symbol']]
        sample.update(registry_id=profile['registry_id'],current_provider_exchange=profile['exchange'],
            selection_scope='CURRENT_PROFILE_ENGINEERING_STRATUM_NOT_HISTORICAL_EXCHANGE_MEMBERSHIP',
            historical_identity_ready=False,selection_by_pdf_availability=False)
        for path,sha in sample.get('source_pins',{}).items():pin(path,sha)
    summary=dict(status='SEEDED_TARGETS_PENDING_DOCUMENT_REVIEW',seed=c['seed'],selected_issuers=[r['symbol'] for r in chosen],
        current_exchange_strata=[r['exchange'] for r in chosen],qualified_clean_cohorts_in_selected_issuers=clean,
        required_document_reviews=len(samples),selected_reviewable_periods=sum('id' in s for s in samples),
        blueprint_completed_reviews=0,completion_source='FUTURE_VERSIONED_REVIEW_RESULT_NOT_THIS_STATIC_BLUEPRINT',
        excluded_previously_reviewed_issuers=excluded,
        unsupported_regular_mapping_issuer_backlog=[r['symbol'] for r in profiles if r['proposed_company_type']!='Regular'],
        reselection_policy='DO_NOT_REPLACE_TARGETS_BECAUSE_PUBLIC_PDF_IS_HARD_TO_FIND',next50_allowed=False,
        financial_features_allowed=False,research_ready=False)
    products={'summary.json':encoded(summary),'audit-tasks.json':encoded(samples),'audit-tasks.csv':csv_body(samples),'input-pins.json':encoded(pins)}
    m={n:digest(raw) for n,raw in products.items()};out=inside(root,c['output_root'])/digest(encoded(m))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=m:raise ValueError('audit blueprint manifest differs')
        for n,sha in m.items():
            if digest((out/n).read_bytes())!=sha:raise ValueError('audit blueprint changed')
    else:
        for n,raw in products.items():put(out/n,raw)
        put(out/'manifest.json',m)
    return dict(summary,output=out.relative_to(root).as_posix())
