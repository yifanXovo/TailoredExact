# Stage1 qualification completed before performance

New-mode micro:6 complete MIPs +4 raw LP calls, all passed. Independent reused
original physics enumerator optimum .4833333333333333; forced state optimum0,
empty domain infeasible. Zero/both-zero caps, missing initial state, singleton,
heterogeneous fleet and loaded return covered. Four micro raw LPs
.3239130434782609. Old36125 projection enumerations not repeated.

Three complete initial-root diagnostic batches (12 raw LP Optimize) all pass.
Actual numerical signatures agree exactly within R1/M-B and Q-I/R2, typed
signatures differ. All16 cross-mappings per role satisfy actual rows/bounds
at inherited1e-6; raw LP objectives agree within1e-7:
F2 .596712375053116; R98-C1 .0864173688882794;
R98-C2 .161236050498760. Historical U only supplies diagnostic root state;
formal runs must pay fresh startup independently.

Standalone presolve does not collapse these distinctions. F2 R1/M-B retain
3466 columns and1707/1627 integer declarations, but have7634/7594 rows and
57391/44996 nonzeros. Q-I/R2 retain3426 columns and1667/1587 integer declarations,
same7554 rows but57294/57092 nonzeros. By surviving names all40 p columns
retain I or C as selected. Similar type differences survive C1/C2.
This demonstrates declaration-dependent presolve transformation, not equal
optimize internal models or absence of implicit-integer reasoning.
Standalone export counts/types are diagnostic; production native logs still
required. Unavailable internal branching/cut causes remain unknown.

Immutable receipts: exports batch10.989s; failed micro01 .155s actual0 calls;
micro02 .134s actual10; LP batches5.014/4.666/16.926s actual4 each.
Conservative billed starts6,22 Optimize,37.884755s outer so far.
Build/configure/micro writer tests recorded separately as engineering.
