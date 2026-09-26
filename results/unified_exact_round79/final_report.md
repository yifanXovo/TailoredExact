# Round79: frozen BDS-C retains small and nonzero proof performance

The unchanged BDS-C candidate certifies all six exposed development roles.
Against fresh P-GRB it is practically close on E7, materially faster on S12/N12,
and gains certificates on D3/C2/D4 at the same per-role budgets. It also
preserves the important K1 proof advantages. This is a successful bounded
validation stage, not overall goal completion: E8, the principal D6 long-window
proof deficit, D7 common3600 validation and independent confirmation remain.

Base R78 final d064fe38c14caf7f8bcc201212cd7654e99f52c1 / draft PR139.
Branch codex/round79-bdsc-small-validation. No C++, algorithm parameter, default
or main change. publication.json records this independent stage draft PR.

## Fresh complete runs

All18 serial runs return normally and pass the original physical, scope/coverage
and numerical endpoint gates. E7/S12/N12 use common120s caps; D3/C2/D4 use
common300s caps. Whole wall includes startup, every model/probe/native call,
evidence persistence and exit. All instances have nonzero original optima.

|Role|P-GRB paid s / status|BDS-C paid s / status|K1-R paid s / status|Certified original F|
|---|---|---|---|---:|
|E7|1.422 / certified|1.235 / certified|5.750 / certified|.020382503842|
|S12|5.657 / certified|1.812 / certified|40.734 / certified|.058563973126|
|N12|4.281 / certified|1.391 / certified|7.438 / certified|.804625519720|
|D3|297.062 / open|138.968 / certified|297.078 / open|.045001550056|
|C2|297.062 / open|113.875 / certified|297.078 / open|.829963413172|
|D4|297.078 / open|52.922 / certified|135.172 / certified|.506343307565|

E7's .187s difference is below the frozen2s/20% small-case rule, without a
statistical-equivalence claim. S12/N12 improve by3.845s/2.890s and exceed both
thresholds. K1's S12 regression against P is severe (35.077s and over50%);
its E7/N12 losses are material but below the absolute severe threshold. BDS-C
repairs those current regressions. D4 improves K1 certification by82.250s under
the other-certified10s/15% rule. Certificate gains on D3/C2/D4 are reported
separately rather than converted to artificial speedup ratios.

All uncertified final endpoints remain visible:

|Role / arm|Physical U|Global L|Absolute gap|Relative gap|
|---|---:|---:|---:|---:|
|D3 / P|.045054161581|.041540120012|.003514041568|.077995937|
|D3 / K1-R|.045054161581|.043855266498|.001198895083|.026610085|
|C2 / P|.829963413172|.771071519989|.058891893183|.070957216|
|C2 / K1-R|.829963413172|.797172650325|.032790762847|.039508685|
|D4 / P|.506343307565|.194483816490|.311859491075|.615905230|

Relative gap is (U-L)/abs(U). K1 still materially improves P's gap on D3/C2;
these are current proof/protection roles, not invented K1 P regressions. BDS-C
goes on to certify both. D4's K1 certificate advantage over P is retained.
At C2/D4, the final P upper bound equals BDS-C's certified objective, so the
primary difference is completing the proof, not reporting a better feasible U.

The63 actual-availability checkpoints cover30/60/120s or60/120/180/300s, as
frozen by role. C2 BDS-C is certified by120s, D3 by180s and D4 by60s; full
trajectories, comparisons and protection records are machine-readable in
campaign/. Availability=max(payload closure, completed observation). K1's S12
startup is first observed at38.063s and is not backdated into the30s checkpoint.
Tiny signed numerical gaps remain: for example N12 P is about-1.11e-16 and
D3 BDS-C about-2.08e-17. D4 K1's certified gap is2.3864e-10, not overwritten
with zero. These are original-tolerance numerical certificates, not rational
proofs. All committed receipts are observed; no incomplete data is promoted.

## What ran and what the result supports

Source4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e and the exact R78 executable
are reused: build/round78/v1/ExactEBRP.exe, SHA256
3fae847a75c3c9d07d8f5f0444daeafb73559865e6bffb816746802b9e2f43ab.
All269 source hashes, CMake/binary identity and prior60/60 qualification are
checked, with no new build/test charge. Gurobi13.0.2, Threads1, Seed0,
PresolveAuto, zero requested gaps, original tolerances and logical2/mask4 with
restoration are common. Input hashes and original V/M/Q/T/handling/lambda are
in campaign/identity.json. Six fresh zero-Optimize reference exports bind the
unchanged compact P model; it receives no added Start, cut or imported bound.

BDS-C remains research-round78-vds-balanced-descent:25 current-run JDS-X paths,
inherited strict physical closure, balanced-block duration descent and unchanged
complete VD-S proof. Only the whole deadline ends an unfinished algorithm.
R78 mathematics.md defines exactness scope and the finite descent argument.
The generic local-search components are not claimed as new theory.

All six runs finish25 paths and exhaust the declared physical neighborhoods.
D3/C2/D4 paths and starters exactly match R78. No balanced relocation is
accepted anywhere in this small panel. N12 accepts two inherited quantity-pair
changes, improving startup F from.884703629847 to.879835617333; all other closure
moves are zero. Every transition and chosen/exhausted neighborhood is physically
replayed, and all six actual outer handoffs match the module final routes.
S12's paid starter has62 pickup/47 station-drop units, retaining the legal
15-unit loaded return. No empty-return restriction or cumulative-pickup cap
has been introduced.

This is full-method retention evidence. R78's D6/D7 diagnostic/startup and full
D7 results remain the direct evidence for the new balanced relocation. The
small-panel gains cannot be attributed to neutral moves that did not occur.
N12's two quantity changes are real, but no fresh isolated ablation attributes
its full speedup solely to those changes.

The gains also cannot all be described as removing lengthy HGA. D3 K1 enters
the exact phase at2.073s, C2 at2.699s and D4 at1.964s; BDS-C certifies in
138.968/113.875/52.922s while K1 remains open on the first two and needs135.172s
on D4. BDS-C's D3 and C2 starters are actually worse than K1's (.078115 versus
.049469, and.837091 versus.829963). Actual full proof behavior, not just startup
time or initial U, determines these results. No startup cost is subtracted to
invent counterfactual performance. S12's large gain does include substantial
startup savings: its K1 exact phase begins at38.020s versus.415s for BDS-C.

## Audit, resources and delivery

All64 actual Optimize calls return:6 P calls,29 BDS-C calls and29 K1-R calls.
The nine actual BDS-C Start decisions are eligible, pass independent full-vector,
actual-row and readback checks, and are accepted in native logs. Maximum
independent row violation is6.66e-15. Twelve controls are checked for absence
of that explicit Start path. Acceptance alone is not a causal speed claim.

Independent audits validate182 physical journal witnesses (170 native and12
startup),21413 global-bound events and all21741 committed events, plus complete
coverage and normal certificates. Numerical comparison rules remain frozen.
Some raw sign-only UB/LB direction flags reflect rounding of order1e-16 on
already-certified cases; these do not change the practical timing conclusions.

Paid full-run wall totals1996.015s within the declared3780s maximum, with
.242146s separate replay. Preflight costs.584773s, including.328s for six
reference exports. Joint analysis costs3.214856s, actual mechanism audit.850892s,
packaging/verification10.741997s and a separate byte check1.432970s. No new
qualification, solver failure, supervisor exception, solver rerun, extra seed,
extension, confirmation run or reset credit occurs. Two early git attempts fail
before a third succeeds. Three later publication pushes fail; authenticated
Git Data API transport then verifies every original blob/tree/commit hash and
updates the branch without force in110.544634s. All original history is retained;
these transport failures never become native experimental failures. Interactive work is not
represented as a complete machine-time census.

Nineteen lossless bundles retain44084 files,46988126 raw bytes and8002390
compressed bytes. Every member's length and SHA256 verifies. The large generated
manifest is for programmatic verification; delivery.json and the reports supply
the compact review. Raw logs, models, receipts, vectors and witnesses remain
available; R78 qualification bundles are referenced rather than duplicated.
See reproduce.md for fresh-namespace and absolute-path limitations.

## Stage decision and remaining questions

The evidence is credible, the inherited architecture remains admissible, and
this frozen candidate passes the six-role primary/protection screen. No model
selection or parameter revision follows from these outcomes. These exposed
roles, including related CitiBike geography and constructed inventories, do
not provide independent generalization evidence. Earlier R73/R72 times are
historical context rather than paired causal ablations or mandatory records.

The overall goal remains unmet. long_role_review.md corrects one imprecise
R78 prospective sentence: D6 is the actual K1/P long-window proof deficit;
the older VD-S variant's advantage must not be mislabeled K1 protection.
D7 is protection. E8's old current-K1 small regression remains an explicit
untested BDS-C target. The old R39 non-startup losses did not reproduce as
large current E7/E8 K1 losses in R66; that is a reclassification, not a repair.

After publishing this stage, separately admit the E8 check and the consequential
fresh common3600 D6 comparison with P/K1 controls. D7 common3600 validation,
appropriate limited replication and structurally diverse unadapted confirmation
still follow. No additional experiment is admitted by this report, and no
single positive panel substitutes for the original overall acceptance criteria.
