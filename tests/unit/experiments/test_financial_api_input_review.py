import json
import tempfile
import unittest
from pathlib import Path

from delta_t1.experiments.financial_api_input_review import (
    map_field, resolve, accounting, arithmetic_diagnostics, family_task, checkpoint, process_symbol)
from delta_t1.ingestion.cafef_financial import digest, encoded


class ApiInputReviewTests(unittest.TestCase):
    def cell(self, statement, group, code, label, status='UNIQUE_CODE_LABEL_CANDIDATE'):
        return dict(statement=statement, group=group, raw_code=code, label=label, mapping_status=status)

    def test_exact_code_and_label_both_required(self):
        self.assertEqual(map_field(self.cell('CDKT','TN','221','1. Tài sản cố định hữu hình')), 'net_tangible_ppe')
        self.assertIsNone(map_field(self.cell('CDKT','TN','220','1. Tài sản cố định hữu hình')))
        self.assertIsNone(map_field(self.cell('CDKT','TN','221','1. Tài sản cố định hữu hình','DUPLICATE_TEMPLATE_CODE_QUARANTINED')))
        self.assertEqual(map_field(self.cell('KQKD','KQKD','22','7. Doanh thu hoạt động tài chính')), 'finance_income')
        self.assertIsNone(map_field(self.cell('KQKD','KQKD','21','7. Doanh thu hoạt động tài chính')))

    def test_dangerous_lookalikes_stay_auxiliary(self):
        cases=[('CDKT','TN','223','- Giá trị hao mòn lũy kế (*)','owned_tangible_ppe_accumulated_depreciation'),
               ('LCTT','HDKD','HDKD_4','- Khấu hao TSCĐ và BĐSĐT','aggregate_fixed_property_depreciation_amortization'),
               ('LCTT','HDTC','HDTC_31','1.Tiền thu từ phát hành cổ phiếu, nhận vốn góp của chủ sở hữu','cash_equity_proceeds_group')]
        for statement,group,code,label,field in cases:
            self.assertEqual(map_field(self.cell(statement,group,code,label)),field)

    def test_conflicting_or_missing_values_never_selected_and_zero_is_real(self):
        row=lambda v:dict(value=v,value_status='NUMERIC_CANDIDATE' if v is not None else 'MISSING')
        self.assertEqual(resolve([row('0'),row('0.00')])[0],'0')
        self.assertIsNone(resolve([row('1'),row('2')])[0])
        self.assertIsNone(resolve([row('1'),row(None)])[0])

    def test_partition_inputs_not_combined_and_numerator_not_vendor_eps(self):
        data={(2025,'HK'):{'eps_adjusted_earnings_numerator':'100','vendor_basic_eps':'10'},
              (2025,'K'):{'weighted_average_basic_shares':'10'}}
        result=family_task('AAA',2025,'EPS',data,'Regular',[])
        self.assertTrue(all(e['missing_inputs'] for e in result['partition_input_evaluations']))
        self.assertIsNone(result['value']);self.assertFalse(result['accepted'])
        self.assertIn('weighted_average_basic_shares',result['required_fields_without_direct_api_alias'])

    def valid_data(self):
        return dict(current_assets='400',current_liabilities='200',total_assets='1000',retained_earnings='100',
                    total_equity='600',total_liabilities='400',profit_before_tax='70',interest_expense='10',
                    total_capital='1000',noncurrent_assets='600',noncurrent_liabilities='200',
                    net_revenue='500',cost_of_goods_sold='300',gross_profit='200',reported_operating_profit='60',
                    other_profit='10',net_profit='60',current_tax_expense='10',deferred_tax_expense='0')

    def test_z_hypothesis_arithmetic_is_never_an_accepted_metric(self):
        v=self.valid_data();checks=accounting(v)
        rows=arithmetic_diagnostics(2025,'HK',{(2025,'HK'):v},checks,False,True)
        z=rows[0];self.assertEqual(z['value'],'7.0006')
        self.assertFalse(z['accepted']);self.assertFalse(z['financial_features_allowed'])
        self.assertIn('SAME_MONETARY_UNIT_UNVERIFIED',z['assumptions'])
        self.assertIsNone(rows[1]['value'])

    def test_anomaly_missing_check_negative_interest_and_institution_block_z(self):
        v=self.valid_data();checks=accounting(v)
        for part,cs,displaced,regular in [(v,checks,True,True),(v,checks,False,False),
                (v,checks[:-1],False,True),(dict(v,interest_expense='-1'),checks,False,True),
                (dict(v,total_capital='999'),accounting(dict(v,total_capital='999')),False,True)]:
            # Removing the tail check is optional, so explicitly remove a core check.
            if cs is not checks and part is v:
                cs=[c for c in checks if c['check']!='PRETAX_BRIDGE']
            self.assertIsNone(arithmetic_diagnostics(2025,'HK',{(2025,'HK'):part},cs,displaced,regular)[0]['value'])

    def test_missing_annual_period_has_no_zero_or_synthetic_score(self):
        r=family_task('AAA',2016,'F_SCORE',{},'Regular',[])
        self.assertEqual(r['partition_input_evaluations'],[]);self.assertIsNone(r['value'])

    def test_checkpoint_rejects_source_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'checkpoint';out.mkdir();source=root/'raw.json';source.write_bytes(b'{}')
            files={'input-pins.json':encoded(dict(job_sha256='job',sources={'raw.json':digest(b'{}')})),
                   'summary.json':encoded(dict(symbol='AAA'))}
            for name,body in files.items():(out/name).write_bytes(body)
            (out/'manifest.json').write_bytes(encoded({n:digest(b) for n,b in files.items()}))
            self.assertEqual(checkpoint(root,out,'job')['symbol'],'AAA')
            source.write_bytes(b'{"changed":1}')
            with self.assertRaises(ValueError):checkpoint(root,out,'job')

    def test_raw_replay_checkpoint_and_institution_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);sources={}
            task=dict(id='r1',symbol='AAA',kind='REPORT',mode='NAM',statement='KQKD',group='KQKD')
            payload=dict(isSuccess=True,value=dict(unit=None,
                templace=[dict(code='50',name='Tổng lợi nhuận kế toán trước thuế')],
                data=[dict(symbol='AAA',year=2025,quater=0,type='HK',time='2025',data=[dict(code='50',value=100)])]))
            raw=encoded(payload);(root/'raw.json').write_bytes(raw);sources['raw.json']=digest(raw)
            receipt=encoded(dict(task=task,status='ACQUIRED',record=dict(path='raw.json',sha256=digest(raw))))
            (root/'batch/receipts').mkdir(parents=True);(root/'batch/receipts/r1.json').write_bytes(receipt);sources['batch/receipts/r1.json']=digest(receipt)
            qa=root/'qa';qa.mkdir()
            files={'input-pins.json':encoded(dict(sources=sources)), 'displacements.json':encoded([]),'arithmetic-findings.json':encoded([])}
            for name,body in files.items():(qa/name).write_bytes(body)
            manifest=encoded({name:digest(body) for name,body in files.items()});(qa/'manifest.json').write_bytes(manifest)
            source_manifest=dict(path='qa/manifest.json',sha256=digest(manifest))
            member=dict(symbol='AAA',registry_id='SEC-A',diagnostic_template_family='Regular')
            out=root/'out';summary=process_symbol(root,out,member,source_manifest,'job',[])
            self.assertEqual(summary['resolved_field_keys'],1)
            self.assertEqual(summary['new_accepted_metric_rows'],0)
            self.assertEqual(len(json.loads((out/'metric-tasks.json').read_bytes())),78)
            self.assertEqual(checkpoint(root,out,'job'),summary)
            bank=process_symbol(root,root/'bank',dict(member,diagnostic_template_family='Bank'),source_manifest,'job',[])
            self.assertEqual(bank['resolved_field_keys'],0)
            (root/'raw.json').write_bytes(b'{}')
            with self.assertRaises(ValueError):checkpoint(root,out,'job')
