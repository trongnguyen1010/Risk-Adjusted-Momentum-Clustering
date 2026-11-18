"""Date-level financial availability; preserve source precision and exact vintage."""
import json
from bisect import bisect_right
from collections import Counter
from datetime import date
from pathlib import Path
from .cafef_financial import digest,encoded,immutable_write
from .financial_documents import verify_inventory

def iso_date(value):
    parsed=date.fromisoformat(value)
    if parsed.isoformat()!=value:raise ValueError('canonical ISO date required')
    return parsed

def next_session(publication_date,exchange,calendar):
    published=iso_date(publication_date)
    rows=[r for r in calendar if r['exchange']==exchange]
    if not rows:return None,'CALENDAR_EXCHANGE_MISSING'
    dates=sorted({iso_date(r['trade_date']) for r in rows})
    if published<dates[0]:return None,'CALENDAR_START_AFTER_PUBLICATION'
    sessions=sorted({iso_date(r['trade_date']) for r in rows if r['is_open'] is True})
    index=bisect_right(sessions,published)
    if index==len(sessions):return None,'NEXT_SESSION_OUTSIDE_CALENDAR'
    return sessions[index].isoformat(),'DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR'

def overlay(readiness,publications,calendar,policy):
    if policy.get('financial_features_allowed') is not False or policy.get('timestamp_inference_allowed') is not False:
        raise ValueError('date overlay cannot approve features or infer timestamps')
    if policy.get('availability_rule')!='FIRST_OBSERVED_EXCHANGE_SESSION_STRICTLY_AFTER_PUBLICATION_DATE':
        raise ValueError('unsupported availability rule')
    if readiness.get('financial_features_allowed') is not False:raise ValueError('unapproved readiness input')
    docs=publications['documents']
    if not 1<=len(docs)<=policy['max_documents']:raise ValueError('publication budget exceeded')
    if sum(len(r.get('document_evidence',[])) for r in readiness['rows'])>policy['max_facts']:
        raise ValueError('fact budget exceeded')
    keys=[(d['symbol'],d['pdf_sha256']) for d in docs]
    if len(set(keys))!=len(keys):raise ValueError('duplicate publication identity; resolve dates first')
    lookup={key:d for key,d in zip(keys,docs)}
    out=[]
    for row in readiness['rows']:
        references=[]
        for fact in row.get('document_evidence',[]):
            pub=lookup.get((fact['symbol'],fact['pdf_sha256']))
            if not pub:
                references.append(dict(fact=fact,date_pit_status='EXACT_VINTAGE_PUBLICATION_MISSING',
                                       usable_from_date=None,available_at=None));continue
            if pub.get('validation_status')!='EXPLICIT_PUBLICATION_STATEMENT_VISUALLY_VERIFIED' or pub.get('precision')!='DATE_ONLY':
                raise ValueError('publication must have reviewed explicit disclosure date')
            usable,status=next_session(pub['publication_date'],pub['exchange'],calendar)
            references.append(dict(fact=fact,publication=pub,usable_from_date=usable,date_pit_status=status,
                available_at=None,availability_rule=policy['availability_rule'],
                availability_precision='TRADING_DATE',financial_features_allowed=False))
        verified=any(x['usable_from_date'] for x in references)
        out.append(dict(symbol=row['symbol'],year=row['year'],field=row['field'],
            value_evidence_status=row['evidence_status'],references=references,
            date_pit_status='HAS_DATE_PIT_REFERENCE' if verified else 'NO_DATE_PIT_REFERENCE',
            selected_canonical_value=None,financial_features_allowed=False))
    return dict(rows=out,counts=dict(Counter(r['date_pit_status'] for r in out)),
                decision_frequency=policy['decision_frequency'],
                calendar_quality=policy['calendar_quality'],financial_features_allowed=False,
                meaning='Temporal evidence only; compatible semantic/vintage/identity and feature acceptance remain separate')

def select_as_of(references,decision_date):
    """Select only released field vintages; ties differing in value are unresolved."""
    decision=iso_date(decision_date)
    eligible=[r for r in references if r.get('usable_from_date') and iso_date(r['usable_from_date'])<=decision
              and r.get('date_pit_status')=='DATE_PIT_VERIFIED_ON_OBSERVED_CALENDAR']
    if not eligible:return dict(status='NO_AVAILABLE_VINTAGE',selected=None)
    identities={(r['fact']['symbol'],r['fact']['year'],r['fact']['item'],r['fact'].get('period_start'),
                 r['fact'].get('period_end'),r['fact'].get('statement_scope'),r['fact'].get('accounting_framework')) for r in eligible}
    if len(identities)!=1:raise ValueError('as-of selection must be one compatible field/report identity')
    latest=max(r['publication']['publication_date'] for r in eligible)
    choices=[r for r in eligible if r['publication']['publication_date']==latest]
    values={(r['fact']['value'],r['fact']['unit']) for r in choices}
    if len(values)!=1:return dict(status='SAME_DATE_VINTAGE_VALUE_CONFLICT',selected=None)
    return dict(status='DATE_AS_OF_REFERENCE_SELECTED_SEMANTICS_PENDING',selected=choices,
                financial_features_allowed=False)

def task_date_coverage(result, tasks, decision_date):
    """Report temporal coverage, separately from model/identity acceptance."""
    iso_date(decision_date)
    if tasks.get('financial_features_allowed') is not False:
        raise ValueError('task input cannot approve features')
    lookup={(r['symbol'],r['year'],r['field']):r for r in result['rows']}
    rows=[]
    for task in tasks['rows']:
        inputs=[]
        for item in task['inputs']:
            source=lookup.get((task['symbol'],item['year'],item['field']),{})
            refs=source.get('references',[])
            try:
                selected=select_as_of(refs,decision_date)
            except ValueError:
                selected={'status':'INCOMPATIBLE_FIELD_REPORT_IDENTITIES','selected':None}
            inputs.append(dict(field=item['field'],year=item['year'],selection=selected))
        covered=sum(bool(i['selection'].get('selected')) for i in inputs)
        rows.append(dict(symbol=task['symbol'],year=task['year'],task=task['task'],
            date_covered_inputs=covered,required_inputs=len(inputs),
            date_input_coverage_complete=covered==len(inputs),inputs=inputs,
            compatible_vintages_status='REQUIRES_JOINT_REVIEW',task_ready=False,computed_value=None))
    return dict(decision_date=decision_date,rows=rows,financial_features_allowed=False,
                meaning='Date coverage only; no score, TTM, compatible-input or research approval')

def export(readiness_run,publication_run,policy_path,root,output,task_run=None,decision_date=None):
    readiness_run=Path(readiness_run).resolve();publication_run=Path(publication_run).resolve()
    for run in [readiness_run,publication_run]:verify_inventory(run)
    policy=json.loads(Path(policy_path).read_bytes());calendar=Path(root)/policy['calendar_path']
    if digest(calendar.read_bytes())!=policy['calendar_sha256']:raise ValueError('calendar hash mismatch')
    pubs=json.loads((publication_run/'publications.json').read_bytes())
    for d in pubs['documents']:
        if digest(Path(d['pdf_path']).read_bytes())!=d['pdf_sha256']:raise ValueError('publication PDF mismatch')
        e=d['evidence']
        if digest(Path(e['image_path']).read_bytes())!=e['image_sha256']:raise ValueError('publication image mismatch')
    result=overlay(json.loads((readiness_run/'readiness.json').read_bytes()),pubs,
                   [json.loads(line) for line in calendar.read_text(encoding='utf8').splitlines()],policy)
    result.update(input_manifest_sha256={str(p):digest((p/'manifest.json').read_bytes()) for p in [readiness_run,publication_run]},
                  calendar_sha256=policy['calendar_sha256'],policy_sha256=digest(Path(policy_path).read_bytes()))
    if (task_run is None)!=(decision_date is None):raise ValueError('task run and decision date must be supplied together')
    if task_run is not None:
        task_run=Path(task_run).resolve();verify_inventory(task_run)
        result['task_date_coverage']=task_date_coverage(result,json.loads((task_run/'task_readiness.json').read_bytes()),decision_date)
        result['input_manifest_sha256'][str(task_run)]=digest((task_run/'manifest.json').read_bytes())
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    immutable_write(out/'date_pit.json',encoded(result))
    immutable_write(out/'policy.json',Path(policy_path).read_bytes())
    immutable_write(out/'analyzer.py',Path(__file__).read_bytes())
    immutable_write(out/'manifest.json',encoded({'files':{p.name:digest(p.read_bytes()) for p in out.iterdir()}}))
    return result
