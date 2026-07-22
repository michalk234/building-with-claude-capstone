**PROGRAM:** Building with Claude
**Case Study:** Finance Domain — Full Training Arc
**Date:** June 2026

---

# Case Study: Intelligent Loan Origination Assistant — Apex Bank

*{Sections are indicative and subject to change}*

---

## Objective

Apex Bank processes 3,500 retail loan applications monthly across home loans, personal loans, and business loans. The current process is heavily manual: a loan officer collects customer details over a 20–30 minute call, cross-checks eligibility against the credit policy, validates documents, queries the credit bureau, and then drafts a preliminary assessment — all before the file reaches the credit committee. Errors at this stage cause an average rework rate of 22%, delaying disbursements and increasing customer drop-off.

The bank's digital transformation team has mandated building a **Claude-powered Loan Origination Assistant** that automates the front-end of this workflow. The assistant must:

- Conduct a structured, multi-turn intake conversation with the applicant or loan officer
- Validate inputs against Apex Bank's credit policy at each step
- Call internal systems (credit bureau, document checker, existing account lookup) via tool use
- Produce a fully validated, schema-compliant preliminary assessment record
- Ground all policy decisions in the official credit policy SOP — never inventing eligibility rules
- Be evaluable for faithfulness and compliance before going live in any branch

This case study spans the full five days of the *Building with Claude* program. Each module's skills are applied as one cohesive, production-realistic application.

---

## Skills Applied Across the Training

| Day | Module | How it applies in this case study |
|-----|--------|----------------------------------|
| Day 1 | API Setup & Secure Integration | Initialise the client securely; handle auth errors, rate limits, and cost tracking for a high-volume banking application |
| Day 1 | Prompt Engineering | Design the loan officer system prompt: role, policy constraints, question sequence, language register, fallback for out-of-policy requests |
| Day 2 | Structured Outputs | Define `LoanApplicationRecord` Pydantic schema; extract and validate all application fields from the conversation; retry on validation failure |
| Day 2 | Conversation & Context Management | Maintain the multi-turn intake conversation across 8–12 turns; manage token growth; summarise and reset when context approaches limits |
| Day 3 | Tool Use | Integrate three internal tools: `check_credit_score`, `validate_documents`, `lookup_existing_account`; implement the manual agentic loop |
| Day 3–4 | RAG | Index the 60-page Apex Bank Credit Policy SOP; retrieve relevant policy sections per loan type; ground all eligibility decisions in retrieved text |
| Day 4 | Evaluation | Score the assistant's assessments for faithfulness to policy, relevance to the applicant's situation, and tool call correctness; version the system prompt |

---

## Tasks to be Completed

### Phase 1 — Secure Foundation (Day 1 skills)

1. Initialise the `anthropic.Anthropic()` client using `ANTHROPIC_API_KEY` from the environment. Add a pre-flight check that fails with a descriptive error if the key is absent. Never hardcode the key.

2. Instrument the client to count tokens before each API call and log the `_request_id` from every response. Estimated cost per application intake should be printed at the end of each run.

3. Write the **loan officer system prompt** that:
   - Establishes the assistant as an Apex Bank intake agent
   - Sequences questions in the correct order: applicant type → income → loan amount requested → property (for home loans) → existing liabilities
   - Enforces plain English and no financial jargon
   - Refuses to state an eligibility decision before all required information is collected
   - Cites `[Policy Section X.Y]` whenever stating an eligibility rule

### Phase 2 — Structured Intake and Validation (Day 2 skills)

4. Define the `LoanApplicationRecord` Pydantic model:

   ```python
   class LoanApplicationRecord(BaseModel):
       applicant_name: str
       applicant_type: Literal["salaried", "self_employed", "government"]
       annual_income_inr: float
       loan_type: Literal["home", "personal", "business", "vehicle"]
       loan_amount_requested_inr: float
       existing_emi_inr: float
       dti_ratio: float                    # computed: (existing_emi + new_emi_estimate) / monthly_income
       credit_score: Optional[int]         # populated after tool call
       documents_verified: bool            # populated after tool call
       preliminary_decision: Literal["proceed", "refer_to_committee", "decline"]
       policy_basis: str                   # the policy section(s) driving the decision
   ```

5. Use `client.messages.parse(output_format=LoanApplicationRecord)` to extract the completed record after the intake conversation ends. Implement a retry loop (max 2) that re-prompts Claude with the `ValidationError` details if parsing fails.

6. Build a `ConversationManager` that maintains full message history across the intake turns. After turn 6 (midpoint), print the running token count. If it exceeds 40,000 tokens, apply the summarise-and-reset pattern before continuing.

### Phase 3 — Tool Integration (Day 3 skills)

7. Define three tools:

   | Tool | Input | Returns |
   |------|-------|---------|
   | `check_credit_score` | `pan_number: str` | `{"score": int, "risk_band": "low/medium/high"}` |
   | `validate_documents` | `doc_type: str, doc_id: str` | `{"valid": bool, "expiry_date": str, "reason": str}` |
   | `lookup_existing_account` | `customer_id: str` | `{"active_loans": int, "existing_emi_total": float, "dpd": int}` |

8. Implement the manual agentic loop. Claude will call these tools after gathering applicant information to enrich the record before producing the `preliminary_decision`. Print each tool call with its inputs before executing.

9. Handle errors gracefully: if `check_credit_score` returns an error (bureau unavailable), Claude should note this in `policy_basis` and set `preliminary_decision` to `"refer_to_committee"` rather than declining.

### Phase 4 — RAG Policy Grounding (Day 3–4 skills)

10. Index the Apex Bank Credit Policy SOP (`shared/data/finance_sop/loan_processing_sop.md`) using section-aware chunking. Attach metadata: `loan_type`, `section_title`, `policy_version`.

11. At the start of each intake, retrieve the top-3 policy chunks relevant to the applicant's declared loan type. Inject them into the system prompt as `[Policy Context]`. Use `cache_control` on the stable policy context to reduce cost on repeated calls.

12. Verify grounding: the `policy_basis` field of the `LoanApplicationRecord` must contain actual section references traceable to the retrieved chunks. Claude must not invent policy thresholds.

### Phase 5 — Evaluation (Day 4 skills)

13. Build an evaluation run over 4 test application scenarios (provided in dataset). For each scenario:
    - Score `faithfulness`: is the `preliminary_decision` and `policy_basis` supported by retrieved policy?
    - Score `tool_correctness`: did Claude call the right tools with accurate inputs extracted from the conversation?
    - Log results to `eval_logs/loan_assistant_v1.jsonl` with `request_id`, scores, and timestamp.

14. Run a **regression test**: modify the system prompt to remove the `[Policy Section X.Y]` citation instruction. Re-run evaluation and show that faithfulness scores drop. Restore and document the change.

---

## Dataset Description

**Policy document:** `shared/data/finance_sop/loan_processing_sop.md`
A 6-section synthetic Apex Bank SOP covering: eligibility criteria by applicant type, DTI thresholds, documentation requirements, credit bureau integration, committee review triggers, and disbursement timelines.

**Mock tool responses** (hardcoded in the script for lab purposes):

| Customer ID | Credit Score | Active Loans | Existing EMI | DPD |
|-------------|-------------|-------------|-------------|-----|
| CUST-001 | 762 (low risk) | 1 | ₹8,500 | 0 |
| CUST-002 | 541 (high risk) | 3 | ₹32,000 | 15 |
| CUST-003 | 680 (medium) | 0 | ₹0 | 0 |
| CUST-004 | N/A (bureau down) | 1 | ₹5,000 | 0 |

**Four test application scenarios:**

| # | Applicant | Loan Type | Amount | Expected Decision |
|---|-----------|-----------|--------|------------------|
| 1 | Salaried, income ₹9L, CUST-001 | Home loan ₹45L | Low DTI, good score | `proceed` |
| 2 | Self-employed, income ₹6L, CUST-002 | Personal ₹5L | High DTI, missed payments | `decline` |
| 3 | Salaried, income ₹12L, CUST-003 | Business ₹80L | Amount > threshold | `refer_to_committee` |
| 4 | Government employee, CUST-004 | Home loan ₹30L | Bureau unavailable | `refer_to_committee` |

**Evaluation golden set:** 4 entries with ground-truth `preliminary_decision` and the expected policy sections that must appear in `policy_basis`.

---

## Expected Outcome

A production-realistic **Intelligent Loan Origination Assistant** at `case_studies/code/loan_origination_assistant.py` that demonstrates:

1. **Security** — API key loaded from environment; `_request_id` logged; token cost printed per run

2. **Reliable prompting** — System prompt with role, citation rule, question sequence, and fallback. Tested against all 4 scenarios including the adversarial "give me a decision now" scenario

3. **Validated structured output** — All 4 applications produce valid `LoanApplicationRecord` instances with correct types; retry loop handles at least one synthetic validation failure

4. **Conversation integrity** — Full history maintained across 8–10 turns; token count printed; summarise-and-reset demonstrated on the longest test scenario

5. **Tool use** — All three tools called correctly; bureau-error case handled gracefully; tool call log printed

6. **Policy grounding** — `policy_basis` contains real section references from retrieved SOP chunks; no invented thresholds

7. **Evaluation report:**
   ```
   Scenario 1: faithfulness=5, tool_correctness=1.0 → PASS
   Scenario 2: faithfulness=5, tool_correctness=1.0 → PASS
   Scenario 3: faithfulness=4, tool_correctness=1.0 → PASS
   Scenario 4: faithfulness=5, tool_correctness=1.0 → PASS  (bureau error handled)
   Overall: 4/4 PASS
   ```

8. **Regression demo** — Faithfulness drops to ≤3 on at least one scenario when citation instruction is removed; restored and documented
