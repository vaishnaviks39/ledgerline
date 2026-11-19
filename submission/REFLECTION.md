# Reflection


## Three things I didn't know when I started, and how I learned each one

1. It's better to use LLMs for extraction and deterministic code for routing. I learned that relying on LLMs for review decisions can be risky, especially in financial systems. 
2. Using AI tools - I learned how to use AI tools while working on a larger existing codebase. It helped me understand the project and fix issues, but I also learned not to blindly trust the generated code.
3. Writing tests first - I learned to write test cases before fixing an issue, run them to see if they fail, then make the changes and run them again. This helped me verify that the fixes actually worked.

## The decision I'm least sure of

I'm still not completely sure about disp_04. The note looks harmless, but I kept suspicious_content because one extra review costs around ₹85, while missing a malicious instruction could cause much bigger loss. I would test more genuine and malicious examples to see if this rule is creating too many unnecessary reviews.

## With one more week

First, I would complete Part 4 by adding field-level evidence so reviewers can see where each value came from. Then I would work on the frontend review queue, test more edge cases and run evaluations on more invoices.
It was challenging to understand and fix this much in one day. I mainly focused on backend fixes, validation and tests. I couldn't complete Part 4 or make any frontend UI changes. I think my AI usgae was high than I initially anticipated. I would definitely try to work on that.