---
description: Run one full trade cycle with the 6-agent crypto team (paper mode unless the user says "live")
---

Run one trade cycle. Mode: PAPER unless the user's message for this run explicitly says "live". $ARGUMENTS

1. **In parallel**, dispatch `scout-investigator`, `sniper-whale-watcher`, and `onchain-strategist` (Part A needs the scout/sniper output, so run the strategist again after step 1 if its first pass had no candidates).
2. Dispatch `security-auditor` on every candidate the scout and analyst scored ≥ 6. Drop all FAILs.
3. Dispatch `risk-manager` on the remaining candidates.
4. Dispatch `portfolio-manager` to apply the consensus rule, record trades (paper, or live after human "confirm"), and append to `reports/journal.md`.
5. Reply to the user with: trades taken (or "no trade" + which rule blocked it), account state, and the top risk for the next 24h.
