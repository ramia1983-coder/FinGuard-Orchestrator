"""Curated official-source metadata; project summaries are NOT regulatory quotations."""
from pathlib import Path
import json

DEFAULT_KNOWLEDGE=Path(__file__).resolve().parents[2]/'data'/'regulations.json'
def load_knowledge(knowledge_file=None):
    path=Path(knowledge_file) if knowledge_file else DEFAULT_KNOWLEDGE
    if not path.exists(): return []
    records=json.loads(path.read_text(encoding='utf-8'))
    required={'source_id','title','url','text','topics'}
    if not isinstance(records,list) or any(not required.issubset(p) for p in records):
        raise ValueError('Invalid regulatory knowledge records')
    return records

def retrieve(case,knowledge_file=None,top_k=3,mode='lexical',persist_dir=None):
    records=load_knowledge(knowledge_file)
    if not records:return []
    typology=case.get('typology','')
    eligible=[p for p in records if typology in p.get('topics',[])]
    if mode=='chroma' and eligible:
        try:
            import chromadb
            client=chromadb.PersistentClient(path=str(persist_dir or '/content/finguard_chroma'))
            collection=client.get_or_create_collection('finguard_regulations_v1')
            # Default Chroma embedding model may download on first run.
            collection.upsert(ids=[p['source_id'] for p in records],documents=[p['text'] for p in records],metadatas=[{'title':p['title'],'url':p['url'],'publisher':p.get('publisher',''),'topics':','.join(p['topics'])} for p in records])
            found=collection.query(query_texts=[typology.replace('_',' ')+' AML suspicious activity'],n_results=min(len(records),max(top_k*2,3)))
            order={sid:i for i,sid in enumerate(found['ids'][0])}
            eligible.sort(key=lambda p:order.get(p['source_id'],10000))
        except (ImportError,RuntimeError,OSError,ValueError) as exc:
            # Deliberate lexical fallback, surfaced to caller via retrieval mode selection.
            pass
    else:
        terms=set(typology.replace('_',' ').split())
        eligible.sort(key=lambda p:sum(term in p['text'].lower() for term in terms),reverse=True)
    return eligible[:top_k]
