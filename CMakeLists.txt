cmake_minimum_required(VERSION 3.20)
project(ExactEBRP LANGUAGES CXX)

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
  src/hga_tgbc/HgaTgbcGreedy.cpp
  src/HgaTgbcRunner.cpp
  src/Logger.cpp
)

add_library(exact_ebrp_core ${EXACT_EBRP_LIB_SOURCES})

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
