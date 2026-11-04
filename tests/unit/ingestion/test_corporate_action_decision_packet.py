from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
from delta_t1.ingestion.corporate_action_decision_packet import precision_diagnostic,inspect_history_document,link_history,disposition,make_request,change_scope


def ratio(n=6,d=7):return {"numerator":n,"denominator":d}


def row(supported=False):
    return {"ticker":"AAA","vci_payload_sha256":"test","field_data_supported_pending_review":supported,
        "original_sdk_row":{"record_date":"2024-03-20T17:00:00.000Z","ex_right_date":None,"ratio":.85714286}}


def history(title="AAA: Thực hiện quyền mua cổ phiếu",ticker="AAA",extra=""):
    b=(f'<h1 class="title-category">{title}</h1><div class="content-category">'
        +(f'<span class="item-info">Mã chứng khoán:</span><span class="item-info">{ticker}</span>' if ticker else '')+
        '<span class="item-info">Ngày đăng ký cuối cùng:</span><span class="item-info">21/03/2024</span>'
        +' Mã quyền mua: MIRAAA241 '+extra+'</div>').encode()
    return inspect_history_document(b,"https://vsdc.vn/vi/ad/1")


class DecisionPacketTests(unittest.TestCase):
    def test_generic_title_does_not_hide_explicit_body_schedule_revision(self):
        text=('Tiếp theo Thông báo số 1133/TB-CNVSD ngày 11/08/2021, CNVSD thông báo về việc gia hạn thời gian thực hiện quyền mua cổ phiếu như sau: '
              'Thông tin đã thông báo: Thời gian đăng ký từ 30/08/2021 đến 20/09/2021. '
              'Thông tin thay đổi: Thời gian đăng ký từ 30/08/2021 đến 15/10/2021. '
              'Các nội dung khác tại Thông báo số 1133/TB-CNVSD ngày 11/08/2021 không thay đổi.')
        result=change_scope(text,'GSP: Thực hiện quyền mua cổ phiếu')
        self.assertEqual('SCHEDULE_WITH_OTHER_TERMS_UNCHANGED',result['scope'])
        self.assertFalse(result['lineage_approved'])
        self.assertFalse(result['price_ratio_revision_ruled_out'])

    def test_body_schedule_marker_still_requires_unchanged_clause(self):
        text=('CNVSD thông báo về việc gia hạn thời gian thực hiện quyền mua cổ phiếu như sau: '
              'Thông tin thay đổi: Thời gian đăng ký từ 30/08/2021 đến 15/10/2021.')
        self.assertEqual('CHANGE_SCOPE_OR_LINEAGE_UNRESOLVED',change_scope(text,'GSP: Thực hiện quyền mua cổ phiếu')['scope'])

    def test_generic_title_body_extension_is_included_by_revision_filter(self):
        h=history(extra='CNVSD thông báo về việc gia hạn thời gian thực hiện quyền mua cổ phiếu như sau:')
        self.assertFalse(h['title_change_markers'])
        self.assertTrue(h['body_change_quotes'])
        self.assertTrue(link_history(row(),h,set(),{'MIRAAA241'})['revision_or_cancellation_candidate'])

    def test_exact_fraction_rounding_is_diagnostic_without_override(self):
        r=precision_diagnostic(.85714286,ratio())
        self.assertEqual("CONSISTENT_WITH_RECORDED_DECIMAL_ROUNDING",r["status"])
        self.assertEqual("0.85714286",r["rounded_source_at_recorded_scale"])
        self.assertFalse(r["override_applied"]);self.assertFalse(r["provider_rounding_method_verified"])

    def test_source_precision_case_does_not_become_one_third(self):
        original=ratio(333333,1000000);copy=deepcopy(original)
        r=precision_diagnostic(.33333333,original)
        self.assertEqual("DIFFERENT_AT_RECORDED_SDK_SCALE",r["status"])
        self.assertEqual("0.33333300",r["rounded_source_at_recorded_scale"])
        self.assertEqual(copy,original)

    def test_positive_half_up_tie_uses_exact_arithmetic(self):
        self.assertEqual("CONSISTENT_WITH_RECORDED_DECIMAL_ROUNDING",precision_diagnostic(.3,ratio(1,4))["status"])
        self.assertEqual("DIFFERENT_AT_RECORDED_SDK_SCALE",precision_diagnostic(.2,ratio(1,4))["status"])

    def test_no_tolerance_for_nearby_non_rounding_value(self):
        self.assertEqual("DIFFERENT_AT_RECORDED_SDK_SCALE",precision_diagnostic(.85714287,ratio())["status"])

    def test_bad_or_nonfinite_values_fail_closed(self):
        for value in [True,None,float('nan'),float('inf'),0,-1]:
            self.assertEqual("UNRESOLVED",precision_diagnostic(value,ratio())["status"])
        self.assertEqual("UNRESOLVED",precision_diagnostic(.5,ratio(True,2))["status"])
        self.assertEqual("UNRESOLVED",precision_diagnostic(.5,ratio(1,0))["status"])

    def test_rights_code_expiry_and_fractional_share_cancellation_are_not_offer_cancellation(self):
        h=history(extra='Ngày hiệu lực hủy mã quyền mua: 01/05/2024. Cổ phiếu lẻ sẽ bị hủy bỏ.')
        self.assertTrue(h["normal_rights_code_expiry_mentioned"])
        self.assertFalse(h["body_change_quotes"])
        link=link_history(row(),h,{"1"},{"MIRAAA241"})
        self.assertFalse(link["revision_or_cancellation_candidate"])

    def test_linked_title_change_is_a_hold_not_latest_winner(self):
        h=history(title='AAA: Thay đổi thời gian thực hiện quyền mua cổ phiếu')
        link=link_history(row(),h,set(),{"MIRAAA241"})
        self.assertTrue(link["revision_or_cancellation_candidate"])
        self.assertEqual("HOLD_LINKED_CHANGE_REVIEW",disposition(True,[],[link]))

    def test_missing_declared_ticker_does_not_gain_identity_from_title_hint(self):
        h=history(title='AAA: Hủy ngày đăng ký cuối cùng',ticker=None)
        h["rights_codes"]=[]
        link=link_history(row(),h,set(),set())
        self.assertFalse(link["strong_event_reference"])
        self.assertTrue(link["weak_reference_only"])
        self.assertFalse(link["event_identity_approved"])

    def test_meeting_same_record_date_is_not_a_rights_event_link(self):
        h=history(title='AAA: Họp đại hội đồng cổ đông');h["rights_codes"]=[]
        link=link_history(row(),h,set(),set())
        self.assertEqual("OTHER_OR_UNLINKED",link["relationship"])

    def test_explicit_rights_code_retains_date_conflict(self):
        h=history();h["record_dates"]=["2024-03-22"]
        link=link_history(row(),h,set(),{"MIRAAA241"})
        self.assertTrue(link["strong_event_reference"]);self.assertTrue(link["date_conflict"])

    def test_possible_outcome_is_not_terminal_execution_approval(self):
        h=history(title='AAA: Báo cáo kết quả chào bán cổ phiếu');link=link_history(row(),h,set(),{"MIRAAA241"})
        self.assertTrue(link["possible_outcome_candidate"])
        self.assertFalse(link["event_identity_approved"])

    def test_rounded_case_is_an_unsigned_case_specific_request(self):
        sources=[{"document_id":"a","price_vnd":"10000","ratio_exact":ratio(),"primary_unit_explicit":True,"ticker_record_supported":True}]
        r=make_request(row(),sources,[])
        self.assertEqual("CASE_SPECIFIC_EXACT_SOURCE_SELECTION_PROPOSAL",r["decision_class"])
        self.assertIsNone(r["owner_decision"]);self.assertFalse(r["signature_created"])
        self.assertFalse(r["provider_transformation_inferred"]);self.assertFalse(r["sdk_values_overwritten"])

    def test_source_price_conflict_cannot_be_selected_by_priority(self):
        self.assertEqual("HOLD_SOURCE_VALUE_CONFLICT",disposition(True,[],[],False))

    def test_schedule_scope_and_unchanged_clause_only_allow_conditional_request(self):
        scope=change_scope('Thông tin đã thông báo: Thời gian đặt mua: 01/03/2024. Thông tin điều chỉnh: Thời gian đặt mua: 02/03/2024. Các nội dung khác tại Thông báo số 1/TB-VSD ngày 01/01/2024 không thay đổi.','AAA: Điều chỉnh thời gian quyền mua')
        self.assertEqual("SCHEDULE_WITH_OTHER_TERMS_UNCHANGED",scope["scope"])
        src={"document_id":"a","price_vnd":"10000","ratio_exact":ratio(),"primary_unit_explicit":True,"ticker_record_supported":True}
        link={"revision_or_cancellation_candidate":True,"strong_event_reference":True,"date_conflict":False,"change_scope_review":scope}
        r=make_request(row(),[src],[link])
        self.assertEqual("HOLD_LINKED_CHANGE_REVIEW",r["decision_class"])
        self.assertIsNotNone(r["conditional_price_selection_after_lineage_review"])
        self.assertEqual({},r["proposed_fields_pending_approval"])
        self.assertIsNone(r["owner_decision"])

    def test_changed_price_cannot_be_treated_as_schedule_only(self):
        scope=change_scope('Thông tin điều chỉnh: Giá phát hành: 12.000 đồng/cổ phiếu. Các nội dung khác không thay đổi.','AAA: Điều chỉnh thời gian quyền mua')
        self.assertEqual("CHANGE_SCOPE_OR_LINEAGE_UNRESOLVED",scope["scope"])
        self.assertTrue(scope["explicit_economic_terms_in_changed_text"])

    def test_conflicting_notice_dates_are_preserved(self):
        scope=change_scope('Thông báo số 44/TB-VSD ngày 08/01/2021. Các nội dung khác tại Thông báo số 44/TB-VSD ngày 07/01/2021 không thay đổi.','AAA: Điều chỉnh')
        self.assertEqual(["44/TB-VSD"],scope["notice_ids_with_conflicting_date_literals"])

    def test_account_correction_is_distinct_from_price_correction(self):
        scope=change_scope('Thông tin đính chính: Tên chủ tài khoản: Công ty AAA Số tài khoản: 222. Lý do đính chính: nhầm tài khoản. Các nội dung khác tại Thông báo số 1/TB-VSD không thay đổi.','AAA: Đính chính tài khoản nhận tiền')
        self.assertEqual("ADMINISTRATIVE_ACCOUNT_WITH_OTHER_TERMS_UNCHANGED",scope["scope"])
        self.assertFalse(scope["lineage_approved"])

    def test_history_quote_offsets_match_raw_decoded_text(self):
        h=history(extra='Đính chính thông báo thực hiện quyền: nội dung cần kiểm tra.')
        for q in h["body_change_quotes"]:
            self.assertEqual(q["text"],h["article_text"][q["start"]:q["end"]])

    def test_runner_path_safety_and_no_overwrite(self):
        spec=importlib.util.spec_from_file_location("decision25_runner",ROOT/"scripts/build_corporate_action_decision25_v1.py")
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        with self.assertRaises(FileExistsError):runner.run(ROOT)
        with self.assertRaises(ValueError):runner.safe(ROOT,'../escape')


if __name__=="__main__":unittest.main()
