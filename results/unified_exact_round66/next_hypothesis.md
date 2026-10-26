# Candidate direction after the load-replacement stage

This is research preparation, not an opened performance phase or a frozen
selection. Round66's D6 and C2 comparisons must finish before its stage decision.

Round55 VD-P deserves a new evaluation against P-GRB. Its full-K1 exclusion was
caused by D3 (V12 M3 T2850), while the aggregate full algorithm gained two
certificates and had no reported V20/V50 material regression. The D3 action
trace did not change materially, supporting investigation of the inner model
rather than a split-controller change. Those are historical results, not a
current-build qualification. Its sealed P-GRB panel never opened.

One bounded possible revision is logarithmic selection of the same inventory
states. On a proved domain Y_i in {L,...,U}, keep the VD-P continuous selector
weights s_y and perspective variables q_y, but replace all one-hot binary
declarations by b=ceil(log2(U-L+1)) binary code variables. For each bit j impose

    code_j = sum_y bit_j(y-L) s_y,

in addition to sum s=1, Y=sum y*s, l*s<=q<=u*s, sum q=G, Z=sum y*q.
Use the natural binary encoding of the domain offset uniformly. A singleton
domain needs no code variables. No instance, runtime or historical winner
chooses an encoding. Do not add the VD-J penalty equality in this experiment.

Every integral code vector forces all positive weights to share every bit, so
injectivity leaves one state. Conversely every allowed state has its code.
Unused bit patterns select no state and hence are infeasible. This preserves
the original integer product and the full original route/objective projection.
With code variables relaxed, their equality just defines a convex combination
of codes in [0,1]^b, so the projection equals VD-P's LP relaxation. It may change
branching and presolve cost in either direction. Equality of LP projections
does not imply equality of performance or of the full integer hull after
intersection with route constraints.

The current writer (CplexBaseline.cpp) already replaces the product-only bit
block for VD-P; no product-only bit names remain referenced by shared rows.
The new mode would need explicit model metadata, main-preset admission,
zero-reliability compatibility, default-off isolation, and finite-domain
mapping tests before native runs. It should start with ARC off, to isolate
inventory representation. Only later evidence could justify combining them.

The general encoding idea is established, not a new theorem of this project.
Primary sources checked on 2026-09-15: publisher abstract of Vielma and
Nemhauser, Mathematical Programming 128 (2011), 49-72,
https://link.springer.com/article/10.1007/s10107-009-0295-4 ; author-submitted
abstract of Vielma, Embedding Formulations and Complexity for Unions of
Polyhedra, https://arxiv.org/abs/1506.01417 . Neither full paper has yet been
claimed as read. The above special-case proof is given directly; these sources
bound novelty claims and motivate reviewing formulation size/encoding cost.

A possible focused next panel is D3 (old VD-P regression), D4 (important
protection), D6 (real CitiBike proof deficit) and C2 (nonzero multi-leaf
protection), with current K1-R/P-GRB binding and an explicit VD-P control. The
actual call count and deadlines must be declared before that stage starts.
