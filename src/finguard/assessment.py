"""Optional OpenAI assessment; deterministic offline fallback."""
import json
import os

def assess(case, transactions, passages=None):
    passages=passages or []
    baseline={'summary':f"Potential {case['typology'].replace('_',' ')} pattern detected by configured rules.", 'risk_level':'requires_analyst_review','transaction_ids':case['transaction_ids'],'regulatory_citations':[],'limitations':['Pattern flag alone is not proof of money laundering.','No verified regulatory citations supplied.'],'source':'deterministic_fallback'}
    if not os.getenv('OPENAI_API_KEY') or not passages:
        return baseline
    try:
        from openai import OpenAI
        client=OpenAI(timeout=25,max_retries=1)
        response=client.chat.completions.create(model=os.getenv('FINGUARD_OPENAI_MODEL','gpt-4.1-mini'),temperature=0,response_format={'type':'json_object'},messages=[{'role':'system','content':'You assist AML analysts. Return JSON with summary, risk_level, transaction_ids, regulatory_citations, limitations. Never invent evidence, transaction IDs, citations, or legal conclusions. Ground citations only in the provided passages.'},{'role':'user','content':json.dumps({'case':case,'transactions':transactions,'regulatory_passages':passages})}])
        answer=json.loads(response.choices[0].message.content)
        answer['source']='openai'
        return answer
    except Exception as exc:
        baseline['limitations'].append(f'AI unavailable ({type(exc).__name__}); deterministic fallback used.')
        return baseline


def validate_assessment(case, assessment, passages):
    allowed = {str(x) for x in case["transaction_ids"]}
    known = {
        str(p["source_id"])
        for p in passages
        if isinstance(p, dict) and "source_id" in p
    }

    txids = assessment.get("transaction_ids", [])
    citations = assessment.get("regulatory_citations", [])

    if not isinstance(txids, list):
        return False, "Transaction IDs must be a list"

    for tx in txids:
        if isinstance(tx, dict):
            tx_id = tx.get("transaction_id", tx.get("id"))
        else:
            tx_id = tx

        if not isinstance(tx_id, (str, int)) or isinstance(tx_id, bool):
            return False, "Invalid transaction ID"

        if str(tx_id) not in allowed:
            return False, "Unrecognized transaction ID"

    if not isinstance(citations, list):
        return False, "Citations must be a list"

    for citation in citations:
        if isinstance(citation, dict):
            citation_id = citation.get("source_id", citation.get("id"))
        else:
            citation_id = citation

        if not isinstance(citation_id, (str, int)) or isinstance(citation_id, bool):
            return False, "Invalid citation ID"

        if str(citation_id) not in known:
            return False, "Unrecognized regulatory citation"

    if not isinstance(assessment.get("summary"), str):
        return False, "Missing summary"

    return True, "passed"
