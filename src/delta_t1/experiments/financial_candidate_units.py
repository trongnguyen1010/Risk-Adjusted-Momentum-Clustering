"""Prove provider monetary display units, independently of value acceptance/PIT."""
from collections import Counter
from decimal import Decimal
import json

from ..ingestion.cafef_financial import digest, encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read, put
from .financial_history_qa import semantic_field, norm


def verify_display_proof(contract, bodies):
    if (contract.get('version')!='financial-cafef-unit-contract-v1'
            or contract.get('canonical_acceptance_allowed') is not False
            or contract.get('financial_features_allowed') is not False
            or contract['monetary_rule'].get('provider_raw_unit')!='VND'
            or contract['monetary_rule'].get('canonical_candidate_multiplier')!='1'):
        raise ValueError('reference-only raw VND display contract required')
    statements=set()
    for proof in contract['proof']:
        raw=bodies[proof['source_path']]
        if digest(raw)!=proof['source_sha256']:raise ValueError('display source changed')
        text=raw.decode('utf-8')
        if not all(anchor in text for anchor in ['return 1000000','return 1000000000',
                         'num / divisor','Tỷ đồng','Triệu đồng',proof['route']]):
            raise ValueError('unit display rule lacks direct code/label evidence')
        for snippet in proof['snippets']:
            position=snippet['character_offset']
            if text[position:position+len(snippet['anchor'])]!=snippet['anchor'] or snippet['text'] not in text:
                raise ValueError('unit code anchor changed')
        statements.add(proof['statement'])
    if statements!={'CDKT','KQKD','LCTT'}:raise ValueError('three separately proven routes required')


def annotate(candidate, payload):
    result=dict(candidate,provider_raw_unit=None,unit_multiplier=None,unit_value=None,
                unit_status='UNREVIEWED_FIELD_UNIT',accepted=False,pit_ready=False,
                value_acceptance='SOURCE_SEMANTICS_VINTAGE_AND_VALUE_QA_REQUIRED')
    if candidate.get('field')!=semantic_field(candidate):return result
    # EPS and static/ratio fields have a separate UI formatter. Never apply money rules.
    if candidate['field']=='vendor_basic_eps':
        return dict(result,unit_status='SPECIAL_EPS_FORMATTER_REQUIRES_SEPARATE_UNIT_REVIEW')
    template=payload['value']['templace']
    fingerprint=digest(json.dumps(template,ensure_ascii=False,sort_keys=True,default=str).encode())
    if fingerprint!=candidate['template_sha256']:raise ValueError('candidate template identity differs')
    rows=template if candidate['statement']=='KQKD' else [r for g in template if g['code']==candidate['group'] for r in g['data']]
    selected=[r for r in rows if str(r['code'])==candidate['raw_code'] and norm(r['name'])==norm(candidate['label'])]
    if len(selected)!=1:raise ValueError('candidate exact code/label differs from source template')
    if selected[0].get('static') is not False:
        return dict(result,unit_status='STATIC_OR_UNKNOWN_FORMATTER_NOT_MONETARY_PROVEN')
    value=candidate['value']
    if value is not None and (type(value) is bool or not Decimal(str(value)).is_finite()):
        raise ValueError('invalid raw monetary candidate')
    return dict(result,provider_raw_unit='VND',unit_multiplier='1',unit_value=value,
                unit_status='RAW_VND_PROVIDER_DISPLAY_CONTRACT_REFERENCE')


def run(root, config_path, action):
    config=read(inside(root,config_path));pins={};cache={}
    if config.get('version')!='financial-candidate-units-v1':raise ValueError('bounded unit overlay config required')
    def pin(path,expected=None):
        if path not in cache:cache[path]=inside(root,path).read_bytes()
        raw=cache[path];sha=pins.get(path) or digest(raw)
        if expected is not None and sha!=expected:raise ValueError('unit overlay input changed: '+path)
        pins[path]=sha;return raw
    pin(config_path)
    for path in ['src/delta_t1/experiments/financial_candidate_units.py','scripts/financial_candidate_units.py',
                 'src/delta_t1/experiments/financial_history_qa.py']:
        pin(path)
    contract=json.loads(pin(config['unit_contract'],config['unit_contract_sha256']))
    bodies={p['source_path']:pin(p['source_path'],p['source_sha256']) for p in contract['proof']}
    verify_display_proof(contract,bodies)
    source=config['qa_result'];manifest=json.loads(pin(source+'/manifest.json',config['qa_manifest_sha256']))
    mapped=pin(source+'/mapped_candidates.jsonl',manifest['mapped_candidates.jsonl'])
    rows=[]
    for line in mapped.splitlines():
        candidate=json.loads(line)
        payload=json.loads(pin(candidate['source_path'],candidate['source_sha256']))
        rows.append(annotate(candidate,payload))
    summary=dict(status='PARTIAL',mapped_candidate_rows=len(rows),unit_statuses=dict(Counter(r['unit_status'] for r in rows)),
                 numeric_units_proven=sum(r['unit_value'] is not None for r in rows),
                 null_raw_values_preserved=sum(r['value'] is None for r in rows),
                 accepted_facts=0,pit_ready=False,financial_features_allowed=False,
                 meaning='Provider display-unit proof only; no row repair, source priority or vintage/scope acceptance')
    products={'summary.json':encoded(summary),'input-pins.json':encoded(pins),
              'unit-candidates.jsonl':b''.join(encoded(r).replace(b'\n',b'')+b'\n' for r in rows)}
    hashes={n:digest(raw) for n,raw in products.items()};out=inside(root,config['output_root'])/digest(encoded(hashes))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=hashes:raise ValueError('unit overlay manifest changed')
        for name,sha in hashes.items():
            if digest((out/name).read_bytes())!=sha:raise ValueError('unit overlay changed')
    else:
        for name,raw in products.items():put(out/name,raw)
        put(out/'manifest.json',hashes)
    return dict(summary,status='VERIFIED' if action=='verify' else 'PARTIAL',output=out.relative_to(root).as_posix())
