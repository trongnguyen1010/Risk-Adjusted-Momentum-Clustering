"""Clustering rework v2 (owner request 25/10/2026): liquidity filter + Ward/PCA+K-Means + multi-metric selection.

Reads served bundle v2 and indicators_v1 read-only. Writes
data/experiments/clustering_rework_v2/<run-id>/ (sweep.csv, summary.csv,
selection.json, report.md). The served model is not changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from delta_t1.experiments import clustering_rework_v2 as cr2  # noqa: E402

CONFIG = 'configs/experiments/clustering_rework_v2.json'
TERMINAL = 'data/web/delta-intelligence-v2/terminal.sqlite'
INDICATORS = 'configs/product/indicators_v1.json'
OUT = 'data/experiments/clustering_rework_v2'
CODE = ['scripts/run_clustering_rework_v2.py', 'src/delta_t1/experiments/clustering_rework_v2.py',
        'src/delta_t1/experiments/clustering_rework.py', 'src/delta_t1/clustering/robust_transforms.py', CONFIG]
ALGO = {'kmeans': 'K-Means', 'pca_kmeans': 'PCA + K-Means', 'ward': 'Ward', 'gmm': 'GMM'}
GROUP = {
    'A_light_base': 'A – Thị trường · lọc nhẹ · 8 đặc trưng',
    'A_light_dvol': 'A – Thị trường · lọc nhẹ · + downside volatility',
    'A_strict_base': 'A – Thị trường · lọc chặt · 8 đặc trưng',
    'A_strict_dvol': 'A – Thị trường · lọc chặt · + downside volatility',
    'B_base': 'B – Tài chính · 9 chỉ số',
    'B_value': 'B – Tài chính · + định giá & quy mô (E/P, B/P, log vốn hóa)',
    'C_light_base': 'C – Kết hợp · lọc nhẹ',
    'C_strict_base': 'C – Kết hợp · lọc chặt',
}


def log(message):
    print(time.strftime('%H:%M:%S'), message, flush=True)


def fmt(x, d=3):
    return '—' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{x:.{d}f}'


def md(frame):
    cols = list(frame.columns)
    lines = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    lines += ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in frame.itertuples(index=False)]
    return '\n'.join(lines)


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups', default=','.join(GROUP))
    parser.add_argument('--config', default=CONFIG, help='Experiment config (default: the v2 config).')
    args = parser.parse_args()
    config = args.config.replace('\\', '/')
    cfg = json.loads((ROOT / config).read_text(encoding='utf-8'))
    until = cfg['screening'].get('until')  # Optional: screen only snapshots on or before this date.
    pointer = json.loads((ROOT / INDICATORS).read_text(encoding='utf-8'))
    pins = {p: sha(p) for p in [c for c in CODE if c != CONFIG] + [config, TERMINAL, pointer['file']]}
    run_id = ('rework2dev-' if until else 'rework2-') + hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()[:16]
    out = ROOT / OUT / run_id
    out.mkdir(parents=True, exist_ok=True)
    groups = args.groups.split(',')
    fs, levels = cfg['feature_sets'], cfg['liquidity_filter']['levels']
    months = cfg['screening']['A_months']

    log('price activity (zero-volume share, downside vol)')
    from delta_t1.experiments.clustering_rework import _observations
    import sqlite3
    with sqlite3.connect(f'file:{ROOT / TERMINAL}?mode=ro', uri=True) as db:
        dates = [d for d in sorted(_observations(db, 'market')) if d[5:7] in months]
    activity = cr2.price_activity(ROOT / TERMINAL, dates)

    market, excluded = {}, {}
    for level in levels:
        for name in ('base', 'dvol'):
            snaps, ex = cr2.market_snapshots(ROOT / TERMINAL, tuple(fs['A_' + name]), levels[level], months, activity)
            if until:
                snaps = [s for s in snaps if s.date <= until]
            market[level, name], excluded[level] = snaps, ex
    years = range(2017, int(until[:4]) + 1) if until else range(2017, 2026)
    financial = {name: cr2.financial_snapshots(ROOT / pointer['file'], tuple(fs['B_' + name]), years)
                 for name in ('base', 'value')}
    snapshots = {}
    for level in levels:
        for name in ('base', 'dvol'):
            snapshots[f'A_{level}_{name}'] = market[level, name]
        snapshots[f'C_{level}_base'] = cr2.combined_snapshots(market[level, 'base'], financial['base'])
    for name in ('base', 'value'):
        snapshots['B_' + name] = financial[name]

    rows, labels, choices = [], {}, {}
    for group in groups:
        snaps = snapshots[group]
        log(f'{group}: {len(snaps)} snapshots, n={min(len(s.tickers) for s in snaps)}..{max(len(s.tickers) for s in snaps)}')
        r, lab = cr2.sweep(snaps, cfg, group, progress=lambda s: log(f'  {group} {s.date}'))
        rows += r
        labels[group] = lab
    summary = cr2.summarize(rows, cfg)
    for group in groups:
        choice = cr2.select(summary, group)
        if choice:
            last = snapshots[group][-1]
            choice = dict(choice, profile_date=last.date,
                          profile=cr2.profile(last, labels[group][choice['algo'], choice['k'], last.date]))
            if group.startswith(('A_', 'C_')):
                level = group.split('_')[1]
                choice['illiquid_last'] = len(excluded[level][last.date if group.startswith('A_') else last.date])
        choices[group] = choice
        log(f'{group}: ' + (f"{choice['algo']} k={choice['k']} score={choice['score']:.2f}" if choice else 'none admissible'))

    pd.DataFrame(rows).to_csv(out / 'sweep.csv', index=False)
    pd.DataFrame([{k: v for k, v in s.items() if k != 'ranks'} for s in summary]).sort_values(
        ['group', 'algo', 'k']).to_csv(out / 'summary.csv', index=False)
    cr2.dump(out / 'selection.json', choices)
    cr2.dump(out / 'excluded.json', {lvl: {d: len(v) for d, v in ex.items()} for lvl, ex in excluded.items()})
    (out / 'input-pins.json').write_text(json.dumps(pins, indent=2), encoding='utf-8')
    write_report(out, cfg, summary, choices, groups, excluded, snapshots, config)
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.name != 'manifest.json'}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    for g in groups:
        c = choices[g]
        print(g, f"{c['algo']} k={c['k']} sil={fmt(c['silhouette'])} db={fmt(c['davies_bouldin'])} stab={fmt(c['stability'], 2)} tARI={fmt(c['temporal_ari'], 2)}" if c else 'none')
    print('report:', (out / 'report.md').relative_to(ROOT).as_posix())


def write_report(out, cfg, summary, choices, groups, excluded, snapshots, config=CONFIG):
    lv = cfg['liquidity_filter']['levels']
    until = cfg['screening'].get('until')
    L = [f'# Báo cáo phân cụm lại v2 — {out.name}', '',
         'Thử nghiệm mô tả, ex post. **Chưa thay mô hình đang phục vụ (bundle v2).** Không dùng lợi nhuận/Sharpe để chọn.', '',
         *([f'**Chỉ sàng lọc trên các kỳ đến {until}** (giai đoạn development của M2); holdout 2024–2025 không tham gia chọn.', '']
           if until else []),
         f'## Quy tắc (đăng ký trước: `{config}`)', '',
         f'- **Lọc thanh khoản** (mã bị lọc nhận nhãn riêng "Kém thanh khoản", không tham gia phân cụm/thước đo): '
         f'*nhẹ* = >{lv["light"]["zero_volume_share_gt"]:.0%} phiên không khớp trong 63 phiên hoặc thanh khoản < '
         f'{lv["light"]["liquidity_21_lt"] / 1e6:.0f} triệu đ/ngày; *chặt* = >{lv["strict"]["zero_volume_share_gt"]:.0%} '
         f'hoặc < {lv["strict"]["liquidity_21_lt"] / 1e6:.0f} triệu đ/ngày. Ngưỡng là lựa chọn nghiệp vụ, owner chọn mức.',
         '- **Thuật toán:** K-Means, PCA (giữ 80% phương sai) + K-Means, Ward, GMM; k = 3–8; biến đổi T1 (log thanh khoản, cắt đuôi 1–99%, z-score).',
         f'- **Chấp nhận được:** cụm nhỏ nhất ≥ {cfg["admissible"]["min_cluster_share"]:.0%} ở ≥ '
         f'{cfg["admissible"]["share_of_snapshots"]:.0%} số kỳ và độ ổn định khi lấy mẫu con 90% (ARI trung vị) ≥ {cfg["admissible"]["median_stability"]}.',
         '- **Chọn:** hạng trung bình trên 5 thước đo — silhouette ↑, Davies-Bouldin ↓, Calinski-Harabasz ↑, độ ổn định ↑, '
         'ARI giữa hai kỳ liền nhau ↑. Hạng thấp nhất thắng; hòa thì k nhỏ hơn.', '',
         '## Tóm tắt', '']
    rows = []
    for g in groups:
        c = choices[g]
        snaps = snapshots[g]
        rows.append(dict(nhóm=GROUP[g], **{'mã/kỳ (trung vị)': int(np.median([len(s.tickers) for s in snaps]))},
                         đề_xuất=f'{ALGO[c["algo"]]} k={c["k"]}' if c else 'không đạt',
                         silhouette=fmt(c and c['silhouette']), DB=fmt(c and c['davies_bouldin']),
                         ổn_định=fmt(c and c['stability'], 2), ARI_thời_gian=fmt(c and c['temporal_ari'], 2),
                         cụm_nhỏ_nhất=fmt(c and c['median_min_share'], 2)))
    L += [md(pd.DataFrame(rows)), '',
          '*Thước đo chỉ so được trong cùng một nhóm (cùng tập mã và cùng không gian đặc trưng).*', '']
    for g in groups:
        c = choices[g]
        L += [f'## {GROUP[g]}', '']
        if g.startswith('A_'):
            level = g.split('_')[1]
            last = snapshots[g][-1].date
            L += [f'Kỳ {last}: {len(snapshots[g][-1].tickers)} mã được phân cụm, {len(excluded[level][last])} mã '
                  '"Kém thanh khoản" tách riêng.', '']
        if c:
            prof = pd.DataFrame(c['profile'])
            feats = [f for f in prof.columns if f not in ('cluster', 'size')]
            prof[feats] = prof[feats].map(lambda v: f'{v:.3g}')
            L += [f'**Đề xuất: {ALGO[c["algo"]]} · k={c["k"]}** (hạng trung bình {c["score"]:.2f}). '
                  f'Trung vị đặc trưng gốc từng cụm ({c["profile_date"]}):', '', md(prof), '']
        top = sorted([s for s in summary if s['group'] == g],
                     key=lambda s: (s['score'] is None, s['score'] if s['score'] is not None else 0, -(s['silhouette'] or 0)))[:10]
        view = pd.DataFrame([dict(thuật_toán=ALGO[s['algo']], k=s['k'], đạt='đạt' if s['admissible'] else 'không',
                                  hạng=fmt(s['score'], 2), cân_bằng=fmt(s['balanced_fraction'], 2),
                                  cụm_nhỏ_nhất=fmt(s['median_min_share'], 2), silhouette=fmt(s['silhouette']),
                                  DB=fmt(s['davies_bouldin']), CH=fmt(s['calinski_harabasz'], 0),
                                  ổn_định=fmt(s['stability'], 2), ARI_thời_gian=fmt(s['temporal_ari'], 2)) for s in top])
        L += ['Top 10 cấu hình:', '', md(view), '']
    L += ['## Giới hạn', '',
          '- Lọc chặt bỏ khoảng 60% số mã ở cuối 2025: kết quả chỉ mô tả nhóm cổ phiếu có giao dịch thường xuyên.',
          '- Ward và GMM có lợi thế/khó khăn khác nhau với silhouette/DB (thiên về cụm tròn); vì vậy chọn theo hạng nhiều thước đo.',
          '- ARI theo thời gian ở đây đo giữa các kỳ sàng lọc (6 tháng/1 năm), vẫn là phân cụm độc lập từng kỳ, chưa phải phân cụm động.',
          '- B (tài chính) không lọc thanh khoản; C dùng A đã lọc nên chỉ gồm mã thanh khoản đủ.', '']
    (out / 'report.md').write_text('\n'.join(L), encoding='utf-8')


if __name__ == '__main__':
    main()
