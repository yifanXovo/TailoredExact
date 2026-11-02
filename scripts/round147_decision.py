"""Freeze one uniform, reviewable paper candidate from the completed evidence."""
import csv
from round147_common import *


def main():
    configure()
    assert not budget()['unclosed']
    full = read(OUT / 'reports/full.json')
    assert not full['pending'] and len(full['new_arms']) == len(full['sealed_R146_references']) == 7
    assert full['new_Native_Optimize'] == full['new_Native_returned'] == 34
    comparisons = {r['role']: r for r in full['comparisons'] if r['transition'] == 'B_to_D'}
    assert all(r['candidate_U'] <= r['reference_U'] + 1e-10 for r in comparisons.values())
    trajectories = list(csv.DictReader((OUT / 'reports/verified_U_trajectories.csv').open(encoding='utf-8')))
    summaries = []
    for role, comparison in comparisons.items():
        events = [r for r in trajectories if r['role'] == role and r['method'] == 'GD']
        match = next(r for r in events if float(r['U']) <= comparison['reference_U'] + 1e-10)
        final = next(r for r in events if abs(float(r['U']) - comparison['candidate_U']) <= 1e-10)
        early = next(r for r in reversed(events) if float(r['producer_seconds']) <= 2000)
        summaries.append(dict(role=role, B_final_U=comparison['reference_U'],
            first_D_meets_B_final_U_seconds=float(match['producer_seconds']), U_at_match=float(match['U']),
            D_final_U_first_available_seconds=float(final['producer_seconds']),
            D_last_witness_before_2000_seconds=float(early['producer_seconds']), U_before_2000=float(early['U']),
            clock='committed physical witness availability on producer wall; not a certificate clock',
            offline_observation_only=True, algorithm_not_switched_or_capped_at_these_times=True))
    write(OUT / 'reports/trajectory_summary.json', dict(Optimize=0, Native_load=0, facts=summaries))
    decision = dict(UTC=utc(), schema='round147-finite-uniform-adoption-v1', study_complete=True,
        decision='RECOMMEND_D_AS_UNIFORM_PAPER_ENHANCEMENT_CANDIDATE',
        uniform_recommendation='Standalone GD (D)', candidate='GD', STOCK=False, GD=True,
        candidate_unchanged_through_core_and_extension=True,
        reviewable_adoption_proposal=dict(entry='scripts/paper_s2_gd_only.py',
            profile='config/gi_tbc_gd_round147.json', policy='Use the same D profile on every role; mathematical omission rules only',
            stable_R137_entry_and_manuscript_preserved=True, automatic_default_replacement=False,
            merge_or_default_replacement_is_for_author_review=True),
        primary_reference='stable BASE (B), controlled with the unchanged R146 PE',
        evidence_scope=dict(new_complete_arms=7, sealed_R146_same_PE_references=7,
            known_roles=4, Gurobi_seed=0, H_seed=20260626, threads=1,
            K20_RX20_RB35_four_cells_complete=True, K35_only_B_D=True,
            cross_round_does_not_mean_identical_host_load=True, independent_validation_set=False,
            multi_seed_robustness_claim=False, full_routing_hull_claim=False),
        B_to_D=comparisons, trajectory_summary_SHA=sha(OUT / 'reports/trajectory_summary.json'),
        full_report_SHA=sha(OUT / 'reports/full.json'), cost_report_SHA=sha(OUT / 'cost_report.json'),
        new_Native_Optimize=34, new_Native_returned=34, new_standalone_LP_Optimize=0,
        new_source_optimizations=0, new_production_builds=0,
        charged_outer_seconds=budget()['G1_seconds'], ceiling_seconds=18000,
        open_T_cert_is_null=True, no_time_factorial_or_aggregate_score=True,
        source_commit=read(OUT / 'candidate_manifest.json')['source_commit'],
        PE_SHA=read(OUT / 'candidate_manifest.json')['production_PE_SHA'])
    decision.update(prose())
    write(OUT / 'candidate_decision.json', decision)
    write(OUT / 'RESUME.json', dict(UTC=utc(), state='SCIENCE_COMPLETE_FINAL_REVIEW_AND_DELIVERY_PENDING',
        decision=decision['decision'], budget=budget(), entered_new_arms=7, all_new_arms_verified=True,
        new_Native_calls_returned=34, no_other_experiment_queued=True,
        next_action='Generate paper/report, obtain independent final review, semantic checks, pack, commit/push, '
                    'create English Draft PR, anonymous public recovery, bounded cleanup and final readback',
        never_repeat_existing_fee_or_sealed_arm=True))
    print(json.dumps(dict(decision=decision['decision'], budget=budget())))


def prose():
    return dict(
        decision_discussion=(
            'Recommend standalone GD (D) as one uniform paper-enhancement candidate for author review. '
            'Against controlled stable BASE, it improves the physical incumbent on both entered difficult roles '
            '(RB35 by 2.5415%, K35 by 3.1283%) and reduces both relative gaps. It avoids the measured STOCK+GD '
            'combination\'s RB35 incumbent regression. The important remaining tradeoff is K35 supported L: '
            'D lowers it by .011455146913 (2.0300%), even while U and gap improve. K20 keeps the same U and '
            'remains open with slightly weaker L; RX20 retains certification with a 2.341246s delay. '
            'These measured disadvantages are retained rather than hidden in an aggregate score. The two '
            'hard-role incumbent/gap gains, with no observed incumbent regression on any of the four roles, '
            'support this bounded uniform recommendation; this is not a general proof-speed or dominance claim. '
            'D does not retain STOCK\'s strong K20 certificate benefit. S/SD remain valuable sealed research '
            'references, and no role-specific D/SD switching is proposed. The concrete proposal is the new '
            'standalone entry/profile for the next enhanced paper version; stable R137 and its manuscript '
            'retain their original bytes pending author review of the Draft PR.'),
        core_discussion=(
            'K20 B and D both return U=.7168065462777502 and remain open after their complete cap1200 '
            'windows. Supported L changes from .7047916969720031 to .7042027654726336; the relative gap '
            'increases from 1.676163% to 1.758324% (+.082160 percentage points). This is not a useful '
            'standalone certificate gain. The sealed same-PE S/SD cells certify the same U in '
            '94.261389/74.916420s; their strong proof advantage is preserved as a real counterpoint. '
            'RB35 D instead returns U/L=.3358835889496765/.21947515015073324 against sealed same-PE '
            'B=.34464262559194814/.2189859496034747. U improves 2.5414838421%, L rises .0004892005473, '
            'and gap falls from 36.459993% to 34.657376% (-1.8026165231 percentage points). The L gain '
            'is small; the main independent benefit is physical incumbent quality. All four RB35 cells '
            'are open. D improves U and gap against SD but has lower L than SD\'s .23349894443616206, '
            'so it does not dominate the combination at both ends. Actual new D models have two GD '
            'rows and zero STOCK rows; the comparison is not inferred from method labels.'),
        trajectory_discussion=(
            'The committed physical-witness records locate the hard-role benefit in finding better '
            'incumbents, not certification. RB35 D already has U=.3372904684849699 at 668.391s, below '
            'B\'s eventual final U, and reaches its own final U at 1346.250s. B reaches its different '
            'final U at 2366.781s. K35 D first beats B\'s final U at 1338.656s with U=.6791034678575588; '
            'B reaches its final U at 1758.516s. D then has U=.6767988451958106 at 1686.187s and '
            'finds the final .671179796420249 at 2364.047s. That last improvement is near cap and is '
            'disclosed; the earlier strict gains establish that the benefit does not arise solely '
            'from the last seconds. Different-quality final-U discovery times are not convergence '
            'speedup ratios. K20 reaches the common final U at 224.546s for B and 417.765s for D. '
            'D\'s 16.338s lower complete total there is mainly a verification-cost decrease '
            '(49.467897 to 33.581330s), not faster proof. All 14 entered/reused formal cells have '
            'zero outer splits. Native root-after-cuts values, simplex, Work and node differences '
            'describe changed search but do not identify a unique cause. For example, K35\'s printed '
            'root bound rises .42856 to .44681 and root simplex increases 5188 to 11374, while final '
            'supported L is lower; stronger root information does not force stronger final proof.'),
        historical_discussion=(
            'R146\'s positive S→SD findings remain unchanged: K20 certifies about 20.52% sooner at the '
            'same U; RX20 retains certification with a small absolute 2.702614s certificate gain; '
            'RB35 improves U by 5.8283%, increases L by .004317345 and lowers gap by 4.6781 percentage '
            'points. Against BASE, that same SD pressure result had U higher by 9.6257%, L higher by '
            '.014512995 and gap larger by 1.7379 percentage points, a mixed tradeoff rather than '
            'two-end regression. RX20 SD\'s approximately 3.02e-9 positive U−L remains certified under '
            'the original R134 policy; no new floating-point repair or solve is introduced. R138\'s '
            'K15/K20 STOCK certificate benefits, its disclosed V2 transport identity in the finite '
            'Seed1 evidence, R144\'s RN-P K35 gains and R145\'s structural complementarity/root-retention '
            'results remain at their original versions. The Seed1 history is not a pure seed-only '
            'intervention, and no universal STOCK regression law is inferred. The strong historical '
            'RN-P K35 incumbent remains a research reference; no new matched RN-P bridge or claim of '
            'D beating every research variant is made. Fixed-domain K20 LP interaction remains a '
            'numerical fact, not complete-search synergy or general supermodularity.'),
        extension_discussion=(
            'After both core roles completed, the real RB35 independent incumbent gain justified '
            'the finite extension with the same D profile. RX20 B/D both certify U=.6453250303858205. '
            'Certificate times are 22.324898/24.666144s: D is slower by 2.341246s (10.4872%); complete '
            'totals are 23.674241/26.345340s (+2.671099s). This small absolute delay preserves the '
            'certified role and is not used as a one-cell veto. The frozen K35 B/D cap2400 pair then '
            'returns U=.6928543586313136/.671179796420249, supported L=.5642907958373754/'
            '.5528356489241707 and gap=18.555640%/17.632257%. U improves 3.1282999004% and gap falls '
            '.9233832014 percentage points, while L decreases .0114551469132 (2.0300077545%). '
            'Both remain open; total costs 2374.928960/2378.192407s differ by 3.263447s and are '
            'not convergence times. This is an explicit incumbent/bound tradeoff, not two-end '
            'dominance. Stop the finite selection study here. Seven new full own-H arms and the '
            'seven sealed references are sufficient for this scoped candidate recommendation; no '
            'automatic 24-configuration/120-position panel, full K35 factorial, extra seed, K15 '
            'boundary, current S/SD clock repeat or RN-P bridge is needed. There is no material '
            'decision resting on a tiny cross-round clock difference. Unused budget is not '
            'unfinished work. Wider claims would require separately justified validation; that '
            'is not asserted or queued by this completed study.'),
        navigation_discussion=(
            'Seven new own-H positions establish real standalone hard-role incumbent gains: '
            'RB35 U improves 2.54% and K35 U improves 3.13%, with smaller relative gaps on both. '
            'K35 supported L is 2.03% lower, K20 does not gain certification, and RX20 retains '
            'certification with a small 2.34s delay. Recommend one uniform standalone-GD paper '
            'enhancement candidate for author review, while preserving stable R137 and the '
            'strong historical STOCK/combination references. The claim is limited to four '
            'known Seed0 roles, with no instance-specific switching.'),
    )


if __name__ == '__main__':
    main()
