# Benchmark evidence blueprint (existing records only)

This is a comparison **map**, not a new experiment or a pooled performance
claim. The source identities, input SHA-256 and execution orders are fixed in
[R87 protocol](../unified_exact_round87/protocol.json),
[R88 preregistration](../unified_exact_round88/preregistration_a1_g3.json),
[R90 G3 preregistration](../unified_exact_round90/preregistration_g3.json)
and [R90 F2/D6 preregistration](../unified_exact_round90/preregistration_g4_priority.json).
R90 ENS-C and LP-G in each row are **contemporary same-new-binary, same-seed
pairs**. The P-GRB column comes from R88 for eight roles and R87 for D6/F2:
those P runs are historical relative to R90, even where the input hash,
scenario, handling parameters and seed agree. Do not divide their times by
R90 times. Within R88, its P-GRB and ENS-C arms *were* same-build pairs; R87
P-GRB and ENS-C were likewise paired in their own long-cap study.
The R88 binary is SHA-256 `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693`;
the R90 G3 ENS-C and flagged LP-G arms share binary
`bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`.
LP-G is the Round90 parent-LP-G split-point research flag on the original
ENS-C 24+1 start, AM gate and finite depth; it is not R88's one-seed A1
startup ablation or Round89's native B1 user-cut candidate.

P-GRB is the actual original compact-model Gurobi arm: the R88 command uses
`--method gurobi --plain-baseline`, no ENS-C preset, no explicit HGA MIP start,
and exports `compact.lp` ([runner command](../../scripts/round88_a1_g3.py)).
`GurobiBaseline.cpp:4033–4044` forces `spec.strengthened=false` through the
shared canonical writer and binds its model SHA/fingerprint; `:4110–4145`
sets/readbacks Threads 1, Seed 0, Presolve Auto and zero requested relative
and absolute MIP gaps before native model read. It does **not** pay the ENS-C
24+1 constructive startup, interval tree and its proof orchestration. Its
complete process wall does pay input parsing, original LP construction/export,
model read, Gurobi search, witness verification and serialization. ENS-C and
LP-G have their own complete startup/model/proof costs inside their process
walls. R88 short caps use `cap−6` native limit, `cap` process limit and an
external stop near `cap−2`; R87 long caps are 86,400 s, with its separate
quota-interrupted F2 exception. Solver Work, startup subphases, audits and
prelaunch overhead are nested or separately reported and must not be added to
an algorithm process time. All stated certificates are project numerical
original-problem certificates under the recorded tolerances, not rational
proofs.

Compact endpoint notation below is `C` certified or `O` open/censored,
followed by **physical U / global L; complete process seconds**. A `≥` means
only a lower bound on observed process time. Values are rounded for display;
the linked reports/tables contain full precision. Cap columns are full
process ceilings in seconds; P source `88`/`87` identifies the *run round*,
not canonical-model ancestry.

| Role | P source/cap; P endpoint | R90 cap; ENS-C endpoint | R90 LP-G endpoint |
| --- | --- | --- | --- |
| E8 | 88/120; C .021337006/.021337006; 1.891 | 120; C .021337006/.021337006; 3.109 | C .021337006/.021337006; 3.515 |
| S12 | 88/120; C .058563973/.058563973; 6.312 | 120; C .058563973/.058563973; 3.484 | C .058563973/.058563973; 3.578 |
| D3 | 88/600; O .045001550/.042637175; 597.141 | 600; C .045001550/.045001550; 153.984 | C .045001550/.045001550; 154.234 |
| C2 | 88/600; O .829963413/.784774182; 597.109 | 600; C .829963413/.829963413; 123.813 | C .829963413/.829963413; 112.141 |
| D6 | 87/86400; C .157083131/.157083131; 22570.062 | 3600; C .157083131/.157083131; 3447.219 | O .157083131/.156352294; 3597.203 |
| F2 | 87/86400; O .865943520/.838628785; ≥70647.797, quota stop | 600; C .865943520/.865943520; 585.656 | C .865943520/.865943517; 311.578 |
| D7 | 88/1200; O .277320866/.197286479; 1197.141 | 1200; O .236602412/.203357232; 1197.172 | O .236696678/.203357232; 1197.140 |
| U6 | 88/1200; O .214077039/.125145260; 1197.125 | 1200; O .152320933/.129058442; 1197.157 | O .153936748/.128924896; 1197.125 |
| F5 | 88/1200; O .435779943/.267832611; 1197.109 | 1200; O .329536990/.281414298; 1197.547 | O .324743383/.280587564; 1197.172 |
| F6 | 88/1200; O .334897451/.264870121; 1197.140 | 1200; O .292941309/.276800909; 1197.172 | O .292941309/.276132276; 1197.157 |

P values for E8/S12 are from [R88 smoke](../unified_exact_round88/runner_smoke_report.md);
D3/C2/D7/U6/F5/F6 from [R88 rest](../unified_exact_round88/runner_rest_report.md).
D6/F2 P values and their true within-R87 ENS pairs are in the
[R87 final report](../unified_exact_round87/final_report.md) and
[paired table](../unified_exact_round87/paired_comparison.csv).
R90 values are from [G3 smoke](../unified_exact_round90/runner_lp_g_g3_smoke_report.md),
[G3 rest](../unified_exact_round90/runner_lp_g_g3_rest_report.md) and
[F2/D6 priority](../unified_exact_round90/g4_priority_report.md), each with
the corresponding raw summary, endpoint audit and cross-arm report. This
table does not include the currently running G4 remaining panel or treat
its incomplete files as results.

Two certified arms in the **same panel and cap** permit a direct
certification-time ratio. A certified arm against a later censored arm gives
only a one-sided observed advantage, not the censored arm's certification
time. R90 LP-G versus ENS-C meets the two-certificate condition for
E8, S12, D3, C2 and F2; the favorable C2 single-seed result changes sign in
the already fixed [three-seed C2 check](../unified_exact_round90/c2_repeat_report.md)
(two LP-G-faster pairs, one ENS-C-faster; median ratio 0.906), so no
best-seed or stable-speed claim follows. E8 shows a concrete small-instance
constant-cost loss: R90 LP-G takes 3.515 s versus its paired ENS-C 3.109 s;
the older R88 P arm at 1.891 s is context, not an R90 pair. On D6, ENS-C
certifies at 3447.219 s while LP-G is **not certified** after 3597.203 s of
its 3600 s cap; the latter is a censoring lower bound on possible later
certification time, not a candidate certification time. D7/U6/F5/F6 are
doubly censored under R90, so endpoint U/L/gaps describe search state, not
convergence wins. R88 P's censored D3/C2 arms cannot provide P certification
times for those roles.

The R87 five-pair long study has one direct two-certificate comparison:
D6 P 22570.062 s versus its **R87** ENS-C 3160.907 s. F2's **R87** ENS-C
certified at 535.921 s, while P was administratively interrupted without a
certificate. Its optimal-valued P witness is physically verified, but the
first legal observation is only in **[3.1272515, 70639.953] s**, because the
original polling times were lost; neither `t_first_optimal` nor a proof tail
has a known exact value. D7/U6/F5 stayed open in both R87 arms. None of this
is a new paired P timing for LP-G or any Round92 candidate.

For a final paper comparison of a *finalized* method, the material missing
evidence is a contemporary P-GRB original-compact arm and ENS-C/final-method
controls built from that final source, on a predeclared input/seed/cap panel
with full-process timing, physical U, valid global L, certificate/censor
status, model/source/input identities and all failed attempts. Independent
held-out data would need the same fixed comparison contract and provenance;
the present development roles cannot be retrospectively selected by their
favorable endpoint. This note does not select such a panel, request H1–H8,
authorize any run, or promote LP-G/Round92 from root-LP or short-cap gaps.
