# Round71: inter-route descent improves D7, but loses most K1 protection

The bounded stage is closed at a resource checkpoint. DS-X is an admissible,
default-off exact candidate with useful incremental performance evidence;
the overall research goal is unmet. It preserves the measured small-instance
and D6 gains and materially improves DS on D7, but does not establish a
material D7 advantage over official P-GRB and loses most K1 protection there.

Base: Round70 final1cf8381206edd5925eca0b03185ac1cd7dc99d2a / draft PR131.
Branch: codex/round71-interroute-descent. Source freeze:
3867214f480d0a4fef4d77f03404f9fd89fb8b42. Executable SHA256:
4f60ed8cd6f65c695947e8ac3bd525b77d28d94733faf2c9ef25d057a69023af.
No measured code, binary, driver, mathematical input or numerical standard
changed after the freeze. Original defaults and the dirty checkout are intact.

## Method and admission

Preset research-round71-vds-interroute-descent adds the existing finite
cross-route tail-relocation neighborhood to the24-seed decoded descent.
Seed20260626, full deterministic greedy decoding and strict fitness gain
greater than1e-12 are unchanged. The proxy orders candidates only; an
unsuccessful pass checks every generated neighbor. Relocations preserve unique
station assignment. A complete independent physical witness is required for UB.

The best paid witness feeds the unchanged VD-S one-hot Gini-product model,
AM controller and complete verified native Start map. Gurobi is the full MIP
engine. The controller retains one initial interval, midpoint splitting,
normalized threshold0.08, depth8 and width1e-4, with complete proof obligations.
No local seconds/Work policy, restart, evolutionary startup, instance switch
or historical bound is introduced. The only time cutoff ends the whole run.
Every construction, decode, verification, model, probe, mapping and exit cost
is paid. Original loaded returns and prefix-capacity/handling semantics remain.

Correctness follows from physical witness admission and the unchanged full
proof. The limited neighborhood and finite strict descent do not prove global
heuristic optimality or faster runtime. Numerical certification is not a
rational certificate. These are established constituent techniques, without a
new-theory claim. See algorithm.md and mathematics.md for the exact scope.

## Complete measured outcomes

|Role|P-GRB|DS|DS-X|
|---|---|---|---|
|E7|Certified1.313s|Certified1.172s|Certified1.172s|
|S12|Certified5.140s|Certified2.156s|Certified2.125s|
|N12|Certified3.891s|Certified1.437s|Certified1.422s|
|D6,600s|Open gap0.012255293|Open0.007004089|Open0.006996067|
|D7,1200s|Open gap0.080034387|Open0.114881641|Open0.074188972|

The frozen practical criteria classify S12/N12 gains over P as material, E7
as below threshold, and all small DS-X/DS differences as below threshold.
Every small arm certifies the same original objective. E7 executes two accepted
cross-route moves; the two single-vehicle roles naturally have none.

D6 DS-X ends at U0.15708313110317415/L0.15008706391847396, a42.9% gap
reduction against P. DS ends at the same U/L0.15007904223698956; the difference
is below threshold. Both starts supply the same U0.16002728060440277 in about
5.51s. D6 generates no cross-route candidate across the completed descents.
This preserves the uniform method's previous gain, without claiming benefit
from a mechanism that does not execute on this role.

D7 demonstrates both the increment and the remaining defect. DS-X's9.380493s
startup supplies U0.5445105902163795,39 served stations and legal return load9,
versus DS U0.6945633798694341,33 stations and return17 after2.828939s.
DS-X completes24 seeds,371 passes and2355 decoded checks (2243 uncached calls),
including298 cross-route checks and178 accepted cross-route moves. The actual
mechanism runs substantially; full strict/terminal and physical audits pass.

After the same complete1200s window, DS-X has U0.2783352667791633 /
L0.20414629462573686. Its gap is35.4% below DS. Against P, UB is worse by
0.001014401 and LB better by0.006859816: the net7.3% gap reduction is below
the frozen10% relative threshold. The last improved physical solution belongs
to this same run and is never backdated to an earlier checkpoint.

Fresh K1-R ends at U0.21564407531579505/L0.1973574792283258, gap0.018286596.
Its612.421181s HGA startup completes2739 generations/41479 uncached decodes,
serving all50 stations with228 pickups/drops and empty return. DS-X's gap is
305.7% larger than K1-R's and retains only9.5% of K1's P-relative gap advantage.
The stronger DS-X lower bound cannot offset its weaker route quality. This is
a serious loss of a meaningful advantage, not a historical fastest-time veto.
No timing correction, seed selection, rerun or best-arm combination is used.

All final UB/LB, signed gaps, certificates, practical classifications and paid
times are in result_tables.md, runs.csv and pairs.csv. D7 details and its earlier
screen decision are retained in d7_screen.md/screen_decision.json. That screen
admitted D6; the later resource decision is separately recorded, not retrofitted
into the original plan or algorithm.

## Qualification and costs

First configure/build/test attempts all passed:49/49 new CTests, including two
actual native CLI certificates. The new unit checks74 cross-route candidates
and accepts67 moves, with physical/cache/finite-exhaustion/deadline checks.
Six separate original-problem micros certify5/24. Micro-zero means zero handling,
not zero objective. Ten no-opt P exports retain the original fingerprints.

Final experiments:16 performance+6 micro runs,95 actual Optimize calls and
6600.169s paid process wall; zero validity failures, startup-only deadlines or
supervisor exceptions. Qualification separately costs95.131s configure/build/
test and39 native calls; ten no-opt exports cost0.797s. Total native calls
including qualification are134. No heavy QA or compilation runs alongside an
optimizer. All fresh arms share Gurobi13.0.2, Threads1, Seed0, PresolveAuto,
requested gaps0 and original tolerances, with logical processor2/mask4 readback.
P remains original compact/native defaults without HGA, external Start, cuts
or imported bounds. No DLL hash or frequency lock is claimed.

Full QA passes75 witness/model checks (30 incompatible Gini intervals),12
eligible/accepted/full-vector-observed Starts and8 controls, every started
tree's full coverage, native versions/parameters and physical routes. The last
offline model/Start passes cost9.828/5.515s, not cumulative QA costs. Submitted/
readback vectors and exported rows are independently replayed; native MIPSOL
equality is qualified C++ observer evidence, not replay of unretained vectors.

There are348 compact artifacts,1084070 bytes:326 lossless artifacts and22 exact
result summaries. Content/hash checks pass for those artifacts,199 source files
and10 input settings. Eighteen conservative300/600/1200 checkpoints preserve
the buffered-clock and intermediate-witness limitations. P intermediate UBs
are native telemetry; candidate early UBs use retained verified initial routes.
Final witnesses are never assigned to earlier times. Large raw data remain local.

## Scope and continuation

The original maximum was25 performance+6 micros/10560 experiment seconds.
After the D6 audit, ordinary usage was still allowed but weekly remaining usage
was only2%; the remaining capacity is reserved for publication and recovery.
No reset credit has been authorized or used. Nine unlaunched D3/C2/D4 runs
(maximum2700s) are explicitly unmeasured. No in-flight run was shortened, no
formal cutoff was changed and no negative result was removed. See stage_decision.json.

Consequently D3 certificate recovery and C2/D4 protection under DS-X remain
unknown; no independent confirmation or3600/7200 comparison was performed.
Do not promote the preset or claim overall acceptance. After resources permit,
use a new separately identified stage to test those remaining roles before
deciding whether a common long D7 window and broader confirmation are justified.
Keep this stage's evidence immutable. Reproduce.md supplies same-byte replay
and zero-optimizer audit entry points. Git transport failures are separately
recorded in publication_transport.json and do not invalidate solver evidence.
