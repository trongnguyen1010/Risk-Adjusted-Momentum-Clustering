"""Read observed FPT disclosure cards; preserve date precision, never infer PIT."""
import re
from datetime import datetime
from html import unescape
from urllib.parse import parse_qs,urlsplit,urljoin

def parse_cards(html):
    pattern=r'<span[^>]*>([^<]+)</span><div[^>]*><span[^>]*>(.*?)</span><a href="([^"]+)"'
    cards=[]
    for name,label,href in re.findall(pattern,html,re.S):
        date=re.search(r'(?<!\d)(\d{2}/\d{2}/\d{4})(?!\d)',re.sub('<[^>]+>','',label))
        if not date:continue
        uri=urlsplit(unescape(href))
        if uri.scheme or uri.netloc or uri.path!='/api/download':continue
        paths=parse_qs(uri.query).get('url',[])
        if len(paths)!=1 or not re.fullmatch(r'/api/media/[A-Za-z0-9_\-.]+\.pdf',paths[0]):continue
        cards.append(dict(title=unescape(name),publication_date=datetime.strptime(date[1],'%d/%m/%Y').date().isoformat(),
            precision='DATE_ONLY',download_url=urljoin('https://fpt.com',unescape(href)),
            attachment_url=urljoin('https://fpt.com',paths[0]),available_at=None,
            publication_timezone=None,financial_features_allowed=False))
    if not cards:raise ValueError('no supported dated disclosure cards; preserve raw and review template')
    return cards
