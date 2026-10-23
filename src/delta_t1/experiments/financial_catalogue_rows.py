"""Extract observed catalogue links; report periods never become publication dates."""
from collections import Counter
from html.parser import HTMLParser
import json,re
from urllib.parse import urljoin,urlsplit,parse_qsl,urlencode,quote,urlunsplit

from ..ingestion.cafef_financial import digest,encoded
from ..ingestion.financial_batch_evidence import inside
from .financial_history_documents import read,put
from .financial_history20_profiles import ProfileParser


class Rows(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.row=None;self.cell=None;self.rows=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr':self.row=dict(cells=[],links=[])
        if tag=='td' and self.row is not None:self.cell=[]
        if tag=='a' and self.row is not None and '_rptDownload_' in a.get('id','') and a.get('id','').endswith('_lnkDownload'):
            self.row['links'].append(a.get('href',''))
    def handle_data(self,value):
        if self.cell is not None:self.cell.append(value)
    def handle_endtag(self,tag):
        if tag=='td' and self.row is not None and self.cell is not None:
            self.row['cells'].append(' '.join(' '.join(self.cell).split()));self.cell=None
        if tag=='tr' and self.row is not None:
            if self.row['links']:self.rows.append(self.row)
            self.row=None;self.cell=None


def parse_catalogue(body,member,profile,path,sha):
    if digest(body)!=sha:raise ValueError('catalogue raw hash differs')
    html=body.decode('utf-8-sig');header=ProfileParser();header.feed(html)
    names={' '.join(' '.join(n).split()) for n in header.names}
    if len(names)!=1:raise ValueError('ambiguous/missing catalogue quote header')
    match=re.fullmatch(r'(.*?)\s*\(\s*([A-Z0-9]+)\s*:\s*([A-Za-z]+)\s*\)',next(iter(names)))
    if not match or (match[2],match[3].upper())!=(member['symbol'],profile['exchange']):raise ValueError('catalogue issuer/exchange differs')
    parser=Rows();parser.feed(html);result=[]
    for index,row in enumerate(parser.rows):
        if len(row['cells'])!=5 or len(row['links'])!=1:
            result.append(dict(status='ROW_SCHEMA_REVIEW_REQUIRED',raw_row=row));continue
        href=row['links'][0];parts=urlsplit(urljoin('https://web.stockbiz.vn/',href));pairs=parse_qsl(parts.query,keep_blank_values=True)
        if parts.hostname!='web.stockbiz.vn' or parts.path.lower()!='/handlers/downloadfinancialstatement.ashx' or len(pairs)!=1 or pairs[0][0].lower()!='filename':
            result.append(dict(status='NONFINANCIAL_OR_UNSUPPORTED_HANDLER_LEAD',raw_row=row));continue
        filename=pairs[0][1];period=row['cells'][3];reasons=[]
        if ' '.join(filename.split())!=row['cells'][1]:reasons.append('LINK_FILENAME_DIFFERS_FROM_CELL')
        if not re.match('^'+re.escape(member['symbol'])+r'(?:[-_ .]|$)',filename,re.I):reasons.append('FILENAME_IDENTITY_REVIEW_REQUIRED')
        if not filename.lower().endswith('.pdf'):reasons.append('NON_PDF_DOCUMENT_LEAD')
        pm=re.fullmatch(r'(?:(Q[1-4])\s*/\s*)?(?:Năm\s+)?((?:19|20)\d{2})',period,re.I)
        if not pm:reasons.append('PERIOD_LABEL_REVIEW_REQUIRED')
        if re.search(r'prospectus|annual\s+reports',filename,re.I):reasons.append('NON_STATEMENT_DOCUMENT_LEAD')
        url=urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(pairs,quote_via=quote),''))
        if parts.scheme!='https':reasons.append('NON_HTTPS_LINK_REVIEW_REQUIRED')
        result.append(dict(symbol=member['symbol'],registry_id=member['registry_id'],provider_partition_id=member['provider_partition_id'],
            status='OBSERVED_FINANCIAL_PDF_LINK_CANDIDATE' if not reasons else 'DOCUMENT_LINK_REVIEW_REQUIRED',reasons=reasons,
            catalogue_row_index=index,filename=filename,description=row['cells'][2],provider_period_label=period,
            provider_year=int(pm[2]) if pm else None,provider_quarter=int(pm[1][1]) if pm and pm[1] else 0 if pm else None,
            observed_href=href,resolved_url=url,source_path=path,source_sha256=sha,
            publication_date=None,publication_status='NOT_PRESENT_IN_THIS_ROW; report period is not publication date',
            report_scope_status='DESCRIPTION_CANDIDATE_ONLY_PDF_REVIEW_REQUIRED',accepted=False,pit_ready=False))
    return result


def run(root,config_path,action):
    c=read(inside(root,config_path));pins={}
    if c.get('version')!='financial-catalogue-rows-v1':raise ValueError('catalogue row contract required')
    def pin(p,expected=None):
        raw=inside(root,p).read_bytes();sha=digest(raw)
        if expected is not None and sha!=expected:raise ValueError('catalogue input changed: '+p)
        pins[p]=sha;return raw
    for p in [config_path,'src/delta_t1/experiments/financial_catalogue_rows.py','scripts/financial_catalogue_rows.py','src/delta_t1/experiments/financial_history20_profiles.py']:pin(p)
    source=c['catalogue_result'];m=json.loads(pin(source+'/manifest.json',c['catalogue_manifest_sha256']))
    receipts=json.loads(pin(source+'/receipts.json',m['receipts.json']));cp=json.loads(pin(source+'/contract-pin.json',m['contract-pin.json']))
    contract=json.loads(pin(c['catalogue_root']+'/contract.json',cp['sha256']))
    for p,sha in contract['pins'].items():pin(p,sha)
    pp=c['profiles_result'];pm=json.loads(pin(pp+'/manifest.json',c['profiles_manifest_sha256']))
    profiles={r['registry_id']:r for r in json.loads(pin(pp+'/profiles.json',pm['profiles.json']))};rows=[];errors=[];seen=set()
    jobs={j['id']:j for j in contract['jobs']}
    for receipt in receipts:
        job=receipt['job'];rid=job['member']['registry_id']
        if job['id'] in seen or jobs.get(job['id'])!=job:raise ValueError('catalogue job identity differs')
        seen.add(job['id'])
        if receipt['status']!='ACQUIRED':errors.append(dict(symbol=job['member']['symbol'],reason=receipt['status']));continue
        body=pin(receipt['path'],receipt['sha256']);profile=profiles[rid]
        if profile['symbol']!=job['member']['symbol']:raise ValueError('catalogue/profile registry join differs')
        try:rows+=parse_catalogue(body,job['member'],profile,receipt['path'],receipt['sha256'])
        except (ValueError,KeyError,TypeError) as error:errors.append(dict(symbol=job['member']['symbol'],reason=str(error)))
    if seen!=set(jobs):raise ValueError('catalogue job census incomplete')
    valid=[r for r in rows if r['status']=='OBSERVED_FINANCIAL_PDF_LINK_CANDIDATE'];years=[r['provider_year'] for r in valid]
    summary=dict(status='CATALOGUE_LINK_CANDIDATES_ONLY',catalogues=len(receipts),catalogue_parse_errors=len(errors),row_statuses=dict(Counter(r['status'] for r in rows)),
        observed_financial_pdf_links=len(valid),observed_year_min=min(years) if years else None,observed_year_max=max(years) if years else None,
        pagination_status='FIRST_PUBLIC_VIEW_ONLY_NOT_PROOF_OF_EXHAUSTION',publication_dates_accepted=0,new_pdf_downloads=0,financial_features_allowed=False,research_ready=False)
    products={'summary.json':encoded(summary),'document-links.json':encoded(rows),'errors.json':encoded(errors),'input-pins.json':encoded(pins)}
    m={n:digest(raw) for n,raw in products.items()};out=inside(root,c['output_root'])/digest(encoded(m))[:20]
    if action=='verify':
        if read(out/'manifest.json')!=m:raise ValueError('parsed catalogue manifest differs')
        for n,sha in m.items():
            if digest((out/n).read_bytes())!=sha:raise ValueError('parsed catalogue changed')
    else:
        for n,raw in products.items():put(out/n,raw)
        put(out/'manifest.json',m)
    return dict(summary,output=out.relative_to(root).as_posix())
