# Independent static review: mathematical target stops

Reviewer: `/root/review_round154`, independent of implementation.
Disposition: **ACCEPT_FOR_FINITE_NEW_INTERFACE_QUALIFICATION** at the source
identity below. Actual Native stop statuses, returned bounds and small-domain
qualification remain to be observed before expensive target-stop pricing.
This is not a claim that an unvalidated negative incumbent in the current
long run is a true counterexample.

The reviewer read round154_goal_oracle.py and the exact price bodies,
guard/transport/zero-branch logic and strengthened-model MRO it reuses.
This pass performed no Optimize, Native model load, compile, enumeration,
large I/O or new qualification. The current admitted K35 long run remains
on its original unchanged price implementation.

## Motivation and unchanged integer models

A long residual call can discover a Native negative residual incumbent
well before its ordinary return. The original wrapper only harvests
its pool at return. The new wrapper introduces mathematical target
stops so a verified refuting stock or qualified sufficient bound can
be consumed promptly. It changes no row, variable, support, objective
coefficient, denominator range, numerical guard or true-price evaluation.

A raw negative q is insufficient: downward coefficient transport makes
the written residual an intentional relaxation, and auxiliary/numerical
completion is not price authority. The new MIPSOL callback reconstructs
Y, then applies the original exact stock_value scope/resource/Gupper/
f/price evaluator. It stops only if that true legal inventory has
p(Y)<tau. This is a valid refutation of the fixed certificate's target,
not a refutation of the entire hull.

The callback calls the original local consider(Y), so a verified stock
remains in the result's true-stock dictionary even if Native terminates
before exposing a corresponding final pool solution. It saves the true
price, exact tau, scope and callback origin. Larger/nonminimal A or q is
never substituted for true price.

No elapsed-time component switch, role/size dispatch, potential box or
production helper modification is introduced. An ordinary offline cap
remains available for the whole price call.

## Guarded bound-stop thresholds

For normalized RN, the existing qualified positive-branch bound is

    scale*(NativeBound-guard-correction)+sum_station anchors.

Therefore a sufficient Native bound threshold for original price tau is

    (tau-sum anchors)/scale + guard + correction.

The wrapper computes this expression with Fraction, rounds the parameter
upward, writes BestBdStop and checks its actual readback. It preserves
the actual objective-coefficient correction as well as the numerical
guard. Signed anchors/costs and negative tau need no change of orientation
because the scale is positive.

For the residual model, the already qualified residual lower is

    ell=scale*(NativeBound-guard_scaled).

Thus NativeBound>=guard_scaled yields ell>=0 and the C4 conversion gives
m_positive>=tau, independently of the positive denominator width.
BestBdStop is set to that guarded scaled threshold. BestObjStop is
explicitly disabled, so an auxiliary incumbent is not a proof stop.

A USER_OBJ_LIMIT status alone is not taken as proof of tau. The inherited
function still obtains the actual finite ObjBound, subtracts the same
guard/correction, restores its units, and applies the original lower
composition. If Native's stopping tolerance returns a bound just short
of the parameter, the recomputed lower must still cross tau before a
whole-price target is called proved. A valid lower short of tau remains
only that lower.

This preserves the sign-dependent C4 recovery: positive qualified ell
uses u, negative ell uses l. Nothing changes q's free negative bound,
the original physical Gupper or the hard-resource constraints at beta=0.

## Zero branch, initial information and returned statuses

The original separate legal-zero price remains in both reused bodies.
A positive-branch proof must still take its minimum with that zero price.
Thus a cheap legal zero stock below tau prevents a whole-domain target
proof even if the positive Native branch reaches its bound threshold.
Zero-only/DP-attained paths may legitimately return without any Native
target-stop record. They should not be forced into a fabricated status15.

The original DP lower, legal warm stocks, upper evaluation and same-direction
inherited information rules remain. A known initial counterexample can
already refute tau without proving the price minimum. The Native callback
simply allows newly discovered stocks to be consumed sooner.

New accepted bound statuses are narrowly:

- USER_OBJ_LIMIT15 with finite bounded ObjBound, for this target wrapper;
- INTERRUPTED11 with finite bounded ObjBound only when this call's
  callback has already verified a true legal p(Y)<tau counterexample.

The old normal optimal/time/node statuses retain their previous policy.
An interrupted call with no own verified counterexample provides no new
Native lower. An unknown/nonfinite result likewise falls back to the
already valid information. A callback exception is durably recorded and
raises instead of manufacturing a returned bound. Existing cumulative
certificates outside the failed call remain available.

The accepted interrupted bound is still a global bound on the actual
unchanged price model; termination by its verified witness does not turn
the incumbent into a lower bound. The witness itself remains a true price
upper/column, independently of the remaining price gap.

## Code generation and MRO

The wrapper copies the old price source into a new function namespace,
requires exact occurrence counts for its limited signature/optimization/
qualification substitutions, and does not mutate the old modules/classes
on disk or assign a replacement to their original Oracle methods.

For the residual case, the MRO is the targeted class, strengthened class,
target residual core, original residual base. The strengthened price
method's super() therefore reaches the transformed core while preserving
its conditional S and DP-tight product setup. The unchanged production
R153 helper continues to instantiate its original normalized Oracle.

The generated source body, its SHA, wrapper SHA, target/threshold,
actual parameter readback and actual model SHA are saved for each call
that reaches Native. This makes the transformation reviewable and permits
a final audit to reconstruct exactly which status policy was used.
Model MPS semantics and the parameter/control record remain distinct.

The original fixed-cap classes, current K35 long task and frozen B/E/J
execution chain retain their own identities. Later target-stop performance
cannot be relabelled as an earlier stop time of the unmodified long run.
The currently observed negative Native residual is motivation only until
a saved true inventory is actually validated.

## Finite next qualification

After the active long price has returned and the serial meter is free,
qualify only this new stop/status interface on existing small domains.
The useful finite checks are actual status15 with guarded conversion,
actual own-counterexample status11, signed/beta0/negative-q and legal-zero
composition through the reused model, and retained DP/no-new-Native-bound
behavior without an eligible self-owned stop.

Actual status15 does not have to imply exact price optimality; its purpose
is a useful threshold proof. Actual status11 does not establish a negative
family result; it supplies a legal column and a fixed-direction ceiling.
Full-price RESOLVED and target-proved are separate notions, and the report
must retain that distinction.

The new interface must pass its finite saved qualification and independent
readback before entering expensive target-stop calls. There is no reason
to rerun old helper/process/complete-model or broad historical matrices.
Later direction selection and useful ceilings remain separate admission
questions.

Reviewed wrapper SHA256:
aeb418aeb97bb1802b9d4abdbcf12aad1c965ac0dfe8bb1fda3eb7ae90eec025.

Reused core identities remain:
round154_residual.py04bfa84774b7be4603ec08ae88ba015d6351d2bd3109a1d599fd4709f18bbc50;
round154_strengthened.py670d385ef6f9239b705fea92345709d4d4edbfe17dd732bb95b76b9b18460824.
Actual generated-body and Native status evidence are pending.

