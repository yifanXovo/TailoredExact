# Thin reviewer request interface

The reviewer has not signed admission. `admission_request.json` supplies:

```json
{
  "production_PE_path": "build/research/<final-build>/ExactEBRP.exe",
  "actual_PE_header": {"magic": 523, "stack_reserve": 2097152, "stack_commit": 4096, "machine": 34404},
  "remaining_formal_overhead_seconds": 1800,
  "artifacts": {
    "qualification_plan": {"path": "...", "SHA": "..."},
    "parser_equivalence": {"path": "...", "SHA": "..."},
    "main_entry": {"path": "...", "SHA": "..."},
    "finite_regressions": {"path": "...", "SHA": "..."},
    "evidence_policy": {"path": "...", "SHA": "..."},
    "repair_evidence": {"path": "...", "SHA": "..."}
  }
}
```

Each referenced artifact has `raw_bindings` (relative path to SHA). The checker
reads those actual raw files, not only status booleans. Schema adjustments to
match actual tool records are welcome before final signature; no scientific
predicate may change from seeing performance.

`qualification_plan`: `conservative_starts`, `outer_cap_seconds`.

`parser_equivalence`: `passed`, `integer_fields_exact`,
`binary64_fields_bitwise_equal`, authority exactly
`same-toolchain-original-and-fixed-C++-Parser`, `Optimize:0`, `roles` in the
original 12 order, `old_mathematical_dump`/`new_mathematical_dump` (path-free,
byte-identical native dump records), `finite_payload_cases_passed`,
`metadata_paths_separate`.

`main_entry`: `passed`, `Optimize:0`, `heuristic_calls:0`, `oracle_calls:0`,
`groups` each with actual `command`, `production_PE_SHA`, `returncode`,
`phases` CSV path, `original_names`, and `path_mapping` records containing
`original_path`, `mapped_path`, `SHA`. A receipt/dump is bound by `raw_bindings`.

`finite_regressions`: `passed`, `Optimize:0`, `native_environment:0`, `subjects`
booleans named `actual_Seed1`, `actual_P15`, `actual_P17`, `missing_return`,
`nonnegative_floor`, `unknown_clock`, `interval_thresholds`,
`mechanism_correction01`, with actual source/launch/exit/audit raw bindings.

`evidence_policy`: `uniform_all_methods`, `raw_flags_preserved`,
`new_calls_bind_own_models`, `reject_all_damaged_call_lower_claims`,
`withdraw_necessary_dependent_closures`, `unknown_new_fault_pauses`,
`floor_requires_own_objective_proof`, `missing_exact_clock_is_null` all true.
Include the concrete predicates/proofs and their finite rejections, not just
these indexing flags. Current-call adjudication is separately reviewed.

`repair_evidence`: `changed_production_files`, `only_entry_engineering`,
`math_search_unchanged`, `compiler_flags_match_inherited`, `actual_PE_header`.
Bind old Parser snapshot/diff, new source, build commands/flags/toolchain and
actual executable header. Reviewer checks scientific equivalence directly.

Five functional qualification raws retain `qualification/cli01/identity.json`
and `qualification/identity.json`, launch/panel/native journal schema, and
all-column model/Start native evidence. All fee launches set `qualification`
explicitly, and every fee has a closed `receipt.json`. No prepaid R109 slots
are reused. Inherited reference path/hash/build metadata are present under
the current root; copy only needed shared historical dependencies.
