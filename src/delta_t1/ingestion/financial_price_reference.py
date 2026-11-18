"""At most four public CafeF pages for financial reference valuation only."""
import json
from pathlib import Path
from .cafef_financial import encoded, immutable_write, now
from .sources.base import AccessControlError, RateLimitError, PublicJsonClient
from .sources.cafef import CafeFSource, classify_cafef_page_row, map_trade_history_row, price_band_row_status
from .financial_pdf_evidence import digest


def collect(config, output, adapter=None):
    if (config.get('financial_features_allowed') is not False or config.get('canonical_market_write_allowed') is not False
            or config['symbols'] != {'VNM': 'HOSE', 'PVS': 'HNX'} or config['target_date'] != '2026-08-28'
            or config['max_pages_per_symbol'] != 2):
        raise ValueError('bounded reference-only price request required')
    adapter = adapter or CafeFSource(PublicJsonClient(attempts=1))
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    records, quotes, stopped = [], [], False
    for symbol, exchange in config['symbols'].items():
        for page in range(1, 3):
            if stopped:
                records.append(dict(symbol=symbol, page=page, status='NOT_REQUESTED_HARD_STOP')); break
            try:
                response = adapter.acquire_trade_history_page(dict(symbol=symbol, page_index=page, page_size=30))
                path = out / f'{symbol}-page-{page}.json'
                immutable_write(path, response['body'])
                records.append(dict(symbol=symbol, page=page, status='DOWNLOADED', url=response['url'],
                    fetched_at=now(), path=path.name, sha256=digest(response['body'])))
                matches = []
                for index, raw in enumerate(response['payload']['Data']):
                    if classify_cafef_page_row(raw['TradeDate'], page, index) != 'HISTORICAL': continue
                    row = map_trade_history_row(raw, symbol, exchange)
                    if row['trade_date'] == config['target_date']:
                        if price_band_row_status(row) != 'VALID' or not row['cafef_close_price'] or row['cafef_close_price'] <= 0:
                            raise ValueError('invalid target price band')
                        matches.append(dict(ticker=symbol, exchange=exchange, trade_date=row['trade_date'],
                            raw_close=row['cafef_close_price'], available_at=row['trade_date']+'T17:00:00+07:00',
                            security_id=f'PROVISIONAL:{exchange}:{symbol}', source='cafef', adjustment_basis='RAW_CLOSE',
                            evidence=dict(path=path.name, sha256=digest(response['body']), row_index=index, page=page,
                                adapter_version='cafef-research-demo-4', multiplier=1000,
                                unit_policy='REUSE_EXISTING_APPROVED_CAFEF_TRADEHISTORY_MAPPING'),
                            financial_features_allowed=False, canonical_market_accepted=False))
                if len(matches) > 1: raise ValueError('duplicate target price rows')
                if matches:
                    quotes.extend(matches); break
            except (AccessControlError, RateLimitError) as exc:
                stopped = True; records.append(dict(symbol=symbol, page=page, status='HARD_STOP', error=str(exc))); break
            except (ValueError, OSError) as exc:
                records.append(dict(symbol=symbol, page=page, status='FAILED', error=str(exc))); break
    for name, data in [('config.json', encoded(config)), ('quotes.json', encoded(quotes)),
                       ('inventory.json', encoded(dict(requests=records, financial_features_allowed=False))),
                       ('collector.py', Path(__file__).read_bytes())]:
        immutable_write(out / name, data)
    immutable_write(out / 'manifest.json', encoded(dict(files={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()})))
    return records, quotes
