"""Versioned compatibility adapter for an already frozen v2 continuation.

Inherited result summaries omitted pdf_sha256; the immutable reservation still
contains it. Supply that metadata in memory only, without changing any artifact.
"""
from contextlib import contextmanager
from pathlib import Path

from . import financial_continuation as base
from . import financial_user_workflow as f


def open_adapter(root, config):
    path=f.inside(root,config,'configs')
    f.verify_inventory(path.parent)
    c=f.load(path)
    if c.get('version')!='financial-resume-v3' or any(c.get(k) is not False for k in f.CLOSED):
        raise ValueError('closed resume adapter required')
    for p,sha in c['code_pins'].items(): f.pin(root,p,sha)
    d=base.descriptor(root,c['base_config'])
    f.open_run(root,d['run'])
    return c,d


@contextmanager
def inherited_metadata(root,run):
    original=f.load
    prefix=f.inside(root,run,'data')/'extract'
    def load(path):
        obj=original(path); p=Path(path)
        if (p.name=='result.json' and p.parent.parent==prefix and
                p.parent.name.startswith('inherited-') and 'pdf_sha256' not in obj):
            f.verify_inventory(p.parent)
            obj=dict(obj,pdf_sha256=original(p.parent/'reservation.json')['pdf_sha256'])
        return obj
    try:
        f.load=load
        yield
    finally:
        f.load=original


def extract(root,config,pdf_sha,full_ocr=False,retry_failed=False,worker=None):
    c,d=open_adapter(root,config)
    with inherited_metadata(root,d['run']):
        return base.extract(root,c['base_config'],pdf_sha,full_ocr,retry_failed,worker)
