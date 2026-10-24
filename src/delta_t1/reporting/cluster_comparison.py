"""Read-only A/B/C cluster comparison, with independent label namespaces."""
import json
from collections import Counter
from pathlib import Path

from ..experiments.dual_cluster_review import FINANCIAL, csv_bytes
from ..experiments.market_financial_integration import inside, rows, sha, check_hashes


def build(root):
    root = Path(root).resolve()
    review = 'artifacts/reports/dual-cluster-review-v1'
    ref = json.loads((root/'artifacts/reports/combined-reference-v1/result-ref.json').read_bytes())
    combined = inside(root, ref['path'])
    if sha(combined/'manifest.json') != ref['manifest_sha256']:
        raise ValueError('combined result reference changed')
    check_hashes(combined,json.loads((combined/'manifest.json').read_bytes()))
    check_hashes(root/review,json.loads((root/review/'manifest.json').read_bytes()))
    labels = rows(root, ref['path']+'/assignments.csv')
    bykey = {(r['snapshot_date'],r['symbol']):r for r in labels}
    outer = rows(root,review+'/dual-memberships-year-end.csv')
    for r in outer:
        c = bykey.get((r['snapshot_date'],r['symbol']))
        if (r['coverage']=='BOTH') != bool(c):
            raise ValueError('combined/common cohort mismatch')
        r['combined_cluster_id'] = c['combined_cluster_id'] if c else ''
        r['combined_label_scope'] = 'THIS_YEAR_ONLY' if c else 'NOT_IN_COMBINED_COHORT'
    catalog = rows(root,review+'/cluster-catalog.csv')
    fs = json.loads((root/FINANCIAL/'snapshots.json').read_bytes())
    cs = json.loads((combined/'snapshots.json').read_bytes())
    market_profiles = rows(root,'M2/artifacts/m2-final-handoff-v1/m2_cluster_profiles_for_m3.csv')
    days = sorted({r['snapshot_date'] for r in labels})
    metrics, small, drivers = [], [], []
    for day in days:
        year = day[:4]
        model = cs[year]
        group = [r for r in labels if r['snapshot_date']==day]
        mp = [r for r in market_profiles if r['snapshot_date']==day]
        sizes_m = sorted(int(r['size']) for r in mp)[::-1]
        sizes_f = sorted(p['size'] for p in fs[year]['profiles'])[::-1]
        sizes_c = sorted(p['size'] for p in model['profiles'])[::-1]
        metrics.append(dict(year=year,market_snapshot=day,market_native_n=sum(sizes_m),financial_native_n=sum(sizes_f),
                            common_n=len(group),market_sizes=json.dumps(sizes_m),financial_sizes=json.dumps(sizes_f),
                            combined_sizes=json.dumps(sizes_c),combined_silhouette=model['metrics']['silhouette'],
                            combined_quality_status=model['metrics']['quality_status'],
                            metric_scope='DIFFERENT_NATIVE_FEATURE_SPACES_AND_COHORTS_NOT_DIRECT_MODEL_RANKING'))
        count = Counter(int(r['combined_cluster_id']) for r in group)
        small.extend(dict(r,combined_cluster_size=count[int(r['combined_cluster_id'])])
                     for r in group if count[int(r['combined_cluster_id'])]<10)
        fields = model['feature_order']
        centers = model['centroids']
        grand = [sum(count[k]*centers[k][j] for k in count)/len(group) for j in range(len(fields))]
        between = [sum(count[k]*(centers[k][j]-grand[j])**2 for k in count) for j in range(len(fields))]
        total = sum(between)
        drivers.extend(dict(year=year,feature=f,family=model['scalers'][f]['family'],
                            separation_share=between[j]/total if total else 0) for j,f in enumerate(fields))
        for p in model['profiles']:
            catalog.append(dict(data_type='COMBINED',snapshot=day,cluster_id=p['cluster_id'],size=p['size'],
                                feature_means_json=json.dumps(p['means'],sort_keys=True),source=ref['path']+'/snapshots.json'))
    counts = Counter((r['snapshot_date'],r['market_cluster_id'],r['financial_cluster_id'],r['combined_cluster_id'])
                     for r in outer if r['coverage']=='BOTH')
    contingency = [dict(snapshot_date=d,market_cluster_id=m,financial_cluster_id=f,combined_cluster_id=c,count=n)
                   for (d,m,f,c),n in sorted(counts.items())]
    summary = dict(status='COMPLETE_A_B_C_DESCRIPTIVE_REFERENCE',market_profiles=168,financial_profiles=30,
                   combined_profiles=21,common_observations=len(labels),outer_memberships=len(outer),
                   combined_small_cluster_members=len(small),combined_years_with_cluster_below_10=len({r['fiscal_year'] for r in small}),
                   strict_pit_ready=False,research_ready=False,backtest_allowed=False,quality_status='REVIEW_REQUIRED')
    table = '\n'.join(f"| {r['year']} | {r['market_native_n']} | {r['financial_native_n']} | {r['common_n']} | {r['combined_sizes']} | {r['combined_silhouette']:.4f} |" for r in metrics)
    report = f'''# Đối chiếu cụm market, financial và kết hợp — 24/10/2026

Đã giữ nguyên A market-only (168 cụm/84 tháng), B financial-only (30 cụm/10 năm)
và thêm C combined reference (21 cụm/7 năm). Có {len(labels):,} quan sát common cohort.
Nhãn A/B/C là ba namespace độc lập; cùng số nhãn không đồng nghĩa cùng ý nghĩa.

## Cấu hình C đã được owner duyệt và thực thi

14 features = 8 market + 6 core ratios. Z-score độc lập từng năm trên cohort chung;
nhân mỗi chiều market với sqrt(0,5/8), financial với sqrt(0,5/6). KMeans k=3,
seed=42, n_init=20, max_iter=300; không clipping/PCA/imputation, không chọn bằng returns.
Trọng số này cân bằng variance đầu vào của hai block, không bảo đảm mỗi block
đóng góp đúng50% vào khoảng cách giữa các cụm sau fit.

| Năm | A native n | B native n | C common n | Kích thước C giảm dần | Silhouette C |
|---|---:|---:|---:|---|---:|
{table}

Cả7năm vẫn có cụm dưới10mã: kỹ thuật hội tụ không đồng nghĩa chất lượng đã đạt.
Không so trực tiếp silhouette A/B/C để chọn winner vì feature space, cohort,
tần suất và preprocessing khác nhau. Chưa chạy thêm comparator hoặc đổi k.

## Kết quả review dữ liệu A/B

Market: median phần tách centroid theo metric đã fit của liquidity_21 là99,997%.
Điều này mô tả sự chi phối của feature trong geometry hiện hành, không chứng minh
nguồn liquidity sai. Robust scaling không tự chặn tails.

Financial:180dòng outlier/157vectors tính lại đúng selected inputs từ cache.
56dòng review có liabilities>assets trong selected inputs;27dòng có revenue<1%assets.
Đây là cờ diagnostic, không tự quarantine hoặc sửa số. QBS2025: netprofit
-78.365.108.636 / revenue150.000.000 = net_margin-522,434. CAD2025: liabilities
1.521.403.252.068 / assets11.571.353.867 =131,480. VTI2025:218.704.147.614 /
1.721.287.069 =127,058. Scope/unit/source facts vẫn cần kiểm độc lập với BCTC gốc;
arithmetic replay không thay thế source-fact acceptance. Không tải PDF/OCR mới.

## Các bảng để sử dụng

- `memberships-a-b-c-year-end.csv`: union các mã A/B tại cuối năm; có nhãn C khi đủ cả hai input.
- `cluster-catalog-a-b-c.csv`:219profiles, giữ original-scale means và source path.
- `contingency-a-b-c.csv`: đếm giao các cụm trên common cohort, không ép nhãn tương đương.
- `annual-comparison.csv`: quy mô native A/B và common C, cùng diagnostics của C.
- `combined-separation-drivers.csv`, `combined-small-cluster-members.csv`: queue review C.
- A/B source-input review và prepared14features ở `../dual-cluster-review-v1/`.
- C independent verification và result pointer ở `../combined-reference-v1/`.

## Phạm vi sử dụng

Financial11.720rows hiện không có published_at trong bảng bàn giao. Join same-fiscal-year
với December là EX_POST_REFERENCE, có thể dùng thông tin công bố sau ngày snapshot.
Chỉ phục vụ mô tả; không historical PIT, không historical identity được chứng nhận,
không backtest/M3 và không claim holdout mới. Sáu core ratios không phải bộ
EPS/P/E/P/B/F/M/Z hoàn chỉnh. A/B không refit; C là run mới có pins và manifest.
'''
    payloads = {'memberships-a-b-c-year-end.csv': csv_bytes(outer),'cluster-catalog-a-b-c.csv':csv_bytes(catalog),
                'contingency-a-b-c.csv':csv_bytes(contingency),'annual-comparison.csv':csv_bytes(metrics),
                'combined-separation-drivers.csv':csv_bytes(drivers),'combined-small-cluster-members.csv':csv_bytes(small),
                'summary.json':(json.dumps(summary,indent=2,sort_keys=True)+'\n').encode(),'report.md':report.encode('utf-8')}
    target = root/'artifacts/reports/cluster-comparison-v1'
    if target.exists():
        for name,data in payloads.items():
            if (target/name).read_bytes()!=data:
                raise ValueError('immutable comparison differs: '+name)
        return target,summary
    target.mkdir(parents=True)
    for name,data in payloads.items():
        (target/name).write_bytes(data)
    (target/'manifest.json').write_bytes((json.dumps({name:sha(target/name) for name in payloads},indent=2,sort_keys=True)+'\n').encode())
    return target,summary
