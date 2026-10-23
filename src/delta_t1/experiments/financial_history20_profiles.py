"""Current provider taxonomy evidence; never historical sector or score applicability."""
from collections import Counter
from html.parser import HTMLParser
import json,re
from urllib.parse import urljoin,urlsplit,parse_qs

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put


class ProfileParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.depth=0;self.name_depth=None;self.names=[];self.link=None;self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='div':
            self.depth+=1
            if 'stockName' in a.get('class','').split():self.name_depth=self.depth;self.names.append([])
        if tag=='a':
            kind='sector' if a.get('id','').lower().endswith('_lnksector') else 'industry' if a.get('id','').lower().endswith('_lnkindustry') else None
            if kind:self.link=dict(kind=kind,href=a.get('href',''),text=[])
    def handle_endtag(self,tag):
        if tag=='div':
            if self.depth==self.name_depth:self.name_depth=None
            self.depth=max(0,self.depth-1)
        if tag=='a' and self.link:self.links.append(self.link);self.link=None
    def handle_data(self,data):
        if self.name_depth is not None:self.names[-1].append(data)
        if self.link:self.link['text'].append(data)


def parse_profile(body,member,path,sha):
    if digest(body)!=sha:raise ValueError('profile body hash differs')
    parser=ProfileParser();parser.feed(body.decode('utf-8-sig'))
    normalize=lambda chunks:' '.join(' '.join(chunks).split())
    names=sorted({normalize(chunks) for chunks in parser.names});reasons=[];observed=None;categories={}
    if len(names)!=1:reasons.append('MISSING_OR_AMBIGUOUS_QUOTE_HEADER')
    else:
        match=re.fullmatch(r'(.*?)\s*\(\s*([A-Z0-9]+)\s*:\s*([A-Za-z]+)\s*\)\s*',names[0])
        if not match:reasons.append('UNRECOGNIZED_QUOTE_HEADER')
        else:
            observed=dict(company_name=match[1].strip(),symbol=match[2],exchange=match[3].upper())
            if observed['symbol']!=member['symbol'] or observed['exchange']!=member['exchange']:reasons.append('CURRENT_PROVIDER_IDENTITY_DIFFERENCE')
    for link in parser.links:
        url=urljoin(member['profile_url'],link['href']);parts=urlsplit(url);codes=parse_qs(parts.query).get('Code',[])
        label=normalize(link['text'])
        if (parts.hostname!='web.stockbiz.vn' or parts.path.lower()!='/industryoverview.aspx' or len(codes)!=1
                or not codes[0].isdecimal() or not label):reasons.append('UNRECOGNIZED_CATEGORY_LINK');continue
        value=dict(provider_code=codes[0],label=label,url=url)
        if link['kind'] in categories and categories[link['kind']]!=value:reasons.append('CONFLICTING_CATEGORY_LABELS')
        categories[link['kind']]=value
    if set(categories)!={'sector','industry'}:reasons.append('MISSING_PROVIDER_SECTOR_OR_INDUSTRY')
    return dict(registry_id=member['registry_id'],symbol=member['symbol'],exchange=member['exchange'],
        provider_partition_id=member['provider_partition_id'],proposed_company_type=member['proposed_company_type'],
        status='CURRENT_PROFILE_OBSERVED' if not reasons else 'METADATA_REVIEW_REQUIRED',reasons=sorted(set(reasons)),
        observed_quote=observed,categories=categories,source_path=path,source_sha256=sha,source_url=member['profile_url'],
        scope='CURRENT_PROVIDER_PROFILE_ENGINEERING_SELECTION_ONLY',historical_identity_ready=False,
        historical_sector_accepted=False,score_applicability_accepted=False,financial_features_allowed=False,
        classification_next_action='VERIFY_ACTUAL_FINANCIAL_API_TEMPLATE; legacy proposed type not authoritative')


def run(root,config_path,action):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-history20-profiles-v1':raise ValueError('profile parser contract required')
    def pin(path,expected=None):
        raw=inside(root,path).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('profile evidence changed: '+path)
        pins[path]=sha;return raw
    pin(config_path)
    for p in ['src/delta_t1/experiments/financial_history20_profiles.py','scripts/financial_history20_profiles.py']:pin(p)
    source=c['metadata_result'];m=json.loads(pin(source+'/manifest.json',c['metadata_manifest_sha256']))
    receipts=json.loads(pin(source+'/receipts.json',m['receipts.json']))
    cp=json.loads(pin(source+'/contract-pin.json',m['contract-pin.json']))
    contract=json.loads(pin(c['metadata_root']+'/contract.json',cp['sha256']))
    for path,sha in contract['pins'].items():pin(path,sha)
    members={r['registry_id']:r for r in contract['members']};profiles=[];seen=set()
    for receipt in receipts:
        member=receipt['member'];rid=member['registry_id']
        if rid in seen or members.get(rid)!=member:raise ValueError('duplicate/altered profile assignment')
        seen.add(rid)
        if receipt['status']!='ACQUIRED':
            profiles.append(dict(registry_id=rid,symbol=member['symbol'],exchange=member['exchange'],status=receipt['status']));continue
        raw=pin(receipt['path'],receipt['sha256']);profiles.append(parse_profile(raw,member,receipt['path'],receipt['sha256']))
    if seen!=set(members):raise ValueError('profile receipts do not cover assignment')
    complete=[p for p in profiles if p['status']=='CURRENT_PROFILE_OBSERVED']
    sectors={p['categories']['sector']['provider_code'] for p in complete};industries={p['categories']['industry']['provider_code'] for p in complete}
    exchanges={p['exchange'] for p in complete};ready=len(complete)==15 and len(sectors)>=3 and len(exchanges)==3
    summary=dict(status='READY_FOR_BOUNDED_TEMPLATE_PROBES' if ready else 'PARTIAL_METADATA',new_current_profiles=len(profiles),
        observed_profiles=len(complete),status_counts=dict(Counter(p['status'] for p in profiles)),
        current_provider_sector_count=len(sectors),current_provider_industry_count=len(industries),exchanges=sorted(exchanges),
        template_probe_eligible=ready,full_history_acquisition_allowed=False,total_target_issuers=20,
        historical_identity_ready=False,historical_sector_accepted=False,score_applicability_accepted=False,
        financial_features_allowed=False,research_ready=False)
    products={'summary.json':encoded(summary),'profiles.json':encoded(profiles),'input-pins.json':encoded(pins)}
    manifest={n:digest(raw) for n,raw in products.items()};out=inside(root,c['output_root'])/digest(encoded(manifest))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=manifest:raise ValueError('profile output manifest differs')
        for n,sha in manifest.items():
            if digest((out/n).read_bytes())!=sha:raise ValueError('profile result changed')
    else:
        for n,raw in products.items():put(out/n,raw)
        put(out/'manifest.json',manifest)
    return dict(summary,output=out.relative_to(root).as_posix())
