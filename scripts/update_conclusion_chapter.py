# -*- coding: utf-8 -*-
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import shutil

DOCX_PATH = "Vo Minh Khoi_Bao cao thuc tap.docx"
BACKUP_PATH = "Vo Minh Khoi_Bao cao thuc tap_backup_before_conclusion_shorten.docx"

# Backup
shutil.copyfile(DOCX_PATH, BACKUP_PATH)
print(f"Backed up to {BACKUP_PATH}")

doc = docx.Document(DOCX_PATH)

start_idx = None
end_idx = None

for i, p in enumerate(doc.paragraphs):
    if p.text.strip() == "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN":
        start_idx = i
    if p.text.strip() == "TÀI LIỆU THAM KHẢO":
        end_idx = i
        break

print(f"Found 'KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN' at index {start_idx}")
print(f"Found 'TÀI LIỆU THAM KHẢO' at index {end_idx}")

target_pb_paragraph = doc.paragraphs[end_idx - 1]
old_paragraphs = doc.paragraphs[start_idx : end_idx - 1]
print(f"Identified {len(old_paragraphs)} old paragraphs to replace.")

def create_styled_paragraph(doc, text_runs, style_name="Normal", align=WD_ALIGN_PARAGRAPH.JUSTIFY, 
                            space_before=Pt(3), space_after=Pt(3), line_spacing=1.15,
                            left_indent=Pt(0), first_line_indent=Pt(0)):
    p = target_pb_paragraph.insert_paragraph_before()
    p.style = doc.styles[style_name]
    p.alignment = align
    p.paragraph_format.space_before = space_before
    p.paragraph_format.space_after = space_after
    p.paragraph_format.line_spacing = line_spacing
    if left_indent:
        p.paragraph_format.left_indent = left_indent
    if first_line_indent:
        p.paragraph_format.first_line_indent = first_line_indent
        
    for text, bold, italic, size in text_runs:
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = "Times New Roman"
        run.font.size = Pt(size)
        rPr = run._r.get_or_add_rPr()
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), 'Times New Roman')
        rFonts.set(qn('w:hAnsi'), 'Times New Roman')
        rFonts.set(qn('w:cs'), 'Times New Roman')
        rPr.append(rFonts)
    return p

# --- Chapter Title ---
create_styled_paragraph(
    doc,
    [("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(14),
    space_after=Pt(8),
    line_spacing=1.2
)

# --- Opening Paragraph ---
create_styled_paragraph(
    doc,
    [("Trải qua 11 tuần thực tập nghiêm túc, trách nhiệm và đầy nỗ lực tại doanh nghiệp, được tham gia trực tiếp vào dự án nghiên cứu định lượng ", False, False, 13),
     ("Project DELTA", True, False, 13),
     (" với đề tài: ", False, False, 13),
     ("“Phân cụm động lượng điều chỉnh rủi ro cho thị trường chứng khoán Việt Nam”", True, True, 13),
     (", em đã hoàn thành toàn diện các mục tiêu nghiên cứu và nhiệm vụ kỹ thuật được giao. Dự án không chỉ giải quyết bài toán phân nhóm cổ phiếu một cách khách quan dựa trên dữ liệu chuỗi thời gian mà còn kết hợp hài hòa giữa mô hình học máy không giám sát với các quy chuẩn tài chính định lượng quốc tế. Dưới đây là tổng kết toàn diện về kết quả nghiên cứu, bài học kinh nghiệm, định hướng phát triển tiếp theo và lời tri ân sâu sắc của em sau quá trình thực tập:", False, False, 13)],
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    space_before=Pt(4),
    space_after=Pt(6),
    line_spacing=1.15
)

# --- Section 1: KẾT QUẢ THỰC NGHIỆM VÀ SẢN PHẨM KỸ THUẬT (RÚT GỌN TẬP TRUNG) ---
create_styled_paragraph(
    doc,
    [("1. Kết luận về các kết quả thực nghiệm và sản phẩm kỹ thuật đạt được", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(10),
    space_after=Pt(4),
    line_spacing=1.2
)

create_styled_paragraph(
    doc,
    [("Trong 11 tuần thực tập, em đã trực tiếp tham gia xây dựng và vận hành thành công 3 phân hệ trụ cột của dự án định lượng với các kết quả thực nghiệm nổi bật:", False, False, 13)],
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    space_before=Pt(2),
    space_after=Pt(4),
    line_spacing=1.15
)

short_section_1_bullets = [
    ("Tiếp nhận và làm sạch dữ liệu lớn 10 năm (Milestone M1): ", 
     "Vận hành ổn định đường ống thu thập và chuẩn hóa chuỗi 3.209.374 dòng nến giá đóng cửa của 1.522 mã cổ phiếu (2016–2026) trên 3 sàn từ CafeF kết hợp VNDIRECT; xử lý chuẩn xác lịch giao dịch và sự kiện quyền; xác lập vũ trụ 905 mã đạt chuẩn Market-Feature-Ready bất biến Point-In-Time với mã băm SHA-256."),
    
    ("Mô hình học máy phân cụm đa chiều (Milestone M2): ", 
     "Trích xuất 8 đặc trưng động lượng và rủi ro; tiền xử lý định lượng bằng Winsorization (1% & 99%) và Robust Scaling, kéo giảm triệt để Skewness từ +6.12 về +0.31 và Kurtosis từ 58.9 về 3.0; chứng minh mô hình K-Means k=3 (Bundle v4) là tối ưu nhất (Silhouette 0.276, DBI 1.52, Subsample ARI 0.98); đồng thời vận hành mô hình tài chính B-PIT (k=3) với 8.461 nhãn phân cụm làm màng lọc cơ bản."),
    
    ("Kiểm chứng chiến lược danh mục đầu tư bằng Backtest (Milestone M3): ", 
     "Vận hành engine Walk-Forward hàng tháng; chiến lược kết hợp Combined (Market Cụm 0 + Financial Cụm 0/1) đạt hiệu quả vượt trội với CAGR 16.97%/năm trên Dev (gấp 3.7 lần VN-INDEX 4.53%, giảm MDD từ -47.88% về -44.60%) và CAGR 18.72%/năm trên Holdout (xếp Hạng 2/5 chiến lược, vượt trội so với Market-Only 11.14% và danh mục thị trường Equal-Weight 14.45%)."),
    
    ("Quy chuẩn kỹ nghệ phần mềm và tính tái lập khoa học: ", 
     "Toàn bộ hệ thống được module hóa, tự động hóa kiểm thử với Pytest và Synthetic Smoke Tests kiểm chứng phòng thủ biên, bảo đảm 100% tính tái lập qua các bản ghi bất biến Immutable Artifacts.")
]

for title, body in short_section_1_bullets:
    create_styled_paragraph(
        doc,
        [("• ", True, False, 13), (title, True, False, 13), (body, False, False, 13)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=Pt(2),
        space_after=Pt(3),
        line_spacing=1.15,
        left_indent=Pt(24),
        first_line_indent=Pt(-14)
    )

# --- Section 2 Heading ---
create_styled_paragraph(
    doc,
    [("2. Đóng góp cá nhân và bài học nghề nghiệp tích lũy của sinh viên", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(10),
    space_after=Pt(4),
    line_spacing=1.2
)

create_styled_paragraph(
    doc,
    [("Quá trình 11 tuần làm việc thực tế tại doanh nghiệp đã giúp em trưởng thành vượt bậc cả về năng lực chuyên môn định lượng lẫn tác phong nghề nghiệp:", False, False, 13)],
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    space_before=Pt(2),
    space_after=Pt(4),
    line_spacing=1.15
)

# Sub 2.1
create_styled_paragraph(
    doc,
    [("Về năng lực chuyên môn và kỹ thuật định lượng (Hard Skills):", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(6),
    space_after=Pt(2),
    line_spacing=1.15,
    left_indent=Pt(10)
)

sub2_1_bullets = [
    "Làm chủ kỹ năng xử lý dữ liệu chuỗi thời gian quy mô lớn trong môi trường thực tế (làm sạch dữ liệu nhiễu, đối soát liên nguồn, xử lý sự kiện doanh nghiệp).",
    "Nắm vững cơ chế toán học và phương pháp đánh giá của các mô hình học máy không giám sát (Unsupervised Learning), phân biệt rõ vai trò của các thước đo hình học cụm (Silhouette, Davies-Bouldin, Calinski-Harabasz) và thước đo độ ổn định thời gian (Adjusted Rand Index).",
    "Nắm vững phương pháp luận kiểm thử chiến lược định lượng theo chu kỳ thời gian tiến bước (Walk-Forward Analysis)."
]
for b in sub2_1_bullets:
    create_styled_paragraph(
        doc,
        [("• ", True, False, 13), (b, False, False, 13)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=Pt(2),
        space_after=Pt(3),
        line_spacing=1.15,
        left_indent=Pt(24),
        first_line_indent=Pt(-14)
    )

# Sub 2.2
create_styled_paragraph(
    doc,
    [("Về tư duy khoa học dữ liệu tài chính khắt khe:", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(6),
    space_after=Pt(2),
    line_spacing=1.15,
    left_indent=Pt(10)
)

sub2_2_bullets = [
    "Thấm nhuần triết lý tối thượng trong định lượng tài chính: Tuyệt đối chống rò rỉ dữ liệu tương lai (Look-ahead Bias / Data Leakage). Hiểu sâu sắc cơ chế Point-In-Time (PIT) khi tích hợp báo cáo tài chính, chỉ sử dụng thông tin kể từ phiên giao dịch đầu tiên sau ngày công bố thông tin thực tế.",
    "Phân định rạch ròi ba tầng đánh giá độc lập: Chất lượng phân cụm, Độ ổn định thời gian và Hiệu quả danh mục đầu tư. Nhận thức sâu sắc rằng không bao giờ được phép sử dụng thước đo lợi nhuận (Return hay Sharpe) để chọn tham số k hay thuật toán phân cụm, nhằm triệt tiêu hoàn toàn rủi ro tối ưu hóa quá mức (Overfitting / Data Snooping)."
]
for b in sub2_2_bullets:
    create_styled_paragraph(
        doc,
        [("• ", True, False, 13), (b, False, False, 13)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=Pt(2),
        space_after=Pt(3),
        line_spacing=1.15,
        left_indent=Pt(24),
        first_line_indent=Pt(-14)
    )

# Sub 2.3
create_styled_paragraph(
    doc,
    [("Về quy chuẩn kỹ nghệ phần mềm và đạo đức nghề nghiệp (Soft Skills & Professionalism):", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(6),
    space_after=Pt(2),
    line_spacing=1.15,
    left_indent=Pt(10)
)

sub2_3_bullets = [
    "Làm quen với văn hóa kỹ nghệ phần mềm chuyên nghiệp: Tuân thủ kiến trúc phân tầng khép kín (Ingestion → Features → Clustering → Experiments → Backtest → Product), viết mã sạch chuẩn PEP 8, quản lý phiên bản với Git.",
    "Rèn luyện đức tính cẩn trọng, kỷ luật và tính trung thực học thuật trong nghiên cứu: Mọi phát biểu kết luận đều phải được chứng minh bằng con số, kiểm thử tự động và biên bản bằng chứng thực nghiệm rõ ràng."
]
for b in sub2_3_bullets:
    create_styled_paragraph(
        doc,
        [("• ", True, False, 13), (b, False, False, 13)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=Pt(2),
        space_after=Pt(3),
        line_spacing=1.15,
        left_indent=Pt(24),
        first_line_indent=Pt(-14)
    )

# --- Section 3 Heading ---
create_styled_paragraph(
    doc,
    [("3. Những hạn chế kỹ thuật và định hướng phát triển trong tương lai", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(10),
    space_after=Pt(4),
    line_spacing=1.2
)

create_styled_paragraph(
    doc,
    [("Mặc dù đã đạt được những kết quả rất tích cực và vượt qua các mốc kiểm định khắt khe, đề tài vẫn tồn tại một số giới hạn kỹ thuật cần tiếp tục nghiên cứu và hoàn thiện:", False, False, 13)],
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    space_before=Pt(2),
    space_after=Pt(4),
    line_spacing=1.15
)

# Sub 3.1
create_styled_paragraph(
    doc,
    [("Những hạn chế kỹ thuật hiện tại:", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(6),
    space_after=Pt(2),
    line_spacing=1.15,
    left_indent=Pt(10)
)

sub3_1_bullets = [
    "Chiến lược phân bổ vốn giản đơn (1/N): Engine backtest hiện tại vẫn áp dụng mô hình phân bổ tỷ trọng đều giữa các cổ phiếu thuộc cụm mục tiêu, chưa tối ưu hóa phương sai danh mục theo rủi ro của từng tài sản riêng lẻ.",
    "Tần suất tái cân bằng cố định theo tháng: Chu kỳ tái cân bằng hàng tháng (Monthly Rebalancing) tuy đảm bảo tính ổn định và tiết kiệm chi phí giao dịch, nhưng chưa kịp thời phản ứng trước các cú sốc thanh khoản đột biến trong tuần.",
    "Dữ liệu tài chính mới dừng ở niên độ năm: Màng lọc tài chính hiện tại mới cập nhật theo báo cáo kiểm toán năm (tần suất 1 năm/lần), chưa phản ánh kịp thời sự biến động sức khỏe doanh nghiệp trong các quý giữa niên độ.",
    "Giả định chi phí giao dịch bằng 0: Mặc dù việc đặt phí và trượt giá bằng 0 là chuẩn mực trong nghiên cứu ban đầu để cô lập tín hiệu alpha thuần túy của mô hình, nhưng trong thực tế danh mục sẽ chịu thuế, phí môi giới và trượt giá thanh khoản (Market Impact)."
]
for b in sub3_1_bullets:
    create_styled_paragraph(
        doc,
        [("• ", True, False, 13), (b, False, False, 13)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=Pt(2),
        space_after=Pt(3),
        line_spacing=1.15,
        left_indent=Pt(24),
        first_line_indent=Pt(-14)
    )

# Sub 3.2
create_styled_paragraph(
    doc,
    [("Định hướng nghiên cứu và phát triển tiếp theo:", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(6),
    space_after=Pt(2),
    line_spacing=1.15,
    left_indent=Pt(10)
)

sub3_2_bullets = [
    "Nâng cấp thuật toán phân bổ vốn tối ưu: Mở rộng từ tỷ trọng đều 1/N sang các thuật toán phân bổ rủi ro ngang bằng (Hierarchical Risk Parity - HRP) hoặc mô hình Black-Litterman kết hợp quan điểm định lượng từ các cụm động lượng nhằm tối ưu hóa tỷ số Sharpe.",
    "Tích hợp dữ liệu Báo cáo tài chính quý theo chuẩn Point-In-Time: Mở rộng đường ống dữ liệu để tiếp nhận và đối soát BCTC quý (Q1, Q2, Q3, Q4) với dấu thời gian công bố chính xác (disclosure timestamp), giúp nâng cao độ nhạy của màng lọc cơ bản.",
    "Thử nghiệm các thuật toán phân cụm động (Dynamic / Regime-Switching Clustering): Nghiên cứu các mô hình phân cụm thích ứng theo chu kỳ kinh tế vĩ mô, lãi suất điều hành và trạng thái thị trường (sử dụng mô hình Markov ẩn - HMM).",
    "Xây dựng mô hình chi phí và cơ chế quản trị rủi ro thực tế: Tích hợp hàm chi phí giao dịch phi tuyến tính, mô hình trượt giá theo thanh khoản thực tế, cùng cơ chế cắt lỗ chủ động (Stop-loss) và giới hạn tỷ trọng ngành tối đa nhằm chuẩn bị cho việc triển khai giao dịch thuật toán tự động (Automated Execution)."
]
for b in sub3_2_bullets:
    create_styled_paragraph(
        doc,
        [("• ", True, False, 13), (b, False, False, 13)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=Pt(2),
        space_after=Pt(3),
        line_spacing=1.15,
        left_indent=Pt(24),
        first_line_indent=Pt(-14)
    )

# --- Section 4 Heading ---
create_styled_paragraph(
    doc,
    [("4. Lời cảm ơn và tri ân", True, False, 13)],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before=Pt(10),
    space_after=Pt(4),
    line_spacing=1.2
)

create_styled_paragraph(
    doc,
    [("Để hoàn thành tốt đợt thực tập tốt nghiệp và đề tài nghiên cứu này, em xin bày tỏ lòng biết ơn chân thành và sâu sắc nhất đến:", False, False, 13)],
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    space_before=Pt(2),
    space_after=Pt(4),
    line_spacing=1.15
)

thanks_bullets = [
    ("Đơn vị thực tập và Quý Doanh nghiệp: ", "Em xin chân thành cảm ơn Ban Giám đốc cùng toàn thể các anh/chị chuyên viên, kỹ sư và mentor hướng dẫn tại doanh nghiệp đã tạo mọi điều kiện thuận lợi nhất về môi trường làm việc, hỗ trợ hạ tầng kỹ thuật, chia sẻ nguồn dữ liệu thực tế và định hướng phương pháp luận nghiên cứu quý báu cho dự án DELTA trong suốt 11 tuần qua."),
    ("Các thành viên trong nhóm nghiên cứu (Team DELTA): ", "Em xin gửi lời cảm ơn chân thành đến các bạn đồng đội trong nhóm dự án đã luôn sát cánh, phối hợp hiệu quả trong việc khảo sát nghiệp vụ, đóng góp ý kiến phản biện khoa học và nhiệt tình hỗ trợ em giải quyết các khó khăn kỹ thuật trong suốt quá trình hoàn thành các mốc M1, M2 và M3."),
    ("Giảng viên giám sát TS. Phạm Thị Thiết: ", "Em xin trân trọng bày tỏ lòng tri ân sâu sắc nhất đến cô TS. Phạm Thị Thiết (Khoa Công nghệ Thông tin – Trường Đại học Công nghiệp TP.HCM). Cô đã luôn dành thời gian theo sát tiến độ, tận tình chỉ bảo, định hướng phương pháp luận khoa học chặt chẽ và đưa ra những lời khuyên chuyên môn sâu sắc giúp em hoàn thiện trọn vẹn và đạt chất lượng tốt nhất cho báo cáo thực tập này.")
]
for title, content in thanks_bullets:
    create_styled_paragraph(
        doc,
        [("• ", True, False, 13), (title, True, False, 13), (content, False, False, 13)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=Pt(2),
        space_after=Pt(3),
        line_spacing=1.15,
        left_indent=Pt(24),
        first_line_indent=Pt(-14)
    )

# --- Remove Old Paragraphs ---
for p in old_paragraphs:
    p._p.getparent().remove(p._p)

print(f"Successfully removed {len(old_paragraphs)} old paragraphs.")

doc.save(DOCX_PATH)
print(f"Successfully saved updated document to {DOCX_PATH}")
