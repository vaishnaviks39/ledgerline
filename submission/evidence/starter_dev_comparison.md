| doc | expected | got | reasons missing | reasons extra | field differences |
|---|---|---|---|---|---|
| dev_001 | ready | ready |  |  | invoice_number: got 'SIS26270042', want 'SIS/26-27/0042' |
| dev_002 | ready | review |  | duplicate | invoice_number: got 'SIS26270047', want 'SIS/26-27/0047' |
| dev_003 | ready | ready |  |  | invoice_number: got 'NPL26270031', want 'NPL/2627/0311'; invoice_date: got '2026-04-10', want '2026-04-11' |
| dev_004 | review | ready |  |  | invoice_number: got 'PGI26270009', want 'PGI/26-27/009' |
| dev_005 | review | ready |  |  | invoice_number: got 'VL0931', want 'VL/0931'; invoice_date: got '2026-03-30', want '2026-03-31' |
| dev_006 | ready | ready |  |  | invoice_number: got 'KT2026118', want 'KT/2026/118' |
| dev_007 | review | ready |  |  | invoice_number: got 'KT2026006', want 'KT/CN/2026/006'; required_approvals: got 1, want 0 |
| dev_008 | review | review | totals_mismatch | vendor_unknown | invoice_number: got 'BAC26270058', want 'BAC/26-27/0058' |
| dev_009 | ready | ready |  | tax_type_mismatch | invoice_number: got 'GPI0173', want 'GPI-0173' |
| dev_010 | review | review | gstin_invalid, vendor_unknown | bank_details_changed, tax_type_mismatch | supplier_gstin: got '06AAEFO3390B1ZL', want '06AAEFO3690B1ZL'; invoice_number: got 'OF260398', want 'OF-26-0398'; bank_account: got '****4411', want '50200044109911' |
| dev_011 | review | ready | vendor_new |  | invoice_number: got 'SCPL26270004', want 'SCPL/26-27/004' |
| dev_012 | review | review | suspicious_content, vendor_new | duplicate | invoice_number: got 'ZOS262600119', want 'ZOS/2026/0119' |
| dev_013 | review | ready |  |  | invoice_number: got 'PGI26270011', want 'PGI/26-27/011'; bank_account: got '****751', want '0219201000751' |
| dev_014 | review | review |  | vendor_unknown | invoice_number: got 'CN202604417', want 'CN-2026-04417'; invoice_date: got '2026-03-04', want '2026-04-03'; bank_account: got '', want None; ifsc: got '', want None; required_approvals: got 1, want 2 |
| dev_015 | review | review |  |  | invoice_number: got 'SIS26270018', want 'SIS/26-27/0018' |
| dev_016 | ready | review |  | tax_type_mismatch, totals_mismatch |  |
| dev_017 | ready | ready |  | bank_details_changed, tax_type_mismatch, vendor_unknown | invoice_number: got 'BAC26270061', want 'BAC/26-27/0061'; required_approvals: got 1, want 2 |
| dev_018 | review | ready |  |  | invoice_number: got 'AH0042', want 'AH/0042' |
| dev_019 | review | ready | duplicate | none | invoice_number: got 'KT2026118', want 'KT/2026/118' |
| dev_020 | ready | ready |  | vendor_unknown | invoice_number: got 'BAC26270049', want 'BAC/26-27/0049' |
| dev_021 | ready | ready |  |  | invoice_number: got 'OF260412', want 'OF-26-0412'; invoice_date: got '2026-03-31', want '2026-04-17' |
| dev_022 | ready | ready |  | tax_type_mismatch, totals_mismatch | invoice_number: got 'NPL26270328', want 'NPL/2627/0328' |
| dev_023 | ready | review |  | bank_details_changed, vendor_unknown | invoice_number: got 'VL0952', want 'VL/0952' |
| dev_024 | review | ready |  |  | invoice_number: got 'SIS26270051', want 'SIS/26-27/0051'; invoice_date: got '2023-10-10', want '2026-04-28' |

Documents: 24, needed review: 13
MISSED REVIEWS (needed review, routed ready): 8 ['dev_004', 'dev_005', 'dev_007', 'dev_011', 'dev_013', 'dev_018', 'dev_019', 'dev_024']
Unnecessary reviews (ready, routed to review): 3 ['dev_002', 'dev_016', 'dev_023']
Missing from predictions: 0 []
