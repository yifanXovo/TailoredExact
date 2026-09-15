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
