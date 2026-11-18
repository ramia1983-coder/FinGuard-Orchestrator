"""Batch entry point shared by CLI and Streamlit."""
import hashlib
from pathlib import Path
from .ingestion import load_transactions
from .workflow import run_workflow
from .storage import connect,save_batch,save_assessment

def process_file(file_path,db_path='finguard.db',limit=5000):
    path=Path(file_path)
    # Batch identity incorporates the file content and requested row limit.
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    batch_id=digest.hexdigest()[:12]+'-'+str(limit)
    tx,labels,errors=load_transactions(path,limit=limit)
    result=run_workflow(tx)
    # Scope candidate IDs by batch to prevent cross-batch collision.
    for case in result['candidates']:case['case_id']=batch_id+'-'+case['case_id']
    con=connect(db_path)
    if con.execute('SELECT 1 FROM batches WHERE batch_id=?',(batch_id,)).fetchone():
        con.close()
        return {'batch_id':batch_id,'transactions':len(tx),'errors':len(errors),'cases':len(result['candidates']),'already_processed':True}
    save_batch(con,batch_id,tx,result['candidates'],errors)
    for finding in result['findings']:
        case=finding['case']
        assessment=finding['assessment']
        if not finding['valid']:
            assessment={'summary':'Assessment failed evidence validation.','limitations':[finding['validation_reason']],'transaction_ids':case['transaction_ids'],'regulatory_citations':[],'source':'validation_fallback'}
        save_assessment(con,case['case_id'],assessment)
    con.close()
    return {'batch_id':batch_id,'transactions':len(tx),'errors':len(errors),'cases':len(result['candidates']),'already_processed':False,'error_samples':errors[:10]}
