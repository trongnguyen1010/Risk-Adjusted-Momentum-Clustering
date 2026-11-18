"""Verify immutable issuer rejection evidence before filtering exact PDF hashes."""
import json
from pathlib import Path
from .cafef_financial import digest
from .financial_documents import verify_inventory

def rejected_hashes(run):
    if run is None:
        return set()
    run = Path(run).resolve()
    verify_inventory(run)
    review = json.loads((run / 'document_review.json').read_bytes())
    if review.get('financial_features_allowed') is not False:
        raise ValueError('document review cannot grant eligibility')
    hashes = set()
    for doc in review['rejected_documents']:
        if not doc.get('reason'):
            raise ValueError('rejection reason required')
        for kind in ('pdf', 'image'):
            if digest(Path(doc[f'{kind}_path']).read_bytes()) != doc[f'{kind}_sha256']:
                raise ValueError('document rejection evidence hash mismatch')
        hashes.add(doc['pdf_sha256'])
    return hashes
