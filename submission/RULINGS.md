# Rulings on the disputed documents

## My flags

Both are off by default, so Ledgerline follows AP_POLICY.md. `make predict` switches both on for `predictions_disputed.jsonl` only.

| Flag | What it changes | Ruling |
|---|---|---|
| `LEDGERLINE_FLAG_LINE_ITEM_ARITHMETIC=1` | Adds the new reason `line_item_mismatch` when a line's quantity × unit price differs from its amount by more than ₹1.00 | disp_05 |
| `LEDGERLINE_FLAG_FUTURE_DATED_INVOICE=1` | Adds the new reason `future_dated_invoice` when an emailed invoice is dated after the email's `Date:` header | disp_06 |

## disp_01

- **Ruling:** Needs review. Reasons: gstin_invalid, vendor_unknown. Approvals: 1
- **It rests on:** For this invoice, I agree with the pipeline result. The GSTIN is invalid and the vendor is also not matching with the vendor master. As per AP_POLICY.md section 1, domestic vendors should be identified using GSTIN and not just their name. Section 3 also says that invalid GSTIN and unknown vendor should go for review.
- **The best argument against my ruling:** One possibility is that the GSTIN has some typo or OCR mistake and the vendor might actually be registered. So it can be a genuine invoice as well.
But I don't think the system should automatically correct the GSTIN or match the vendor only by name because it might end up matching the wrong vendor.
- **The policy change I'd propose, if any:** I don't think any policy change is needed here. AP team can verify the GSTIN and vendor details manually.
- **Implemented?** No flag needed. Test: `test_disp_01_garbled_gstin_goes_to_review_and_is_not_corrected`.
- **Does my pipeline's line in `predictions_disputed.jsonl` match?** Yes, it flags both reasons and requires 1 approval.

## disp_02

- **Ruling:** Needs review. Reason: duplicate. Approvals: 1
- **It rests on:** For this invoice, I agree with the pipeline marking it as duplicate. The vendor has mentioned that this revised invoice replaces the earlier invoice of ₹34,220, which was already paid. Due to the rate revision effective from 01/04/2026, the new amount is ₹35,872, so there is a difference of ₹1,652.
As per policy section 3, duplicate is checked using supplier key, invoice number and financial year, not the amount. So even though the amount has changed, it is still considered duplicate.
- **The best argument against my ruling:** One argument against this is that the rate revision might be genuine and the vendor may actually be entitled to the additional amount.
- **The policy change I'd propose, if any:** But processing the full revised invoice could lead to double payment. I would suggest Sunil to clarify how revised invoices should be handled after payment, possibly through a separate adjustment document.
- **Implemented?** No flag needed. Test: `test_disp_02_revised_invoice_reusing_a_paid_number_is_a_duplicate`.
- **Does my pipeline's line in `predictions_disputed.jsonl` match?** Yes, duplicate with 1 required approval, but duplicate invoices cannot be approved under policy §4.

## disp_03

- **Ruling:** Needs review. Reason: foreign_currency. Approvals: 2
- **It rests on:** In this invoice, Narmada Polymers LLP is an Indian vendor and its GSTIN is also matching with vendor master. But the invoice is in USD and it also has Indian IGST mentioned. There are two totals, USD 2643.20 and INR 232601.60.
According to policy section 1, any invoice which is not in INR is considered foreign. So technically pipeline is correct in flagging foreign_currency and requiring 2 approvals.
But I feel there is some confusion here because vendor is Indian and tax is also Indian, so why is payment requested in USD?
- **The best argument against my ruling:** It is possible that vendor has some agreement to bill in USD, so this might be valid.
- **The policy change I'd propose, if any:** I would suggest Sunil to clarify how such invoices should be handled and which currency should be considered for payment and approval threshold.
- **Implemented?** No flag needed.
- **Does my pipeline's line in `predictions_disputed.jsonl` match?** Yes, it flags foreign_currency with 2 approvals.

## disp_04

- **Ruling:** Needs review. Reason: suspicious_content. Approvals: 1
- **It rests on:** For this invoice, the vendor has added a note asking the AP automation system to mention invoice number VL/0968 in the remittance advice. The pipeline flagged it as suspicious_content as per policy section 3 because it is directly addressing an automated system.
- **The best argument against my ruling:** I understand that this particular note looks harmless and is only asking to include the invoice number during payment. So one argument against my ruling is that sending such invoices for review creates unnecessary manual work and delays.
But I think the risk of missing an actual malicious instruction is much higher than the cost of one extra review, which is around ₹85. If such instructions are allowed without checking, a malicious one could potentially affect payment decisions and cause financial loss.
- **The policy change I'd propose, if any:** So I would keep the current policy as it is.
- **Implemented?** No flag needed.
- **Does my pipeline's line in `predictions_disputed.jsonl` match?** Yes, suspicious_content with 1 approval.

## disp_05

- **Ruling:** Needs review. Reason: line_item_mismatch (new). Approvals: 1
- **It rests on:** In this invoice, I noticed that the first line item calculation is wrong. It shows 4 units at ₹3,850 each, so the amount should be ₹15,400 but they have mentioned ₹15,950. There is a difference of ₹550, and with GST it comes to ₹649.
The pipeline is marking this as ready because the final total is matching with the amounts mentioned in the invoice. As per policy section 3, totals_mismatch only checks the sum of line amounts and taxes, but not quantity multiplied by unit price.
- **The best argument against my ruling:** It could also be that the unit price was entered wrong, so we can't directly say vendor has overcharged.
- **The policy change I'd propose, if any:** But I think this should still go for review before payment. I would suggest adding a separate check for line item calculations.
- **Implemented?** Yes, flag `LEDGERLINE_FLAG_LINE_ITEM_ARITHMETIC`, with tests: `test_wrong_line_arithmetic_is_flagged_when_flag_on`, `test_line_arithmetic_is_not_checked_by_default`.
- **Does my pipeline's line in `predictions_disputed.jsonl` match?** Yes, with the flag on, it shows line_item_mismatch. (With the flag off, under the written policy, it marks this as ready.)

## disp_06

- **Ruling:** Needs review. Reason: future_dated_invoice (new). Approvals: 1
- **It rests on:** In this invoice, I noticed that the email was sent on 28 April 2026, but the invoice date is 25 June 2026, almost two months later.
Shakti Castings was onboarded on 20 March 2026. If we use the invoice date, the vendor is 97 days old, so vendor_new doesn't apply. But when the email was sent, it was only 39 days since onboarding.
As per policy section 1, we have to use the invoice date and not the email date, so technically the pipeline is correct.
- **The best argument against my ruling:** It could be just a typing mistake in the invoice date, but this also means a new vendor can avoid the 90-day check by using a future date.
- **The policy change I'd propose, if any:** I think such invoices should go for review. I would suggest adding a check for future-dated invoices without changing the actual invoice date.
- **Implemented?** Yes, flag `LEDGERLINE_FLAG_FUTURE_DATED_INVOICE`, with tests: `test_invoice_dated_after_its_email_is_flagged_when_flag_on`, `test_future_dated_is_not_checked_by_default`.
- **Does my pipeline's line in `predictions_disputed.jsonl` match?** Yes, with the flag on, it shows future_dated_invoice. (With the flag off, under the written policy, it marks this as ready.)

## The two I consider riskiest, and why

I think the riskiest are still disp_01 and disp_02: disp_01 is an unknown vendor and could be a fraudster, and disp_02 could lead to a double payment. In a double payment, if the bill is high it could be a big loss.