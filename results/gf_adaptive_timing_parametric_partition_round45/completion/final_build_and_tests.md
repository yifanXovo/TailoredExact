# Round 45 completion build and test record

Date: 2026-08-22

Machine: `WIN-3NO58RVQ4VC`

Configuration: clean Release build with Gurobi enabled, MinGW Makefiles,
single-config generator

Compiler: `g++.exe (Rev2, Built by MSYS2 project) 14.2.0`

CMake: `3.30.5`

Gurobi: `13.0.2 build v13.0.2rc1 (win64)`

## Clean build

The independent build directory was
`build_round45_completion_clean_20260822`. Configuration used the Visual
Studio-bundled CMake executable, `D:/msys64/ucrt64/bin/c++.exe`,
`D:/msys64/ucrt64/bin/mingw32-make.exe`,
`EXACT_EBRP_ENABLE_GUROBI=ON`, and `GUROBI_ROOT=D:/gurobi1302/win64`.

```powershell
& 'D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' -S . -B build_round45_completion_clean_20260822 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER='D:/msys64/ucrt64/bin/c++.exe' -DCMAKE_MAKE_PROGRAM='D:/msys64/ucrt64/bin/mingw32-make.exe' -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT='D:/gurobi1302/win64'
& 'D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' --build build_round45_completion_clean_20260822 --config Release
```

Result: build completed successfully (100%). The compiler emitted only the
pre-existing dynamic-library pointer-cast warnings and one unused-function
warning; there were no build errors.

The clean-build executable SHA-256 is
`4b8ec1622bc6bc68f18633492e184846c2e1ae65ceb9d867a69a9df2a3ba82f5`.
The sealed official-run executable SHA-256 is
`d0b17662a6021cf2cc3c7b4c66868bf76c3d11e268f0b63afc71a7a77e7e88f4`.
The independent rebuild is not byte-identical because the Windows/MinGW link
does not use a reproducible-link contract; all official rows and their
manifests consistently reference the single sealed official-run hash.

## Tests and audits

```powershell
& 'D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe' --test-dir build_round45_completion_clean_20260822 --output-on-failure -C Release
& 'D:/msys64/ucrt64/bin/python.exe' -m unittest discover -s tests -p 'round??_protocol_tests.py' -v
& 'D:/msys64/ucrt64/bin/python.exe' tests/round45_completion_protocol_tests.py
& 'D:/msys64/ucrt64/bin/python.exe' scripts/run_round45_equivalence.py --executable build_round45_completion_clean_20260822/ExactEBRP.exe
& 'D:/msys64/ucrt64/bin/python.exe' scripts/finalize_round45.py
```

Results:

- CTest: 23/23 passed.
- Historical protocol suite: 104/104 passed.
- Round 45 completion protocol suite: 16/16 passed.
- Default-off and deterministic candidate equivalence: 4/4 comparisons
  passed across six sealed executions.
- Required matrix audit: 232/232 rows completed with 232 unique completion
  markers and no missing, extra, or duplicate markers.
- Artifact audit: every run command and artifact manifest hash revalidated.
- Complex gate: 48/48 mandatory rows and 6/6 secondary diagnostic rows
  completed.
- Counterfactual, point, classification, and small-panel rerun gates passed.
- Secret scan: zero matching files in the intended completion publication
  scope.
- License scan: zero license files in the intended completion publication
  scope.
- False-certificate flags: 77 rejected certificate claims recorded by the
  certificate audit; none is accepted as an original-problem certificate and
  they are not omitted matrix rows. No validated algorithm classification is
  emitted.

The finalizer reports `round45_completion_status = complete` while deriving the
honest negative/inconclusive classifications from the completed evidence.
