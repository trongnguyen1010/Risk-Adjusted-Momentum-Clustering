import docx
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import qn, nsdecls
import xml.etree.ElementTree as ET

doc_path = 'Vo Minh Khoi_Bao cao thuc tap.docx'
doc = docx.Document(doc_path)

print("1. Updating styles.xml...")
# Fix styles in doc.styles
for s_name, left_val in [('toc 1', 0), ('toc 2', 280), ('toc 3', 520)]:
    try:
        s = doc.styles[s_name]
        pPr = s.element.get_or_add_pPr()
        ind = pPr.find(qn('w:ind'))
        if ind is None:
            ind = OxmlElement('w:ind')
            pPr.append(ind)
        ind.set(qn('w:left'), str(left_val))
        ind.set(qn('w:firstLine'), '0')
        ind.set(qn('w:right'), '0')
        if qn('w:hanging') in ind.attrib:
            del ind.attrib[qn('w:hanging')]
        print(f"  Updated style '{s_name}': left={left_val}, firstLine=0")
    except KeyError:
        print(f"  Style '{s_name}' not found!")

print("\n2. Updating TOC paragraphs in SDT 0...")
sdts = doc.element.xpath('//w:sdt')
if not sdts:
    print("  ERROR: No SDT found!")
else:
    sdt = sdts[0]
    ps = sdt.findall('.//' + qn('w:p'))
    print(f"  Found {len(ps)} paragraphs in SDT 0")
    
    for i, p in enumerate(ps):
        pPr = p.get_or_add_pPr()
        pStyle = pPr.find(qn('w:pStyle'))
        style_val = pStyle.get(qn('w:val')) if pStyle is not None else ''
        
        if style_val == 'TOC1':
            ind = pPr.find(qn('w:ind'))
            if ind is None:
                ind = OxmlElement('w:ind')
                pPr.append(ind)
            ind.set(qn('w:left'), '0')
            ind.set(qn('w:firstLine'), '0')
            ind.set(qn('w:right'), '0')
            if qn('w:hanging') in ind.attrib:
                del ind.attrib[qn('w:hanging')]
                
        elif style_val == 'TOC2':
            ind = pPr.find(qn('w:ind'))
            if ind is None:
                ind = OxmlElement('w:ind')
                pPr.append(ind)
            ind.set(qn('w:left'), '280') # 0.49 cm
            ind.set(qn('w:firstLine'), '0')
            ind.set(qn('w:right'), '0')
            if qn('w:hanging') in ind.attrib:
                del ind.attrib[qn('w:hanging')]
                
            # If paragraph has tab at 1760 (Chapter 4 headings), clean it up
            tabs_el = pPr.find(qn('w:tabs'))
            if tabs_el is not None:
                for tab in list(tabs_el.findall(qn('w:tab'))):
                    if tab.get(qn('w:pos')) == '1760':
                        tabs_el.remove(tab)
                        
            # Clean up tab between number and text in hyperlink
            hyperlink = p.find(qn('w:hyperlink'))
            if hyperlink is not None:
                runs = hyperlink.findall(qn('w:r'))
                # If first run is "4.1" and second run has w:tab
                if len(runs) >= 3:
                    t1 = ''.join(runs[0].itertext()).strip()
                    has_tab = runs[1].find(qn('w:tab')) is not None
                    if t1 in ['4.1', '4.2', '4.3', '4.4'] and has_tab:
                        # Replace tab in run 1 with ". "
                        runs[0].find(qn('w:t')).text = t1 + '. '
                        hyperlink.remove(runs[1])
                        print(f"  Cleaned tab in TOC2 P[{i}]: {t1}")
                        
        elif style_val == 'TOC3':
            ind = pPr.find(qn('w:ind'))
            if ind is None:
                ind = OxmlElement('w:ind')
                pPr.append(ind)
            ind.set(qn('w:left'), '520') # 0.92 cm
            ind.set(qn('w:firstLine'), '0')
            ind.set(qn('w:right'), '0')
            if qn('w:hanging') in ind.attrib:
                del ind.attrib[qn('w:hanging')]
                
            # Clean up tab at 1980 if present
            tabs_el = pPr.find(qn('w:tabs'))
            if tabs_el is not None:
                for tab in list(tabs_el.findall(qn('w:tab'))):
                    if tab.get(qn('w:pos')) == '1980':
                        tabs_el.remove(tab)
                        
            # Clean up tab in hyperlink runs between number (e.g. 2.2.1) and text
            hyperlink = p.find(qn('w:hyperlink'))
            if hyperlink is not None:
                runs = hyperlink.findall(qn('w:r'))
                if len(runs) >= 3:
                    t1 = ''.join(runs[0].itertext()).strip()
                    has_tab = runs[1].find(qn('w:tab')) is not None
                    if has_tab and (t1.count('.') >= 2):
                        # Convert to ". "
                        runs[0].find(qn('w:t')).text = t1.rstrip('.') + '. '
                        hyperlink.remove(runs[1])
                        # print(f"  Cleaned tab in TOC3 P[{i}]: {t1}")

print("\n3. Updating Chapter 4 Headings in Body...")
# Clean up Chapter 4 body headings to remove numPr and add standard prefix
h2_map = {
    379: '4.1. Kết luận về các kết quả thực nghiệm và sản phẩm kỹ thuật đạt được',
    389: '4.2. Đóng góp cá nhân và bài học nghề nghiệp tích lũy của sinh viên',
    401: '4.3. Những hạn chế kỹ thuật và định hướng phát triển trong tương lai',
    413: '4.4. Lời cảm ơn và tri ân'
}
for p_idx, text_val in h2_map.items():
    p = doc.paragraphs[p_idx]
    pPr = p._p.get_or_add_pPr()
    numPr = pPr.find(qn('w:numPr'))
    if numPr is not None:
        pPr.remove(numPr)
    ind = pPr.find(qn('w:ind'))
    if ind is not None:
        ind.set(qn('w:left'), '0')
        ind.set(qn('w:firstLine'), '0')
        if qn('w:hanging') in ind.attrib:
            del ind.attrib[qn('w:hanging')]
    # Update run text
    runs = p._p.findall('.//' + qn('w:r'))
    t_found = False
    for r in runs:
        t_el = r.find(qn('w:t'))
        if t_el is not None and not t_found:
            t_el.text = text_val
            t_found = True
        elif t_el is not None and t_found:
            t_el.text = ''
    print(f"  Updated Chapter 4 Heading 2 P[{p_idx}]: {text_val[:40]}...")

h3_map = {
    391: '4.2.1. Về năng lực chuyên môn và kỹ thuật định lượng',
    395: '4.2.2. Về tư duy khoa học dữ liệu tài chính khắt khe',
    398: '4.2.3. Về quy chuẩn kỹ nghệ phần mềm và đạo đức nghề nghiệp'
}
for p_idx, text_val in h3_map.items():
    p = doc.paragraphs[p_idx]
    pPr = p._p.get_or_add_pPr()
    numPr = pPr.find(qn('w:numPr'))
    if numPr is not None:
        pPr.remove(numPr)
    ind = pPr.find(qn('w:ind'))
    if ind is not None:
        ind.set(qn('w:left'), '357')
        ind.set(qn('w:firstLine'), '0')
        if qn('w:hanging') in ind.attrib:
            del ind.attrib[qn('w:hanging')]
    runs = p._p.findall('.//' + qn('w:r'))
    t_found = False
    for r in runs:
        t_el = r.find(qn('w:t'))
        if t_el is not None and not t_found:
            t_el.text = text_val
            t_found = True
        elif t_el is not None and t_found:
            t_el.text = ''
    print(f"  Updated Chapter 4 Heading 3 P[{p_idx}]: {text_val[:40]}...")

output_path = 'Vo Minh Khoi_Bao cao thuc tap.docx'
doc.save(output_path)
print(f"\nDocument successfully saved to {output_path}!")
