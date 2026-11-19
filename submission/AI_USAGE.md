# How I worked with AI

## Tools and models

- **Claude** (claude.ai chat, Claude Opus 5.5) for reading the codebase, planning, drafting code and tests, and drafting some documents.
- **Data shared with the AI tool:** I sent the repository's data (vendor master, documents, labels) to Claude for reference, which is fine here because the README says all of it is fictional. In a real client project I would not do that, because the data is confidential: I would share only headers or structure (for example the CSV column names), and only after confirming with the client that it is allowed.
- **LLM used by Ledgerline in my runs:** OpenAI `gpt-4o-mini` via `LLM_PROVIDER=openai_compat` (budget of about $3.40).
- VS Code with Pylance for editing.

## How I set up context

I uploaded the starter's backend, frontend, tests, docs, reference data and all dev and disputed documents into the chat, along with the README, so the assistant could quote exact code and policy text. When I moved to a new session I wrote a context hand-off file (`LEDGERLINE_CONTEXT.md`) summarising setup, baseline results, ranked findings and how I wanted to work (one step at a time, short commit messages, my own words for the required documents). No planning mode; I asked for step-by-step instructions.

## My workflow

- I asked the assistant to explain each part of the code before changing it (for example, exactly where routing values came from in `pipeline.py`).
- I captured the starter's baseline first, before any code change: batch runs, the eval, cost, the prompt contents, approvals and XSS.
- For each fix: the test first, run it and watch it fail, then the change, then the full suite, then a commit. Each fix has its own commit.
- I checked the AI's code by running the tests and real batch runs against the labels with my comparison script, not by reading alone.
- I made the judgment calls myself: ranking, the option B decision for the model's `suspicious_content` (after the dev run), the rulings, which disputed documents are riskiest, and keeping the dev predictions on the written policy while the disputed ones use flags.

## Where the AI was wrong

1. **It miscounted the documents that need review.** It said 15 of 24 dev documents need review; my comparison script counted the labels and found 13. (First session, after the starter dev run.)
2. **Its masking regex in an evidence script hit the wrong text.** It masked every 10-digit run, which also masked the policy's GSTIN alphabet `0123456789`. Only the evidence copy was affected, but it showed that masking must target account numbers specifically. (First session, step 6 of the baseline.)
3. **It wrote a test with inconsistent data.** The US-vendor approval test used Sitara's day-first date `25/04/2026`, which correctly raised "month must be in 1..12". I noticed when the test failed, and the AI fixed the test, not the code. (F7.3.)
4. **I went along with its design at first, and the eval showed it was wrong.** In F1.4 it recommended letting the model add `suspicious_content` on top of the code. I agreed. My first dev rerun showed 4 unnecessary reviews (plus one extra reason) caused by exactly that, and it caught nothing the code missed. I switched to "the model's flag is a warning only". (F1.4, then the first "mine" dev run.)
5. **Its masking fix corrupted an invoice number.** The F5 account masking treated `2026-04417` in `CN-2026-04417` as an account number, so dev_014's invoice number became `CN-XXXXX4417`. I found it in the comparison table; fixed with a test. (First "mine" dev run.)
6. **It initially pasted a full-file replacement that lost code.** When I replaced `parse_amount`, the date patterns between the functions were deleted and 30 tests failed with `ISO_DATE is not defined`. After that I asked for full-file versions or exact, small edits. (F7.2.)

## What I deliberately didn't delegate, and why

- **The rulings, the first-hour note, the reflection and the stakeholder replies:** the README requires them in my own words, and they are the decisions I have to defend.
- **The ranking of findings and the go/no-go recommendation:** these are business judgments about Meridian's money.
- **Deciding when the model's output should or should not count** (option B): I decided it from my own eval numbers.
- **Running and reading every test and batch result myself**, instead of trusting that suggested code worked.

## Time

About 12 to 13 hours in total, more than the suggested 6 to 8, mostly because the Part 1 fixes took much longer than I planned:
- about 1 hour reading and writing the first-hour note
- about 1.5 hours setting up and capturing the starter baseline (including fixing an old API key in `~/.zshrc` and the code-fence failure)
- about 8 hours on the Part 1 fixes and tests (there were a lot of them, each with a failing test first)
- about 1 hour on Part 2 (rulings, flags, tests, final predictions)
- about 1 hour on the eval report and the write-ups

## Transcripts

- `ai-logs/00_first_hour…` (first-hour session)
- `ai-logs/01_…` (other work and write-ups)