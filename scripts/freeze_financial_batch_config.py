"""Create a new config version after engineering code review, preserving source scope."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from delta_t1.ingestion.financial_batch_evidence import inside,validate

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();c=json.loads(inside(ROOT,a.input,'configs').read_bytes())
    c['code_sha256']={n:digest(inside(ROOT,n).read_bytes()) for n in c['code_sha256']}
    validate(c);immutable_write(inside(ROOT,a.output,'configs'),encoded(c))
    print(json.dumps(dict(output=a.output,source_scope_unchanged=True,code_files=len(c['code_sha256']))))
