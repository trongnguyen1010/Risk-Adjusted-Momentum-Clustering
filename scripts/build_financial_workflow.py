import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.financial_workflow import export
if __name__=='__main__':
    p=argparse.ArgumentParser(description='Build bounded offline financial work queue; no crawl or acceptance')
    p.add_argument('--readiness-run',required=True);p.add_argument('--task-run',required=True)
    p.add_argument('--index-run',action='append',required=True)
    p.add_argument('--policy',default='configs/data/financial_workflow_v1.json')
    p.add_argument('--output',required=True)
    p.add_argument('--document-review-run')
    a=p.parse_args();out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT/'data'):raise ValueError('output must be under data')
    r=export(ROOT/a.readiness_run,ROOT/a.task_run,[ROOT/x for x in a.index_run],ROOT/a.policy,out,
             ROOT/a.document_review_run if a.document_review_run else None)
    print(json.dumps({k:r[k] for k in ['counts','unique_field_year_cells','task_input_references','reused_ocr_pages']}))
