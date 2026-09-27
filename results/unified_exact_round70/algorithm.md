# DS: fixed multi-start decoded descent with VD-S proof

Formal candidate: research-round70-vds-descent. The accepted experimental
revision is recorded under revision2/; revision1's complete-CLI qualification
failure and costs remain separate. No stable/default preset is changed.

1. Generate24 random station permutations with vehicle separators using the
   existing native initializer and seed20260626. Fully decode the initial
   population with the existing deterministic greedy operation decoder.
2. For each seed, generate the existing guided intra-route neighborhood and
   order it by its proxy objective. Fully decode successive candidates until
   a decoded fitness increase greater than1e-12 is found; accept it and restart
   that seed's neighborhood. If no improvement exists among all generated
   candidates, finish that seed. The proxy is never a rejection certificate.
3. Independently verify and retain every globally improving published physical
   witness. Stop early only for the whole-run deadline or a verified numerical
   zero certificate. Otherwise finish all24 finite descents.
4. Use the retained verified UB in the unchanged VD-S one-hot Gini-product
   model and AM proof controller. Preserve complete interval coverage and
   existing mathematical bound-target stops. For every actual MIP, map the
   paid witness to a complete Start when its interval/cutoff is compatible;
   verify rows, types, objective and API readback. Native Gurobi completes the
   MIP search. Retained LP models restore integer domains before MIP solving.
5. Report independently verified original routes as UB and the complete
   frontier's legal global LB. A certificate uses the original numerical
   standards; this implementation does not construct a rational certificate.

All seed construction, proxy work, cached/full decodes, verification, model
creation, LP/MIP calls, mapping and exit costs remain inside the paid run.
There is no internal seconds/Work quota, fallback search, hardware-dependent
selection or instance/history switch. The fixed24 seeds define the sampling
algorithm; the finite state descent, not an iteration allowance, ends each
search. Exhaustion concerns the generated neighborhood and this decoder only.

Gurobi13.0.2, Threads1, Seed0, PresolveAuto and requested gaps0 are shared with
the official original-compact P-GRB control. P uses native defaults and no
HGA, external Start, additional cuts or imported bounds. K1-R is the explicitly
defined reliability reference research-round65-k1-h. VD-S remains
research-round68-vdp-start. Logical processor2/mask4 is a uniform measurement
condition for all freshly paired arms, not a formal mathematical decision.

The backend retains the legacy round34 startup-container label hga-full for
compatibility, but actual dispatch and result hga_stop_mode are decoded-descent,
with zero HGA generations and a separate descent CSV. The revision2 backend
admits this combination only for the explicit DS preset, seed20260626 and24
starts. Old historical HGA-specific variants keep their existing restrictions.

Correctness follows from physical witness admission and the unchanged exact
proof, independently of heuristic quality. The design hypothesis is that a
small finite local search provides useful starts without the long evolutionary
stagnation tail. A weaker initial UB can enlarge the proof problem; only the
complete paired outcomes establish efficiency. The constituent local-search,
one-hot and native-Start techniques are not claimed as new theory.

The actual guided neighborhood is deliberately limited. For each route, form
the longest prefix whose travel plus return fits T (handling is checked by
the decoder, not this ordering proxy). Its first decoded drop and last decoded
pickup are insertion anchors. Move supply-role nodes to the supply anchor,
demand-role nodes after the pickup anchor, and the last zero-operation prefix
node to the tail, using the existing eligibility rules. Roles follow decoded
operations, then residual inventory surplus/shortage for zero-operation nodes.
The first eligible supply/demand nodes beyond the travel prefix are included.
Cross-route moves are disabled. Consequently each seed preserves its sampled
station-to-vehicle allocation. Duplicate generated candidates can remain and
are counted; cached evaluations still count as inspected candidates.

The inherited proof controller is the first-class K1-AM-SF controller:
one initial Gini interval, midpoint bisection, balanced normalized closure
threshold0.08, maximum split depth8 and minimum width1e-4. The historical
round47 tau0.07915 field is inactive compatibility metadata. Given parent
bound b, verified U and terminal child LP bounds bL,bR, normalize child gains
by max(U-b, certificate tolerance,1e-12), clip these decision scores to[0,1],
and multiply their minimum by their mean. This clips only the heuristic score,
never a reported legal bound. A score reaching0.08 admits the complete child
partition; small strict gain supplies a mathematical native-bound target;
no strict gain sends the parent to full exact closure. Strict child
infeasibility and all logical depth/width limits retain complete proof
obligations. Every required MIP uses the one-hot model and compatible verified
Start. These inherited rules are unchanged, not newly tuned in Round70.
