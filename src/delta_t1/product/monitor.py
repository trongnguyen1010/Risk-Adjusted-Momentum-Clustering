"""Read-only projection of local financial workflow state; never runs pipeline code."""
import json
from datetime import datetime,timezone
from pathlib import Path

class WorkflowMonitor:
    def __init__(self,root):
        self.root=Path(root).resolve();self.cached={}
        self.qa_root=self.root/'data/financial/history_inventory1522_qa_v1'
        self.acquisition_root=self.root/'data/financial/history_acquisition_overnight_v2'

    def read_json(self,path,warnings):
        try:
            value=json.loads(path.read_bytes())
            if not isinstance(value,dict):raise ValueError('expected object')
            self.cached[path]=value;return value
        except (OSError,ValueError) as error:
            warnings.append(dict(source=path.relative_to(self.root).as_posix(),reason=type(error).__name__,using_last_good=path in self.cached))
            return self.cached.get(path,{})

    def tail(self,path,max_bytes=65536):
        try:
            with path.open('rb') as f:
                f.seek(0,2);length=f.tell();f.seek(max(0,length-max_bytes));raw=f.read(max_bytes)
            if length>max_bytes:raw=raw.partition(b'\n')[2]
            return raw.decode('utf-8',errors='replace').splitlines()[-35:]
        except OSError:return []

    def artifact(self,name):
        if name=='report':path=self.root/'artifacts/reports/financial-inventory1522-qa-v1/report.md'
        else:
            filenames={'summary':'summary.json','symbols':'symbols.csv','coverage':'coverage.csv','missing':'missing-periods.csv','queue':'document-priority-queue.csv'}
            if name not in filenames:return None
            status=self.read_json(self.qa_root/'pipeline-status.json',[]);relative=status.get('output')
            if not isinstance(relative,str):return None
            directory=(self.root/relative).resolve()
            if not directory.is_relative_to((self.qa_root/'jobs').resolve()):return None
            path=directory/filenames[name]
        return path if path.resolve().is_relative_to(self.root) and path.is_file() else None

    def snapshot(self):
        warnings=[];acquisition=self.read_json(self.acquisition_root/'pipeline-status.json',warnings);qa=self.read_json(self.qa_root/'pipeline-status.json',warnings)
        log=self.tail(self.qa_root/'worker.log');errors=self.tail(self.qa_root/'worker.stderr.log')
        recent=[]
        for line in log:
            try:
                value=json.loads(line)
                if value.get('event')=='INVENTORY_QA_CHECKPOINT':recent.append(value)
            except (ValueError,AttributeError):pass
        total=qa.get('total') or acquisition.get('partitions') or 1522
        completed=qa.get('completed')
        if not isinstance(completed,int):completed=recent[-1].get('completed') if recent else None
        qa_done=qa.get('stage')=='COMPLETE_OFFLINE_INVENTORY_QA_DIAGNOSTICS'
        acq_done=acquisition.get('stage')=='COMPLETE_CURRENT_REGISTRY_TASK_ACCOUNTING'
        percent=round(completed*100/total,1) if isinstance(completed,int) and isinstance(total,int) and total>0 and 0<=completed<=total else None
        summary={};summary_path=self.artifact('summary')
        if summary_path:summary=self.read_json(summary_path,warnings)
        updated=None
        for path in [self.qa_root/'pipeline-status.json',self.qa_root/'worker.log']:
            try:updated=max(updated or 0,path.stat().st_mtime)
            except OSError:pass
        age=round(datetime.now(timezone.utc).timestamp()-updated) if updated is not None else None
        return dict(served_at=datetime.now(timezone.utc).isoformat(),timezone='Asia/Barnaul',read_only=True,
            acquisition=dict(stage=acquisition.get('stage','UNKNOWN'),completed=acquisition.get('partitions') if acq_done else None,total=total,percent=100 if acq_done else None,complete=acq_done,at=acquisition.get('at')),
            qa=dict(stage=qa.get('stage','UNKNOWN'),completed=completed,total=total,percent=percent,complete=qa_done,last_symbol=qa.get('last_symbol') or (recent[-1].get('last_symbol') if recent else None),at=qa.get('at') or qa.get('at_utc'),reason=qa.get('reason'),last_activity_age_seconds=age,activity_stale=age is not None and age>120 and not qa_done),
            summary=summary,log=log,errors=errors,recent=recent[-8:][::-1],warnings=warnings,
            downloads={name:'/api/v1/monitor/files/'+name for name in ['report','summary','symbols','coverage','missing','queue'] if self.artifact(name)},
            financial_delivery='PARTIAL_NOT_NUMERIC_OR_PIT_ACCEPTANCE',verified_pilot_metrics=dict(value=29,target=30,scope='FY2025 pilot5 only'))
