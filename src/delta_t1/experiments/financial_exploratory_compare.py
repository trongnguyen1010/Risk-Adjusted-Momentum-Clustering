"""Fixed rank-scaling sensitivity for the same exploratory cross-section."""
import csv,io,json
from collections import Counter
from pathlib import Path
from .financial_exploratory import fit_year,validate_mode
from .financial_history_documents import put
from .financial_api_input_review import csv_bytes
from ..features.financial_exploratory import FEATURES
from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside


def run(root,config_path):
    root=Path(root);c=json.loads(inside(root,config_path).read_bytes());pins={}
    if c.get('scope')!='EXPLORATORY_SCALE_SENSITIVITY_NO_FINAL_MODEL_SELECTION' or c.get('portfolio_evaluation_enabled') is not False:raise ValueError('reference sensitivity only')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();actual=digest(raw)
        if expected is not None and actual!=expected:raise ValueError('comparison input changed')
        pins[path]=actual;return raw
    for p in [config_path,'src/delta_t1/experiments/financial_exploratory_compare.py','scripts/financial_exploratory_compare.py',
        'src/delta_t1/experiments/financial_exploratory.py','src/delta_t1/features/preprocessing.py',
        'src/delta_t1/clustering/kmeans.py','src/delta_t1/evaluation/cluster_metrics.py']:pin(p)
    ref=c['baseline_result'];m=json.loads(pin(ref['path']+'/manifest.json',ref['manifest_sha256']))
    config=json.loads(pin(ref['path']+'/config.json',m['config.json']));validate_mode(config)
    snapshots=json.loads(pin(ref['path']+'/snapshots.json',m['snapshots.json']))
    rows=list(csv.DictReader(io.StringIO(pin(ref['path']+'/features.csv',m['features.csv']).decode())))
    numeric=[dict(r,year=int(r['year']),**{f:float(r[f]) for f in FEATURES}) for r in rows]
    selected=[r for r in numeric if r['year']==c['year']]
    alternative=dict(config,scaling='rank');rank=fit_year(selected,alternative);baseline=snapshots[str(c['year'])]
    if {r['registry_id'] for r in rank['assignments']}!={r['registry_id'] for r in baseline['assignments']}:raise ValueError('sensitivity sample differs')
    outliers=[]
    by_key={(r['year'],r['registry_id']):r for r in numeric}
    for year,snapshot in snapshots.items():
        small={r['cluster_id'] for r in snapshot.get('profiles',[]) if r['size']<10}
        for assignment in snapshot.get('assignments',[]):
            if assignment['cluster_id'] not in small:continue
            row=by_key[int(year),assignment['registry_id']]
            outliers.append(dict(symbol=row['symbol'],registry_id=row['registry_id'],year=int(year),cluster_id=assignment['cluster_id'],
                **{f:row[f] for f in FEATURES},source_evidence=row['source_evidence'],qa_evidence=row['qa_evidence'],
                review_status='EXTREME_OR_DISTINCT_PROFILE_NOT_AUTOMATIC_DATA_ERROR_DO_NOT_DELETE'))
    summary=dict(status='COMPLETE_EXPLORATORY_RANK_SENSITIVITY',year=c['year'],sample_size=len(selected),
        zscore_cluster_sizes=baseline['diagnostics']['cluster_sizes'],rank_cluster_sizes=rank['diagnostics']['cluster_sizes'],
        outlier_review_rows=len(outliers),same_sample_verified=True,final_model_selected=False,strict_pit_ready=False,m3_backtest_allowed=False)
    products={'summary.json':encoded(summary),'rank-snapshot.json':encoded(rank),'rank-assignments.csv':csv_bytes(rank['assignments']),
        'outlier-review.csv':csv_bytes(outliers),'input-pins.json':encoded(pins)}
    manifest={n:digest(b) for n,b in products.items()};out=inside(root,c['output_root'])/digest(encoded(manifest))[:20]
    for name,body in products.items():put(out/name,body)
    put(out/'manifest.json',manifest)
    import os
    report=inside(root,c['report_root']);rel=os.path.relpath(out,report).replace('\\','/')
    original=os.path.relpath(root/'artifacts/reports/financial-exploratory-core-v1/report.md',report).replace('\\','/')
    text=f'''# Review baseline financial và rank sensitivity

Đã chạy đối chứng cố định trên **cùng {len(selected)} mã FY{c['year']}**, không thêm/bớt mã, không impute, không đổi k=3/seed/restarts. Thay duy nhất zscore bằng midrank transform; không sửa baseline đã seal hoặc tự chọn model cuối.

| Phép thử | Cluster sizes | Silhouette trong không gian riêng |
|---|---|---:|
| Z-score baseline | {baseline['diagnostics']['cluster_sizes']} | {baseline['diagnostics']['silhouette']:.4f} |
| Rank sensitivity | {rank['diagnostics']['cluster_sizes']} | {rank['diagnostics']['silhouette']:.4f} |

Hai silhouette thuộc hai geometry khác nhau, không dùng so trực tiếp để tự tuyên bố model tốt hơn. Rank giảm ảnh hưởng độ lớn cực đoan nhưng làm mất thông tin khoảng cách kinh tế tuyệt đối; phải review trước freeze phương pháp.

Baseline có singleton/tiny clusters ở nhiều năm. Ví dụ FY2025 JOS có liabilities/assets≈77,99 và PTC net margin≈814,26. Những số này có thể do equity âm hoặc doanh thu rất nhỏ so với thu nhập khác; chưa đủ chứng minh data sai. Giữ source refs để kiểm tra, không tự xoá, winsorize hoặc dùng EPS/F/M/Z thay thế.

- [Baseline 10 năm và phạm vi dữ liệu]({original}).
- [Rank assignments FY2025]({rel}/rank-assignments.csv), [rank model/scaler/profiles]({rel}/rank-snapshot.json).
- [Các mã ở cụm nhỏ cần review]({rel}/outlier-review.csv), [summary]({rel}/summary.json).

Đây là exploratory sensitivity owner đã cho phép trong luồng core financial ratios, không final M2/M3, không PIT, không Dynamic Clustering, không có portfolio return/Sharpe hoặc chọn feature/model bằng backtest. Market handoff vẫn chờ teammate; EPS/P/E/P/B/F/M/Z vẫn hoàn thiện song song, không bị thay mục tiêu.
'''
    put(report/'report.md',text.encode());put(report/'result-ref.json',dict(path=out.relative_to(root).as_posix(),manifest_sha256=digest((out/'manifest.json').read_bytes())))
    return dict(summary,output=out.relative_to(root).as_posix())
