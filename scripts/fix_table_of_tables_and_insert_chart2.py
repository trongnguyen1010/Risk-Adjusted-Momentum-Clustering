# -*- coding: utf-8 -*-
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
import shutil
import os

DOCX_PATH = "Vo Minh Khoi_Bao cao thuc tap.docx"
BACKUP_PATH = "Vo Minh Khoi_Bao cao thuc tap_backup_before_chart2_and_tot_fix.docx"

# Backup
shutil.copyfile(DOCX_PATH, BACKUP_PATH)
print(f"Backup created at: {BACKUP_PATH}")

doc = docx.Document(DOCX_PATH)

# ==============================================================================
# PART 1: FIX DANH MỤC BẢNG BIỂU (DOT LEADERS & RIGHT ALIGNED PAGE NUMBERS)
# ==============================================================================
print("\n--- Fixing DANH MỤC BẢNG BIỂU ---")

# Paragraph 69 is title 'DANH MỤC BẢNG BIỂU'
p69 = doc.paragraphs[69]
p69.alignment = WD_ALIGN_PARAGRAPH.CENTER
p69.paragraph_format.space_before = Pt(14)
p69.paragraph_format.space_after = Pt(10)
p69.paragraph_format.first_line_indent = Pt(0)
p69.paragraph_format.left_indent = Pt(0)
p69.paragraph_format.right_indent = Pt(0)
for r in p69.runs:
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.bold = True

# Paragraphs 70 to 75 are the table list entries
for p_idx in range(70, 76):
    p = doc.paragraphs[p_idx]
    pPr = p._p.get_or_add_pPr()
    
    # 1. Update/Add Right Tab stop at 9072 dxa (16.0cm) with leader="dot"
    tabs = pPr.find(qn('w:tabs'))
    if tabs is None:
        tabs = OxmlElement('w:tabs')
        pPr.append(tabs)
    else:
        tabs.clear()
    
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right')
    tab.set(qn('w:leader'), 'dot')
    tab.set(qn('w:pos'), '9072')
    tabs.append(tab)
    
    # 2. Clear weird indents
    ind = pPr.find(qn('w:ind'))
    if ind is not None:
        ind.set(qn('w:left'), '0')
        ind.set(qn('w:firstLine'), '0')
        ind.set(qn('w:right'), '0')
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.left_indent = Pt(0)
    p.paragraph_format.right_indent = Pt(0)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    # 3. Inside hyperlinks, replace the space run with a tab run (<w:tab/>)
    for hl in p._element.xpath('.//w:hyperlink'):
        runs = hl.xpath('.//w:r')
        # The run separating title and page number is runs[1] which contains a space
        for r_node in runs:
            t_node = r_node.find(qn('w:t'))
            if t_node is not None and t_node.text == ' ':
                # Replace <w:t> </w:t> with <w:tab/>
                r_node.remove(t_node)
                tab_node = OxmlElement('w:tab')
                r_node.append(tab_node)
                
    # 4. In P70, remove \p " " from TOC field code
    if p_idx == 70:
        for instr in p._element.xpath('.//w:instrText'):
            if 'TOC' in instr.text:
                instr.text = ' TOC \\h \\z \\t "Bảng biểu1,1,Bảng biểu,1" '
                print("Updated TOC field code in P70 to include both Bảng biểu styles without space separator.")

print("DANH MỤC BẢNG BIỂU has been formatted with right-aligned dots (leader=dot).")


# ==============================================================================
# PART 2: INSERT BIỂU ĐỒ 2 (HÌNH 3.4)
# ==============================================================================
print("\n--- Inserting Biểu đồ 2 (Hình 3.4: Strategy Performance Comparison) ---")
chart2_path = "reports/figures/strategy_performance_comparison.png"
if os.path.exists(chart2_path):
    # Target: right after paragraph 365 (discussion of limitations/lessons, end of section 3.5)
    target_p = None
    for p in doc.paragraphs:
        if "Các giới hạn kỹ thuật và bài học phương pháp luận rút ra từ dự án" in p.text:
            target_p = p
            break
            
    if target_p is not None:
        # Caption paragraph
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(4)
        p_cap.paragraph_format.space_after = Pt(12)
        p_cap.paragraph_format.first_line_indent = Pt(0)
        p_cap.paragraph_format.left_indent = Pt(0)
        p_cap.paragraph_format.right_indent = Pt(0)
        
        run_cap = p_cap.add_run("Hình 3.4: Đối sánh tỷ suất sinh lời kép (CAGR) và mức sụt giảm tối đa (MDD) giữa các chiến lược thực nghiệm trên hai tập Development và Holdout")
        run_cap.bold = True
        run_cap.font.name = "Times New Roman"
        run_cap.font.size = Pt(11.5)
        
        # Image paragraph
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        p_img.paragraph_format.first_line_indent = Pt(0)
        p_img.paragraph_format.left_indent = Pt(0)
        p_img.paragraph_format.right_indent = Pt(0)
        
        run_img = p_img.add_run()
        run_img.add_picture(chart2_path, width=Inches(5.8))
        
        # Insert target_p -> p_img -> p_cap
        target_p._p.addnext(p_cap._p)
        target_p._p.addnext(p_img._p)
        print("Inserted Hình 3.4 successfully at the end of Section 3.5!")
    else:
        print("WARNING: Could not find target paragraph for Hình 3.4")
else:
    print(f"WARNING: Image not found: {chart2_path}")

doc.save(DOCX_PATH)
print(f"Document saved successfully: {DOCX_PATH}")
