# Exercise the Round88 research switch through the real ENS-C startup and
# complete exact certificate. A heuristic-only result cannot pass.
string(RANDOM LENGTH 16 ALPHABET 0123456789abcdef suffix)
set(out "${OUTPUT_ROOT}/round88_constructive_only_cli_${suffix}")
if(EXISTS "${out}")
  message(FATAL_ERROR "Refusing to replace prior qualification artifacts")
endif()
file(MAKE_DIRECTORY "${out}")
execute_process(COMMAND "${EXACT_EXE}"
  --input "${SOURCE_ROOT}/tests/data/round59_tiny.txt"
  --lambda 0.15 --T 3 --pickup-time 0 --drop-time 0
  --time-limit 24 --process-wall-time-limit 30 --process-shutdown-margin 3
  --threads 1 --mip-threads 1 --gurobi-seed 0 --gurobi-presolve -1
  --method gcap-frontier --algorithm-preset research-round83-vds-equal-net-exchange
  --round88-constructive-only-descent true
  --round61-candidate-mode off --round65-witness-audit true
  --round65-hga-zero-stop true --round60-hga-candidate-log "${out}/candidates.csv"
  --out "${out}/result.json"
  --log "${out}/native.log" --external-gini-artifact-dir "${out}/external"
  --primal-heuristic-generation-log "${out}/hga.csv"
  RESULT_VARIABLE code OUTPUT_FILE "${out}/stdout.log"
  ERROR_FILE "${out}/stderr.log" TIMEOUT 40 WORKING_DIRECTORY "${SOURCE_ROOT}")
if(NOT code EQUAL 0)
  message(FATAL_ERROR "Round88 real CLI failed: ${code}; artifacts=${out}")
endif()
file(READ "${out}/result.json" result)
foreach(field strict_certified_original_problem decoded_descent_complete
    decoded_descent_cross_route_enabled external_gini_tree_root_coverage_valid
    external_gini_tree_parent_child_coverage_valid
    external_gini_tree_backend_parameter_roundtrip_valid)
  string(JSON value GET "${result}" "${field}")
  if(NOT value)
    message(FATAL_ERROR "Round88 CLI did not establish ${field}; artifacts=${out}")
  endif()
endforeach()
string(JSON preset GET "${result}" algorithm_preset)
string(JSON seeds GET "${result}" decoded_descent_seeds_completed)
string(JSON generations GET "${result}" hga_total_generations)
string(JSON upper GET "${result}" upper_bound)
string(JSON lower GET "${result}" lower_bound)
if(NOT preset STREQUAL "research-round88-ensc-constructive-only" OR
    NOT seeds EQUAL 1 OR NOT generations EQUAL 0 OR
    upper LESS 0.208333233333 OR upper GREATER 0.208333433334 OR
    lower LESS 0.208333233333 OR lower GREATER 0.208333433334)
  message(FATAL_ERROR "Round88 candidate identity/path/certificate mismatch; artifacts=${out}")
endif()
file(READ "${out}/hga.csv.exchange/result.json" closure)
string(JSON exhausted GET "${closure}" exhausted)
string(JSON rejected GET "${closure}" verification_failed)
string(JSON deadline GET "${closure}" deadline)
if(NOT exhausted OR rejected OR deadline)
  message(FATAL_ERROR "Round88 physical closure did not finish; artifacts=${out}")
endif()
file(STRINGS "${out}/external/paper_optimize_ledger.csv" ledger)
list(LENGTH ledger rows)
if(rows LESS 2)
  message(FATAL_ERROR "Round88 never entered native exact proof; artifacts=${out}")
endif()
file(READ "${out}/candidates.csv" candidates)
if(NOT candidates MATCHES "round88_constructive_only_decoded_descent_verified_improvement")
  message(FATAL_ERROR "Round88 candidate ledger lost research source identity; artifacts=${out}")
endif()
execute_process(COMMAND "${EXACT_EXE}"
  --input "${out}/missing-input.txt" --method gcap-frontier
  --algorithm-preset research-round83-vds-equal-net-exchange
  --round88-constructive-only-descent true --out "${out}/emergency.json"
  RESULT_VARIABLE emergency_code OUTPUT_FILE "${out}/emergency_stdout.log"
  ERROR_FILE "${out}/emergency_stderr.log" TIMEOUT 10 WORKING_DIRECTORY "${SOURCE_ROOT}")
if(emergency_code EQUAL 0 OR NOT EXISTS "${out}/emergency.json")
  message(FATAL_ERROR "Round88 emergency identity fixture did not fail safely; artifacts=${out}")
endif()
file(READ "${out}/emergency.json" emergency)
string(JSON emergency_preset GET "${emergency}" algorithm_preset)
if(NOT emergency_preset STREQUAL "research-round88-ensc-constructive-only")
  message(FATAL_ERROR "Round88 emergency result was misattributed; artifacts=${out}")
endif()
execute_process(COMMAND "${EXACT_EXE}"
  --input "${SOURCE_ROOT}/tests/data/round59_tiny.txt" --method gcap-frontier
  --algorithm-preset research-round73-vds-joint-seeded-descent
  --round88-constructive-only-descent true --out "${out}/invalid-preset.json"
  RESULT_VARIABLE invalid_code OUTPUT_FILE "${out}/invalid_stdout.log"
  ERROR_FILE "${out}/invalid_stderr.log" TIMEOUT 10 WORKING_DIRECTORY "${SOURCE_ROOT}")
file(READ "${out}/invalid_stderr.log" invalid_stderr)
if(invalid_code EQUAL 0 OR
    NOT invalid_stderr MATCHES "requires the ENS-C Round83 preset")
  message(FATAL_ERROR "Round88 switch accepted an incompatible preset; artifacts=${out}")
endif()
message(STATUS "Round88ConstructiveOnlyCliTests: one path, physical closure and certificate; artifacts=${out}")
