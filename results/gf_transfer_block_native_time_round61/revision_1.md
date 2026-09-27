# Candidate revision 1, before confirmation

Evidence: initial BLOCK covers 30/30 D6 stations and 42/50 D7 stations, then
stops because no unused-station append improves. Its F is 0.256642/0.623429,
against PREFIX 0.157241/0.282856. LEGACY60 uses its 512 evaluations on only
2/1 accepted stations. These records support repairing committed quantities,
not merely increasing their scan budget.

Hypothesis: simultaneously changing two inventories in existing route orders
can undo greedy quantity commitments. Use the same exact increment, shortlist
24 ratio-contrast pairs, quantity-major scan up to 2048 evaluations per round,
at most 16 rounds and 20 seconds. Rebuild each route from its original template,
remove zero operations, allow one direction per station, validate all load
prefixes and full duration. Strict final improvement is required. No optimizer.

One new mechanism, evaluated both after BLOCK and PREFIX to separate the value
of repair from the input constructor. v2 batch fixed sequence is LEGACY60,
BLOCK, BLOCK-R, PREFIX, PREFIX-R; its total physical cap is 90 seconds
(PREFIX 30 + BLOCK 20 + two repairs 20 each), normal stopping remains logical.
Repeat four developer roles D3/D4/D6/D7 (four charged launches), then freeze one
uniform scheme before any confirmation performance. Stop revision after this
comparison unless a correctness defect is found. PREFIX length stays 16.
