# Complete inventory coupling: geometry, certificates and finite decisions

## Four distinct claims

A stronger inventory expression, a better lower bound for one price direction,
a narrower interval for the complete inventory epigraph coupled to Q, and a
better complete routing algorithm are different statements. A result at one
level does not imply the next. Round155's offline loops address the third
statement. The separate paid own-floor B/E panel addresses the fourth, without
changing its already qualified producer or introducing the offline columns.

## Optimal faces and columns

For an ideal exact-coefficient LP, let U_K be the restricted-master optimum,
D_K its dual feasible region, and D_K*={d in D_K:z(d)=U_K}. A true inventory Y
adds the constraint alpha<=p_d(Y)=beta f(Y)-pi'chi(Y). If both old and enlarged
primal/dual problems are feasible, have finite optima and attain dual optima,
then for a finite batch S,

    U_(K union S)=U_K
      iff D_K* intersect {d:alpha<=p_d(Y) for every Y in S} is nonempty.

Adding columns expands the primal domain and shrinks the dual domain, so the
new value cannot exceed U_K. A surviving old optimal dual point supplies the
reverse inequality by weak duality. Conversely, a new dual optimum attaining
U_K lies in that intersection. This is classical LP geometry, not a new
general column-generation theorem.

For a minimal covering example, demand is (1,1), the sole old column is (1,1)
with cost1, and duals obey u>=0 and u1+u2<=1. At (1,0), column (1,0) with
cost1/2 has reduced cost -1/2. Adding it leaves dual (0,1) feasible and optimal;
the primal still needs one unit of the old column to cover the second demand.
Thus a strict negative column can cut one dual optimum without reducing U_K.
R154's eight strict K35 columns and near-constant upper are compatible with
this effect; tiny floating-point movements are not proofs about exact faces.

## Qualified full-Q lower and upper

For one direction, Q residual support and its original pre-column implied
bounds give C_Q. The existing true columns correct the convexity multiplier:

    a_K=min(alpha, min_(Y in K) p_d(Y)),
    L(d)=C_Q+min(a_K,L_m).

L_m must lower-bound price over the entire unchanged legal inventory domain.
Only L(d), or an independently qualified replay of all valid support rows in
free Q, may improve the cumulative hull lower. The fixed-direction ceiling
C_Q+min(a_K,U_m) bounds this direction's possible certificate, not the complete
hull. A rejected target therefore says nothing by itself about every other
direction or the value of continued column feedback.

An upper requires a full RMP primal with all Q rows and original variables,
convexity, every marginal, and actual expected completion checked under the
accepted R134 numerical policy. The numerical RMP completion margin 1e-8 is
excluded from the dual certificate. An RMP upper is an LP-value upper; it is
not a routing incumbent. The saved source/witness chain remains attached to
every inherited numerical upper even if the latest RMP differs in last bits.

## Residual meaning and stopping

The inherited state-product residual obeys

    R_tau(Y)=S(Y)(p_d(Y)-tau).

With variable positive S, minimizing residual and minimizing original price
need not rank columns equally. Round155 reevaluates original price for all
returned stocks and records true reduced costs, later lambda weights and
marginal contributions separately from native residual objectives.

For a safe positive branch l<=S<=u and guarded residual lower ell, the original
price lower is tau+ell/u when ell>=0 and tau+ell/l otherwise. Legal zero stock
is a separate branch combined by minimum. A previously valid whole-domain
lower on the same direction is retained by maximum. The compact evidence
adapter changes none of these formulas, model constraints, qualifications or
stopping predicates.

The basic baseline uses the current optimal RMP dual directly. Its first true
counterexample is sent back immediately. The matched alternative uses the
same strengthened residual oracle for at most256 nodes (existing pool20),
with the same offline120s safety cap. Both use the exact original-price test
against corrected a_K. Duplicate returns never count as progress. The shared
whole-phase cap and screen count are experimental limits; they are not
hardware-dependent switches between algorithm components.

## Optional fixed level, if the screen motivates it

At a fixed stage target zeta in (L,U), an admissible direction must satisfy
C_Q+a_K>=zeta, with tau=zeta-C_Q. A full price lower L_m>=tau proves L>=zeta.
A legal stock p_d(Y)<tau rejects only that direction, adds a genuinely new
column and continues the stage. A qualified full RMP primal U<zeta resolves
the upper side. Selection-LP timeout, infeasibility or objective alone cannot
resolve that side. If a midpoint level is resolved, the corresponding interval
is at most half its previous width; there is no promise that any iteration or
price invocation resolves a level. Such a selector is not yet an executed
Round155 treatment and will only be adopted after evidence motivates it.

## E remains separate

E consumes the unchanged own-root floor through the already qualified proof
ledger. For each covered leaf it uses max(raw_L,min(U0,floor)); the complete
frontier is combined by minimum. Native model and AM inputs remain those of B
on the same domain. Paid helper cost and valid early termination can still
alter the actual trajectory. No universal improvement or default promotion is
presupposed. Checkpoint evidence is restricted to what the original journal
had made available by that checkpoint; later returns cannot be backfilled.

## Sources and existing ownership

The dual interpretation and stabilization context are classical; see
[Luebbecke and Desrosiers (2005)](https://pubsonline.informs.org/doi/pdf/10.1287/opre.1050.0234)
and [Pessoa et al. (2018)](https://pubsonline.informs.org/doi/abs/10.1287/ijoc.2017.0784?journalCode=ijoc).
The publisher records were checked in this round. The project's persistent
Master, midpoint/near-optimal selection and incumbent pools are R153 work;
signed/strengthened residuals and the proof-only consumer are R154 work.
Parameterized fractional objectives, McCormick products and proof ledgers
retain their established attribution. This round's potential contribution is
the measured problem-specific closed-loop improvement and its limits.
