# Round169 directed original-source reading

Independent research reviewer: `/root/research_review` (agent review, not
human peer review). Read on 2026-11-16 through the live author-hosted PDF:

Paquete, L. and Stutzle, T. (2003), *A Two-Phase Local Search for the
Biobjective Traveling Salesman Problem*, author manuscript, 15 PDF pages,
<https://iridia.ulb.ac.be/~stuetzle/publications/EMO03.pdf>.

The relevant reading is section 2 and Algorithm 1 (PDF pages 2-4), together
with implementation sections 4.1-4.2 (PDF pages 5-6). The live text exposes
the complete algorithm steps; the mathematical glyph extraction is imperfect,
so this memo relies on the legible surrounding definitions and implementation
description rather than reconstructing missing formula symbols. No local
PDF checksum is asserted for this web-read version.

The paper combines changed weighted aggregations, local search initialized
from the preceding local optimum, an archive, and dominance filtering to
approximate a Pareto set. Its TSP implementation uses smooth weight changes,
updates nearest-neighbor lists, and compares local-search variants by quality
and cost. It explicitly warns that more aggregations need not escape local
optima. These establish direct prior art for objective diversification and
the need to pay for it.

R169 has a different, narrower experimental target: two independent extra
complete own-H paths, a single fixed evaluation objective, and a matched
two-restart original-weight control. It neither copies the chained TPLS
method name nor claims scalarization, multistart or feasible-fleet transfer
as new OR theory. The design/note describe that relationship accurately.
This source does not establish that the R169 recipe improves the complete
solver; only the paid B/M/C experiment can supply such evidence.
