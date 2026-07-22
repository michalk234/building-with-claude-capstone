**PROGRAM:** Building with Claude
**Case Study:** Retail Domain — Full Training Arc
**Date:** June 2026

---

# Case Study: Product Intelligence and Customer Service Platform — ShopMart Retail

*{Sections are indicative and subject to change}*

---

## Objective

ShopMart Retail is one of India's fastest-growing e-commerce platforms with over 2 million SKUs across electronics, apparel, home goods, and beauty. Two operational bottlenecks are costing the business ₹4 crore annually:

**Problem 1 — Product Catalogue Quality:** 600–800 new products are onboarded monthly from 150+ vendors who submit descriptions in inconsistent formats — some in paragraph form, some as spec sheets, some in regional languages. Each product must be normalised into ShopMart's catalogue schema before it can go live. Currently, 12 data-entry staff spend 3 days per week on this task, with a 9% error rate that requires rework.

**Problem 2 — Customer Product Queries:** ShopMart's support team handles 1,800 product-related queries per day — "Does this laptop have Thunderbolt?", "Is this saree machine washable?", "What is the warranty on this refrigerator?". Agents manually search the catalogue and vendor specs to answer each one, averaging 6 minutes per query with a 14% accuracy failure rate.

The technology team must build a **Claude-powered Product Intelligence Platform** that solves both problems:
- An automated product enrichment pipeline that processes raw vendor descriptions into validated catalogue records
- A customer-facing product Q&A assistant grounded in the enriched catalogue and vendor specification sheets

This case study applies every skill from the *Building with Claude* program across both sub-systems.

---

## Skills Applied Across the Training

| Day | Module | How it applies in this case study |
|-----|--------|----------------------------------|
| Day 1 | API Setup & Secure Integration | Secure client for both the enrichment pipeline and the Q&A assistant; cost tracking per product and per query |
| Day 1 | Prompt Engineering | Extraction prompt for enrichment; Q&A assistant system prompt with grounding constraints and tone rules for customer-facing responses |
| Day 2 | Structured Outputs | `ProductRecord` Pydantic schema; `messages.parse()` for enrichment; retry logic for malformed vendor input |
| Day 2 | Conversation & Context Management | Multi-turn customer Q&A session maintaining product context across follow-up questions |
| Day 3 | Tool Use | `check_inventory(sku)`, `get_price(sku)`, `fetch_vendor_spec(sku)` tools in the Q&A assistant |
| Day 3–4 | RAG | Index enriched product records + vendor spec PDFs; retrieve relevant product info per customer query |
| Day 4 | Evaluation | Evaluate enrichment accuracy (field correctness) and Q&A faithfulness to catalogue data; prompt versioning |

---

## Tasks to be Completed

### Phase 1 — Secure Foundation (Day 1 skills)

1. Initialise the shared Claude client securely. The platform has two entry points — the enrichment pipeline (batch, runs nightly) and the Q&A assistant (real-time, customer-facing). Both must use the same secure key-loading pattern. Implement a simple rate-aware wrapper that logs cost per product enriched and per Q&A response, so the finance team can track AI spend.

2. Write the **enrichment system prompt** that instructs Claude to:
   - Act as a product data specialist extracting catalogue fields
   - Infer `category` and `subcategory` from context if not stated
   - Normalise prices to INR float (handle "₹1,299", "Rs 1299", "INR 1,299.00" uniformly)
   - Return `null` for fields that genuinely cannot be inferred — never fabricate specifications
   - Output only valid JSON matching the schema

3. Write the **Q&A assistant system prompt** that:
   - Positions Claude as ShopMart's knowledgeable product advisor
   - Answers only from the retrieved catalogue data and vendor specs
   - Uses a warm, helpful tone appropriate for retail customers
   - Returns a defined fallback when a spec is not available: *"I don't have that specification on file — I recommend checking with the vendor or contacting our support team."*
   - Never makes up warranty periods, compatibility claims, or certification statuses

### Phase 2 — Structured Catalogue Enrichment (Day 2 skills)

4. Define the `ProductRecord` Pydantic model:

   ```python
   class ProductRecord(BaseModel):
       sku: str
       name: str
       brand: Optional[str]
       category: Literal["electronics","apparel","homeware","beauty","grocery","sports","other"]
       subcategory: str
       price_inr: float                           # must be > 0
       mrp_inr: Optional[float]                   # original price if discounted
       key_features: List[str]                    # 3–6 bullet points
       specifications: Dict[str, str]             # e.g. {"RAM": "16GB", "Storage": "512GB SSD"}
       in_stock: bool
       warranty_months: Optional[int]
       care_instructions: Optional[str]           # relevant for apparel/homeware
   ```

5. Use `client.messages.parse(output_format=ProductRecord)` as the primary extraction method. Implement a 2-retry loop on `ValidationError` — on each retry, include the validation error details in the re-prompt so Claude can self-correct.

6. Run the pipeline against all 15 vendor descriptions in the dataset. Track: success count, retry count per product, failed products (logged, not raised). Print a final summary table.

### Phase 3 — Multi-Turn Q&A Conversation (Day 2 skills)

7. Build a `ProductConversationManager` that holds the Q&A session context. A customer may ask 4–6 follow-up questions about the same product or switch to a different product mid-session. The manager must:
   - Maintain the full message history
   - Track which product(s) have been discussed (stored in session metadata)
   - Print a token count warning if the session exceeds 30,000 tokens
   - Apply summarise-and-reset if tokens exceed 60,000

### Phase 4 — Real-Time Tool Integration (Day 3 skills)

8. Define three tools for the Q&A assistant:

   | Tool | Input | Returns |
   |------|-------|---------|
   | `check_inventory` | `sku: str` | `{"available": bool, "quantity": int, "warehouse": str}` |
   | `get_current_price` | `sku: str` | `{"price_inr": float, "discount_pct": int, "offer_ends": str}` |
   | `fetch_vendor_spec` | `sku: str, spec_field: str` | `{"field": str, "value": str, "source": "vendor_sheet"}` |

9. Implement the manual agentic loop for the Q&A assistant. When a customer asks about live inventory or pricing (which changes daily), Claude should call `check_inventory` or `get_current_price` rather than relying on the catalogue record. When a spec is missing from the catalogue, Claude should call `fetch_vendor_spec`.

10. Test with the provided multi-turn customer conversation (dataset). Verify that tool calls are logged, live pricing is fetched correctly, and the out-of-stock scenario triggers the appropriate response.

### Phase 5 — RAG over Product Catalogue and Vendor Specs (Day 3–4 skills)

11. Build the product knowledge index:
    - Enrich all 15 products through the pipeline from Phase 2
    - Convert each `ProductRecord` to a text document and embed using Voyage AI (`voyage-3`)
    - Also embed the 3 vendor spec sheets from the dataset (PDF summaries as markdown)
    - Store in the `VectorStore`; attach metadata: `sku`, `category`, `brand`

12. Implement `retrieve_product_context(query, store, top_k=3)` that:
    - Embeds the customer's query
    - Retrieves the top-3 most relevant product/spec chunks
    - Filters by `category` metadata if the customer has already specified one (e.g. "I'm looking at laptops")

13. Before each Q&A response, inject the retrieved context into the user message as `[Product Context: SKU-XXX]` blocks. Use `"citations": {"enabled": true}` so Claude's answer includes source references the customer can verify.

### Phase 6 — Evaluation (Day 4 skills)

14. **Enrichment accuracy evaluation:** For 5 products in the golden set, compare the extracted `ProductRecord` against ground-truth values. Score field-level accuracy (correct fields / total fields). Flag any record where a specification was hallucinated (present in extracted record but absent from the raw description).

15. **Q&A faithfulness evaluation:** For 5 golden customer queries, score whether Claude's answer is grounded in the retrieved catalogue/spec data. Use `judge_faithfulness()`. Flag any answer that states a warranty period, compatibility claim, or certification not in the source.

16. Log all evaluation results to `eval_logs/product_platform_v1.jsonl`. Print separate scores for enrichment accuracy and Q&A faithfulness.

---

## Dataset Description

**Raw vendor descriptions:** `shared/data/retail_products.txt`
15 vendor product descriptions across electronics (5), apparel (4), homeware (3), beauty (2), sports (1). Challenges include: prices in words, missing brands, ambiguous categories, regional language product names, and 2 intentionally incomplete records.

**Vendor spec sheets (as markdown):** `shared/data/vendor_specs/`

| File | Product | Key specs |
|------|---------|----------|
| `dell_laptop_xps15_specs.md` | Dell XPS 15 (SKU-E001) | Processor, RAM, storage, display, ports, weight, warranty |
| `titan_analog_watch_specs.md` | Titan Kairos (SKU-A002) | Movement type, water resistance, strap material, case size |
| `prestige_cooker_specs.md` | Prestige Svachh 5L (SKU-H003) | Capacity, material, safety valve, ISI certification, warranty |

**Mock tool responses:**

| SKU | Inventory | Current Price | Live Discount |
|-----|-----------|--------------|--------------|
| SKU-E001 | 12 units, Whitefield WH | ₹1,24,990 | 8% off, ends Sunday |
| SKU-A002 | Out of stock | ₹3,495 | No offer |
| SKU-H003 | 47 units, Hosur Plant | ₹2,199 | No offer |

**Multi-turn customer conversation (test):** A 6-turn conversation about the Dell XPS 15 — asking about RAM upgradeability, Thunderbolt support, warranty in India, and whether it is in stock and at what price.

**Evaluation golden sets:**
- Enrichment: 5 products with ground-truth `ProductRecord` field values
- Q&A: 5 customer queries with expected source (catalogue vs. vendor spec vs. fallback)

---

## Expected Outcome

A working **Product Intelligence Platform** with two components demonstrating the full course skill set:

1. **Enrichment pipeline** (`case_studies/code/product_platform.py`):
   - Processes all 15 vendor descriptions; ≥ 13 successful records; 2 gracefully failed
   - `ProductRecord` schema with validators; `messages.parse()` used throughout
   - Retry loop demonstrated on at least one malformed description
   - Price normalisation handles all 3 currency formats in the dataset

2. **Q&A assistant** (same file, separate function):
   - Multi-turn session maintains full history; token warning fires correctly
   - `check_inventory` called when customer asks about stock; `get_current_price` called for pricing
   - Out-of-stock response (SKU-A002) generated without hallucinating availability
   - All answers cite product sources with `[Product Context: SKU-XXX]`

3. **Evaluation report:**
   ```
   ENRICHMENT ACCURACY (5 golden products)
   Field accuracy: 94%  |  Hallucinated specs: 0  |  PASS

   Q&A FAITHFULNESS (5 golden queries)
   Faithfulness avg: 4.8 / 5  |  Relevance avg: 4.6 / 5  |  PASS
   ```

4. **Demonstrated understanding** — participant can articulate:
   - Why `messages.parse()` is safer than `create()` + `json.loads()` for catalogue pipelines
   - How metadata filtering (by `category`) improves retrieval precision
   - Why live inventory/pricing is handled via tools rather than embedded in the RAG index
