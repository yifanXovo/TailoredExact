# Round106 exact oracle and conflict assumptions

Every native single-car full model uses the R105 all-station optional
physical template. It contains no global objective, inventory cutoff or
other vehicle obligation. Generic bounds permit legal loaded return and
all original station/order choices. Exact signed operation vectors and
source candidate columns are retained in each pattern's manifest/model.

| Proof/family | Assumptions actually required | Master row / transfer |
|---|---|---|
| FULL native INF | For qi!=0: a_i_z=1, a_i_p=max(qi,0), a_i_d=max(-qi,0); for qi=0: a_i_z=0 | Served groups require z_ki and state_i,(bi-qi); every absence contributes -z_ki; vehicle-specific full mode |
| CORE confirmed | Whole semantic groups from IIS, re-proved in a fresh template with all unmentioned stations free | Same served/absence interpretation on released core; never Y-only |
| A_MST | Actual conservative metric depot/support MST, h/T/travel and integer ownership; no current outside obligations | h sumP+L(sumZ-|S|+1)<=T; Q-independent only across h/T/travel-compatible vehicles |
| B_EXACT | Balanced three operations, all six orders fail, strict integer handling budget L+h(P0+1)>T | Three ownership and three exact state literals<=5; no absent stations needed |
| B_THRESHOLD | Same complete proof plus quantity thresholds forced equal by pickup budget and nonnegative return | Ownership plus pickup/drop threshold state sums<=5; no generic quantity monotonicity |

For FULL/CORE with a served groups and b absent groups the row is
sum(served)(z+state)-sum(absent)z<=2a-1. An IIS row hit lifts conservatively
to its whole station semantic group. IISMinimal does not mean a minimum
core. Native INFEASIBLE on the released all-station template is needed;
interrupted IIS/confirmation retains only the already-proved full mode.
INF_OR_UNBD, no incumbent and limit statuses are UNKNOWN. A independently
verified FEAS route is usable without proving minimum travel.

STRUCT scans all cars for A/B before paying new full oracle calls; if any
reliable proved rejection exists it can submit it immediately. Its native
fallback is FULL without IIS. FULL and CORE generate/use no A/B. Caches
are isolated per formal run and bind operation vector, vehicle label/full
physical data/travel/numerical contract; same Y with different ownership
is not a hit. Cross-car A rows require the explicit proof above, never a
Q20 ordinary INF copied to Q25/30.

Only rows currently reliably violated in raw MIPSOL_SOL are sent to
GRBcblazy. Unviolated valid rows remain in the pool. Repeated INF candidates
re-submit violated known rows; API0 from a prior event is not a fresh
rejection. All-car independent physical verification is needed for own UB;
submission attempt/deferred API0/native exact acceptance remain separate.
UNKNOWN without a rejection terminates safely and disqualifies the final
native bound. All Optimize/IIS calls receive only global remaining time.

Raw full.lp, proposal.ilp/json, core_confirm.lp/log, proof status, calls.csv,
row coefficients, candidate.sol, physical witness and lazy.csv are packaged
for actual calls/rows. Pure B's six-order checks are arithmetic separation,
not a hidden TSP/oracle. A/B mathematical declarations may include selector
states absent from the current non-strict U0 domain; those columns are
fixed zero and safely omitted from the actual submitted row.
