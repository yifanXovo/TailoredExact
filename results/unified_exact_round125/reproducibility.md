# Round125 reproduction scope

The deliverable is the full [manuscript](manuscript.md), [model and proof appendix](model_appendix.md), and [algorithm appendix](algorithm_appendix.md). [method_spec_matrix.csv](method_spec_matrix.csv) maps actual enabled families and decisions to those definitions and the frozen implementation. It is an audit map, not a substitute for the definitions.

## Immutable authorities and unchanged experiment layer

The base is R124 head `8d80a6f46b49f97bf082b074e20941699de27fe4` (science `d1e03b180e3f3a9b2af48053f2200a5cb9c83b53`). Its historical COMPLETE / READY_FOR_ADVISOR_REVIEW label remains in the original record. Round125 adds a stricter self-contained-method assessment; improved prose supplies no new computational contribution evidence.

Production source-before-native remains `355eefd2be3fe5651195681faf7b3a63ee4032f8`. All 216 file bindings were compared with the sparse worktree or its HEAD blob; the compact [binding ledger](evidence/production_bindings.json) records the hashes and access levels. No production file was edited. The executable SHA256 is `5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba`; Gurobi 13.0.2 DLL SHA256 is `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`. Neither binary is copied into this package.

All six files in [tables](tables/complete_results.md) are byte-identical to R124; [unchanged_tables.json](checks/unchanged_tables.json) records that limited check. They retain all 32 R122 arms, 48 directed pairs, three R123 endpoints, unknown checkpoints, negative/MIXED results, signed gaps and all published clocks. There is no new 32/48/3 campaign audit. R124's original derivation remains its authority. Literature reading levels and citations are inherited, with no new broad literature search or redistributed paper PDFs.

## Bounded executable checks

Run, using Python 3.10 or later and only its standard library:

```text
python checks/finite_checks.py
```

The script reads only this directory's compact evidence, performs rational inequalities, reconstructs 64 distinct saved algebra templates, computes finite controller states, and replays fixed already-declared physical moves. It writes [finite_results.json](checks/finite_results.json) and [template_coverage.csv](checks/template_coverage.csv). It cannot call a solver, load a native library, compile production, or run H. Its duration is its own wall time, not a new solver time point.

The arithmetic includes spread/centering, SP, cutoff, integer handling, Big-M deactivation, implicit service/A/B, S=0, empty and heterogeneous-route boundaries, and counterexamples when required premises are removed. These small finite examples support, but do not replace, the analytic proofs. The decision adapter consumes explicit returns and tests incomplete/invalid results, partial TimeLimit, missing Start, target returns, complete atomic replacement, and one/both infeasible children. This is a second implementation of the documented rules, checked against the pure C++ source by independent review; it does not execute or compile that C++ function.

The matrix authority is one already-saved R123 M-B LP, `L0.0.0.0_epoch_0_generation_6.lp`, SHA256 `086c6ba3c5890b993449ef8b10aa9807e125c49b77e1dc39e637fdeb8959c564`. The script independently reconstructs coefficients, selected domains and VTypes from the input and documented formulas, then compares compact literal row excerpts. [matrix_samples.json](evidence/matrix_samples.json) includes source bytes/hash, interval and cutoff. The full 16.9 MB LP is not redistributed. Seven conditional source mappings are explicitly unsampled in this selected open leaf: unreachable singleton, pair/triple cover, required pickup/drop, domain-infeasibility and numerical-closure rows. Their triggers are absent here; this does not claim their bytes are absent everywhere in history. Their source generation and analytical/numerical premises were reviewed separately. No exporter was run and no historical carrier was expanded to fill these cases. This is sampled algebra validation, not full-matrix reproduction.

The physical replay uses exactly three saved accepted joint insertions and one saved neutral relocation. It checks inventory, unique service, prefix/return loads, complete duration, original objective and the full sorted duration tuple. Saved descent acceptance and one exhausted pass are checked separately. No candidates are searched, no route is improved by this check, and the replay is not a new heuristic outcome. The AM calculation uses one saved R123 decision. [provenance.json](evidence/provenance.json) binds all selected input and trajectory files to the existing native record.

The extraction switch `--extract` is for the original author's already-present R123 worktree only. It reads the one named LP as text and copies the fixed compact trace list; portable reproduction uses the default mode. No extraction switch is needed for public reconstruction.

## Independent review and known limits

The independent reviewer first received only the three manuscripts and sealed its questions before source access. Its second pass checked actual argv/presets, enabled writer/controller/H paths, and finite samples. Corrections and disposition are in [review_actions.md](review_actions.md). The review directory contains the separate reports, an independent bounded check script and its receipt. That script can rerun its 11 bounded cases using saved source excerpts; revalidation against the complete frozen source requires the checkout. The excerpt fallback does not extend its source coverage.

The raw scheduler does not clip L to U; the exact complement proof and actual numerical storage are distinguished. Post-seal certification uses a two-sided signed-gap policy that is stronger than the native predicate. Numerical penalty closure does not prove rational infeasibility of arbitrarily small improvements. H equivalent-key heap/sort order depends on the frozen C++ library; portable implementations may follow different valid paths. Neither finite tests nor detailed proofs establish family-level runtime gains, firstness, acceptance, exact cross-language trajectories, or a global accumulated floating-point error bound.

## Publication and resource boundary

Science commit A carries these lightweight documents, finite check source, compact evidence and a SHA256/size manifest. An anonymous public raw-file reconstruction into a fresh directory validates the actual published A bytes, reruns the portable check and compares JSON as typed JSON, excluding only its elapsed wall time. Review/public-rebuild/cleanup receipts are committed afterward in B; A does not claim to prove its future verification. A single export is enough; the manifest excludes itself and later receipts to avoid recursive self-certification.

The main entry is `E:\codes\ExactEBRP`; all new work and intermediate files are under `E:\codes\ExactEBRP-work`. A sparse linked worktree reuses the existing object store. Git writes disable automatic maintenance for that command only. No shared objects, old worktrees or user files are cleanup targets. The three pre-existing dirty files are hash-protected. Checks are bounded read-only mathematics and small document/script writes. New formal arms, optimizer processes, LP/MIP/CP/DP Optimize calls, production compilations, H searches and production changes are all zero. Publication receipts record measured check/rebuild intervals; agent reasoning, human and network waiting are not invented as machine CPU time.
