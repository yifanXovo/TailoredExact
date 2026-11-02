"""Finite result-dependent extension, with a single unchanged GD candidate."""
import shutil
from round147_campaign import freeze
from round147_common import *


def extension():
    configure()
    assert not budget()['unclosed']
    full = read(OUT / 'reports/full.json')
    assert len(full['new_arms']) == 3 and not full['pending']
    comparisons = {r['role']: r for r in full['comparisons'] if r['transition'] == 'B_to_D'}
    pressure = comparisons['R-B35-S-T2']
    assert pressure['delta_U'] < 0 and pressure['delta_L'] > 0
    reason = ('Keep the same standalone GD candidate. Core RB35 improves U by 2.5415%, raises supported L by '
        '.000489200547 and lowers gap by 1.8026 percentage points versus sealed same-PE BASE; '
        'K20 keeps the same U and remains open with slightly lower L, so it does not retain STOCK certificates. '
        'This is a real independent hard-role benefit with an unresolved proof/coverage tradeoff, '
        'not a claim that D dominates S/SD. First check RX20 B/D certificate stability; '
        'only then enter the already frozen K35 B/D pair to test another hard role and important regressions. '
        'No new mechanism, tuning, full K35 factorial or extra seed is selected.')
    stage = OUT / 'stages'
    stage.mkdir(parents=True, exist_ok=True)
    for old, new in [('reports/full.json', 'core_full.json'), ('cost_report.json', 'core_cost.json'),
                     ('reports/verified_U_trajectories.csv', 'core_U_trajectories.csv')]:
        assert not (stage / new).exists()
        shutil.copyfile(OUT / old, stage / new)
    write(OUT / 'stage_core_decision.json', dict(UTC=utc(), decision='ENTER_LIMITED_D_EXTENSION',
        candidate='GD', uniform=True, STOCK=False, GD=True, candidate_unchanged=True,
        core_report_SHA=sha(stage / 'core_full.json'), comparisons=comparisons,
        reason=reason, prior_spend=budget()['G1_seconds'], new_nominal_caps=7200,
        first_stage='RX20 B/D, cap1200 each', second_stage='K35 B/D, cap2400 each, conditional on RX20',
        Optimize=0, Native_load=0))
    freeze('extension', [dict(role='R-X20-S-T1', method='BASE', cap=1200),
        dict(role='R-X20-S-T1', method='GD', cap=1200), dict(role='K-35-U', method='BASE', cap=2400),
        dict(role='K-35-U', method='GD', cap=2400)], reason)
    print(json.dumps(dict(stage='extension', matrix_SHA=sha(OUT / 'extension_matrix.json'), budget=budget())))


def enter_k35():
    configure()
    assert not budget()['unclosed']
    matrix = read(OUT / 'extension_matrix.json')
    endpoints = [read(Path(g['launch']['destination']) / 'round135_endpoint.json') for g in matrix['groups'][:2]]
    assert all(r['certificate'] and r['H_complete'] and r['native_proof_qualified'] for r in endpoints)
    assert abs(endpoints[0]['U'] - endpoints[1]['U']) <= 1e-8
    write(OUT / 'stage_RX_decision.json', dict(UTC=utc(), decision='ENTER_FROZEN_K35_B_D_PAIR',
        candidate='GD', candidate_unchanged=True, RX20_endpoints=endpoints,
        reason='RX20 retains certification at the same U. Small certificate/verification clock differences are not decisive; '
        'now test the same D on the second hard role using the registered full cap2400 B/D windows.',
        extension_matrix_SHA=sha(OUT / 'extension_matrix.json'), new_remaining_nominal_caps=4800,
        budget=budget(), no_extra_seed_or_RNP_bridge=True, Optimize=0, Native_load=0))
    print('RX20 stability gate passed; enter the unchanged registered K35 pair')


if __name__ == '__main__':
    globals()[sys.argv[1]]()
