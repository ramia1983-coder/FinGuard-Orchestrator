
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from finguard.regulations import retrieve,load_knowledge
from finguard.workflow import run_workflow
from finguard.evaluation import evaluate_transactions

def test_curated_regulatory_metadata():
    records=load_knowledge()
    assert records and all(p['url'].startswith('https://') for p in records)
    assert retrieve({'typology':'possible_structuring'})

def test_workflow_four_stages():
    tx={'transaction_id':'t1','source_account':'A','destination_account':'B','amount':'100','timestamp':'2022-01-01T00:00:00','payment_currency':'USD','received_currency':'USD','origin_country':'US','destination_country':'US','payment_type':'Transfer'}
    result=run_workflow([tx])
    assert all(key in result for key in ('candidates','retrieved','assessed','findings'))

def test_eval_metrics():
    path=Path(__file__).resolve().parents[1]/'data'/'labeled_examples_1000.csv'
    metrics=evaluate_transactions(path,limit=100)
    assert metrics['evaluated_transactions'] == 100
    assert metrics['tp']+metrics['fp']+metrics['fn']+metrics['tn']==100
