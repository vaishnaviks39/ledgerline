# My first hour

_Under about 300 words, in your own words. Commit it on its own, before any commit that touches `backend/` or `frontend/`, and don't edit it afterwards. Save the AI sessions from this stretch in `ai-logs/` with a name starting `00_first_hour`. Being wrong here is fine._

## What I think is going on
I think the main issue is that the system depends too much on LLM for making important decisions and routing instead of following fixed business rules from the policy. Earlier code controlled the routing part, but in version 0.3, that responsibility also moved to the LLM(replaced with warnings only). This could explain why some invoices are being wrongly approved, payments are duplicated and costs are mismatched. Evaluation part is also measuring wrong things(incorrect choice of metrics).


## The risks I suspect, most serious first

Incorrect invoice routing (most serious): LLM might make wrong decisions or follow instructions hidden in invoice. (Missed review - invoice asking LLM to skip the review)
Duplicate Payments: Since approval process is not idempotent it may cause two payments for 2 approval clicks.
Weak Duplicate Check: Similar invoices or bank accounts might not be checked properly it may lead to loss of extra money
Vendor Identity issue: matching only with name without GSTIN could lead to payments to wrong vendor
Incorrect Eval: We are not measuring routing accuracy anywhere in eval set, it is testing fields only.
Data Privacy: bank details are being shared with LLM provider.


## My plan for the time I have

First, I would reproduce existing issues on dev env and save the results as proof. Then I would make routing deterministic using fixed rules from policy instead of LLM routing. Then I would fix duplicate payment/approval issues. Need to improve evaluation to check if correct approvals and reviews happen. I would check disputed documents, verification of vendor details and data that is being sent to LLM. I would test everything and prioritise payment safety and routing correctness over everything.


## What I would ask Meridian

If a vendor sends a corrected invoice with the same invoice number after we've already paid, how do we pay the remaining amount?

Should an invoice with future date be payable? Because policy does not have any rule about this and due to this new vendors can silently bypass 90 day check mentioned in policy.
