"""Strict public document URLs for the bounded DTP/ASG evidence stage."""
from urllib.parse import urljoin,urlsplit,urlunsplit,quote,unquote
import hashlib
import re
from .corporate_action_sources import Document,PublicTransport,SourceLimitation


def allowed_url(url,config):
    u=urlsplit(url)
    if u.scheme!="https" or u.username or u.password or u.port not in {None,443} or u.query or u.fragment:return False
    path=unquote(u.path)
    if "\\" in path or any(part in {".",".."} for part in path.split("/")):return False
    if url in {config["dtp_page"],config["asg_page"],config["asg_prospectus_copy"]}:return True
    return u.hostname=="www.aseansc.com.vn" and path.startswith("/uploads/2021/12/") and path.rsplit("/",1)[-1] in config["dtp_attachment_names"]


def public_document_links(html,base,config):
    out=[]
    for node in Document(html).root.find():
        raw=node.attrs.get("href") if node.tag=="a" else node.attrs.get("src") if node.tag in {"iframe","embed"} else node.attrs.get("data") if node.tag=="object" else None
        if not raw:continue
        u=urlsplit(urljoin(base,raw));url=urlunsplit((u.scheme,u.netloc,quote(unquote(u.path),safe="/"),u.query,u.fragment))
        item={"url":url,"label":node.text()[:250],"allowed_target_document":allowed_url(url,config)}
        if u.path.lower().endswith(".pdf") or "sharepoint.com" in (u.hostname or ""):
            if item not in out:out.append(item)
    return out


class TargetDocumentTransport(PublicTransport):
    HOSTS={"www.aseansc.com.vn","asg.net.vn","static2.vietstock.vn"}
    def __init__(self,root,config,**kwargs):
        self.config=config
        if not config["tls_verification"] or config["follow_redirects"] or any(config[k] for k in ["hnx_requests_allowed","bulk_collection_allowed","automatic_field_approval","canonical_build"]):raise ValueError("STRICT_BOUNDED_STAGE_REQUIRED")
        if config["max_requests"]>6 or config["interval_seconds"]<2 or config["timeout_seconds"]>30 or config["max_bytes"]>5000000:raise ValueError("STAGE_BUDGET_EXCEEDED")
        super().__init__(root,max_requests=config["max_requests"],interval=config["interval_seconds"],timeout=config["timeout_seconds"],max_bytes=config["max_bytes"],**kwargs)

    def fetch(self,url,*args,**kwargs):
        if not allowed_url(url,self.config):raise SourceLimitation("TARGET_DOCUMENT_URL_NOT_ALLOWED")
        return super().fetch(url,*args,**kwargs)


def validate_saved_public_article(body,base,followup):
    """Validate one already-received public article; never relax live page gates."""
    if hashlib.sha256(body).hexdigest()!=followup["dtp_saved_page_sha256"]:raise ValueError("SAVED_PAGE_HASH_MISMATCH")
    text=body.decode("utf-8-sig");root=Document(text).root
    if [n.text() for n in root.find('h1')]!=[followup["dtp_exact_h1"]]:raise ValueError("SAVED_PUBLIC_ARTICLE_TITLE_MISMATCH")
    if any(n.attrs.get('data-sitekey') or 'g-recaptcha' in n.attrs.get('class','').split() or n.attrs.get('type')=='password' for n in root.find()):raise ValueError("ACTIVE_WIDGET_OR_PASSWORD_FORM")
    spans=[];seen={}
    for match in re.finditer(r'<script\b[^>]*>.*?</script\s*>',text,re.I|re.S):
        if not re.search('captcha',match.group(),re.I):continue
        scripts=Document(match.group()).root.find('script')
        if len(scripts)!=1:raise ValueError("SCRIPT_SCOPE_AMBIGUOUS")
        identifier=scripts[0].attrs.get('id');digest=hashlib.sha256(match.group().encode()).hexdigest()
        if followup['contact_form_script_hashes'].get(identifier)!=digest or identifier in seen:raise ValueError("UNKNOWN_OR_DUPLICATE_CONTACT_SCRIPT")
        seen[identifier]=digest;spans.append(match.span())
    if seen!=followup['contact_form_script_hashes']:raise ValueError("CONTACT_SCRIPT_SET_MISMATCH")
    markers=list(re.finditer(r'captcha|verify you are human|access denied|cloudflare challenge|cf-chl-',text,re.I))
    if any(not any(a<=m.start() and m.end()<=b for a,b in spans) for m in markers):raise ValueError("UNSCOPED_ACCESS_MARKER")
    links=[l for l in public_document_links(text,base['dtp_page'],base) if l['allowed_target_document']]
    if len({l['url'] for l in links})!=2:raise ValueError("EXACT_TWO_TARGET_PDFS_REQUIRED")
    return {'status':'PINNED_COMPLETE_PUBLIC_ARTICLE_WITH_CONTACT_FORM_SCRIPT_MARKERS','marker_count':len(markers),
        'script_hashes':seen,'public_pdf_links':links,'page_refetched':False,'scripts_executed':False,
        'default_live_access_challenge_gate_changed':False}


class ScopedPdfTransport(TargetDocumentTransport):
    """One exact prospectus has a declared bounded cap; other PDFs retain5MB."""
    def __init__(self,root,base,followup,**kwargs):
        if followup['normal_pdf_max_bytes']!=5000000 or not 5000000<followup['one_asg_prospectus_max_bytes']<=64000000 or followup['max_requests']>3 or followup['canonical_build'] or followup['automatic_field_approval']:
            raise ValueError('STRICT_PDF_FOLLOWUP_ONLY')
        config=base|{'max_requests':followup['max_requests'],'interval_seconds':followup['interval_seconds'],'timeout_seconds':followup['timeout_seconds'],'max_bytes':followup['normal_pdf_max_bytes']}
        super().__init__(root,config,**kwargs);self.large_cap=followup['one_asg_prospectus_max_bytes']
    def fetch(self,url,*args,**kwargs):
        if not kwargs.get('binary') or not urlsplit(url).path.lower().endswith('.pdf'):raise SourceLimitation('PDF_ONLY_NO_LIVE_PAGE_EXCEPTION')
        old=self.max_bytes
        self.max_bytes=self.large_cap if url==self.config['asg_prospectus_copy'] else 5000000
        try:return super().fetch(url,*args,**kwargs)
        finally:self.max_bytes=old
