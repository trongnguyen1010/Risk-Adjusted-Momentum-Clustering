"""Task 11 V2: verify the frozen sklearn winner, then open holdout exactly once."""
from collections import defaultdict
from datetime import datetime, timezone
import importlib.metadata
import math
from pathlib import Path
from statistics import median
import zipfile

from ..clustering.registry import get_algorithm
from ..io import digest, encoded, now, read_json, write_json, write_rows
from .artifacts import load_verified_market_only_features
from .final_holdout import (
    QUALITY, TEMPORAL, TEMPORAL_FIELDS, TRANSITION_FIELDS, DRIFT_FIELDS,
    _path, _csv_rows, _write_csv, _summary, fit_holdout,
)
from .protocol import M2_MARKET_FEATURES, validate_protocol
from .runner import m2_clustering_config, prepare_snapshot_rows, _with_c8_market_readiness_alias

CONFIG_PATH = 'configs/experiments/m2_final_holdout_v2.json'


def _code_paths(root):
    names = ['experiments/final_holdout_v2.py', 'experiments/final_holdout.py',
             'experiments/protocol.py', 'experiments/runner.py', 'experiments/artifacts.py',
             'clustering/base.py', 'clustering/kmeans.py', 'clustering/registry.py',
             'features/preprocessing.py', 'features/registry.py', 'evaluation/cluster_metrics.py',
             'evaluation/temporal_metrics.py', 'io.py']
    return [root / 'src/delta_t1' / name for name in names]


def freeze_gate(root):
    """Read development/config/manifest metadata only; never load holdout features."""
    root = Path(root).resolve()
    cfg_path = root / CONFIG_PATH
    cfg = read_json(cfg_path)
    expected = dict(stage='M2_TASK_11_HOLDOUT', selected_method='KMeans_Baseline',
                    implementation='sklearn', min_eligible_count=100,
                    eligibility_field='market_feature_ready_v2', gap_reset=True,
                    portfolio_evaluation_enabled=False, k_scan_enabled=False,
                    rerun_policy='verify_existing_complete_artifacts_without_refit',
                    output_dir='M2/artifacts/m2-final-holdout-v2',
                    model_dir='M2/models/holdout_v2',
                    report_path='M2/reports/Bao_cao_M2_Nhiem_vu_11_Final_Holdout_v2.md')
    for key, value in expected.items():
        if cfg.get(key) != value:
            raise ValueError('V2 holdout config conflicts with frozen plan: ' + key)
    pins = cfg['frozen_inputs_sha256']
    required = {cfg[k] for k in ['decision_path', 'protocol_path', 'task4_config_path',
                               'development_manifest_path', 'selected_models_manifest_path']}
    if not required <= pins.keys():
        raise ValueError('Missing pinned development input')
    for relative, expected_hash in pins.items():
        if digest(_path(root, relative).read_bytes()) != expected_hash:
            raise ValueError('Frozen V2 input checksum mismatch: ' + relative)
    decision = read_json(_path(root, cfg['decision_path']))
    if (decision.get('status') != 'FROZEN_FOR_HOLDOUT'
            or decision.get('selected_method') != cfg['selected_method']
            or decision.get('global_k') != 2
            or set(decision.get('comparator_methods', [])) != {'Ward_Hierarchical', 'PCA_KMeans'}):
        raise ValueError('Task 10 must freeze exactly the current KMeans winner/K=2')
    timestamp = datetime.fromisoformat(decision['decision_timestamp'])
    if timestamp.tzinfo is None or timestamp > datetime.now(timezone.utc):
        raise ValueError('Decision must be timezone-aware and precede holdout opening')
    protocol = read_json(_path(root, cfg['protocol_path']))
    validate_protocol(protocol)
    dev, hold = protocol['development_snapshots'], protocol['holdout_snapshots']
    if (len(dev) != 60 or len(hold) != 24 or max(dev) >= min(hold)
            or decision['development_snapshots'] != dev or cfg['holdout_snapshots'] != hold
            or (cfg['start'], cfg['end']) != (hold[0], hold[-1])):
        raise ValueError('V2 requires the complete frozen 60 development / 24 holdout split')
    baseline = read_json(_path(root, cfg['development_manifest_path']))
    task4 = read_json(_path(root, cfg['task4_config_path']))
    params = task4.get('seed'), task4.get('n_init'), task4.get('max_iter')
    if (baseline['config'] != protocol or baseline['implementation'] != 'sklearn'
            or task4.get('implementation') != 'sklearn' or params != (42, 10, 300)
            or baseline['parameters'] != dict(seed=42, n_init=10, max_iter=300)
            or baseline['global_k'] != 2 or baseline['total_snapshots'] != 60
            or baseline['features'] != list(M2_MARKET_FEATURES)):
        raise ValueError('Development implementation/parameters differ from frozen Task 4')
    bundle = decision['frozen_artifacts_manifest']
    model_dir = _path(root, bundle['selected_model_directory'])
    model_index_path = _path(root, cfg['selected_models_manifest_path'])
    if model_index_path != model_dir / 'model_file_manifest.json':
        raise ValueError('Selected model directory differs from Task 10')
    index = read_json(model_index_path)
    if (index['selected_method'] != 'KMeans_Baseline' or index['development_snapshots'] != dev
            or sorted(f['name'] for f in index['files']) != [d+'.json' for d in dev]):
        raise ValueError('Expected exactly 60 frozen development models')
    inputs = dict(pins)
    for item in index['files']:
        p = _path(model_dir, item['name'])
        if digest(p.read_bytes()) != item['sha256'] or baseline['model_checksums_sha256'][item['name']] != item['sha256']:
            raise ValueError('Frozen selected model checksum mismatch: ' + item['name'])
        model = read_json(p)
        if (model['parameters'] != baseline['parameters'] or model['feature_order'] != list(M2_MARKET_FEATURES)
                or model['k'] != 2 or model['snapshot'] != p.stem
                or len(model['centroids_scaled']) != 2
                or any(len(c) != 8 for c in model['centroids_scaled'])
                or any(model['scaler'][f]['method'] != 'robust_per_snapshot' for f in M2_MARKET_FEATURES)):
            raise ValueError('Frozen model schema/preprocessing mismatch')
        inputs[p.relative_to(root).as_posix()] = item['sha256']
    diagnostics_path = _path(root, cfg['development_diagnostics_path'])
    diagnostics = _csv_rows(diagnostics_path)
    if ([r['snapshot_date'] for r in diagnostics] != dev
            or any(int(r['k']) != 2 for r in diagnostics)
            or any(not math.isfinite(float(r[m])) for r in diagnostics for m in QUALITY)):
        raise ValueError('Expected 60 development diagnostics at K=2')
    comparison_path = _path(root, bundle['comparison_table'])
    comparison = _csv_rows(comparison_path)
    winner = next(r for r in comparison if r['method'] == 'KMeans_Baseline')
    if not math.isclose(median(float(r['silhouette']) for r in diagnostics),
                        float(winner['median_silhouette']), abs_tol=1e-10):
        raise ValueError('Task 10 differs from saved development diagnostics')
    evaluation_dir = _path(root,cfg['development_evaluation_dir'])
    dev_profiles = []
    for row in _csv_rows(evaluation_dir/'cluster_profiles.csv'):
        profile = dict(snapshot_date=row['snapshot_date'])
        for feature in M2_MARKET_FEATURES:
            value = float(row[feature] if feature in row else row[feature+'_mean'])
            if not math.isfinite(value):
                raise ValueError('Nonfinite development profile')
            profile[feature] = value
        dev_profiles.append(profile)
    if (len(dev_profiles) != 120 or {p['snapshot_date'] for p in dev_profiles} != set(dev)
            or any(sum(p['snapshot_date']==d for p in dev_profiles)!=2 for d in dev)):
        raise ValueError('Expected two original-feature development profiles per month')
    dev_temporal = _csv_rows(evaluation_dir/'temporal_stability.csv')
    if [(r['from_date'],r['to_date']) for r in dev_temporal] != list(zip(dev[:-1],dev[1:])):
        raise ValueError('Expected exactly 59 internal development temporal pairs')
    source = read_json(_path(root, cfg['feature_store']) / 'manifest.json')
    lineage = decision['source_lineage']['KMeans_Baseline']
    if (digest((_path(root, cfg['feature_store']) / 'manifest.json').read_bytes()) != lineage['c8_manifest_sha256']
            or source['outputs']['canonical/feature_snapshots.jsonl'] != lineage['c8_feature_sha256']):
        raise ValueError('C8 source metadata differs from frozen Task 10 lineage')
    cluster = m2_clustering_config(protocol, algorithm='kmeans', implementation='sklearn',
                                  k=2, k_range=[2], seed=42, n_init=10, max_iter=300,
                                  momentum_feature='mom_21', risk_feature='vol_63')
    get_algorithm('kmeans').validate_config(cluster)
    inputs[CONFIG_PATH] = digest(cfg_path.read_bytes())
    code = {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in _code_paths(root)}
    packages = {p:importlib.metadata.version(p) for p in ['numpy','scikit-learn','matplotlib']}
    return dict(selected_method='KMeans_Baseline', algorithm='kmeans', task_config=cfg,
                protocol=protocol, clustering=cluster, decision=decision,
                input_sha256=inputs, code_sha256=code, dev_diagnostics=diagnostics,
                evaluation_dir=evaluation_dir, dev_profiles=dev_profiles, package_versions=packages)


def prepare_holdout(root, gate):
    dates = gate['task_config']['holdout_snapshots']
    source, rows = load_verified_market_only_features(_path(root, gate['task_config']['feature_store']), dates)
    grouped = defaultdict(list)
    for row in rows:
        day = row['as_of_date']
        available = datetime.fromisoformat(row['available_at'])
        if (row.get('feature_version') != '1.6.0' or available.tzinfo is None
                or available > datetime.fromisoformat(day+'T23:59:59+07:00')):
            raise ValueError('Wrong version or future availability in holdout: ' + day)
        grouped[day].append(_with_c8_market_readiness_alias(row, 'market_feature_ready_v2'))
    return source, [prepare_snapshot_rows(grouped[d], gate['protocol'], d) for d in dates]


def verify_existing(root, gate):
    target = _path(root, gate['task_config']['output_dir'])
    manifest = read_json(target/'manifest.json')
    if (manifest.get('status') != 'complete' or manifest['input_sha256'] != gate['input_sha256']
            or manifest['code_sha256'] != gate['code_sha256'] or manifest['clustering'] != gate['clustering']):
        raise ValueError('Incomplete run or frozen inputs/code changed: preserve evidence; no refit')
    if (manifest['methods_executed'] != ['kmeans'] or manifest['k_values_executed'] != [2]
            or manifest['selected_method'] != 'KMeans_Baseline'
            or manifest['holdout_snapshots'] != gate['task_config']['holdout_snapshots']):
        raise ValueError('Holdout manifest no longer matches the frozen winner/split')
    for rel, expected in manifest['artifacts'].items():
        if digest(_path(root, rel).read_bytes()) != expected:
            raise ValueError('Holdout artifact checksum mismatch: ' + rel)
    store = _path(root, gate['task_config']['feature_store'])
    if (digest((store/'manifest.json').read_bytes()) != manifest['c8_manifest_sha256']
            or digest((store/'canonical/feature_snapshots.jsonl').read_bytes()) != manifest['c8_feature_sha256']):
        raise ValueError('C8 source changed since holdout execution')
    return target, manifest


def _plot(target, gate, diagnostics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dev = gate['protocol']['development_snapshots']
    hold = gate['protocol']['holdout_snapshots']
    values = {r['snapshot_date']:r['silhouette'] for r in diagnostics}
    fig, ax = plt.subplots(figsize=(20, 7))
    ax.plot(range(60), [float(r['silhouette']) for r in gate['dev_diagnostics']], 'o-', label='Development')
    ax.plot(range(60,84), [values.get(d,float('nan')) for d in hold], 's-', label='Holdout')
    ax.hlines(median(float(r['silhouette']) for r in gate['dev_diagnostics']),0,59,linestyles=':',colors='tab:blue')
    ax.hlines(median(values.values()),60,83,linestyles=':',colors='tab:orange')
    ax.axvline(59.5,linestyle='--',color='red')
    ax.text(59.5,.03,'Train/Holdout Boundary — Out-of-Sample Sealed Separation',rotation=90,ha='right',fontsize=8)
    ax.set_xticks(range(84),dev+hold,rotation=75,ha='right',fontsize=7)
    ax.set(ylim=(0,1),ylabel='Silhouette',title='Frozen KMeans Baseline / K=2 — 60 development + 24 holdout')
    ax.legend();ax.grid(axis='y',alpha=.2);fig.tight_layout()
    fig.savefig(target/'holdout_vs_dev_trajectory.png',dpi=150);plt.close(fig)


def run_final_holdout(root):
    root = Path(root).resolve()
    gate = freeze_gate(root)
    cfg = gate['task_config']
    target = _path(root,cfg['output_dir'])
    if target.exists():
        return verify_existing(root,gate)
    model_dir, report_path = _path(root,cfg['model_dir']), _path(root,cfg['report_path'])
    if (model_dir.exists() and any(model_dir.iterdir())) or report_path.exists():
        raise FileExistsError('Existing V2 models/report must not be overwritten')
    target.mkdir(parents=True,exist_ok=False)
    manifest = dict(artifact_id=target.name,stage='M2_TASK_11_HOLDOUT',status='running',
        selected_method='KMeans_Baseline',algorithm='kmeans',implementation='sklearn',global_k=2,
        clustering=gate['clustering'],input_sha256=gate['input_sha256'],code_sha256=gate['code_sha256'],
        decision_timestamp=gate['decision']['decision_timestamp'],holdout_opened_at=now(),
        holdout_snapshots=cfg['holdout_snapshots'],methods_executed=['kmeans'],k_values_executed=[2],
        portfolio_evaluation_enabled=False,gap_reset=True,market_only=True,synthetic=cfg.get('synthetic',False),
        historical_identity_verified=False,
        package_versions=gate['package_versions'])
    write_json(target/'manifest.json',manifest)
    try:
        print('Opening 24 holdout snapshots; frozen sklearn KMeans/K=2 only.',flush=True)
        source, prepared = prepare_holdout(root,gate)
        store = _path(root,cfg['feature_store'])
        manifest.update(c8_manifest_sha256=digest((store/'manifest.json').read_bytes()),
            c8_feature_sha256=source['outputs']['canonical/feature_snapshots.jsonl'],
            feature_version='1.6.0',data_version=source['data_version'])
        snapshots, temporal, transitions, drift = fit_holdout(prepared,gate['clustering'],'kmeans')
        assignments, profiles, diagnostics, scalers = [], [], [], []
        model_dir.mkdir(parents=True,exist_ok=True)
        for snap in snapshots:
            day, ids = snap['snapshot_date'],snap['aligned_ids']
            write_json(target/'models'/(day+'.json'),snap['model'])
            write_json(model_dir/(day+'.json'),snap['model'])
            assignments.extend(dict(snapshot_date=day,security_id=r['security_id'],raw_cluster_id=label,
                aligned_cluster_id=ids[label],run_id=target.name,data_version=source['data_version'])
                for r,label in zip(snap['rows'],snap['labels']))
            for p in snap['profiles']:
                profiles.append(dict(snapshot_date=day,raw_cluster_id=p['raw_cluster_id'],
                    aligned_cluster_id=ids[p['raw_cluster_id']],size=p['size'],size_ratio=p['size']/len(snap['rows']),
                    **{f:p['centroid'][f] for f in M2_MARKET_FEATURES}))
            diagnostics.append(dict(snapshot_date=day,**snap['diagnostics'][0]))
            scalers.extend(dict(snapshot_date=day,feature=f,**{k:v for k,v in snap['model']['scaler'][f].items()
                if k!='rank_reference'}) for f in M2_MARKET_FEATURES)
        for name, rows in [('assignments',assignments),('profiles',profiles),('diagnostics',diagnostics)]:
            write_rows(target/(name+'.jsonl'),rows)
            serial=[{k:encoded(v).decode() if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows]
            _write_csv(target/('cluster_profiles.csv' if name=='profiles' else name+'.csv'),serial)
        validation=[dict(snapshot_date=p['snapshot_date'],status=p['status'],n_eligible=p['eligible_count'],reason=p['reason']) for p in prepared]
        _write_csv(target/'snapshot_validation.csv',validation)
        write_rows(target/'skipped_snapshots.jsonl',[v for v in validation if v['status']=='skipped'])
        _write_csv(target/'scaler_parameters.csv',scalers)
        _write_csv(target/'temporal_stability.csv',temporal,TEMPORAL_FIELDS)
        _write_csv(target/'transition_matrices.csv',transitions,TRANSITION_FIELDS)
        _write_csv(target/'centroid_drift.csv',drift,DRIFT_FIELDS)
        _write_csv(target/'quality_summary.csv',[dict(metric=m,n_total=24,n_available=len(diagnostics),
            **_summary(r[m] for r in diagnostics)) for m in QUALITY])
        dev_temporal=_csv_rows(gate['evaluation_dir']/'temporal_stability.csv')
        gaps=[]
        for metric in (*QUALITY,*TEMPORAL):
            dev,h=(gate['dev_diagnostics'],diagnostics) if metric in QUALITY else (dev_temporal,temporal)
            if h:
                a,b=median(float(r[metric]) for r in dev),median(float(r[metric]) for r in h)
                gaps.append(dict(metric=metric,development_n=len(dev),holdout_n=len(h),development_median=a,
                                 holdout_median=b,delta_holdout_minus_development=b-a))
        _write_csv(target/'holdout_generalization_gap.csv',gaps)
        checks=[]
        for period, rows in [('development',gate['dev_profiles']),('holdout',profiles)]:
            grouped=defaultdict(list)
            for r in rows:grouped[r['snapshot_date']].append(r)
            ranked=defaultdict(list)
            for members in grouped.values():
                for role,r in zip(['Higher_mom63','Lower_mom63'],sorted(members,key=lambda r:-float(r['mom_63']))):
                    ranked[role].append(r)
            for role,members in ranked.items():
                for f in M2_MARKET_FEATURES:
                    checks.append(dict(period=period,role=role,feature=f,n_snapshots=len(members),**_summary(float(r[f]) for r in members)))
        _write_csv(target/'profile_consistency.csv',checks)
        write_json(target/'execution_config.json',dict(cfg,clustering=gate['clustering']))
        with zipfile.ZipFile(target/'source_snapshot.zip','w',zipfile.ZIP_DEFLATED) as archive:
            for p in _code_paths(root):archive.write(p,p.relative_to(root).as_posix())
        _plot(target,gate,diagnostics)
        sil=next(r for r in gaps if r['metric']=='silhouette')
        table='\n'.join(f"| {r['metric']} | {r['development_median']:.6f} | {r['holdout_median']:.6f} | {r['delta_holdout_minus_development']:+.6f} |" for r in gaps)
        profile_values={(r['period'],r['role'],r['feature']):r['mean'] for r in checks}
        profile_lines=[]
        for f in M2_MARKET_FEATURES:
            divisor=1e9 if f=='liquidity_21' else 1
            values=[profile_values[period,role,f]/divisor for role in ['Higher_mom63','Lower_mom63']
                    for period in ['development','holdout']]
            label=f+' (tỷ VND/phiên)' if divisor==1e9 else f
            profile_lines.append('| '+label+' | '+' | '.join(f'{v:.6f}' for v in values)+' |')
        profile_table='\n'.join(profile_lines)
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(f'''# Báo cáo Nhiệm vụ 11 — Final Holdout V2

## A — Cổng đóng băng và thực thi
KMeans Baseline, sklearn, K=2; seed=42, n_init=10, max_iter=300.
Decision: {manifest['decision_timestamp']}; mở holdout: {manifest['holdout_opened_at']}.
Nguồn: `{manifest['data_version']}`, feature version 1.6.0; source hash
`{manifest['c8_feature_sha256']}`. Input/config/code được khóa trong manifest.
Chạy {len(snapshots)}/24 snapshot; skip {24-len(snapshots)}; {len(assignments)} assignments;
{len(temporal)}/23 cặp nội bộ holdout. Robust Scaling và fit độc lập mỗi tháng,
ngưỡng universe 100, không quét K hoặc chạy comparator. Nhãn bắt đầu chuỗi mới tại
ranh giới Dev/Holdout; không nối qua skip hoặc khoảng trống tháng.

## B — Development so với Holdout
| Metric | Median Development | Median Holdout | Holdout − Development |
| --- | --- | --- | --- |
{table}

Delta Silhouette thực tế: **{sil['delta_holdout_minus_development']:+.6f}**.
Đọc kết quả cùng Balance, quy mô cụm nhỏ, ARI và biến động universe. Rubric trong
kế hoạch không tự chứng minh không overfit, macro regime shift hay lợi ích đầu tư.

![Quỹ đạo 84 mốc](../artifacts/{target.name}/holdout_vs_dev_trajectory.png)

## C — Hồ sơ và giới hạn
`profile_consistency.csv` so tám feature gốc qua mean hồ sơ tháng, xếp vai trò
Higher/Lower mom_63 riêng từng tháng; không giả định nhãn C0/C1 có cùng ý nghĩa
qua ranh giới. Cụm nhỏ nhất holdout: {min(r['size'] for r in profiles)} mã.

| Feature | Higher mom63 Dev mean | Higher mom63 Holdout mean | Lower mom63 Dev mean | Lower mom63 Holdout mean |
| --- | --- | --- | --- | --- |
{profile_table}

Các Mean trên là tổng hợp không trọng số qua hồ sơ tháng, không phải median cổ phiếu.
Giữ mô tả trung tính; không mặc định nhóm momentum cao phải có thanh khoản lớn.
Migration chỉ tính mã chung, không phải turnover/chi phí danh mục. Không suy nguyên
nhân VN-Index khi chưa có phân tích chỉ số; không retune từ kết quả holdout.
Đây là monthly independent clustering market-only, không phải Dynamic Clustering.
Lần chạy sau chỉ verify checksum/nạp lại, không refit. Task 12/M3 thực hiện riêng.
''',encoding='utf-8',newline='\n')
        outputs=[p for p in target.rglob('*') if p.is_file() and p.name!='manifest.json']
        outputs.extend(model_dir.glob('*.json'));outputs.append(report_path)
        manifest.update(status='complete',completed_at=now(),n_snapshots=len(snapshots),n_skipped=24-len(snapshots),
            n_assignments=len(assignments),n_temporal_pairs=len(temporal),delta_silhouette=sil['delta_holdout_minus_development'],
            artifacts={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in outputs})
        write_json(target/'manifest.json',manifest)
    except Exception as exc:
        manifest.update(status='failed',error=type(exc).__name__+': '+str(exc),finished_at=now())
        write_json(target/'manifest.json',manifest)
        raise
    return verify_existing(root,gate)
