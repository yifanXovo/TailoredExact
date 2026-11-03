"""Four frozen, serial complete own-H B/D arms on the unchanged R149 PE."""
import copy
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round150_read import verify
from round150_common import *


def freeze():
    configure()
    assert not budget()['unclosed']
    target = OUT/'confirmation_matrix.json'
    assert not target.exists()
    manifest_path = OUT/'candidate_manifest.json'
    manifest = inherited._candidate(manifest_path)
    source = read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
    by = {g['launch']['id']:g['launch'] for g in source['groups']
          if g['launch']['method']=='S2' and g['launch']['seed']==0}
    positions = [dict(role=r, method=m) for r in ['N-C20-U', 'N-B35-S'] for m in ['B', 'D']]
    reason = ('Two fixed known/exposed R137 configurations not used to select GD; preserve original '
              'lambda=.15, physical horizons, complete own-H and paired caps. '
              'Freeze all four before inspecting any Round150 D result. No default clarification pair.')
    groups = []
    for i, spec in enumerate(positions, 1):
        old = by[spec['role']]
        launch = copy.deepcopy(old)
        panel = launch['panel']
        method, gd, cap = spec['method'], spec['method']=='D', old['cap_seconds']
        assert cap == (1200 if panel['V']==20 else 2400)
        assert panel['lambda']==.15 and panel['pickup_seconds']==panel['drop_seconds']==60
        assert sha(ROOT/panel['input_path']) == panel['input_sha256']
        panel.update(gurobi_seed=0, round150_method=method, round138_stock_rlt=False,
            round146_gd=gd, round149_penalty_feedback=False, known=True, exposed=True,
            used_in_GD_selection=False, panel_kind='Round150 fixed known/exposed GD confirmation; complete own H')
        camp = OUT/'campaign_confirmation'/f'{i:03}'
        camp.mkdir(parents=True, exist_ok=False)
        armid = f'R150_{i:03}_{spec["role"]}_S0_{method}'
        destination = camp/'raw'/armid
        command = [v.replace(old['destination'], str(destination)) for v in old['command']]
        command[0] = manifest['production_PE']
        command += ['--round146-gd', 'on' if gd else 'off', '--round149-penalty-feedback', 'off']
        assert all(flag not in command for flag in ['--round138-stock-rlt', '--round148-shared-s',
            '--round140-counts', '--round141-count-proof', '--round142-count-products',
            '--round143-rn', '--round144-projection', '--round145-projection', '--round135-ap'])
        launch.update(number=1, group_number=i, global_launch_number=i,
            method='S2' if method=='B' else 'GD', R147_method='BASE' if method=='B' else 'GD',
            R150_method=method, seed=0, binary_layer='R149-reused-PE/R150-wrapper', version='candidate',
            panel=panel, panel_kind=panel['panel_kind'], destination=str(destination),
            command=command, arm_id=armid, stage='confirmation', AM_threshold=.08)
        identity = dict(schema='round150-own-complete-lifecycle-v1',
            prereg=dict(common=dict(COMMON, gurobi_seed=0), candidate_binary=manifest['production_PE'],
                        candidate_binary_sha256=manifest['production_PE_SHA']),
            prereg_sha256=hashlib.sha256(json.dumps(dict(positions=positions, reason=reason),sort_keys=True).encode()).hexdigest(),
            runner_sha256=sha(__file__), source_hashes=manifest['source_hashes'],
            candidate_binary_sha256=manifest['production_PE_SHA'], dll_sha256=DLL_SHA,
            measured_source_commit=manifest['source_commit'], delivery_base_commit=BASE,
            launches=[launch], candidate_manifest_path=str(manifest_path), candidate_manifest_SHA=sha(manifest_path),
            stage='confirmation', no_cross_arm_information=True,
            old_method_definition=manifest['method_definition_science'],
            original_frozen_launch=old, original_fixed_science=SCIENCE137)
        write(camp/'identity.json', identity)
        groups.append(dict(position=i, group=camp.relative_to(OUT).as_posix(), arm_id=armid,
                           identity_SHA=sha(camp/'identity.json'), launch=launch))
    helpers = inherited.helper_bindings()
    for name in ['round150_campaign.py','round150_read.py','round150_common.py','round149_context.py','round149_read.py']:
        helpers['scripts/'+name] = sha(ROOT/'scripts'/name)
    write(target, dict(UTC=utc(), groups=groups, selection_reason=reason,
        candidate_manifest_SHA=sha(manifest_path), helpers=helpers, new_nominal_caps=7200,
        Seed=0, H_seed=20260626, serial=True, threads=1, affinity_mask=4, all_own_H=True,
        no_original_H_LP_incumbent_or_cross_arm_injection=True, optional_clarification_not_started=True))
    print(json.dumps(dict(frozen=str(target), SHA=sha(target), Optimize=0)))


def admission():
    path = OUT/'confirmation_matrix.json'
    matrix = read(path)
    gate = read(OUT/'review/confirmation_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(path)
    assert gate['independent_nonimplementer_review']
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name, digest in matrix['helpers'].items():
        assert sha(ROOT/name)==digest, name
    return matrix


def arm(position):
    group = admission()['groups'][position-1]
    camp = OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA']
    identity = read(camp/'identity.json')
    launch = identity['launches'][0]
    destination = Path(launch['destination'])
    assert not (destination/'verification_closeout.json').exists()
    if not destination.exists():
        tick, creation = inherited.inherited.process_origin()
        inherited.supervised(launch, identity, tick)
        finish_producer(launch, tick, creation)
    else:
        assert (destination/'producer_receipt.json').exists() and (destination/'producer_seal.json').exists(), \
            'Inspect unsealed producer; never repeat Optimize'
    value = verify(launch, identity)
    write(OUT/'runtime_status.json', dict(UTC=utc(), position=position, arm_id=launch['arm_id'],
        certificate=value['arm']['certificate'], U=value['arm']['U'], L=value['arm']['L']))
    print(json.dumps(value['arm']), flush=True)


def run(stop_after=4):
    configure()
    for group in admission()['groups']:
        if group['position']>stop_after:
            break
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():
            continue
        label = f'confirmation_{group["position"]:03}'
        assert not (OUT/'fees'/label).exists(), 'Inspect prior fee; never repeat'
        write(OUT/'active_position.json', dict(UTC=utc(), position=group['position'],
            fee_label=label, arm_id=group['arm_id']))
        # Reserve the complete cap plus explicit verification overhead before entering.
        assert metered(label, 'native', [PYTHON, '-B', __file__, 'arm', group['position']],
            group['launch']['cap_seconds']+600, group['launch']['cap_seconds']+1800)==0
    write(OUT/'confirmation_run_return.json', dict(UTC=utc(), budget=budget()))


if __name__ == '__main__':
    if sys.argv[1]=='arm': arm(int(sys.argv[2]))
    elif sys.argv[1]=='run': run(int(sys.argv[2]) if len(sys.argv)>2 else 4)
    else: freeze()
