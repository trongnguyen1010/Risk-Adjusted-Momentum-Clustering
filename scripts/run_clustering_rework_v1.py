"""Clustering rework v1 (owner request 25/10/2026): sweep transforms x k-means/GMM x k=3-8.

Reads the served terminal.sqlite and indicators_v1 read-only; writes a new run under
data/experiments/clustering_rework_v1/<run-id>/ with sweep.csv, summary.csv,
selected assignments, profiles and report.md. The served model is not changed.
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

from delta_t1.experiments import clustering_rework as cr  # noqa: E402

CONFIG = 'configs/experiments/clustering_rework_v1.json'
TERMINAL = 'data/web/delta-intelligence-v1/terminal.sqlite'
INDICATORS = 'configs/product/indicators_v1.json'
OUT = 'data/experiments/clustering_rework_v1'
SERVED_K = {'A': 2, 'B': 3, 'C': 3, 'B2': 3}
CODE = ['scripts/run_clustering_rework_v1.py', 'src/delta_t1/experiments/clustering_rework.py',
        'src/delta_t1/clustering/robust_transforms.py', CONFIG]
LABEL = {'A': 'A – Thị trường (tháng)', 'B': 'B – Tài chính 6 tỷ số cũ (năm)',
         'B2': 'B2 – Tài chính bộ chỉ số mới, phi tài chính (năm)', 'C': 'C – Kết hợp (tháng 12)'}
RECIPE = {'T0': 'gốc (như đang phục vụ)', 'T1': 'log + cắt đuôi 1–99% + z-score', 'T2': 'xếp hạng → điểm chuẩn'}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def log(message):
    print(time.strftime('%H:%M:%S'), message, flush=True)


def fmt(x, d=3):
    return '—' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{x:.{d}f}'


def md(frame):
    cols = list(frame.columns)
    lines = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    lines += ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in frame.itertuples(index=False)]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--families', default='A,B,B2,C')
    args = parser.parse_args()
    cfg = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    pointer = json.loads((ROOT / INDICATORS).read_text(encoding='utf-8'))
    pins = {p: sha(p) for p in CODE + [TERMINAL, pointer['file']]}
    run_id = 'rework-' + hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()[:16]
    out = ROOT / OUT / run_id
    out.mkdir(parents=True, exist_ok=True)
    families = args.families.split(',')

    sweep_rows, series_rows, profile_rows, choices, baselines = [], [], [], {}, []
    for family in families:
        if family == 'B2':
            screen = full = cr.load_indicators(ROOT / pointer['file'], cfg['families']['B2']['features'])
        elif family == 'A':
            screen = cr.load_terminal(ROOT / TERMINAL, 'A', cfg['families']['A']['screen_months'])
            full = cr.load_terminal(ROOT / TERMINAL, 'A')
        else:
            screen = full = cr.load_terminal(ROOT / TERMINAL, family)
        log(f'{family}: {len(screen)} screening snapshots, n={min(s.raw.shape[0] for s in screen)}..{max(s.raw.shape[0] for s in screen)}')
        rows = cr.sweep(screen, cfg, progress=lambda s: log(f'  {family} {s.date} done'))
        # The served configuration (baseline transform, served k) for comparison.
        served = cr.sweep(screen, cfg, recipes=('T0',), algos=['kmeans'], ks=[SERVED_K[family]])
        for r in served:
            r['recipe'] = 'SERVED'
        sweep_rows += rows + served
        summary = cr.summarize(rows + served, cfg)
        choice = cr.select(summary, family)
        choices[family] = choice
        baselines += [s for s in summary if s['recipe'] == 'SERVED']
        if choice:
            log(f'{family}: selected {choice["recipe"]} {choice["algo"]} k={choice["k"]}; full series {len(full)} snapshots')
            series = cr.full_series(full, choice, cfg)
            for s in series:
                labels = s.pop('labels')
                series_rows.append(dict(family=family, **s))
                for t, c in labels.items():
                    profile_rows.append(dict(family=family, date=s['date'], ticker=t, cluster=c, kind='assignment'))
            last = full[-1]
            choices[family]['profile'] = cr.profile(last, {r['ticker']: r['cluster'] for r in profile_rows
                                                           if r['family'] == family and r['date'] == last.date})
            choices[family]['profile_date'] = last.date
        else:
            log(f'{family}: no admissible configuration')

    sweep = pd.DataFrame(sweep_rows)
    summary = pd.DataFrame(cr.summarize(sweep_rows, cfg))
    sweep.to_csv(out / 'sweep.csv', index=False)
    summary.sort_values(['family', 'recipe', 'algo', 'k']).to_csv(out / 'summary.csv', index=False)
    pd.DataFrame(series_rows).to_csv(out / 'selected-series.csv', index=False)
    pd.DataFrame(profile_rows).drop(columns='kind').to_csv(out / 'selected-assignments.csv.gz', index=False)
    (out / 'selection.json').write_text(json.dumps(choices, indent=2, ensure_ascii=False, default=float), encoding='utf-8')
    (out / 'input-pins.json').write_text(json.dumps(pins, indent=2), encoding='utf-8')
    write_report(out, cfg, summary, pd.DataFrame(series_rows), choices, families)
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.name != 'manifest.json'}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    for family in families:
        c = choices.get(family)
        print(family, 'selected:', f"{c['recipe']} {c['algo']} k={c['k']} sil={fmt(c['median_silhouette'])} min_share={fmt(c['median_min_share'], 2)}" if c else 'none')
    print('report:', (out / 'report.md').relative_to(ROOT).as_posix())


def write_report(out, cfg, summary, series, choices, families):
    L = [f'# Báo cáo phân cụm lại — {out.name}', '',
         'Thử nghiệm mô tả, ex post, **chưa thay mô hình đang phục vụ**. Chọn cấu hình chỉ bằng hình học, '
         'độ cân bằng và độ ổn định; không dùng lợi nhuận/Sharpe.', '',
         '**Quy tắc (đăng ký trước, `configs/experiments/clustering_rework_v1.json`):** chấp nhận được nếu '
         f'cụm nhỏ nhất ≥ {cfg["admissible"]["min_cluster_share"]:.0%} số mã ở ≥ {cfg["admissible"]["share_of_snapshots"]:.0%} '
         f'số kỳ và ARI giữa các seed (trung vị) ≥ {cfg["admissible"]["median_seed_ari"]}. Trong nhóm chấp nhận được, '
         'chọn silhouette trung vị cao nhất (đo chung trên không gian T1); chênh ≤ 0,01 thì ưu tiên k nhỏ, T1, k-means.', '',
         'Biến đổi: ' + '; '.join(f'**{k}** = {v}' for k, v in RECIPE.items()) + '.', '']
    for family in families:
        s = summary[summary.family == family].copy()
        served = s[s.recipe == 'SERVED']
        c = choices.get(family)
        L += [f'## {LABEL[family]}', '']
        if len(served):
            b = served.iloc[0]
            L += [f'**Đang phục vụ** (k-means, k={b.k}): cụm lớn nhất trung vị {fmt(b.median_max_share, 2)} số mã, '
                  f'cụm nhỏ nhất {fmt(b.median_min_share, 3)}, silhouette (không gian T1) {fmt(b.median_silhouette)}.', '']
        if c:
            ser = series[series.family == family]
            L += [f'**Đề xuất: {RECIPE[c["recipe"]]} · {c["algo"]} · k={c["k"]}.** Silhouette trung vị {fmt(c["median_silhouette"])}, '
                  f'Davies-Bouldin {fmt(c["median_davies_bouldin"])}, cụm nhỏ nhất {fmt(c["median_min_share"], 2)} / lớn nhất '
                  f'{fmt(c["median_max_share"], 2)}, ARI seed {fmt(c["median_seed_ari"], 2)}. Chạy trên {len(ser)} kỳ: '
                  f'ARI giữa hai kỳ liền nhau trung vị {fmt(ser.temporal_ari.median(), 2)}; '
                  f'{(ser.min_share >= cfg["admissible"]["min_cluster_share"]).mean():.0%} số kỳ đạt ngưỡng cỡ cụm.', '']
            prof = pd.DataFrame(c['profile'])
            feats = [f for f in prof.columns if f not in ('cluster', 'size')]
            prof[feats] = prof[feats].map(lambda v: f'{v:.3g}')
            L += [f'Trung vị đặc trưng gốc từng cụm ({c["profile_date"]}):', '', md(prof), '']
        else:
            L += ['**Không có cấu hình nào đạt quy tắc.** Xem bảng dưới để thấy ràng buộc nào bị vi phạm.', '']
        top = s[s.recipe != 'SERVED'].sort_values(['admissible', 'median_silhouette'], ascending=[False, False]).head(10)
        view = top[['recipe', 'algo', 'k', 'admissible', 'balanced_fraction', 'median_min_share', 'median_max_share',
                    'median_silhouette', 'median_davies_bouldin', 'median_seed_ari']].copy()
        for col in ('balanced_fraction', 'median_min_share', 'median_max_share', 'median_seed_ari'):
            view[col] = view[col].map(lambda v: fmt(v, 2))
        for col in ('median_silhouette', 'median_davies_bouldin'):
            view[col] = view[col].map(fmt)
        view['admissible'] = view['admissible'].map({True: 'đạt', False: 'không'})
        L += ['Top 10 cấu hình (đạt trước, rồi silhouette):', '', md(view), '']
    L += ['## Giới hạn', '',
          '- Silhouette đo trên không gian T1; k-means có lợi thế tự nhiên trên thước đo này so với GMM.',
          '- B2 chỉ dùng mã phi tài chính có đủ 9 chỉ số trong năm (không điền giá trị thiếu).',
          '- Nhãn giữa các kỳ fit độc lập không cùng ý nghĩa; ARI theo thời gian chỉ đo mức xáo trộn thành viên.',
          '- Chưa phải phân cụm động (dynamic clustering) và chưa dùng cho backtest/PIT.', '']
    (out / 'report.md').write_text('\n'.join(L), encoding='utf-8')


if __name__ == '__main__':
    main()
