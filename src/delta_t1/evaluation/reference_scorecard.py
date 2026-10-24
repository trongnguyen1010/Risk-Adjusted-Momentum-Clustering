"""Geometry scorecards; no model selection via portfolio metrics."""
from collections import Counter
import numpy as np
from sklearn.metrics import silhouette_samples, davies_bouldin_score, calinski_harabasz_score


def score(matrix,labels,features,distances,reference_distances,market_width=None):
    x=np.asarray(matrix);labels=np.asarray(labels);sizes=Counter(int(v) for v in labels);n=len(x)
    valid=[v for v in sizes if v>=0];noise=sizes.get(-1,0)
    threshold=max(10,int(np.ceil(.01*n)))
    result=dict(n=n,k=len(valid),sizes=dict(sorted(sizes.items())),noise_fraction=noise/n,
                largest_share=max((sizes[v] for v in valid),default=0)/n,
                singleton_count=sum(sizes[v]==1 for v in valid),tiny_count=sum(sizes[v]<threshold for v in valid),tiny_threshold=threshold)
    fractions=np.array([sizes[v]/n for v in valid]);result['effective_k']=float(np.exp(-sum(fractions*np.log(fractions)))) if len(fractions) else 0
    result['dominant_flag']=result['largest_share']>.90
    # Noise-aware callers report separate coverage. R1 K-Means never generates noise.
    if noise or not 1<len(valid)<n:
        result.update(silhouette=None,silhouette_reference=None,davies_bouldin=None,calinski_harabasz=None)
        return result
    samples=silhouette_samples(distances,labels,metric='precomputed')
    ref=silhouette_samples(reference_distances,labels,metric='precomputed')
    centers=np.array([x[labels==v].mean(axis=0) for v in valid]);overall=x.mean(axis=0)
    between=np.sum(np.array([sizes[v] for v in valid])[:,None]*(centers-overall)**2,axis=0)
    within=sum(float(np.sum((x[labels==v]-centers[i])**2)) for i,v in enumerate(valid))
    shares=between/between.sum() if between.sum() else np.zeros(x.shape[1])
    result.update(silhouette=float(samples.mean()),silhouette_reference=float(ref.mean()),
        silhouette_quantiles=np.quantile(samples,[0,.1,.25,.5,.75,.9,1]).tolist(),
        silhouette_per_cluster={str(v):dict(mean=float(samples[labels==v].mean()),quantiles=np.quantile(samples[labels==v],[0,.25,.5,.75,1]).tolist()) for v in valid},
        silhouette_distribution=samples.tolist(),davies_bouldin=float(davies_bouldin_score(x,labels)),calinski_harabasz=float(calinski_harabasz_score(x,labels)),
        within_dispersion=within,between_dispersion=float(between.sum()),feature_contribution=dict(zip(features,shares.tolist())),
        single_feature_flag=bool(shares.max()>.8))
    if market_width is not None:result['block_contribution']=dict(market=float(shares[:market_width].sum()),financial=float(shares[market_width:].sum()))
    return result
