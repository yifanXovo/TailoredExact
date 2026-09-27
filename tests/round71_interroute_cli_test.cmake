# Exercise the real preset, native startup, exact controller and certificate.
# A successful heuristic alone must not pass this regression test.
string(RANDOM LENGTH 16 ALPHABET 0123456789abcdef suffix)
set(out "${OUTPUT_ROOT}/round71_cli_${suffix}")
if(EXISTS "${out}")
  message(FATAL_ERROR "Refusing to replace a prior test artifact")
endif()
file(MAKE_DIRECTORY "${out}")
execute_process(COMMAND "${EXACT_EXE}"
  --input "${SOURCE_ROOT}/tests/data/round59_tiny.txt"
  --lambda 0.15 --T 3 --pickup-time 0 --drop-time 0
  --time-limit 24 --process-wall-time-limit 30 --process-shutdown-margin 3
  --threads 1 --mip-threads 1 --gurobi-seed 0 --gurobi-presolve -1
  --method gcap-frontier --algorithm-preset research-round71-vds-interroute-descent
  --round61-candidate-mode off --round65-witness-audit true
  --round65-hga-zero-stop true --out "${out}/result.json"
  --log "${out}/native.log" --external-gini-artifact-dir "${out}/external"
  --primal-heuristic-generation-log "${out}/hga.csv"
  RESULT_VARIABLE exit_code OUTPUT_FILE "${out}/stdout.log"
  ERROR_FILE "${out}/stderr.log" TIMEOUT 40 WORKING_DIRECTORY "${SOURCE_ROOT}")
if(NOT exit_code EQUAL 0)
  message(FATAL_ERROR "Real DS-X CLI failed: ${exit_code}; artifacts=${out}")
endif()
file(READ "${out}/result.json" result)
foreach(field strict_certified_original_problem decoded_descent_complete decoded_descent_cross_route_enabled
    external_gini_tree_root_coverage_valid external_gini_tree_parent_child_coverage_valid
    external_gini_tree_backend_parameter_roundtrip_valid)
  string(JSON value GET "${result}" "${field}")
  if(NOT value)
    message(FATAL_ERROR "DS-X CLI did not establish ${field}; artifacts=${out}")
  endif()
endforeach()
string(JSON mode GET "${result}" hga_stop_mode)
string(JSON seeds GET "${result}" decoded_descent_seeds_completed)
string(JSON generations GET "${result}" hga_total_generations)
string(JSON upper GET "${result}" upper_bound)
string(JSON lower GET "${result}" lower_bound)
if(NOT mode STREQUAL "decoded-descent-interroute" OR NOT seeds EQUAL 24 OR NOT generations EQUAL 0
    OR upper LESS 0.208333233333 OR upper GREATER 0.208333433334
    OR lower LESS 0.208333233333 OR lower GREATER 0.208333433334)
  message(FATAL_ERROR "DS-X CLI mode/seed/original-objective mismatch; artifacts=${out}")
endif()
file(STRINGS "${out}/external/paper_optimize_ledger.csv" ledger)
list(LENGTH ledger rows)
math(EXPR calls "${rows} - 1")
if(calls LESS 1)
  message(FATAL_ERROR "DS-X CLI never entered the exact backend")
endif()
file(GLOB starts "${out}/external/*.round68.start.json")
if(NOT starts)
  file(GLOB_RECURSE starts "${out}/external/*.round68.start.json")
endif()
if(NOT starts)
  message(FATAL_ERROR "DS-X CLI did not exercise a native Start decision")
endif()
message(STATUS "Round71InterrouteCliTests: real CLI certificate5/24; Optimize calls=${calls}; artifacts=${out}")
