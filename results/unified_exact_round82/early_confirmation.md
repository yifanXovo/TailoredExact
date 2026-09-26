# First three fixed confirmation roles

All nine original arms returned normally and passed per-run physical/bound
checks. Joint final audit and actual Start/trajectory checks remain pending.

|Role|P-GRB|BDS-C|K1-R|Preliminary comparison|
|---|---|---|---|---|
|U1 synthetic V12|3.641s certified|0.875s certified|2.063s certified|BDS materially improves P; near K1 by frozen rule|
|U2 Citi compact surplus V12|36.265s certified|11.969s certified|20.047s certified|BDS materially improves both|
|U3 synthetic high imbalance V20|Open at297.062s, gap.315606693|61.937s certified|81.156s certified|BDS gains certificate against P and improves K1 time|

All three objectives are nonzero, including U2 whose pre-solve zero exclusion
was not established. Raw signed numerical gaps are preserved in JSON; values
near minus1e-15 are not clipped. Numerical certification is not rational proof.
U3 is a common300s screen. It does not stand in for U4--U6's common3600s runs.
All exact endpoints, native call counts and costs are in early_confirmation.json.

A live commentary initially assigned U2's BDS/K1 difference to the near group;
that arithmetic interpretation was immediately corrected:8.078s and40.3%
passes the unchanged small certified2s/20% rule. It is U1's1.188s difference
that fails the absolute threshold. No data, rule, run or classification code
was changed to make the correction.

The first two ordinary HTTPS pushes failed with connection resets. Exact-object
API publication subsequently preserved and freshly verified all four original
commits through668229b5b28465423cb91c74f0374dce975a8ab7 in94.536586s. This is
transport recovery, not a solver rerun. The generation-before-outcome history
remains intact. No draft PR or overall confirmation acceptance is declared yet.
