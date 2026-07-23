"""
Intelligent Loan Origination Assistant — Apex Bank
====================================================
Build this file in 5 phases, one day's skills at a time.

Phase 1  (Day 1)  — Secure client · system prompt · basic API call
Phase 2  (Day 2)  — Pydantic schema · parse() with retry · ConversationManager
Phase 3  (Day 3)  — Tool definitions · manual agentic loop
Phase 4  (Day 3-4)— RAG indexing · policy retrieval · prompt caching
Phase 5  (Day 4)  — LLM-as-judge evaluation · regression test

Run:
    python loan_origination_assistant.py
"""

# ── Imports (provided) ─────────────────────────────────────────────────────────
import json
import os
import re
import datetime
from pathlib import Path
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator

import anthropic

# ── Constants (provided) ───────────────────────────────────────────────────────
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
TOKEN_COMPACT_THRESHOLD = 40_000
MAX_PARSE_RETRIES = 2
TOP_K_CHUNKS = 3
EVAL_LOG_PATH = Path("eval_logs/loan_assistant_v1.jsonl")


# ── Mock data (provided — do not modify) ──────────────────────────────────────

CUSTOMER_DB = {
    "CUST-001": {"credit_score": 762, "risk_band": "low",
                 "active_loans": 1, "existing_emi_total": 8_500, "dpd": 0},
    "CUST-002": {"credit_score": 541, "risk_band": "high",
                 "active_loans": 3, "existing_emi_total": 32_000, "dpd": 15},
    "CUST-003": {"credit_score": 680, "risk_band": "medium",
                 "active_loans": 0, "existing_emi_total": 0, "dpd": 0},
    "CUST-004": {"credit_score": None, "risk_band": None,  # bureau unavailable
                 "active_loans": 1, "existing_emi_total": 5_000, "dpd": 0},
}

DOCUMENTS_DB = {
    ("aadhaar", "AADHAAR-1234"): {"valid": True,  "expiry_date": "N/A",    "reason": "Valid Aadhaar"},
    ("pan",     "PAN-ABCDE1234F"): {"valid": True, "expiry_date": "N/A",    "reason": "Valid PAN"},
    ("salary_slip", "SAL-MAY26"): {"valid": True,  "expiry_date": "2026-08-31", "reason": "Current pay slip"},
    ("aadhaar", "AADHAAR-EXPIRED"): {"valid": False, "expiry_date": "2024-01-01", "reason": "Expired document"},
}

TEST_SCENARIOS = [
    {
        "id": "S1",
        "description": "Salaried applicant, good profile → expect: proceed",
        "conversation": [
            "Hi, I'd like to apply for a home loan.",
            "My name is Rahul Verma. I'm a salaried employee.",
            "My annual income is 9 lakhs. I need 45 lakhs for 20 years.",
            "The property is at 12 MG Road, Bengaluru.",
            "My PAN is PAN-ABCDE1234F and Aadhaar is AADHAAR-1234. Customer ID: CUST-001.",
            "No other EMIs at the moment.",
        ],
        "expected_decision": "proceed",
        "expected_policy_sections": ["Section 2.1", "Section 3.1"],
    },
    {
        "id": "S2",
        "description": "Self-employed, high DTI, missed payments → expect: decline",
        "conversation": [
            "I want a personal loan of 5 lakhs.",
            "Name is Sunita Rao, self-employed consultant.",
            "Annual income around 6 lakhs. Customer ID CUST-002.",
            "Aadhaar: AADHAAR-1234, PAN: PAN-ABCDE1234F.",
        ],
        "expected_decision": "decline",
        "expected_policy_sections": ["Section 2.3", "Section 4.2"],
    },
    {
        "id": "S3",
        "description": "Large business loan exceeds single-officer limit → expect: refer_to_committee",
        "conversation": [
            "I need a business loan for my company.",
            "Arun Mehta, salaried director. Annual income 12 lakhs.",
            "Loan amount: 80 lakhs. Customer ID CUST-003.",
            "PAN: PAN-ABCDE1234F, Aadhaar: AADHAAR-1234.",
        ],
        "expected_decision": "refer_to_committee",
        "expected_policy_sections": ["Section 5.1"],
    },
    {
        "id": "S4",
        "description": "Bureau unavailable — cannot confirm score → expect: refer_to_committee",
        "conversation": [
            "Home loan application. I'm Priya Nair, government employee.",
            "Annual income 8 lakhs. Loan amount 30 lakhs.",
            "Customer ID: CUST-004. Aadhaar: AADHAAR-1234, PAN: PAN-ABCDE1234F.",
        ],
        "expected_decision": "refer_to_committee",
        "expected_policy_sections": ["Section 4.1"],
    },
]

EVAL_GOLDEN_SET = [
    {"scenario_id": "S1", "ground_truth_decision": "proceed",
     "required_sections": ["Section 2.1", "Section 3.1"]},
    {"scenario_id": "S2", "ground_truth_decision": "decline",
     "required_sections": ["Section 2.3", "Section 4.2"]},
    {"scenario_id": "S3", "ground_truth_decision": "refer_to_committee",
     "required_sections": ["Section 5.1"]},
    {"scenario_id": "S4", "ground_truth_decision": "refer_to_committee",
     "required_sections": ["Section 4.1"]},
]


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Secure Foundation (Day 1 skills)
# ═══════════════════════════════════════════════════════════════════════════════

def make_client() -> anthropic.Anthropic:
    """Initialise the Anthropic client from the environment.

    TODO:
    - Call load_dotenv() to pick up .env
    - Read ANTHROPIC_API_KEY with os.environ.get()
    - Raise EnvironmentError with a descriptive message if it is absent
    - Return anthropic.Anthropic() — no api_key= argument; SDK reads env automatically
    """
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return anthropic.Anthropic()


# Write your system prompt here.
# The string {policy_context} will be filled in dynamically in Phase 4.
# Leave it as a literal placeholder for now; in Phase 1 you can remove it
# and inject raw policy text later.


LOAN_OFFICER_SYSTEM = """You are an Apex Bank loan intake officer.
    Ask one plain-English question at a time, without jargon. Collect in order:
    applicant type, annual income, loan type, requested amount, property details
    (home loans only), customer ID, documents, existing EMIs.
    Do not give a preliminary decision until all applicable data is collected.
    Cite [Policy Section X.Y] for every eligibility rule. Never invent rules.

    Policy:
    {policy_context}"""


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for a single API call (Sonnet 4.6 pricing).

    TODO:
    - Input rate:  $3.00 per 1M tokens
    - Output rate: $15.00 per 1M tokens
    - Return the sum
    """
    input_cost = input_tokens * 3.00 / 1_000_000
    output_cost = output_tokens * 15.00 / 1_000_000
    return input_cost + output_cost


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Structured Intake and Validation (Day 2 skills)
# ═══════════════════════════════════════════════════════════════════════════════

class LoanApplicationRecord(BaseModel):
    """Validated record produced at the end of an intake conversation.

    All fields are extracted by Claude from the conversation history and
    enriched by tool calls (Phase 3).

    TODO (Phase 2):
    - Replace each `Any` placeholder below with the correct type
      (str, float, Literal, Optional, bool) — `Any` is just a Pydantic-safe
      stand-in so this class can be imported before Phase 2 is implemented
    - Add a @field_validator for dti_ratio checking it is a positive number
    - Remember: in Pydantic v2, @classmethod must appear ABOVE @field_validator
    """

    applicant_name:             str
    applicant_type:             Literal["salaried", "self_employed", "government"]
    annual_income_inr:          float
    loan_type:                  Literal["home", "personal", "business", "vehicle"]
    loan_amount_requested_inr:  float
    existing_emi_inr:           float
    dti_ratio:                  float  # computed: (existing_emi + new_emi_est) / (annual_income/12)
    credit_score:               Optional[int]  # None when bureau is unavailable
    documents_verified:         bool
    preliminary_decision:       Literal["proceed", "refer_to_committee", "decline"]
    policy_basis:               str  # must contain actual [Policy Section X.Y] references

    @field_validator("dti_ratio")
    @classmethod
    def validate_dti_ratio(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("dti_ratio must be positive")
        return value


class ConversationManager:
    """Maintains full message history for a multi-turn intake session.

    TODO (Phase 2):
    - __init__(self, client, system): store client and system; initialise self.messages = []
    - send(self, user_message) -> str:
        * append {"role": "user", "content": user_message}
        * call client.messages.create(model, max_tokens, system, messages)
        * append {"role": "assistant", "content": reply}   ← full list, not just .text
        * return the text reply
    - token_count(self) -> int:
        * use client.messages.count_tokens(model, system, messages)
        * return result.input_tokens
    - summarise_and_reset(self) -> str:
        * build a history_text string from self.messages
        * ask Claude to summarise in ≤150 words preserving all collected fields
        * reset self.messages to [{"role":"user","content":"[Summary]\n{summary}"}]
        * return the summary string
    """

    def __init__(self, client: anthropic.Anthropic, system: str) -> None:
        self.client = client
        self.system = system
        self.messages: list[dict] = []


    def send(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=self.system,
            messages=self.messages,
        )
        reply = "".join(block.text for block in response.content if block.type == "text")
        self.messages.append({"role": "assistant", "content": response.content})  # append full list, not just .text
        return reply

    def token_count(self) -> int:
        count = self.client.messages.count_tokens(
            model=MODEL,
            system=self.system,
            messages=self.messages,
        )
        return count.input_tokens
    
    def summarise_and_reset(self) -> str:
        history_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.messages
        )
        summary_prompt = (
            "Please summarise the following conversation in 150 words or less, "
            "preserving all collected fields:\n\n" + history_text
        )
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=self.system,
            messages=[{"role": "user", "content": summary_prompt}],
        )
        summary = "".join(block.text for block in response.content if block.type == "text")
        self.messages = [{"role": "user", "content": f"[Summary]\n{summary}"}]
        return summary

def extract_application_record(
    client: anthropic.Anthropic,
    conversation_history: list[dict],
    policy_context: str = "",
) -> LoanApplicationRecord:
    """Extract and validate a LoanApplicationRecord from the completed conversation.

    Uses client.messages.parse() and retries on ValidationError.

    TODO (Phase 2):
    - Build a messages list: the full conversation_history + a final user prompt
      asking Claude to extract all fields as the JSON defined by LoanApplicationRecord
    - Call client.messages.parse(model, max_tokens, messages, output_format=LoanApplicationRecord)
    - Return response.parsed_output on success
    - On ValidationError: append the assistant response and error details, then retry
    - After MAX_PARSE_RETRIES attempts, re-raise the last ValidationError

    Hint: reference day2/loan_application_extractor.py for the retry loop pattern
    """
    messages = list(conversation_history)
    messages.append({
        "role": "user",
        "content": (
            "Extract all collected loan application information into a "
            "LoanApplicationRecord. Return values matching the schema exactly.\n\n"
            "Calculate dti_ratio as:\n"
            "(existing_emi_inr + estimated new monthly EMI) / monthly income.\n\n"
            #"Use only policy sections supported by the conversation and policy "
            #"context. Do not invent policy references.\n\n"
            f"Policy context:\n{policy_context or 'No policy context provided.'}"
        ),
    })

    for attempt in range(MAX_PARSE_RETRIES + 1):
        try:
            response = client.messages.parse(
                model=MODEL,
                max_tokens=1024,
                temperature=0,
                messages=messages,
                output_format=LoanApplicationRecord,
            )
            return response.parsed_output

        except ValidationError as error:
            if attempt == MAX_PARSE_RETRIES:
                raise

            messages.append({
                "role": "user",
                "content": (
                    "Your previous output failed schema validation:\n"
                    f"{error}\n\n"
                    "Correct the invalid fields and return a JSON object "
                    "matching LoanApplicationRecord exactly."
                ),
            })


def run_intake_conversation(
    client: anthropic.Anthropic,
    turns: list[str],
    policy_context: str = "",
) -> tuple[list[dict], float]:
    """Drive the intake conversation and return (message_history, total_cost_usd).

    TODO (Phase 2):
    - Instantiate ConversationManager with the formatted LOAN_OFFICER_SYSTEM
    - Iterate over turns; call manager.send(turn) for each
    - Print the officer reply after each turn
    - After turn 6 (index 5): call manager.token_count()
      * Print the token count
      * If it exceeds TOKEN_COMPACT_THRESHOLD: call manager.summarise_and_reset() and print summary
    - Accumulate cost using estimate_cost() on each response's usage (you'll need to track tokens
      separately — or do a single count_tokens() call at the end as an approximation)
    - Return (manager.messages, total_cost)
    """
    system_prompt = LOAN_OFFICER_SYSTEM.format(
        policy_context=policy_context or "No policy context provided."
    )
    manager = ConversationManager(client, system_prompt)

    compacted_input_tokens = 0

    for turn_index, turn in enumerate(turns):
        reply = manager.send(turn)
        print(f"\n  Loan officer: {reply}")

        if turn_index == 5:
            running_tokens = manager.token_count()
            print(f"\n  Running token count: {running_tokens:,}")

            if running_tokens > TOKEN_COMPACT_THRESHOLD:
                compacted_input_tokens += running_tokens
                summary = manager.summarise_and_reset()
                print(f"\n  Conversation summary:\n{summary}")

    final_input_tokens = manager.token_count()
    approximate_input_tokens = compacted_input_tokens + final_input_tokens
    total_cost = estimate_cost(approximate_input_tokens, 0)

    return manager.messages, total_cost

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Tool Integration (Day 3 skills)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Mock tool implementations (provided — matches the mock DB above) ───────────

def _check_credit_score(pan_number: str) -> dict:
    """Look up a CIBIL score by PAN. Returns None score when bureau is down."""
    # Map PAN → customer for demo; in production this hits the bureau API
    pan_to_customer = {"PAN-ABCDE1234F": "CUST-001"}  # extended in real data
    customer_id = pan_to_customer.get(pan_number)
    if not customer_id:
        return {"error": f"PAN {pan_number} not found in bureau records."}
    c = CUSTOMER_DB[customer_id]
    if c["credit_score"] is None:
        return {"error": "Credit bureau temporarily unavailable. Retry later."}
    return {"score": c["credit_score"], "risk_band": c["risk_band"]}


def _validate_documents(doc_type: str, doc_id: str) -> dict:
    """Validate a document against the documents database."""
    result = DOCUMENTS_DB.get((doc_type.lower(), doc_id))
    if not result:
        return {"valid": False, "expiry_date": "N/A", "reason": f"Document {doc_id} not found."}
    return result


def _lookup_existing_account(customer_id: str) -> dict:
    """Fetch active loan count, existing EMI, and DPD for a customer."""
    c = CUSTOMER_DB.get(customer_id)
    if not c:
        return {"error": f"Customer {customer_id} not found."}
    return {
        "active_loans":        c["active_loans"],
        "existing_emi_total":  c["existing_emi_total"],
        "dpd":                 c["dpd"],
    }


TOOL_FN_MAP = {
    "check_credit_score":     _check_credit_score,
    "validate_documents":     _validate_documents,
    "lookup_existing_account": _lookup_existing_account,
}


def build_tools() -> list[dict]:
    """Return the list of tool definitions passed to client.messages.create().

    TODO (Phase 3):
    Define three tools as dicts with "name", "description", and "input_schema".

    Tool 1 — check_credit_score
      input:  pan_number (string) — applicant's PAN card number
      output: {"score": int, "risk_band": "low|medium|high"} or {"error": str}

    Tool 2 — validate_documents
      input:  doc_type (string) — e.g. "aadhaar", "pan", "salary_slip"
              doc_id   (string) — the document ID or number
      output: {"valid": bool, "expiry_date": str, "reason": str}

    Tool 3 — lookup_existing_account
      input:  customer_id (string) — Apex Bank customer ID, e.g. CUST-001
      output: {"active_loans": int, "existing_emi_total": float, "dpd": int}

    Remember:
    - Each input_schema needs "type": "object", "properties": {...}, "required": [...],
      "additionalProperties": False
    - Descriptions matter — Claude reads them to decide when and how to call the tool
    """
    raise NotImplementedError("Phase 3 ▸ implement build_tools()")


def run_agentic_loop(
    client: anthropic.Anthropic,
    conversation_history: list[dict],
    tools: list[dict],
) -> list[dict]:
    """Run the manual agentic loop: Claude calls tools, you execute them, loop until end_turn.

    Takes the completed conversation_history from Phase 2 as the starting messages.
    Returns the updated messages list with all tool interactions appended.

    TODO (Phase 3):
    - Start with messages = conversation_history (make a copy to be safe)
    - Add a final user turn: "Please look up the customer's credit score, validate
      their documents, and check their existing account before making your assessment."
    - while True:
        * call client.messages.create(model, max_tokens, tools=tools, messages=messages)
        * if response.stop_reason == "end_turn": break
        * append {"role": "assistant", "content": response.content}   ← full list
        * for each tool_use block in response.content:
            - print the tool name and input
            - look up the function in TOOL_FN_MAP
            - call it with **block.input
            - set is_error = "error" in result
            - append tool_result to tool_results list
        * append {"role": "user", "content": tool_results}
    - Return the final messages list

    Key mistakes to avoid:
    - Break on "end_turn", NOT on "tool_use"
    - Append response.content (the list), NOT response.content[0].text
    - Tool result content must be json.dumps(result) — a string, not a dict
    """
    raise NotImplementedError("Phase 3 ▸ implement run_agentic_loop()")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — RAG Policy Grounding (Day 3–4 skills)
# ═══════════════════════════════════════════════════════════════════════════════

def build_policy_index(policy_path: str = "data/loan_processing_sop.md") -> object:
    """Chunk and embed the Apex Bank Credit Policy SOP into a Chroma collection.

    TODO (Phase 4):
    - import chromadb and openai lazily inside this function (so the file runs
      without those keys/packages configured when only Phase 1-3 is used)
    - Read the file at policy_path
    - Split into chunks of ~400 words with 50-word overlap
    - For each chunk, attach metadata: section_title, chunk_index
    - Start a Chroma client: chromadb.PersistentClient(path="./chroma_data")
      (or EphemeralClient() during development) and get_or_create_collection(...)
    - Embed all chunks using openai.OpenAI().embeddings.create(
          input=[c.text for c in chunks], model="text-embedding-3-small"
      )
    - collection.add(ids=[...], embeddings=[...], documents=[c.text for c in chunks],
      metadatas=[{"section_title":.., "chunk_index":..}, ...])
    - Return the populated collection

    Hint: the lazy imports mean the file still runs without an OpenAI key
    when only Phase 1–3 features are exercised.
    """
    raise NotImplementedError("Phase 4 ▸ implement build_policy_index()")


def retrieve_policy_context(query: str, store: object, top_k: int = TOP_K_CHUNKS) -> str:
    """Retrieve the top-k policy chunks most relevant to the query.

    TODO (Phase 4):
    - Embed the query using the same model as build_policy_index()
    - Call store.query(query_embeddings=[query_embedding], n_results=top_k)
    - Format the returned chunks as:
        [Policy Section <section_title>, chunk <chunk_index>]
        <chunk text>
      joined by double newlines
    - Return the formatted string

    This string replaces {policy_context} in LOAN_OFFICER_SYSTEM and is also
    passed to extract_application_record() so the extraction prompt sees policy text.
    """
    raise NotImplementedError("Phase 4 ▸ implement retrieve_policy_context()")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — Evaluation (Day 4 skills)
# ═══════════════════════════════════════════════════════════════════════════════

FAITHFULNESS_JUDGE_SYSTEM = """
TODO (Phase 5): Write the faithfulness judge system prompt.

It should instruct Claude to:
- Score 1–5 how well the preliminary_decision and policy_basis are supported
  by the provided policy context (1 = hallucinated, 5 = fully grounded)
- Return JSON: {"score": <int>, "reasoning": "<str>"}
- Not penalise for style, only for unsupported factual claims
"""


def judge_faithfulness(
    client: anthropic.Anthropic,
    policy_context: str,
    record: LoanApplicationRecord,
) -> dict:
    """Score a LoanApplicationRecord for faithfulness to the retrieved policy.

    TODO (Phase 5):
    - Build a user prompt combining policy_context and the record's
      preliminary_decision + policy_basis
    - Call client.messages.create() with FAITHFULNESS_JUDGE_SYSTEM
    - Strip markdown fences from the response text before json.loads()
      Hint: re.search(r"```(?:json)?\\s*(\\{[\\s\\S]*?\\})\\s*```", text)
    - Return the parsed dict {"score": int, "reasoning": str}
    - On any parse error, return {"score": 0, "reasoning": "parse error: <raw text>"}
    """
    raise NotImplementedError("Phase 5 ▸ implement judge_faithfulness()")


def evaluate_tool_correctness(
    expected_tools: list[str],
    messages: list[dict],
) -> float:
    """Check what fraction of expected tool calls actually appeared in the loop.

    TODO (Phase 5):
    - Walk messages looking for tool_use blocks (blocks with type == "tool_use")
    - Collect the set of tool names that were called
    - Return len(called & set(expected_tools)) / len(expected_tools)
      (proportion of expected tools that were actually called)
    """
    raise NotImplementedError("Phase 5 ▸ implement evaluate_tool_correctness()")


def log_eval_result(record: dict) -> None:
    """Append one evaluation result as a JSON line to EVAL_LOG_PATH.

    TODO (Phase 5):
    - Add "timestamp": datetime.datetime.utcnow().isoformat() to the record
    - EVAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    - Open EVAL_LOG_PATH in append mode and write json.dumps(record) + "\\n"
    """
    raise NotImplementedError("Phase 5 ▸ implement log_eval_result()")


def run_evaluation(
    client: anthropic.Anthropic,
    store: object,
    tools: list[dict],
) -> None:
    """Run all four test scenarios through the assistant and score the outputs.

    TODO (Phase 5):
    - Iterate over TEST_SCENARIOS and EVAL_GOLDEN_SET in parallel (zip)
    - For each scenario:
        1. policy_context = retrieve_policy_context(scenario["description"], store)
        2. history, cost = run_intake_conversation(client, scenario["conversation"], policy_context)
        3. messages = run_agentic_loop(client, history, tools)
        4. record = extract_application_record(client, messages, policy_context)
        5. faith = judge_faithfulness(client, policy_context, record)
        6. tool_score = evaluate_tool_correctness(
               ["check_credit_score", "validate_documents", "lookup_existing_account"],
               messages
           )
        7. decision_correct = record.preliminary_decision == golden["ground_truth_decision"]
        8. log_eval_result({...})
        9. Print a one-line summary

    - Print "Overall: N/4 PASS" at the end
    """
    raise NotImplementedError("Phase 5 ▸ implement run_evaluation()")


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION — wire all phases together
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    # ── Phase 1: Initialise ────────────────────────────────────────────────────
    client = make_client()
    #tools = build_tools()         # to be uncommented after developing ph3 # Phase 3 — safe to call empty list until then
    tools: list[dict] = []  # to be removed after developing ph3 # 

    # ── Phase 4: Build policy index ───────────────────────────────────────────
    # Comment this block out until Phase 4 is implemented:
    # store = build_policy_index()

    # For Phase 1–3, use an empty policy context:
    store = None
    policy_context = ""

    # ── Run one scenario end-to-end ────────────────────────────────────────────
    scenario = TEST_SCENARIOS[0]
    print(f"\n{'='*60}")
    print(f"Running: {scenario['description']}")
    print("=" * 60)

    # Phase 4: replace with retrieve_policy_context(scenario["description"], store)
    if store is not None:
        policy_context = retrieve_policy_context(scenario["description"], store)

    # Phase 2: drive the intake conversation
    history, cost = run_intake_conversation(client, scenario["conversation"], policy_context)
    print(f"\n  Estimated cost: ${cost:.4f}")

    # Phase 3: enrich with tool calls
    #messages = run_agentic_loop(client, history, tools)  # to be uncommented after developing ph3 
    messages = list(history)  # to be removed after developing ph3
    
    # Phase 2: extract the validated record
    record = extract_application_record(client, messages, policy_context)
    print(f"\n  Decision : {record.preliminary_decision}")
    print(f"  Policy   : {record.policy_basis}")
    print(f"  DTI      : {record.dti_ratio:.1%}")

    # ── Phase 5: Run full evaluation ──────────────────────────────────────────
    # Uncomment when Phase 5 is ready:
    # run_evaluation(client, store, tools)


if __name__ == "__main__":
    main()
