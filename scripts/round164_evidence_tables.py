"""Readable tables of the completed, separately identified Seed observations.

This is a presentation of qualified readback, not a new experiment or a
selection rule. It imports no solver and is run only after all 24 positions.
"""
from round164_common import *


def number(value):
    if value is None:
        return '—'
    if isinstance(value, bool):
        return 'yes' if value else 'no'
    if isinstance(value, int):
        return str(value)
    return format(value, '.17g')


def table(headers, records):
    return '\n'.join([
        '| ' + ' | '.join(headers) + ' |',
        '| ' + ' | '.join('---' for _ in headers) + ' |',
        *('| ' + ' | '.join(str(value).replace('|', '\\|') for value in row) + ' |'
          for row in records),
    ])


def run():
    assert read(OUT/'panel_complete.json')['arms'] == 24
    assert read(OUT/'science_identity.json')['PASS']
    arms = read(OUT/'reports/three_seed_arms.json')
    pairs = read(OUT/'reports/three_seed_comparisons.json')
    configs = read(OUT/'reports/within_configuration.json')
    summary = read(OUT/'reports/summary.json')
    arrival = read(OUT/'reports/primal_target_arrival.json')
    assert len(arms) == len(arrival) == 36 and len(pairs) == 18 and len(configs) == 6
    ids = [value['id'] for value in read(OUT/'input_references.json')['roles']]
    order = {name: index for index, name in enumerate(ids)}
    arms.sort(key=lambda value: (order[value['id']], value['seed'], value['method']))
    pairs.sort(key=lambda value: (order[value['id']], value['gurobi_seed']))
    arrival.sort(key=lambda value: (order[value['id']], value['gurobi_seed'], value['method']))
    lines = [
        '# Qualified finite three-Seed evidence',
        '',
        'There are six mathematical inputs, twelve new B/P pairs at Seeds 1/2, '
        'and six separately identified historical Seed0 pairs. These eighteen '
        'pairs are repeated observations within six inputs. No endpoint is '
        'composed across runs; descriptive medians are not additional solutions '
        'or certificates. Seed0 is R163 historical data, not a new R164 run.',
        '',
        'Numbers below retain binary64 reporting precision. Endpoint signs use '
        'the frozen 1e-7 tolerance. ΔU=B−P, so negative favors B; ΔL=B−P, '
        'so positive favors B. Every OPEN state and adverse direction is retained.',
        '',
        '## Certificate denominators',
        '',
        table(['Gurobi Seed', 'Source', 'B CERT /6', 'P CERT /6', 'Joint CERT /6'], [
            [seed, 'R163 historical' if seed == 0 else 'R164 new',
             summary['seeds'][str(seed)]['methods']['B']['CERT'],
             summary['seeds'][str(seed)]['methods']['P']['CERT'],
             summary['seeds'][str(seed)]['joint_CERT']] for seed in (0, 1, 2)]),
        '',
        '## Own-run feasible and proof endpoints',
        '',
        'Raw search L is result.json.lower_bound; qualified search L is the '
        'original-domain qualified reader endpoint. B has no E+ floor, so its '
        'final proof L equals qualified search L. Signed gap and original '
        'relative gap belong to that same run.',
        '',
        table(['Input', 'Seed', 'Method', 'State', 'Physical U', 'Raw search L',
               'Qualified search L', 'Final proof L', 'U−L', 'Original relative gap'], [
            [a['id'], a['seed'], a['method'], a['state'], number(a['U']),
             number(a['raw_search_L']), number(a['qualified_search_L']),
             number(a['final_proof_L']), number(a['U']-a['L']), number(a['relative_gap'])]
            for a in arms]),
        '',
        '## Paid clocks, H and diagnostic solver effort',
        '',
        'All times are seconds. T_cert is the actual qualified paid producer '
        'close and is absent for OPEN. T_verify is separate; new-run T_verify '
        'also includes the outer reader trailer. H is already inside T_produce '
        'and is not added again. Native Work, nodes and Runtime are diagnostic '
        'counters and do not replace paid wall time.',
        '',
        table(['Input', 'Seed', 'Method', 'T_cert', 'T_produce', 'T_verify',
               'T_total', 'Own H', 'Native Work', 'Native nodes'], [
            [a['id'], a['seed'], a['method'], number(a['T_cert']),
             number(a['T_produce']), number(a['T_verify']), number(a['T_total']),
             number(a['H_seconds']), number(a['Native_Work']), number(a['Native_nodes'])]
            for a in arms]),
        '',
        '## Paired endpoint directions',
        '',
        table(['Input', 'Seed', 'B state', 'P state', 'ΔU', 'ΔU sign', 'ΔL', 'ΔL sign'], [
            [p['id'], p['gurobi_seed'], p['B_state'], p['P_state'],
             number(p['delta_U']), p['delta_U_sign'], number(p['delta_L']), p['delta_L_sign']]
            for p in pairs]),
        '',
        '## Within-input descriptive summaries',
        '',
        table(['Input', 'B CERT /3', 'P CERT /3', 'ΔU signs S0/S1/S2',
               'Median ΔU', 'ΔU range', 'ΔL signs S0/S1/S2', 'Median ΔL', 'ΔL range'], [
            [c['id'], c['B_CERT'], c['P_CERT'], '/'.join(map(str, c['delta_U']['signs'])),
             number(c['delta_U']['median']),
             '['+number(c['delta_U']['minimum'])+', '+number(c['delta_U']['maximum'])+']',
             '/'.join(map(str, c['delta_L']['signs'])), number(c['delta_L']['median']),
             '['+number(c['delta_L']['minimum'])+', '+number(c['delta_L']['maximum'])+']']
            for c in configs]),
        '',
        '## Conditional paid certificate times',
        '',
        'The following table contains only joint CERT pairs, with the exact '
        'intersection denominators above. ΔT=B−P; the ratio is B/P. A difference '
        'is substantive only when |ΔT|≥max(10s,10% of the faster time). This '
        'conditional comparison supplies no full-panel speedup or OPEN '
        'convergence time.',
        '',
        table(['Input', 'Seed', 'B T_cert', 'P T_cert', 'ΔT', 'B/P',
               'Substantive scale /s', 'Meets scale'], [
            [p['id'], p['gurobi_seed'], number(p['B_T_cert']), number(p['P_T_cert']),
             number(p['paid_cert_absolute_difference']), number(p['paid_cert_B_over_P']),
             number(p['material_time_scale_seconds']), number(p['material_time_difference'])]
            for p in pairs if p['joint_CERT']]),
        '',
        '## Uniform offline known-feasible targets',
        '',
        'Each u_ref was frozen before the first new Optimize as the better '
        'qualified Seed0 physical U. It is a known feasible value, not an '
        'optimum, and never enters production. An interval [0,u] supplies a '
        'conservative upper bound on a saved verifiable attainment; it is not '
        'an exact discovery or earliest-other-emitter timestamp. Absence means '
        'not observed within that run, with censoring at its own T_produce. '
        'Receipt-qualified journal bounds and source clock details remain '
        'in primal_target_arrival.json and ../target_clock_contract.json.',
        '',
        table(['Input', 'Seed', 'Method', 'u_ref', 'Observed reached', 'Disposition',
               'Paid lower /s', 'Paid upper /s', 'Window end /s'], [
            [a['id'], a['gurobi_seed'], a['method'], number(a['u_ref']),
             number(a['reached_observed']), a['disposition'], number(a['paid_clock_lower_seconds']),
             number(a['paid_clock_upper_seconds']), number(a['window_end_T_produce'])]
            for a in arrival]),
        '',
        'Sources: complete_arms.json (24 new arms), three_seed_arms.json (all '
        '36 identified arms), three_seed_comparisons.json, within_configuration.json, '
        'primal_target_arrival.json, ../Seed0_reuse_qualification.json and '
        '../historical_member_access.json. Paid failures and independent review '
        'costs are separately retained in ../cost_report.json. E+ was not retested.',
        '',
    ]
    destination = OUT/'reports/seed_evidence.md'
    destination.write_text('\n'.join(lines), encoding='utf-8')
    print('Wrote completed finite-Seed evidence tables; no Optimize or new sample.')


if __name__ == '__main__':
    run()
