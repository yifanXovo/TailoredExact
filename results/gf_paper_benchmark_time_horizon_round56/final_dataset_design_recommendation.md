# Recommended design for the later replicated paper dataset

Retain the Round 56 structural coverage rather than selecting only easy or certified cells. The final paper dataset should independently generate and freeze multiple landscapes per structural cell before any performance result is inspected.

Recommended strata:

- retain V in {8, 12, 20, 30, 50};
- retain both frozen fleet-density levels at each V for primary Q=30;
- retain T in {1800, 3600, 10800, 18000} as operational route limits;
- retain Q=20 sentinels at T=3600 and T=18000 for the lower-M fleet at each V;
- replicate each retained structural cell across multiple independently derived base-landscape seeds, with seeds and all cells frozen before runtime inspection;
- stratify reporting by inventory imbalance, geographic dispersion, fleet density, native utilization, and common-3600-second proof difficulty;
- preserve capped rows and failed-to-certify rows exactly as observed.

A practical minimum is three independent base landscapes per V; five or more is preferable for stable descriptive summaries. Computational allocation may be planned by structural stratum, but scenario inclusion must not depend on whether a Round 56 counterpart certified or produced a favorable objective.

Round 56 should be cited only as a paper-candidate screening panel. It does not justify a universal scalability claim, a minimum-route-duration claim, or a final statistical conclusion.
