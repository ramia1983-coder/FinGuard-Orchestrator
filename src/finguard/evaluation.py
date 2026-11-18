"""Transaction-level screening metrics; NOT case-level accuracy or SAR validity."""
from .ingestion import load_transactions
from .detection import detect_candidates

def evaluate_transactions(csv_path,limit=1000):
    tx,labels,errors=load_transactions(csv_path,limit=limit)
    candidates=detect_candidates(tx)
    flagged={tid for case in candidates for tid in case['transaction_ids']}
    def positive(value):return str(value).strip().lower() in {'1','true','yes'}
    y={tid:positive(v['is_laundering']) for tid,v in labels.items() if str(v.get('is_laundering','')).strip()!=''}
    tp=sum(tid in flagged and truth for tid,truth in y.items())
    fp=sum(tid in flagged and not truth for tid,truth in y.items())
    fn=sum(tid not in flagged and truth for tid,truth in y.items())
    tn=sum(tid not in flagged and not truth for tid,truth in y.items())
    div=lambda a,b:a/b if b else None
    return {'evaluated_transactions':len(y),'candidate_cases':len(candidates),'validation_errors':len(errors),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn),'false_positive_rate':div(fp,fp+tn),'limitations':['Transaction-level labels used; case-level labels not available.','Sampling and heuristic candidate expansion can distort metrics.','Ground-truth labels are excluded from detection and AI prompts.']}
