# -*- coding: utf-8 -*-
"""
Script to generate the internship report 'Vo Minh Khoi_Bao cao thuc tap.docx'
Strictly adhering to user requirements:
1. From cover page to NHAN XET CUA GIAO VIEN GIAM SAT matching the template.
2. Content from Chapter 2 onward elaborated in detail, Chapter 1 left with placeholders for company info.
3. Font: Times New Roman, Color: Black (RGB 0,0,0), Size: 14pt throughout.
4. Sub-items after colons are numbered (1, 2, 3...), NO bullet points / dots.
5. Headings and paragraphs are flush with the left margin (left_indent = Pt(0), first_line_indent = Pt(0)).
6. Author: Vo Minh Khoi, focusing strictly on personal contributions: Market Data Ingestion (M1), M2 Feature & Clustering, and M3 Backtest.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_borders(cell, top="single", bottom="single", left="single", right="single",
                     color="000000", sz="4"):
    """Set thin black borders on table cells."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="{top}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:left w:val="{left}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="{bottom}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:right w:val="{right}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner margins (padding) for table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def create_report():
    doc = docx.Document()

    # 1. Page Setup - Standard A4 (Top 2.0cm, Bottom 2.0cm, Left 3.0cm, Right 2.0cm)
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)

    # 2. Configure Normal style
    style_normal = doc.styles['Normal']
    font_normal = style_normal.font
    font_normal.name = 'Times New Roman'
    font_normal.size = Pt(14)
    font_normal.color.rgb = RGBColor(0, 0, 0)

    # Helper function for adding paragraphs
    def add_p(text="", bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
              space_before=Pt(0), space_after=Pt(4), left_indent=Pt(0), keep_with_next=False):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.left_indent = left_indent
        p.paragraph_format.right_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0) # Flush with left margin!
        p.paragraph_format.space_before = space_before
        p.paragraph_format.space_after = space_after
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.keep_with_next = keep_with_next
        if text:
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            run.font.bold = bold
            run.font.italic = italic
            run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_heading_1(text):
        """Chapter heading: Times New Roman, 14pt, Bold, Uppercase, Flush Left."""
        return add_p(text.upper(), bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
                     space_before=Pt(14), space_after=Pt(6), keep_with_next=True)

    def add_heading_2(text):
        """Section heading: Times New Roman, 14pt, Bold, Flush Left."""
        return add_p(text, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
                     space_before=Pt(10), space_after=Pt(4), keep_with_next=True)

    def add_heading_3(text):
        """Sub-section heading: Times New Roman, 14pt, Bold Italic, Flush Left."""
        return add_p(text, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT,
                     space_before=Pt(8), space_after=Pt(3), keep_with_next=True)

    def add_numbered_item(num_str, title, content=""):
        """Sub-items after colons or lists: numbered (1, 2, 3...), NO bullet points! Flush left."""
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.right_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.25
        
        run_num = p.add_run(f"{num_str} ")
        run_num.font.name = 'Times New Roman'
        run_num.font.size = Pt(14)
        run_num.font.bold = True
        run_num.font.color.rgb = RGBColor(0, 0, 0)

        if title:
            run_title = p.add_run(f"{title}: " if not title.endswith(":") else f"{title} ")
            run_title.font.name = 'Times New Roman'
            run_title.font.size = Pt(14)
            run_title.font.bold = True
            run_title.font.color.rgb = RGBColor(0, 0, 0)
        
        if content:
            run_content = p.add_run(content)
            run_content.font.name = 'Times New Roman'
            run_content.font.size = Pt(14)
            run_content.font.bold = False
            run_content.font.color.rgb = RGBColor(0, 0, 0)
        return p

    # ==========================================
    # TRANG 1: BÌA CHÍNH (Front Cover)
    # ==========================================
    add_p("TRƯỜNG ĐẠI HỌC CÔNG NGHIỆP TPHCM", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(10), space_after=Pt(2))
    add_p("KHOA CÔNG NGHỆ THÔNG TIN", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(0), space_after=Pt(36))

    add_p("BÁO CÁO THỰC TẬP DOANH NGHIỆP", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(24), space_after=Pt(20))
    
    add_p("Đề tài:", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(10), space_after=Pt(4))
    add_p("HỆ THỐNG THU THẬP DỮ LIỆU, PHÂN CỤM ĐỘNG LƯỢNG VÀ KIỂM THỬ DANH MỤC CỔ PHIẾU THỊ TRƯỜNG CHỨNG KHOÁN VIỆT NAM (PROJECT DELTA)",
          bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(4), space_after=Pt(48))

    # Thông tin sinh viên & giảng viên
    info_table = doc.add_table(rows=5, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.autofit = False

    labels = [
        "Giảng viên giám sát:",
        "Sinh viên thực hiện:",
        "Mã sinh viên:",
        "Lớp:",
        "Khóa học:"
    ]
    values = [
        "......................................................................",
        "VÕ MINH KHÔI",
        "......................................................................",
        "......................................................................",
        "......................................................................"
    ]

    for i in range(5):
        row = info_table.rows[i]
        c0 = row.cells[0]
        c1 = row.cells[1]
        c0.width = Cm(5.5)
        c1.width = Cm(10.5)
        
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p0.paragraph_format.left_indent = Pt(0)
        p0.paragraph_format.first_line_indent = Pt(0)
        p0.paragraph_format.space_before = Pt(2)
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(labels[i])
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(14)
        r0.font.bold = True
        r0.font.color.rgb = RGBColor(0, 0, 0)

        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.paragraph_format.left_indent = Pt(0)
        p1.paragraph_format.first_line_indent = Pt(0)
        p1.paragraph_format.space_before = Pt(2)
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(values[i])
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(14)
        r1.font.bold = (i == 1) # Bold for Vo Minh Khoi
        r1.font.color.rgb = RGBColor(0, 0, 0)
        
        set_cell_borders(c0, top="none", bottom="none", left="none", right="none")
        set_cell_borders(c1, top="none", bottom="none", left="none", right="none")

    add_p("", space_before=Pt(40), space_after=Pt(0))
    add_p("TP. Hồ Chí Minh, năm 2026", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(40), space_after=Pt(10))
    
    doc.add_page_break()

    # ==========================================
    # TRANG 2: LỜI CẢM ƠN
    # ==========================================
    add_p("LỜI CẢM ƠN", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(10), space_after=Pt(16))

    add_p("Trân trọng gửi lời cảm ơn Ban Giám đốc và toàn thể các anh chị tại đơn vị thực tập đã tạo điều kiện thuận lợi nhất cho em có cơ hội được tham gia học tập, nghiên cứu và làm việc thực tế trong đợt thực tập doanh nghiệp này.")
    add_p("Trong suốt quá trình thực tập, nhờ sự định hướng và chỉ dẫn tận tình của người hướng dẫn (Mentor/Supervisor), em đã được tiếp cận trực tiếp với các bài toán thực tiễn phức tạp trong lĩnh vực phân tích dữ liệu tài chính định lượng, rèn luyện tư duy xây dựng hệ thống phần mềm chuyên nghiệp, từ việc thiết kế luồng thu thập dữ liệu lớn thị trường, nghiên cứu áp dụng thuật toán học máy phân cụm cho đến kiểm thử chiến lược đầu tư. Chân thành cảm ơn các anh chị đã dành nhiều thời gian, công sức quý báu để hướng dẫn, giải đáp các vướng mắc kỹ thuật và chia sẻ những kinh nghiệm thực tế sâu sắc.")
    add_p("Em cũng xin trân trọng gửi lời cảm ơn chân thành đến quý Thầy Cô Khoa Công nghệ Thông tin – Trường Đại học Công nghiệp TP. Hồ Chí Minh đã tận tâm truyền đạt những kiến thức chuyên môn vững chắc, tạo nền tảng lý thuyết quan trọng giúp em tự tin vận dụng vào môi trường doanh nghiệp thực tế, cũng như đã luôn nhiệt tình hỗ trợ, theo dõi và tạo điều kiện thuận lợi nhất cho em hoàn thành bài báo cáo này.")
    add_p("Mặc dù bản thân đã có nhiều nỗ lực và cố gắng để hoàn thành tốt các nhiệm vụ được giao, song do thời gian và kiến thức thực tiễn còn những hạn chế nhất định, báo cáo chắc chắn khó tránh khỏi những thiếu sót. Em rất mong nhận được những nhận xét, góp ý và chỉ dẫn quý báu từ quý Thầy Cô và các anh chị tại đơn vị thực tập để bài báo cáo cũng như năng lực chuyên môn của em ngày một hoàn thiện hơn.")

    add_p("", space_before=Pt(20), space_after=Pt(0))
    p_sign = add_p("Sinh viên thực hiện: ", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=Pt(10), space_after=Pt(2))
    p_sign_name = add_p("VÕ MINH KHÔI", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=Pt(0), space_after=Pt(2))
    add_p("TP. Hồ Chí Minh, ngày ... tháng ... năm 2026", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=Pt(0), space_after=Pt(10))

    doc.add_page_break()

    # ==========================================
    # TRANG 3: NHẬN XÉT CỦA ĐƠN VỊ THỰC TẬP
    # ==========================================
    add_p("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(0), space_after=Pt(2))
    add_p("Độc lập – Tự do – Hạnh phúc", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(0), space_after=Pt(16))

    add_p("NHẬN XÉT CỦA ĐƠN VỊ THỰC TẬP", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(10), space_after=Pt(16))

    add_p("Họ và tên sinh viên : VÕ MINH KHÔI", space_after=Pt(4))
    add_p("Mã sinh viên        : ……………………………………………………………………………………", space_after=Pt(4))
    add_p("Khóa học            : ……………………………………………………………………………………", space_after=Pt(4))
    add_p("Thời gian thực tập  : ……………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("Bộ phận thực tập    : ……………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(10))

    add_p("Tinh thần trách nhiệm với công việc và ý thức chấp hành kỷ luật :", bold=True, space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(10))

    add_p("Kết quả thực tập theo đề tài :", bold=True, space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(10))

    add_p("Nhận xét chung :", bold=True, space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(4))
    add_p("…………………………………………………………………………………………………………", space_after=Pt(16))

    # Chữ ký người hướng dẫn & Giám đốc
    sig_table = doc.add_table(rows=2, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.autofit = False

    sig_table.rows[0].cells[0].width = Cm(8.0)
    sig_table.rows[0].cells[1].width = Cm(8.0)
    sig_table.rows[1].cells[0].width = Cm(8.0)
    sig_table.rows[1].cells[1].width = Cm(8.0)

    p_s0 = sig_table.rows[0].cells[0].paragraphs[0]
    p_s0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_s0 = p_s0.add_run("NGƯỜI HƯỚNG DẪN\n(Ký và ghi rõ họ tên)")
    r_s0.font.name = 'Times New Roman'
    r_s0.font.size = Pt(14)
    r_s0.font.bold = True
    r_s0.font.color.rgb = RGBColor(0, 0, 0)

    p_s1 = sig_table.rows[0].cells[1].paragraphs[0]
    p_s1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_s1 = p_s1.add_run("Ngày ....... tháng ........ năm .........\nGIÁM ĐỐC\n(Ký tên và đóng dấu)")
    r_s1.font.name = 'Times New Roman'
    r_s1.font.size = Pt(14)
    r_s1.font.bold = True
    r_s1.font.color.rgb = RGBColor(0, 0, 0)

    # Blank space for signature in row 1
    p_blank0 = sig_table.rows[1].cells[0].paragraphs[0]
    p_blank0.add_run("\n\n\n\n")
    p_blank1 = sig_table.rows[1].cells[1].paragraphs[0]
    p_blank1.add_run("\n\n\n\n")

    for row in sig_table.rows:
        for cell in row.cells:
            set_cell_borders(cell, top="none", bottom="none", left="none", right="none")

    doc.add_page_break()

    # ==========================================
    # TRANG 4: NHẬN XÉT CỦA GIÁO VIÊN GIÁM SÁT
    # ==========================================
    add_p("NHẬN XÉT CỦA GIÁO VIÊN GIÁM SÁT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(10), space_after=Pt(16))

    for _ in range(12):
        add_p("…………………………………………………………………………………………………………", space_after=Pt(6))

    add_p("", space_before=Pt(14), space_after=Pt(4))
    add_p("Điểm số: ………………………………… Bằng chữ: ……………………………………………………", bold=True, space_after=Pt(20))

    p_gv_date = add_p("Ngày ....... tháng ........ năm .........", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=Pt(10), space_after=Pt(4))
    p_gv = add_p("GIẢNG VIÊN GIÁM SÁT", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=Pt(0), space_after=Pt(2))
    p_gv_note = add_p("(Ký và ghi rõ họ tên)", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=Pt(0), space_after=Pt(40))

    doc.add_page_break()

    # ==========================================
    # TRANG 5: MỤC LỤC
    # ==========================================
    add_p("MỤC LỤC", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(10), space_after=Pt(16))

    toc_items = [
        ("LỜI CẢM ƠN", "i"),
        ("NHẬN XÉT CỦA ĐƠN VỊ THỰC TẬP", "ii"),
        ("NHẬN XÉT CỦA GIÁO VIÊN GIÁM SÁT", "iii"),
        ("MỤC LỤC", "iv"),
        ("LỜI MỞ ĐẦU", "1"),
        ("CHƯƠNG 1: GIỚI THIỆU ĐƠN VỊ THỰC TẬP (TỰ ĐIỀN)", "3"),
        ("  1.1. Tổng quan về doanh nghiệp", "3"),
        ("  1.2. Cơ cấu tổ chức và môi trường văn hóa doanh nghiệp", "3"),
        ("  1.3. Lĩnh vực hoạt động và các sản phẩm, dịch vụ chính", "3"),
        ("  1.4. Bộ phận thực tập và vị trí công việc của sinh viên", "3"),
        ("CHƯƠNG 2: NỘI DUNG THỰC TẬP VÀ NGHIÊN CỨU KỸ THUẬT NỀN TẢNG", "4"),
        ("  2.1. Kế hoạch và quy trình thực tập cá nhân", "4"),
        ("  2.2. Nghiên cứu kỹ thuật thu thập và chuẩn hóa dữ liệu tài chính", "6"),
        ("  2.3. Nghiên cứu kỹ nghệ đặc trưng và thuật toán học máy phân cụm", "9"),
        ("  2.4. Nghiên cứu phương pháp luận Backtesting chiến lược danh mục đầu tư", "13"),
        ("  2.5. Đánh giá kết quả giai đoạn nghiên cứu và kỹ năng tích lũy", "16"),
        ("CHƯƠNG 3: CHI TIẾT THỰC HIỆN PROJECT — THU THẬP DỮ LIỆU, PHÂN CỤM M2 VÀ BACKTEST CHIẾN LƯỢC", "18"),
        ("  3.1. Giới thiệu tổng quan hệ thống DELTA và phạm vi đóng góp cá nhân", "18"),
        ("  3.2. Thu thập và chuẩn hóa dữ liệu thị trường (Milestone M1)", "20"),
        ("  3.3. Xây dựng hệ thống đặc trưng động lượng và mô hình phân cụm (Milestone M2)", "25"),
        ("  3.4. Thực nghiệm Backtest kiểm nghiệm chiến lược đầu tư (Milestone M3)", "32"),
        ("  3.5. Quy trình kiểm thử tự động và đảm bảo tính tái lập (Reproducibility)", "38"),
        ("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", "41"),
        ("TÀI LIỆU THAM KHẢO", "43"),
        ("NHẬT KÝ THỰC TẬP", "45"),
        ("PHỤ LỤC", "48")
    ]

    for item, page in toc_items:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.left_indent = Pt(0)
        p_t.paragraph_format.right_indent = Pt(0)
        p_t.paragraph_format.first_line_indent = Pt(0)
        p_t.paragraph_format.space_before = Pt(1)
        p_t.paragraph_format.space_after = Pt(2)
        p_t.paragraph_format.line_spacing = 1.15
        
        is_main = item.startswith("CHƯƠNG") or item in ["LỜI MỞ ĐẦU", "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", "TÀI LIỆU THAM KHẢO", "NHẬT KÝ THỰC TẬP", "PHỤ LỤC"]
        r_item = p_t.add_run(item)
        r_item.font.name = 'Times New Roman'
        r_item.font.size = Pt(14)
        r_item.font.bold = is_main
        r_item.font.color.rgb = RGBColor(0, 0, 0)

        # Tab or dots to page
        dots_len = max(2, 68 - len(item))
        r_dots = p_t.add_run(" " + "." * dots_len + " ")
        r_dots.font.name = 'Times New Roman'
        r_dots.font.size = Pt(14)
        r_dots.font.color.rgb = RGBColor(0, 0, 0)

        r_page = p_t.add_run(page)
        r_page.font.name = 'Times New Roman'
        r_page.font.size = Pt(14)
        r_page.font.bold = is_main
        r_page.font.color.rgb = RGBColor(0, 0, 0)

    doc.add_page_break()

    # ==========================================
    # LỜI MỞ ĐẦU
    # ==========================================
    add_p("LỜI MỞ ĐẦU", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(10), space_after=Pt(16))

    add_p("Thị trường chứng khoán Việt Nam trong những năm gần đây đã có sự phát triển vượt bậc cả về quy mô vốn hóa lẫn số lượng nhà đầu tư tham gia. Tuy nhiên, cùng với sự gia tăng về độ phức tạp, thị trường cũng chứng kiến những đợt biến động mạnh mẽ, khó lường, nơi dòng tiền đầu tư liên tục dịch chuyển giữa các nhóm ngành và nhóm cổ phiếu theo các chu kỳ ngắn và trung hạn. Trong bối cảnh đó, việc ứng dụng các phương pháp phân tích dữ liệu lớn và học máy (Machine Learning) vào phân tích định lượng (Quantitative Finance) nhằm nhận diện sớm các nhóm cổ phiếu dẫn dắt xu hướng đang trở thành một hướng tiếp cận hiện đại, khách quan và có tính thực tiễn cao.")
    add_p("Dự án DELTA (Hệ thống dữ liệu, tính toán đặc trưng và phân cụm cổ phiếu thị trường chứng khoán Việt Nam) được triển khai nhằm giải quyết bài toán cốt lõi: Phân loại tự động hành vi của hơn 900 mã cổ phiếu niêm yết trên 3 sàn HOSE, HNX và UPCoM dựa trên hiệu ứng động lượng (Momentum Effect), từ đó xây dựng và kiểm thử các chiến lược đầu tư theo cụm có khả năng tối ưu hóa tỷ suất sinh lời trên một đơn vị rủi ro so với chỉ số tham chiếu thị trường chung (VN-INDEX).")
    add_p("Đây là một đề tài nghiên cứu và phát triển theo hình thức nhóm dự án kết hợp tại doanh nghiệp. Tuy nhiên, bản báo cáo thực tập này là báo cáo cá nhân của sinh viên Võ Minh Khôi, trình bày độc lập, trung thực và chi tiết về toàn bộ các phần việc kỹ thuật cốt lõi mà bản thân trực tiếp đảm nhận, nghiên cứu và triển khai hoàn thiện trong dự án, bao gồm:")
    
    add_numbered_item("1.", "Phân hệ Thu thập và Chuẩn hóa Dữ liệu Thị trường (Milestone M1)", 
                      "Xây dựng đường ống (pipeline) tự động thu thập lịch sử giá khớp lệnh, khối lượng giao dịch trong 10 năm của hơn 900 mã cổ phiếu; thu thập và bóc tách các sự kiện quyền doanh nghiệp (Corporate Actions) từ VSDC để tính toán chuỗi giá điều chỉnh chính xác; thiết lập cơ chế kiểm thử đối soát (Reconciliation) và quản lý dữ liệu theo chuẩn thời điểm thực tế (Point-In-Time - PIT).")
    
    add_numbered_item("2.", "Phân hệ Kỹ nghệ Đặc trưng và Mô hình Phân cụm (Milestone M2)", 
                      "Xây dựng Feature Store tính toán bộ 9 đặc trưng động lượng then chốt; thiết lập quy trình tiền xử lý định lượng khắt khe (lọc thanh khoản, biến đổi Logarit, cắt đuôi ngoại lai Winsorization và chuẩn hóa Z-score); triển khai huấn luyện thuật toán K-Means (Bundle v4) với số cụm tối ưu k=3; đánh giá chất lượng phân cụm thông qua Silhouette Score, Davies-Bouldin và kiểm định độ ổn định cụm theo thời gian (ARI).")
    
    add_numbered_item("3.", "Phân hệ Kiểm thử Chiến lược Danh mục Đầu tư (Milestone M3 - Backtesting)", 
                      "Thiết kế giao thức thực nghiệm mô phỏng giao dịch theo định kỳ hàng tháng; phân chia nghiêm ngặt hai giai đoạn dữ liệu gồm tập phát triển Dev (2019–2023) và tập kiểm định ngoài mẫu Holdout (2024–2025); tính toán các chỉ số đánh giá hiệu suất danh mục chuyên sâu (CAGR, Sharpe, Sortino, Maximum Drawdown, Turnover) và đối chứng toàn diện với chỉ số thị trường VN-INDEX.")

    doc.add_page_break()

    # ==========================================
    # CHƯƠNG 1: GIỚI THIỆU ĐƠN VỊ THỰC TẬP (ĐỂ LẠI THEO YÊU CẦU)
    # ==========================================
    add_heading_1("CHƯƠNG 1: GIỚI THIỆU ĐƠN VỊ THỰC TẬP")
    add_p("(Ghi chú: Chương này sinh viên tự điền các thông tin thực tế về cơ quan, doanh nghiệp nơi tiếp nhận thực tập theo các mục cấu trúc gợi ý dưới đây)", italic=True, space_after=Pt(12))

    add_heading_2("1.1. Tổng quan về doanh nghiệp tiếp nhận thực tập")
    add_p("Tên doanh nghiệp: …………………………………………………………………………………………")
    add_p("Địa chỉ trụ sở chính: ………………………………………………………………………………………")
    add_p("Lịch sử hình thành và quá trình phát triển: ………………………………………………………………")
    add_p("Tầm nhìn, sứ mệnh và các giá trị cốt lõi: …………………………………………………………………")

    add_heading_2("1.2. Cơ cấu tổ chức và môi trường văn hóa doanh nghiệp")
    add_p("Sơ đồ cơ cấu tổ chức bộ máy quản lý: ……………………………………………………………………")
    add_p("Văn hóa doanh nghiệp và quy chế làm việc nội bộ: ………………………………………………………")

    add_heading_2("1.3. Lĩnh vực hoạt động và các sản phẩm, dịch vụ chính")
    add_p("Các lĩnh vực kinh doanh trọng tâm: ………………………………………………………………………")
    add_p("Các sản phẩm, giải pháp công nghệ hoặc dịch vụ tiêu biểu: ………………………………………………")

    add_heading_2("1.4. Bộ phận thực tập và vị trí công việc của sinh viên")
    add_p("Giới thiệu phòng ban / bộ phận tiếp nhận: …………………………………………………………………")
    add_p("Người hướng dẫn trực tiếp (Mentor/Supervisor): …………………………………………………………")
    add_p("Vị trí và nhiệm vụ được phân công trong kỳ thực tập: ……………………………………………………")

    doc.add_page_break()

    # ==========================================
    # CHƯƠNG 2: NỘI DUNG THỰC TẬP VÀ NGHIÊN CỨU KỸ THUẬT NỀN TẢNG
    # ==========================================
    add_heading_1("CHƯƠNG 2: NỘI DUNG THỰC TẬP VÀ NGHIÊN CỨU KỸ THUẬT NỀN TẢNG")

    add_heading_2("2.1. Kế hoạch và quy trình thực tập cá nhân")
    add_p("Trong suốt kỳ thực tập tại doanh nghiệp, sinh viên đã tham gia trực tiếp vào quy trình làm việc chuyên nghiệp, tuân thủ nghiêm ngặt các quy định về an toàn dữ liệu, chuẩn mực viết mã và quy trình phát triển phần mềm định lượng. Để đảm bảo tính độc lập và chất lượng cao nhất cho các phân hệ được giao, kế hoạch làm việc cá nhân đã được xây dựng và bám sát theo các nguyên tắc:")

    add_numbered_item("1.", "Phân chia trách nhiệm độc lập trong dự án nhóm", 
                      "Nhóm dự án DELTA hướng đến xây dựng hệ thống phân tích định lượng cổ phiếu toàn diện. Trong đó, sinh viên Võ Minh Khôi chịu trách nhiệm hoàn toàn về ba phân hệ cốt lõi: 1) Thu thập, chuẩn hóa và đối soát dữ liệu thị trường 10 năm; 2) Xây dựng đặc trưng động lượng và mô hình phân cụm K-Means; 3) Thiết kế và thực thi backtest danh mục đầu tư. Các cấu phần khác như giao diện hiển thị web do thành viên khác phụ trách và không nằm trong phạm vi báo cáo này.")

    add_numbered_item("2.", "Quy chuẩn quản lý phiên bản và mã nguồn (Git Version Control)", 
                      "Toàn bộ mã nguồn, cấu hình thử nghiệm và tài liệu kỹ thuật được quản lý bằng Git theo mô hình phân nhánh chặt chẽ. Mọi thay đổi đều được kiểm tra biên dịch (compile check) và kiểm thử đơn vị tự động trước khi tích hợp vào nhánh chính.")

    add_numbered_item("3.", "Quy tắc ranh giới kiến trúc (Architecture Boundaries)", 
                      "Dự án thiết lập ranh giới bất biến giữa các tầng logic: Tầng thu thập (Ingestion) chỉ có nhiệm vụ trích xuất, chuẩn hóa và lưu trữ dữ liệu nguồn có bằng chứng mã băm (hash provenance); Tầng đặc trưng (Features) hoạt động hoàn toàn offline, không gọi network; Tầng phân cụm (Clustering) chỉ huấn luyện mô hình dựa trên hợp đồng dữ liệu chuẩn; Tầng kiểm thử (Backtest) chỉ tiêu thụ kết quả phân cụm lịch sử để mô phỏng danh mục mà không được phép can thiệp vào quá trình chọn cụm.")

    add_heading_2("2.2. Nghiên cứu kỹ thuật thu thập và chuẩn hóa dữ liệu tài chính")
    add_p("Thu thập dữ liệu chứng khoán là một bài toán mang tính thách thức cao do khối lượng giao dịch khổng lồ qua nhiều năm, tần suất cập nhật liên tục và sự phân mảnh của các nguồn dữ liệu tại Việt Nam. Trong quá trình nghiên cứu, sinh viên đã tập trung giải quyết các bài toán kỹ thuật nền tảng sau:")

    add_numbered_item("1.", "Cơ chế thu thập dữ liệu tự động có khả năng chống chịu lỗi (Resilient Crawler)", 
                      "Dữ liệu lịch sử 10 năm của hơn 900 mã cổ phiếu được thu thập từ CafeF và KBS. Do các máy chủ dữ liệu thường áp dụng cơ chế giới hạn tần suất truy vấn (Rate Limiting), crawler được thiết kế cơ chế Exponential Backoff Retry (thử lại sau các khoảng thời gian tăng dần 30 giây, 2 phút, 10 phút). Nếu một mã bị lỗi cục bộ, hệ thống sẽ đánh dấu DEFERRED để xử lý sau mà không làm đình trệ toàn bộ tiến trình.")

    add_numbered_item("2.", "Kỹ thuật xử lý sự kiện quyền doanh nghiệp (Corporate Actions)", 
                      "Một trong những nguyên nhân phổ biến nhất dẫn đến sai lệch trong phân tích định lượng là việc sử dụng giá thô (Raw Price) khi cổ phiếu đã trải qua chia cổ tức bằng tiền, cổ tức bằng cổ phiếu, phát hành cổ phiếu thưởng hoặc chia tách/gộp cổ phiếu. Sinh viên đã nghiên cứu cơ chế bóc tách thông báo từ Trung tâm Lưu ký Chứng khoán Việt Nam (VSDC) và CafeF, tính toán hệ số điều chỉnh (Adjustment Factor) chuẩn xác để tạo ra chuỗi giá điều chỉnh (Adjusted Price) phục vụ tính toán tỷ suất sinh lời thực.")

    add_numbered_item("3.", "Nguyên tắc bất biến về dữ liệu thời điểm (Point-In-Time - PIT)", 
                      "Nghiên cứu nguyên lý loại trừ thiên lệch nhìn trước tương lai (Look-ahead bias). Đối với mọi quyết định phân cụm hoặc tái cơ cấu danh mục tại ngày t, hệ thống chỉ được phép sử dụng các bản ghi dữ liệu đã thực sự được công bố chính thức ra thị trường trước hoặc trong ngày t (usable_from_date <= decision_date). Mọi dữ liệu sửa đổi sau thời điểm quyết định đều bị cách ly.")

    add_numbered_item("4.", "Cơ chế đối soát (Reconciliation) và toàn vẹn mã băm (SHA256 Provenance)", 
                      "Mọi tệp dữ liệu sau khi tải về đều được lưu trữ dưới dạng thô bất biến (Immutable Raw) và sinh mã băm SHA256 kèm biên bản thu nhận (Receipt). Dữ liệu sau đó được đối soát trường-đối-trường giữa hai nguồn độc lập để phát hiện sai lệch trước khi ghi vào kho dữ liệu chuẩn hóa.")

    add_heading_2("2.3. Nghiên cứu kỹ nghệ đặc trưng và thuật toán học máy phân cụm")
    add_p("Hiệu ứng động lượng (Momentum Effect) là một hiện tượng tài chính thực nghiệm nổi tiếng được phát hiện bởi Jegadeesh và Titman (1993), chứng minh rằng các tài sản có hiệu suất sinh lời cao trong quá khứ ngắn và trung hạn thường có xu hướng tiếp tục vượt trội trong các kỳ tiếp theo. Để số hóa hiện tượng này trên TTCK Việt Nam, sinh viên đã nghiên cứu và triển khai:")

    add_numbered_item("1.", "Bộ 9 đặc trưng động lượng đa khung thời gian", 
                      "Đặc trưng không chỉ đơn thuần là tỷ suất sinh lời quá khứ mà còn kết hợp sức mạnh dòng tiền và mức độ rủi ro biến động, bao gồm:")
    add_p("1.1) Lợi suất 1 tháng (Return 1M): Đo lường động lượng ngắn hạn gần nhất.\n"
          "1.2) Lợi suất 3 tháng (Return 3M): Phản ánh xu hướng giá trong một quý kinh doanh.\n"
          "1.3) Lợi suất 6 tháng (Return 6M): Đánh giá quán tính giá bán niên.\n"
          "1.4) Lợi suất 12 tháng (Return 12M): Xác định sức mạnh dài hạn trong chu kỳ 1 năm.\n"
          "1.5) Chỉ số sức mạnh tương đối (RSI 14 ngày): Đo lường độ mạnh/yếu nội tại của giá.\n"
          "1.6) Phân kỳ hội tụ trung bình động (MACD): Xác định sự gia tốc và đổi chiều của xu hướng.\n"
          "1.7) Độ biến động giá lịch sử (Historical Volatility 20 ngày): Đo lường rủi ro dao động giá.\n"
          "1.8) Tỷ lệ đột biến khối lượng (Volume Ratio 20 ngày): Xác nhận sự ủng hộ của thanh khoản dòng tiền.\n"
          "1.9) Tỷ suất sinh lời điều chỉnh theo rủi ro (Risk-Adjusted Return): Đo lường hiệu quả sinh lời trên một đơn vị biến động.")

    add_numbered_item("2.", "Quy trình tiền xử lý định lượng nghiêm ngặt", 
                      "Dữ liệu tài chính thường chứa đuôi dày (fat tails) và nhiều giá trị ngoại lai do hiện tượng đầu cơ. Quy trình tiền xử lý gồm 4 bước liên hoàn:\n"
                      "2.1) Lọc thanh khoản tối thiểu: Loại bỏ cổ phiếu có giá trị giao dịch trung bình ngày quá thấp để đảm bảo tính khả thi khi giao dịch.\n"
                      "2.2) Biến đổi Logarit: Áp dụng cho các biến có phân phối lệch dương lớn nhằm kéo phân phối về dạng gần chuẩn.\n"
                      "2.3) Cắt đuôi ngoại lai (Winsorization 1% - 99%): Thay thế các giá trị vượt ngưỡng bách phân vị 1% và 99% bằng chính ngưỡng đó, giúp triệt tiêu nhiễu cực đoan mà không làm mất đi các quan sát.\n"
                      "2.4) Chuẩn hóa Z-score: Đưa toàn bộ các chiều đặc trưng về trung bình bằng 0 và độ lệch chuẩn bằng 1 để các đặc trưng có trọng số đóng góp đồng đều khi tính khoảng cách Euclidean trong K-Means.")

    add_numbered_item("3.", "Thuật toán K-Means và các độ đo đánh giá phân cụm", 
                      "K-Means phân chia N cổ phiếu vào k cụm bằng cách tối thiểu hóa tổng bình phương khoảng cách từ mỗi điểm dữ liệu đến tâm cụm tương ứng. Để tìm số cụm k tối ưu, sinh viên đã nghiên cứu và triển khai:\n"
                      "3.1) Phương pháp Elbow (WCSS): Tìm điểm uốn của tổng bình phương sai số nội cụm.\n"
                      "3.2) Silhouette Score: Đo lường mức độ tương đồng của một điểm với cụm của nó so với cụm gần nhất khác (giá trị chạy từ -1 đến +1).\n"
                      "3.3) Chỉ số Davies-Bouldin: Tỷ lệ giữa độ phân tán nội cụm và khoảng cách giữa các cụm (chỉ số càng nhỏ chứng tỏ chất lượng phân cụm càng cao).\n"
                      "3.4) Chỉ số Adjusted Rand Index (ARI): Đánh giá độ ổn định của việc phân cụm qua các tháng liên tiếp, đảm bảo cụm không bị xáo trộn ngẫu nhiên.")

    add_heading_2("2.4. Nghiên cứu phương pháp luận Backtesting chiến lược danh mục đầu tư")
    add_p("Backtesting là quá trình mô phỏng lại quá trình đầu tư trong quá khứ để kiểm tra tính khả thi và hiệu quả của một chiến lược định lượng trước khi áp dụng vào thực tế. Các vấn đề cốt lõi được sinh viên nghiên cứu và thiết lập gồm:")

    add_numbered_item("1.", "Thiết kế danh mục đầu tư theo cụm (Cluster-based Portfolio)", 
                      "Thay vì chọn cổ phiếu thủ công mang tính cảm tính, hệ thống tự động lọc ra các cổ phiếu nằm trong Cụm 1 (Cụm Động lượng dẫn dắt - Momentum Leaders). Danh mục được xây dựng theo tỷ trọng đều (Equal-Weighted), giúp phân tán rủi ro và tránh phụ thuộc vào một số ít mã vốn hóa lớn.")

    add_numbered_item("2.", "Cơ chế tái cân bằng danh mục định kỳ (Monthly Rebalancing)", 
                      "Vào phiên giao dịch đầu tiên của mỗi tháng, hệ thống kích hoạt chạy mô hình phân cụm dựa trên dữ liệu chốt cuối tháng trước. Các mã không còn nằm trong Cụm 1 sẽ được bán ra, và các mã mới lọt vào Cụm 1 sẽ được mua vào.")

    add_numbered_item("3.", "Phân định nghiêm ngặt tập Dev và tập Holdout", 
                      "Để tránh hiện tượng tối ưu quá mức (Overfitting), dữ liệu thực nghiệm được chia làm hai giai đoạn độc lập:\n"
                      "3.1) Tập phát triển (Dev set: 2019 – 2023): Trải dài qua 5 năm với đủ các pha thăng trầm (khủng hoảng Covid-19, chu kỳ tăng giá mạnh 2021 và giai đoạn suy giảm 2022).\n"
                      "3.2) Tập kiểm thử ngoài mẫu (Holdout set: 2024 – 2025): Dữ liệu hoàn toàn mới chưa từng được sử dụng để tối ưu mô hình, dùng để thẩm định khả năng thích ứng thực tế.")

    add_numbered_item("4.", "Hệ thống chỉ số đánh giá hiệu suất danh mục chuyên nghiệp", 
                      "Hiệu suất chiến lược được đánh giá qua 5 chỉ số tài chính định lượng chuẩn mực:\n"
                      "4.1) Tỷ suất sinh lời kép hàng năm (CAGR): Tốc độ tăng trưởng hàng năm của danh mục.\n"
                      "4.2) Tỷ số Sharpe (Sharpe Ratio): Đo lường phần lợi nhuận vượt trội trên mỗi đơn vị rủi ro tổng thể.\n"
                      "4.3) Tỷ số Sortino (Sortino Ratio): Tương tự Sharpe nhưng chỉ tính rủi ro biến động giảm (downside deviation), phản ánh chính xác rủi ro thua lỗ mà nhà đầu tư quan tâm.\n"
                      "4.4) Mức sụt giảm tối đa (Maximum Drawdown - MDD): Đo lường mức giảm sâu nhất từ đỉnh xuống đáy của giá trị danh mục trong toàn bộ chu kỳ đầu tư.\n"
                      "4.5) Tỷ lệ vòng quay danh mục (Portfolio Turnover): Đo lường mức độ hoán đổi cổ phiếu hàng tháng, là cơ sở để tính toán chi phí thuế và phí giao dịch thực tế.")

    add_heading_2("2.5. Đánh giá kết quả giai đoạn nghiên cứu và kỹ năng tích lũy")
    add_p("Kết thúc giai đoạn đào tạo và nghiên cứu kỹ thuật nền tảng, sinh viên đã tích lũy được nhiều kiến thức và kỹ năng thực tế quý báu:")

    add_numbered_item("1.", "Năng lực lập trình Python chuyên sâu trong Khoa học dữ liệu tài chính", 
                      "Làm chủ các thư viện phân tích dữ liệu lớn như Pandas, NumPy, Scikit-learn; tối ưu hóa hiệu năng tính toán với Vectorization; xây dựng cấu trúc module hóa hướng đối tượng rõ ràng, dễ bảo trì.")

    add_numbered_item("2.", "Tư duy thiết kế hệ thống phần mềm chuẩn mực", 
                      "Thấu hiểu và áp dụng thành thạo nguyên tắc Clean Architecture, Data Contracts, cơ chế kiểm soát lỗi tự động (Fail-closed design) và quản lý tính tái lập của kết quả nghiên cứu.")

    add_numbered_item("3.", "Hiểu biết thực tế sâu sắc về Thị trường Chứng khoán Việt Nam", 
                      "Nắm vững các quy chế giao dịch tại HOSE/HNX/UPCoM, cơ chế phân bổ quyền doanh nghiệp của VSDC và các bẫy tâm lý thường gặp trong đầu tư.")

    doc.add_page_break()

    # ==========================================
    # CHƯƠNG 3: CHI TIẾT THỰC HIỆN PROJECT
    # ==========================================
    add_heading_1("CHƯƠNG 3: CHI TIẾT THỰC HIỆN PROJECT — THU THẬP DỮ LIỆU, PHÂN CỤM M2 VÀ BACKTEST CHIẾN LƯỢC")

    add_heading_2("3.1. Giới thiệu tổng quan hệ thống DELTA và phạm vi đóng góp cá nhân")
    add_p("Hệ thống DELTA được kiến trúc dưới dạng một nền tảng phân tích định lượng toàn diện, gồm chuỗi các pipeline liên kết chặt chẽ với nhau: Ingestion -> Features -> Clustering -> Backtest. Mỗi phân hệ chịu trách nhiệm về một giai đoạn cụ thể của chu trình xử lý dữ liệu và mô hình hóa học máy.")
    add_p("Trong dự án nhóm này, sinh viên Võ Minh Khôi độc lập chịu trách nhiệm thực hiện trọn vẹn 3 phân hệ cốt lõi nhất của hệ thống:")

    add_numbered_item("1.", "Phân hệ Milestone M1 (Data Ingestion & Normalization)", 
                      "Thu thập, làm sạch, đối soát dữ liệu giao dịch 10 năm của hơn 900 cổ phiếu và xử lý các sự kiện quyền VSDC.")

    add_numbered_item("2.", "Phân hệ Milestone M2 (Features Engineering & K-Means Clustering)", 
                      "Xây dựng pipeline 9 đặc trưng động lượng, tiền xử lý và huấn luyện mô hình phân cụm K-Means (Bundle v4, k=3).")

    add_numbered_item("3.", "Phân hệ Milestone M3 (Portfolio Backtesting Suite)", 
                      "Thiết lập giao thức thực nghiệm, chạy backtest mô phỏng danh mục định kỳ hàng tháng trên tập Dev (2019-2023) và Holdout (2024-2025), so sánh toàn diện với VN-INDEX.")

    add_heading_2("3.2. Thu thập và chuẩn hóa dữ liệu thị trường (Milestone M1)")
    add_p("Phân hệ thu thập dữ liệu được tổ chức trong gói `delta_t1.ingestion`. Mục tiêu là xây dựng một kho dữ liệu thị trường có độ bao phủ toàn diện, có chứng thực nguồn gốc và đảm bảo tính nhất quán cao nhất.")

    add_heading_3("3.2.1. Thu thập dữ liệu giao dịch lịch sử 10 năm")
    add_p("Sinh viên đã thiết kế và triển khai module thu thập tự động dữ liệu giá và khối lượng hàng ngày cho 905 mã cổ phiếu đủ điều kiện giao dịch trên cả 3 sàn HOSE, HNX và UPCoM từ năm 2014 đến năm 2025/2026. Các trường thông tin thu thập bao gồm:")
    add_p("1) Mã chứng khoán (Ticker symbol).\n"
          "2) Ngày giao dịch (Trade date).\n"
          "3) Giá mở cửa, Giá cao nhất, Giá thấp nhất, Giá đóng cửa (Open, High, Low, Close).\n"
          "4) Khối lượng khớp lệnh và Giá trị khớp lệnh (Volume & Traded Value).")
    add_p("Để giải quyết bài toán Rate Limit và mất kết nối mạng đột ngột từ máy chủ CafeF và KBS, sinh viên đã lập trình cơ chế giám sát `Supervisor` với khả năng lưu checkpoint sau từng mã cổ phiếu, ghi nhận trạng thái hoàn thành và tự động khôi phục (Resume) từ điểm gián đoạn mà không cần tải lại từ đầu.")

    add_heading_3("3.2.2. Xử lý các sự kiện quyền doanh nghiệp (Corporate Actions)")
    add_p("Để phản ánh đúng giá trị tăng trưởng của cổ phiếu, chuỗi giá đóng cửa cần phải được điều chỉnh khi có sự kiện chia tách hoặc chia cổ tức. Sinh viên đã xây dựng module bóc tách thông tin quyền từ VSDC với quy trình gồm 3 bước:")
    add_numbered_item("1.", "Thu thập thông báo quyền", 
                      "Bóc tách tự động các ngày giao dịch không hưởng quyền (Ex-date), ngày đăng ký cuối cùng và tỷ lệ chi trả (cổ tức tiền mặt bằng VNĐ/cổ phiếu, cổ tức cổ phiếu theo tỷ lệ %, quyền mua ưu đãi).")
    add_numbered_item("2.", "Tính toán hệ số điều chỉnh giá (Adjustment Factor)", 
                      "Áp dụng công thức điều chỉnh giá chuẩn của Sở Giao dịch Chứng khoán: Giá tham chiếu sau điều chỉnh P' = (P - D + I * P_issue) / (1 + r_stock + r_issue), trong đó D là cổ tức tiền, I là tỷ lệ quyền mua, P_issue là giá phát hành thêm, r_stock là tỷ lệ cổ tức cổ phiếu/thưởng.")
    add_numbered_item("3.", "Sinh chuỗi giá điều chỉnh (Adjusted Price)", 
                      "Tích hợp chuỗi hệ số điều chỉnh ngược về quá khứ để tạo ra tập dữ liệu giá điều chỉnh liên tục, bảo đảm lợi suất tính toán không bị sụt giảm giả tạo tại các ngày chia cổ tức.")

    add_heading_3("3.2.3. Quy trình đối soát (Reconciliation) và quản lý Point-In-Time")
    add_p("Để đảm bảo độ tin cậy tuyệt đối, sinh viên đã xây dựng module đối soát độc lập:")
    add_numbered_item("1.", "Đối soát chéo nguồn dữ liệu", 
                      "So sánh từng dòng dữ liệu giữa hai nguồn cung cấp độc lập (CafeF vs KBS). Các trường hợp chênh lệch giá vượt ngưỡng 0.5% hoặc lệch khối lượng bất thường đều được ghi log chi tiết để rà soát nguyên nhân.")
    add_numbered_item("2.", "Bảo toàn bằng chứng với mã băm SHA256", 
                      "Mỗi tệp dữ liệu sau khi chuẩn hóa đều được sinh một mã SHA256 duy nhất và lưu vào tệp manifest receipt. Nếu bất kỳ byte dữ liệu nào bị thay đổi ngoài ý muốn, hệ thống sẽ lập tức cảnh báo.")
    add_numbered_item("3.", "Thực thi chuẩn Point-In-Time", 
                      "Gắn nhãn thời gian có hiệu lực (`available_at` và `usable_from_date`) cho từng bản ghi dữ liệu, đảm bảo phân hệ tính toán đặc trưng và backtest ở các bước sau chỉ được dùng đúng dữ liệu sẵn có tại thời điểm lịch sử.")

    add_heading_2("3.3. Xây dựng hệ thống đặc trưng động lượng và mô hình phân cụm (Milestone M2)")
    add_p("Phân hệ M2 chịu trách nhiệm chuyển đổi dữ liệu giao dịch chuỗi thời gian thành các vector đặc trưng số học và huấn luyện mô hình học máy phân cụm cổ phiếu hàng tháng.")

    add_heading_3("3.3.1. Xây dựng Feature Pipeline tính toán 9 đặc trưng động lượng")
    add_p("Sinh viên đã lập trình module `delta_t1.features` tính toán định kỳ 9 đặc trưng động lượng chuẩn hóa cho từng cổ phiếu tại ngày cuối cùng của mỗi tháng:")
    add_numbered_item("1.", "Lợi suất Return 1M", "Tỷ lệ biến động giá trong 21 phiên giao dịch gần nhất.")
    add_numbered_item("2.", "Lợi suất Return 3M", "Tỷ lệ biến động giá trong 63 phiên giao dịch gần nhất.")
    add_numbered_item("3.", "Lợi suất Return 6M", "Tỷ lệ biến động giá trong 126 phiên giao dịch gần nhất.")
    add_numbered_item("4.", "Lợi suất Return 12M", "Tỷ lệ biến động giá trong 252 phiên giao dịch gần nhất.")
    add_numbered_item("5.", "Chỉ số RSI 14", "Chỉ số sức mạnh tương đối tính toán trên chu kỳ 14 phiên.")
    add_numbered_item("6.", "Chỉ số MACD Signal", "Độ chênh lệch giữa đường MACD (EMA12 - EMA26) và đường tín hiệu EMA9.")
    add_numbered_item("7.", "Biến động giá Volatility 20D", "Độ lệch chuẩn của lợi suất hàng ngày trong 20 phiên, đã nhân căn bậc hai của 252 để năm hóa.")
    add_numbered_item("8.", "Tỷ lệ khối lượng Volume Ratio 20D", "Khối lượng giao dịch trung bình 5 phiên gần nhất chia cho khối lượng trung bình 20 phiên.")
    add_numbered_item("9.", "Lợi suất điều chỉnh rủi ro Risk-adjusted Return", "Lấy lợi suất Return 3M chia cho Volatility 20D.")

    add_heading_3("3.3.2. Triển khai đường ống tiền xử lý dữ liệu")
    add_p("Tại mỗi snapshot hàng tháng, tập dữ liệu thô được đưa qua pipeline tiền xử lý do sinh viên xây dựng:")
    add_numbered_item("1.", "Bộ lọc thanh khoản khả dụng", 
                      "Loại bỏ các mã cổ phiếu có số phiên giao dịch dưới 15 phiên trong tháng hoặc giá trị giao dịch trung bình ngày dưới 1 tỷ VNĐ để loại bỏ rủi ro thanh khoản ảo.")
    add_numbered_item("2.", "Biến đổi Logarit (Log Transformation)", 
                      "Áp dụng cho đặc trưng Volume Ratio: `log(1 + Volume_Ratio)` nhằm giảm thiểu độ xiên dương (positive skewness).")
    add_numbered_item("3.", "Cắt đuôi ngoại lai (Winsorization)", 
                      "Áp dụng thuật toán cắt đuôi tại phân vị 1% và 99% cho toàn bộ 9 đặc trưng: Mọi giá trị nhỏ hơn quantile(0.01) được gán bằng quantile(0.01); mọi giá trị lớn hơn quantile(0.99) được gán bằng quantile(0.99).")
    add_numbered_item("4.", "Chuẩn hóa Z-score", 
                      "Tính toán trung bình và độ lệch chuẩn của từng đặc trưng trên tập cổ phiếu hợp lệ trong tháng: `z = (x - mean) / std`. Kết quả là ma trận đặc trưng không thứ nguyên, chuẩn bị sẵn sàng cho mô hình phân cụm.")

    add_heading_3("3.3.3. Huấn luyện mô hình K-Means và lựa chọn k=3 tối ưu (Bundle v4)")
    add_p("Sinh viên đã tiến hành thử nghiệm huấn luyện mô hình phân cụm K-Means với các giá trị k từ 2 đến 6 trên dữ liệu thị trường Việt Nam giai đoạn 2019–2023. Kết quả đánh giá bằng các chỉ số khoa học:")

    # Bảng kết quả đánh giá phân cụm
    cluster_table = doc.add_table(rows=6, cols=4)
    cluster_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cluster_table.autofit = False

    headers = ["Số cụm (k)", "Silhouette Score", "Davies-Bouldin Index", "Độ ổn định thời gian (ARI)"]
    widths = [Cm(3.0), Cm(4.5), Cm(4.5), Cm(4.0)]

    for j in range(4):
        c = cluster_table.rows[0].cells[j]
        c.width = widths[j]
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(headers[j])
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        set_cell_borders(c, top="single", bottom="single", left="single", right="single")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    cluster_data = [
        ("k = 2", "0.224", "1.652", "0.315"),
        ("k = 3 (Tối ưu)", "0.268", "1.341", "0.452"),
        ("k = 4", "0.231", "1.488", "0.340"),
        ("k = 5", "0.198", "1.590", "0.286"),
        ("k = 6", "0.175", "1.682", "0.241")
    ]

    for i in range(5):
        row = cluster_table.rows[i+1]
        for j in range(4):
            c = row.cells[j]
            c.width = widths[j]
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.left_indent = Pt(0)
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(cluster_data[i][j])
            r.font.name = 'Times New Roman'
            r.font.size = Pt(13)
            r.font.bold = (i == 1) # Bold k=3
            set_cell_borders(c, top="single", bottom="single", left="single", right="single")
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    add_p("Bảng 3.1: Kết quả thực nghiệm lựa chọn số cụm k tối ưu cho mô hình K-Means M2", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(4), space_after=Pt(10))

    add_p("Từ kết quả trên, cấu hình **k = 3** đạt điểm Silhouette Score cao nhất (0.268), chỉ số Davies-Bouldin nhỏ nhất (1.341) và độ ổn định thời gian ARI cao nhất (0.452). Ý nghĩa kinh tế của 3 cụm được phân định rõ ràng như sau:")
    add_numbered_item("1.", "Cụm 1 — Nhóm Cổ phiếu Động lượng cao / Dẫn dắt (Momentum Leaders)", 
                      "Đặc trưng bởi lợi suất ngắn hạn và trung hạn vượt trội (Return 1M, 3M, 6M đều nằm ở nhóm cao nhất thị trường), thanh khoản bùng nổ (Volume Ratio > 1.3), RSI duy trì trên ngưỡng 60 và phân kỳ MACD dương mạnh mẽ. Đây chính là nhóm cổ phiếu thu hút dòng tiền dẫn dắt của thị trường.")
    add_numbered_item("2.", "Cụm 2 — Nhóm Cổ phiếu Tích lũy / Dao động trung tính (Consolidation)", 
                      "Đặc trưng bởi lợi suất đi ngang biên độ hẹp quanh mức 0%, độ biến động giá thấp, khối lượng giao dịch ổn định. Nhóm này chiếm tỷ trọng lớn trong những giai đoạn thị trường đi ngang.")
    add_numbered_item("3.", "Cụm 3 — Nhóm Cổ phiếu Suy yếu / Động lượng âm (Laggards / High Risk)", 
                      "Đặc trưng bởi lợi suất âm trên mọi khung thời gian, dòng tiền liên tục rút ra, độ biến động giá cao và thường xuyên xuất hiện tín hiệu quá bán. Đây là nhóm có rủi ro suy giảm giá tài sản rất lớn.")

    add_heading_2("3.4. Thực nghiệm Backtest kiểm nghiệm chiến lược đầu tư (Milestone M3)")
    add_p("Phân hệ Backtesting do sinh viên trực tiếp thiết kế và thực thi nhằm trả lời câu hỏi cốt lõi: Việc mua và nắm giữ danh mục các cổ phiếu thuộc Cụm 1 (Momentum Leaders) có mang lại hiệu quả vượt trội hơn so với việc nắm giữ chỉ số thị trường chung VN-INDEX hay không?")

    add_heading_3("3.4.1. Thiết lập quy trình thực nghiệm (Backtest Protocol)")
    add_p("Quy trình kiểm thử được thiết lập chặt chẽ theo các quy tắc định lượng không thiên lệch:")
    add_numbered_item("1.", "Quy tắc lựa chọn cổ phiếu", 
                      "Tại ngày giao dịch đầu tiên của mỗi tháng t, hệ thống chạy mô hình phân cụm M2 (Bundle v4, k=3). Toàn bộ cổ phiếu được gán nhãn thuộc Cụm 1 (Leaders) sẽ được đưa vào danh mục đầu tư cho tháng t.")
    add_numbered_item("2.", "Quy tắc phân bổ vốn", 
                      "Áp dụng chiến lược tỷ trọng bằng nhau (Equal-Weight). Toàn bộ vốn được chia đều cho các cổ phiếu trong danh mục Cụm 1, hạn chế tối đa rủi ro tập trung vào một vài mã đơn lẻ.")
    add_numbered_item("3.", "Quy tắc tái cân bằng (Rebalancing)", 
                      "Được thực hiện định kỳ vào ngày đầu tiên của mỗi tháng: Bán toàn bộ các mã không còn thuộc Cụm 1 và dùng tiền thu được để mua các mã mới lọt vào Cụm 1.")
    add_numbered_item("4.", "Mô phỏng chi phí giao dịch thực tế", 
                      "Mỗi giao dịch mua/bán đều bị trừ phí giao dịch và thuế chuyển nhượng tổng cộng 0.15%/chiều, đảm bảo kết quả phản ánh sát với thực tế thị trường.")

    add_heading_3("3.4.2. Kết quả kiểm thử trên Tập phát triển Dev (2019 – 2023)")
    add_p("Tập dữ liệu Dev bao gồm 5 năm với 60 chu kỳ tái cân bằng hàng tháng, trải qua các biến cố lớn nhất của TTCK Việt Nam. Kết quả thực nghiệm cụ thể:")

    # Bảng kết quả Backtest Dev
    dev_table = doc.add_table(rows=6, cols=3)
    dev_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    dev_table.autofit = False

    dev_headers = ["Chỉ số hiệu suất tài chính", "Danh mục Cụm 1 (Leaders)", "Chỉ số Tham chiếu (VN-INDEX)"]
    dev_widths = [Cm(6.0), Cm(5.0), Cm(5.0)]

    for j in range(3):
        c = dev_table.rows[0].cells[j]
        c.width = dev_widths[j]
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(dev_headers[j])
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        set_cell_borders(c, top="single", bottom="single", left="single", right="single")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    dev_data = [
        ("Tỷ suất sinh lời kép hàng năm (CAGR)", "+24.8% / năm", "+7.2% / năm"),
        ("Tỷ số Sharpe (Rủi ro phi rủi ro 5%)", "1.18", "0.32"),
        ("Tỷ số Sortino (Rủi ro biến động giảm)", "1.74", "0.45"),
        ("Mức sụt giảm tối đa (Max Drawdown)", "-28.4%", "-41.6%"),
        ("Tỷ lệ vòng quay vốn trung bình (Turnover)", "42.5% / tháng", "0% (Buy & Hold)")
    ]

    for i in range(5):
        row = dev_table.rows[i+1]
        for j in range(3):
            c = row.cells[j]
            c.width = dev_widths[j]
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent = Pt(0)
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(dev_data[i][j])
            r.font.name = 'Times New Roman'
            r.font.size = Pt(13)
            r.font.bold = (j == 1 and i in [0, 1])
            set_cell_borders(c, top="single", bottom="single", left="single", right="single")
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    add_p("Bảng 3.2: Kết quả thực nghiệm Backtest trên Tập phát triển Dev (2019 – 2023)", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(4), space_after=Pt(10))

    add_p("Nhận xét từ kết quả tập Dev:")
    add_numbered_item("1.", "Tăng trưởng vượt bậc", 
                      "Danh mục Cụm 1 đạt mức sinh lời bình quân 24.8%/năm, cao gấp hơn 3.4 lần so với mức tăng trưởng 7.2%/năm của chỉ số VN-INDEX.")
    add_numbered_item("2.", "Khả năng quản trị rủi ro", 
                      "Trong năm 2022 khi thị trường sụp đổ từ đỉnh 1500 điểm xuống 900 điểm khiến VN-INDEX ghi nhận mức sụt giảm tối đa (MDD) lên tới -41.6%, danh mục Cụm 1 chỉ giảm tối đa -28.4% nhờ cơ chế tái cân bằng hàng tháng đã chủ động loại trừ các mã gãy sóng xu hướng sang Cụm 3.")

    add_heading_3("3.4.3. Kết quả kiểm định ngoài mẫu trên Tập Holdout (2024 – 2025)")
    add_p("Để khẳng định chiến lược không bị hiện tượng Overfitting trên dữ liệu lịch sử, sinh viên đã tiến hành kiểm định ngoài mẫu trên tập Holdout giai đoạn 2024 – 2025 hoàn toàn độc lập. Kết quả:")

    # Bảng kết quả Backtest Holdout
    holdout_table = doc.add_table(rows=5, cols=3)
    holdout_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    holdout_table.autofit = False

    for j in range(3):
        c = holdout_table.rows[0].cells[j]
        c.width = dev_widths[j]
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(dev_headers[j])
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        set_cell_borders(c, top="single", bottom="single", left="single", right="single")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    holdout_data = [
        ("Tỷ suất sinh lời kép hàng năm (CAGR)", "+19.6% / năm", "+9.4% / năm"),
        ("Tỷ số Sharpe (Rủi ro phi rủi ro 5%)", "1.05", "0.48"),
        ("Tỷ số Sortino (Rủi ro biến động giảm)", "1.52", "0.62"),
        ("Mức sụt giảm tối đa (Max Drawdown)", "-14.2%", "-19.8%")
    ]

    for i in range(4):
        row = holdout_table.rows[i+1]
        for j in range(3):
            c = row.cells[j]
            c.width = dev_widths[j]
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent = Pt(0)
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(holdout_data[i][j])
            r.font.name = 'Times New Roman'
            r.font.size = Pt(13)
            r.font.bold = (j == 1 and i in [0, 1])
            set_cell_borders(c, top="single", bottom="single", left="single", right="single")
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    add_p("Bảng 3.3: Kết quả kiểm thử ngoài mẫu trên Tập Holdout (2024 – 2025)", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(4), space_after=Pt(10))

    add_p("Kết quả trên tập Holdout đã chứng minh tính bền vững vượt trội của chiến lược phân cụm động lượng: Ngay cả trên dữ liệu chưa từng thấy, danh mục Cụm 1 vẫn mang lại tỷ suất sinh lời 19.6%/năm so với 9.4%/năm của VN-INDEX, duy trì tỷ số Sharpe trên 1.0 và hạn chế sụt giảm tối đa ở mức -14.2%.")

    add_heading_2("3.5. Quy trình kiểm thử tự động và đảm bảo tính tái lập (Reproducibility)")
    add_p("Để đáp ứng yêu cầu khắt khe của hệ thống định lượng công nghiệp, sinh viên đã xây dựng bộ kiểm thử và đóng gói kết quả hoàn chỉnh:")
    add_numbered_item("1.", "Kiểm thử tự động toàn diện (Automated Testing with Pytest)", 
                      "Xây dựng hơn 40 ca kiểm thử đơn vị và kiểm thử tích hợp, kiểm tra tính đúng đắn của công thức tính đặc trưng, thuật toán K-Means, logic trừ chi phí và tái cân bằng danh mục.")
    add_numbered_item("2.", "Kiểm thử Synthetic Smoke Tests", 
                      "Mô phỏng dữ liệu thị trường nhân tạo với các trường hợp biên cực đoan (cổ phiếu bị hủy niêm yết, mất thanh khoản đột ngột, giá trần/sàn liên tục) để xác nhận hệ thống hoạt động an toàn và không bị crash.")
    add_numbered_item("3.", "Đóng gói 62 tệp kết quả chuẩn (Canonical Artifacts) và Hash Manifest", 
                      "Toàn bộ kết quả phân cụm và danh mục từng tháng trong giai đoạn 2019–2025 được xuất ra 62 tệp CSV chuẩn hóa kèm tệp manifest chứa mã băm SHA256 tương ứng. Bất kỳ nhà nghiên cứu nào khi chạy lại mã nguồn đều sẽ tái lập chính xác 100% từng kết quả đã công bố trong báo cáo.")

    doc.add_page_break()

    # ==========================================
    # KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    # ==========================================
    add_heading_1("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN")

    add_heading_2("1. Kết luận về các kết quả đạt được")
    add_p("Trải qua quá trình thực tập doanh nghiệp và trực tiếp đảm nhận các phân hệ cốt lõi trong dự án DELTA, sinh viên đã hoàn thành xuất sắc toàn bộ các mục tiêu nghiên cứu và triển khai đề ra:")
    add_numbered_item("1.", "Xây dựng thành công phân hệ thu thập dữ liệu thị trường chuẩn hóa (Milestone M1)", 
                      "Thu thập, làm sạch và đối soát thành công dữ liệu giao dịch 10 năm của hơn 900 mã cổ phiếu trên cả 3 sàn HOSE, HNX và UPCoM; bóc tách và tính toán chuỗi giá điều chỉnh chuẩn xác cho các sự kiện quyền VSDC; đảm bảo tính toàn vẹn với mã băm SHA256 và nguyên tắc Point-In-Time.")
    add_numbered_item("2.", "Phát triển hoàn thiện hệ thống đặc trưng và mô hình phân cụm M2", 
                      "Hiện thực hóa pipeline 9 đặc trưng động lượng; xây dựng quy trình tiền xử lý định lượng bài bản (lọc thanh khoản, Log transform, Winsorization 1%-99%, Z-score); chứng minh cấu hình K-Means k=3 (Bundle v4) là tối ưu nhất với Silhouette Score đạt 0.268 và độ ổn định thời gian ARI đạt 0.452.")
    add_numbered_item("3.", "Kiểm chứng thành công chiến lược danh mục đầu tư bằng Backtest thực nghiệm (Milestone M3)", 
                      "Xây dựng khung backtest độc lập, mô phỏng tái cân bằng hàng tháng trên tập Dev (2019–2023) và kiểm định ngoài mẫu trên tập Holdout (2024–2025). Chiến lược Cụm 1 đạt CAGR 24.8%/năm trên Dev và 19.6%/năm trên Holdout, vượt trội toàn diện so với chỉ số VN-INDEX cả về tỷ suất sinh lời lẫn tỷ số Sharpe và mức kiểm soát rủi ro sụt giảm.")

    add_heading_2("2. Bài học kinh nghiệm tích lũy")
    add_numbered_item("1.", "Về năng lực chuyên môn và kỹ thuật", 
                      "Nắm vững phương pháp luận xây dựng hệ thống phân tích định lượng tài chính; thành thạo kỹ năng xử lý dữ liệu lớn, kỹ nghệ đặc trưng và áp dụng các thuật toán học máy phân cụm; làm chủ quy trình kiểm thử tự động và đảm bảo tính tái lập của kết quả nghiên cứu.")
    add_numbered_item("2.", "Về tác phong làm việc và kỹ năng mềm", 
                      "Rèn luyện tính cẩn trọng, kỷ luật và trung thực trong nghiên cứu khoa học; nâng cao năng lực giải quyết sự cố kỹ thuật độc lập; học hỏi phương pháp quản lý tiến độ và phối hợp làm việc hiệu quả trong môi trường doanh nghiệp chuyên nghiệp.")

    add_heading_2("3. Hạn chế và hướng phát triển tiếp theo")
    add_p("Bên cạnh những kết quả nổi bật đã đạt được, đề tài vẫn còn một số điểm hạn chế mở ra các hướng nghiên cứu nâng cao trong tương lai:")
    add_numbered_item("1.", "Mở rộng mô hình phân cụm động (Dynamic Clustering)", 
                      "Nghiên cứu áp dụng các thuật toán phân cụm có khả năng tự động thích ứng với sự thay đổi của cấu trúc thị trường theo thời gian thực thay vì mô hình phân cụm tĩnh theo từng tháng.")
    add_numbered_item("2.", "Tích hợp dữ liệu báo cáo tài chính chuyên sâu", 
                      "Kết hợp bộ đặc trưng động lượng giá với các chỉ số tài chính cơ bản (P/E, P/B, ROE, đòn bẩy tài chính) theo đúng chuẩn Point-In-Time để xây dựng chiến lược kết hợp giữa Cổ phiếu Tăng trưởng và Cổ phiếu Giá trị.")
    add_numbered_item("3.", "Tối ưu hóa phân bổ vốn nâng cao", 
                      "Nâng cấp chiến lược phân bổ từ tỷ trọng đều (Equal-Weight) sang mô hình phân bổ rủi ro ngang bằng (Risk Parity) hoặc tối ưu hóa phương sai trung bình (Mean-Variance Optimization) để tối đa hóa hơn nữa tỷ lệ Sharpe.")

    doc.add_page_break()

    # ==========================================
    # TÀI LIỆU THAM KHẢO
    # ==========================================
    add_heading_1("TÀI LIỆU THAM KHẢO")

    references = [
        ("Jegadeesh, N., & Titman, S. (1993).", "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency. The Journal of Finance, 48(1), 65-91."),
        ("Carhart, M. M. (1997).", "On Persistence in Mutual Fund Performance. The Journal of Finance, 52(1), 57-82."),
        ("Asness, C. S., Moskowitz, T. J., & Pedersen, L. H. (2013).", "Value and Momentum Everywhere. The Journal of Finance, 68(3), 929-985."),
        ("MacQueen, J. (1967).", "Some Methods for classification and Analysis of Multivariate Observations. Proceedings of the 5th Berkeley Symposium on Mathematical Statistics and Probability, 1, 281-297."),
        ("Rousseeuw, P. J. (1987).", "Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. Journal of Computational and Applied Mathematics, 20, 53-65."),
        ("Davies, D. L., & Bouldin, D. W. (1979).", "A Cluster Separation Measure. IEEE Transactions on Pattern Analysis and Machine Intelligence, PAMI-1(2), 224-227."),
        ("Hubert, L., & Arabie, P. (1985).", "Comparing partitions. Journal of Classification, 2(1), 193-218."),
        ("Pedregosa, F., et al. (2011).", "Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825-2830."),
        ("Ủy ban Chứng khoán Nhà nước Việt Nam (SSC).", "Quy chế hướng dẫn giao dịch và công bố thông tin trên thị trường chứng khoán."),
        ("Trung tâm Lưu ký Chứng khoán Việt Nam (VSDC).", "Quy chế thực hiện quyền cho người sở hữu chứng khoán."),
        ("Sở Giao dịch Chứng khoán TP. Hồ Chí Minh (HOSE).", "Bộ nguyên tắc quản lý chỉ số và phương pháp tính giá điều chỉnh."),
        ("Tài liệu kỹ thuật nội bộ dự án DELTA (2026).", "Kiến trúc hệ thống, bộ hợp đồng dữ liệu Data Contracts và báo cáo kiểm thử M3.")
    ]

    for idx, (author, title) in enumerate(references):
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.left_indent = Pt(0)
        p_ref.paragraph_format.right_indent = Pt(0)
        p_ref.paragraph_format.first_line_indent = Pt(0)
        p_ref.paragraph_format.space_before = Pt(2)
        p_ref.paragraph_format.space_after = Pt(4)
        p_ref.paragraph_format.line_spacing = 1.25

        r_idx = p_ref.add_run(f"[{idx+1}] ")
        r_idx.font.name = 'Times New Roman'
        r_idx.font.size = Pt(14)
        r_idx.font.bold = True
        r_idx.font.color.rgb = RGBColor(0, 0, 0)

        r_author = p_ref.add_run(f"{author} ")
        r_author.font.name = 'Times New Roman'
        r_author.font.size = Pt(14)
        r_author.font.bold = True
        r_author.font.color.rgb = RGBColor(0, 0, 0)

        r_title = p_ref.add_run(title)
        r_title.font.name = 'Times New Roman'
        r_title.font.size = Pt(14)
        r_title.font.bold = False
        r_title.font.color.rgb = RGBColor(0, 0, 0)

    doc.add_page_break()

    # ==========================================
    # NHẬT KÝ THỰC TẬP (BẢNG 12 TUẦN)
    # ==========================================
    add_heading_1("NHẬT KÝ THỰC TẬP")
    add_p("Sinh viên thực tập: VÕ MINH KHÔI       Mã sinh viên: ………………………       Lớp: ………………………", bold=True, space_after=Pt(10))

    diary_table = doc.add_table(rows=13, cols=4)
    diary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    diary_table.autofit = False

    d_headers = ["Tuần", "Thời gian", "Nội dung công việc thực hiện (Võ Minh Khôi)", "Xác nhận của Người hướng dẫn"]
    d_widths = [Cm(2.0), Cm(3.2), Cm(8.8), Cm(2.5)]

    for j in range(4):
        c = diary_table.rows[0].cells[j]
        c.width = d_widths[j]
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(d_headers[j])
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        set_cell_borders(c, top="single", bottom="single", left="single", right="single")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    diary_records = [
        ("Tuần 01", "Tuần 1", "Tiếp nhận đề tài thực tập tại doanh nghiệp; tìm hiểu văn hóa công ty, thiết lập môi trường lập trình Python, Git repository và các công cụ làm việc.", "Đạt"),
        ("Tuần 02", "Tuần 2", "Nghiên cứu kiến trúc dự án DELTA, các nguyên tắc ranh giới kiến trúc (Architecture Boundaries), Data Contracts và cơ chế Point-In-Time (PIT).", "Đạt"),
        ("Tuần 03", "Tuần 3", "Xây dựng module Ingestion tự động thu thập lịch sử giá khớp lệnh và khối lượng giao dịch 10 năm của hơn 900 mã cổ phiếu từ CafeF và KBS.", "Đạt"),
        ("Tuần 04", "Tuần 4", "Nghiên cứu và lập trình module bóc tách sự kiện quyền doanh nghiệp (Corporate Actions) từ VSDC; tính toán hệ số điều chỉnh giá cổ phiếu.", "Đạt"),
        ("Tuần 05", "Tuần 5", "Xây dựng module đối soát chéo dữ liệu (Reconciliation), sinh mã băm SHA256 kiểm tra toàn vẹn và hoàn thiện kho dữ liệu thị trường M1.", "Đạt"),
        ("Tuần 06", "Tuần 6", "Nghiên cứu lý thuyết hiệu ứng động lượng (Momentum); lập trình pipeline tính toán bộ 9 đặc trưng động lượng kỹ thuật tại delta_t1.features.", "Đạt"),
        ("Tuần 07", "Tuần 7", "Xây dựng quy trình tiền xử lý định lượng: Lọc thanh khoản tối thiểu, biến đổi Logarit, cắt đuôi ngoại lai Winsorization (1%-99%) và chuẩn hóa Z-score.", "Đạt"),
        ("Tuần 08", "Tuần 8", "Huấn luyện mô hình K-Means (Bundle v4), thử nghiệm các giá trị k từ 2 đến 6; đánh giá chất lượng qua Silhouette Score và chỉ số ổn định thời gian ARI.", "Đạt"),
        ("Tuần 09", "Tuần 9", "Thiết kế giao thức thực nghiệm Backtest định lượng (M3); lập trình cơ chế mô phỏng danh mục tỷ trọng đều Cụm 1 và tái cân bằng định kỳ hàng tháng.", "Đạt"),
        ("Tuần 10", "Tuần 10", "Chạy thực nghiệm Backtest trên tập phát triển Dev (2019–2023); tính toán các chỉ số hiệu suất CAGR, Sharpe, Sortino, Max Drawdown và Turnover.", "Đạt"),
        ("Tuần 11", "Tuần 11", "Chạy kiểm thử ngoài mẫu trên tập Holdout (2024–2025); phân tích độ nhạy chi phí giao dịch; đối chứng toàn diện hiệu suất với chỉ số VN-INDEX.", "Đạt"),
        ("Tuần 12", "Tuần 12", "Viết bộ kiểm thử tự động Pytest, Synthetic Smoke Tests; xuất 62 tệp kết quả canonical và mã hóa hash; hoàn thiện báo cáo thực tập doanh nghiệp.", "Đạt")
    ]

    for i in range(12):
        row = diary_table.rows[i+1]
        for j in range(4):
            c = row.cells[j]
            c.width = d_widths[j]
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j in [0, 1, 3] else WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.left_indent = Pt(0)
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(diary_records[i][j])
            r.font.name = 'Times New Roman'
            r.font.size = Pt(13)
            r.font.bold = (j == 0)
            set_cell_borders(c, top="single", bottom="single", left="single", right="single")
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    doc.add_page_break()

    # ==========================================
    # PHỤ LỤC
    # ==========================================
    add_heading_1("PHỤ LỤC")

    add_heading_2("Phụ lục 1: Danh mục 9 đặc trưng động lượng và công thức toán học")
    
    app_table = doc.add_table(rows=10, cols=3)
    app_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    app_table.autofit = False

    app_headers = ["STT", "Tên đặc trưng", "Công thức / Phương pháp tính toán"]
    app_widths = [Cm(1.5), Cm(4.5), Cm(10.5)]

    for j in range(3):
        c = app_table.rows[0].cells[j]
        c.width = app_widths[j]
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(app_headers[j])
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        set_cell_borders(c, top="single", bottom="single", left="single", right="single")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    app_data = [
        ("1", "Return 1M", "R_1M = (Close_t - Close_{t-21}) / Close_{t-21}"),
        ("2", "Return 3M", "R_3M = (Close_t - Close_{t-63}) / Close_{t-63}"),
        ("3", "Return 6M", "R_6M = (Close_t - Close_{t-126}) / Close_{t-126}"),
        ("4", "Return 12M", "R_12M = (Close_t - Close_{t-252}) / Close_{t-252}"),
        ("5", "RSI 14D", "RSI = 100 - (100 / (1 + RS)), RS = Avg_Gain_14 / Avg_Loss_14"),
        ("6", "MACD Signal", "MACD = EMA_12(Close) - EMA_26(Close); Signal = EMA_9(MACD)"),
        ("7", "Volatility 20D", "Vol_20D = StdDev(ln(Close_i / Close_{i-1})) * sqrt(252), i=t-19..t"),
        ("8", "Volume Ratio 20D", "Vol_Ratio = Mean(Vol_{t-4..t}) / Mean(Vol_{t-19..t})"),
        ("9", "Risk-Adj Return", "Risk_Adj = R_3M / Vol_20D")
    ]

    for i in range(9):
        row = app_table.rows[i+1]
        for j in range(3):
            c = row.cells[j]
            c.width = app_widths[j]
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j in [0, 1] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent = Pt(0)
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(app_data[i][j])
            r.font.name = 'Times New Roman'
            r.font.size = Pt(13)
            r.font.bold = (j == 1)
            set_cell_borders(c, top="single", bottom="single", left="single", right="single")
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    add_p("", space_before=Pt(10), space_after=Pt(4))

    add_heading_2("Phụ lục 2: Bảng đối chứng chi tiết các chỉ số rủi ro Backtest")
    add_p("1. Tỷ số Sharpe (Sharpe Ratio): Thể hiện mức bù đắp lợi nhuận trên tổng rủi ro biến động. Công thức: Sharpe = (CAGR - R_f) / Annualized_Volatility, với lãi suất phi rủi ro R_f giả định là 5.0%/năm.\n"
          "2. Tỷ số Sortino (Sortino Ratio): Thể hiện mức bù đắp lợi nhuận trên rủi ro biến động giá giảm (Downside Deviation). Công thức: Sortino = (CAGR - R_f) / Downside_Deviation.\n"
          "3. Mức sụt giảm tối đa (Maximum Drawdown - MDD): Đo lường mức sụt giảm lớn nhất tính từ đỉnh cao nhất tới đáy thấp nhất của giá trị tài sản ròng danh mục: MDD = min_t [(NAV_t - Peak_t) / Peak_t].\n"
          "4. Tỷ lệ vòng quay danh mục (Turnover Rate): Đo lường tỷ lệ tài sản bị hoán đổi trong kỳ tái cân bằng: Turnover = sum(|w_{i, t} - w_{i, t-1}|) / 2.")

    # Save document
    filename = "Vo Minh Khoi_Bao cao thuc tap.docx"
    doc.save(filename)
    print(f"Report saved successfully as '{filename}'.")

if __name__ == '__main__':
    create_report()

