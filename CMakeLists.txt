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
  src/Result.cpp
  src/StrictCertificate.cpp
  src/ModelCorrectness.cpp
  src/FileSha256.cpp
  src/ProcessPhaseLedger.cpp
  src/DenseProgress.cpp
  src/GurobiCertificate.cpp
  src/GurobiProgress.cpp
  src/MipStartMapping.cpp
  src/ExternalGiniTree.cpp
  src/PaperExternalGiniTree.cpp
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
  src/IntervalRowFactory.cpp
  src/DispersionChildBound.cpp
  src/hga_tgbc/HgaTgbcGreedy.cpp
  src/HgaTgbcRunner.cpp
  src/Logger.cpp
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
