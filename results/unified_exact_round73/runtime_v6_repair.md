# v5 retained failure and one v6 repair qualification

v5 at source110ca82298b4ea52d2474b477fe67322b5c8f5f8 built successfully.
Its53 existing tests passed, including75 actual native fixture calls. New test1
failed at the corrupt-fixture file-copy setup: this MinGW/Windows runtime
reported `File exists` despite the overwrite option. Configure/build/tests
cost1.547141300+90.567191100+6.754223500=98.868555901s. This is a test-fixture
failure, not a successful durability qualification. No six-role native
diagnosis was launched. The new fixture uses a separate new corrupt directory.

Inspection also found that retaining only improving witnesses hid the first
native MIPSOL when it equalled the already verified startup. v6 explicitly
persists the first verified native witness per call even when non-improving;
it remains observational. A contradictory new physical witness is persisted
before its failure marker, so rejection retains the offending evidence.

Allocate one new isolated v6 configure/build/full54-test batch. Preserve v5
logs, fixture artifacts and cost; existing75 native qualification calls are
expected again and charged. Six reserved <=30s diagnoses remain unused and
follow runtime_qualification_plan.md only after the complete suite passes.
This repair adds no performance allocation or algorithmic timer.
