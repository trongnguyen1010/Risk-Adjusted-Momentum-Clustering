"""Snapshot-local candidate transforms for bounded descriptive research only."""
import numpy as np
from sklearn.preprocessing import PowerTransformer, QuantileTransformer, StandardScaler, RobustScaler


def prepare(matrix, recipe, market_width=None):
    raw=np.asarray(matrix,dtype=float)
    if raw.ndim!=2 or not len(raw) or not np.isfinite(raw).all():raise ValueError('Missing/nonfinite input; no imputation or silent exclusions.')
    constant=np.ptp(raw,axis=0)==0
    spec=dict(recipe=recipe,constant=constant.tolist(),fit_scope='THIS_SNAPSHOT_COHORT_ONLY')
    if recipe=='P1':
        values=np.zeros_like(raw);lambdas=np.ones(raw.shape[1])
        for j in range(raw.shape[1]):
            if constant[j]:continue
            pt=PowerTransformer(method='yeo-johnson',standardize=False)
            values[:,j]=pt.fit_transform(raw[:,j:j+1]).ravel();lambdas[j]=pt.lambdas_[0]
        scaler=StandardScaler();values=scaler.fit_transform(values)
        spec.update(lambdas=lambdas.tolist(),center=scaler.mean_.tolist(),scale=scaler.scale_.tolist())
    elif recipe=='P2':
        qt=QuantileTransformer(n_quantiles=min(1000,len(raw)),output_distribution='normal',random_state=42,subsample=None)
        values=qt.fit_transform(raw)
        spec.update(quantiles=qt.quantiles_.tolist(),references=qt.references_.tolist())
    elif recipe=='P3':
        scales=np.array([np.median(np.abs(v[v!=0])) if np.any(v!=0) else 1. for v in raw.T])
        values=np.sign(raw)*np.log1p(np.abs(raw)/scales)
        scaler=RobustScaler();values=scaler.fit_transform(values)
        spec.update(nonzero_scales=scales.tolist(),center=scaler.center_.tolist(),scale=scaler.scale_.tolist())
    else:raise ValueError('Unknown preregistered recipe')
    if not np.isfinite(values).all():raise ValueError('Transform generated nonfinite values')
    weights=np.ones(raw.shape[1])
    if market_width is not None:
        for lo,hi in ((0,market_width),(market_width,raw.shape[1])):
            variance=float(np.var(values[:,lo:hi],axis=0,ddof=0).sum())
            if variance<=0 or not np.isfinite(variance):raise ValueError('Zero/nonfinite block variance; recipe/snapshot failed')
            weights[lo:hi]=np.sqrt(.5/variance)
    spec['weights']=weights.tolist()
    return values*weights,spec


def replay(matrix,spec):
    """No fitting: reconstruct from saved parameters, including quantile reference knots."""
    raw=np.asarray(matrix,dtype=float)
    recipe=spec['recipe']
    if recipe=='P1':
        from scipy.special import boxcox1p
        values=np.zeros_like(raw)
        for j,lam in enumerate(spec['lambdas']):
            if spec['constant'][j]:continue
            positive=raw[:,j]>=0
            values[positive,j]=boxcox1p(raw[positive,j],lam)
            values[~positive,j]=-boxcox1p(-raw[~positive,j],2-lam)
        values=(values-spec['center'])/spec['scale']
    elif recipe=='P2':
        # Restore only learned knots; transform does not learn parameters.
        qt=QuantileTransformer(output_distribution='normal',subsample=None)
        qt.quantiles_=np.array(spec['quantiles']);qt.references_=np.array(spec['references'])
        qt.n_quantiles_=len(qt.references_);qt.n_features_in_=raw.shape[1]
        values=qt.transform(raw)
    elif recipe=='P3':
        values=np.sign(raw)*np.log1p(np.abs(raw)/spec['nonzero_scales'])
        values=(values-spec['center'])/spec['scale']
    else:raise ValueError('Unknown recipe')
    return values*spec['weights']
