# Numeric guard work required before final freeze

Found by execution-team source inspection during development; no source edits or compilation are admitted during the active frozen performance batch.

1. `prepareFleetContract` uses an int loop over global Y endpoints; an endpoint at INT_MAX risks increment overflow. Use a wider iterator. All measured nondepot capacities are small (<100), so this boundary has not occurred in any measured audit.
2. Separator allocation/threshold iteration uses `maxQ+1` and int increments. Make size arithmetic and iterators representable at the integer boundary; retain the declared q family, without adding a time/Work or arbitrary size policy.
3. The physical handling sum is currently nominal binary64 `pickup+drop`. For generic nonexact sums, obtain an outward lower sum before taking the imported-coefficient minima. Every formal/actual-matrix role in this round uses pickup=drop=60, whose sum120 is exact, so this issue does not invalidate those coefficients or measurements.
4. Reject an unmapped physical-only contract from the column separator, rather than permitting empty-column/state access. Production uses the audited mapped factory; the issue concerns the standalone API path.
5. Protect integer-to-double aggregate resource conversion and rank/count dimension arithmetic. Unknown oversized arithmetic must weaken a necessary bound or return unsupported, never return a guessed deficit.

Repair only the new module, in a separate numeric-guard commit. Preserve current build05 and every current identity/receipt. Rebuild/archive a new stage after development is idle. Recheck exhaustive microcases and all four saved raw-point selections (zero Optimize), run actual-matrix fault guards, and pay for a fresh finite F2 P/ENS/ROOT protection group under the final source before freeze. No guard benefit is attributed to the event-cut method. The ordinary measured matrices and coefficient pairs have not triggered these edge paths; retain their results with their actual source/binary identities.

The existing80000s/72-start budget has approximately9000s reserve after the planned stages, enough for the finite common1200 F2 protection group and these solver-free checks. Reconcile the actual ledger before admission. Confirmation inputs remain absent until the repaired candidate is frozen.
