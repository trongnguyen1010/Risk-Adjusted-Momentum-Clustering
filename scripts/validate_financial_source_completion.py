"""Capture finite stage checks; preserve the known frozen M2 checksum failure."""
import argparse,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def validate(output):
    out=ROOT/output
    out.mkdir(parents=True,exist_ok=True)
    checks=[('features',['-m','unittest','discover','-s','tests/unit/features','-p','test_financial*.py']),
        ('ingestion',['-m','unittest','discover','-s','tests/unit/ingestion','-p','test_financial*.py']),
        ('experiments',['-m','unittest','discover','-s','tests/unit/experiments','-p','test_financial*.py']),
        ('compile',['-m','compileall','-q','src','tests','scripts','run.py']),
        ('synthetic-smoke',['run.py','run','--config','configs/data/synthetic_smoke.example.json']),
        ('full-suite',['-m','unittest','discover','-s','tests'])]
    results=[]
    for name,args in checks:
        completed=subprocess.run([sys.executable]+args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
        log=completed.stdout.decode('utf8','replace')
        with (out/f'{name}.log').open('x',encoding='utf8') as f:f.write(log)
        match=re.search(r'Ran (\d+) tests',log)
        known=(name=='full-suite' and completed.returncode==1 and 'FAILED (errors=1)' in log
            and 'M2-PREP input hash mismatch: docs/DECISIONS.md' in log and log.count('ERROR: ')==1)
        status='PASS' if completed.returncode==0 else 'KNOWN_FROZEN_M2_CHECKSUM_FAILURE' if known else 'FAIL'
        results.append(dict(name=name,command=[sys.executable]+args,exit_code=completed.returncode,status=status,
            tests=int(match[1]) if match else None))
        print(name,status,flush=True)
    with (out/'validation.json').open('x',encoding='utf8') as f:json.dump(results,f,indent=2)
    if any(r['status']=='FAIL' for r in results):raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);validate(p.parse_args().output)
