"""Analyst-gated training reports. No SAR filing or legal determination is made."""
from io import BytesIO
from xml.sax.saxutils import escape
import json
from .storage import get_case, get_case_transactions

DISCLAIMER = 'TRAINING / DEMONSTRATION ONLY — NOT A FILED SAR'
NOTICE = ('Analyst approval in this class project is a demonstration workflow only. '
          'It does not establish wrongdoing, authorize a SAR filing, or replace legal and compliance review.')

def report_data(con, case_id):
    row = get_case(con, case_id)
    if not row:
        raise ValueError('Case not found')
    if row['status'] != 'approved':
        raise PermissionError('Only analyst-approved cases can be exported')
    review = con.execute('SELECT reviewer, notes, created_at FROM reviews WHERE case_id=? AND decision=? ORDER BY id DESC LIMIT 1',
                         (case_id, 'approved')).fetchone()
    return (json.loads(row['payload']), json.loads(row['assessment']) if row['assessment'] else {},
            get_case_transactions(con, case_id), dict(review) if review else None)

def _as_list(value):
    if value is None or value == '':
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]

def _citations(assessment):
    result = []
    for item in assessment.get('regulatory_citations', []) or []:
        if isinstance(item, dict):
            result.append((str(item.get('title') or item.get('source_id') or 'Reference'),
                           str(item.get('source_id') or ''), str(item.get('url') or ''),
                           str(item.get('text_excerpt') or '')))
        else:
            result.append((str(item), str(item), '', ''))
    return result

def _tx_row(tx):
    return [str(tx.get('transaction_id','')), str(tx.get('source_account','')),
            str(tx.get('destination_account','')),
            f"{tx.get('amount','')} {tx.get('payment_currency','')}"]

def make_docx(con, case_id):
    from docx import Document
    from docx.shared import Inches, Pt
    case, assessment, transactions, review = report_data(con, case_id)
    doc = Document()
    sec = doc.sections[0]
    sec.header_distance = Inches(.35)
    doc.add_heading('FinGuard | Investigation Draft', 0)
    doc.add_paragraph(DISCLAIMER)
    doc.add_heading('Case Summary', 1)
    doc.add_paragraph(f"Case ID: {case_id}\nPattern: {case.get('typology','Unknown')}\nStatus: Analyst approved (training)\nRisk level: {assessment.get('risk_level','Not specified')}\nAssessment source: {assessment.get('source','Not specified')}")
    doc.add_heading('Assessment', 1)
    doc.add_paragraph(str(assessment.get('summary') or 'No AI assessment available.'))
    doc.add_heading('Transaction Evidence', 1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Shading Accent 1'
    for cell, label in zip(table.rows[0].cells, ['Transaction ID','Sender','Receiver','Amount / Currency']):
        cell.text = label
    for tx in transactions:
        for cell, value in zip(table.add_row().cells, _tx_row(tx)):
            cell.text = value
    doc.add_heading('Regulatory References (Project Summaries)', 1)
    citations = _citations(assessment)
    if citations:
        for title, source_id, url, excerpt in citations:
            doc.add_paragraph(title + (f' [{source_id}]' if source_id else ''), style='List Bullet')
            if url: doc.add_paragraph('Reference: ' + url)
            if excerpt: doc.add_paragraph('Provided excerpt: ' + excerpt)
    else:
        doc.add_paragraph('No regulatory references supplied.')
    doc.add_paragraph('References are project-authored summaries and have not been independently verified for jurisdictional applicability.')
    doc.add_heading('Limitations', 1)
    limits = _as_list(assessment.get('limitations'))
    for item in limits: doc.add_paragraph(item, style='List Bullet')
    if not limits: doc.add_paragraph('No limitations supplied in the assessment.')
    doc.add_heading('Analyst Review', 1)
    if review:
        doc.add_paragraph(f"Reviewer: {review.get('reviewer','')}\nApproved at (UTC): {review.get('created_at','')}\nReview notes: {review.get('notes','')}")
    else:
        doc.add_paragraph('Approved status recorded; reviewer details unavailable.')
    doc.add_paragraph(NOTICE)
    styles = doc.styles
    styles['Normal'].font.size = Pt(9)
    out = BytesIO(); doc.save(out); return out.getvalue()

def make_pdf(con, case_id):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import inch
    case, assessment, transactions, review = report_data(con, case_id)
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=(612,792), rightMargin=43,leftMargin=43,topMargin=44,bottomMargin=43)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='FinBody',parent=styles['BodyText'],fontSize=9,leading=13,spaceAfter=7))
    styles.add(ParagraphStyle(name='FinSmall',parent=styles['BodyText'],fontSize=8,leading=11,spaceAfter=5))
    styles.add(ParagraphStyle(name='FinHeader',parent=styles['Heading2'],spaceBefore=14,spaceAfter=7))
    p = lambda s, sty='FinBody': Paragraph(escape(str(s)),styles[sty])
    items = [p('FinGuard | Investigation Draft','Title'),p(DISCLAIMER,'FinSmall'),Spacer(1,9),
             p('Case Summary','FinHeader'),p('Case ID: '+case_id),p('Pattern: '+str(case.get('typology','Unknown'))),
             p('Status: Analyst approved (training)'),p('Risk level: '+str(assessment.get('risk_level','Not specified'))),
             p('Assessment source: '+str(assessment.get('source','Not specified'))),
             p('Assessment','FinHeader'),p(assessment.get('summary') or 'No AI assessment available.'),
             p('Transaction Evidence','FinHeader')]
    rows = [[p(x,'FinSmall') for x in ['Transaction ID','Sender','Receiver','Amount / Currency']]]
    rows.extend([[p(x,'FinSmall') for x in _tx_row(tx)] for tx in transactions])
    tbl=Table(rows,colWidths=[105,116,116,181],repeatRows=1,hAlign='LEFT')
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9EFF7')),
                             ('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),
                             ('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,colors.grey),
                             ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F9FC')])]))
    items.append(tbl)
    items.append(p('Regulatory References (Project Summaries)','FinHeader'))
    citations = _citations(assessment)
    for title, sid, url, excerpt in citations:
        items.append(p(title + (f' [{sid}]' if sid else ''),'FinBody'))
        if url: items.append(p('Reference: '+url,'FinSmall'))
        if excerpt: items.append(p('Provided excerpt: '+excerpt,'FinSmall'))
    if not citations: items.append(p('No regulatory references supplied.'))
    items.append(p('References are project-authored summaries and have not been independently verified for jurisdictional applicability.','FinSmall'))
    items.append(p('Limitations','FinHeader'))
    for limit in _as_list(assessment.get('limitations')) or ['No limitations supplied in the assessment.']:
        items.append(p('- '+limit))
    items.append(p('Analyst Review','FinHeader'))
    if review:
        for label,key in [('Reviewer','reviewer'),('Approved at (UTC)','created_at'),('Review notes','notes')]:
            items.append(p(label+': '+str(review.get(key,''))))
    else:
        items.append(p('Approved status recorded; reviewer details unavailable.'))
    items.append(Spacer(1,8));items.append(p(NOTICE,'FinSmall'))
    doc.build(items)
    return stream.getvalue()
