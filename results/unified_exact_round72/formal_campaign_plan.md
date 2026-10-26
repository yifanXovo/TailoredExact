# Round72 full validation extension, declared before exact results

Base is Round71 final 73ce04d9a3c5031c2b5a1021523502f0a9a85168, draft PR132.
The closed Round71 outputs remain immutable. The six separately declared
startup-only diagnostics cost 0.390s and zero native Optimize calls. All three
DS-X startup objectives improve DS, but that is not exact performance evidence.

The resource service subsequently reported ordinary usage allowed and 100%
remaining. The agent did not redeem a reset credit; the cause of the change
is unknown. This enables the following bounded extension in a new campaign
subdirectory. No algorithm or parameter changes are made after seeing the
diagnostic results. All roles are exposed development/protection data.

First run nine fresh complete comparisons, in this order: D3, C2, D4, each
P-GRB, DS, DS-X, with a common whole-process cap of 300s. Maximum 2700s.
Each candidate computes and pays for its own startup. The diagnostic routes,
historical bounds and known objectives are never imported. This tests whether
DS-X restores D3 certification and preserves C2/D4 protection while retaining
the previously measured small and D6 gains.

Reserve, but do not automatically open, three additional fresh D7 runs:
P-GRB, K1-R, DS-X, each with a common whole-process cap of 3600s. Maximum
10800s. Admit this extension only after all nine full runs pass physical,
model, Start, coverage and configuration audits; DS-X has no newly observed
severe P-relative loss on those roles; and there is a material DS-relative
improvement or a recovered certificate. Record the decision and the exact
evidence before launching D7. The purpose is to determine whether the R71
1200s protection loss persists at a common 3600s window, not to assume it
will disappear. If the gate fails, retain the negative result and change
research direction instead of consuming this reserve. No repeats or further
7200s extension are declared here.

Total extension maximum: 12 full performance launches, 13500s. Four separate
P model exports have zero Optimize calls and caps of 30s each (120s maximum).
Together with the diagnostic prefix, the maximum is 18 charged experiments,
13680s, plus four no-opt exports. Actual native calls and full costs are
counted from the ledgers. All new optimization is serial, without compilation
or heavy audits competing with it. Uniform launcher/child mask4 is inherited
and read back on every arm. No clock-frequency correction is made.

Use unchanged R71 source freeze 3867214f480d0a4fef4d77f03404f9fd89fb8b42,
executable SHA256 4f60ed8cd6f65c695947e8ac3bd525b77d28d94733faf2c9ef25d057a69023af.
All 199 qualified source hashes, reference binary and test log must match.
The 49 CTests and 39 native qualification calls are inherited, with zero new
builds/tests/qualification calls. No such historical cost is charged again.

P-GRB retains the original compact model and native defaults: no extra Start,
cut, heuristic or bound. Gurobi13.0.2, Threads1, Seed0, PresolveAuto, zero
requested MIP gaps and original numerical tolerances are common. DS/DS-X and
K1-R retain their exact R71 definitions. Only the common whole-run deadline
terminates work; no internal seconds/Work slice, restart or timed fallback.

The R69/R71 practical criteria remain frozen. Both certified and both below
60s on V<=12: material >2s and20%, severe >5s and50%; otherwise material
>10s and15%, severe >30s and50%. Both open: material absolute-gap change
>0.001 and10%; severe >0.01 and50%. Certificate loss is reported explicitly.
These are practical, not statistical criteria. Mixed UB/LB changes remain
visible. Valid same-run checkpoints may be used conservatively; final routes
are never backdated. No independent confirmation is claimed. This extension
cannot by itself establish the sustained goal.
