"""Exact same-PDF transcription corrections, never provider priority or restatement."""
import copy
from pathlib import Path
from .cafef_financial import digest


def verify_correction_evidence(review):
    if not all(c['passed'] for c in review['checks']):raise ValueError('correction QA failed')
    for correction in review['corrections']:
        f=correction['replacement']
        for kind in ['pdf','image']:
            if digest(Path(f[f'{kind}_path']).read_bytes())!=f[f'{kind}_sha256']:
                raise ValueError('correction evidence changed')
    for check in review['checks']:
        if check.get('additional_image_path') and digest(Path(check['additional_image_path']).read_bytes())!=check['additional_image_sha256']:
            raise ValueError('correction bridge evidence changed')


def apply_review_corrections(facts,review):
    from .financial_pilot_readiness import eligible_fact
    if review.get('financial_features_allowed') is not False:
        raise ValueError('correction cannot grant eligibility')
    corrections=review['corrections'];excluded=[];remaining=list(facts)
    seen=set()
    for correction in corrections:
        replacement=correction['replacement'];keys=['symbol','year','item','pdf_sha256','unit']
        identity=tuple(replacement[k] for k in keys)
        if identity in seen or not eligible_fact(replacement):raise ValueError('invalid correction identity/fact')
        seen.add(identity)
        if correction['rule']!='EXACT_PDF_VISUAL_TRANSCRIPTION_CORRECTION':raise ValueError('unsupported correction')
        if replacement['value']==correction['incorrect_value']:raise ValueError('not a correction')
        kept=[]
        for f in remaining:
            if tuple(f.get(k) for k in keys)==identity and f['value']==correction['incorrect_value']:
                excluded.append(copy.deepcopy(f))
            else:kept.append(f)
        if not any(tuple(f.get(k) for k in keys)==identity and f['value']==replacement['value'] for f in kept):
            kept.append(copy.deepcopy(replacement))
        remaining=kept
    return remaining,excluded
