"""Independent no-fit replay: source pins, transforms, nearest centroids and scorecards."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def verify(root,run):
    import numpy as np
    from scipy.special import boxcox1p,ndtri
    root=Path(root).resolve();run=Path(run).resolve()
    if not run.is_relative_to(root):raise ValueError('Result outside project')
    for name,expected in json.loads((run/'manifest.json').read_bytes()).items():
        path=(run/name).resolve()
        if not path.is_relative_to(run) or sha(path)!=expected:raise ValueError('Result hash mismatch: '+name)
    for relative,expected in json.loads((run/'input-pins.json').read_bytes()).items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or sha(path)!=expected:raise ValueError('Input pin mismatch: '+relative)
    connection=sqlite3.connect((root/'data/web/delta-intelligence-v1/terminal.sqlite').as_uri()+'?mode=ro',uri=True)
    connection.row_factory=sqlite3.Row
    groups={};transforms={};checked=0;sampled_silhouettes=0
    for path in sorted((run/'models').glob('*.json')):
        model=json.loads(path.read_bytes());key=model['kind'],model['date']
        if key not in groups:
            groups[key]=[dict(r) for r in connection.execute('SELECT * FROM observations WHERE kind=? AND date=? ORDER BY ticker',key)]
        cohort=groups[key];fields=model['feature_order']
        raw=np.array([[json.loads(r['features'])[f] for f in fields] for r in cohort])
        if model['symbols']!=[r['ticker'] for r in cohort] or model['security_ids']!=[r['security_id'] for r in cohort]:raise ValueError('Cohort order/identity changed')
        transform=model['transform']
        if transform not in transforms:
            spec=json.loads((run/transform).read_bytes())
            if fields!=spec['feature_order']:raise ValueError('Feature order mismatch')
            if hashlib.sha256(json.dumps([(r['ticker'],r['security_id']) for r in cohort]).encode()).hexdigest()!=spec['cohort_sha256']:raise ValueError('Transform cohort mismatch')
            if spec['recipe']=='P1':
                values=np.zeros_like(raw,dtype=float)
                for j,lam in enumerate(spec['lambdas']):
                    if spec['constant'][j]:continue
                    positive=raw[:,j]>=0
                    values[positive,j]=boxcox1p(raw[positive,j],lam)
                    values[~positive,j]=-boxcox1p(-raw[~positive,j],2-lam)
                values=(values-spec['center'])/spec['scale']
            elif spec['recipe']=='P3':
                values=np.sign(raw)*np.log1p(np.abs(raw)/spec['nonzero_scales'])
                values=(values-spec['center'])/spec['scale']
            elif spec['recipe']=='P2':
                quantiles=np.array(spec['quantiles']);references=np.array(spec['references']);values=np.empty_like(raw,dtype=float)
                for j in range(raw.shape[1]):
                    column=raw[:,j]
                    uniform=.5*(np.interp(column,quantiles[:,j],references)-np.interp(-column,-quantiles[::-1,j],-references[::-1]))
                    # sklearn's documented symmetric duplicate-knot interpolation and bounded normal tails.
                    uniform[column-1e-7<quantiles[0,j]]=0
                    uniform[column+1e-7>quantiles[-1,j]]=1
                    lower=ndtri(1e-7-np.spacing(1));upper=ndtri(1-(1e-7-np.spacing(1)))
                    values[:,j]=np.clip(ndtri(uniform),lower,upper)
            else:raise ValueError('Unknown transform')
            values*=spec['weights']
            if model['kind']=='combined':
                np.testing.assert_allclose([np.var(values[:,:8],axis=0).sum(),np.var(values[:,8:],axis=0).sum()],[.5,.5],rtol=1e-7,atol=1e-8)
            transforms[transform]=values
        x=transforms[transform];labels=np.array(model['labels']);centers=np.array(model['centroids'])
        distances=((x[:,None,:]-centers[None,:,:])**2).sum(axis=2)
        np.testing.assert_allclose(distances[np.arange(len(x)),labels],distances.min(axis=1),rtol=1e-8,atol=1e-8)
        counts=Counter(int(x) for x in labels);metrics=model['metrics']
        if {str(k):v for k,v in counts.items()}!=metrics['sizes'] or sum(counts.values())!=metrics['n']:raise ValueError('Size mismatch')
        np.testing.assert_allclose(float(distances[np.arange(len(x)),labels].sum()),metrics['inertia'],rtol=1e-7,atol=1e-7)
        samples=np.array(metrics['silhouette_distribution'])
        np.testing.assert_allclose(samples.mean(),metrics['silhouette'],atol=1e-10)
        for i in np.linspace(0,len(x)-1,min(8,len(x)),dtype=int):
            norms=np.linalg.norm(x-x[i],axis=1)
            own=labels==labels[i]
            a=norms[own].sum()/(own.sum()-1) if own.sum()>1 else 0.
            b=min(norms[labels==cluster].mean() for cluster in counts if cluster!=labels[i])
            silhouette=(b-a)/max(a,b) if own.sum()>1 and max(a,b)>0 else 0.
            np.testing.assert_allclose(silhouette,samples[i],atol=1e-7,rtol=1e-7);sampled_silhouettes+=1
        for profile in model['profiles']:
            selected=raw[labels==profile['cluster']]
            if len(selected)!=profile['size']:raise ValueError('Profile count mismatch')
            for j,field in enumerate(fields):np.testing.assert_allclose(np.quantile(selected[:,j],[0,.25,.5,.75,1]),profile['quartiles'][field],rtol=1e-10,atol=1e-10)
        checked+=1
    connection.close()
    summary=json.loads((run/'summary.json').read_bytes())
    if checked!=summary['saved_models'] or summary['fits']['screening']>315 or summary['fits']['seed_stability']>270:raise ValueError('Fit count/cap mismatch')
    return dict(status='PASS_INDEPENDENT_NO_FIT_REPLAY',models_checked=checked,transforms_checked=len(transforms),sampled_point_silhouettes=sampled_silhouettes,
        input_pins='PASS',nearest_centroid='PASS',profiles='PASS',variance_blocks='PASS',model_fits=0,research_ready=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run');args=parser.parse_args()
    print(json.dumps(verify(ROOT,ROOT/args.run),indent=2))
