# Decisions

## Architecture

Model only extracts, code decides. I moved the review decisions back to validation.py as originally planned in ARCHITECTURE.md. The model only extracts invoice details. Its review suggestions are saved as warnings but don't affect the final decision. During testing, I noticed the model was sometimes flagging clean invoices and even marking known vendors as unknown, so I felt code-based validation was more reliable.

Prompt and output. I kept the prompt focused on extraction. If extraction fails or fields are missing, the document goes to review with processing_error instead of being skipped.

Suspicious documents. I treat invoice text as untrusted input. Even if a document contains instructions for the AI, those instructions cannot change the review decision. Suspicious text is checked in code. (using regex)

Data privacy. Before sending documents to the LLM, bank account numbers are masked except for the last four digits. I also removed vendor master and payment history from the prompt. The original account number is used locally for validation.

Approvals. I added server-side(db) checks so the same person cannot approve twice, duplicates and credit notes cannot be approved, and repeated clicks don't create multiple payment instructions. Approval and rejection attempts are also recorded in the audit log.

## Part 4: what I went deep on, and why

I did not get time to work on Part 4. If I had to choose, I would choose option A (evidence-linked review), because reviewers who can't trace numbers re-key every invoice, while cost is already far under the CTO's budget.

## Replies to stakeholders

### Anita Rao, CFO
I understand the need to reduce manual work, especially for invoices under ₹10,000. But according to the current AP policy, every invoice needs at least one human approval, so I wouldn't enable automatic approval without Sunil updating the policy first.

For GSTIN errors, I also wouldn't let AI automatically correct them. Even a small OCR mistake can lead to matching the wrong vendor. My approach is to validate the GSTIN using the checksum and send invalid ones for review.

I think we can still reduce manual effort by improving extraction accuracy & showing reviewers the source of each field. Once these checks are reliable, we can discuss automatic approval for low risk invoices.

### Farhan Sheikh, Head of AP
I agree that reviewers should be able to see where the extracted values came from. Otherwise they will keep checking the original invoice manually, which defeats the purpose of automation. I haven't completed field-level evidence linking yet, but that would be my next priority.

For bank-detail changes, my pipeline compares the invoice details with the vendor master and flags any mismatch. I also agree with your call-back suggestion, especially considering the previous ₹3.8 lakh fraud loss. But we first need verified vendor contact numbers and a way to record the verification.

I have also added server-side approval checks to prevent duplicate payment instructions when someone clicks Approve multiple times.

### Deepak Menon, CTO
I noticed the difference between the dashboard cost and the actual Anthropic bill. The dashboard was not giving a reliable picture of LLM spending, so I would use actual token usage and model pricing to calculate cost rather than trusting the old figures.

I switched to gpt-4o-mini and my measured cost is around ₹0.053 per document, which is well below the ₹1.50 target. I would still check p95 latency before saying the system is ready for rollout.

Regarding fine-tuning, I wouldn't prioritize it right now. Most of the problems I found were related to validation, approvals and missing checks rather than just extraction accuracy. I would fix these first and only consider fine-tuning if we have enough evidence that it would improve results.

### Priya Natarajan, Data Protection Officer
I agree that vendor bank account numbers should not be sent to external LLM providers.

In my version, I mask bank account numbers before sending the document to the model, keeping only the last four digits. I also removed the vendor master and paid invoice history from the prompt because the model doesn't need that information for extraction.

The original account number stays within Meridian's system and is used locally to compare against the vendor master.

I would also recommend testing the masking logic on different invoice formats before rollout, because bank account numbers may appear with spaces or unusual formatting. We should verify the actual outbound requests rather than relying only on the prompt.

### Sunil Joshi, Finance Controller
I understand that sending too many invoices for review can delay payments, especially for MSME vendors. So I wouldn't suggest sending every invoice for review just to be safe.

My approach is to keep the existing policy checks and add new ones only where I found actual gaps.

I kept both changes behind flags that are off by default, so the current policy behavior is not changed without approval.

For bank detail changes, I would propose a verified call-back process, but we would need a reliable contact number in the vendor master first.

### Ravi Kulkarni, contractor
I understand why you kept the policy rules in the prompt, since it makes policy updates easier without changing code. But during testing, I noticed that the model was sometimes giving incorrect review reasons, including flagging clean documents and marking a known vendor as unknown.

That's why I moved the final review decisions back to deterministic code. The model now focuses on extracting information, while validation.py applies the policy rules. This also makes the decisions easier to test and debug.

I agree that maintaining rules in code takes more effort when policies change. To make this easier, I would keep the rules modular and add tests for each policy change.

I also kept the model's suggestions as warnings so they can still be reviewed without affecting the final routing decision.

## Policy changes I propose

These are suggestions for Sunil to review. I haven't changed AP_POLICY.md directly.

1. Line-item calculation (disp_05): Add a check for quantity × unit price against line amount, allowing ₹1 tolerance.

2. Future-dated invoices (disp_06): Flag emailed invoices when the invoice date is later than the email date. Otherwise, a recently onboarded vendor could avoid the 90-day check.

3. Revised invoices (disp_02): Vendors should use a separate adjustment document with a new number when revising an already paid invoice. This avoids confusion with duplicates.

4. Foreign currency (disp_03): Clarify how Indian vendors billing in USD should be handled, GSTIN validation, payment currency and which amount is used for the ₹5 lakh approval threshold.

5. Bank-detail changes: I would suggest requiring a verified call-back before approving changed bank details. This could help prevent fraud, but we first need verified vendor contact numbers in the master data.