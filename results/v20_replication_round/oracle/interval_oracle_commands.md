# Interval Cutoff Oracle Commands

```powershell
build\ExactEBRP.exe --method interval-cutoff-oracle --input reference\hard_stress\V20_M3\moderate_seed3301.txt --lambda 0.15 --T 3600.0 --threads 1 --time-limit 600.0 --interval-exact-cutoff-oracle compact-mip --interval-exact-cutoff-gamma-L 0.0163841842216 --interval-exact-cutoff-gamma-U 0.0327683684432 --interval-exact-cutoff-UB 0.0491525526647 --interval-exact-cutoff-epsilon 1e-08 --interval-exact-cutoff-time-limit 600.0 --interval-exact-cutoff-export-lp results\v20_replication_round\oracle\cplex\interval_oracle_1_0p0163841842216_0p0327683684432.lp --interval-exact-cutoff-result results\v20_replication_round\oracle\cplex\interval_oracle_1_0p0163841842216_0p0327683684432.sol --log results\v20_replication_round\oracle\logs\interval_oracle_1_0p0163841842216_0p0327683684432.cplex.log --out results\v20_replication_round\oracle\raw\interval_oracle_1_0p0163841842216_0p0327683684432.json
```
