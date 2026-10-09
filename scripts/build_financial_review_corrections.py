import argparse,json,copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.cafef_financial import digest,encoded,immutable_write
from delta_t1.ingestion.financial_documents import verify_inventory

def build(output):
    source=ROOT/'data/financial/source_completion_v3';verify_inventory(source)
    result=json.loads((source/'result.json').read_bytes());corrections=[]
    for field,value in [('operating_cash_flow',11703777188868),('noncurrent_loans_and_finance_leases',501115537075)]:
        conflict=next(x for x in result['provider_comparisons'] if x['cell']['field']==field
            and x['cell']['header']['YearPeriod']==2024 and x['comparison']['status']=='VALUE_CONFLICT')
        original=conflict['reviewed']['fact'];replacement=copy.deepcopy(original)
        replacement.update(value=value,derivation=dict(rule='EXACT_PDF_VISUAL_TRANSCRIPTION_CORRECTION',
            incorrect_value=original['value'],not_a_corporate_revision=True,publication_date_unchanged=True))
        for kind in ['pdf','image']:
            if digest(Path(replacement[f'{kind}_path']).read_bytes())!=replacement[f'{kind}_sha256']:raise ValueError('changed source')
        corrections.append(dict(rule='EXACT_PDF_VISUAL_TRANSCRIPTION_CORRECTION',incorrect_value=original['value'],
            replacement=replacement,trigger='PROVIDER_COMPARISON_CONFLICT_REVIEW_NOT_SOURCE_PRIORITY'))
    checks=[dict(check='CFO_PLUS_CFI_PLUS_CFF_EQUALS_NET_CASH_CHANGE',
        inputs=[11703777188868,-8461812173101,-2197766125834],reported_net_cash_change=1044198889933,
        passed=11703777188868-8461812173101-2197766125834==1044198889933),
        dict(check='NONCURRENT_LIABILITY_COMPONENT_SUM',
            inputs=[131344534204,183788442785,501115537075,356966680614,262864215119,192096283],
            reported_noncurrent_liabilities=1436271506080,
            passed=sum([131344534204,183788442785,501115537075,356966680614,262864215119,192096283])==1436271506080)]
    cash_image=Path(corrections[0]['replacement']['image_path']).with_name('page-15.png')
    checks[0].update(additional_image_path=str(cash_image),additional_image_sha256=digest(cash_image.read_bytes()))
    assert all(c['passed'] for c in checks)
    out=ROOT/output;out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'corrections.json',encoded(dict(corrections=corrections,checks=checks,financial_features_allowed=False)))
    immutable_write(out/'builder.py',Path(__file__).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return dict(corrections=len(corrections),checks=len(checks))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);print(json.dumps(build(p.parse_args().output)))
