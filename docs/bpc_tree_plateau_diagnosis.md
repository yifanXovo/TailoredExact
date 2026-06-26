# BPC Tree Plateau Diagnosis

The selected stress rows did not primarily plateau in BPC pricing/tree work.
Pricing time is near zero in the summary rows, while bound time consumes almost
all runtime. BPC tree improvements remain important for future cases where
relaxation-only bounds cannot close but a tree is entered.

Current diagnosis:

- V12 M2 closes by relaxation-only full-frontier certificate.
- V12 M1 and V20/M3 do not close because interval lower bounds are too weak.
- No run in this round provides evidence that exact-label pricing is the active
  bottleneck.

The next BPC-specific optimization should be triggered only after a case shows
substantial pricing or node time in `results/exact_primal_stress_round`.
