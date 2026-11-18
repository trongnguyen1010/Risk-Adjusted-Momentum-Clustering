"""Seal visually reviewed scan evidence and two unsigned observed-field proposals."""
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path,PureWindowsPath
import re
import sys
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from delta_t1.ingestion.corporate_action_sources import now
from delta_t1.ingestion.corporate_action_offline_reconcile import date_view
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    from pypdf import PdfReader
    out=ROOT/'tmp/ca_dtp_asg_evidence_20261102_v1'
    if (out/'manifest.json').exists():raise FileExistsError('REFUSE_OVERWRITE_SEALED_EVIDENCE')
    inputs={}
    def safe(name):
        rel=PureWindowsPath(name)
        if rel.drive or rel.root or '..' in rel.parts:raise ValueError('PATH_ESCAPE')
        return ROOT.joinpath(*rel.parts)
    def pin(path,expected=None):
        body=path.read_bytes();digest=sha(body)
        if expected and digest!=expected:raise ValueError('INPUT_HASH_MISMATCH: '+str(path))
        inputs[path.relative_to(ROOT).as_posix()]=digest
        return body
    config=json.loads(pin(ROOT/'configs/data/corporate_action_dtp_asg_documents_v1.json'))
    base=ROOT/'tmp/ca_cached26_review_20261102_v1'
    bm=json.loads(pin(base/'manifest.json',config['cached26_manifest_sha256']))
    rows={r['vci_payload_sha256']:r for r in (json.loads(l) for l in pin(base/'reviewed_payloads_26.jsonl',bm['files']['reviewed_payloads_26.jsonl']).splitlines() if l.strip())}
    old_docs={r['document_id']:r for r in (json.loads(l) for l in pin(base/'reparsed_documents.jsonl',bm['files']['reparsed_documents.jsonl']).splitlines() if l.strip())}
    visual=json.loads((out/'visual_transcriptions.json').read_bytes())
    if visual['owner_approved']:raise ValueError('VISUAL_REVIEW_IS_NOT_OWNER_APPROVAL')
    documents={};complete_pdfs=[]
    for d in visual['documents']:
        folder=safe(d['acquisition_root']);manifest=json.loads(pin(folder/'manifest.json'))
        docs=json.loads(pin(folder/'documents.json',manifest['files']['documents.json']))
        matches=[r for r in docs if r['status']=='PUBLIC_PDF_RECEIVED' and unquote(urlsplit(r['url']).path).rsplit('/',1)[-1]==d['document_filename']]
        if len(matches)!=1:raise ValueError('EXACT_COMPLETE_PUBLIC_DOCUMENT_REQUIRED')
        source=matches[0];path=folder/source['receipt']['path'];body=pin(path,source['receipt']['source_hash'])
        if len(body)!=source['size_bytes']:raise ValueError('PDF_LENGTH_MISMATCH')
        pdf=PdfReader(path)
        if len(pdf.pages)!=d['pdf_pages'] or pdf.is_encrypted:raise ValueError('PDF_STRUCTURE_MISMATCH')
        if any(not 1<=p<=len(pdf.pages) for p in d['reviewed_pages']):raise ValueError('REVIEW_PAGE_RANGE')
        for name in d['evidence_images']:
            image=out/name
            if not image.is_file() or not image.read_bytes().startswith(b'\x89PNG'):raise ValueError('RENDERED_EVIDENCE_MISSING')
        documents[d['id']]=d|{'source_url':source['url'],'source_role':source['role'],'raw_path':path.relative_to(ROOT).as_posix(),
            'raw_sha256':source['receipt']['source_hash'],'size_bytes':len(body),'actual_pdf_pages':len(pdf.pages),
            'text_extraction_status':'SCANNED_NO_TEXT_ON_REVIEWED_PAGES','digital_signature_verified':False}
        complete_pdfs.append(path.relative_to(ROOT).as_posix())
    notice=documents['dtp_offering_notice'];schedule=documents['dtp_schedule_resolution'];asg=documents['asg_offering_prospectus']
    def vi(value):return Decimal(value.replace(',','.'))
    def legs(d):return Fraction(vi(d['rights_per_allocation']))/Fraction(vi(d['existing_shares']))*Fraction(vi(d['new_shares_literal']))/Fraction(vi(d['execution_rights']))
    def exact(value):return {'numerator':value.numerator,'denominator':value.denominator,'decimal':str(Decimal(value.numerator)/Decimal(value.denominator))}
    dtp_ratio=legs(notice);asg_ratio=legs(asg)
    if dtp_ratio!=Fraction(vi(notice['declared_ratio_percent_literal'].rstrip('%')))/100:raise ValueError('PERCENT_AND_LEGS_CONFLICT')
    if notice['offering_license_reference']!=schedule['offering_license_reference'] or notice['license_date']!=schedule['license_date'] or notice['document_date']!=schedule['document_date']:raise ValueError('DTP_DOCUMENT_LINK_MISMATCH')
    dtp=rows[config['targets']['DTP']['payload_sha256']];old_asg=rows[config['targets']['ASG']['payload_sha256']]
    if schedule['record_date']!=date_view(dtp['original_sdk_row']['record_date']):raise ValueError('DTP_RECORD_DATE_MISMATCH')
    old_asg_doc=old_docs[old_asg['candidate_sources'][0]['document_id']]
    dtp_doc=old_docs[dtp['candidate_sources'][0]['document_id']]
    # Raw data and reviewed literals must agree; do not derive a price from ratios.
    for d,old in [(notice,dtp_doc),(asg,old_asg_doc)]:
        text=old['article_text']
        quantity=f"{d['offer_quantity_shares']:,}".replace(',','.')
        price=f"{d['primary_price_vnd']:,}".replace(',','.')
        if quantity not in text or price not in text:raise ValueError('OLD_NEW_OFFER_QUANTITY_OR_PRICE_MISMATCH')
    if asg_ratio!=Fraction(str(old_asg['original_sdk_row']['ratio'])):raise ValueError('ASG_RATIO_MISMATCH')
    if dtp_ratio!=Fraction(dtp['candidate_sources'][0]['source_ratio_exact']['numerator'],dtp['candidate_sources'][0]['source_ratio_exact']['denominator']):raise ValueError('DTP_VSDC_SOURCE_RATIO_MISMATCH')
    proposals=[{
        'ticker':'DTP','vci_payload_sha256':dtp['vci_payload_sha256'],'original_sdk_row':dtp['original_sdk_row'],
        'evidence_status':'ISSUER_OFFERING_NOTICE_CONFIRMS_VSDC_LITERAL_RATIO','record_date':schedule['record_date'],
        'observed_rights_ratio':exact(dtp_ratio),'observed_price_vnd_per_share':notice['primary_price_vnd'],
        'source_ratio_percent_literal':notice['declared_ratio_percent_literal'],
        'source_documents':['dtp_offering_notice','dtp_schedule_resolution'],
        'sdk_ratio_difference_remains':dtp_ratio!=Fraction(str(dtp['original_sdk_row']['ratio'])),
        'one_third_inferred':False,'selection_proposal':'Select observed source ratio333333/1000000 only after explicit case-specific approval; preserve SDK0.33333333 and conflict evidence.',
        'review_status':'MANUAL_REVIEW_REQUIRED','field_approved':False,'canonical_written':False},
        {'ticker':'ASG','vci_payload_sha256':old_asg['vci_payload_sha256'],'original_sdk_row':old_asg['original_sdk_row'],
        'evidence_status':'PRIMARY_OFFER_PRICE_UNIT_EXPLICIT_IN_ISSUER_PROSPECTUS_COPY','record_date':date_view(old_asg['original_sdk_row']['record_date']),
        'observed_rights_ratio':exact(asg_ratio),'observed_price_vnd_per_share':asg['primary_price_vnd'],
        'primary_unit_literal':asg['primary_price_unit_literal'],'primary_unit_pages':[104,105],
        'offer_quantity_shares':asg['offer_quantity_shares'],'source_documents':['asg_offering_prospectus'],
        'cross_source_link_evidence':['issuer name','primary price amount','offer quantity7244987','allocation1:1 andexecution100:15','Q1/2020 planned period; actual record date remains VSDC evidence'],
        'residual_price_unit_borrowed':False,'terminal_execution_confirmed':False,'event_identity_approved':False,
        'selection_proposal':'Observed18000VND/share primary offer price is supported; request field selection after event/revision review, not final research approval.',
        'review_status':'MANUAL_REVIEW_REQUIRED','field_approved':False,'canonical_written':False}]
    acquisition_roots=['tmp/ca_dtp_asg_documents_20261102_v1','tmp/ca_dtp_asg_documents_20261102_v2','tmp/ca_dtp_asg_pdfs_20261102_v1','tmp/ca_asg_prospectus_20261102_v1']
    attempts=[]
    for name in acquisition_roots:
        folder=safe(name);m=json.loads(pin(folder/'manifest.json'))
        rs=json.loads(pin(folder/'requests.json',m['files']['requests.json']))
        if 'head_receipt.json' in m['files']:rs=[json.loads(pin(folder/'head_receipt.json',m['files']['head_receipt.json']))]+rs
        attempts.extend({'artifact_root':name,**r} for r in rs)
    summary={'stage':'DTP_ASG_TARGET_EVIDENCE_REVIEW_V1','technical_stage_status':'PASS','data_status':'SUPPORTED_OBSERVED_FIELDS_PENDING_APPROVAL',
        'targets_reviewed':2,'complete_new_pdf_documents':3,'total_pdf_pages':sum(d['pdf_pages'] for d in documents.values()),
        'unique_pdf_pages_visually_reviewed':sum(len(d['reviewed_pages']) for d in documents.values()),
        'asg_primary_unit_supported_before_after':[False,True],'dtp_primary_issuer_ratio_confirmation_before_after':[False,True],
        'dtp_sdk_source_ratio_difference_preserved':True,'approved_fields_before_after':[0,0],'canonical_rows_written':0,
        'formal_acquisition_attempts_including_environment_failures':len(attempts),'http_responses':sum('status' in r for r in attempts),
        'environment_dns_failures':sum('getaddrinfo failed' in r.get('error','') for r in attempts),
        'head_requests':sum(r.get('method')=='HEAD' for r in attempts),'discovery_web_requests':'Separate uninstrumented discovery, not included in formal attempt count.',
        'hnx_network_requests':0,'tls_verification':True,'prior_truncated_pdf_used':False,'prior_decision_packet_applied':False,
        'pit_status':'NOT_PROMOTED','historical_identity':'UNVERIFIED','review_status':'MANUAL_REVIEW_REQUIRED',
        'limitations':['Scan facts are visual transcriptions with page PNGs; PDF copies are hosted on the named adviser/market archive, not cryptographically authenticated issuer files.',
            'Source document dates are not verified publication timestamps; no historical available_at assigned.',
            'Only selected ASG pages reviewed; this stage does not certify full revision history or actual terminal execution.',
            'Repeated Info-key parser warnings in DTP PDFs do not change raw bytes; rendered pages were reviewed.']}
    def dump(name,value):
        with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    dump('documents_reviewed.json',documents);dump('field_proposals.json',proposals);dump('summary.json',summary)
    dump('acquisition_attempts.json',attempts)
    dump('next_step_proposal.json',{'status':'MANUAL_REVIEW_REQUIRED','proposal':'Complete cached original-to-revision linkage for six conditional cases, then present final observed-field selections for explicit owner approval before application.',
        'conditional_cases':['DXG2023','GSP2021','SPB2023','KOS2020','KPF2021','LCG2019'],'new_sources_required_for_current_two_target_fields':False,
        'prior_packet_not_overwritten':True,'canonical_build':False})
    for name,digest in inputs.items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError('INPUT_CHANGED')
    dump('self_review.json',{'status':'PASS','input_hashes_rechecked':len(inputs),'visual_review_documents':len(documents),
        'ratio_percent_and_allocation_execution_checks':'PASS','old_new_price_quantity_date_link_checks':'PASS',
        'complete_pdf_files_only':complete_pdfs,'zero_approved_fields':all(not p['field_approved'] for p in proposals),'canonical_build':False})
    code=[Path(__file__),ROOT/'src/delta_t1/ingestion/corporate_action_target_documents.py']
    dump('manifest.json',{'artifact_type':'dtp-asg-visual-primary-document-evidence-v1','created_at':now(),'inputs_verified':inputs,
        'files':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()},
        'code_hashes':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in code},'approved_fields':0,'canonical_build':False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
