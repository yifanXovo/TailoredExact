# Scope and correctness of equal-net served-block exchange

Let each route start empty, and let each integer signed operation be pickup
minus drop. For a contiguous block A write delta(A) for its sum, and m(A),M(A)
for the minimum/maximum relative prefix including the empty prefix0. Swapping
blocks A,B with delta(A)=delta(B) preserves every load before or after either
block, including each terminal load. Internal feasibility is exactly
0 <= entry_load + m(incoming) and entry_load + M(incoming) <= recipient_Q.
Check each recipient's actual capacity, which may differ. Loaded returns are
preserved and remain legal. Blocks' internal order and integer operations
follow their stations; single visits and nonzero unidirectional service survive.
Thus all final station inventories Y and the original F(Y) remain identical.

Recompute both complete routes' actual directed travel in route order and
original handling plus depot unloading: cp*pickup+cd*drop+cd*terminal_load.
No metric assumption or travel shortcut is needed. Both durations must satisfy
the unchanged T and physical tolerance. Neutral comparison uses the entire
descending sorted M-vector of durations, with exact finite double tuple
ordering (never an epsilon that overlooks an earlier increase). Adoption is
guarded by a complete original verifier, exact inventory/objective equality,
and exact predicted/verified duration-potential agreement. Invalid moves are
rejected, not used as U or proof information.

For one-way transfer between two empty-return routes, new terminal loads are
-delta and+delta, so feasibility implies delta=0. Equal-net exchange can move
nonzero-net blocks while preserving both returns. This explains the extension
at U6, without claiming that it necessarily improves its final gap.

Existing strict closure decreases F; neutral moves preserve F and strictly
decrease the duration tuple. With finite stations, bounded integer operations,
single visits and finitely many route orders, the lexicographic (F,tuple)
descent terminates absent the whole deadline. The program computes F from Y
in the same order and independently verifies adoptions. Local exhaustion is
limited to the declared move rules; it is not original-problem optimality.
This heuristic adds only verified feasible routes and never removes exact
search coverage, but complete exact integration is not yet admitted here.
Numeric verification is not a rational certificate; novelty and efficiency
are not inferred from feasibility or termination.
