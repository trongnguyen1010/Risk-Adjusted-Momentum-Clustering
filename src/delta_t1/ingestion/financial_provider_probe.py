"""Bounded public JSON discovery. Provider values never gain PIT by retrieval."""
import json, re
from pathlib import Path
from urllib.parse import urlsplit
from .cafef_financial import digest, encoded, immutable_write, now
from .cafef_financial_detail import PublicEvidenceClient
from .sources.base import AccessControlError, RateLimitError, SemanticValidationError


def collect(config, output, client=None):
    requests = config['requests']
    hosts = set(config['approved_hosts'])
    if config.get('financial_features_allowed') is not False or not 1<=len(requests)<=12:
        raise ValueError('bounded raw-only probe required')
    if type(config['max_bytes']) is not int or not 1<=config['max_bytes']<=10000000:
        raise ValueError('response cap invalid')
    for r in requests:
        u=urlsplit(r['url'])
        if (u.scheme!='https' or u.hostname not in hosts or u.username or u.password
            or not re.fullmatch('[A-Z0-9]{1,10}',r['symbol'])):
            raise ValueError('unapproved URL/symbol')
    if len({r['symbol'] for r in requests})>4:
        raise ValueError('pilot symbol budget exceeded')
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    client=client or PublicEvidenceClient(approved_hosts=hosts,max_bytes=config['max_bytes'])
    records=[];stopped=set()
    for i,r in enumerate(requests):
        record=dict(r,published_at=None,available_at=None,financial_features_allowed=False)
        if r['provider'] in stopped:
            record['status']='NOT_REQUESTED_PROVIDER_HARD_STOP'
        else:
            try:
                body,status=client.get(r['url'])
                payload=json.loads(body)
                if not isinstance(payload,(dict,list)):
                    raise SemanticValidationError('JSON envelope expected')
                name=f'{i:02d}-{r["provider"]}-{r["symbol"]}.json'
                immutable_write(out/name,body)
                record.update(status='RAW_JSON_CAPTURED',path=str(out/name),sha256=digest(body),
                    fetched_at=now(),http_status=status,envelope_keys=list(payload)[:30] if isinstance(payload,dict) else [],
                    source_scope='UNVERIFIED',source_unit='UNVERIFIED',revision_history='UNVERIFIED')
            except (AccessControlError,RateLimitError) as exc:
                stopped.add(r['provider']);record.update(status='HARD_STOP',error=str(exc))
            except (ValueError,OSError) as exc:
                record.update(status='FAILED',error=str(exc))
        records.append(record)
    result=dict(requests=records,financial_features_allowed=False,full_universe_allowed=False)
    immutable_write(out/'inventory.json',encoded(result));immutable_write(out/'config.json',encoded(config))
    immutable_write(out/'collector.py',Path(__file__).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()}}))
    return result
