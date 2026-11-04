"""Report assembly and fee arithmetic only; no solver or producer import."""
import csv
from round152_common import *

def documents():
    configure();external=[]
    for p in sorted((OUT/'review').glob('*fee.json')):
        r=read(p);seconds=r.get('outer_experimental_seconds',0.)
        if seconds:external.append(dict(kind='verification',outer_seconds=seconds,source=p.relative_to(OUT).as_posix()))
    write(OUT/'infra/external_costs.json',dict(processes=external,nested_times_not_recharged=True))
    costs=budget();assert not costs['unclosed'];audit=read(OUT/'reports/audit.json');table=[]
    review=read(OUT/'review/final_scientific_review.json')
    assert review['disposition']=='ACCEPT_OFFLINE_SCIENTIFIC_STAGE' and not review['scientific_blockers']
    for role in ['N-B35-S','K-35-U','N-C20-U']:
        d=read(OUT/'domains'/role/'domain.json');values={v:read(OUT/'LP'/f'{role}_{v}'/'result.json')['L'] for v in ['AP','strong','strongCP2','strongRN','cycle_08','global']}
        gl=read(OUT/'global'/f'{role}_global'/'result.json');cycle=read(OUT/'cycles'/f'{role}_cycle'/'result.json')
        proj=read(OUT/'projection'/f'{role}_strongCP2'/'result.json');last=gl['iterations'][-1]
        values.update(role=role,B=d['B_L'],global_parent=gl['parent'],parent_L=read(OUT/'LP'/f'{role}_{gl["parent"]}'/'result.json')['L'],
                      incremental_over_RN=values['global']-values['strongRN'],relative_increment_over_RN_percent=100*(values['global']/values['strongRN']-1),
                      residual_row_gain=gl['LP']['gain'],cycle_outer_seconds=read(OUT/'fees'/f'cycles_{"NB35" if role=="N-B35-S" else "K35" if role=="K-35-U" else "NC20"}_001'/'receipt.json')['G1_seconds'],
                      global_outer_seconds=read(OUT/'fees'/f'global_{"NB35" if role=="N-B35-S" else "K35" if role=="K-35-U" else "NC20"}_001'/'receipt.json')['G1_seconds'],
                      final_direction_L=last['lower'],final_direction_U=last['upper'],final_direction_threshold=read(OUT/'global'/f'{role}_global'/f'iter{last["iteration"]:02}'/'pricing/result.json')['threshold'],
                      original_strong_joint_compatible=proj['full_oracle_projection_feasible'],joint_mixture_columns=len(proj['paths']))
        table.append(values)
    write(OUT/'reports/evidence_table.json',table)
    with (OUT/'reports/evidence_table.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    failures=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        r=read(p)
        if r['exit_code']!=0:failures.append(dict(label=p.parent.name,outer_seconds=r['G1_seconds'],exit_code=r['exit_code'],stderr=(p.parent/'stderr.log').relative_to(OUT).as_posix()))
    write(OUT/'failures.json',dict(attempts=failures,all_preserved_and_charged=True,
          interpretations={'lp_NB35_AP_001':'syntax failure before Optimize','lp_NC20_AP_001':'same syntax failure before Optimize',
          'qualify_001':'qualification script syntax failure before Optimize','aggregate_checks_001':'fixture incorrectly demanded identical floating outward endpoints; replaced by exact containment',
          'strongCP_NB35_001':'explicit zero coefficients differed from Native sparse readback; zero terms removed before the admitted CP runs; no Optimize in failed attempt',
          'small_001':'exact-basis verifier attempted Fraction(infinite UB); finite bounds only, one returned LP retained',
          'normalized_qualify_001':'fixture compared an absolute gap with relative MIPGap=1e-4; preserved/reused returned MIP and actual UNDECIDED label, no repeat Optimize'}))
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=costs['G1_seconds'],ceiling_seconds=86400,remaining_seconds=costs['remaining_G1_seconds'],
          experiment=costs,build_seconds=0.,complete_arms=0,Native_Optimize=audit['new_native_calls'],Native_returned=audit['returned'],
          known_B_Optimize_new=0,K35_AP_Optimize_new=0,failures_charged=len(failures),
          includes_construction_DP_pricing_LP_MIP_qualification_failure_and_required_verification=True,
          nested_Runtime_Work_not_added=True,old_fees_not_recharged=True,authoring_and_public_IO_separate=True))
    sources={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'scripts').glob('round152*.py'))}
    write(OUT/'source_manifest.json',dict(UTC=utc(),fixed_dependency_base=BASE,research_sources=sources,
          actual_per_process_source_bytes='engineering/source_snapshots and engineering/source_bytes',
          initial_pre_snapshot_runs='First AP/preparation/qualification runs precede automatic snapshots; their admitted matrices, rows, points and explicit failed source copies are retained. No production performance identity is inferred from a later source.',
          production_source='c26382d9bf1d4edde538a01c62e57ba563cf865c',production_PE_SHA=audit['production_PE_SHA'],Native_DLL_SHA=DLL_SHA,
          source_science_commit='Bound by fixed-science publication record after commit; dependency base is not the new research source identity.'))
    decision=dict(UTC=utc(),study_complete=True,stage='offline_object_and_expression_research',production_entered=False,complete_arms=0,
          stable_algorithm='R137 GI-TBC',new_default=False,inventory_object_has_new_information=True,
          independent_scientific_review=review['disposition'],independent_review_file='review/final_scientific_review.json',
          exact_small_same_marginal_gap='53/1080',exact_small_global_floor_gap='1/480',
          stronger_than_all_historical_formulations=False,whole_family_redundancy_proved=False,oracle_undecided_is_negative=False,
          real_free_LP_increment_over_RN={r['role']:r['incremental_over_RN'] for r in table},
          production_gate_reason='Deliver the explicitly allowed object-level stage: point separation is reliable, but eight lifted rows mostly move marginals; N-B35 gains only a scalar floor, K35 residual gains disappear against old RN, and N-C20 has a small residual-row gain. No uniform production composition and complete-cost benefit have been established. Diagnostic AP/GD/count/RN blocks are not automatically promoted.',
          not_claimed=['new full algorithm speedup','new physical U or terminal supported L','whole-epigraph invalidity or redundancy','oracle uncomputability','all historical normalized/disjunctive hull dominance'],
          next_question='Can a potential chosen against several current optimal-face marginals, rather than one sparse optimum, yield a materially stronger free root bound with a small paid row collection?')
    write(OUT/'candidate_decision.json',decision)
    lines=['| Role | Reused B | AP | AP+GD/stock/count/CP | + old RN | Eight-row loop before RN | Final after RN and qualified new row/floor |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for r in table:lines.append(f"| {r['role']} | {r['B']:.12f} | {r['AP']:.12f} | {r['strongCP2']:.12f} | {r['strongRN']:.12f} | {r['cycle_08']:.12f} | {r['global']:.12f} |")
    evidence='\n'.join(lines)
    report=f'''# Round152: resource-feasible integer objective epigraphs

The offline object-level study is complete. It establishes nonduplicate
objective information beyond the declared AP/GD/count/stock reference, two
qualified pricing formulations, and finite consequences on three complete
saved LP domains. Stable R137 GI-TBC remains the paper algorithm. Production
and new complete B/J arms were not entered; no new physical U, terminal
supported L, certificate or complete-method speedup is claimed.

## Structural result

At fixed compatible marginals, Theta(s)=H_AP(s)+Gamma(s). Expected penalty is
already fixed by AP; Gamma is the minimum expected nonminimal Gini completion
over the same hard-resource joint distribution. The independently verified
heterogeneous three-station example has an exact feasible extension through
all 117 rows and 46 variables of the declared old strong inventory block.
Its unique feasible common distribution gives a same-marginal objective gap
**53/1080**. Exhaustive evaluation of 49 feasible inventories also gives a
separate global-integer-floor gap **1/480**. The equal-target R133 control is
closed by the strong reference. See [the full proof](mathematical_analysis.md)
and [independent exact theorem](review/exact_small_theorem.md).

The small theorem is scoped to the complete declared inventory block. It
does not claim a route extension or dominance over every historical RN/source
projection or count disjunction. R55 penalty-cover, R135 AP, R138--142 count
and common-product results, R143--145 normalization and R146--151 local/full
boundaries retain their original positive and negative evidence.

## Same-domain complete free LP evidence

{evidence}

Every original variable, objective coefficient, cutoff and old row is
retained; no g, selector, product, route or auxiliary is fixed to manufacture
gain. Both N-domain B roots and K35's matching R135 AP result are reused,
with no baseline Optimize. The K35 complete-domain equality and its saved
AP point were checked before reuse. AP, all supported count ranges, CP and
RN references are diagnostic controls, not adopted online components.

N-B35's new integer-objective scalar floor raises the RN reference from
0.386737186565 to 0.392978953519 ({table[0]['relative_increment_over_RN_percent']:.6f}%). Its original
bin oracle LB/UB are 0.392978953519/0.396046548957. Eight lifted residual rows
and a full-support normalized-priced row add no further root objective value.
K35's eight-row microgain is more than covered by old RN; the new full-support
row then separates the saved RN point but gives no distinguishable root gain.
N-C20's full-support row raises the RN reference by 0.000267616518
({table[2]['relative_increment_over_RN_percent']:.6f}%). These are initial free-LP results, not Native
MIP root-after-cuts or terminal proof bounds.

All three original strong-reference marginals have explicit hard-resource
joint mixtures satisfying the actual Gini upper bound. The later global
comparisons also reconstruct compatible mixtures. Thus the reported positive
point separations concern objective information, not projection infeasibility.
One row can cut a saved optimum and still permit another optimum at the same
value; the repeated loops explicitly observe this limitation.

## Oracle deepening, cost and uncertainty

The reference oracle uses fully covered positive-denominator bins and hard
integer resource MILPs, with an independent exact unary-DP fallback for every
unsolved bin and a separate exact zero-stock component. It records denominator
error, MIP gap, lower bounds and true-stock upper bounds separately. A bounded
residual master proposes potentials; only global qualified pricing LBs are
installed. Negative potentials and negative intercepts are retained.

The first refinement prices sparse active states and covers the whole parent
complement by an exact flagged hard-resource DP. A deterministic coefficient
lift reduces inactive penalties. N-B35's first discovery has 78 active versus 537
full states, but later directions become harder and free LPs keep moving their
marginals. Eight support rounds cost 444.078/82.955/52.914 outer seconds for
N-B35/K35/N-C20, respectively; these costs include their LPs, projections,
masters, pricing and coefficient construction, not just Native Runtime.

The second refinement makes the historical RN formulation integer in its
selectors. On positive stock its common reciprocal t satisfies tS=1 exactly;
there is no denominator approximation. Hard resource, gamma_L's max semantics
and the separate zero state remain. The accompanying continuous RN+scaled-stock
reference prevents old normalization from being presented as new information.
The final full-support discovery/LP stages cost 137.216/6.522/4.614 outer seconds.
The longer N-B35 MIP returns a useful separating lower bound before resolving
its whole MIP gap; this is sufficient for its valid row.

The saved audit counts **{audit['new_native_calls']}/{audit['returned']} returned new Native calls**, including
masters, projections, small qualifications and all failed-attempt calls.
There are 41 new complete saved-model LP optimizations and one reused AP result.
The pricing classification includes 28 separations, 21 direction-nonseparations,
two resolved prices and one **undecided small qualification price**. The last
has a valid exact bracket but the configured relative MIP gap does not meet
the stricter fixed price-resolution threshold; it is retained as undecided.
No unresolved direction is called a negative family result. See
[the machine audit](reports/audit.json), [pricing records](reports/pricing_results.json)
and [expense ledger](cost_report.json).

Final new experimental outer cost, including independent scientific review, is
**{costs['G1_seconds']:.9f} seconds / 86400**. The independent review accepted
the offline scientific stage with no scientific blockers. Nested Work and
Runtime, historical experiments and pure authoring/public I/O are not charged
again. Build cost is zero. All seven failed outer attempts are preserved and
paid: syntax errors, a zero-term sparse readback mismatch, and three verification
fixture issues; none produced an admitted invalid row. The normalized tiny
result was reused after its fixture correction, not reoptimized to force a
preferred label. See [failures](failures.json).

## Stage decision

The object contains new information and has executable, qualified separation.
The tested small row collections yield limited extra free-LP strength after
the relevant old information is present. This stage does not establish a
uniform production composition with convincing complete-cost value. The task
explicitly permits an offline theoretical/object-level delivery, so no new
production entry, profile, PE or complete B/J panel is forced. This decision
does not assert that the entire epigraph is redundant or uncomputable.

The next focused question is whether a full-domain potential chosen against
several marginals on the current optimal face can improve the complete free
LP more consistently than a direction fitted to one sparse optimum. That
question can be addressed without reopening the old inventory-routing master
architecture or automatically promoting all diagnostic AP/GD/count/RN blocks.

## Identity and delivery

The new branch starts at verified R151 c6e930ffcb84f0c3801c651f28b5f7e8e2062f33;
main had not absorbed it. Research source files and per-process snapshots are
bound in source_manifest.json and engineering/source_snapshots. The unchanged
production source is c26382d9bf1d4edde538a01c62e57ba563cf865c; its retained PE SHA
is {audit['production_PE_SHA']}. The Native DLL SHA is {DLL_SHA}. Existing
production source, entries and profiles are byte-preserved. Seed 0 / Threads 1
is used throughout; own-H seed 20260626 is unchanged but no new H is run.

All new assets are under ExactEBRP-work. The original workspace and historical
user/raw assets are protected. New necessary carriers, fixed old member
references, one bounded public restore, English Draft PR and bounded cleanup
are recorded in [RESUME](RESUME.md). No merge, force push or old-history deletion
is part of this delivery. [Independent reviews](review) and the
[paper section](manuscript.tex) preserve the stage's scope.
'''
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    write(OUT/'reports/final_table.json',dict(rows=table,qualified=True,complete_arms_entered=False))
    print(json.dumps(dict(experiment_seconds=costs['G1_seconds'],failures=len(failures),LP_rows=len(table))),flush=True)

if __name__=='__main__':documents()
