"""Sinh từ điển dữ liệu chuẩn từ hợp đồng thực thi; không suy diễn nhà cung cấp."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delta_t1.contracts import schema

DESCRIPTIONS = {
    "security_id": "Định danh kinh tế ổn định từ danh mục thời gian có bằng chứng",
    "ticker": "Mã có hiệu lực vào ngày bản ghi, không phải định danh vĩnh viễn",
    "company_name": "Tên công ty từ bản ghi tham chiếu có hiệu lực",
    "exchange": "Sàn có hiệu lực; hỗ trợ UPCOM rõ ràng",
    "valid_from": "Ngày bắt đầu khoảng, có tính ngày này",
    "valid_to": "Ngày kết thúc khoảng, không tính ngày này; null nghĩa là chưa có điểm kết thúc",
    "listing_date": "Ngày niêm yết có thể giao dịch đầu tiên theo quy ước nguồn có bằng chứng",
    "delisting_date": "Ngày đầu tiên không thể giao dịch theo quy ước của kho mã",
    "available_at": "Thời điểm khả dụng sớm nhất có bằng chứng; không bao giờ âm thầm lùi ngày",
    "fetched_at": "Thời điểm tải, khác với thời điểm khả dụng trong lịch sử",
    "source": "Định danh nguồn gốc được giữ lại khi chuyển đổi",
    "data_version": "Định danh ảnh chụp/lần chạy bất biến; quan hệ truy vết nằm trong manifest",
    "identity_status": "verified/provisional/synthetic; provisional không đủ điều kiện",
    "sector": "Lĩnh vực có hiệu lực nếu nguồn cung cấp", "industry": "Ngành có hiệu lực nếu nguồn cung cấp",
    "currency": "Tiền tệ của chứng khoán/sự kiện", "price_unit": "VND/cổ phiếu chuẩn; bắt buộc có bằng chứng nguồn",
    "trade_date": "Ngày phiên theo giờ địa phương của sàn, dùng múi giờ có bằng chứng",
    "raw_open": "Giá mở cửa chưa điều chỉnh", "raw_high": "Giá cao nhất trong phiên chưa điều chỉnh",
    "raw_low": "Giá thấp nhất trong phiên chưa điều chỉnh", "raw_close": "Giá đóng cửa chưa điều chỉnh, không bao giờ sao chép từ giá điều chỉnh",
    "adj_close": "Giá đóng cửa điều chỉnh đã xác minh; null khi nguồn chưa rõ hoặc chỉ có giá chưa điều chỉnh",
    "adjustment_basis": "unadjusted/split_adjusted/total_return/unknown/synthetic",
    "volume": "Số cổ phiếu trong phạm vi giao dịch đã xác minh; null nếu chưa rõ",
    "traded_value": "Giá trị danh nghĩa đã xác minh; không bao giờ dùng giá điều chỉnh nhân khối lượng làm đại diện",
    "trading_status": "normal/suspended/halted/unknown; có thanh giá không chứng minh trạng thái bình thường",
    "index_id": "VNINDEX/VN30/HNXINDEX hoặc chỉ số được cấu hình rõ",
    "close": "Mức đóng cửa của chỉ số theo index_basis đã khai báo",
    "index_basis": "price/total_return/unknown/synthetic",
    "total_return_level": "Mức lợi suất toàn phần do nguồn cung cấp riêng, không tự tạo",
    "is_open": "Cờ phiên giao dịch từ nguồn độc lập có thẩm quyền",
    "is_month_end": "Phiên mở cửa cuối cùng đã xác minh của một tháng đầy đủ",
    "open_at": "Thời điểm mở cửa sàn; null với lịch giả lập cũ",
    "close_at": "Thời điểm đóng cửa sàn", "decision_at": "Thời điểm chốt nghiên cứu đã cấu hình, tại hoặc sau giờ đóng cửa",
    "event_id": "Định danh sự kiện ổn định từ nguồn",
    "event_type": "cash_dividend/stock_dividend/split/reverse_split/rights_issue/bonus_share/other",
    "announcement_date": "Ngày công bố; available_at kiểm soát thời điểm biết trong ngày",
    "ex_date": "Ngày giao dịch không hưởng quyền", "record_date": "Ngày đăng ký cuối cùng nếu biết",
    "effective_date": "Ngày sự kiện có hiệu lực theo quy ước nguồn",
    "payment_date": "Ngày thanh toán nếu biết, không giả định bằng ex_date",
    "adjustment_factor": "Hệ số của nhà cung cấp, cần bằng chứng riêng về quy ước",
    "cash_amount": "Khoản phân phối tiền mặt trên mỗi cổ phiếu", "ratio": "Số cổ phiếu mới trên mỗi cổ phiếu cũ; cần xác minh quy ước sự kiện",
    "date": "Ngày hiệu lực của quan sát lãi suất phi rủi ro", "annual_rate": "Lãi suất năm hiệu dụng dạng thập phân sau khi chuẩn hóa nguồn rõ ràng",
    "tenor": "Định danh kỳ hạn hoặc đại diện lãi suất", "day_count_basis": "Quy ước lãi suất; đặc trưng ở chế độ bảng thật cần chuẩn hóa theo 252 phiên giao dịch/năm",
}
UNITS = {k:"VND/cổ phiếu" for k in ("raw_open","raw_high","raw_low","raw_close","adj_close","cash_amount")}
UNITS.update(volume="cổ phiếu", traded_value="VND", annual_rate="thập phân/năm", ratio="cổ phiếu mới/cổ phiếu cũ", close="điểm chỉ số", total_return_level="điểm chỉ số")

if __name__ == "__main__":
    lines = ["# Từ điển dữ liệu chuẩn — hợp đồng 1.1.0", "", "Được sinh từ các schema thực thi bởi `scripts/build_data_dictionary.py`.",
             "Việc một trường cho phép `null` không bao giờ cho phép tự tạo giá trị. Dữ liệu tham chiếu giữ thông tin nguồn và thời điểm tải; bước chuyển đổi lưu các mã băm.", ""]
    for table in ("securities","prices_daily","benchmark_daily","trading_calendar","corporate_actions","risk_free_rate"):
        contract = schema(table)
        lines.extend(["## " + table, "", "Khóa chính: `" + "`, `".join(contract["primary_key"]) + "`", "", "| Trường | Kiểu | Mô tả | Đơn vị | Cho phép null | Nguồn |", "|---|---|---|---|---|---|"])
        for name, spec in contract["fields"].items():
            unit = UNITS.get(name, "ISO-8601 có độ lệch múi giờ" if spec["type"] == "datetime" else "YYYY-MM-DD" if spec["type"] == "date" else "nhãn/cờ" if spec["type"] in ("string","boolean") else "không thứ nguyên")
            source = "thông tin truy vết pipeline" if name in ("source","fetched_at","data_version") else "ánh xạ nhà cung cấp đã xác minh" if table in ("prices_daily","benchmark_daily") else "dữ liệu tham chiếu đã xác minh"
            lines.append(f"| {name} | {spec['type']} | {DESCRIPTIONS[name]} | {unit} | {'có' if spec['nullable'] else 'không'} | {source} |")
        lines.append("")
    (ROOT / "docs/data_dictionary.md").write_text("\n".join(lines), encoding="utf-8")
