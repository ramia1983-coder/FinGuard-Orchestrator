"""Transparent candidate detection. Thresholds are demo heuristics, not legal rules."""
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib

DEFAULT_CONFIG = {'structuring_min':Decimal('8000'), 'structuring_max':Decimal('10000'), 'structuring_count':3, 'structuring_hours':24, 'fan_out_min':4, 'fan_in_min':4, 'cycle_max_hops':4, 'max_graph_edges':15000}

def _case(typology, ids, accounts, details):
    ids = sorted(set(ids))
    key = typology + '|' + '|'.join(ids)
    return {'case_id': 'FG-' + hashlib.sha256(key.encode()).hexdigest()[:14], 'typology':typology, 'transaction_ids':ids, 'accounts':sorted(set(accounts)), 'details':details, 'status':'pending_review'}

def detect_candidates(transactions, config=None):
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    result = []
    by_sender = defaultdict(list)
    inbound, outbound = defaultdict(list), defaultdict(list)
    for tx in transactions:
        by_sender[(tx['source_account'],tx['payment_currency'])].append(tx)
        inbound[tx['destination_account']].append(tx)
        outbound[tx['source_account']].append(tx)
    # Sliding windows within each account/currency; never sum different currencies.
    for (account, currency), rows in by_sender.items():
        qualifying = sorted((t for t in rows if cfg['structuring_min'] <= Decimal(t['amount']) < cfg['structuring_max']), key=lambda t:t['timestamp'])
        left = 0
        for right, tx in enumerate(qualifying):
            while datetime.fromisoformat(tx['timestamp']) - datetime.fromisoformat(qualifying[left]['timestamp']) > timedelta(hours=cfg['structuring_hours']):
                left += 1
            window = qualifying[left:right+1]
            if len(window) == cfg['structuring_count']:
                result.append(_case('possible_structuring', [t['transaction_id'] for t in window], [account], {'count':len(window),'currency':currency,'total':str(sum((Decimal(t['amount']) for t in window),Decimal(0))),'rule':'Demo heuristic: repeated amounts in configured band; not a regulatory threshold'}))
    for account, rows in outbound.items():
        dests = {t['destination_account'] for t in rows}
        if len(dests) >= cfg['fan_out_min']:
            selected = rows[:100]
            result.append(_case('fan_out', [t['transaction_id'] for t in selected], [account,*dests], {'unique_recipients':len(dests),'sample_limited':len(rows)>100}))
    for account, rows in inbound.items():
        sources = {t['source_account'] for t in rows}
        if len(sources) >= cfg['fan_in_min']:
            selected = rows[:100]
            result.append(_case('fan_in', [t['transaction_id'] for t in selected], [account,*sources], {'unique_senders':len(sources),'sample_limited':len(rows)>100}))
    # Optional bounded graph analysis: only inspect small batches to avoid unbounded memory.
    if len(transactions) <= cfg['max_graph_edges']:
        try:
            import networkx as nx
            graph = nx.DiGraph()
            edge_tx = defaultdict(list)
            for tx in transactions:
                a,b = tx['source_account'],tx['destination_account']
                graph.add_edge(a,b)
                edge_tx[(a,b)].append(tx['transaction_id'])
            # Strongly connected components reduce unnecessary traversal.
            for comp in nx.strongly_connected_components(graph):
                if len(comp) < 2 or len(comp) > cfg['cycle_max_hops']:
                    continue
                sub = graph.subgraph(comp)
                for cycle in nx.simple_cycles(sub):
                    if 2 <= len(cycle) <= cfg['cycle_max_hops']:
                        edges = list(zip(cycle, cycle[1:]+cycle[:1]))
                        ids = [edge_tx[e][0] for e in edges]
                        result.append(_case('circular_flow',ids,cycle,{'hops':len(cycle),'note':'Directed cycle; chronology and amount continuity require analyst verification'}))
                        break
        except ImportError:
            pass
    return sorted({c['case_id']:c for c in result}.values(),key=lambda c:c['case_id'])
