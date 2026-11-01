"""Generate the concise scientific closeout from the retained authorities."""
from round144_common import *
def display(v,digits=12):return '' if v is None else format(v,f'.{digits}g')
def md_table(header,values):
    return '| '+' | '.join(header)+' |\n| '+' | '.join('---' for _ in header)+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in values)+'\n'
def main():
    assert not budget()['unclosed'];decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    lp=read(OUT/'reports/LP.json');full=read(OUT/'reports/full.json');m=read(OUT/'candidate_manifest.json');cost=read(OUT/'cost_report.json')
    assert not full['pending']
    order={r:i for i,r in enumerate(['K-20-S','K-35-U','R-X20-S-T1','R-B35-S-T2'])}
    arms=sorted(full['new_arms'],key=lambda r:(order.get(r['role'],99),r['seed'],['OFF','RNP','RN'].index(r['method'])))
    roots=md_table(['Role','BASE objective','RN objective','Compiled PC objective','RN gain retained'],[
        [r['role'],display(r['old_L']),display(r['RN_L']),display(r['compiled_PC_L']),display(r['compiled_retention_fraction'])] for r in lp['matched_roots']])
    outcomes=md_table(['Role / method','U','Supported L','Relative gap','Certificate'],[
        [r['role']+' / '+r['method'],display(r['U']),display(r['L']),display(r['relative_gap']),str(r['certificate'])] for r in arms])
    clocks=md_table(['Role / method','T_produce','T_cert','T_verify','T_total'],[
        [r['role']+' / '+r['method'],*[display(r[k],9) for k in ['T_produce','T_cert','T_verify','T_total']]] for r in arms])
    sizes=md_table(['Role / method','Presolved columns','Terminal nodes','Terminal Work','Source prep s'],[
        [r['role']+' / '+r['method'],r.get('presolved_columns',''),display(r['terminal_nodes'],9),display(r['terminal_Work'],9),display(r['source_preparation_seconds'],8)] for r in arms])
    source_commit=m['source_commit'];hours=cost['charged_new_experiment_seconds']/3600
    text=f'''# Round144: RN information projected into original selectors and G

The decision is **{decision['decision']}**. {decision['summary']}

Stable R137 GI-TBC, its paper entry/profile and earlier research entries remain
available. The RN-P binary flag defaults off; its separate research launcher
explicitly selects this candidate. This is
a finite representation-cost experiment, not a claim that normalized Gini
information or root compression is universally fast.

## Information retained by one original-variable row

{roots}
Displayed table values are rounded. The actual compiled interval writer loses only
{display(lp['matched_roots'][0]['compiled_loss'])} and
{display(lp['matched_roots'][1]['compiled_loss'])} in matched root objectives.
K35 removes 1170 persistent RN columns/2340 RN rows; RX20-T1 removes 354/708.
Each useful compact model adds one selector/G row and no new columns. All old
matrix rows, objective and penalty, cutoff, supports and G domain are retained.
The two RN source LPs newly save optimal source Pi/RC/basis; the other two
primary LPs reoptimize their matched compact models. R143's raw did not
contain those complete dual attributes. Two additional
compact optimizations qualify the actual C++ coefficients after Native transport.

The single saved actual RX20 upper AM-lookahead child has inherited-PC and
full-RN objectives both {display(lp['actual_descendant']['full_RN_child_L'])}.
Only its RN comparison is newly optimized; the compact optimization is reused
from the sealed health qualifier. There are seven new standalone LP solves in
total. This one no-loss child does not establish full-tree equality.

Box support and original-box coefficient compensation establish validity for
actual binary64 multipliers, including residual extension coefficients and
tiny-term deletion. Independent Fraction checks and actual Native readback
verify the final rows. Exact same-root optimal-value preservation requires
exact optimal primal/dual solutions, the same P and objective. It is the
standard dual-aggregation principle already present in R104; it is neither a
new theorem nor the complete RN projection. R104 ACTIVE's full regression and
its 4349 auxiliary LPs / 3644 DPs per ACTIVE/SHADOW remain prior negative evidence.

## Structural content and scalar floors

On the declared three-station fixed-selector continuous Gini/stock/count/product
cross-section, the RN optimum for objective g+p, with independent p>=0, is
exactly 5/12. The old point g=1/3, p=1/12 satisfies that matched scalar floor;
the selector/G Rank-PC still excludes it by 1/4. Exact old-row feasibility,
the RN lower proof and an attaining extension are retained in the local witness.
This strictly distinguishes the two on that declared local block. There is
no claimed exact separating point for the complete routing P, no universal
floor dominance and no use of floating primal ObjVal as a paid proof floor.
The six saved-point Rank-PC violations were finitely reconstructed without
Optimize and agree with the goal's displayed decimals. Different legal
station subgradients give their own certificate identities and sparsities;
they are not represented as byte-identical to the absent supplemental ZIP.

## Complete same-PE results

{outcomes}
{clocks}
Times are seconds. Open T_cert entries are intentionally empty. T_produce
includes each run's own H, the once-root source where applicable, row
construction, formal solves and in-process checks. T_verify contains all
mandatory sealed-raw postverification; T_total is their actual complete clock.
Same-role pairs verify equal physical inputs/fleets, H semantics and H fleet,
source/PE, Seed and full cap. Native return ObjBoundC and the external merged
supported L remain separate fields in reports/new_arms.csv; signed U-L is
retained without clipping. No historical fleet, point or bound is injected.

{sizes}
Nodes, Work, simplex, presolved size, AM decisions and trajectories describe
the observed searches. Fewer nodes or equal LP roots alone do not establish
complete benefit, and Work/node is not a causal measurement of column cost.

{decision.get('role_interpretation','')}

## Implementation, qualification and limits

RN-P obtains one production-capped RN continuous source after the run's own H
and initial root are known. Actual mixed row directions and scaling are
checked. The source's types are restored and its handle explicitly discarded;
formal models use distinct canonical hashes, original integer columns and
unchanged Start mapping. Only compatible narrower input/G/cutoff/support
domains inherit the PC. All source calls remain in Native quality, lifecycle
and cost audits; they are excluded from formal controller-bound reconstruction.
A zero RN dual block is a uniformly omitted tautology. Nonpositive proved
denominator bounds uniformly omit the source. Every complete run clears its
source/cache state; no instance/size/time-specific rule is introduced.

The initial K20 qualifier failed on a zero aggregate before durable dual
serialization. A second K20 producer exposed the disposable source's missing
integer-restoration lifecycle count; it remains unqualified. V5 restores the
source types before disposal. RX20's active-PC health producer then passed;
reader-only formal/source ledger separation was recovered from sealed raw,
without repeating Optimize. All failed producers/readers and costs remain.
Delayed health-verification latency is retained but is not a performance cell.
The complete-run/qualification ledgers contain
{full['all_entered_observed_Native_Optimize']} observed Native Optimize calls,
all returned; {cost['failed_qualification_observed_Native_Optimize']} belong to
the two unqualified attempts. These counts include once-root sources but
exclude the seven separately reported standalone LPs. Reader-only recoveries
perform zero Optimize and retain their actual outer costs.
Compiled mixed-sense/free-equality/sign-repair/signed-box/deletion/reset fixtures,
actual writer/Native rows, physical complete Start, off matrix and scope
rejection checks are preserved. Independent pre-full and final reviews have
separate evidence and identities.

Measured production source is `{source_commit}`; PE SHA256 is
`{m['production_PE_SHA']}`. The measured link uses verified inherited object
and archive lineage and newly compiled affected units. CMake explicitly links
the same projection arithmetic library for a clean build. The process and
commercial runtime binaries/licenses are not published.

## Cost, adoption and remaining scope

New experimental outer cost is **{cost['charged_new_experiment_seconds']:.9f}
seconds ({hours:.9f} hours) of 28800 seconds**. Failed qualification/readers,
once-root sources and all mandatory postverification are included. Nested
H/LP/MIP/Work observations are not charged a second time. Build time
({cost['build_seconds_separate']:.6f} seconds), exact offline arithmetic,
paper/PDF work and public I/O are separate. Pure setup/debug waiting is not
invented as extra Native compute; actual delayed qualification T_total remains
visible. All entered formal positions are preserved with their full windows.

{decision.get('optional_controls_and_stop_reason','')}

The continuation/delivery record identifies actual Draft PR/base/head, fixed
science, finite carrier/member recovery and post-PR current-round cleanup.
Local scientific acceptance and public byte readability are separate. Retained
new research assets stay under ExactEBRP-work; the original user tree and old rounds are
protected. No merge, force-push, historical deletion, email or submission is made.
'''
    if (OUT/'figures/K35_verified_U.png').exists():
        figure='''![K35 physical incumbent trajectories](figures/K35_verified_U.png)

The figure uses postqualified committed physical witnesses and their effective
availability on each producer wall clock. It does not relabel Native log time
as T_produce or T_total. Full supported L, signed gaps and complete verification
costs remain in the tables and full-precision reports.

'''
        text=text.replace('## Implementation, qualification and limits',figure+'## Implementation, qualification and limits')
    if (OUT/'figures/RB35_T2_verified_U.png').exists():
        figure='''![RB35-T2 physical incumbent trajectories](figures/RB35_T2_verified_U.png)

RB35-T2 emits no PC: its formal model and own-H identity match OFF. The
adverse endpoint remains part of the complete candidate's evidence. This
verified trajectory records the late OFF improvement; it establishes no
structural cause or general redundancy of RN.

'''
        text=text.replace('## Implementation, qualification and limits',figure+'## Implementation, qualification and limits')
    (OUT/'final_report.md').write_text(text,encoding='utf-8',newline='\n')
    (OUT/'LP_report.md').write_text('# Matched RN projection LPs\n\n'+roots+'\nActual compiled/transported coefficients are the reported authority. Full precision, models, duals and qualities are in reports/LP.json and the finite diagnostics carrier.\n',encoding='utf-8',newline='\n')
    print('Scientific report and LP summary generated from retained full-precision authorities')
if __name__=='__main__':main()
