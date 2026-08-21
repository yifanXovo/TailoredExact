# Round 45 completion-matrix amendment

The original 213-row completion freeze treated the existing 19-row K4
gamma-veto small panel as reusable. A later source-scope audit, performed before
any of those 19 reruns, found that the authoritative-parent-bound correction is
on the ordinary adaptive split path. This is a bound-aggregation change under
Section 9.2 of the completion contract, so reuse is not permitted.

The required matrix is therefore amended, transparently rather than silently,
with the fixed pre-existing panel: five material-development rows, seven
validation rows, and seven opened-holdout rows. All use the final completion
executable, K4 gamma-veto at rho_gamma=0.012, midpoint, the 3600-second process
cap, and selection_use=false for validation and holdout. No result from any of
these 19 reruns was inspected before their identities were recorded.

The completion freeze manifest retains the original matrix hash and row count
inside its `amendment` object and records the amended hash and 232-row count.
This amendment is a disclosed repair to the original freeze procedure; it does
not retroactively pretend that the initial matrix was sufficient.
