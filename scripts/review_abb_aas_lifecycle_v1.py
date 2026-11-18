"""ABB scoped access correction + bounded AAS resolution discovery; no canonical."""
import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit, parse_qs, urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_sources import Document, PublicTransport, SourceLimitation, now, sha
from delta_t1.ingestion.abb_public_article import ARTICLE_URL, classify_article, AbbPublicArticleTransport

CONFIG=ROOT/"configs/data/corporate_action_abb_aas_v1.json"
OLD_RAW=ROOT/"tmp/ca_supplement_source_pilot_20261102_v2/raw/response-0001.bin"


def aas_url(url):
    u=urlsplit(url)
    if u.scheme!="https" or u.hostname not in {"aas.com.vn","www.aas.com.vn"} or u.username or u.password or u.port not in {None,443} or u.fragment:
        return False
    if "\\" in unquote(u.path) or any(part in {".",".."} for part in unquote(u.path).split("/")):
        return False
    if u.path=="/" and set(parse_qs(u.query))=={"s"}:return True
    return not u.query and u.path.startswith(("/thong-tin-co-dong/","/wp-content/uploads/","/Content/Archive/FileAttact/"))


def pdf_links(html,base):
    result=[]
    for a in Document(html).root.find("a"):
        href=a.attrs.get("href","")
        if not href:continue
        u=urlsplit(urljoin(base,href))
        url=urlunsplit((u.scheme,u.netloc,quote(unquote(u.path),safe="/"),u.query,u.fragment))
        if aas_url(url) and u.path.casefold().endswith(".pdf"):
            item={"url":url,"label":a.text()}
            if item not in result:result.append(item)
    return result


def select_resolution_pdf(links,number):
    eligible=[]
    for item in links:
        text=(item["label"]+" "+unquote(item["url"])).casefold()
        if re.search(r"\bnq\b|nghị.quyết|nghi.quyet",text) and re.search(rf"\b{number}\b",text):eligible.append(item)
    unique={x["url"]:x for x in eligible}
    if len(unique)==1:return next(iter(unique.values()))
    if not eligible and len({x["url"] for x in links})==1:return links[0]
    return None


class AasPublicTransport(PublicTransport):
    HOSTS={"aas.com.vn","www.aas.com.vn"}
    def fetch(self,url,*args,**kwargs):
        if not aas_url(url):raise ValueError("AAS_PUBLIC_DOCUMENT_URL_REQUIRED")
        return super().fetch(url,*args,**kwargs)


def run(output,collect=False):
    if output.exists():raise FileExistsError("REFUSE_OVERWRITE")
    c=json.loads(CONFIG.read_text(encoding="utf-8"))
    if (c["max_requests"]!=8 or c["interval_seconds"]<2 or c["timeout_seconds"]>15 or c["max_bytes"]>5000000
        or not c["tls_verification"] or c["follow_redirects"] or any(c[k] for k in ("bulk_collection_allowed","canonical_build","hnx_requests_allowed"))):raise ValueError("BOUNDED_STAGE_ONLY")
    body=OLD_RAW.read_bytes()
    if sha(body)!=c["abb_previous_raw_sha256"]:raise ValueError("OLD_ABB_RAW_HASH_MISMATCH")
    diagnostic=classify_article(body.decode("utf-8-sig"),ARTICLE_URL)
    output.mkdir(parents=True)
    def write(name,value):
        with (output/name).open("x",encoding="utf-8") as f:json.dump(value,f,ensure_ascii=False,indent=2)
    write("abb_offline_diagnostic.json",diagnostic|{"raw_path":str(OLD_RAW),"raw_sha256":sha(body),"source_artifact_changed":False})
    receipts=[];documents=[];stops=set()
    if collect:
        common=dict(interval=c["interval_seconds"],timeout=c["timeout_seconds"],max_bytes=c["max_bytes"])
        abb=AbbPublicArticleTransport(output/"abb",max_requests=1,**common)
        if not diagnostic["challenge"]:
            try:
                text,receipt=abb.fetch(ARTICLE_URL)
                fresh=classify_article(text,ARTICLE_URL)
                write("abb_live_diagnostic.json",fresh|{"receipt":receipt})
                documents.append({"id":"abb_article","status":"PUBLIC_ARTICLE_RECEIVED","receipt":receipt})
            except SourceLimitation as exc:
                documents.append({"id":"abb_article","status":"SOURCE_STOP","reason":str(exc)})
        receipts.extend({"source":"ABB","local_root":"abb",**r} for r in abb.requests)
        aas=AasPublicTransport(output/"aas",max_requests=7,**common);aas.last=abb.last
        def fetch(identifier,url,binary=False):
            if "AAS" in stops or len(aas.requests)>=7:return None
            try:
                value,receipt=aas.fetch(url,binary=binary)
                record={"id":identifier,"url":url,"format":"pdf" if binary else "html","status":"PUBLIC_DOCUMENT_RECEIVED","receipt":receipt}
                if binary:
                    with (output/f"{identifier}.pdf").open("xb") as f:f.write(value)
                else:
                    with (output/f"{identifier}_text.txt").open("x",encoding="utf-8") as f:f.write(Document(value).root.text())
                documents.append(record)
                return value
            except SourceLimitation as exc:
                stops.add("AAS");documents.append({"id":identifier,"url":url,"status":"SOURCE_STOP","reason":str(exc)})
                return None
        for page,number in zip(c["aas_pages"],[18,20]):
            html=fetch(page["id"],page["url"])
            if html is None:continue
            links=pdf_links(html,page["url"]);selected=select_resolution_pdf(links,number)
            write(page["id"]+"_attachments.json",{"observed_pdf_links":links,"selected":selected})
            if selected:fetch(page["id"]+"_attachment",selected["url"],True)
        # At most one public search, one matching disclosure, one attachment.
        # These are discovery candidates; the PDF itself must prove final identity.
        if "AAS" not in stops and len(aas.requests)<=4:
            search="https://aas.com.vn/?"+urlencode({"s":"nghị quyết đại hội đồng cổ đông 2024"})
            html=fetch("aas_agm_public_search",search)
            if html:
                links=[]
                for a in Document(html).root.find("a"):
                    url=urljoin(search,a.attrs.get("href",""));label=a.text()
                    words=(label+" "+unquote(url)).casefold()
                    if aas_url(url) and "/thong-tin-co-dong/" in url and "2024" in words and re.search(r"nghị.quyết|nghi.quyet",words) and re.search(r"đại.hội|dai-hoi|đhđcđ|dhdcd",words):
                        if url not in {x["url"] for x in links}:links.append({"url":url,"label":label})
                write("aas_agm_discovery.json",{"candidates":links,"selection":"ONLY_IF_UNIQUE"})
                if len(links)==1:
                    html=fetch("aas_agm_disclosure",links[0]["url"])
                    if html:
                        links_pdf=pdf_links(html,links[0]["url"]);selected=select_resolution_pdf(links_pdf,1)
                        write("aas_agm_attachments.json",{"observed_pdf_links":links_pdf,"selected":selected})
                        if selected:fetch("aas_agm_attachment",selected["url"],True)
        receipts.extend({"source":"AAS","local_root":"aas",**r} for r in aas.requests)
    write("requests.json",receipts)
    result={"stage":c["stage"],"created_at":now(),"status":"TECHNICAL_RESULTS_REQUIRE_DOCUMENT_REVIEW",
        "abb_offline_false_positive_confirmed_for_exact_layout":not diagnostic["challenge"],
        "network_request_attempts":len(receipts),"documents":documents,"hnx_requests":0,
        "canonical_rows_written":0,"accepted_fields":0,"price_factors_written":0,
        "pit_status":"NOT_PROMOTED","historical_identity":"UNVERIFIED","bulk_collection_started":False}
    write("summary.json",result)
    code=[Path(__file__),ROOT/"src/delta_t1/ingestion/corporate_action_sources.py",ROOT/"src/delta_t1/ingestion/abb_public_article.py",CONFIG]
    write("manifest.json",{"artifact_type":"abb-aas-source-remediation-v1","input_raw_sha256":sha(body),
        "code_and_config":{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in code},
        "files":{p.relative_to(output).as_posix():sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}})
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True);p.add_argument("--collect",action="store_true")
    a=p.parse_args();print(json.dumps(run(a.output.resolve(),a.collect),ensure_ascii=False,indent=2))
