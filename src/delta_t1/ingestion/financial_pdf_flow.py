"""PDF candidates with explicit provenance; extraction never grants acceptance."""
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote

from ..features.financial_exploratory import REQUIRED


def normalized(text):
    text = text.lower().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


class Anchors(HTMLParser):
    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base, self.current, self.text, self.links = base, None, [], []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = dict(attrs).get('href')
            self.text = []

    def handle_data(self, data):
        if self.current is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(dict(url=urljoin(self.base, self.current), label=' '.join(self.text).strip()))
            self.current = None


def annual_links(html, base, year, scope):
    parser = Anchors(base)
    parser.feed(html)
    selected = {}
    for link in parser.links:
        label = normalized(link['label'] + ' ' + unquote(link['url']))
        if not re.search(r'(?<!\d)' + str(year) + r'(?!\d)', label):
            continue
        if not any(s in label for s in ['bao cao tai chinh', 'baocaotaichinh', 'bctc', 'financial statement']):
            continue
        if re.search(r'quy|quarter|ban nien|6 thang|9 thang|giua nien|q[1-4](?!\d)|giai trinh|hop dong|lua chon', label):
            continue
        if scope == 'CONSOLIDATED' and not any(s in label for s in ['hop nhat', 'hopnhat', 'consolidated']):
            continue
        if scope == 'STANDALONE' and any(s in label for s in ['hop nhat', 'hopnhat', 'consolidated']):
            continue
        uri = urlsplit(link['url'])
        if uri.scheme != 'https' or uri.username or uri.password or uri.port not in (None, 443):
            continue
        selected[link['url']] = link
    return sorted(selected.values(), key=lambda r: r['url'])


LABELS = {
    'current_assets': 'tai san ngan han', 'total_assets': 'tong cong tai san',
    'total_liabilities': 'no phai tra', 'current_liabilities': 'no ngan han',
    'net_revenue': 'doanh thu thuan', 'gross_profit': 'loi nhuan gop',
    'net_profit': 'loi nhuan sau thue', 'operating_cash_flow': 'luu chuyen tien thuan tu hoat dong kinh doanh',
}


def page_candidates(pages):
    result = []
    for page in pages:
        lines = page['text'].splitlines()
        for index, line in enumerate(lines):
            norm = normalized(line)
            for field, label in LABELS.items():
                if label not in norm:
                    continue
                context = '\n'.join(lines[max(0, index-1):index+3])
                result.append(dict(field=field, pdf_page=page['page'], line=index+1,
                    source_text=context, number_tokens=re.findall(r'\(?-?\d[\d.,]*\)?', context),
                    column_status='YEAR_COLUMN_REVIEW_REQUIRED', value=None,
                    accepted=False, strict_pit_ready=False))
    return result


def extraction_state(pages):
    candidates = page_candidates(pages)
    found = {r['field'] for r in candidates}
    return dict(candidates=candidates, candidate_fields_found=sorted(found),
        missing_candidate_fields=sorted(REQUIRED-found),
        low_text_pages=[p['page'] for p in pages if len(p['text'].strip()) < 80],
        status='SEMANTIC_REVIEW_REQUIRED' if found == REQUIRED else 'TEXT_OR_SELECTED_OCR_REVIEW_REQUIRED',
        accepted=False, financial_features_allowed=False, strict_pit_ready=False)
