cmake_minimum_required(VERSION 3.20)
project(ExactEBRP LANGUAGES CXX)

option(EXACT_EBRP_ENABLE_GUROBI "Enable the optional local Gurobi backend" OFF)
set(GUROBI_ROOT "" CACHE PATH "Root of the local Gurobi win64 installation")

enable_testing()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
  add_compile_options(/W4 /permissive-)
else()
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

set(EXACT_EBRP_LIB_SOURCES
  src/Parser.cpp
  src/Evaluator.cpp
  src/Round73JointInsertion.cpp
  src/Round75QuantityDescent.cpp
  src/Result.cpp
  src/StrictCertificate.cpp
  src/ModelCorrectness.cpp
  src/FileSha256.cpp
  src/ProcessPhaseLedger.cpp
  src/NativeEvidenceJournal.cpp
  src/DenseProgress.cpp
  src/GurobiCertificate.cpp
  src/GurobiProgress.cpp
  src/MipStartMapping.cpp
  src/Round60Candidates.cpp
  src/Round61Candidates.cpp
  src/Round61TimeOracle.cpp
  src/Round62Passive.cpp
  src/Round62Thresholds.cpp
  src/Round63TimeResource.cpp
  src/Round64SharedResource.cpp
  src/Round65Projection.cpp
  src/ExternalGiniTree.cpp
  src/PaperExternalGiniTree.cpp
  src/Round48K1AMF.cpp
  src/Round49K1RC.cpp
  src/Round50IntervalMip.cpp
  src/PaperK1AmSf.cpp
  src/Round53CallbackIsolation.cpp
  src/InventoryRouteCuts.cpp
  src/InventoryRouteRootClosure.cpp
  src/PenaltyCoverSeparation.cpp
  src/Round51IntervalMip.cpp
  src/Round52TailoredCuts.cpp
  src/Round52GurobiCutAdapter.cpp
  src/ReplicaExternalGiniTree.cpp
  src/ConnectivityFlow.cpp
  src/Bounds.cpp
  src/ColumnPool.cpp
  src/TailoredExact.cpp
  src/Pricing.cpp
  src/Cuts.cpp
  src/Branching.cpp
  src/Master.cpp
  src/ColumnGeneration.cpp
  src/CplexBaseline.cpp
  src/TailoredBC.cpp
  src/TailoredBCCuts.cpp
  src/TailoredBCCallbacks.cpp
  src/TailoredBCCplexApi.cpp
  src/ControllingLeafScheduler.cpp
  src/GiniBranching.cpp
  src/GiniFrontierGeometry.cpp
  src/GiniEnvelopeRefinement.cpp
  src/GiniEnvelopeTailRepair.cpp
  src/GiniAdaptiveParametric.cpp
  src/StaticSegmentedGini.cpp
  src/IntervalRowFactory.cpp
  src/DispersionChildBound.cpp
  src/hga_tgbc/HgaTgbcGreedy.cpp
  src/HgaTgbcRunner.cpp
  src/Logger.cpp
  src/Round58Benchmark.cpp
)

if(EXACT_EBRP_ENABLE_GUROBI)
  find_path(GUROBI_INCLUDE_DIR gurobi_c.h
    HINTS "${GUROBI_ROOT}" "$ENV{GUROBI_HOME}"
    PATH_SUFFIXES include win64/include)
  if(NOT GUROBI_INCLUDE_DIR)
    message(FATAL_ERROR
      "EXACT_EBRP_ENABLE_GUROBI=ON but gurobi_c.h was not found. Set GUROBI_ROOT or GUROBI_HOME to the installed Gurobi win64 root; no fallback backend will be selected.")
  endif()
  list(APPEND EXACT_EBRP_LIB_SOURCES src/GurobiBaseline.cpp)
else()
  list(APPEND EXACT_EBRP_LIB_SOURCES src/GurobiBaselineStub.cpp)
endif()

add_library(exact_ebrp_core ${EXACT_EBRP_LIB_SOURCES})

add_executable(NativeEvidenceJournalTests tests/native_evidence_journal_tests.cpp)
target_link_libraries(NativeEvidenceJournalTests PRIVATE exact_ebrp_core)
add_test(NAME NativeEvidenceJournalTests COMMAND NativeEvidenceJournalTests)

if(EXACT_EBRP_ENABLE_GUROBI)
  target_include_directories(exact_ebrp_core PRIVATE "${GUROBI_INCLUDE_DIR}")
  target_compile_definitions(exact_ebrp_core PUBLIC EXACT_EBRP_ENABLE_GUROBI=1)
  if(GUROBI_ROOT)
    string(REPLACE "\\" "/" GUROBI_ROOT_NORMALIZED "${GUROBI_ROOT}")
    target_compile_definitions(exact_ebrp_core PRIVATE
      EXACT_EBRP_GUROBI_ROOT="${GUROBI_ROOT_NORMALIZED}")
  endif()
else()
  target_compile_definitions(exact_ebrp_core PUBLIC EXACT_EBRP_ENABLE_GUROBI=0)
endif()

add_executable(ExactEBRP src/main.cpp)
add_executable(Round66ArcLoadTests tests/round66_arc_load_tests.cpp)
target_link_libraries(Round66ArcLoadTests PRIVATE exact_ebrp_core)
add_test(NAME Round66ArcLoadTests COMMAND Round66ArcLoadTests)
add_executable(Round67LogStateTests tests/round67_log_state_tests.cpp)
target_link_libraries(Round67LogStateTests PRIVATE exact_ebrp_core)
add_test(NAME Round67LogStateTests COMMAND Round67LogStateTests)
add_executable(Round68StartTests tests/round68_start_tests.cpp)
target_link_libraries(Round68StartTests PRIVATE exact_ebrp_core)
add_test(NAME Round68StartTests COMMAND Round68StartTests)
add_executable(Round70DescentTests tests/round70_descent_tests.cpp)
target_link_libraries(Round70DescentTests PRIVATE exact_ebrp_core)
add_test(NAME Round70DescentTests COMMAND Round70DescentTests)
add_executable(Round71InterrouteTests tests/round71_interroute_tests.cpp)
target_link_libraries(Round71InterrouteTests PRIVATE exact_ebrp_core)
add_test(NAME Round71InterrouteTests COMMAND Round71InterrouteTests)
add_executable(Round75QuantityDescentTests tests/round75_quantity_descent_tests.cpp)
target_link_libraries(Round75QuantityDescentTests PRIVATE exact_ebrp_core)
add_test(NAME Round75QuantityDescentTests COMMAND Round75QuantityDescentTests)
add_executable(Round73JointInsertionTests tests/round73_joint_insertion_tests.cpp)
target_link_libraries(Round73JointInsertionTests PRIVATE exact_ebrp_core)
add_test(NAME Round73JointInsertionTests COMMAND Round73JointInsertionTests)
add_executable(Round73ConstructiveSeedTests tests/round73_constructive_seed_tests.cpp)
target_link_libraries(Round73ConstructiveSeedTests PRIVATE exact_ebrp_core)
add_test(NAME Round73ConstructiveSeedTests COMMAND Round73ConstructiveSeedTests)
if(EXACT_EBRP_ENABLE_GUROBI)
  add_test(NAME Round75QuantityDescentCliTests COMMAND ${CMAKE_COMMAND}
    "-DEXACT_EXE=$<TARGET_FILE:ExactEBRP>"
    "-DSOURCE_ROOT=${CMAKE_CURRENT_SOURCE_DIR}"
    "-DOUTPUT_ROOT=${CMAKE_CURRENT_BINARY_DIR}"
    -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/round75_quantity_descent_cli_test.cmake")
  add_test(NAME Round73ConstructiveSeedCliTests COMMAND ${CMAKE_COMMAND}
    "-DEXACT_EXE=$<TARGET_FILE:ExactEBRP>"
    "-DSOURCE_ROOT=${CMAKE_CURRENT_SOURCE_DIR}"
    "-DOUTPUT_ROOT=${CMAKE_CURRENT_BINARY_DIR}"
    -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/round73_constructive_seed_cli_test.cmake")
  add_test(NAME Round73JointInsertionCliTests COMMAND ${CMAKE_COMMAND}
    "-DEXACT_EXE=$<TARGET_FILE:ExactEBRP>"
    "-DSOURCE_ROOT=${CMAKE_CURRENT_SOURCE_DIR}"
    "-DOUTPUT_ROOT=${CMAKE_CURRENT_BINARY_DIR}"
    -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/round73_joint_insertion_cli_test.cmake")
  add_test(NAME Round71InterrouteCliTests COMMAND ${CMAKE_COMMAND}
    "-DEXACT_EXE=$<TARGET_FILE:ExactEBRP>"
    "-DSOURCE_ROOT=${CMAKE_CURRENT_SOURCE_DIR}"
    "-DOUTPUT_ROOT=${CMAKE_CURRENT_BINARY_DIR}"
    -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/round71_interroute_cli_test.cmake")
  add_test(NAME Round70DescentCliTests COMMAND ${CMAKE_COMMAND}
    "-DEXACT_EXE=$<TARGET_FILE:ExactEBRP>"
    "-DSOURCE_ROOT=${CMAKE_CURRENT_SOURCE_DIR}"
    "-DOUTPUT_ROOT=${CMAKE_CURRENT_BINARY_DIR}"
    -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/round70_descent_cli_test.cmake")
endif()
add_executable(Round61CandidateExperiment src/round61_candidate_main.cpp)
add_executable(Round61TimeOracle src/round61_time_main.cpp)
add_executable(Round62ThresholdProbe src/round62_threshold_main.cpp)
add_executable(Round62NativeMicro src/round62_native_micro.cpp)
add_executable(Round63ResourceProbe src/round63_resource_probe.cpp)
target_link_libraries(Round63ResourceProbe PRIVATE exact_ebrp_core)
add_executable(Round64ResourceProbe src/round64_resource_probe.cpp)
target_link_libraries(Round64ResourceProbe PRIVATE exact_ebrp_core)
add_executable(Round64ProjectionAudit src/round64_projection_audit.cpp)
target_link_libraries(Round64ProjectionAudit PRIVATE exact_ebrp_core)
add_executable(Round65ReferenceBuild src/round65_reference_build.cpp)
target_link_libraries(Round65ReferenceBuild PRIVATE exact_ebrp_core)
if(EXACT_EBRP_ENABLE_GUROBI)
  target_include_directories(Round64ProjectionAudit PRIVATE "${GUROBI_INCLUDE_DIR}")
  target_include_directories(Round65ReferenceBuild PRIVATE "${GUROBI_INCLUDE_DIR}")
endif()
add_executable(Round64Tests tests/round64_shared_tests.cpp)
add_executable(Round65Tests tests/round65_proof_tests.cpp)
target_link_libraries(Round65Tests PRIVATE exact_ebrp_core)
add_test(NAME Round65Tests COMMAND Round65Tests)
target_link_libraries(Round64Tests PRIVATE exact_ebrp_core)
add_test(NAME Round64Tests COMMAND Round64Tests)
add_executable(Round62ProjectionAudit src/round62_projection_audit.cpp)
target_link_libraries(Round62ProjectionAudit PRIVATE exact_ebrp_core)
if(EXACT_EBRP_ENABLE_GUROBI)
  target_include_directories(Round62ProjectionAudit PRIVATE "${GUROBI_INCLUDE_DIR}")
endif()
target_link_libraries(Round62NativeMicro PRIVATE exact_ebrp_core)
target_link_libraries(Round62ThresholdProbe PRIVATE exact_ebrp_core)
target_link_libraries(Round61TimeOracle PRIVATE exact_ebrp_core)
target_link_libraries(Round61CandidateExperiment PRIVATE exact_ebrp_core)
add_executable(Round61CandidateTests tests/round61_candidate_tests.cpp)
add_executable(Round63Tests tests/round63_time_tests.cpp)
target_link_libraries(Round63Tests PRIVATE exact_ebrp_core)
add_test(NAME Round63Tests COMMAND Round63Tests)
add_executable(Round62Tests tests/round62_tests.cpp)
target_link_libraries(Round62Tests PRIVATE exact_ebrp_core)
add_test(NAME Round62Tests COMMAND Round62Tests)
target_link_libraries(Round61CandidateTests PRIVATE exact_ebrp_core)
add_test(NAME Round61CandidateTests COMMAND Round61CandidateTests)
add_executable(Round59ResearchTests tests/round59_research_tests.cpp)
target_link_libraries(Round59ResearchTests PRIVATE exact_ebrp_core)
add_test(NAME Round59ResearchTests COMMAND Round59ResearchTests)
add_executable(Round60CandidateTests tests/round60_candidate_tests.cpp)
target_link_libraries(Round60CandidateTests PRIVATE exact_ebrp_core)
add_test(NAME Round60CandidateTests COMMAND Round60CandidateTests)
target_link_libraries(ExactEBRP PRIVATE exact_ebrp_core)

add_executable(ExactEBRPCompare src/compare_main.cpp)
target_link_libraries(ExactEBRPCompare PRIVATE exact_ebrp_core)

add_executable(ControllingLeafSchedulerTests tests/controlling_leaf_scheduler_tests.cpp)
target_link_libraries(ControllingLeafSchedulerTests PRIVATE exact_ebrp_core)
add_test(NAME ControllingLeafSchedulerTests COMMAND ControllingLeafSchedulerTests)

add_executable(GlobalGiniTreeTests tests/global_gini_tree_tests.cpp)
target_link_libraries(GlobalGiniTreeTests PRIVATE exact_ebrp_core)
add_test(NAME GlobalGiniTreeTests COMMAND GlobalGiniTreeTests)

add_executable(StrictCertificateTests tests/strict_certificate_tests.cpp)
target_link_libraries(StrictCertificateTests PRIVATE exact_ebrp_core)
add_test(NAME StrictCertificateTests COMMAND StrictCertificateTests)

add_executable(ConnectivityFlowTests tests/connectivity_flow_tests.cpp)
target_link_libraries(ConnectivityFlowTests PRIVATE exact_ebrp_core)
add_test(NAME ConnectivityFlowTests COMMAND ConnectivityFlowTests)

add_executable(StrictSerializationTests tests/strict_serialization_tests.cpp)
target_link_libraries(StrictSerializationTests PRIVATE exact_ebrp_core)
add_test(NAME StrictSerializationTests COMMAND StrictSerializationTests)

add_executable(ModelCorrectnessTests tests/model_correctness_tests.cpp)
target_link_libraries(ModelCorrectnessTests PRIVATE exact_ebrp_core)
add_test(NAME ModelCorrectnessTests COMMAND ModelCorrectnessTests)

add_executable(DenseProgressTests tests/dense_progress_tests.cpp)
target_link_libraries(DenseProgressTests PRIVATE exact_ebrp_core)
add_test(NAME DenseProgressTests COMMAND DenseProgressTests)

add_executable(DispersionChildBoundTests tests/dispersion_child_bound_tests.cpp)
target_link_libraries(DispersionChildBoundTests PRIVATE exact_ebrp_core)
add_test(NAME DispersionChildBoundTests COMMAND DispersionChildBoundTests)

add_executable(Round24BackendTests tests/round24_backend_tests.cpp)
target_link_libraries(Round24BackendTests PRIVATE exact_ebrp_core)
add_test(NAME Round24BackendTests COMMAND Round24BackendTests)

add_executable(Round27PaperSchedulingTests tests/round27_paper_scheduling_tests.cpp)
target_link_libraries(Round27PaperSchedulingTests PRIVATE exact_ebrp_core)
add_test(NAME Round27PaperSchedulingTests COMMAND Round27PaperSchedulingTests)

add_executable(Round28ReplicaTests tests/round28_replica_tests.cpp)
target_link_libraries(Round28ReplicaTests PRIVATE exact_ebrp_core)
add_test(NAME Round28ReplicaTests COMMAND Round28ReplicaTests)

add_executable(Round29PerformanceRecoveryTests
  tests/round29_performance_recovery_tests.cpp)
target_link_libraries(Round29PerformanceRecoveryTests PRIVATE exact_ebrp_core)
add_test(NAME Round29PerformanceRecoveryTests
  COMMAND Round29PerformanceRecoveryTests)

add_executable(Round30C5Tests tests/round30_c5_tests.cpp)
target_link_libraries(Round30C5Tests PRIVATE exact_ebrp_core)
add_test(NAME Round30C5Tests COMMAND Round30C5Tests)

add_executable(Round31C6Tests tests/round31_c6_tests.cpp)
target_link_libraries(Round31C6Tests PRIVATE exact_ebrp_core)
add_test(NAME Round31C6Tests COMMAND Round31C6Tests)

add_executable(Round36CausalTests tests/round36_causal_tests.cpp)
target_link_libraries(Round36CausalTests PRIVATE exact_ebrp_core)
add_test(NAME Round36CausalTests COMMAND Round36CausalTests)

add_executable(Round37GeometryTests tests/round37_geometry_tests.cpp)
target_link_libraries(Round37GeometryTests PRIVATE exact_ebrp_core)
add_test(NAME Round37GeometryTests COMMAND Round37GeometryTests)

add_executable(Round40CoarseStartTests tests/round40_coarse_start_tests.cpp)
target_link_libraries(Round40CoarseStartTests PRIVATE exact_ebrp_core)
add_test(NAME Round40CoarseStartTests COMMAND Round40CoarseStartTests)

add_executable(Round40UbGeometryTests tests/round40_ub_geometry_tests.cpp)
target_link_libraries(Round40UbGeometryTests PRIVATE exact_ebrp_core)
add_test(NAME Round40UbGeometryTests COMMAND Round40UbGeometryTests)

add_executable(Round41StaticSegmentedTests
    tests/round41_static_segmented_tests.cpp)
target_link_libraries(Round41StaticSegmentedTests PRIVATE exact_ebrp_core)
add_test(NAME Round41StaticSegmentedTests COMMAND Round41StaticSegmentedTests)

add_executable(Round42StaticSegmentedTests
    tests/round42_static_segmented_tests.cpp)
target_link_libraries(Round42StaticSegmentedTests PRIVATE exact_ebrp_core)
add_test(NAME Round42StaticSegmentedTests COMMAND Round42StaticSegmentedTests)

add_executable(Round43EnvelopeRefinementTests
    tests/round43_envelope_refinement_tests.cpp)
target_link_libraries(Round43EnvelopeRefinementTests PRIVATE exact_ebrp_core)
add_test(NAME Round43EnvelopeRefinementTests
  COMMAND Round43EnvelopeRefinementTests)

add_executable(Round44EnvelopeTailRepairTests
    tests/round44_envelope_tail_repair_tests.cpp)
target_link_libraries(Round44EnvelopeTailRepairTests PRIVATE exact_ebrp_core)
add_test(NAME Round44EnvelopeTailRepairTests
  COMMAND Round44EnvelopeTailRepairTests)

add_executable(Round45AdaptiveParametricTests
    tests/round45_adaptive_parametric_tests.cpp)
target_link_libraries(Round45AdaptiveParametricTests PRIVATE exact_ebrp_core)
add_test(NAME Round45AdaptiveParametricTests
  COMMAND Round45AdaptiveParametricTests)

add_executable(Round46C6RhoTests tests/round46_c6_rho_tests.cpp)
target_link_libraries(Round46C6RhoTests PRIVATE exact_ebrp_core)
add_test(NAME Round46C6RhoTests COMMAND Round46C6RhoTests)

add_executable(Round47AdaptiveMassTests
    tests/round47_adaptive_mass_tests.cpp)
target_link_libraries(Round47AdaptiveMassTests PRIVATE exact_ebrp_core)
add_test(NAME Round47AdaptiveMassTests COMMAND Round47AdaptiveMassTests)

add_executable(Round48K1AMFTests tests/round48_k1_amf_tests.cpp)
target_link_libraries(Round48K1AMFTests PRIVATE exact_ebrp_core)
add_test(NAME Round48K1AMFTests COMMAND Round48K1AMFTests)

add_executable(Round49RCOfflineExtract src/round49_rc_extract_main.cpp)
target_link_libraries(Round49RCOfflineExtract PRIVATE exact_ebrp_core)

add_executable(Round49K1LPPrimalDualTests tests/round49_k1_rc_tests.cpp)
target_link_libraries(Round49K1LPPrimalDualTests PRIVATE exact_ebrp_core)
add_test(NAME Round49K1LPPrimalDualTests COMMAND Round49K1LPPrimalDualTests)

add_executable(Round50IntervalMipExperiment
  src/round50_interval_mip_main.cpp)
target_link_libraries(Round50IntervalMipExperiment PRIVATE exact_ebrp_core)

# Round 51 uses the same fixed-state driver and emits an independently hashed
# executable for its causally staged comparisons. Historical Round 50 policy
# names remain accepted and byte-preserving for default-off audits.
add_executable(Round51IntervalMipExperiment
  src/round50_interval_mip_main.cpp)
target_link_libraries(Round51IntervalMipExperiment PRIVATE exact_ebrp_core)

add_executable(Round50IntervalMipTests tests/round50_interval_mip_tests.cpp)
target_link_libraries(Round50IntervalMipTests PRIVATE exact_ebrp_core)
add_test(NAME Round50IntervalMipTests COMMAND Round50IntervalMipTests)

add_executable(Round51TightBigMTests tests/round51_tight_big_m_tests.cpp)
target_link_libraries(Round51TightBigMTests PRIVATE exact_ebrp_core)
add_test(NAME Round51TightBigMTests COMMAND Round51TightBigMTests)

add_executable(Round52TailoredCutTests
  tests/round52_tailored_cut_tests.cpp)
target_link_libraries(Round52TailoredCutTests PRIVATE exact_ebrp_core)
add_test(NAME Round52TailoredCutTests COMMAND Round52TailoredCutTests)

add_executable(Round53F0AndCallbackTests
  tests/round53_f0_callback_tests.cpp)
target_link_libraries(Round53F0AndCallbackTests PRIVATE exact_ebrp_core)
add_test(NAME Round53F0AndCallbackTests COMMAND Round53F0AndCallbackTests)

add_executable(Round54InventoryRouteExperiment
  src/round54_inventory_route_main.cpp)
target_link_libraries(Round54InventoryRouteExperiment PRIVATE exact_ebrp_core)

add_executable(Round54MainlineAndInventoryRouteTests
  tests/round54_mainline_inventory_route_tests.cpp)
target_link_libraries(Round54MainlineAndInventoryRouteTests
  PRIVATE exact_ebrp_core)
target_compile_definitions(Round54MainlineAndInventoryRouteTests PRIVATE
  EXACT_EBRP_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
add_test(NAME Round54MainlineAndInventoryRouteTests
  COMMAND Round54MainlineAndInventoryRouteTests)

add_executable(Round55StationStateChainTests
  tests/round55_station_state_chain_tests.cpp)
target_link_libraries(Round55StationStateChainTests PRIVATE exact_ebrp_core)
target_compile_definitions(Round55StationStateChainTests PRIVATE
  EXACT_EBRP_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
add_test(NAME Round55StationStateChainTests
  COMMAND Round55StationStateChainTests)

add_executable(Round56PaperBenchmarkTests
  tests/round56_paper_benchmark_tests.cpp)
target_link_libraries(Round56PaperBenchmarkTests PRIVATE exact_ebrp_core)
target_compile_definitions(Round56PaperBenchmarkTests PRIVATE
  EXACT_EBRP_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
add_test(NAME Round56PaperBenchmarkTests
  COMMAND Round56PaperBenchmarkTests)

add_executable(Round58CitiBikePairedBenchmarkTests
  tests/round58_citibike_paired_benchmark_tests.cpp)
target_link_libraries(Round58CitiBikePairedBenchmarkTests
  PRIVATE exact_ebrp_core)
target_compile_definitions(Round58CitiBikePairedBenchmarkTests PRIVATE
  EXACT_EBRP_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
add_test(NAME Round58CitiBikePairedBenchmarkTests
  COMMAND Round58CitiBikePairedBenchmarkTests)
