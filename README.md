# Building with Claude — Capstone

A project built during the *Building with Claude* programme. Two case-study
stubs are provided — **fork and implement whichever one matches your track**
(or both):

| File | Case study | Spec |
|------|-----------|------|
| `loan_origination_assistant.py` | Finance — Apex Bank loan intake | `CS_Finance_Loan_Origination_Assistant.md` |
| `product_platform.py` | Retail — ShopMart product intelligence | `CS_Retail_Product_Intelligence_Platform.md` |

Both files ship fully stubbed with `NotImplementedError` markers — implement
them in phases, one day's skills at a time, following the TODO docstrings.

## Folder structure

```
building-with-claude-capstone/
├── loan_origination_assistant.py   ← Finance case study (implement this)
├── product_platform.py             ← Retail case study (implement this)
├── data/
│   ├── apex_bank_credit_policy.md  ← Finance: credit policy reference
│   ├── loan_processing_sop.md      ← Finance: SOP for RAG (Phase 4)
│   ├── retail_products.txt         ← Retail: 15 raw vendor descriptions (Phase 2)
│   └── vendor_specs/               ← Retail: 3 vendor spec sheets (Phase 5 RAG)
├── eval_logs/                      ← evaluation output (gitignored)
├── pyproject.toml / uv.lock        ← uv-managed project + locked dependencies
├── .env.example                    ← copy to .env and fill in keys
├── requirements.txt                ← same deps, for non-uv/pip workflows
└── GIT_WORKFLOW.md                 ← step-by-step GitHub guide
```

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# 1. Clone your repo (see GIT_WORKFLOW.md for how to create it)
git clone https://github.com/<your-username>/building-with-claude-capstone.git
cd building-with-claude-capstone

# 2. Install dependencies (creates .venv automatically, pinned to Python 3.12)
uv sync

# 3. Set up API keys
cp .env.example .env
# Open .env and fill in ANTHROPIC_API_KEY, OPENAI_API_KEY (Finance Phase 4
# embeddings) and/or VOYAGE_API_KEY (Retail Phase 5 embeddings)

# 4. Verify syntax compiles
uv run python -m py_compile loan_origination_assistant.py product_platform.py && echo "OK"
```

Prefer plain pip/venv instead? `requirements.txt` is kept in sync with
`pyproject.toml` — `pip install -r requirements.txt` works the same way.

Both stubs use [ChromaDB](https://docs.trychroma.com/) as the vector store
for their RAG phase (Finance Phase 4 / Retail Phase 5) — no external vector
DB service needed, it runs embedded/local (`chromadb.PersistentClient` or
`EphemeralClient`).

## Running

```bash
uv run python loan_origination_assistant.py     # Finance
uv run python product_platform.py               # Retail
```

Each `NotImplementedError` tells you which phase to implement next.

## Implementation phases — Finance (`loan_origination_assistant.py`)

| Phase | Day | What you build |
|-------|-----|----------------|
| 1 | Day 1 | `make_client()`, `LOAN_OFFICER_SYSTEM`, `estimate_cost()` |
| 2 | Day 2 | `LoanApplicationRecord`, `ConversationManager`, `extract_application_record()`, `run_intake_conversation()` |
| 3 | Day 3 | `build_tools()`, `run_agentic_loop()` |
| 4 | Day 3–4 | `build_policy_index()`, `retrieve_policy_context()` (ChromaDB + OpenAI embeddings) |
| 5 | Day 4 | `judge_faithfulness()`, `evaluate_tool_correctness()`, `run_evaluation()` |

### Expected final output (all phases complete)

```
Scenario S1: faithfulness=5, tool_correctness=1.0, decision=✓ → PASS
Scenario S2: faithfulness=5, tool_correctness=1.0, decision=✓ → PASS
Scenario S3: faithfulness=4, tool_correctness=1.0, decision=✓ → PASS
Scenario S4: faithfulness=5, tool_correctness=1.0, decision=✓ → PASS
Overall: 4/4 PASS
```

## Implementation phases — Retail (`product_platform.py`)

| Phase | Day | What you build |
|-------|-----|----------------|
| 1 | Day 1 | `make_client()`, `ENRICHMENT_SYSTEM`, `QA_SYSTEM` |
| 2 | Day 2 | `ProductRecord`, `extract_product_record()`, `run_enrichment_pipeline()` |
| 3 | Day 2 | `ProductConversationManager` |
| 4 | Day 3 | `build_qa_tools()`, `run_qa_agentic_loop()` |
| 5 | Day 3–4 | `build_product_index()`, `retrieve_product_context()` (ChromaDB + Voyage embeddings) |
| 6 | Day 4 | `judge_faithfulness()`, `evaluate_enrichment_accuracy()`, `run_evaluation()` |

### Expected final output (all phases complete)

```
ENRICHMENT ACCURACY (5 golden products)
Field accuracy: 94%  |  Hallucinated specs: 0  |  PASS

Q&A FAITHFULNESS (5 golden queries)
Faithfulness avg: 4.8 / 5  |  Relevance avg: 4.6 / 5  |  PASS
```
