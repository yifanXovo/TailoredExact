# Independent group08 cold P-GRB audit-failure investigation

**Finding: a read-only legacy-auditor mismatch is supported; no same-domain lower-bound counterexample was found.** This is an investigation, not a completed recovery or final performance review.

All 156 original committed physical fleets and the final result fleet independently pass service direction/integrality, inventory, assigned-Q prefix/return loads and original time checks. Best own observed event217 has F=0.391713327901773; the unchanged final native-result fleet has F=0.39178055857928196. The exact positive difference is 19602104372118545887/291564879284810400000000 (about 6.72307e-5), so the 1e-7 assertion failure is real and not hidden by rounding.

Every one of the 64 native lower bounds, including final L=0.34945085964584033, stays below both physical upper bounds. The actual single returned call uses the original cold compact model, Seed1 and frozen settings; model/reference/log/source identities agree and no D1 selector or Start is present.

The failing R86 assertion enforces an ordering between an observational history minimum and the final native-result physical upper bound. The frozen R114 reader explicitly defines own_U from the final result fleet. The journal is a read-only observer and the cold producer reconstructs its final result from returned native X. A valid earlier observed physical fleet can give a stronger U than that final result without contradicting a native lower bound. Internal native acceptance/branch behavior is not inferred.

The unchanged original finalizer was actually executed in memory and reproduced the failure. A receipt-specific semantic guard, checking independently proved feasible U values and all lower-bound inequalities while retaining the exact final result, allowed all remaining original finalizer checks to pass. No measured helper was edited and this does not substitute for the required complete recovered audit.

Protocol-compliant recovery must preserve every original failure/raw/fee, use a separately bound read-only recovery view, retain final U/L/certificate and T_produce exactly, retain the full waiting gap in T_verify/T_total, and rerun no producer. A separately recorded continuation may then fill only the never-started original D1 position with the unchanged role/Seed/argv/PE/environment and full own work/fees. Full32/all48, final stage, restore and cleanup remain pending.
