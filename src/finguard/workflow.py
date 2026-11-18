"""Auditable node-by-node LangGraph pipeline; safe offline execution supported."""
from typing import TypedDict
from .detection import detect_candidates
from .assessment import assess,validate_assessment
from .regulations import retrieve
import os
class CaseState(TypedDict,total=False):
    transactions:list
    candidates:list
    findings:list
    retrieved:list
    assessed:list

def detect_node(state):
    return {'candidates':detect_candidates(state['transactions'])}

def retrieve_node(state):
    mode=os.getenv('FINGUARD_RETRIEVAL_MODE','lexical')
    return {'retrieved':[retrieve(case,mode=mode,persist_dir=os.getenv('FINGUARD_CHROMA_PATH')) for case in state['candidates']]}

def assess_node(state):
    txmap={t['transaction_id']:t for t in state['transactions']}
    assessed=[]
    for case,passages in zip(state['candidates'],state['retrieved']):
        evidence=[txmap[i] for i in case['transaction_ids'] if i in txmap]
        assessed.append(assess(case,evidence,passages))
    return {'assessed':assessed}

def validate_node(state):
    findings=[]
    for case,passages,assessment in zip(state['candidates'],state['retrieved'],state['assessed']):
        valid,reason=validate_assessment(case,assessment,passages)
        if not valid:
            assessment={'summary':'Assessment failed evidence validation.','risk_level':'requires_analyst_review','limitations':[reason],'transaction_ids':case['transaction_ids'],'regulatory_citations':[],'source':'validation_fallback'}
        findings.append({'case':case,'assessment':assessment,'valid':valid,'validation_reason':reason})
    return {'findings':findings}

def run_workflow(transactions):
    nodes=[('detect',detect_node),('retrieve',retrieve_node),('assess',assess_node),('validate',validate_node)]
    try:
        from langgraph.graph import StateGraph,START,END
        graph=StateGraph(CaseState)
        for name,fn in nodes:graph.add_node(name,fn)
        graph.add_edge(START,'detect')
        for a,b in zip(nodes,nodes[1:]):graph.add_edge(a[0],b[0])
        graph.add_edge('validate',END)
        return graph.compile().invoke({'transactions':transactions})
    except ImportError:
        state={'transactions':transactions}
        for _,fn in nodes:state.update(fn(state))
        return state
