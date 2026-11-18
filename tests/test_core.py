import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from finguard.ingestion import load_transactions
from finguard.detection import detect_candidates
from finguard.assessment import validate_assessment
from finguard.storage import connect,save_batch,review_case
from finguard.reports import report_data
import pytest

def tx(i,sender='A',receiver='B',amount='9000',timestamp='2022-01-01T00:00:00'):
    return {'transaction_id':f't{i}','source_account':sender,'destination_account':receiver,'amount':amount,'timestamp':timestamp,'payment_currency':'USD','received_currency':'USD','origin_country':'US','destination_country':'US','payment_type':'Transfer'}

def test_ingestion_no_label_leak():
    path=Path(__file__).resolve().parents[1]/'data'/'development_first_50000.csv'
    rows,labels,errors=load_transactions(path,limit=3)
    assert len(rows)==3 and not errors
    assert 'is_laundering' not in rows[0] and 'laundering_type' not in rows[0]
    assert len(labels)==3

def test_structuring():
    rows=[tx(1),tx(2,timestamp='2022-01-01T01:00:00'),tx(3,timestamp='2022-01-01T02:00:00')]
    cases=detect_candidates(rows)
    assert any(c['typology']=='possible_structuring' for c in cases)

def test_no_cross_currency_aggregation():
    rows=[tx(1),tx(2),tx(3)]
    rows[2]['payment_currency']='EUR'
    assert not any(c['typology']=='possible_structuring' for c in detect_candidates(rows))

def test_cycle():
    cases=detect_candidates([tx(1,'A','B'),tx(2,'B','C'),tx(3,'C','A')])
    assert any(c['typology']=='circular_flow' for c in cases)

def test_reject_hallucinated_ids():
    case={'transaction_ids':['t1']}
    assert not validate_assessment(case,{'summary':'x','transaction_ids':['fake'],'regulatory_citations':[]},[])[0]

def test_export_requires_approval(tmp_path):
    con=connect(str(tmp_path/'db.sqlite'))
    rows=[tx(1)]
    case={'case_id':'case1','typology':'test','transaction_ids':['t1'],'accounts':['A'],'details':{},'status':'pending_review'}
    save_batch(con,'batch1',rows,[case],[])
    with pytest.raises(PermissionError):report_data(con,'case1')
    review_case(con,'case1','approved','Analyst A')
    assert report_data(con,'case1')[0]['case_id']=='case1'
    con.close()
