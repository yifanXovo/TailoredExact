"""Four explicit mechanisms; serial own-H arms on the unchanged R146 PE."""
import copy
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round148_read import verify
from round148_common import *

configure()


def freeze(batch, positions, reason):
    configure()
    assert not budget()['unclosed']
    target = OUT / f'{batch}_matrix.json'
    assert not target.exists()
    manifest_path = OUT / 'candidate_manifest.json'
    manifest = inherited._candidate(manifest_path)
    source = read(ROOT / 'results/unified_exact_round137/matrix_frozen.json')
    by = {g['launch']['id']: g['launch'] for g in source['groups']
          if g['launch']['method'] == 'S2' and g['launch']['seed'] == 0}
    groups = []
    for i, spec in enumerate(positions, 1):
        old = by[spec['role']]
        launch = copy.deepcopy(old)
        panel = launch['panel']
        seed, method = spec.get('seed', 0), spec['method']
        assert method in ('D', 'D_SHARED_S')
        stock, gd = False, True
        cap = spec.get('cap', panel['cap_seconds'])
        panel.update(gurobi_seed=seed, cap_seconds=cap, round148_method=method,
                     round138_stock_rlt=stock, round146_gd=gd,
                     panel_kind='Round148 independent GD/stock; complete own H')
        camp = OUT / ('campaign_' + batch) / f'{i:03}'
        camp.mkdir(parents=True, exist_ok=False)
        armid = f'R148_{batch}_{i:03}_{spec["role"]}_S{seed}_{method}'
        destination = camp / 'raw' / armid
        command = [v.replace(old['destination'], str(destination)) for v in old['command']]
        command[0] = manifest['production_PE']
        for flag, value in [('--gurobi-seed', seed), ('--time-limit', cap - 6),
                            ('--process-wall-time-limit', cap)]:
            command[command.index(flag) + 1] = str(value)
        if stock:
            command += ['--round138-stock-rlt']
        command += ['--round146-gd', 'on', '--round148-shared-s', 'on' if method == 'D_SHARED_S' else 'off']
        assert all(flag not in command for flag in ['--round140-counts', '--round141-count-proof',
            '--round142-count-products', '--round143-rn', '--round144-projection', '--round145-projection'])
        launch.update(number=1, group_number=i, global_launch_number=i,
            method=method, R147_method='GD', R148_method=method, seed=seed,
            binary_layer='R148-new-PE', version='candidate', panel=panel,
            panel_kind=panel['panel_kind'], destination=str(destination), cap_seconds=cap,
            hard_stop_seconds=cap - 2, command=command, arm_id=armid, stage=batch, AM_threshold=.08)
        identity = dict(schema='round148-own-complete-lifecycle-v1',
            prereg=dict(common=dict(COMMON, gurobi_seed=seed), candidate_binary=manifest['production_PE'],
                        candidate_binary_sha256=manifest['production_PE_SHA']),
            prereg_sha256=hashlib.sha256(json.dumps(dict(batch=batch, positions=positions,
                reason=reason), sort_keys=True).encode()).hexdigest(),
            runner_sha256=sha(__file__), source_hashes=manifest['source_hashes'],
            candidate_binary_sha256=manifest['production_PE_SHA'], dll_sha256=DLL_SHA,
            measured_source_commit=manifest['source_commit'], delivery_base_commit=BASE,
            launches=[launch], candidate_manifest_path=str(manifest_path),
            candidate_manifest_SHA=sha(manifest_path), stage=batch, no_cross_arm_information=True)
        write(camp / 'identity.json', identity)
        groups.append(dict(position=i, stage=batch, group=camp.relative_to(OUT).as_posix(),
            arm_id=armid, identity_SHA=sha(camp / 'identity.json'), launch=launch))
    helpers = inherited.helper_bindings()
    helpers.update({p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / 'scripts').glob('round148_*.py')
                    if p.stem in ('round148_campaign', 'round148_read', 'round148_common')})
    write(target, dict(UTC=utc(), batch=batch, groups=groups, selection_reason=reason,
        candidate_manifest_SHA=sha(manifest_path), helpers=helpers,
        new_nominal_caps=sum(g['launch']['cap_seconds'] for g in groups), Seed_default=0,
        H_seed=20260626, serial=True, threads=1, affinity_mask=4, all_own_H=True))


def admission(batch):
    path = OUT / f'{batch}_matrix.json'
    matrix = read(path)
    gate = read(OUT / 'review' / f'{batch}_admission.json')
    assert gate['decision'] == 'ACCEPT' and gate['matrix_SHA'] == sha(path)
    assert gate['independent_nonimplementer_review'] or batch.startswith('qualification')
    assert matrix['candidate_manifest_SHA'] == sha(OUT / 'candidate_manifest.json')
    inherited._candidate(OUT / 'candidate_manifest.json')
    for name, digest in matrix['helpers'].items():
        assert sha(ROOT / name) == digest, name
    return matrix


def arm(batch, position):
    group = admission(batch)['groups'][position - 1]
    camp = OUT / group['group']
    assert sha(camp / 'identity.json') == group['identity_SHA']
    identity = read(camp / 'identity.json')
    launch = identity['launches'][0]
    destination = Path(launch['destination'])
    assert not (destination / 'verification_closeout.json').exists()
    if not destination.exists():
        tick, creation = inherited.inherited.process_origin()
        inherited.supervised(launch, identity, tick)
        finish_producer(launch, tick, creation)
    else:
        assert (destination / 'producer_receipt.json').exists() and (destination / 'producer_seal.json').exists(), \
            'Inspect unsealed producer; never repeat Optimize'
    value = verify(launch, identity)
    write(OUT / 'runtime_status.json', dict(UTC=utc(), batch=batch, position=position,
        arm_id=launch['arm_id'], certificate=value['arm']['certificate'], U=value['arm']['U'], L=value['arm']['L']))
    print(json.dumps(value['arm']), flush=True)


def run(batch, stop_after=None):
    configure()
    for group in admission(batch)['groups']:
        if stop_after is not None and group['position'] > stop_after:
            break
        if (Path(group['launch']['destination']) / 'verification_closeout.json').exists():
            continue
        label = f'{batch}_{group["position"]:03}'
        assert not (OUT / 'fees' / label).exists(), 'Inspect prior fee; never repeat'
        write(OUT / 'active_position.json', dict(UTC=utc(), batch=batch, position=group['position'],
            fee_label=label, arm_id=group['arm_id']))
        assert metered(label, 'diagnostic' if batch.startswith('qualification') else 'native', [PYTHON, '-B', __file__, 'arm', batch, group['position']],
            group['launch']['cap_seconds'] + 120, group['launch']['cap_seconds'] + 1800) == 0
    write(OUT / f'{batch}_run_return.json', dict(UTC=utc(), budget=budget()))


def qualification():
    freeze('qualification', [dict(role='K-20-S', method='D_SHARED_S', cap=90)],
        'One short actual own-root append/cache/GD-SHA/Native/Start lifecycle check, not a performance cell')
    write(OUT/'review/qualification_admission.json', dict(decision='ACCEPT',
        matrix_SHA=sha(OUT/'qualification_matrix.json'),independent_nonimplementer_review=False,
        reason='Independent production static review and actual C++/writer/Native/Start qualifications pass'))


def k35():
    freeze('k35', [dict(role='K-35-U', method=m, cap=2400) for m in ('D','D_SHARED_S')],
        'E1 all-five optimized increments; test K35 difficult incumbent/bound tradeoff on the same new PE. One added own-root row/LP; full windows retained.')


if __name__ == '__main__':
    if sys.argv[1] == 'arm':arm(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1] == 'run':run(sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else None)
    else:globals()[sys.argv[1]]()
