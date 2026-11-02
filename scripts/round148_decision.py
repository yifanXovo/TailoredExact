"""Finite adoption decision from actual complete pairs; no solver imports."""
from round148_common import *


def main():
    configure();assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');assert not full['pending']
    by={r['role']:r for r in full['comparisons']};assert set(by)=={'K-35-U','R-B35-S-T2'}
    b=by['R-B35-S-T2']
    severe_U=max(.001,.05*abs(b['D_U']));severe_gap=max(.005,.25*abs(b['D_signed_gap']))
    assert b['delta_U']>=severe_U and b['delta_signed_gap']>=severe_gap
    complete='''The same-new-PE K35 pair gives a real bound/incumbent tradeoff. D returns U/L .676798845196/.545729444783; the candidate returns .679917519727/.558283855657. Supported L rises .012554410874 (2.300483%), physical U is .003118674531 worse (.460798%), and relative gap falls from 19.366079% to 17.889473% (-1.476606 percentage points). The signed gap falls .009435736343. Both remain open. Their accepted T_total values are 2378.764522/2379.834894s; this 1.070373s difference is not convergence or certification speed. The complete comparison justified one RB35 pressure pair, not promotion.

RB35-T2 answers that pressure question adversely. D returns U/L .335883588950/.219663876370; the candidate returns .371420783400/.220898439927. L rises only .001234563557 (.562024%), while physical U is .035537194450 worse (10.580212%). The signed gap grows from .116219712580 to .150522343473 (+.034302630893, about 29.52%); relative gap grows from 34.601188% to 40.526096% (+5.924908 percentage points). Both remain open. The accepted complete totals are 2378.591470/2379.626412s; their small difference is not a speed result. This is a serious regression under the inherited double-open rule: U loss exceeds max(.001,5% of D U), and signed-gap loss exceeds max(.005,25% of D signed gap).

All four formal arms retain their full cap2400 windows, complete independent own H and Seed0/Threads1. The candidate pays its normal root, construction/transport and one added root LP. Both roles have zero committed outer splits; Native target/search paths, Work, simplex and nodes remain separate observations. K35 initial LP increases .204187028164 to .209568159043, whereas printed Native root-after-cuts values are .44681/.44808. RB35 own-root LP increases .135292103721 to .1365597514 (rounded log value). These layers do not imply a monotone final search bound or incumbent. Native/trajectory changes locate observed gains and losses, without uniquely attributing them to a static row, a particular branch or AM. Candidate final U is worse on both roles, so neither candidate trajectory ever beats the corresponding D final U; saved committed trajectories retain the chronology.'''
    discussion='''Retain as research only; do not recommend the current shared-S one-row root mechanism as a uniform paper enhancement. The common-first-moment family is valid, strictly stronger than isolated GD, and supplies clear reoptimized LP information on every saved diagnostic domain. K35 adds useful final bound/gap information at a small incumbent cost. However, the serious RB35 incumbent/signed-gap regression fails the required retention question and is not offset by its small L gain. Keep the default-off implementation and reproducible evidence as a completed research result. Preserve R147 standalone D as its previously limited paper candidate and R137 as the stable default. Do not replace defaults or merge automatically.'''
    scope='''This closes the tested uniform one-row/one-added-own-root-LP implementation direction, not the entire mathematical common-S family. Two known Seed0 hard-role pairs are a finite selection study, not broad validation or a robustness claim. K20/RX20 complete proof pairs, extra seeds, more root cuts, high-deviation variants, RN/STOCK combinations and AM parameter rescues are not needed to overturn the observed important RB35 loss and are not queued. Unused experimental capacity is not unfinished work. The optional AM/no-strict information-retention question remains a separate possible future study; historical R47/R52 negative anchors and prior threshold experiments remain intact and are not rerun here.'''
    paper=r'''The common-first-moment rows improve all five matched LP values. In complete own-H search, K35 supported L improves 2.3005\% with a 0.4608\% worse physical U, reducing relative gap by 1.4766 percentage points. RB35 instead has a 10.5802\% worse U and only a 0.5620\% higher L; its relative gap rises by 5.9249 percentage points. Both pairs remain open. The latter serious incumbent/signed-gap regression rules out promotion of this uniform one-row root implementation. We retain the construction and LP evidence as a research result, preserve the limited standalone-D candidate and stable R137 version, and do not open a high-deviation, RN, STOCK or AM rescue grid. These observations do not invalidate the affine family or establish performance over unseen instances or seeds.'''
    write(OUT/'candidate_decision.json',dict(UTC=utc(),decision='RESEARCH_ONLY_SHARED_S_AFFINE_ROOT_NO_PROMOTION',
        goal_outcome=2,study_complete=True,decision_discussion=discussion,complete_discussion=complete,
        scope_discussion=scope,paper_conclusion_tex=paper,uniform_mechanism_frozen=True,
        candidate='Standalone D + one own-root common-S low affine/moment row',new_rows_max=1,added_root_LP_max=1,
        exact_validity=True,isolated_GD_strictness=True,saved_point_separations=5,
        fixed_domain_LPs=5,physical_diagnostic_instances=3,positive_LP_increments=5,extra_LP_iterations=0,
        formal_complete_arms=4,formal_complete_pairs=2,qualification_complete_arms=1,
        complete_Native_Optimize=full['complete_Native_Optimize'],complete_Native_returned=full['complete_Native_returned'],
        source_solves=0,baseline_reoptimization=0,serious_RB35_regression=True,
        inherited_serious_rule=dict(U_loss=b['delta_U'],U_threshold=severe_U,
            signed_gap_loss=b['delta_signed_gap'],signed_gap_threshold=severe_gap,both_conditions=True,
            relative_gap_not_substituted_for_signed_gap=True),
        retained_stable='R137',retained_limited_paper_candidate='R147 standalone GD (D)',
        new_uniform_recommendation=None,no_default_replacement=True,no_merge=True,
        no_further_experiment_queued=True,budget_at_decision=budget(),comparisons=full['comparisons']))
    print('Decision: research only; serious RB35 incumbent/signed-gap loss; stop new solves')


if __name__=='__main__':main()
