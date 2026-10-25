"""Read-only access to computed annual indicators (D-IND-01). Never recomputes values.

The SQLite file is pinned by configs/product/indicators_v1.json (path + sha256);
a missing or changed file leaves the endpoints unavailable instead of serving
unverified numbers.
"""
from contextlib import closing
from datetime import date as calendar_date, timedelta
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sqlite3

from .repository import MissingData, InvalidQuery

YEARS = (2016, 2025)
FINANCIAL_SECTORS = {'BANK', 'SECURITIES', 'INSURANCE'}
SECTOR_LABELS = {'BANK': 'Ngân hàng', 'SECURITIES': 'Chứng khoán', 'INSURANCE': 'Bảo hiểm',
                 'NON_FINANCIAL': 'Doanh nghiệp phi tài chính', 'OTHER': 'Khác'}

# One sentence of purpose + formula per metric; the UI shows these as tooltips.
METRICS = {
    'eps': ('Định giá', 'EPS', 'vnd', 'Lợi nhuận mỗi cổ phiếu. = LNST cổ đông công ty mẹ / số CP.'),
    'bvps': ('Định giá', 'BVPS', 'vnd', 'Giá trị sổ sách mỗi cổ phiếu. = VCSH công ty mẹ / số CP.'),
    'pe': ('Định giá', 'P/E', 'times', 'Nhà đầu tư trả bao nhiêu đồng cho 1 đồng lợi nhuận. = Giá / EPS.'),
    'pb': ('Định giá', 'P/B', 'times', 'Giá so với giá trị sổ sách. = Giá / BVPS.'),
    'market_cap': ('Định giá', 'Vốn hóa', 'vnd', 'Giá trị thị trường của công ty. = Giá × số CP.'),
    'roe': ('Sinh lời', 'ROE', 'percent', 'Lãi trên vốn chủ. = LNST công ty mẹ / VCSH bình quân.'),
    'roa': ('Sinh lời', 'ROA', 'percent', 'Lãi trên tổng tài sản. = LNST / tổng tài sản bình quân.'),
    'gross_margin': ('Sinh lời', 'Biên lãi gộp', 'percent', 'Phần lãi gộp trên doanh thu. = LN gộp / doanh thu thuần.'),
    'net_margin': ('Sinh lời', 'Biên lãi ròng', 'percent', 'Phần lãi ròng trên doanh thu. = LNST / doanh thu thuần.'),
    'revenue_growth': ('Tăng trưởng', 'Tăng trưởng doanh thu', 'percent', 'Doanh thu tăng so với năm trước.'),
    'profit_growth': ('Tăng trưởng', 'Tăng trưởng lợi nhuận', 'percent', 'LNST công ty mẹ tăng so với năm trước.'),
    'debt_to_equity': ('An toàn tài chính', 'Nợ / VCSH', 'times', 'Mức dùng nợ so với vốn chủ. = Nợ phải trả / VCSH.'),
    'current_ratio': ('An toàn tài chính', 'Thanh toán hiện hành', 'times', 'Khả năng trả nợ ngắn hạn. = TS ngắn hạn / nợ ngắn hạn.'),
    'asset_turnover': ('An toàn tài chính', 'Vòng quay tài sản', 'times', 'Tài sản tạo ra bao nhiêu doanh thu. = Doanh thu / TS bình quân.'),
    'cfo_to_ni': ('An toàn tài chính', 'Dòng tiền / lợi nhuận', 'times', 'Lợi nhuận có thành tiền thật không. = CFO / LNST.'),
    'f_score': ('Điểm sức khỏe', 'F-score', 'points', 'Sức khỏe tài chính 0–9 điểm; càng cao càng tốt.'),
    'm_score': ('Điểm sức khỏe', 'M-score', 'score', 'Dấu hiệu bất thường trong số liệu kế toán; trên −1,78 cần chú ý.'),
    'z_score': ('Điểm sức khỏe', 'Z-score', 'score', 'Nguy cơ kiệt quệ tài chính; dưới 1,81 là rủi ro cao.'),
    'z_score_dp': ('Điểm sức khỏe', "Z''-score", 'score', 'Biến thể Z không cần giá; dưới 1,1 là rủi ro cao.'),
}
GROUPS = ('Định giá', 'Sinh lời', 'Tăng trưởng', 'An toàn tài chính', 'Điểm sức khỏe')
CARD_METRICS = ('eps', 'pe', 'pb', 'roe', 'f_score', 'z_score')
BANK_CARD_METRICS = ('eps', 'pe', 'pb', 'roe', 'roa', 'bvps')
F_SIGNAL_TEXT = {
    'roa_positive': 'ROA dương: công ty có lãi.',
    'cfo_positive': 'Dòng tiền kinh doanh dương.',
    'roa_improving': 'ROA cao hơn năm trước.',
    'accruals': 'Dòng tiền kinh doanh lớn hơn lợi nhuận kế toán.',
    'leverage_falling': 'Tỷ lệ nợ vay dài hạn giảm.',
    'liquidity_improving': 'Khả năng thanh toán ngắn hạn tốt lên.',
    'no_dilution': 'Không phát hành thêm cổ phiếu.',
    'gross_margin_improving': 'Biên lãi gộp tăng.',
    'turnover_improving': 'Vòng quay tài sản tăng.',
}
M_VARIABLE_TEXT = {
    'DSRI': 'Phải thu so với doanh thu', 'GMI': 'Biên lãi gộp suy giảm', 'AQI': 'Chất lượng tài sản',
    'SGI': 'Tăng trưởng doanh thu', 'DEPI': 'Tốc độ khấu hao', 'SGAI': 'Chi phí bán hàng & quản lý',
    'LVGI': 'Đòn bẩy', 'TATA': 'Lợi nhuận chưa thành tiền / tài sản'}
Z_COMPONENT_TEXT = {
    'X1': 'Vốn lưu động / tổng tài sản', 'X2': 'LN chưa phân phối / tổng tài sản', 'X3': 'EBIT / tổng tài sản',
    'X4': 'Vốn hóa / nợ phải trả', 'X5': 'Doanh thu / tổng tài sản'}


def f_rating(score):
    return None if score is None else 'Mạnh' if score >= 7 else 'Trung bình' if score >= 4 else 'Yếu'


def z_zone(score):
    return None if score is None else 'Nguy hiểm' if score < 1.81 else 'Cảnh báo' if score <= 2.99 else 'An toàn'


def m_flag(score):
    return None if score is None else 'Có dấu hiệu bất thường' if score > -1.78 else 'Bình thường'


RATINGS = {'f_score': f_rating, 'z_score': z_zone, 'm_score': m_flag}


def sha256(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def finite(value):
    return value if isinstance(value, (int, float)) and math.isfinite(value) else None


class FundamentalsRepository:
    def __init__(self, database, expected_sha256=None):
        self.database = Path(database).resolve()
        if not self.database.is_file():
            raise MissingData('Chưa build indicators.sqlite.')
        if expected_sha256 and sha256(self.database) != expected_sha256:
            raise MissingData('indicators.sqlite checksum mismatch; không phục vụ số chưa xác minh.')
        with closing(self.connect()) as db:
            self.metadata = dict(db.execute('select key, value from metadata').fetchall())

    @classmethod
    def from_config(cls, root, config='configs/product/indicators_v1.json'):
        root = Path(root).resolve()
        pointer = json.loads((root / config).read_bytes())
        manifest = root / pointer['manifest']
        if not manifest.is_file() or sha256(manifest) != pointer['manifest_sha256']:
            raise MissingData('Indicators manifest missing or checksum mismatch.')
        if json.loads(manifest.read_bytes()).get('indicators.sqlite') != pointer['file_sha256']:
            raise MissingData('indicators.sqlite is not pinned by its manifest.')
        return cls(root / pointer['file'], pointer['file_sha256'])

    def connect(self):
        db = sqlite3.connect(self.database.as_uri() + '?mode=ro', uri=True)
        db.execute('PRAGMA query_only=ON')
        return db

    def rows(self, sql, args=()):
        with closing(self.connect()) as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute(sql, args).fetchall()]

    @lru_cache(maxsize=512)
    def company(self, ticker):
        found = self.rows('select c.*, l.latest_fiscal_year, l.last_price, l.last_price_date, l.shares, '
                          'l.market_cap_last from company c left join latest l on l.ticker = c.ticker '
                          'where c.ticker = ?', (ticker.upper(),))
        if not found:
            raise MissingData('Mã không có trong bộ chỉ số tài chính.')
        row = found[0]
        row['sector_label'] = SECTOR_LABELS.get(row['sector_group'], row['sector_group'])
        row['financial_sector'] = row['sector_group'] in FINANCIAL_SECTORS
        return row

    @lru_cache(maxsize=512)
    def cells(self, ticker):
        """{metric: {year: cell}} without inputs (small payload)."""
        out = {}
        for r in self.rows("select fiscal_year, metric, value, status, json_extract(inputs_json, '$.missing') as missing "
                           "from indicator_values where ticker = ? order by metric, fiscal_year", (ticker.upper(),)):
            missing = json.loads(r['missing']) if r['missing'] else []
            cell = dict(value=finite(r['value']), status=r['status'])
            if missing == ['NO_ANNUAL_REPORT']:
                cell['reason'] = 'NO_ANNUAL_REPORT'
            out.setdefault(r['metric'], {})[r['fiscal_year']] = cell
        return out

    def card(self, ticker, metric, year):
        cell = self.cells(ticker).get(metric, {}).get(year, dict(value=None, status='MISSING_INPUT'))
        group, label, unit, description = METRICS[metric]
        rating = RATINGS.get(metric)
        return dict(metric=metric, label=label, unit=unit, description=description, year=year, **cell,
                    rating=rating(cell['value']) if rating else None)

    def overview(self, ticker, prices=None):
        c = self.company(ticker)
        year = c['latest_fiscal_year']
        metrics = BANK_CARD_METRICS if c['financial_sector'] else CARD_METRICS
        return dict(ticker=c['ticker'], name=c['name'], exchange=c['exchange'], sector_group=c['sector_group'],
                    sector_label=c['sector_label'], financial_sector=c['financial_sector'], latest_fiscal_year=year,
                    price=price_summary(prices or []), market_cap=finite(c['market_cap_last']), shares=finite(c['shares']),
                    cards=[self.card(c['ticker'], m, year) for m in metrics] if year else [],
                    summary=self.summary(c['ticker'], year) if year else [])

    def summary(self, ticker, year):
        """Three short generated sentences; ranks are against the same fiscal year."""
        lines = []
        roe = [self.cells(ticker).get('roe', {}).get(y, {}).get('value') for y in range(year - 4, year + 1)]
        roe = [v for v in roe if v is not None]
        if len(roe) >= 3:
            avg = sum(roe) / len(roe)
            rank = self.percentile('roe', year, roe[-1]) if roe else None
            lines.append(f'ROE {len(roe)} năm trung bình {avg * 100:.0f}%'
                         + (f', năm {year} cao hơn {rank:.0f}% số mã.' if rank is not None else '.'))
        growth = self.cells(ticker).get('revenue_growth', {}).get(year, {}).get('value')
        if growth is not None:
            lines.append(f'Doanh thu năm {year} {"tăng" if growth >= 0 else "giảm"} {abs(growth) * 100:.0f}% so với năm trước.')
        f = self.cells(ticker).get('f_score', {}).get(year, {}).get('value')
        z = self.cells(ticker).get('z_score', {}).get(year, {}).get('value')
        if f is not None:
            lines.append(f'F-score {f:.0f}/9 ({f_rating(f).lower()})' + (f', Z-score vùng {z_zone(z).lower()}.' if z is not None else '.'))
        return lines[:3]

    @lru_cache(maxsize=64)
    def distribution(self, metric, year):
        return [r['value'] for r in self.rows("select value from indicator_values where metric = ? and fiscal_year = ? "
                                              "and status = 'OK' order by value", (metric, year))]

    def percentile(self, metric, year, value):
        values = self.distribution(metric, year)
        if not values:
            return None
        return 100 * sum(v < value for v in values) / len(values)

    def fundamentals(self, ticker, start=YEARS[0], end=YEARS[1]):
        if not (YEARS[0] <= start <= end <= YEARS[1]):
            raise InvalidQuery(f'Năm phải trong {YEARS[0]}–{YEARS[1]} và from ≤ to.')
        c = self.company(ticker)
        cells = self.cells(c['ticker'])
        years = list(range(start, end + 1))
        metrics = {m: {str(y): cells.get(m, {}).get(y, dict(value=None, status='MISSING_INPUT')) for y in years}
                   for m in METRICS}
        return dict(ticker=c['ticker'], financial_sector=c['financial_sector'], years=years, metrics=metrics,
                    definitions={m: dict(group=g, label=l, unit=u, description=d) for m, (g, l, u, d) in METRICS.items()},
                    groups=[dict(name=g, metrics=[m for m, v in METRICS.items() if v[0] == g]) for g in GROUPS])

    def scores(self, ticker, year):
        if not YEARS[0] <= year <= YEARS[1]:
            raise InvalidQuery(f'Năm phải trong {YEARS[0]}–{YEARS[1]}.')
        c = self.company(ticker)
        found = {r['metric']: r for r in self.rows(
            "select metric, value, status, inputs_json from indicator_values where ticker = ? and fiscal_year = ? "
            "and metric in ('f_score', 'm_score', 'z_score', 'z_score_dp')", (c['ticker'], year))}
        if not found:
            raise MissingData('Không có dữ liệu điểm cho năm này.')

        def head(metric):
            r = found[metric]
            inputs = json.loads(r['inputs_json'])
            rating = RATINGS.get(metric)
            value = finite(r['value'])
            return inputs, dict(value=value, status=r['status'], rating=rating(value) if rating else None,
                                missing=inputs.get('missing', []), flags=inputs.get('flags', []))

        f_inputs, f = head('f_score')
        f['known_signals'] = f_inputs.get('known_signals', 0)
        f['signals'] = [dict(name=k, passed=f_inputs.get('signals', {}).get(k), text=text) for k, text in F_SIGNAL_TEXT.items()]
        m_inputs, m = head('m_score')
        m['variables'] = [dict(name=k, value=finite(m_inputs.get('variables', {}).get(k)), text=text)
                          for k, text in M_VARIABLE_TEXT.items()]
        z_inputs, z = head('z_score')
        z['components'] = [dict(name=k, value=finite(z_inputs.get('variables', {}).get(k)), text=text)
                           for k, text in Z_COMPONENT_TEXT.items()]
        dp_inputs, dp = head('z_score_dp')
        return dict(ticker=c['ticker'], year=year, applicable=not c['financial_sector'],
                    f_score=f, m_score=m, z_score=z, z_score_dp=dp)

    def peer_rows(self, tickers):
        if not tickers:
            return []
        marks = ','.join('?' * len(tickers))
        rows = self.rows(f'select c.ticker, c.name, c.exchange, c.sector_group, l.latest_fiscal_year, '
                         f'l.market_cap_last, l.metrics_json from company c join latest l on l.ticker = c.ticker '
                         f'where c.ticker in ({marks})', tuple(tickers))
        out = []
        for r in rows:
            metrics = json.loads(r.pop('metrics_json') or '{}')
            r.update({m: finite(metrics.get(m, {}).get('value')) for m in ('pe', 'pb', 'roe', 'eps')})
            r['market_cap'] = finite(r.pop('market_cap_last'))
            out.append(r)
        return out

    def peers(self, ticker, cluster_members=None, basis=None, limit=9):
        """Same model cluster when given (closest market caps), else same sector group."""
        c = self.company(ticker)
        if not cluster_members:
            basis = 'SECTOR'
            cluster_members = [r['ticker'] for r in self.rows('select ticker from company where sector_group = ?',
                                                             (c['sector_group'],))]
        candidates = [r for r in self.peer_rows([t for t in set(cluster_members) if t != c['ticker']])
                      if r['market_cap']]
        cap = finite(c['market_cap_last'])
        if cap:
            candidates.sort(key=lambda r: (abs(math.log(r['market_cap'] / cap)), r['ticker']))
        else:
            candidates.sort(key=lambda r: -r['market_cap'])
        current = self.peer_rows([c['ticker']])
        return dict(ticker=c['ticker'], basis=basis, items=current + candidates[:limit])


def price_summary(points):
    """points: [(date 'YYYY-MM-DD', raw_close, adj_close)] ascending.

    The shown close is the raw VND close; % changes use adj_close only, so stock
    dividends/splits do not look like price drops. Each value uses one basis.
    """
    raw = [(d, r) for d, r, a in points if r is not None]
    adj = [(d, a) for d, r, a in points if a is not None]
    if not raw:
        return None
    last_date, last = raw[-1]
    end = calendar_date.fromisoformat(last_date)

    def close_on_or_before(day):
        found = [p for d, p in adj if d <= day.isoformat()]
        return found[-1] if found else None

    latest_adj = close_on_or_before(end)

    def change(base):
        return None if not base or latest_adj is None else latest_adj / base - 1

    earlier = [p for d, p in adj if d < last_date]
    return dict(close=last, date=last_date, close_basis='raw_close', change_basis='adj_close',
                change_1d=change(earlier[-1] if earlier else None),
                change_1m=change(close_on_or_before(end - timedelta(days=30))),
                change_ytd=change(close_on_or_before(calendar_date(end.year - 1, 12, 31))))
