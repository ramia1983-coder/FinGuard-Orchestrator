import sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from finguard.storage import connect,save_batch,save_assessment,review_case
from finguard.reports import make_docx,make_pdf
import pytest

def test_reports_approval_and_formats(tmp_path):
    con=connect(str(tmp_path/'test.db'))
    case={'case_id':'batch-FG-test','typology':'fan_in','transaction_ids':['t1']}
    tx={'transaction_id':'t1','source_account':'A','destination_account':'B','amount':'100','payment_currency':'GBP'}
    save_batch(con,'batch',[tx],[case],[])
    save_assessment(con,case['case_id'],{'summary':'Multiple deposits need review','risk_level':'medium','source':'openai','limitations':'Insufficient context', 'regulatory_citations':[{'source_id':'finra_aml','title':'FINRA AML','url':'https://www.finra.org','text_excerpt':'Sample'}]})
    with pytest.raises(PermissionError):make_pdf(con,case['case_id'])
    with pytest.raises(PermissionError):make_docx(con,case['case_id'])
    review_case(con,case['case_id'],'approved','training_reviewer','Reviewed for training')
    pdf=make_pdf(con,case['case_id']);docx=make_docx(con,case['case_id'])
    assert pdf.startswith(b'%PDF-')
    assert docx.startswith(b'PK')
    from docx import Document
    from io import BytesIO
    content='\n'.join(p.text for p in Document(BytesIO(docx)).paragraphs)
    assert 'Risk level: medium' in content and 'FINRA AML' in content and 'Insufficient context' in content
