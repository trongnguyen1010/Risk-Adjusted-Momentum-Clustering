"""Column-pair OCR diagnostics for VAS statement tables; no digit repair or acceptance."""
from .financial_table_parser import grouped_integer


def code_cell(record, code, current_headers, prior_headers, offset=0, code_band=None):
    if offset not in [0,-1]:raise ValueError('current/comparative columns only')
    words=[w for line in record['lines'] for w in line['words']]
    width,height=record['width'],record['height']
    current=[w for w in words if w['text'] in current_headers and .4<w['x']/width<.9]
    prior=[w for w in words if w['text'] in prior_headers and .5<w['x']/width<.99]
    pairs=[(a,b) for a in current for b in prior if a['x']<b['x'] and abs(a['y']-b['y'])<height*.03]
    if len(pairs)!=1:return dict(status='HEADER_PAIR_AMBIGUOUS',value=None)
    a,b=pairs[0];header=a if offset==0 else b
    anchors=[w for w in words if w['text']==code and w['x']<a['x']-20 and w['y']>max(a['y'],b['y'])]
    if code_band is not None:
        left,right=code_band
        if not 0<=left<right<=1:raise ValueError('invalid reviewed code-column band')
        anchors=[w for w in anchors if left<=w['x']/width<=right]
    if len(anchors)!=1:return dict(status='ROW_CODE_AMBIGUOUS',value=None)
    anchor=anchors[0];center=anchor['y']+anchor['height']/2;edge=header['x']+header['width']
    candidates=[]
    for w in words:
        if (abs(w['y']+w['height']/2-center)<=max(anchor['height'],w['height'])*.7+3
                and abs(w['x']+w['width']-edge)<width*.04):
            try:candidates.append((grouped_integer(w['text']),w))
            except ValueError:pass
    if len(candidates)!=1:return dict(status='CELL_MISSING_OR_AMBIGUOUS',value=None,candidate_count=len(candidates))
    value,word=candidates[0]
    return dict(status='OCR_CANDIDATE_ONLY',value=value,source_token=word,header_pair=[a,b],
                row_anchor=anchor,financial_features_allowed=False)
