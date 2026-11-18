# FinGuard Orchestrator — Phase 2 class-project prototype

FinGuard is a synthetic-data AML screening and investigation demonstrator. It is **not** a production compliance tool, legal advice, or an application for filing an official Suspicious Activity Report (SAR).

## What is included

- CSV ingestion and normalization for the supplied SAML-D-style data.
- Heuristic candidate detection for patterns such as fan-in, fan-out, possible structuring, and bounded transaction cycles.
- A four-node LangGraph workflow: detection, regulatory retrieval, assessment, and evidence validation (with a sequential fallback if LangGraph is unavailable).
- Optional OpenAI-generated case assessments. If the API key or regulatory passages are unavailable, the system uses a deterministic fallback.
- Regulatory reference retrieval from the project's curated reference records. Lexical retrieval is available offline; optional ChromaDB retrieval can be enabled in Colab.
- SQLite persistence, analyst review status, and DOCX/PDF training-draft exports for approved cases.
- A Streamlit interface and command-line batch runner.
- Automated tests and a development evaluation script.

## Quick start (Windows PowerShell / macOS / Linux)

1. Extract this ZIP and open the `FinGuard_Project` folder in a terminal or VS Code.
2. Install Python 3.11 or 3.12.
3. Create and activate a virtual environment:
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Run tests: `python -m pytest -q`
6. Process a sample batch: `python cli.py --limit 2000`
7. Launch the interface: `python -m streamlit run app.py`

The Colab notebook is the recommended route for the supplied Phase 2 demonstration. It installs dependencies, mounts Drive, loads the project ZIP, runs tests, configures optional OpenAI/ChromaDB services, processes a batch, displays candidate cases, evaluates the labeled development sample, and provides a manual analyst-review/report-export gate.

## Colab workflow

Run the notebook sections in order. Section 8 defaults to `APPROVE_FOR_TRAINING = False`; leave it false for normal processing. For a class demonstration only, inspect a candidate in Section 6, explicitly enable the manual approval gate for that case, run Section 8 once, and then return the flag to false. Approval is a training demonstration, not a real AML determination or SAR filing.

OpenAI assessments are only used when an API key is configured and regulatory passages are available. The project uses a deterministic fallback otherwise. OpenAI API usage may incur charges. ChromaDB retrieval is optional; lexical retrieval is the offline fallback.

## Evaluation results and limitations

The supplied Colab development evaluation produced:

- Evaluated transactions: 1,000
- Candidate cases: 78
- Validation errors: 0
- True positives: 510
- False positives: 0
- False negatives: 490
- True negatives: 0
- Precision: 1.00
- Recall: 0.51
- F1: approximately 0.6755
- False-positive rate: unavailable because the evaluated sample contained no true negatives.

These are development metrics for the supplied labeled sample, **not certification or evidence of production screening performance**. The sample is not representative; transaction-level labels are used while case-level labels are unavailable, and heuristic candidate expansion/sampling can distort the metrics. Ground-truth labels are excluded from detection and AI prompts. A more defensible evaluation requires a representative, leakage-safe holdout containing both positive and negative examples, plus case-level adjudication.

## Important prototype limitations

- Detection rules and thresholds are illustrative candidate generators, not validated AML classifiers or regulatory reporting thresholds.
- Regulatory entries are project-authored summaries with official-source URLs. They are not verified quotations or a complete, jurisdiction-specific legal corpus.
- ChromaDB provides optional retrieval over the included reference records; it does not make the reference corpus authoritative or complete.
- The system requires analyst review. An AI-generated risk level is not proof of wrongdoing.
- SQLite is a demonstration database; production authentication, role-based access, audit hardening, encryption, privacy controls, and operational monitoring are not implemented.
- The current prototype uses Python function calls and a Streamlit UI; proposed REST/API deployment is not implemented.
- Reports are training/investigation drafts, not official SAR forms.

## Project structure

```text
FinGuard_Project/
  app.py                         Streamlit analyst UI
  cli.py                         command-line batch runner
  requirements.txt               dependencies
  src/finguard/
    ingestion.py                 CSV loading and normalization
    detection.py                 heuristic candidate detection
    regulations.py               lexical/optional ChromaDB retrieval
    assessment.py                optional OpenAI assessment and validation
    workflow.py                  four-node LangGraph orchestration
    storage.py                   SQLite cases, transactions, and reviews
    reports.py                   approved-case DOCX/PDF draft exports
    service.py                   end-to-end batch processing
    evaluation.py                development screening metrics
  tests/                         automated tests
  data/                          sample data and reference records
  docs/                          design and implementation documents
```
