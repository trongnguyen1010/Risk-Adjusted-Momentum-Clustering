"""Explicit bounded scan probe; OCR output remains a candidate until QA/review."""
import argparse,json,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
sys.stdout.reconfigure(encoding='utf8')
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from delta_t1.ingestion.financial_batch_evidence import inside,seal
from delta_t1.experiments.financial_batch_flow import verify_pins


def validate(c):
    docs=c['documents']
    if c.get('financial_features_allowed') is not False or not 1<=len(docs)<=8:
        raise ValueError('bounded candidate OCR required')
    count=0;seen=set()
    for d in docs:
        key=(d['pdf_sha256'],d['first_page'],d['last_page'])
        if key in seen or not 1<=d['first_page']<=d['last_page']<=250:raise ValueError('duplicate/invalid page range')
        seen.add(key);count+=d['last_page']-d['first_page']+1
    if count>320:raise ValueError('global320 page OCR cap')


def run(config,output):
    c=json.loads(inside(ROOT,config,'configs').read_bytes());validate(c)
    verify_pins(ROOT,c['input_pins']);verify_pins(ROOT,c['code_pins'])
    renderer=shutil.which('pdftoppm')
    if not renderer:raise ValueError('pdftoppm required')
    for d in c['documents']:
        if digest(inside(ROOT,d['pdf_path'],'data').read_bytes())!=d['pdf_sha256']:raise ValueError('PDF pin changed')
    out=inside(ROOT,output,'data');out.mkdir(parents=True,exist_ok=False);start=time.monotonic();records=[]
    immutable_write(out/'config.json',encoded(c));immutable_write(out/'runner.py',Path(__file__).read_bytes())
    immutable_write(out/'ocr-script.ps1',(ROOT/'scripts/ocr_financial_pages.ps1').read_bytes())
    for d in c['documents']:
        folder=out/f"{d['symbol']}-{d['year']}";folder.mkdir(exist_ok=False)
        try:
            subprocess.run([renderer,'-f',str(d['first_page']),'-l',str(d['last_page']),'-scale-to','2200',
                '-png',str(inside(ROOT,d['pdf_path'],'data')),str(folder/'page')],check=True,timeout=360,capture_output=True)
            subprocess.run(['powershell.exe','-NoProfile','-File',str(ROOT/'scripts/ocr_financial_pages.ps1'),
                '-ImageDirectory',str(folder)],check=True,timeout=600,capture_output=True)
            pages=[]
            for p in sorted(folder.glob('*.ocr.json')):
                x=json.loads(p.read_bytes());image=p.with_name(p.name.replace('.ocr.json','.png'))
                if digest(image.read_bytes())!=x['image_sha256']:raise ValueError('image/OCR pin mismatch')
                number=int(re.search(r'page-(\d+)',p.name)[1])
                pages.append(dict(pdf_page=number,image_path=image.relative_to(ROOT).as_posix(),image_sha256=x['image_sha256'],
                    ocr_path=p.relative_to(ROOT).as_posix(),ocr_sha256=digest(p.read_bytes()),text=x['text']))
            if len(pages)!=d['last_page']-d['first_page']+1:raise ValueError('incomplete OCR output')
            records.append(dict(d,status='OCR_CANDIDATE_COMPLETE',pages=pages))
        except (OSError,ValueError,subprocess.SubprocessError) as e:
            records.append(dict(d,status='OCR_FAILED',error=str(e)))
        print(d['symbol'],d['year'],records[-1]['status'],flush=True)
    result=dict(documents=records,ocr_pages=sum(len(d.get('pages',[])) for d in records),
        seconds=time.monotonic()-start,financial_features_allowed=False,accepted_facts=0)
    immutable_write(out/'index.json',encoded(result));seal(out)
    print(json.dumps({k:v for k,v in result.items() if k!='documents'}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.config,a.output)
