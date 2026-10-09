"""Bounded, reviewed-template OCR cell extraction; candidates never grant features."""
import re
from decimal import Decimal


def grouped_integer(text):
    """Accept grouped integers, including OCR comma/dot separators; no digit repair."""
    if not re.fullmatch(r'\(?\d{1,3}(?:[.,]\d{3})+\)?', text):
        raise ValueError('not a grouped integer')
    negative = text.startswith('(')
    if negative != text.endswith(')'):
        raise ValueError('unbalanced sign')
    return int(re.sub(r'[.,()]', '', text)) * (-1 if negative else 1)


def extract_cell(record, spec, year):
    """Use row code + year column, or an explicitly reviewed note-table rectangle."""
    words = [w for line in record['lines'] for w in line['words']]
    width, height = record['width'], record['height']
    if 'box' in spec:
        left, top, right, bottom = spec['box']
        candidates = [w for w in words if left <= (w['x'] + w['width']/2)/width <= right
                      and top <= (w['y'] + w['height']/2)/height <= bottom]
    else:
        headers = [w for w in words if w['text'] == str(year)
                   and .5 < w['x']/width < .85 and w['y']/height < .3]
        if len(headers) != 1:
            return {'status': 'YEAR_HEADER_AMBIGUOUS', 'value': None}
        edge = headers[0]['x'] + headers[0]['width']
        anchors = [w for w in words if w['text'] == spec['row_code'] and w['x']/width < .22
                   and w['y'] > headers[0]['y']]
        if len(anchors) != 1:
            return {'status': 'ROW_CODE_AMBIGUOUS', 'value': None}
        anchor = anchors[0]
        following = [w['y'] for w in words if re.fullmatch(r'\d{2,3}[ab]?', w['text'])
                     and w['x']/width < .22 and w['y'] > anchor['y'] + anchor['height']]
        bottom = (min(following) + anchor['y'])/2 if following else anchor['y'] + 45
        candidates = [w for w in words if anchor['y']-5 <= w['y'] < bottom
                      and abs(w['x'] + w['width'] - edge) < width*.035]
    parsed = []
    for word in candidates:
        try:
            parsed.append((grouped_integer(word['text']), word))
        except ValueError:
            pass
    if len(parsed) != 1:
        return {'status': 'CELL_MISSING_OR_AMBIGUOUS', 'value': None, 'candidate_count': len(parsed)}
    value, word = parsed[0]
    return dict(status='OCR_CANDIDATE_REQUIRES_REFERENCE_QA', value=value, source_token=word,
                financial_features_allowed=False)


def compare_candidate(candidate, reviewed):
    if candidate.get('value') is None:
        return {'status': candidate['status'], 'passed': False}
    return dict(status='MATCHES_REVIEWED_REFERENCE' if Decimal(candidate['value']) == Decimal(str(reviewed))
                else 'OCR_REFERENCE_MISMATCH', passed=Decimal(candidate['value']) == Decimal(str(reviewed)))
