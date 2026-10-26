# Reproduction commands

```powershell
cmake -S . -B build_round44 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT="D:/gurobi1302/win64"
cmake --build build_round44 -j 4
ctest --test-dir build_round44 --output-on-failure
python scripts/run_round44_default_off.py --process-cap 3600
python scripts/analyze_round44_default_off.py
python scripts/run_round44_small_qualification.py --stage validation --candidate primary
python scripts/analyze_round44_qualification.py --small validation
python scripts/analyze_round44_qualification.py --activate-fallback
python scripts/run_round44_small_qualification.py --stage validation --candidate veto-f05
python scripts/analyze_round44_qualification.py --small validation --candidate veto-f05
python scripts/analyze_round44_qualification.py --seal-negative
python scripts/finalize_round44.py
```
