# G1 identity and rejection checks only; every command stops before Optimize.
string(RANDOM LENGTH 16 ALPHABET 0123456789abcdef suffix)
set(out "${OUTPUT_ROOT}/round92_cli_${suffix}")
if(EXISTS "${out}")
  message(FATAL_ERROR "Refusing to overwrite Round92 qualification artifacts")
endif()
file(MAKE_DIRECTORY "${out}")
execute_process(COMMAND "${EXACT_EXE}"
  --input "${out}/missing-input.txt" --method gcap-frontier
  --algorithm-preset research-round83-vds-equal-net-exchange
  --round92-handling-activation true --out "${out}/candidate.json"
  RESULT_VARIABLE candidate_code OUTPUT_FILE "${out}/candidate.stdout.log"
  ERROR_FILE "${out}/candidate.stderr.log" TIMEOUT 10)
if(candidate_code EQUAL 0 OR NOT EXISTS "${out}/candidate.json")
  message(FATAL_ERROR "Candidate emergency path failed; artifacts=${out}")
endif()
file(READ "${out}/candidate.json" candidate)
string(JSON identity GET "${candidate}" algorithm_preset)
if(NOT identity STREQUAL "research-round92-ensc-rounded-handling-activation")
  message(FATAL_ERROR "Candidate emergency identity mismatch; artifacts=${out}")
endif()
execute_process(COMMAND "${EXACT_EXE}"
  --input "${out}/missing-input.txt" --method gcap-frontier
  --algorithm-preset research-round83-vds-equal-net-exchange
  --out "${out}/control.json"
  RESULT_VARIABLE control_code OUTPUT_FILE "${out}/control.stdout.log"
  ERROR_FILE "${out}/control.stderr.log" TIMEOUT 10)
if(control_code EQUAL 0 OR NOT EXISTS "${out}/control.json")
  message(FATAL_ERROR "Control emergency path failed; artifacts=${out}")
endif()
file(READ "${out}/control.json" control)
string(JSON control_identity GET "${control}" algorithm_preset)
if(NOT control_identity STREQUAL "research-round83-vds-equal-net-exchange")
  message(FATAL_ERROR "Default-off identity changed; artifacts=${out}")
endif()
foreach(other --round88-constructive-only-descent --round89-native-ot-b1
              --round90-lp-g-split)
  string(REPLACE "--" "" label "${other}")
  execute_process(COMMAND "${EXACT_EXE}"
    --input "${out}/missing-input.txt" --method gcap-frontier
    --algorithm-preset research-round83-vds-equal-net-exchange
    --round92-handling-activation true "${other}" true
    --out "${out}/${label}.json"
    RESULT_VARIABLE code OUTPUT_FILE "${out}/${label}.stdout.log"
    ERROR_FILE "${out}/${label}.stderr.log" TIMEOUT 10)
  file(READ "${out}/${label}.stderr.log" error)
  if(code EQUAL 0 OR NOT error MATCHES "Round92 handling activation requires isolated")
    message(FATAL_ERROR "Round92 accepted incompatible ${other}; artifacts=${out}")
  endif()
endforeach()
message(STATUS "Round92 CLI identity and combination gates PASS; artifacts=${out}")
