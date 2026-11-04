"""ABB one-article false-positive diagnostic; not a general CAPTCHA exception."""
import re
from urllib.parse import urlsplit

from .corporate_action_sources import Document, PublicTransport, sha

ARTICLE_URL = "https://abbank.vn/thong-tin/thong-tin-huong-dan-co-dong-ve-dot-chao-ban-co-phieu-cho-co-dong-hien-huu-nam-2021.html"
ARTICLE_TITLE = "Thông tin hướng dẫn Cổ đông về đợt chào bán cổ phiếu cho cổ đông hiện hữu năm 2021"
BENIGN_HELPER_SHA256 = "c4b041c344f7e2687db01628cd7f81eed79a5bd6103e66e648cb3838871f6529"
MARKER = re.compile(r"captcha|verify you are human|access denied|cloudflare challenge|cf-chl-", re.I)


def classify_article(text, url):
    """Classify only a pinned inert helper plus a complete public article.

    No script is executed and no form/widget is submitted. Any new marker,
    active widget, different URL or ambiguous layout remains a source stop.
    HTTP status/TLS/redirect guards are enforced separately by PublicTransport.
    """
    blocked = {"status": "SOURCE_STOP_OR_LAYOUT_REVIEW_REQUIRED", "challenge": True}
    if url != ARTICLE_URL:
        return blocked
    root = Document(text).root
    if re.search(r"verify you are human|access denied|cloudflare challenge|cf-chl-|challenge-platform|hcaptcha|h-captcha|turnstile|data-sitekey", text, re.I):
        return blocked
    markers = list(MARKER.finditer(text))
    helpers = [m for m in re.finditer(r"<script\b[^>]*>([\s\S]*?)</script\s*>", text, re.I)
               if sha(m[1].encode()) == BENIGN_HELPER_SHA256]
    if markers and (len(helpers) != 1 or any(not helpers[0].start(1) <= m.start() < helpers[0].end(1) for m in markers)):
        return blocked
    if any(re.search(r"captcha|challenge|turnstile", str(n.attrs), re.I) for n in root.find()):
        return blocked
    if any(n.attrs.get("type", "").lower() == "password" for n in root.find("input")):
        return blocked
    if any(n.attrs.get("action") not in {"/tim-kiem", "/subscribe"} for n in root.find("form")):
        return blocked
    headings, pages, content = root.find("h1"), root.find(id="pageNewsDetail"), root.find(cls="dynamic-content")
    if len(headings) != 1 or headings[0].text() != ARTICLE_TITLE or len(pages) != 1 or len(content) != 1:
        return blocked
    if len(pages[0].find(cls="dynamic-content")) != 1:
        return blocked
    article = content[0].text()
    if (not re.search(r"Mã cổ phiếu\s*:\s*ABB\b", article, re.I)
            or not all(label in article for label in ("Giá chào bán:", "Ngày đăng ký cuối cùng", "Tỷ lệ thực hiện quyền:"))
            or MARKER.search(root.text())):
        return blocked
    return {"status": "PUBLIC_ARTICLE_WITH_PINNED_INERT_FORM_HELPER" if markers else "PUBLIC_ARTICLE_WITHOUT_CHALLENGE_MARKER",
            "challenge": False, "helper_sha256": BENIGN_HELPER_SHA256 if markers else None,
            "marker_count": len(markers), "article_text": article}


class AbbPublicArticleTransport(PublicTransport):
    HOSTS = {"abbank.vn"}

    def fetch(self, url, *args, **kwargs):
        parts = urlsplit(url)
        if url != ARTICLE_URL or parts.username or parts.password or parts.port not in {None, 443}:
            raise ValueError("ABB_ONE_PUBLIC_ARTICLE_ONLY")
        return super().fetch(url, *args, **kwargs)

    def access_challenge(self, text, url):
        # Restriction to this one public layout applies even when no old keyword
        # matches; an unexpected body never silently becomes a successful pilot.
        return classify_article(text, url)["challenge"]
