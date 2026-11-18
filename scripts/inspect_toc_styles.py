import docx
from docx.oxml.ns import qn

doc = docx.Document('Vo Minh Khoi_Bao cao thuc tap.docx')

print("=== INSPECTING SDT ELEMENTS ===")
sdts = doc.element.xpath('//w:sdt')
print(f"Total SDT elements: {len(sdts)}")

for i, sdt in enumerate(sdts):
    ps = sdt.findall('.//' + qn('w:p'))
    print(f"\nSDT {i} has {len(ps)} paragraphs")
    for j, p in enumerate(ps[:15]):
        pPr = p.find(qn('w:pPr'))
        style = pPr.find(qn('w:pStyle')) if pPr is not None else None
        s_val = style.get(qn('w:val')) if style is not None else 'None'
        ind = pPr.find(qn('w:ind')) if pPr is not None else None
        ind_attrs = dict(ind.attrib) if ind is not None else {}
        text = ''.join(p.itertext()).strip()
        if text:
            print(f"  P[{j}] style={s_val} ind={ind_attrs} text={text[:60]}")

print("\n=== INSPECTING TOC STYLES IN STYLES.XML ===")
styles = doc.styles
for s in styles:
    if 'toc' in s.name.lower() or 'normal' in s.name.lower():
        pPr = s.element.find(qn('w:pPr'))
        ind = pPr.find(qn('w:ind')) if pPr is not None else None
        ind_attrs = dict(ind.attrib) if ind is not None else 'None'
        base = s.base_style.name if s.base_style else 'None'
        print(f"Style name='{s.name}', id='{s.style_id}', base='{base}', ind={ind_attrs}")
