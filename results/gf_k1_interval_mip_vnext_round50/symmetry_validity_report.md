# Round 50 symmetry validity report

## Exactness argument

For every frozen state, all vehicles have the same capacity and the model's vehicle-indexed variables and constraints are otherwise label invariant. Any feasible solution can therefore be relabeled without changing feasibility or objective value.

The v0 representative orders adjacent vehicle routes by nonincreasing customer-use cardinality. S1 instead orders the unique depot successor index, using rank zero for an unused route. S1-R1 uses rank `s_k + (V+1)(1-a_k)`, so used routes are ordered by successor and precede unused routes. Customer and station degree constraints make the depot successor unique for a used route. Sorting interchangeable vehicle labels by either declared rank therefore selects at least one representative from every orbit and cannot remove an objective value.

## Independent model audit

`symmetry_model_correctness_s1.csv` and `symmetry_model_correctness_s1r.csv` cover D1--D14. All 28 rows pass. Each audit compares parsed LP row-signature multisets, checks identical capacity vectors, verifies the exact removed and added formulas, and requires all non-symmetry rows to be byte-equivalent after canonical parsing.

## Experimental disposition

S1 materially improved D2, D10, and D12. Its permitted used-first revision materially improved D2, D3, and D4. Both nevertheless changed D13 from v0-certified optimal to time-capped at 300 seconds. With one revision exhausted and the severe-regression gate triggered twice, neither candidate is accepted. The frozen backend retains v0 cardinality symmetry and no confirmation run is opened for these candidates.
