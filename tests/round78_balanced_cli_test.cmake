# Run the actual balanced preset; inherited R76/R75 tests are same-build controls.
string(RANDOM LENGTH 16 ALPHABET 0123456789abcdef suffix)
set(root "${OUTPUT_ROOT}/round78_balanced_cli_${suffix}")
if(EXISTS "${root}")
  message(FATAL_ERROR "Refusing to replace prior qualification artifacts")
endif()
foreach(arm BDS-C)
  set(out "${root}/${arm}")
  file(MAKE_DIRECTORY "${out}")
  set(preset research-round78-vds-balanced-descent)
  execute_process(COMMAND "${EXACT_EXE}"
    --input "${SOURCE_ROOT}/tests/data/round59_tiny.txt"
    --lambda 0.15 --T 3 --pickup-time 0 --drop-time 0
    --time-limit 24 --process-wall-time-limit 30 --process-shutdown-margin 3
    --threads 1 --mip-threads 1 --gurobi-seed 0 --gurobi-presolve -1
    --method gcap-frontier --algorithm-preset "${preset}"
    --round61-candidate-mode off --round65-witness-audit true
    --round65-hga-zero-stop true --out "${out}/result.json"
    --log "${out}/native.log" --external-gini-artifact-dir "${out}/external"
    --primal-heuristic-generation-log "${out}/hga.csv"
    RESULT_VARIABLE code OUTPUT_FILE "${out}/stdout.log"
    ERROR_FILE "${out}/stderr.log" TIMEOUT 40 WORKING_DIRECTORY "${SOURCE_ROOT}")
  if(NOT code EQUAL 0)
    message(FATAL_ERROR "Real physical closure preset failed: ${code}; artifacts=${out}")
  endif()
  file(READ "${out}/result.json" result)
  foreach(field strict_certified_original_problem decoded_descent_complete decoded_descent_cross_route_enabled
      external_gini_tree_root_coverage_valid external_gini_tree_parent_child_coverage_valid
      external_gini_tree_backend_parameter_roundtrip_valid)
    string(JSON value GET "${result}" "${field}")
    if(NOT value)
      message(FATAL_ERROR "Physical closure CLI did not establish ${field}; artifacts=${out}")
    endif()
  endforeach()
  string(JSON seeds GET "${result}" decoded_descent_seeds_completed)
  string(JSON generations GET "${result}" hga_total_generations)
  string(JSON upper GET "${result}" upper_bound)
  string(JSON lower GET "${result}" lower_bound)
  if(NOT seeds EQUAL 25 OR NOT generations EQUAL 0 OR upper LESS 0.208333233333
      OR upper GREATER 0.208333433334 OR lower LESS 0.208333233333 OR lower GREATER 0.208333433334)
    message(FATAL_ERROR "Physical closure native certificate/mode mismatch; artifacts=${out}")
  endif()
  file(READ "${out}/hga.csv.balanced/result.json" balanced)
  string(JSON exhausted GET "${balanced}" exhausted)
  string(JSON rejected GET "${balanced}" verification_failed)
  string(JSON deadline GET "${balanced}" deadline)
  if(NOT exhausted OR rejected OR deadline OR NOT result MATCHES "Round78 balanced descent")
    message(FATAL_ERROR "Balanced controller did not complete a verified descent; artifacts=${out}")
  endif()
  foreach(suffix initial final)
    if(NOT EXISTS "${out}/hga.csv.balanced/${suffix}.json")
      message(FATAL_ERROR "Balanced physical snapshot missing: ${suffix}")
    endif()
  endforeach()
  file(STRINGS "${out}/external/paper_optimize_ledger.csv" ledger)
  list(LENGTH ledger rows)
  math(EXPR calls "${rows} - 1")
  if(calls LESS 1)
    message(FATAL_ERROR "Physical closure CLI never entered native proof")
  endif()
  message(STATUS "Round78BalancedDescentCliTests ${arm}: certificate5/24; Optimize calls=${calls}; artifacts=${out}")
endforeach()
