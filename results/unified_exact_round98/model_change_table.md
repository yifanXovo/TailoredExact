# Actual active model relationship

Source baseline: R97 delivery bd68cf1c3b33fce0b6bc67e2947e9770c01e2601.
New canonical implementation 91ef377bd, production adapters/tests 6178a3971.
Formal identity pins full file bytes, not only these abbreviated commits.

| Block / column | R0 ENS-C actual active behavior | R1 | R2 | Related evidence / limitation |
|---|---|---|---|---|
| `state_i_y`, `state_g_i_y` | VD-P binary s, continuous q; Y/G/Z reconstruction and perspective q bounds | unchanged | unchanged | R55 isolated Y/G/Z hull; q represents epigraph G, not assumed true Gini |
| `Y_i`, `load_k_i` | integer | unchanged | unchanged | No new integrality claim for load or Y declarations |
| `z_k_i` | binary, sum per station<=1 | unchanged | unchanged | Single service and nonzero p+d>=z retained |
| `p_k_i`, `d_k_i` | nonnegative integer, original quantity/visit bounds | unchanged | continuous, physical integer semantics retained | Implied by integer s/z and joint reconstruction; strict all-column decoder |
| `mode_k_i` | binary, m<=z, p<=min(b,Q)m, d<=min(C-b,Q)(z-m) | unchanged | column and these three rows removed | Every active mathematical use checked; original coefficients projected |
| direction projection | old m block | old m block | cross-multiplied C when both caps positive; original individual visit bounds retained | Zero-cap directions fixed; no division; product computed in double |
| expected movement | inventory balance + mode/visit restrictions only | A: sum p+d=sum abs(b-y)s | same A | Adds two rows total per station with B; no direction reconstruction duplicates |
| expected visit | binary z and aggregate station visit cap | B: sum z+s_b=1 | same B | Absent b creates no selector; singleton/empty handled by inherited domain factory |
| ratio, penalty, G epigraph | unchanged original objective, VD-P epigraph/true-G embedding | unchanged | unchanged | No VD-J replacement and no claim G always equals true Gini |
| routing/time/load | empty departure, loaded return allowed, prefix load and inherited time contract | unchanged | unchanged | No total-pickup cap or total-inventory conservation added |
| Start | R68 maps actual native columns; all actual rows/domain/objective/readback checked | same mapper | removed m not submitted; p/d still original integers | Temporary mode dictionary keys are irrelevant to actual-column loop |
| native decoding | inherited numerical/physical validation | stricter all p/d integral check | same stricter check despite continuous type | Failed final decoding disables all candidate bound/certificate promotion |
| outer controller | original24+1 startup/closure, AM0.08, depth/width, static policy | same rules | same rules | Improved LP may change actual AM path; full cost includes this interaction |
| protected P-GRB | plain original compact; no Start/VD-P/new rows | unchanged | unchanged | Fresh original.lp SHA/fingerprint/rows/columns checked against actual P |

R1/R2 have no theta variables. No new threshold, selection parameter, branch priority tuning,
resource switch, dynamic user cut, R97 feedback, R96 reorder, LP-G or H-ACT is
active. The known50000 static-row policy is inherited. R62 service threshold
and R66 arc/load replacement modes are disallowed by the shared admission
predicate; their mathematical assumptions cannot silently enter elimination.

R3 (`vehicle-state`, source17272d41a) extends the same production path:

| Block | R3 change from R2 | Justification / scope |
|---|---|---|
| `theta_k_i_y` | continuous [0,1], only y!=b and abs(y-b)<=Q[k] in current safe domain | Capacity necessity only; no claim of route feasibility |
| state allocation | sum eligible theta=s for EVERY noninitial state, including empty eligibility | No unallocated state mass; empty row fixes that s=0 |
| vehicle quantities | z=sum theta, p=sum(b-y)+theta, d=sum(y-b)+theta for EVERY vehicle, even empty pools | Shared state/owner; empty pool fixes z=p=d=0 |
| A/B and C | replaced by theta equations | Implied continuously; no redundant aggregate copies |
| declarations | p/d/theta C, z/s B, Y/load I, no m | Original integer operation semantics proved and decoded |
| Start | explicit theta mapping from actual service vehicle and final inventory | Unknown/ineligible names fail closed; actual whole-row audit still required |
| outer/default/P | same frozen policy; defaultoff and original P unchanged | Every subsequent matched arm uses fresh common v3 build |

C3 raw R3 has6976 additional continuous columns; total33393 columns,
107144 rows,749224 nonzeros. Presolve:33355 columns,86235 rows,730262
nonzeros. Actual raw LP remains equal to R2. Structural projection evidence
does not by itself imply objective-bound or certification-time improvement.

Actual generated rows use sequential canonical constraint IDs. Exact LP SHA,
actual row coefficients and native ordered columns identify the model. Old
root identity equality is demonstrated on F2: R0 LP SHA
a37e2165fb900bb0d26d9158b89ade883202049456b7d1c6180f361070638091,
equal to R97 development02/raw/13_F2_OFF/external/models/L0.lp.
