# Round84 recovery and review

All nine original runs and all listed offline producers are now complete.
Driver session19331 exited0, all nine per-run audits pass, and the campaign
lock is absent. Campaign/Start/replication audits pass; ten bundles verify twice
and all three first-layout figures pass visual review. Do not rerun a closed
producer. The commands below document the original completed workflow.
Read final_report.md and runtime_checkpoint.json for the closed state.

Owned checkout: E:/codes/ExactEBRP-round66. Base is R83 final
131d09280a1563243d0201e68367b26baf5079c3, draft PR144. Plan/protocol/original
driver were committed before launch at3dae75c03. The original nine-run queue
has already completed: do not run scripts/round84_research.py again.

The former exec session19331 is closed. campaign/active_experiment.json is
the retained last launch, not evidence of a live process. Read the complete
campaign/summary.json and driver_completion.json. PID48520 is only a historical
identity hint. The driver refuses an
existing campaign. It records each original command, affinity, observations,
completion and per-run physical/global audit, and stops on the first validity
failure. Keep raw artifacts and every attempt. A missing summary before the
first whole run exits is expected.

The measured source, both executables and qualification are inherited from
R83 without a rebuild. Source4496078f25c0cdad1cf7a5c39835fd23121e8978;
build/round83/v1/ExactEBRP.exe SHA256
25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e.
The exact qualified Windows working source bytes, including line endings,
are in R83's measured_source_bytes bundle. A Git blob can use different line
endings; do not silently replace measured bytes and retain the old hash claim.

The following offline producers were executed once in this order after all
original native processes closed and all nine per-run audits passed:

```powershell
$env:PYTHONUTF8='1'
& 'D:\msys64\ucrt64\bin\python.exe' 'scripts/round84_analyze.py'
& 'D:\msys64\ucrt64\bin\python.exe' 'scripts/round84_mechanism.py'
& 'D:\msys64\ucrt64\bin\python.exe' 'scripts/round84_replication.py'
& 'D:\msys64\ucrt64\bin\python.exe' 'scripts/round84_package.py'
& 'D:\msys64\ucrt64\bin\python.exe' 'scripts/round84_package.py' --verify-only
& 'E:\codes\ExactEBRP-round66\build\round81\plot_env\Scripts\python.exe' 'scripts/round84_plot.py'
```

Keep each producer's measured completion and failure records. Do not overwrite
completed output or rerun a native producer to repair a reader. Inspect all
three rendered figures before delivery. The inherited R83 empty-route-preserving
reader is round83_audit_v2.py; its failed predecessor remains historical evidence.

The final package comprises nine new complete run trees and one directory of
three zero-Optimize compact exports. Published R83 qualification, exact source
and startup diagnostic bundles are bound by hashes rather than regenerated or
charged again. Verification reads each archived member without extracting it.
Journal payloads and logs contain original absolute paths: direct replay uses
this original checkout or a deliberately reviewed path adapter; a relocation
alone is not an identical replay. No executable, license or credential is bundled.

A genuinely fresh replication needs its own explicit namespace, frozen plan
and charged allocation; editing OUT to bypass the existing-run guard is not a
continuation of the original queue. This R84 plan admits no extra seed, native
retry,7200s extension or next-stage confirmation. R84 remains development and
protection on exposed inputs. Overall acceptance remains pending.
