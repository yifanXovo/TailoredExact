# Round71 pre-implementation plan: finite inter-route tail descent

Base: Round70 final1cf8381206edd5925eca0b03185ac1cd7dc99d2a, draft PR131.
Owned branch codex/round71-interroute-descent in E:/codes/ExactEBRP-round66.
The original dirty checkout and all old evidence remain untouched. The overall
goal is unmet. Round70 final_report.md and next_hypothesis.md are the research
basis; no historical report is reclassified as a fresh result.

Main hypothesis: the24 random-seed DS descents lose useful vehicle allocation
on D7, where initialU0.694563 serves33 stations versus HGA's50/U0.215644.
Enable the existing finite cross-route tail neighborhood uniformly within
decoded descent. DS-X uses research-round71-vds-interroute-descent, sampling
the same24 initial chromosomes at seed20260626. Candidates include existing
intra-route moves plus relocation of the first eligible unused-tail supply
or demand node to another route's decoded service anchor. The current greedy
decode and proxy ordering are unchanged. Only strict full-decoded objective
gain accepts a move; unsuccessful passes check every generated neighbor.

Keep the VD-S one-hot model, AM threshold0.08/initial interval1/midpoint/depth8/
width1e-4, full verified Start mapping and complete Gurobi proof unchanged.
No construction, evolution, larger population, local seconds/Work/iteration
allowance, restart, mathematical-input change or instance/history switch.
Stop on finite exhaustion, the whole-run deadline, or verified numerical zero.
Trace actual cross-route candidates and accepted moves, not merely the flag.
All construction/proxy/decoding/verification/model/native/exit costs are paid.

Qualification precedes performance. Add a substantive inter-route unit test
and complete native CLI regression; verify original physical semantics,
strict/exhaustive descent, cache agreement, fixed seed, actual cross-route
execution, deadline/zero behavior and actual Start/certificate path. First
configure/build/CTest attempts and failures are charged separately. The two
original micro settings (T5 with handling1+1; T3 with handling0+0) use
P-GRB/DS/DS-X at30 each, six correctness-only runs. Expected optimum5/24.
No zero-objective performance claim is inferred from zero handling.

Bounded performance plan: at most25 launches and10380s worst-case total.
Add six micros/180s, so the maximum is31 experiment launches/10560s. Ten
fresh no-opt original-P reference exports are separate qualification costs.
All eight roles retain original file hashes, V/M/Q/mathematical T and weights.

|Roles|Arms|Whole-run cap|Launches|
|---|---|---:|---:|
|E7,S12,N12|P-GRB,DS,DS-X|120|9|
|D3,C2,D4|P-GRB,DS,DS-X|300|9|
|D6|P-GRB,DS,DS-X|600|3|
|D7|P-GRB,DS,DS-X,K1-R|1200|4|

D7's1200 cap is declared now because both Round70 HGA controls failed to
reach proof at600. It allows a meaningful whole-algorithm K1 comparison and
reuses conservative300/600/1200 checkpoints from the same fresh runs. It is
not an internal resource policy or an extension spliced onto Round70 runs.
Only same-cap final endpoints enter performance pairs. P is original compact,
native defaults, no HGA/explicit external Start/new cut/imported bound.
K1-R is research-round65-k1-h with the already defined reliability settings.

After qualification, first screen E7/S12/N12 and D7. A mathematical/validity
failure stops launches. If cross-route moves never execute or supply no
meaningful route-quality/proof improvement on D7 while adding cost, review
the mechanism before opening the remaining D6/D3/C2/D4 panel. Do not reject
solely for losing one historical variant's fastest time. Conversely a large
P regression or loss of most meaningful K1 protection must remain visible.
Any revision receives new identities and an explicit revised resource plan;
no failed/unfavorable result is replaced or silently regenerated.

All fresh arms use Gurobi13.0.2/Threads1/Seed0/PresolveAuto/requested gaps0 and
original numerical standards. Own launchers inherit logical processor2/mask4,
with child readback and launcher restoration. Reuse prior affinity API
qualification as inherited evidence; do not claim a newly executed one.
No compilation or heavy QA runs concurrently with an optimizer. Raw logs,
models, witnesses and exact stage ledgers remain available; qualify legal
pre-proof whole-run deadlines with analytic global LB0 rather than fabricated
tree flags. Record supervisor exceptions separately from solver validity.

The Round69/70 practical thresholds remain frozen: both-certified V<=12 and
both under60s use material>2s AND20%, severe>5s AND50%; otherwise>10s/15%
and>30s/50%. Both-open gap changes require>.001 AND10% for material,
>.01 AND50% for large effects. Mixed UB/LB, certificates, signed numerical
differences and intermediate-witness limitations are explicit. These labels
are not significance claims or automatic per-point K1 vetoes.

All roles are exposed development data. No independent confirmation, extra
repeat,3600/7200 comparison or additional candidate is opened by this plan.
The proposed distinct V50 confirmation cases remain unrun. A promising result
still needs later common long windows and independent confirmation. Publish
a new draft PR for this substantive stage, then reassess against the whole
goal. Latest ordinary usage is available with12% weekly remaining; no reset
credit is authorized or used. Do not invent a resource block while meaningful
authorized work remains possible.
