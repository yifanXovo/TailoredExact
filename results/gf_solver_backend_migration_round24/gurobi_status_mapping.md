# Gurobi status mapping

| Code | Native name | Round 24 class | Strict optimality |
|---:|---|---|---|
| 1 | LOADED | incomplete | reject |
| 2 | OPTIMAL | exact-optimal candidate | accept only after every independent gate |
| 3 | INFEASIBLE | infeasibility candidate | accept only for audited original scope and no witness contradiction |
| 4 | INF_OR_UNBD | ambiguous | reject |
| 5 | UNBOUNDED | unbounded | reject for this bounded original model |
| 6 | CUTOFF | cutoff | reject |
| 7, 8, 9, 10, 15, 16, 17 | iteration/node/time/solution/objective/work/memory limit | limit | reject; retain only valid finite native bound evidence |
| 11 | INTERRUPTED | interrupted | reject |
| 12, 13 | NUMERIC, SUBOPTIMAL | numeric or suboptimal | reject |
| 14 | INPROGRESS | incomplete | reject |
| other | unsupported | unsupported | reject |

API errors are separate from statuses. Error 10009 is serialized as `gurobi_error_10009:No Gurobi license found`; environment-specific suffixes are removed.
