# Minimal production change

Measured source is `d0014a716` on base `ded38c756a32a464bfa9800212da75778707d974`.
The initial implementation is `0b2b990e2`; the following five-line repair
preserves the effective P-S identity in the final run-config snapshot. Neither
commit contains the later scientific results or future public receipts.

* One default-false `SolveOptions` flag and a strict plain-gurobi CLI allowlist.
* One optional paid-start pointer on the baseline and its disabled-native stub.
* The main entry copies options for H, applies the original R83 preset, keeps
  original startup Seed20260626, performs the existing physical H diagnostic,
  writes its required exclusive checked evidence, then calls original compact.
* Baseline revalidates H before journaling/retaining it, handles own zero and
  exhausted work window, and submits one complete Start after original model
  construction/domain checks. Original absolute remaining time is queried again
  at Optimize. No extra LP, presolve diagnostic, hints, cut or target is added.
* `Round112CompactStart.inc` captures all actual numeric/name metadata, maps and
  validates all columns/rows/objective, calls the full Start API once, reads it
  back and captures the same matrix afterward. Its required failure is fatal
  to this paid-start path. The existing callback only observes matching vectors.
* The mapper separately rejects duplicate IDs and supports explicit empty cars;
  it retains original unequal-Q IDs and the inherited equal-Q normalization.
* CMake adds a build-only finite reference batch target. Its eight original
  exports read native model metadata and perform zero Optimize.

The original compact writer, original exhaustive-block strategy, physical
evaluator, R83 H implementation and ENS/M-B solve paths are unchanged. All four
formal methods use the new PE; old binary results supply historical context
only. Exact old/new source hashes, compiler/stack/PE/DLL identities and complete
CLI/helper bindings are saved separately. Default ENS remains unchanged.
