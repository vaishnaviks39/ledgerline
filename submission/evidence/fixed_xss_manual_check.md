# Manual check after fix: stored XSS in reviewer UI (F6)

- Fix: frontend/src/App.tsx renders `notes` as plain text (`{selected.notes}`) instead of dangerouslySetInnerHTML.
- Same setup as the baseline check: fake provider, dev_013 uploaded, its Remarks line inserted into `notes` by hand.
- Result: the notes box shows the <img ...> markup as visible text; no broken image; no request to exfil.example in DevTools Network (Keep log on). The document was also routed to review with suspicious_content (code check on raw text).
- Screenshots: fixed_xss_notes.png, fixed_xss_network.png.
- Baseline for comparison: starter_xss_manual_check.md and starter_xss_network.png (request to exfil.example fired).
