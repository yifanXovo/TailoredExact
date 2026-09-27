# Round 87: ENS-C versus official P-GRB, five-pair early closure

## Decision and scope

This is a test-only comparison of the frozen R83 ENS-C preset with official
original-compact P-GRB. The original protocol planned nine pairs and 18
serial runs, each with an 86,400-second process cap. The user ended this
round after the first 10 completed runs because of the available time budget.
Those 10 runs form five complete pairs: D6, D7, U6, F2, and F5. All 10
completion audits passed. This is **not** completion of the original nine-pair
protocol, and no 18-run `driver_completion.json` is claimed. F6 and the three
additional Round 58 CitiBike roles remain eligible for later testing; their
omission is not an algorithm failure. The user-directed scope change and the
brief, excluded run-11 launch are recorded in `scope_amendment_2026-09-26.md`.

The measured algorithm/model source remains qualified commit
`4496078f25c0cdad1cf7a5c39835fd23121e8978`; the common R83 executable
SHA256 is `25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e`.
No algorithm, model, default, heuristic, cut, branch rule, or per-instance
dispatch was changed. Gurobi 13.0.2, Threads=1, Seed=0, Presolve=Auto,
requested MIPGap=MIPGapAbs=0, and equal CPU affinity were frozen before
launch. Each arm paid its own full process time and used only same-run
physical witnesses and global bounds. These are numerical solver
certificates, not strict rational proofs. The inherited 62 qualification
tests/165 native calls are identified by hash; they were not rerun here.

## Main outcome

| Role | P-GRB original-problem result | ENS-C original-problem result | What the pair establishes |
| --- | --- | --- | --- |
| D6 | Certified in 22,570.062 s | Certified in 3,160.907 s | ENS-C certified 7.140× faster, a 19,409.155 s advantage. Both certified objective 0.157083131103174. |
| D7 | Censored near 86,398 s; UB/LB 0.216466726/0.201850006 | Censored near 86,398 s; UB/LB 0.223531546/0.208219082 | No certification-time ordering. P-GRB has the better UB and smaller absolute gap; ENS-C has the stronger LB. |
| U6 | Censored near 86,398 s; UB/LB 0.145272981/0.132164045 | Censored near 86,398 s; UB/LB 0.145287738/0.134881298 | No certification-time ordering. UBs are close; ENS-C has the stronger LB and smaller absolute gap. |
| F2 | Quota-interrupted, administratively censored after at least 70,647.797 s; UB/LB 0.865943520/0.838628785 | Certified in 535.921 s | ENS-C certified well before the observed P-GRB interruption. P-GRB did **not** receive the full 86,400 s; no full-budget speed ratio is inferred. |
| F5 | Censored near 86,398 s; UB/LB 0.299991538/0.271980747 | Censored near 86,398 s; UB/LB 0.302443014/0.281512720 | No certification-time ordering. ENS-C has the better LB and smaller gap, but its final UB is worse. |

One pair has two certificates (D6), one has an ENS-C certificate and an
administratively censored P-GRB arm (F2), and three are doubly censored.
Thus the earlier fixed-budget gap evidence converts to a measured
certification-time advantage on D6 and an observed advantage up to F2's
interruption, **not** to a demonstrated stable win across these five pairs.
No test in this reduced round establishes a late certification-time reversal
on a hard role: D7, U6, and F5 never certified in either arm. F5 does show
the requested primal/proof tension concretely: ENS-C's stronger LB and
smaller gap did not overcome its weaker verified UB within the shared cap.
The untested additional CitiBike roles cannot corroborate or contradict
this pattern.

## Finding a solution versus proving it

For D6, the first same-run verified witness at the certified optimum was
observed at 22,569.375 s (P-GRB) and 3,160.844 s (ENS-C), leaving observed
proof/closure tails of 0.687 s and 0.063 s respectively. The main D6 time
difference therefore arose before each arm first produced its final optimal
witness, not from a long post-discovery proof tail.

For F2, ENS-C first observed the certified objective 0.865943520322989 at
73.765 s and certified it at 535.921 s, an observed tail of 462.156 s.
P-GRB's committed journal contains a physically verified witness at the
same certified objective, with a receipt close time of 3.1272515 s; however,
the quota interruption lost the original per-event polling timestamps.
Its first legal observation is only bounded between that receipt time and
the last original driver status at 70,639.953 s. The final committed
endpoint at 70,647.797 s has no certificate and LB 0.838628785.
Accordingly `discovery_and_tail.csv` gives an interval for this arm, not a
fabricated exact `t_find*` or `t_tail`.

For D7, U6, and F5 no reliable optimal objective was certified by either
arm. Their discovery entries mean *first observation of that run's own final
UB*, never `t_find*`. A smaller gap on any censored arm is not promoted to
an optimality certificate or a speed winner.

## Evidence, anomalies, and validation

The original quota loss interrupted run 8 (F2/P-GRB) before its cap. Its
719,974 contiguous committed receipts were independently replayed and
physically/scope-audited without a normal result or certificate. All
recovered events were assigned a conservative observation upper bound;
precise per-event times are not claimed. The actual process exit time is
unknown and later than the last receipt. See
`interruption_report_2026-09-24.md` and the raw recovery manifest.

The 10 formal runs accumulated at least 615,302.749 recorded process
seconds (170.917 hours); this is a lower bound because run 8's actual exit
time is unknown. The later, user-directed stop of run 11 preserved its raw
directory but did not yield a completed formal result. Runs 12–18 were not
started. No raw evidence was overwritten or any arm rerun.

`scripts/round87_analyze_partial.py` separately re-read every receipt of
the 10 formal arms, recomputed physical witness feasibility and scoped/global
bound validity, rechecked finalized original-problem endpoints, and compared
them with the saved audits. It made zero optimizer calls. It found 971
verified witness rows and no contradiction between either arm's physical UB
and the strongest same-role global LB. All five cross-arm contradiction
checks passed. `independent_validation.json`, `endpoints.csv`,
`paired_comparison.csv`, `checkpoint_trajectories.csv`,
`discovery_and_tail.csv`, and `witness_index.csv` carry the compact
machine-readable results. `excluded_run11_raw_index.csv` indexes the
non-formal raw fragment separately.

The frozen 18-run `round87_analyze.py` was not edited or invoked on an
incomplete campaign. The user-authorized partial analyzer is a separate
entry point. To reproduce its calculation, use an isolated copy of this
checkout *before* the generated `campaign/analysis.json` is present,
retain the identity-matched raw tree at the paths in `campaign/identity.json`,
and run:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round87_analyze_partial.py
```

The original run commands, complete parameter set, input hashes, and
prelaunch identities are in `protocol.json`, `campaign/identity.json`,
`preflight.json`, and `reproduce.md`. The raw tree remains at
`E:\codes\ExactEBRP-round87-runtime`; the package path, size, SHA256, and
selection policy are recorded in `package_index.json`. Individual journal
files are retained there; each formal receipt was checked against its
observation record during independent validation. The compact package
does not replace the raw journal tree.

## Conclusion

ENS-C has one unambiguous 7.140× certification-time win on D6. It also
certified F2 in 535.921 s while P-GRB remained uncertified at its
quota-interrupted, shorter-than-cap observation endpoint. D7, U6, and F5
do not establish a true certification-time ranking. In particular, F5
warns against reading ENS-C's better LB/gap as an optimality victory when
its verified UB is worse. The original nine-pair claim remains untested
after the user's early stop; no algorithm change or new selection is made
in response to these outcomes.
