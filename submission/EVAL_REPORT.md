# Evaluation report

## Setup

- **Provider and model:** OpenAI `gpt-4o-mini` through `LLM_PROVIDER=openai_compat`, for both the starter and my version (same model, so the comparison is fair). The starter was designed for `claude-opus-5-5`; I used gpt-4o-mini for budget reasons.
- **Runs:** 18–19 November 2026. Dev set: 24 labelled documents. Disputed set: 6 unlabelled documents.
- **Starter baseline:** the starter as shipped wrote **0/24** on gpt-4o-mini (it wraps its JSON in a code fence and `json.loads` failed every time; `submission/evidence/starter_dev_json_fail.log`). The baseline below is therefore *starter + one fix* (accept a fenced JSON reply), commit "Accept model JSON wrapped in a code fence". Nothing else was changed for the baseline.
- **Reproduce:**
  - predictions: `python -m ledgerline.cli predict --input ../data/invoices/dev --reference ../data/reference --output <out.jsonl> --db <run.db>` (from `backend/`)
  - routing vs labels: `python eval/compare_predictions.py <out.jsonl>`
  - cost, latency and field accuracy: the scripts recorded in `submission/evidence/cost_latency.txt` and `field_accuracy.txt`
- **Evidence files:** `submission/evidence/starter_*` (baseline) and `submission/evidence/mine_*` (my version, two runs).

## What the "94%" actually measured

`eval/run_eval.py` measures **field accuracy**: for 12 extracted fields, whether the value matches the label. It does **not** measure routing (whether a document that needed review was sent to review), which is what Meridian's risk depends on. It also has three problems:

1. **Leaked examples.** The prompt contained dev_001–dev_003 *with their labelled answers*, so the model was tested on documents it had been shown.
2. **Failed documents are dropped.** A document that crashes is skipped and removed from the denominator, so failures raise the score instead of lowering it.
3. **Empty equals empty.** A missing value matches a missing label, which pads the score.

Reproduced on gpt-4o-mini (starter + fence fix):

| Starter run | Score shown by `run_eval.py` | Skipped documents counted as failures |
|---|---|---|
| Eval run 1 | 242/264 = **91.7%** (dev_001, dev_007 skipped) | 242/288 = **84.0%** |
| Eval run 2 | 252/276 = **91.3%** (dev_016 skipped) | 252/288 = **87.5%** |

Re-scored from the starter's batch predictions with the same 12 fields and the same matching (`field_accuracy.txt`): **89.6%** on all 24, **89.7%** with the leaked dev_001–003 removed. On this model the leaked examples barely moved the number; the bigger inflation came from dropping failed documents.

**The headline:** the same starter run that scores about 90% field accuracy **routed 8 of the 13 documents that needed review as ready**. Field accuracy says almost nothing about whether Ledgerline is safe.

## What I chose to measure, and why

1. **Missed reviews** (needed review, routed ready). A missed review can mean paying a fraudster, paying twice or paying a credit note. This is the metric the AP Lead cares about ("I can't live with a missed one").
2. **Unnecessary reviews** (ready, routed to review). Each costs about ₹85 of AP time and can delay an MSME vendor's payment (the Finance Controller's concern).
3. **Missing documents** (no output line). The output contract says a document must never be skipped.
4. **Cost per document (₹)**, from real token counts at list price, against the CTO's ₹1.50 budget, plus whether the app's own recorded cost matches.
5. **Latency p50 and p95 per document** (total time of its LLM calls), against the CTO's 10 s p95 target.
6. **Field accuracy**, the starter's own metric, for continuity.
7. **Variation:** my version was run twice on the dev set.

## Starter versus mine, on the same model

| Metric | Starter (+ fence fix) | Mine, run 1 | Mine, run 2 |
|---|---|---|---|
| **Missed reviews** (of 13 that needed review) | **8** (dev_004, 005, 007, 011, 013, 018, 019, 024) | **0** | **0** |
| Unnecessary reviews (of 11 clean) | 3 (dev_002, 016, 023) | 0 | 1 (dev_022) |
| Missing documents | 0 on this run; 1–2 on other runs, 24 on the unfixed starter | 0 | 0 |
| Cost per document (₹, real) | 0.175 | 0.053 | 0.053 |
| Cost per document as recorded by the app (₹) | 0.0002 (about 1000× too low) | 0.053 (matches) | 0.053 (matches) |
| Input tokens per document | 10,000 | 1,739 | 1,738 |
| Latency p50 (s) | 10.7 | 7.5 | 7.8 |
| Latency p95 (s) | 14.0 | 10.0 | 10.7 |
| Field accuracy, 12 fields | 89.6% | 99.0% | 99.0% |

Value of the 8 documents the starter missed: **₹4,37,485** on a 24-document set.

Cost check for the CTO: his October bill of about $165 for 2,400 documents is about ₹6.05 per document on Opus at ₹88/$. The dashboard showed ₹15 in total because `pricing.py` stored per-thousand-token prices in a per-million table. With the units fixed, the app's recorded cost matches the real cost (table above). At 3,000 documents a month, my version on gpt-4o-mini costs about **₹160 a month** in LLM calls.

## Labels I disagree with

- **dev_015, `invoice_number`.** The label is `SIS/26-27/0018`, but the document prints `SIS / 26-27 / 0018`, and the output contract says `invoice_number` is "as printed". My version outputs it as printed, so it loses one field match on each run. If my reading is right, field accuracy is 286/288 = 99.3% on each run. Routing is unaffected: the duplicate check normalises both forms (policy §1), and dev_015 is flagged `duplicate` either way.

I agree with the routing labels on all 24 dev documents.

## Failure analysis

| What happened | Documents | Cause | Status |
|---|---|---|---|
| Starter routed 8 problem documents as ready | dev_004, 005, 007, 011, 013, 018, 019, 024 | **Rules:** routing came from the model's answer; code checks were only warnings; prompt asked for `requires_review` while the examples used `needs_review` | Fixed (F1): code decides routing |
| Starter skipped documents | all 24 (first run), disp_06, dev_001, 007, 016 | **Model** returned fenced or broken JSON; **code** skipped instead of flagging | Fixed: fence accepted, failures become `processing_error` |
| Model flagged `suspicious_content` on clean documents | dev_001, 011, 017, 020, 023 (one run) | **Model** | Fixed: the model's flag is a warning only; code patterns catch HTML and AI-addressed text (dev_012, dev_013) |
| Invoice number corrupted to `CN-XXXXX4417` | dev_014 | **Code:** account masking treated a hyphenated invoice number as an account | Fixed, with a test |
| Invented bank account `****1234` | dev_014 | **Model** (the document has no bank details) | Fixed: an account not found in the document is dropped |
| One digit misread in a line amount (73,837.50 → 73,437.50) | dev_022, run 2 | **Model** extraction | Caught by the totals check; failed safe (extra review, not a missed one) |

## How much to trust these numbers

- **Small sample.** 24 dev documents, 13 needing review, two runs. Zero missed reviews in 26 chances is encouraging but not proof: by the "rule of three", the true miss rate could still be up to about 3/26 ≈ 11% at 95% confidence.
- **Not Meridian's mix.** The dev set is deliberately rich in problem cases (54% need review, against 13% in production). Rates per document will differ in production.
- **Run-to-run variation is real.** The model's output changes between runs (dev_022 in run 2; different documents skipped by the starter on different runs). Results here are from two runs only.
- **One model.** Everything is on gpt-4o-mini. I did not measure Opus or another provider.
- **Latency** is LLM time only, measured sequentially from one machine; end-to-end time includes a little more.
- **Not covered by the dev set:** real OCR noise at scale, long multi-page invoices, provider outages, and documents from vendors outside the reference data.

## My recommendation

**Yes, with conditions.** Put every invoice through Ledgerline next month, with every invoice still approved by a person (policy §4.3: there is no automatic approval), under these conditions:

1. **Two weeks of shadow running first.** Ledgerline routes in parallel while the AP team works as today, and every disagreement is checked. Go live only if there are **no missed reviews** in that period.
2. **No straight-through processing** for invoices under ₹10,000 yet (the CFO's request): the policy does not allow it, and 26 dev chances are not enough evidence.
3. **Latency:** p95 is at the CTO's 10 s limit. Removing or making conditional the second "verification" LLM call would roughly halve latency and cost. Test it before rollout.
4. **The DPO signs off** on what is now sent to OpenAI: the document text with bank account numbers masked to the last 4 digits, and nothing else.

**How it weighs the two errors**, at Meridian's production mix (3,000 documents a month, 13% needing review):
- Unnecessary reviews: 1 in 22 clean documents across my two runs (about 4.5%) means about 120 a month, about **₹10,000 a month** of AP time. The starter's 3 in 11 (about 27%) would be about 700 a month, about ₹60,000.
- Missed reviews: the starter missed 8 of 13. At production volume that is about 240 problem invoices a month going to approval unchecked. The 8 it missed on the dev set were worth ₹4,37,485, and one fraudulent bank-change email already cost Meridian ₹3.8 lakh. One missed fraud costs more than a year of extra reviews.

**What would change my mind:** any missed review during the shadow period; an unnecessary-review rate above about 10% (the Finance Controller's late-payment risk); or p95 latency above 10 s that the verification-call change does not fix.