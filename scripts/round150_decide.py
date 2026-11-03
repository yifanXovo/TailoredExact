"""Record the finite scientific judgment after all four frozen arms close."""
from round150_common import *


def main():
    full = read(OUT/'reports/full.json')
    assert len(full['formal_arms'])==4 and not full['pending']
    pairs = {r['role']:r for r in full['comparisons']}
    c,n = pairs['N-C20-U'],pairs['N-B35-S']
    assert c['B_certificate'] and c['D_certificate'] and c['B_U']==c['D_U']
    assert not n['B_certificate'] and not n['D_certificate']
    cpf = read(OUT/'CPF_decision.json')
    cpf.update(next_information='In a future study, qualify a single fixed-dual CPF implementation '
        'on top of D+PF, including actual transport, Start and child scope. The most informative '
        'bounded complete comparison is D+PF versus D+PF+CPF on the original RB35 objective, '
        'which previously exposed PF incumbent cost. Do not dispatch methods by role and do '
        'not start that experiment in Round150.')
    write(OUT/'CPF_decision.json',cpf)
    d = dict(decision='RETAIN_LIMITED_UNIFORM_PAPER_CANDIDATE_RESTRICT_CLAIMS',
        reason=('Retain standalone GD only as a finite uniform candidate for paper discussion, '
            'without broadening the R147 enhancement claim or replacing stable GI-TBC. '
            'The R147 selected hard-role U gains remain real (K35 3.12830%, RB35-T2 2.54148%). '
            'The two additional known/exposed roles preserve the positive-objective certificate '
            'on N-C20-U, but D takes 43.73383% more T_cert with identical U. On N-B35-S '
            'D improves supported L 0.16464% while losing U 2.24371% and enlarging signed '
            'gap about15.46345%; both stay open. These ordinary but relevant losses do not '
            'trigger the severe double-open reference rule and do not invalidate GD, yet '
            'they add no complete U/proof-speed superiority outside the selection roles. '
            'A limited candidate with disclosed tradeoffs is defensible; broad replacement '
            'or robustness is not. This is not an all-cases-must-win rule.'),
        paper_conclusion=('Standalone GD remains a limited uniform candidate for discussion, '
            'rather than a replacement for stable GI-TBC. Its selected-role incumbent gains '
            'coexist with new costs: N-C20-U retains the same U and accepted certificate but '
            'takes 43.73383 percent longer to certify; N-B35-S gains 0.16464 percent in '
            'supported L but loses 2.24371 percent in U, and its signed gap is about15.46345 '
            'percent larger. Both hard-role arms remain open. The new confirmation does '
            'not establish complete superiority outside selection. The same D profile is '
            'retained uniformly, with no role-based dispatch and no broad robustness claim.'),
        continue_as_limited_uniform_paper_candidate=True,
        strengthen_claim_beyond_R147_selection=False,recommend_broad_replacement=False,
        stable_B_primary=True,automatic_default_change=False,role_based_dispatch=False,
        known_exposed_new_roles=2,blind_validation=False,multi_seed_robustness=False,
        certificates_preserved_on_new_positive_role=True,
        severe_double_open_reference_triggered=any(r['serious_double_open_regression'] for r in pairs.values()),
        adoption_not_decided_by_reference_threshold_alone=True,
        no_clarification_reason='The two frozen roles answer certificate preservation and a distinct '
            'physical hard-input tradeoff. There is no remaining specific question that would '
            'change this deliberately finite positioning; another role or rescue run is not purchased.')
    write(OUT/'candidate_decision.json',dict(UTC=utc(),study_complete=True,D=d,CPF=cpf,
        new_complete_arms=4,new_diagnostic_LPs=3,optional_clarification_entered=False,
        stable_R137_unchanged=True,new_production_source=False,new_build=False,
        no_more_Optimize_queued=True,automatic_merge=False,
        methods_uniform=True,independent_tasks_can_close=True,
        production_source=SOURCE,PE_SHA=read(OUT/'candidate_manifest.json')['production_PE_SHA']))
    external = read(OUT/'infra/external_costs.json')
    for row in external['processes']:
        if row['label']=='independent_prelaunch_review':
            row['outer_seconds'] = 13.598493
            row['basis'] = ('3.598493s measured independent process enclosing times, including '
                'the type supplement, plus disclosed conservative10s unmetered qualification '
                'reading allowance. Nested script times are not added. Prose-only review '
                '.4334406s is separately reported theory/authoring, not another experimental fee.')
    write(OUT/'infra/external_costs.json',external)
    print(json.dumps(dict(D=d['decision'],CPF=cpf['decision'],no_more_Optimize=True)))


if __name__=='__main__':
    main()
