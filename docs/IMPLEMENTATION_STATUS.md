# Implementation status — FinGuard Phase 2

This status reflects the Phase 2 source package and Colab workflow. FinGuard remains a class-project prototype, not a production AML compliance system.

| Area | State | Notes |
|---|---|---|
| SAML-D ingestion | Implemented | CSV loading, normalization, and label isolation |
| AML heuristics | Implemented prototype | Candidate patterns include repeated payments, fan-in/out, and bounded directed cycles |
| LangGraph orchestration | Implemented | Four nodes: detect, retrieve, assess, validate; sequential fallback when LangGraph is unavailable |
| SQLite persistence | Implemented | Batches, transactions, cases, and analyst review records |
| Streamlit UI | Implemented | Upload, case listing, evidence review, decisions, and export |
| OpenAI assessment | Optional | Requires API key and retrieved passages; deterministic fallback otherwise |
| Regulatory retrieval | Implemented prototype | Curated project summaries; lexical mode and optional ChromaDB retrieval; sources require independent verification |
| Evidence validation | Implemented baseline | Checks transaction IDs and regulatory citation IDs against available evidence |
| DOCX/PDF reports | Implemented | Approved-case training drafts with assessment, risk level, transaction evidence, references, limitations, and review details |
| Evaluation | Partial/development only | Supplied 1,000-row run: 78 candidate cases, 510 TP, 0 FP, 490 FN, 0 TN; precision 1.00, recall 0.51, F1 ~0.6755; FPR unavailable because TN=0 |
| Authentication/security/production deployment | Not implemented | No production identity, RBAC, hardened audit controls, or production deployment |
| REST API | Not implemented | Current interface uses Python calls, CLI, and Streamlit; API design is future-facing |

## Requirements-to-code mapping

- CSV validation and normalization: `src/finguard/ingestion.py`
- Candidate AML patterns: `src/finguard/detection.py`
- Workflow orchestration: `src/finguard/workflow.py`
- Regulatory reference retrieval: `src/finguard/regulations.py`
- AI assessment and evidence validation: `src/finguard/assessment.py`
- Database and human review: `src/finguard/storage.py`
- DOCX/PDF exports: `src/finguard/reports.py`
- Evaluation metrics: `src/finguard/evaluation.py`
- User interface: `app.py`
- End-to-end processing: `src/finguard/service.py`

## Evaluation caveats

The supplied labeled sample is not representative and contains no true negatives in the reported run. Transaction-level labels are used, while case-level labels are unavailable. Sampling and heuristic candidate expansion can distort metrics. These results are development diagnostics, not certification or evidence of production screening performance. A representative leakage-safe holdout with both positive and negative examples and case-level adjudication is still required.

## Regulatory and compliance caveats

The included regulatory records are project-authored summaries linked to official sources; they are not verbatim legal text and have not been independently verified for applicability. AI assessments are explanatory aids only. All cases require qualified human review. Generated reports are training drafts, not official SAR filings.
