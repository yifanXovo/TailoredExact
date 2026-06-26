# Primal UB Threshold Study

This study separates upper-bound quality from lower-bound certificate evidence.
All heuristic and imported incumbents in this study are UB-only and contribute
no lower-bound evidence.

## Diagnostic Targets

Regenerated V12 M1:

- known good UB: `0.357200583208`;
- strong target: `<= 0.357500`;
- minimum target: `<= 0.360000`.

Regenerated V12 M2:

- known diagnostic archive UB: `0.719065249476`;
- strong target: `<= 0.724500`;
- minimum target: `<= 0.735000`.

These values are diagnostic targets only. Archive rows are not paper-core
defaults and must be labeled diagnostic.

## Current Findings

The improved reproducible heuristic reached:

- V12 M2: `0.745475`;
- V12 M1: `0.366800`.

The explicit exported incumbent JSON rows reproduce the same UB values, which
confirms that the route export/import path is deterministic and verifier-gated.
However, both UBs remain too weak for the current relaxation-only certificate
portfolio to close in 300 seconds.

The diagnostic archive comparison for V12 M2 closes with objective
`0.719065249476` in the same solver/certificate pipeline. This confirms that
the main blocker in the current paper-reproducible run is primal UB quality,
not a lower-bound certificate regression.

## How Much UB Is Needed

For a relaxation-only frontier certificate, every improving Gini interval must
be empty or bound-fathomed against the verified incumbent cutoff. A weaker UB
expands the improving range and raises the cutoff target needed for interval
fathoming. The gap between `0.745475` and `0.719065249476` on V12 M2 is
approximately `0.026410`, which is large enough to leave active intervals
unfathomed under the current relaxation time budget.

Per-interval cutoff thresholds are summarized in
`results/primal_ub_improvement_round/cutoff_threshold_summary.csv` when they
can be inferred from raw result ledgers. Artificial UBs are not used as proof.

## Conclusion

The next certificate-oriented improvement should strengthen the reproducible
HGA/TGBC incumbent, especially the compact TGBC decoder and guided education.
Broad frontier tuning is secondary until the paper UB approaches the diagnostic
archive UB target.
