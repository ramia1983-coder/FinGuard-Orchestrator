# FinGuard — UI quick start

FinGuard Phase 1 is the **design** (PRD, HLD, LLD, evaluation plan). Phase 2 is the **implementation** of the same system. They are not separate products.

## Start the application on your computer

1. Unzip `FinGuard_Phase2_UI_Ready.zip` and open the `FinGuard_Project` folder.
2. Install Python 3.11 or 3.12 if it is not already installed.
3. Open Terminal (macOS) or PowerShell (Windows) **in the `FinGuard_Project` folder**.
4. Run `python3 -m pip install -r requirements.txt` on macOS, or `py -m pip install -r requirements.txt` on Windows.
5. Run `python3 -m streamlit run app.py` on macOS, or `py -m streamlit run app.py` on Windows.
6. The app opens in your browser, usually at `http://localhost:8501`.
7. Choose **Use included sample**, set the limit to **150**, and click **Process transactions**.
8. Open **Investigation Queue** to inspect flagged cases. Use **Analyst decision** to approve a demonstration case; only approved cases offer report downloads.

The UI runs on **your computer**, not automatically in Google Colab. Do not upload the ZIP to a public Streamlit hosting service without reviewing data handling and access controls. The prototype is not production secure.

## Optional OpenAI assessments

Without an API key, FinGuard uses an offline deterministic assessment. For AI-assisted assessments, set the `OPENAI_API_KEY` environment variable **before** starting Streamlit. API usage may incur charges. Optional Chroma retrieval can be configured through `FINGUARD_RETRIEVAL_MODE=chroma` (first use may download embeddings).

## Data and files

The included sample is synthetic. Your own CSV must follow the supplied SAML-D-style columns expected by the ingestion code. The local SQLite database is stored in `runtime/finguard.db`. Avoid placing real customer financial information in this educational prototype.

## Limitations

The app has no login, role-based access control, or production-grade security. Risk scores and regulatory summaries are not validated legal or compliance decisions. Reports are training investigation drafts, **not** filed SARs.
