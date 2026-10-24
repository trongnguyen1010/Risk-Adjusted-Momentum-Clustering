"""Build a read-only presentation index from pinned A/B/C artifacts, never fit."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import statistics
import time

from ..experiments.market_financial_integration import MARKET, HANDOFF, sha, inside, check_hashes
from ..experiments.dual_cluster_review import FINANCIAL, FEATURES_M, FEATURES_F

VERSION = 'delta-intelligence-v1'
FIELDS = FEATURES_M + FEATURES_F
DEFINITIONS = {
    'mom_21': ('Momentum · 1 month', '21-session adjusted-price momentum', 'percent'),
    'mom_63': ('Momentum · 3 months', '63-session adjusted-price momentum', 'percent'),
    'mom_126': ('Momentum · 6 months', '126-session adjusted-price momentum', 'percent'),
    'mom_252': ('Momentum · 12 months', '252-session adjusted-price momentum', 'percent'),
    'vol_63': ('Volatility · 63 sessions', 'sample_std(daily_returns, 63 sessions) * sqrt(252); annualized', 'ratio'),
    'mdd_126': ('Drawdown · 126 sessions', 'Maximum drawdown over 126 sessions', 'percent'),
    'beta_126': ('Market beta · 126 sessions', '126-session beta relative to VNINDEX', 'ratio'),
    'liquidity_21': ('Liquidity · 21 sessions', 'Mean matched traded value over 21 sessions; raw VND, not log', 'vnd'),
    'gross_margin': ('Gross margin', 'gross_profit / net_revenue', 'percent'),
    'net_margin': ('Net margin', 'net_profit / net_revenue', 'percent'),
    'liabilities_to_assets': ('Liabilities / assets', 'total_liabilities / ending_total_assets', 'ratio'),
    'current_ratio': ('Current ratio', 'current_assets / current_liabilities', 'ratio'),
    'operating_cashflow_to_assets': ('Operating cash flow / assets', 'operating_cash_flow / ending_total_assets', 'ratio'),
    'asset_turnover_ending_assets': ('Asset turnover', 'net_revenue / ending_total_assets; ending, not average assets', 'ratio'),
}


def numeric(value):
    if value is None or value == '' or isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def table(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def quantiles(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    def q(f):
        p = (len(values)-1)*f
        lo = int(p)
        return values[lo] + (values[min(lo+1,len(values)-1)]-values[lo])*(p-lo)
    return [values[0], q(.25), q(.5), q(.75), values[-1]]


def schema(db):
    db.executescript('''
    CREATE TABLE securities(ticker TEXT PRIMARY KEY,name TEXT,exchange TEXT,security_id TEXT,ambiguous INTEGER DEFAULT 0);
    CREATE TABLE observations(kind TEXT,date TEXT,ticker TEXT,security_id TEXT,cluster INTEGER,features TEXT,scope TEXT,PRIMARY KEY(kind,date,ticker));
    CREATE TABLE snapshots(kind TEXT,date TEXT,n INTEGER,k INTEGER,sizes TEXT,metrics TEXT,scope TEXT,PRIMARY KEY(kind,date));
    CREATE TABLE profiles(kind TEXT,date TEXT,cluster INTEGER,size INTEGER,means TEXT,medians TEXT,quartiles TEXT,PRIMARY KEY(kind,date,cluster));
    CREATE TABLE prices(ticker TEXT,security_id TEXT,date TEXT,adj_close REAL,raw_close REAL,volume REAL,basis TEXT,available_at TEXT,conflict INTEGER DEFAULT 0,PRIMARY KEY(security_id,date));
    CREATE TABLE relations(date TEXT,ticker TEXT,market_cluster INTEGER,financial_cluster INTEGER,combined_cluster INTEGER,coverage TEXT,PRIMARY KEY(date,ticker));
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
    CREATE INDEX observation_ticker ON observations(ticker,kind,date);
    CREATE INDEX observation_cluster ON observations(kind,date,cluster);
    CREATE INDEX prices_ticker_date ON prices(ticker,date);
    ''')


def export(root, output='data/web/delta-intelligence-v1', include_prices=True):
    root = Path(root).resolve()
    target = inside(root, output)
    if target.exists():
        raise FileExistsError('Presentation bundle already exists; use a new output/version, preserve existing bundle')
    target.mkdir(parents=True)
    temporary = target/'terminal.building.sqlite'
    final = target/'terminal.sqlite'
    db = sqlite3.connect(temporary)
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('PRAGMA synchronous=OFF')
    schema(db)
    pins = {}
    def pin(relative, expected=None):
        p = inside(root, relative)
        h = sha(p)
        if expected and h != expected:
            raise ValueError('source checksum mismatch: '+relative)
        pins[relative] = dict(sha256=h,size=p.stat().st_size)
        return p
    def load(relative, expected=None):
        return json.loads(pin(relative,expected).read_bytes())
    def csv_rows(relative, expected=None):
        return table(pin(relative,expected))
    market_manifest = load(MARKET+'/manifest.json')
    handoff = load(HANDOFF+'/m2_to_m3_handoff_manifest.json')
    fm = load(FINANCIAL+'/manifest.json')
    combined_ref = load('artifacts/reports/combined-reference-v1/result-ref.json')
    combined = combined_ref['path']
    cm = load(combined+'/manifest.json',combined_ref['manifest_sha256'])
    cfg_c = load(combined+'/protocol.json',cm['protocol.json'])
    checks = {
        'market': load('M2/artifacts/market-financial-integration-v1/verification.json'),
        'financial': load('M2/artifacts/financial-execution56-integration-review-v2/verification.json'),
        'combined': load('artifacts/reports/combined-reference-v1/verification.json'),
    }
    security_file = pin(MARKET+'/canonical/securities.jsonl',market_manifest['outputs']['canonical/securities.jsonl'])
    securities = {}
    with security_file.open(encoding='utf-8') as f:
        for line in f:
            r = json.loads(line); t = r['ticker']
            if t in securities and securities[t]['security_id'] != r['security_id']:
                securities[t]['ambiguous'] = 1
            else:
                securities[t] = dict(ticker=t,name=r.get('company_name') or t,exchange=r.get('exchange') or '',security_id=r['security_id'],ambiguous=0)
    db.executemany('INSERT INTO securities VALUES(:ticker,:name,:exchange,:security_id,:ambiguous)',securities.values())
    labels = csv_rows(HANDOFF+'/m2_cluster_labels_for_m3.csv',handoff['artifacts_sha256']['m2_cluster_labels_for_m3.csv'])
    lookup = {(r['snapshot_date'],r['security_id']):r for r in labels}
    if len(lookup) != len(labels):
        raise ValueError('duplicate market assignment')
    grouped = defaultdict(list)
    feature_file = pin(MARKET+'/canonical/feature_snapshots.jsonl',market_manifest['outputs']['canonical/feature_snapshots.jsonl'])
    seen = set()
    with feature_file.open(encoding='utf-8') as f:
        for line in f:
            r = json.loads(line); key=(r['as_of_date'],r['security_id'])
            if key not in lookup: continue
            label = lookup[key]
            if key in seen or r['ticker'] != label['ticker'] or not r.get('market_feature_ready_v2',r.get('market_feature_ready')):
                raise ValueError('invalid market feature/label join')
            seen.add(key)
            values = {k:numeric(r.get(k)) for k in FEATURES_M}
            if any(v is None for v in values.values()):
                raise ValueError('eligible market feature missing')
            scope = 'MARKET_ONLY_PROVISIONAL_IDENTITY_'+label['membership_period'].upper()
            record = ('market',r['as_of_date'],r['ticker'],r['security_id'],int(label['cluster_label']),encoded(values),scope)
            db.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?)',record)
            grouped['market',r['as_of_date'],int(label['cluster_label'])].append(values)
    if seen != set(lookup): raise ValueError('missing market rows')
    financial_features = csv_rows(FINANCIAL+'/features.csv',fm['features.csv'])
    financial_labels = {(r['registry_id'],r['year']):r for r in csv_rows(FINANCIAL+'/assignments.csv',fm['assignments.csv'])}
    for r in financial_features:
        label = financial_labels[r['registry_id'],r['year']]
        values = {k:numeric(r.get(k)) for k in FEATURES_F}
        if any(v is None for v in values.values()):raise ValueError('financial core feature missing')
        db.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?)',('financial',r['year'],r['symbol'],r['registry_id'],int(label['cluster_id']),encoded(values),'EX_POST_FISCAL_YEAR_REFERENCE_NOT_PIT'))
        grouped['financial',r['year'],int(label['cluster_id'])].append(values)
    combined_labels = csv_rows(combined+'/assignments.csv',cm['assignments.csv'])
    for r in combined_labels:
        values={k:numeric(r.get(k)) for k in FIELDS}
        if any(v is None for v in values.values()):raise ValueError('combined feature missing')
        label=int(r['combined_cluster_id'])
        db.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?)',('combined',r['snapshot_date'],r['symbol'],r['market_security_id'],label,encoded(values),'EX_POST_ANNUAL_DESCRIPTIVE_NOT_PIT'))
        grouped['combined',r['snapshot_date'],label].append(values)
    profiles = csv_rows('artifacts/reports/cluster-comparison-v1/cluster-catalog-a-b-c.csv')
    fm_snapshots = load(FINANCIAL+'/snapshots.json',fm['snapshots.json'])
    cm_snapshots = load(combined+'/snapshots.json',cm['snapshots.json'])
    diagnostics = {}
    for rel in ['M2/artifacts/m2-task4-kmeans-baseline-v1/diagnostics.csv','M2/artifacts/m2-final-holdout/diagnostics.csv']:
        for row in csv_rows(rel):diagnostics[row['snapshot_date']]=row
    for r in profiles:
        kind=r['data_type'].lower(); day=r['snapshot']; cluster=int(r['cluster_id'])
        members=grouped[kind,day,cluster]
        if len(members)!=int(r['size']):raise ValueError('profile membership count mismatch')
        fields=FEATURES_M if kind=='market' else FEATURES_F if kind=='financial' else FIELDS
        medians={k:statistics.median(x[k] for x in members) for k in fields}
        boxes={k:quantiles([x[k] for x in members]) for k in fields}
        db.execute('INSERT INTO profiles VALUES(?,?,?,?,?,?,?)',(kind,day,cluster,len(members),r['feature_means_json'],encoded(medians),encoded(boxes)))
    for kind,day in sorted({(k,d) for k,d,_ in grouped}):
        size={str(c):len(v) for (k,d,c),v in grouped.items() if k==kind and d==day}
        raw=diagnostics[day] if kind=='market' else fm_snapshots[day]['diagnostics'] if kind=='financial' else cm_snapshots[day[:4]]['metrics']
        metrics={k:numeric(raw.get(k)) for k in ['silhouette','davies_bouldin','calinski_harabasz','inertia','cluster_balance']}
        metrics['min_cluster_size']=min(size.values())
        metrics['quality_status']='REVIEW_REQUIRED'
        scope='MARKET_ONLY_PROVISIONAL_IDENTITY' if kind=='market' else 'EX_POST_REFERENCE_NOT_PIT'
        db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?)',(kind,day,sum(size.values()),len(size),encoded(size),encoded(metrics),scope))
    for r in csv_rows('artifacts/reports/cluster-comparison-v1/memberships-a-b-c-year-end.csv'):
        db.execute('INSERT INTO relations VALUES(?,?,?,?,?,?)',(r['snapshot_date'],r['symbol'],numeric(r['market_cluster_id']),numeric(r['financial_cluster_id']),numeric(r['combined_cluster_id']),r['coverage']))
    db.commit()
    print('Indexed A/B/C',dict(db.execute('SELECT kind,count(*) FROM observations GROUP BY kind')),flush=True)
    prices_count=0;duplicates=0;conflicts=0
    if include_prices:
        price_path=pin(MARKET+'/canonical/prices_daily.jsonl',market_manifest['outputs']['canonical/prices_daily.jsonl'])
        batch=[]
        def insert(batch):
            nonlocal duplicates,conflicts
            for r in batch:
                try:db.execute('INSERT INTO prices VALUES(?,?,?,?,?,?,?,?,0)',r)
                except sqlite3.IntegrityError:
                    duplicates+=1
                    old=db.execute('SELECT ticker,security_id,date,adj_close,raw_close,volume,basis,available_at FROM prices WHERE security_id=? AND date=?',(r[1],r[2])).fetchone()
                    if tuple(old[:7])!=r[:7]:
                        conflicts+=1
                        db.execute('UPDATE prices SET adj_close=NULL,raw_close=NULL,volume=NULL,conflict=1 WHERE security_id=? AND date=?',(r[1],r[2]))
        with price_path.open(encoding='utf-8') as f:
            for line in f:
                r=json.loads(line)
                batch.append((r['ticker'],r['security_id'],r['trade_date'],numeric(r.get('adj_close')),numeric(r.get('raw_close')),numeric(r.get('volume')),r.get('adjustment_basis'),r.get('available_at')))
                prices_count+=1
                if len(batch)==10000:
                    insert(batch);db.commit();batch=[]
                    if prices_count%500000==0:print('Indexed prices',prices_count,flush=True)
            if batch:insert(batch)
        db.commit()
    metadata=dict(version=VERSION,generated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        candidates=len(securities),market_snapshots=84,financial_periods=10,combined_snapshots=7,
        scope='HISTORICAL_RESEARCH_REFERENCE_NOT_LIVE',strict_pit_ready=False,research_ready=False,backtest_allowed=False,
        financial_publication_rows=0,financial_rows=len(financial_features),price_rows=prices_count,
        price_duplicates=duplicates,price_conflicts_held=conflicts,
        definitions={k:dict(label=v[0],formula=v[1],unit=v[2],family='market' if k in FEATURES_M else 'financial') for k,v in DEFINITIONS.items()},
        validations={k:dict(status=v.get('status',v.get('technical_status')),quality_status=v.get('quality_status','REVIEW_REQUIRED')) for k,v in checks.items()},
        full_suite=dict(status='PARTIAL',reason='Latest full repository gate timed out; targeted tests and numerical verification reported separately'),
        model_configs=dict(market=dict(k=2,scaling='Robust per snapshot',frequency='Monthly',features=FEATURES_M,version='C8 V2 / M2 60+24'),
                           financial=dict(k=3,scaling='Z-score per year',frequency='Annual FY',features=FEATURES_F,version='Execution56 full10'),
                           combined=dict(k=3,scaling='Z-score + 50/50 block weights',frequency='Annual December reference',features=FIELDS,version='3904b52cda7753aeac90',protocol=cfg_c)),
        limitations=['Financial FY / December joins are ex-post, not verified PIT.','Fixed financial full10 cohort retains selection and survivorship bias.',
                     'Cluster labels are descriptive, not investment recommendations.','Financial facts, units and vintage are not all independently revalidated.',
                     'High silhouette does not remove severe cluster imbalance.','No live quotes, portfolio returns or complete F/M/Z scores are provided.'])
    db.execute('INSERT INTO metadata VALUES(?,?)',('overview',encoded(metadata)))
    db.commit();db.execute('ANALYZE');db.close()
    temporary.rename(final)
    manifest=dict(version=VERSION,database='terminal.sqlite',database_sha256=sha(final),sources=pins,metadata=metadata)
    (target/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
    print('Presentation bundle complete',final,flush=True)
    return target
