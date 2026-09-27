# Manuscript algorithm identity audit

The compiled manuscript identifies the stable paper algorithm as K1-AM-SF,
preset `paper-k1-am-sf`, with one complete initial Gini interval, midpoint
refinement, balanced normalized closure, `tau=0.08`, exact coverage, and the
F0-CLEAN fixed-interval backend. Gurobi settings are Threads=1, Seed=0,
Presolve=Auto, zero MIP gaps, native branching, default PreCrush, and no
dynamic user-cut callback.

MC4, VD-P, and VD-J are presented as default-off research formulations. The
manuscript states that VD-P passed fixed-interval gates but failed full K1 on
one severe major-witness regression; it does not replace the paper preset. It
also states that split revision, sealed P-GRB, and expansion were not opened.
No restricted diagnostic is described as an original-problem certificate, no
V50/V70 generalization is claimed, and no novelty claim is made without a
literature review.

Result: pass.
