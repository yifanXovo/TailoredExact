# Round108 evidence reconstruction

Round108 uses the unchanged production source content at R107 delivery
`b5db3f038f64215766a54498d8acc82e384de733`. The current measured PE SHA is
`4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0`; the
actual Gurobi 13.0.2 DLL SHA is
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
The source, helper, protocol, input and all 21 command bindings are in
`candidate_identity.json`, `bridge01/identity.json` and
`confirmation01/identity.json` inside the public carrier. Functional H100
qualification has its separate actual identity and three raw CLI runs.

## Public-only restoration

The logical `compact_evidence/evidence.tar.gz` compressed stream is an exact-byte,
manifest-bound carrier of
the current raw routes/vectors, canonical LPs, Start vectors, native logs,
committed native journal events, controller/cover ledgers, process completions,
whole-arm timing, fees, qualification, failed attempts and frozen identities.
It also contains the exact stdlib readers and measured source/helper bytes.
`compact_evidence/manifest.json` records every member's SHA256 and size, the
combined compressed SHA/size, and the exact public carrier blob names. The
strict single-blob gate is less than 95 MiB. Only an actual stream at or above
that gate is cut into consecutive 90 MiB parts, without per-part recompression;
each part has a canonical index, offset, size and SHA. A smaller stream remains
one file. Export/restore reject missing, extra, reordered, overlapping,
misplaced or hash-mismatched parts and verify the complete compressed SHA
before extracting any raw member. No
executable, DLL, license file or credentials are included.

The manifest's `public_dependencies` are exact, small historical R100/R107
documents/tables and the R98/R99/R102/R105/R106 family-decision reports,
pinned to a public Git commit. They document inherited claims;
they do not replace current performance evidence. To prepare a public-only
directory, copy the manifest and exactly the carrier blobs it names, plus
`scripts/round108_public.py`, then
fetch only the listed dependency bytes from each pinned commit/path and check
their SHA256/size. The provided `export` operation performs exactly that
procedure through `git show` for the recorded public commit.

Use an ordinary Python 3.11+ installation. The actual exact-field recovery was
verified with CPython 3.12.7, GCC UCRT 14.2.0 64 bit, on Windows 10 build 19045;
use that tested Python release when checking the last floating-point digits.
These operations use only the standard library and never load a solver. Choose new destination directories;
the restorer and report writer refuse existing destinations/output files.

```powershell
python scripts/round108_public.py export --root <published-checkout> --out <new-public-only-directory>
python <new-public-only-directory>/scripts/round108_public.py restore --public-root <new-public-only-directory> --out <new-isolated-directory>
python <new-isolated-directory>/scripts/round108_reader.py --root <new-isolated-directory> --out <new-isolated-directory>/rebuilt --compare <new-isolated-directory>/results/unified_exact_round108/reports_final
python <new-isolated-directory>/results/unified_exact_round108/review/campaign_raw_audit01.py --root <new-isolated-directory> --through N36 --isolated-public-math --out <new-isolated-directory>/results/unified_exact_round108/review/<new-exclusive-audit>
```

The reader takes its evidence root explicitly. It translates retained absolute
native paths into that root and has no original-worktree fallback. It checks
actual model types/A/B, every submitted full Start, every own reported fleet,
native parameters/call lifecycle, scoped native/LP bounds and the original
interval coverage before rebuilding endpoints and decisions. It preserves
signed `U-L`, uses the original zero tolerance for relative-gap nulls, and
applies certificate priority and the frozen materiality/selection rules.

The comparison requires exactly the same published CSV file set and all JSON
files in `reports_final`; it compares every CSV field and complete JSON value.
The candidate/evidence and stopped-family scope tables are included. Raw CSVs
and JSON journal records are input evidence, rather than copied summary
answers. Historical dependency tables are explicitly historical inputs.

The actual public export, fresh restoration, reader command/exit/source/root
and comparison receipts are delivered as supplements outside the immutable
carrier, avoiding a circular archive of its own hash. Independent final and
isolated reviews likewise retain their own commands and receipts. This is
evidence and mathematical reconstruction, not an independent engine
performance rerun or reproduction of exact wall times.

## Measured engine procedure

The engineering build receipts record the actual CMake/Ninja/MinGW toolchain,
blank `CMAKE_BUILD_TYPE`, four required target builds and source identities.
`review/performance_admission.json` accepted the current source/PE/DLL, true
production CLI qualification and all 21 frozen commands before the first
formal arm. Original cold P uses no ENS Start or extra linking row. ENS-C uses
the original `research-round83-vds-equal-net-exchange` input preset; M-B uses
that same preset with `--round98-state-service m-binary`. Its reported
effective identity is `research-round99-ensc-discrete-structure-m-binary`.
`--round100-continuous-quantities` is absent.

The already measured formal wrapper command was:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/round108_campaign.py billed bridge01 1 6 bridge01_all
```

The immutable run identities contain each child argv. Do not execute a
measured wrapper again in an existing raw directory: exclusive launch/fee
records prohibit overwrites and implicit retries. Any separate native
performance replication needs its own licensed engine, fresh qualification,
identity, budget and complete same-PE paired stage. The public reconstruction
above requires none of those native operations.

The standalone independent public audit explicitly requires the PE to be absent
and accepts no DLL argument. It verifies retained actual run identities and
current source/argv/raw evidence, while disclosing that binary bytes are not
rehashable in a PE/DLL-free public reconstruction. All evidence reads are guarded
to remain in the supplied restored root, including rebased historical native
paths. It never consults the original worktree or loads the installed solver.

The original qualification declarations omitted each inner Python driver.
Two retained +1 corrections in `fee_corrections/` make qualification 19 starts,
and an all-21 completion 46 starts, below 48. Original launches/receipts and
outer seconds remain unchanged. Independent accounting review accepted this
correction. `round108_budget.py` adds the corrections before reserving any
future complete confirmation group; the frozen performance helpers are not
changed to hide the original declaration mistake.

`whole_arm_receipt.json` measures admission/identity checks, startup, all
LP/MIP/callback work, raw writing, postexit physical audit and crosscheck through
the durable arm record. The legacy supervisor duration is retained separately.
Formal comparisons use the complete duration; enclosing fee bookkeeping is
charged in the outer wrapper. Internal native times overlap the outer wall
clock and are not added to the fee. Missing reserve-ending checkpoints are
not extrapolated. Safe witness-discovery intervals end at a committed own
observation or complete endpoint, and are not exact first native discovery
times.

## Retained reader repairs and failures

The input generator's depot-inclusive parser assertion failed before any
B24/L48 draw. The failed source/empty bytes and same-recipe assertion repair
are retained. Independent qualification first rejected a parser assumption
that zipped station operations with route order; its corrected independent
audit maps operations by station and preserves the failure.

The initial Round108 qualification reader assumed route variables were all
`I`; the existing canonical also uses `B`. The failure is retained with its
actual assertion/command and honestly unavailable exact old whole-script
snapshot/timing. Later reader attempts retain full source snapshots and actual
stdout/stderr/exit receipts before any repair. These are reader repairs and
do not change the production PE or rerun performance.

The frozen decision reader's tiny-negative-gap percentage check was repaired
without changing any production, comparison threshold or selection rule.
`engineering/signed_gap_reader_correction01/round108_decisions.py` retains the
original source; `review/reader_correction_review01.json` binds its SHA and the
accepted corrected SHA to the original candidate identity. Seventeen original
and nine independent finite counterexamples passed without a solver.

`engineering/reader_corrections01/history.json` indexes five actual full-reader
attempts, their exact sources, stderr/stdout SHA, durations and exit codes.
The successful fifth attempt reads the final per-call native log bound only
after its matching successful NEJ return; callback maxima alone can omit a
terminal OPTIMAL bound. Saved model SHA, original integer native preconditions,
actual optimize status/log and return sequence qualify that proof. Conditional
scope bounds use their original cutoff for proof qualification, while the
published raw L and signed gap remain unchanged. The actual shared interval
writer encodes G domain in Bounds and does not require redundant explicit G
rows; true-G cap/floor and objective cutoff rows are still checked. Original
`overall_global_deadline` with the exact time-limit status and valid open
coverage is a normal finite-window result. Reader failures do not justify
discarding or rerunning those performance arms.

The independent proof audit also retains 26 synthetic zero-solve cases for
conditional and chronological coverage, actual model scopes and conservative
witness-time offsets. The deterministic role-order correction preserves its
exact old source and changes only public table ordering. Subsequent independent
reviews bind any later source changes and actual raw audit receipts.

`engineering/reader_log_binding_correction01/comparison.json` records the exact
returned-call/log-path assertion added after independent review: all 28 then
published CSVs (825705 fields) and decisions remained unchanged. Twenty-five
additional independent finite cases cover returned scoped bounds and wrong-log
or future-evidence rejection, accepting the actual inherited Bounds-only G
domain while retaining cutoff/true-G row checks.

The first S12 prefix reader attempt also exposed the missing final returned
bound for cold P: the last callback bound was .22523739349916488, whereas the
actual OPTIMAL native final log/readback established .22524870597274965.
`engineering/confirmation_S12_reader01/` preserves that failed source, command,
stdout/stderr and 35.5805672-second exit-1 receipt. The second attempt passed
with an exact original reference matrix, unique integer full-model call,
matching native log, terminal status and successful return. The raw final bound
is corroborated by the printed native value; it is not replaced by rounded log
text. `returned_native_bounds.csv` publishes this separate provenance.
`review/cold_final_bound_review01.json` accepts the correction and 20 additional
finite cases. Independent S12 audit source/failed attempt and successful raw
reconstruction likewise remain public. No native performance was repeated.

B24's first independent prefix audit assumed every role exposed a partial-target
MIP and two Starts. Its actual root/child LP evidence showed no strict
disjunction gain, so the original controller took three LPs directly to one
terminal MIP and one Start. The failed audit source/command/exit receipt and
actual-path repair are retained. The independent proof store keeps the strongest
already available bound only for the same call, true-G domain and cutoff;
every raw event is still checked. Fifty finite prefix/interval cases validated
this storage equivalence without any solver. Independent B24 review accepted
the actual models, Starts, physics, coverage, all prefix endpoints and frozen
continuation with no production change or performance rerun.

L48 naturally exposes the original multi-leaf lifecycle: an infeasible right
half permits the original contraction, the remaining L0.0 receives an AM
split into two relevant leaves, two next-leaf target MIPs return after reaching
their original bound targets, and a terminal MIP closes L0.0.1. Each ENS-series
arm has seven LPs and three integer MIPs, with two submitted Starts and one
outside-true-G-scope mapping skip. These are inherited controller actions,
not a forced split, changed AM threshold or R107 assignment-event experiment.

The first L48 primary reader rejected the inherited next-leaf native-bound
source label; its source/command/52.6774423-second exit-1 receipt are retained.
The second still treated a saved status=open leaf as an unresolved obligation
although its independently supported full-scope bound excluded improvement
of the final physical U; its exact source and 51.0442075-second exit-1 receipt
are retained. The repaired reader qualifies the next-leaf bound through its
same-leaf successful native call, model domain, original cutoff and chronology,
and discharges an open leaf only after full-partition proof validation.
Unsupported, future or wrong-scope evidence remains invalid. The third and
fourth attempts passed in 86.1488919 and 85.9749072 seconds. The fourth separates
child-bound and next-leaf target subcounts while including both as partial
MIPs. `engineering/next_leaf_reader_correction01/comparison.json` confirms
28 other CSVs / 1286668 fields and all decision JSONs unchanged between those
two successful rebuilds. No engine performance was repeated.

### Actual F5 independent Start normalization correction

The primary through-F5 reader passed unchanged: engineering/confirmation_F5_reader01, exit 0, 116.241156000062 seconds, source SHA 52cadcf5ff7ce5fcfb1f828efd1a81a1c4d14d5e31d9b6b72963f7348e8408c1. Independent confirmation_F5_raw_audit01 failed its extra source-car-number assertion. Its original source, command, explicit root, failure and receipt remain available. The cause was an omitted inherited normalizeRound61Routes call before mapVerifiedRoutesToCanonicalModel: nonempty routes are stably sorted by descending operation count inside each exact Q class, then assigned ascending vehicle IDs. F5 source cars 2 and 0 have equal capacity and 15/11 operations, so that old normalization swaps their labels while preserving every operation, final inventory and physical objective.

The actual corrected independent command was:

```
D:/msys64/ucrt64/bin/python.exe results/unified_exact_round108/review/campaign_raw_audit01.py --root E:/codes/ExactEBRP-round108 --through F5
```

Audit02 passed 5,837,423 checks, exit 0 in 93.1919237000402 seconds; source SHA b396a25769ee4812f337e7c5839db6888d06d729663927c14d8c6a7a7c017987; audit SHA 074f2c07544c5e9ce15000660812f82f2faafe1780469d0f50d9e9a71eeed25e. It matches complete x/conn/z/mode/p/d/load/ord/Y/state/G values to the precisely normalized own fleet, and checks all native vector columns/types/bounds/rows/objective. Twenty-four synthetic finite cases passed in 0.134753499995 seconds with actual source/call-site inheritance bindings (review/start_normalization_finite01). Final F5 review is ACCEPT, SHA 2dc1dc79699edc36b3020ea15755915928706dcade6c28306da94e4edbf6ba35. This was an independent evidence-reader correction only: no production, frozen helper, primary reader, decision rule or native performance rerun changed.
## Final N36 group and complete primary reconstruction

The original serial N36 wrapper (session 7055) returned exit 0 at 2026-10-08 19:25:49 UTC. All three arms returned normally, with no performance retry or cancellation. The M-B legacy completion reports 5370.405999999959 seconds, while the separately retained full observation receipt includes postexit evidence/accounting and reports 5371.085680300021 seconds. The final tables use the latter complete observation time, as for all other formal arms.

The actual final reconstruction command was:

```text
D:/msys64/ucrt64/bin/python.exe scripts/round108_engineering.py --source-root E:/codes/ExactEBRP-round108 --receipt-root E:/codes/ExactEBRP-round108 --label confirmation_N36_reader01 --script round108_reader.py --timeout 1800 -- --root E:/codes/ExactEBRP-round108 --out E:/codes/ExactEBRP-round108/results/unified_exact_round108/reports_final
```

Its measured engineering duration was 126.13462640007492 seconds, exit code 0, with reader source SHA256 `52cadcf5ff7ce5fcfb1f828efd1a81a1c4d14d5e31d9b6b72963f7348e8408c1`. The exclusive launch/source snapshots/stdout/stderr/receipt are in `engineering/confirmation_N36_reader01/`. It rebuilt 21 formal arms and 3 functional qualification arms, 961 own physical UB records, 100 actual Optimize calls and returns, 68 canonical models, and 30 submitted Starts. Corrected fees are 46 conservative starts and 47514.073242100014 outer seconds. Failed formal arms, cancellations, IIS and route-oracle calls are all zero.

N36's independently recomputed primary-reader own U/L values are P 0.28697503167264493 / 0.15003601758156443, ENS 0.18251247295488404 / 0.15323711693023456, and M-B 0.18903343435886416 / 0.1530742203952435. All remain uncertified. Both ENS and M-B actually expose three original LPs, one original child-bound partial target and one root terminal MIP, with maximum one open relevant leaf and no actual multiactive-leaf split. Their original controller target/call journals are retained; the extra target call must not be inferred away from terminal logs.

The raw-rebuilt selection is `SELECT_MB_FOR_BROAD_EVALUATION`: S12/B24/L48/N36 are respectively TIE/WIN/WIN/WIN versus P. All seven P pairs are evaluable, with six WIN and S12 TIE and no severe P regression. ENS losses occur at F2, F5 and N36; F5 is a severe ENS regression. Completed local and isolated-public audits and actual recovery receipts are recorded separately below.

## Completed local independent audit and public packaging correction

The final local standalone source was `47cb299f4a8844ca668fab0117b035076f760041fb44ba6c4be0cd751af15adc`. Its actual through-N36 audit returned ACCEPT, exit 0 in 101.20076569996309 seconds. The serialized audit recorded 6,510,517 checks; its console recorded two additional post-serialization source/audit identity read guards. Those guards are metadata checks, not extra native calls. The audit SHA is `464a56660ab90f4e852f2ef6bc8c4a7c9614674e91c83dbb5900a7be0f9cf5fa`; sealed local final review SHA is `70fa0f323c088b68a05169b5eca22444703154b2524bb843ca8717f939a8f636`. Local final acceptance did not claim the later public recovery had happened.

Actual first packaging attempt `engineering/public_pack01` failed only the preregistered strict single-blob size gate, exit 1 after 67.64884240005631 seconds. The original compressed file was 150,926,168 bytes, SHA `135ecdc4769cc9c8beaa237a9eb42778ce243e91e73e96ef45ab33e46e2c1556`, source `dfcaa2409e9f684bd8375977100f7458aad2d68e5aed32a8bcd1f5f6517d071b`. The exact original archive remains local in `compact_evidence_failed01`. Its source, commands, receipts, diagnostics and all 79,111 original plain-member names/sizes/hashes were preserved in `engineering/pack_oversize01` and are inside the final public carrier. The oversized combined file itself is not published as a Git blob.

The first exact-part implementation, source `62333f124a980e1abe07adda886f389aecc872fde67d89ada5483c0a58be636d`, failed an actual finite dependency-path escape test before any actual public export. `review/packaging_boundary_probe01` retains that source, case, command and exit-1 HOLD receipt. The repaired public tool, source `c35f285d76dbfba1ca16e4d73bd670de603b868337095b563eeda3e0f5786ce3`, validates every dependency and target inside the declared roots, rejects aliases/symlinks, binds the actually executed public restorer and validates all part/member hashes. Forty-nine actual finite cases passed in 5.611692 seconds, including split and unsplit export/restore, CRLF preservation, missing/extra/reordered/wrong-path parts, index/offset/gap/overlap/size/hash failures, wrong source/reader identity, the original escape and three exercised Windows symlink refusals. The sealed packaging review is `review/packaging_exact_parts_review01.json`, SHA `d4e08f903ed2f77d601580f7c0cf90e32b8a890cb86ea1f0a985df3771aa1eaa`. These are evidence-packaging repairs, with no production, performance, candidate or selection-rule change.

## Actual fresh public export, recovery and all-field reconstruction

Both destination directories were verified absent before the actual runs. Export used `E:/round108-public-export-20261009-v1`; restoration used the distinct new directory `E:/round108-public-recovered-20261009-v1`. The latter is the explicit read root of both completed raw reconstructions. The local carrier combined file is 155,012,329 compressed bytes, SHA `9ae11d97e81f9434b7ac438fe32d61341e8712ea6e1d6699b7030fa0b0f347d8`, with 79,898 plain members and 15 exact historical dependencies. Manifest SHA is `214bdc55cb827d7189e73525b5a954c8fd7a3ad2bdae985542a58e8e9e455cbb`.

| Public compressed-byte part | Offset | Bytes | SHA256 |
|---|---:|---:|---|
| evidence.tar.gz.part001 | 0 | 94371840 | 006160e7a28f2d35d0171e8b4512969af19950b20e9d17de3d69687b6848f01e |
| evidence.tar.gz.part002 | 94371840 | 60640489 | 3fc3b631245cea9649c2190583c3d268f4dbcc6b05ca83d5b3135e6876486774 |

The following actual commands completed with exit code 0. Durations below are enclosing engineering-wrapper observations, not solver fees:

```text
D:/msys64/ucrt64/bin/python.exe scripts/round108_engineering.py --source-root E:/codes/ExactEBRP-round108 --receipt-root E:/codes/ExactEBRP-round108 --label public_pack02 --script round108_public.py --timeout 3600 -- pack --root E:/codes/ExactEBRP-round108
D:/msys64/ucrt64/bin/python.exe scripts/round108_engineering.py --source-root E:/codes/ExactEBRP-round108 --receipt-root E:/codes/ExactEBRP-round108 --label public_export01 --script round108_public.py --timeout 1800 -- export --root E:/codes/ExactEBRP-round108 --out E:/round108-public-export-20261009-v1
D:/msys64/ucrt64/bin/python.exe scripts/round108_engineering.py --source-root E:/round108-public-export-20261009-v1 --receipt-root E:/codes/ExactEBRP-round108 --label public_restore01 --script round108_public.py --timeout 1800 -- restore --public-root E:/round108-public-export-20261009-v1 --out E:/round108-public-recovered-20261009-v1
D:/msys64/ucrt64/bin/python.exe E:/round108-public-recovered-20261009-v1/scripts/round108_engineering.py --source-root E:/round108-public-recovered-20261009-v1 --receipt-root E:/codes/ExactEBRP-round108 --label public_rebuild01 --script round108_reader.py --timeout 1800 -- --root E:/round108-public-recovered-20261009-v1 --out E:/round108-public-recovered-20261009-v1/rebuilt --compare E:/round108-public-recovered-20261009-v1/results/unified_exact_round108/reports_final
```

| Engineering run | Complete observed seconds | Exit code |
|---|---:|---:|
| public_pack02 | 65.42337620002218 | 0 |
| public_export01 | 1.6295306999236345 | 0 |
| public_restore01 | 42.37286920007318 | 0 |
| public_rebuild01 | 356.2101506999461 | 0 |

The restore child executed the copied public script with cwd/source root equal to the export directory; its actual receipt reports `public_files_only=true` and `original_workspace_reads=false`. The rebuild child executed the restored reader (source `52cadcf5ff7ce5fcfb1f828efd1a81a1c4d14d5e31d9b6b72963f7348e8408c1`) with cwd and payload read root equal to the recovered directory. The enclosing wrapper only writes source snapshots and engineering receipts in the original delivery directory. It does not supply raw evidence to the child.

All 30 published CSV file sets, row counts and 1,313,668 field values matched. Every value and file set in all four JSON files matched: `admission_decision.json`, `continuation_decision.json`, `selection_decision.json` and `summary.json`. The separately published root admission and selection also match the fresh rebuild. There was no summary-copy reconstruction or original-worktree fallback. Actual metadata is in `engineering/public_rebuild01`, `public_comparison_receipt.json` (SHA `5addfd63ad1ab35309af334c6fdd7f405fa236f76d60cd56c8bbb18b620db682`) and the exact restored receipt copy `public_restore_receipt.json` (SHA `c74f401c7408df8abe8e3a0e27962a3337d2e23148e777879ad13dd51b8d2b7b`).

## Actual standalone independent public mathematics

The independent reviewer executed the restored standalone source, with cwd and read root in the recovered directory:

```text
D:/msys64/ucrt64/bin/python.exe results/unified_exact_round108/review/campaign_raw_audit01.py --root E:/round108-public-recovered-20261009-v1 --through N36 --isolated-public-math --out E:/round108-public-recovered-20261009-v1/results/unified_exact_round108/review/public_isolated_raw_audit01
```

The actual audit returned ACCEPT, exit 0, in 320.8277053999482 seconds. Its serialized audit records 6,510,514 checks and 77,281 explicit-root evidence bindings; audit SHA is `de43845f9435b3302aca17a6325c143126cf725691fc0fe7cd74b3564da0df6d`. This mode-specific count includes public restoration/identity metadata and omits local PE/DLL byte rehashes; it is not an engine experiment or a claim of additional native calls. The audit independently recomputes own physical fleets/objectives/loads/durations, every reported UB, actual model VType/A/B and normalized Start vectors, native scope/chronological full-cover certificates, signed gaps, checkpoints, bridge, paired classifications, exact four-role eligibility, final selection and fees.

A separate fresh-root metadata/table crosscheck returned ACCEPT, exit 0, in 8.581683399970643 seconds, with 13,727 checks. It matched all 961 physical UB rows, 68 models, 100 started/returned native calls, 30 submitted Starts / 32 mapping attempts, 108 checkpoint rows and 12 reliable-Fstar rows. Crosscheck source SHA is `012f46c8926c7e0fb95a3acf652d33cd5b427205ec8367968f891c0d52de93d9`; output SHA is `081ca3a7a8db46fa9b252d045cbcbb9735327c76f9d747deee529fbc10a69a86`. All raw-audit evidence reads were in the recovered root. Completed primary comparison/restore/run metadata was copied there byte-exactly as a new supplement for final review, without changing carrier members or rebuilt outputs.

The independent raw audit, source-at-execution, launch/exit/time receipts, per-arm chronology, separate crosscheck and sealed `review/public_isolated_review01.json` / `.md` are separately public supplements. Final narrative and publication receipts are also supplements, avoiding a circular carrier of its own hash. No native environment, Optimize, LP solve, IIS, compiler, PE/DLL distribution or independent performance rerun occurs in this public reconstruction.
