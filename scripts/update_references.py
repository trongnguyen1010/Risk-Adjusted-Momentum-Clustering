# -*- coding: utf-8 -*-
"""
Script to update the References section in 'Vo Minh Khoi_Bao cao thuc tap.docx'
adding the 3 requested Vietnam momentum papers plus the highly relevant paper
discovered in the ref folder (Aslam, 2025).
"""

import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

DOCX_PATH = "Vo Minh Khoi_Bao cao thuc tap.docx"

UPDATED_REFERENCES = [
    # 1. Cơ sở lý thuyết tài chính hành vi & hiệu quả thị trường
    "Barberis, N., Shleifer, A., & Vishny, R. (1998). A model of investor sentiment. Journal of Financial Economics, 49(3), 307-343.",
    "Fama, E. F. (1970). Efficient capital markets: A review of theory and empirical work. The Journal of Finance, 25(2), 383-417.",
    
    # 2. Cơ sở lý thuyết động lượng kinh điển
    "Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. The Journal of Finance, 48(1), 65-91.",
    
    # 3. Nghiên cứu thực nghiệm Động lượng & Phân cụm tại TTCK Việt Nam
    "Vo, X. V., & Truong, Q. B. (2018). Does momentum work? Evidence from Vietnam stock market. Journal of Behavioral and Experimental Finance, 17, 10-15.",
    "Nguyen, T. H. (2012). Momentum Effect in the Vietnamese Stock Market. Procedia - Social and Behavioral Sciences, 40, 505-511.",
    "Le, H., & Bertrand, P. (2023). Overreaction and momentum in the Vietnamese stock market. Managerial Finance, 49(8), 1279-1300.",
    "Aslam, B. (2025). Identifying optimistic stocks with K-means clustering algorithm. International Review of Economics and Finance, 104, 104579.",

    # 4. Thuật toán phân cụm & Thước đo đánh giá cụm
    "MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. Proceedings of the 5th Berkeley Symposium on Mathematical Statistics and Probability, 1, 281-297.",
    "Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. Journal of Computational and Applied Mathematics, 20, 53-65.",
    "Davies, D. L., & Bouldin, D. W. (1979). A cluster separation measure. IEEE Transactions on Pattern Analysis and Machine Intelligence, 1(2), 224-227.",
    "Calinski, T., & Harabasz, J. (1974). A dendrite method for cluster analysis. Communications in Statistics, 3(1), 1-27.",
    "Hubert, L., & Arabie, P. (1985). Comparing partitions. Journal of Classification, 2(1), 193-218.",

    # 5. Căn cứ pháp lý & Quy chế giao dịch TTCK Việt Nam
    "Ủy ban Chứng khoán Nhà nước & Sở Giao dịch Chứng khoán TP.HCM (HOSE). Quy chế giao dịch chứng khoán niêm yết và quy định điều chỉnh giá tham chiếu trong ngày giao dịch không hưởng quyền.",
    "Ủy ban Chứng khoán Nhà nước & Các Sở giao dịch Chứng khoán HOSE, HNX. Quy chế giao dịch và chuẩn mực công bố thông tin trên thị trường chứng khoán Việt Nam."
]

def update_references(docx_path=DOCX_PATH):
    doc = docx.Document(docx_path)

    # Find the heading 'TÀI LIỆU THAM KHẢO'
    heading_idx = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == "TÀI LIỆU THAM KHẢO":
            heading_idx = i
            break

    if heading_idx is None:
        raise ValueError("Could not find 'TÀI LIỆU THAM KHẢO' heading in document!")

    print(f"Found heading at paragraph {heading_idx}: '{doc.paragraphs[heading_idx].text}'")

    # Find where the references end
    end_idx = heading_idx + 1
    while end_idx < len(doc.paragraphs):
        p_text = doc.paragraphs[end_idx].text.strip()
        if any(p_text.startswith(kw) for kw in ["NHẬT KÝ", "PHỤ LỤC", "CHƯƠNG"]):
            break
        end_idx += 1

    print(f"Old references span from paragraph {heading_idx + 1} to {end_idx - 1}")

    # Remove old reference paragraphs
    # Collect paragraph elements to remove
    target_p_before = doc.paragraphs[end_idx]  # The paragraph right after old references (e.g. NHẬT KÝ THỰC TẬP or empty p)

    # We will remove the old reference paragraphs between heading_idx and end_idx
    old_p_list = doc.paragraphs[heading_idx + 1 : end_idx]
    for p in old_p_list:
        p._p.getparent().remove(p._p)

    # Now insert the new references before target_p_before
    for idx, ref_text in enumerate(UPDATED_REFERENCES, start=1):
        full_text = f"{idx}. {ref_text}"
        new_p = doc.add_paragraph()
        new_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        new_p.paragraph_format.left_indent = Pt(0)
        new_p.paragraph_format.right_indent = Pt(0)
        new_p.paragraph_format.first_line_indent = Pt(0)
        new_p.paragraph_format.space_before = Pt(2)
        new_p.paragraph_format.space_after = Pt(4)
        new_p.paragraph_format.line_spacing = 1.15

        r = new_p.add_run(full_text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.color.rgb = RGBColor(0, 0, 0)

        target_p_before._p.addprevious(new_p._p)

    doc.save(docx_path)
    print(f"Successfully updated References to {len(UPDATED_REFERENCES)} citations in '{docx_path}'!")

if __name__ == "__main__":
    update_references()
