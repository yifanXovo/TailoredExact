# Round161 final research report

The complete physical RN objective is integer/objective preserving, but neither RN-core nor the sole uniform RN-P revision is competitive with the declared OLD whole-native control on these two sources. Keep the research entry default off and stop this finite study without entering the conditional complete E+/N-RN panel.

The C++ RN replacement is a real complete-carrier Native model. Its integer
and objective correspondence, including the zero-stock union, is established
algebraically and checked on tiny exhaustive physical cases. This finite
study keeps stable GI-TBC/B, E+ and the bare CLI defaults unchanged.

## Matched whole-native comparison

The two inputs are the identity-complete offline own-H/R83 parents used at
the intended pre-scope inlet: RX35 J=.4246498451636405 and NB35
J=.5772179446388801. They are development inputs, not fresh complete-arm
performance. There is no online old-parent or old-floor consumption.

|Role|Form|Mode|Physical U|Raw L|Qualified/global floor|Work|Nodes|Native s|Outer s|Stop|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
|R-X35-S-T2|OLD|LP|0.424649845164|0.186099795447|0.186099795447|2.7899207|0|0.897|3.20261|OPTIMAL|
|R-X35-S-T2|RN|LP|0.424649845164|0.120868897014|0.120868897014|2.1057117|0|0.772|2.95148|OPTIMAL|
|R-X35-S-T2|RN-P|LP|0.424649845164|0.124676728839|0.124676728839|2.2582256|0|0.78|2.95643|OPTIMAL|
|R-X35-S-T2|OLD|MIP|0.401139788438|0.210751964941|0.210751964941|2252.8907|716|895.744|898.082|TIME_LIMIT|
|R-X35-S-T2|RN|MIP|0.415548056887|0.179466164584|0.179466164584|2269.4926|975|895.897|898.097|TIME_LIMIT|
|R-X35-S-T2|RN-P|MIP|0.406923269363|0.173456239045|0.173456239045|2308.246|1001|895.872|898.079|TIME_LIMIT|
|N-B35-S|OLD|LP|0.577217944639|0.327833772177|0.327833772177|2.7207639|0|0.807|3.12497|OPTIMAL|
|N-B35-S|RN|LP|0.577217944639|0.269025714286|0.269025714286|3.1467323|0|1.053|3.24596|OPTIMAL|
|N-B35-S|RN-P|LP|0.577217944639|0.301013209511|0.301013209511|3.6434433|0|1.258|3.45646|OPTIMAL|
|N-B35-S|OLD|MIP|0.463426190476|0.388764524133|0.388764524133|2208.9426|1046|895.743|898.094|TIME_LIMIT|
|N-B35-S|RN|MIP|0.466805915424|0.365784602936|0.365784602936|2174.2418|1150|895.883|898.102|TIME_LIMIT|
|N-B35-S|RN-P|MIP|0.497425087324|0.378710952495|0.378710952495|2147.6571|1711|895.877|898.082|TIME_LIMIT|

Each LP has a 300s outer allowance; each MIP has NodeLimit=4096 and
a 900s outer allowance. The same complete inclusive initial improvement
scope, original parent, support, cutoff, physical/common rows, Start and
Seed0/Threads1/MIPFocus0 contract are used within each pair. TIME_LIMIT is
censored; identical node capacity does not imply equal work or runtime.
The LP physical U column is the independently validated input parent.
Full verified-U trajectories and first/best observation times, absolute/
relative gaps and presolve sizes are in reports/bridge.json and bridge.csv.
Raw bound observations are retained in each journal/progress file.

RN-P is the sole uniform revision: the same original-e penalty budget
legally tightens the reciprocal bounds. Its affected LP/MIPs are new C++
calls. OLD is the paid core-phase control, with exact new-export model/
Start equality and byte-identical Native-backend/mapper objects; the
RN-P executable is different and this is not a fresh same-PE panel.
Core and revised results remain separate in the table.

All reported lowers pass the existing model/source/parameter/numerical and
same-scope witness qualification. The complete J<=c region transports a
qualified ell by min(ell,c); G>c is also excluded by nonnegative penalty.
No local R160 bound is used. There is no independently paid inventory
helper in this development-only bridge. No full gap is closed, so T_cert
is empty and certified=false. Qualified OPEN is not a certificate.

## Matrix, penalty and physical domain

|Role|Form|Rows|Columns|Nonzeros|B/I/C|Presolved rows/cols/nz|Matrix min/max|
|---|---|---:|---:|---:|---|---|---|
|R-X35-S-T2|OLD|23334|9729|164317|4390/140/5199|19707/9536/152321|0.0075405/14439.7|
|R-X35-S-T2|RN|22732|9729|140668|4390/140/5199|19485/9514/129905|0.0075405/14439.7|
|R-X35-S-T2|RN-P|22732|9729|140668|4390/140/5199|19485/9514/129905|0.0075405/14439.7|
|N-B35-S|OLD|23608|10003|165467|4527/140/5336|19743/9812/152259|0.024/15426|
|N-B35-S|RN|23006|10003|141955|4527/140/5336|19669/9801/130040|0.024/15426|
|N-B35-S|RN-P|23006|10003|141955|4527/140/5336|19669/9801/130040|0.024/15426|

The registry explicitly removes state_g, zprod, unscaled h and W_SP plus
their exact row-consumer closure. Objective-dependent caps, spread and
estimators leave with that module. Original G+sum alpha_i e_i, r/e links,
e bounds, cutoff/penalty-common information and all remaining original
rows/column types are equal. No state-unary penalty was introduced. The
actual complete removed list and both full named matrices are saved.
The contrast concerns this declared replacement, not just a coefficient.
RN is not smaller in column count here; a reduction relative to old+RN
is not presented as a reduction relative to the original carrier.

The two exact basic-subblock witnesses show neither selector/G LP
projection dominates: RN permits G=0 where OLD needs 1/16, while R143's
three-station point permits OLD G=1/3 and requires RN G>=5/12. They do
not prove strict separation of arbitrary full routing LPs. Saved LP
rho-t*cY and zprod-GY residuals explain product slack without extra
Optimize calls or a causal claim. See reports/LP_product_diagnostics.json.

Every saved improving fleet is rechecked under original T with complete
stock, owner, routes, per-car travel/handling/unloading and prefix loads.
The exact loaded-c objective and original evaluator agree within the
existing numerical policy. Complete details are in reports/fleets.json.
reports/physical_changes.json identifies changed stocks, active stations
and owners. Original J depends only on final Y; the routes provide its
verified physical implementation. Endpoint changes do not isolate the
causal contribution of individual search operations.

The standalone trajectory plot distinguishes physical-U observations
from raw Native incumbent objectives on the Work axis; native objectives
are never substituted for physical U. Component time columns separate
build/conversion/Start/registry, Native Runtime (including callbacks),
and a composite remainder for environment/read/Start/return. Unmeasured
subparts of that remainder are not invented or added as extra fees.

## Decision and scope

All six finite MIPs execute meaningful integer search under the same 4096-node capacity and 900s outer allowance, each ending TIME_LIMIT. OLD dominates both RN versions in final verified physical U and qualified L on RX35 and NB35. RN-P raises both continuous LP bounds, but its integer outcomes remain inferior: RX35 U/L=.406923269363301/.173456239045039 versus OLD .401139788438118/.210751964941072; NB35 U/L=.497425087324243/.378710952495425 versus OLD .463426190476191/.388764524132733. Auxiliary column counts are equal and the smaller matrix does not provide a compensating useful cost/search tradeoff. Lower Native Work on NB35 is reported, not treated as a win when both endpoints are worse. The decision uses full finite integer-search evidence, not root weakness alone.

Stop investing in this RN-core/RN-P expression on the present evidence. A future structural study would first need a useful quantitative bound on reciprocal covariance/distortion implied jointly by the original stock, e-penalty and physical scope. The fixed-denominator limit and elementary distortion bound identify a falsifiable condition; merely having a new factor t does not justify a split controller. The present penalty-only tightening excludes saved LP points and raises roots but does not yield competitive whole-native outcomes. No automatic S/t buckets, old+RN cut intersection, route-flow replacement, larger R160 blocks, passive archive or late-feedback project is started.

The conditional complete E+/N-RN panel is not entered.
No fresh E+ result is inferred from R160, and no historical main comparison
CSV is updated. The data cover two sources and one Seed, not stable
promotion, independent confirmation, a P-GRB comparison or a universal
impossibility theorem. No automatic backup mechanism or seed/grid study
is started to spend unused capacity.

## Verification, identities, costs and delivery

The separate final saved-evidence audit is by the same agent, not an
independent person. It checks actual source/PE/DLL/input identities,
common physical rows/types and penalty, denominator/zero coverage,
complete Starts, original-J routes, source scope and all failed fees.
The initial archive-selection and zero-only construction failures remain
in their original trees/receipts; correctness repairs are distinguished
from a major scientific recipe revision.

Measured full bridge PE SHA256: `567e8c34d578843adf19e5958c36b63dcf92bd60d75b889db1d5fd2334a34598`.
Verified matching C++ commit: `1fafb6e2a4a3569cbb312a2f94738f822d2da500`.
Revised RN-P PE SHA256: `52ef690873f9f4d4c71f7695c2164380647a2c8f686ec044046c1a08c0cdb0f0`; C++ commit `006103fa7a3f5f7a09ff3621ee54c2c1ad7bab9f`.
Gurobi 13.0.2 DLL SHA256: `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
The OS module receipt records the actual loaded DLL path. Build flags
retain inherited GNU C++17/warnings, with no optimization, fast-math or
tolerance change. Later delivery builds are not performance samples.
Source, measured executable, scientific snapshot and delivery commits
are separate. The exact measured changed-source bytes are retained.

Closed scientific outer costs, including every failure, scientific
readback and necessary verification, are in cost_report.json against
86400s capacity. Nested Runtime/Work/callback validation are decompositions
and are not added again. Compile and public recovery/push costs are
separate. Capacity is not a minimum spend.

Closed science: **5455.093317711260 / 86400 seconds**; compilation/dependency setup: **280.674543300644 seconds**, separately.

The new-only public carrier excludes commercial runtime, licenses and
protected user metadata. Old inputs and parent provenance use fixed
commit/member/SHA references. One finite anonymous new-artifact recovery
and bounded metadata cleanup are recorded by the delivery commit.

See [mathematical/paper section](../../docs/round161_native_rn.md),
[history and increment](history_dedup.md), [decision](decision.json),
[full goal](goal.md), [final review](final_review.json) and
[continuation/publication](RESUME.md).
