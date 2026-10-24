"""Verify presentation sidecar against every selected frozen source model. No fit."""
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'web/backend'))
from app.repository import TerminalRepository
from app.previews import PreviewRepository,digest


def verify():
    repo=PreviewRepository(TerminalRepository(ROOT/'data/web/delta-intelligence-v1'),ROOT)
    for relative,expected in repo.preview_manifest['sources'].items():
        if digest(ROOT/relative)!=expected:raise ValueError('Preview source pin changed: '+relative)
    source_models={}
    for relative in repo.preview_manifest['sources']:
        if '/models/' in relative:
            value=json.loads((ROOT/relative).read_bytes());source_models[value['kind'],value['date'],value['recipe'],value['k']]=value
    count=0;observations=0
    for kind,variants in repo.variants.items():
        for version,item in variants.items():
            for day in item['snapshots']:
                data=repo.snapshot(kind,day,version);source=source_models[kind,day,item['recipe'],item['k']]
                if [p['cluster'] for p in data['points']]!=source['labels']:raise ValueError('Preview labels do not match the frozen model')
                for profile in data['profiles']:
                    original=next(p for p in source['profiles'] if p['cluster']==profile['cluster'])
                    if profile['quartiles']!=original['quartiles'] or profile['medians']!=original['medians']:raise ValueError('Preview profile mismatch')
                    members=[p for p in data['points'] if p['cluster']==profile['cluster']]
                    for field,value in profile['means'].items():
                        expected=math.fsum(p['features'][field] for p in members)/len(members)
                        if not math.isclose(value,expected,rel_tol=1e-10,abs_tol=1e-10):raise ValueError('Presentation mean mismatch: '+field)
                for field,value in source['metrics'].items():
                    if data['snapshot']['metrics'][field]!=value:raise ValueError('Saved quality metric changed: '+field)
                count+=1;observations+=len(data['points'])
    if count!=repo.preview_manifest['models']:raise ValueError('Preview model count mismatch')
    return dict(status='PASS_PREVIEW_SOURCE_REPLAY',models=count,observations=observations,presentation_revision=repo.revision,baseline_unchanged=True,promotion_status='NOT_PROMOTED',model_fits=0)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
