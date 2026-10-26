# Candidate family definition

All primary arms use K0=4 and a shared implementation path.

- A: K4 envelope with no recursive refinement.
- B: unchanged C6 decisions plus parent-only or nested envelope strengthening.
- C: C6 split veto, `old_split AND F >= rho_F`.
- D: veto plus parameter-free decisive-frontier promotion gated by M_root.
- E: F-only, F-and-M_root, or H=F*M_root conservative refinement.
- F: M_root-only causal reference.

Lookahead is fixed-d1, fixed-d2 reference, or bound-driven frontier-d2.
Injection is E-all, E-violated, E-active-one, or causal E-none. Scope is parent
or nested. Every split is a binary midpoint split. D_R43 and P_profile are
diagnostics only; fitted score combinations are forbidden.
