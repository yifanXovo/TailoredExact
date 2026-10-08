# Round108 independent zero-solver inheritance review

Reviewer: `/root/independent_admission`. Scope: frozen M-B mathematics/search inheritance and S12/N36 historical measurement eligibility. This reviewer did not run a solver, create a native environment, call Optimize/IIS, compile, generate an input, import production helpers, alter production source, or decide candidate performance.

Decision: **INHERITANCE_PASS; CURRENT_PRODUCTION_PERFORMANCE_ADMISSION_PENDING**. The inspected existing M-B implementation preserves the R100 contract. The specified R106 S12/N36 inputs retain sealed, unmeasured eligibility in the inspected retained history. This does not admit any formal performance arm: the current PE/DLL, actual P/ENS/M-B CLI qualification, canonical/Start/native readbacks, and frozen Round108 protocol still require a separate independent admission.

## Source, mathematics and call path

Frozen source commit: `b5d6d83bb8fc74682de6f1f6862c2e687712f4cf`. Inspected R107 delivery/new-worktree base: `b5db3f038f64215766a54498d8acc82e384de733`. Actual old R100 PE `fd2a30ea0bdba13dda7c19ee69e8c1f7f874482f3dad7cb2c1df48c4d7404f64` is historical identity, not a current performance observation.

The independent executable audit compares complete Git blobs and worktree bytes. Eleven relevant files are exactly unchanged, including CplexBaseline.cpp/.hpp, Round98StateService.hpp, MipStartMapping.cpp, Evaluator.cpp, ControllingLeafScheduler.cpp, PaperK1AmSf.cpp, IntervalRowFactory.cpp, CanonicalCompactModel.hpp and PhysicalWitnessValidation.cpp/.hpp. Their complete hashes are in `inheritance_audit01/audit.json`. Selected current-byte SHA256 values match the R100 candidate freeze:

| File | SHA256 |
|---|---|
| src/CplexBaseline.cpp | 9a230e48f9c6f5179d5760c216fd39774579e268c762aea4fe089efd076ea65c |
| include/Round98StateService.hpp | 5b202a5db205941cde679ab967508546a171e5846de79dbc8454591a76f126e7 |
| src/MipStartMapping.cpp | f8e7d7412613a390d821145fb7f7c54f4d98bf201c84c76d2dfbf5737ba90873 |
| src/ControllingLeafScheduler.cpp | 6bbc7e773355bac11e2fb60d9ec4641d57eedd7baf29c38de6eba3cde3674303 |
| src/PaperK1AmSf.cpp | a46dc43c2b0cba21b427d1c38884114e6b68f3e52f6c13493b609aecde702440 |

`writeCompactLp` in CplexBaseline.cpp retains x binary, load/Y integer and s/z/m binary; lines 909–910 make only p/d continuous for m-binary. `Round98StateService.hpp` makes m-binary nonprojected and nonlinked. The state block at lines 2986–3031 adds precisely the inherited two rows per station: sum(p+d) minus sum |b-y|s equals 0, and sum z plus the existing s(i,b) equals 1. The loop adds no selector for an absent b. Missing b is fixed-zero semantics; a singleton or empty actual state range preserves the original domain/infeasibility contract. There is no M-BL direction link or theta block on this path.

The implicit-integrality proof is valid under the retained assumptions: nonnegative quantities, integer b/Y, at most one binary service z, binary direction m, and original p/d direction upper bounds. With no service all quantities are zero; pickup forces d=0 and p=b-Y; delivery forces p=0 and d=Y-b. Hence p/d are integral without A/B. The original nonzero-service row excludes a visit at Y=b and makes B valid; one-hot state reconstruction makes A valid. Zero directional upper bounds require no division. This reasoning does not extend to split service, simultaneous pickup/drop, fractional b/Y, or fractional LP solutions.

`reconstructRoutes` at CplexBaseline.cpp:4084 checks every p/d column, including unvisited ones, for existence, finiteness, actual physical bounds and 1e-5 integrality tolerance before integer route construction. Gurobi callbacks and final decode invoke this inherited research check at GurobiBaseline.cpp:2980 and :3881. The unchanged Start mapper iterates all actual columns and original native types, with finite/value/bound checks. The original backend captures VType before LP relaxation at :2386–2392 and restores the exact array at :3929–3940; it does not restore all continuous quantity columns to I. Typed canonical identity and original cutoff/epoch remain cache qualifiers.

Evaluator.cpp:verifySolution retains empty departure, unique service, every prefix and final return load, and unloading of remaining return load. Its duration is travel + pickup_time * total pickup + drop_time * (station delivery + depot unload), equivalent to travel + (pickup_time + drop_time) * total pickup. Cumulative pickup may exceed Q. Station inventory decreases by aggregate return load; it is not constrained to preserve its initial sum. The unchanged objective/evaluator contract retains the zero-denominator convention and penalty.

The current parser consumes `--algorithm-preset research-round83-vds-equal-net-exchange` and `--round98-state-service m-binary`. main.cpp:271–272 reports the effective identity `research-round99-ensc-discrete-structure-m-binary`; this is not a recognized replacement input preset. `round100_continuous_quantities` defaults false and its flag consumes no false argument: omit the flag for M-B. The isolated guard rejects ENS-Q/M-B mixing. The preserved R83-to-R68 preset expansion retains the original 24+1 startup, physical closure and verified handoff.

Later additions are guarded: R101/102 native callbacks and PreCrush only activate under their non-off modes; R103/104 preparation requires their non-off modes; R105/106 alternate engines require non-off main dispatch; `makeGurobiFixedIntervalBackend` selects R107 only when its bool is true. main.cpp:3386–3477 rejects these later mechanisms combined with M-B. New options default off in Instance.hpp. The inspected shared PaperExternalGiniTree diffs add optional scope handling, readback fields and zero preparation offsets; AM, cutoff/child-cache/terminal rules and the default-off full-cover certificate branch remain original. The common DLL loader now resolves additional API symbols, so current actual DLL/CLI qualification is still needed.

## Historical measurements and sealed eligibility

The specified original bytes match:

| Role | Path | SHA256 |
|---|---|---|
| S12 | reference/round106_confirmation/S12.txt | 475763e70a2dc3b9d28a88028378e76946cbebf33aa7b7e5b033e018dd13369f |
| N36 | reference/round106_confirmation/N36.txt | 52d7e43a1cc3717cfe7183b302212c7ef0a4e81f3e62642c4fe8f83c546e6fea |

Both first appear in commit `8a2af86155fa2ef206d8d5156a9efc14d0acb102`. Case-insensitive exact SHA and slash/backslash path searches were actually executed with `--follow --hidden --no-ignore` in the complete retained R106 and R107 worktrees plus E:/codes/ExactEBRP, across results/scripts/reference text metadata. Junction following matters for R107. Every matching file and matching line is retained in the independent audit, together with exact command/cwd/return code, read-file SHA and elapsed time. Matches are protocols, input/archive manifests, cancellation/admission decisions and review/source snapshots or their failed reader receipts. No actual solver/LP launch/result matching these two identities was found.

R106 confirmation protocol says SEALED_NOT_ADMITTED_NOT_EXECUTED; its actual admission decision says formal_arms_started=0. R107 cancellation records both roles with actual_native_processes=0 and actual_Optimize_calls=0, NOT_STARTED_CANCELLED. The final independent implementation/performance review and public delivery review both confirm all nine sealed arms unstarted and cancelled. These records corroborate the actual scan; manifest or pure generation registration alone is not treated as a measurement.

Earlier measured S12 aliases in R88–R92 are the different file `reference/citibike443-regional-v1/instances/V12/cb443_V12_regional_r1_surplus_M01_Q30.txt`, SHA `060ee6366b2277c8427675e1a1484de7db10d2ef82a64d4e2ffa6e4695b7b626`. Their solver records therefore do not invalidate the specified R106 S12. Alias launch identities are independently parsed and retained.

The audit covers available retained text evidence and public manifest indexes; it is not a claim of hidden engine history, a fresh public-only restore, or a new independent performance rerun. No present measurement-eligibility defect was found. This eligibility must still be preserved through first-formal freeze.

## Read historical scope and remaining admission

The complete R100 report, mathematical note, candidate freeze, original runner scripts and complete_results_final tables were read. They preserve M-B's F2/C1 ENS certificate-time losses, F5 primal/gap loss, and measured P benefits on C2/N2 and certification roles. Those historical losses are disclosed tradeoffs; they are not a new automatic per-instance veto.

The complete R107 final report, reports05 arms/AM/requests/leaf/fees and both final independent-review types were read. Its eight same-PE results and STOP_TESTED_CONFIGURATION apply to original AM plus existing assignment/STRUCT. Both FRONTIER roles expose three original LPs, root partial target, legal requeue/cache reuse and root terminal; no multi-active-leaf split or noninitial cross-request reuse is exposed. The candidate retains C2's U≈0.3750564073 versus P≈0.1983028486 and loses F2 ENS certification at 539.500s. None of that authorizes further split/AM/net-return/IIS/fixed-Y/fallback experiments in this round.

Before performance admission, supply current source/build/PE/DLL identity; complete real three-arm argv and parameter readbacks; same-domain actual ENS/M-B canonical comparison and native p/d/type restoration/Start mapping; finite known-fixture or known-F2 real backend coverage; at least one applicable current-PE complete certificate or legal termination; the complete frozen seven-role order, thresholds and cancellation rules; input identities/generation records and resource supervisor. A pure exporter or historical PE does not replace current full CLI evidence. The signed gap must be rebuilt as own U-L; inherited native result.gap can be clipped and cannot supply the Round108 comparison field or prove full-cover certification.

Audit script SHA256: `67bf1d985e91ee2d25f52a6455033830d9aa2c8255e74b225071fb18b2bccb4d`. Actual successful execution: 94.75664300000062 engineering seconds, exit 0, zero solver/Optimize/IIS/compiler calls. Audit SHA256: `8873cb3903757a5973eabed3c7dda80d534c2efd8690cc25a30e0e83faed1514`; command-receipt SHA256: `e543eac6fe0a784b9ce11caf07bc1a7f52ce08cbb049bf9828424baeb6414806`.
