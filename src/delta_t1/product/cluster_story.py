"""Plain-language cluster names and one-sentence descriptions for the product layer.

Derived only from how a cluster's members differ from the cohort the model was fitted
on: the mean z-score of each feature (same transform as the model) picks what stands
out, raw medians give the numbers. Nothing is refitted and no returns are used.
"""
import numpy as np

# feature -> (theme, phrase when high, phrase when low)
THEMES = {
    'mom_21': ('momentum', 'Đà tăng giá mạnh', 'Giá đang giảm'),
    'mom_63': ('momentum', 'Đà tăng giá mạnh', 'Giá đang giảm'),
    'mom_126': ('momentum', 'Đà tăng giá mạnh', 'Giá đang giảm'),
    'mom_252': ('momentum', 'Đà tăng giá mạnh', 'Giá đang giảm'),
    'vol_63': ('volatility', 'biến động mạnh', 'ít biến động'),
    'downside_vol_63': ('volatility', 'biến động mạnh', 'ít biến động'),
    'mdd_126': ('drawdown', 'ít bị sụt giảm', 'từng sụt giảm sâu'),
    'beta_126': ('beta', 'nhạy với thị trường', 'ít nhạy với thị trường'),
    'liquidity_21': ('liquidity', 'thanh khoản cao', 'thanh khoản thấp'),
    'roe': ('profitability', 'sinh lời cao', 'sinh lời thấp'),
    'roa': ('profitability', 'sinh lời cao', 'sinh lời thấp'),
    'gross_margin': ('margin', 'biên lãi cao', 'biên lãi mỏng'),
    'net_margin': ('margin', 'biên lãi cao', 'biên lãi mỏng'),
    'debt_to_equity': ('leverage', 'nợ cao', 'nợ thấp'),
    'current_ratio': ('short_liquidity', 'khả năng trả nợ ngắn hạn tốt', 'khả năng trả nợ ngắn hạn yếu'),
    'asset_turnover': ('turnover', 'vòng quay tài sản nhanh', 'vòng quay tài sản chậm'),
    'revenue_growth': ('growth', 'doanh thu tăng nhanh', 'doanh thu tăng chậm'),
    'cfo_to_ni': ('cash', 'lợi nhuận có dòng tiền tốt', 'dòng tiền yếu so với lợi nhuận'),
}
NEUTRAL = 'Gần mức chung'
MIN_Z = 0.25


def _fmt(value, unit):
    if value is None or not np.isfinite(value):
        return '—'
    if unit == 'percent':
        return f'{value * 100:+.0f}%'.replace('.', ',')
    if unit == 'vnd':
        return f'{value / 1e9:.1f} tỷ đ/ngày'.replace('.', ',') if value >= 1e9 else f'{value / 1e6:.0f} triệu đ/ngày'
    return f'{value:.2f}'.replace('.', ',')


def themes_for(z_mean, features):
    """Strongest feature per theme, ordered by |z| (largest first)."""
    best = {}
    for j, f in enumerate(features):
        if f not in THEMES or not np.isfinite(z_mean[j]):
            continue
        theme = THEMES[f][0]
        if theme not in best or abs(z_mean[j]) > abs(z_mean[best[theme]]):
            best[theme] = j
    return sorted(best.values(), key=lambda j: -abs(z_mean[j]))


def phrase(feature, z):
    _, high, low = THEMES[feature]
    return high if z > 0 else low


def describe_clusters(raw, z, labels, features, definitions):
    """{cluster: {name, description}}. raw/z/labels cover the rows that defined the clusters."""
    features = list(features)
    overall = np.nanmedian(raw, axis=0)
    info = {}
    for c in sorted(set(labels.tolist())):
        member = labels == c
        z_mean = np.nanmean(z[member], axis=0)
        info[c] = dict(order=themes_for(z_mean, features), z=z_mean, median=np.nanmedian(raw[member], axis=0))
    stories = {}
    for c, i in info.items():
        strong = [j for j in i['order'] if abs(i['z'][j]) >= MIN_Z]
        parts = [phrase(features[j], i['z'][j]) for j in strong[:2]]
        stories[c] = dict(parts=parts, strong=strong)
    # Unique names: add a third trait only where two clusters would read the same.
    names = {}
    for c, s in stories.items():
        if s['parts']:
            names[c] = ', '.join(s['parts'])
        elif info[c]['order']:  # nothing stands out: name the largest (mild) difference
            j = info[c]['order'][0]
            s['strong'] = info[c]['order'][:1]
            names[c] = f'{phrase(features[j], info[c]["z"][j])} (nhẹ)'
        else:
            names[c] = NEUTRAL
    for c, name in list(names.items()):
        if list(names.values()).count(name) > 1 and len(stories[c]['strong']) > 2:
            j = stories[c]['strong'][2]
            names[c] = f'{name}, {phrase(features[j], info[c]["z"][j])}'
    out = {}
    for c, name in names.items():
        name = name[0].upper() + name[1:]
        facts = []
        for j in stories[c]['strong'][:2]:
            f = features[j]
            d = definitions.get(f, {})
            facts.append(f'{d.get("label", f)} trung vị {_fmt(info[c]["median"][j], d.get("unit"))} '
                         f'(chung: {_fmt(overall[j], d.get("unit"))})')
        description = ('; '.join(facts) + '.') if facts else 'Các đặc trưng gần mức chung của nhóm được phân cụm.'
        out[c] = dict(name=name, description=description)
    return out
