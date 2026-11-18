"""Start the read-only FastAPI and Next.js demo together. Ctrl+C stops both."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--production',action='store_true',help='Use a previously built Next.js production bundle.')
    parser.add_argument('--web-port',type=int,default=3000)
    parser.add_argument('--api-port',type=int,default=8010)
    args=parser.parse_args()
    frontend=ROOT/'web/frontend'
    next_cli=frontend/'node_modules/next/dist/bin/next'
    if not next_cli.exists():raise SystemExit('Run npm ci in web/frontend first. See web/README.md.')
    bundle=Path(os.environ.get('DELTA_BUNDLE',str(ROOT/'data/web/delta-intelligence-v4')))
    if not (bundle/'manifest.json').exists():
        raise SystemExit('Build the presentation index: python scripts/export_delta_terminal.py')
    if args.production:
        rewrites=frontend/'.next/routes-manifest.json'
        if not rewrites.exists():raise SystemExit('Run npm --prefix web/frontend run build first.')
        if f'127.0.0.1:{args.api_port}/api/v2/' not in rewrites.read_text(encoding='utf8'):
            raise SystemExit('Production API port differs from the built rewrite. Set DELTA_API_URL and rebuild first.')
    env=os.environ.copy()
    env['PYTHONPATH']=os.pathsep.join([str(ROOT/'.tools/web-runtime'),str(ROOT/'src'),str(ROOT/'web/backend'),env.get('PYTHONPATH','')])
    env['PYTHONIOENCODING']='utf-8'
    env['DELTA_API_URL']=f'http://127.0.0.1:{args.api_port}'
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    processes=[]
    try:
        processes.append(subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(args.api_port)],cwd=ROOT,env=env,creationflags=flags))
        processes.append(subprocess.Popen([shutil.which('node') or 'node',str(next_cli),'start' if args.production else 'dev','--hostname','127.0.0.1','--port',str(args.web_port)],cwd=frontend,env=env,creationflags=flags))
        print(f'DELTA Intelligence: http://127.0.0.1:{args.web_port}\nAPI docs: http://127.0.0.1:{args.api_port}/docs',flush=True)
        while all(p.poll() is None for p in processes):time.sleep(.5)
        failed=next((p.returncode for p in processes if p.returncode is not None),1)
        if failed:raise SystemExit(f'A demo service exited ({failed}). Check the logs above.')
    except KeyboardInterrupt:pass
    finally:
        for p in processes:
            if p.poll() is None:
                if os.name=='nt':
                    subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
                else:p.terminate()
        for p in processes:
            try:p.wait(timeout=8)
            except subprocess.TimeoutExpired:p.kill()

if __name__=='__main__':main()
