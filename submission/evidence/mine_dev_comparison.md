| doc | expected | got | reasons missing | reasons extra | field differences |
|---|---|---|---|---|---|
| dev_001 | ready | review |  | suspicious_content |  |
| dev_002 | ready | ready |  |  |  |
| dev_003 | ready | ready |  |  |  |
| dev_004 | review | review |  |  |  |
| dev_005 | review | review |  |  |  |
| dev_006 | ready | ready |  |  |  |
| dev_007 | review | review |  |  |  |
| dev_008 | review | review |  |  |  |
| dev_009 | ready | ready |  |  |  |
| dev_010 | review | review |  |  |  |
| dev_011 | review | review |  | suspicious_content |  |
| dev_012 | review | review |  |  |  |
| dev_013 | review | review |  |  |  |
| dev_014 | review | review |  |  | invoice_number: got 'CN-XXXXX4417', want 'CN-2026-04417' |
| dev_015 | review | review |  |  | invoice_number: got 'SIS / 26-27 / 0018', want 'SIS/26-27/0018' |
| dev_016 | ready | ready |  |  |  |
| dev_017 | ready | review |  | suspicious_content |  |
| dev_018 | review | review |  |  |  |
| dev_019 | review | review |  |  |  |
| dev_020 | ready | review |  | suspicious_content |  |
| dev_021 | ready | ready |  |  |  |
| dev_022 | ready | ready |  |  |  |
| dev_023 | ready | review |  | suspicious_content |  |
| dev_024 | review | review |  |  |  |

Documents: 24, needed review: 13
MISSED REVIEWS (needed review, routed ready): 0 []
Unnecessary reviews (ready, routed to review): 4 ['dev_001', 'dev_017', 'dev_020', 'dev_023']
Missing from predictions: 0 []
