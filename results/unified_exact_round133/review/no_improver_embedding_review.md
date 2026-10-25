# Inclusive cutoff embedding repair design review

Independent reviewer: reliability_review. This approves the repair design,
not an unbuilt candidate or D admission.

Deleting the proof-only constant row is the correct uniform repair. B2
requires the native model to include a legal extension of every physical
point with `G` in the leaf and `F<=c`. The old trigger
`gamma_L+lambda*Pmin>=c-1e-9` does not establish that inclusive set is
empty. In particular equality at the cutoff is legal. A constant `0<=-1`
cannot represent a nonempty such set, even if its induced floor would happen to fall
within the inherited certificate tolerance.

This is a statement about the insufficiency of the old trigger as a uniform
embedding guarantee, not a claim that every historical triggering call has
a nonempty physical domain. If an independently valid physical box proves
the exact floor `A=gamma_L+lambda*Pmin_safe>c`, the cutoff physical set is
empty and the artificial row is vacuous for that particular call. `A==c`
still permits boundary points; `A<c` permits points below the cutoff. A
finite regional floor then uses the actual safe `min(A,c)`, without raising
it to the cutoff or adding a tolerance.

Keep the legitimate `P>=Pmin` row and the existing physical analytic floor.
Their provenance remains distinct from a native INFEASIBLE claim. Removing
the invalid row allows qualified lower bounds or the analytic floor to
close normally under the existing `1e-7` certificate contract. A genuinely
infeasible inclusive cutoff model still contributes the finite cutoff floor
through the existing complement proof. No tolerance or parameter change is
needed.

The proposed exact boundary fixture is sufficient to expose this row:
two stations, `b=(1,0)`, `D=(1,1)`, `C=(2,2)`, `Q=1`, all coordinates zero,
physical horizon one second, pickup/drop handling 60 seconds,
`lambda=2^-39`, leaf `[.5,.5]` and cutoff `c=.5+2^-39`. Both lambda and
cutoff are exactly representable binary64 values. Set interval enabled,
`add_incumbent_row=true`, and `incumbent_epsilon=0` explicitly. The no-op
fleet has duration zero, `Y=(1,0)`, `G=.5`, `P=1`, and `F=c`, hence belongs
to the required inclusive set. Since `Pmin>=0` and `lambda<1e-9`, the old
trigger is true and the constant row rejects it. The fixture should check the emitted legal rows
against this boundary extension and retain a negative check showing why
the former constant row rejects it; a tag-only absence check is weaker.

Correction to the review's initial proposal: lambda zero does not activate
the shared factory's cutoff branch because `cutoff_active` requires
`lambda>1e-12`. It is therefore not a reproducing negative control. The
primary implementer caught this guard; the dyadic value above exceeds it.
The mathematical inclusion error remains the same. This is a single domain
contract fixture, not a lambda sensitivity study.

There are two source emitters: the shared factory and the
`!use_shared_interval_rows` fallback in `CplexBaseline.cpp`. The latter is
not excluded by `round127Validate`. A uniform claim covering all new S2
cutoff models therefore requires deleting the same invalid block from both
emitters, or an explicit enforced qualification boundary excluding the
fallback. Rebuilding the affected factory and compact-emitter objects is
required; changing an inline helper while reusing old objects would not
establish that the old generated row is gone.

This changes the production model only in the domains where the invalid
row previously triggered. Bind both emitters and rebuilt objects in the
new candidate identity and describe the change in D3. S2R already excluded
the row. D24's saved complete matrix has a feasible rational point and is
unaffected; the SC-B20-S GEOM diagnostic uses inclusive S2R and is also
unaffected. No historical raw result or qualification is rewritten.

Remaining admission work is to inspect the actual patch, exact boundary
fixture result, rebuilt source/object/PE identities, the normal positive
closure checks and the final reader. This review started no native work.

The implementation and zero-Optimize fixtures were subsequently read and
matched the approved design. Both old blocks are deleted, the two compact
emitter objects and the shared factory object were rebuilt, and 27 emitted
rows/bounds retain the exact dyadic boundary point. Source/build identities
and the normal positive closure checks are bound in `pre_admission.json`.
This does not grant final D admission.

For the four actual ORIGINAL_E3 D3 positions only, the agreed forward policy
is conservative. A source/mode/row-motif-bound old marker can receive an
evidence-complete UNEVALUABLE closeout only after full producer, physical,
H, Start, model, return and clock audits. Model-scope, implementation,
native, performance and certificate qualification remain false, and
`T_cert` is null; raw tuples and clocks remain intact. Actual native Y
bounds alone do not prove a box containing every physical `X_l(c)` point,
so the diagnostic Fraction minimum over that box is not automatically
promoted to a physical floor. No additional box proof or analytic old
certificate upgrade is requested. A known model shortcut is not relabeled
as a commercial solver numerical contradiction. Nonmarker evidence still
receives its ordinary independent checks. The final reader must implement
this after complete audits, rather than raising inside the initial model
loop and claiming evidence completion.
