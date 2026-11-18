# FinGuard Phase 2 bulk upgrade

Adds a curated regulatory reference set (project-authored summaries with official-source links), optional ChromaDB retrieval, four-node LangGraph orchestration, and transaction-level evaluation. **The source URLs are references, not automatically downloaded or verified full regulatory texts.** Lexical retrieval works without embeddings. Chroma embeddings may download a model on first use. OpenAI assessments require a Colab secret and are only applied to newly processed batches; reprocessing the same batch ID reuses stored results. This is a class prototype, not a production compliance system.

To activate OpenAI in Colab, store OPENAI_API_KEY in Colab Secrets, set ENABLE_OPENAI=True before processing a *new* batch, and understand API charges may apply. To activate Chroma set FINGUARD_RETRIEVAL_MODE=chroma; lexical mode is the offline default.

Run tests with `python -m pytest -q tests`; metrics from `evaluate_transactions` are screening-level, not legal or SAR filing validation.
