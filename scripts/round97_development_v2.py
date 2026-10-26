"""Frozen v2 development, conditional on audited real native qualification.

No optimization on import or prepare. Every launch uses the already qualified
v2 supervisor; no completed arm can be overwritten or restarted.
"""
import argparse
import json
import subprocess
from pathlib import Path
import round97_campaign_v2 as campaign
from round97_campaign_v2 import ROOT, OUT, BUILD, read, write, sha, ext, r90

CAMP = OUT / 'development02'
GATE = OUT / 'qualification03/gate.json'


def qualified():
    gate = read(GATE)
    assert gate['passed'] and gate['real_post_start_native_qualified']
    assert gate['independent_actual_model_vectors_passed']
    assert gate['combined_increment_observed'] and gate['feedback_continued_proof_observed']
    for path, expected in gate['bindings'].items():
        assert sha(ROOT/path) == expected, path
    q = read(OUT/'qualification03/identity.json')
    assert q['runner_sha256'] == sha(campaign.__file__)
    for path, expected in q['helper_hashes'].items():
        assert sha(ROOT/path) == expected, path
    assert q['prereg_sha256'] == sha(OUT/'research_state.md')
    assert q['revision_plan_sha256'] == sha(OUT/'revision02_plan.md')
    assert q['build_identity_sha256'] == sha(OUT/'production_v2_identity.json')
    assert q['source_hashes'] == campaign.bindings()
    assert q['candidate_binary_sha256'] == sha(BUILD/'ExactEBRP.exe')
    campaign.ready_build()
    return q


def prepare():
    ext.ensure_idle()
    assert not CAMP.exists()
    q = qualified()
    prior_path = ROOT/'results/unified_exact_round96/primal/identity.json'
    historical_path = ROOT/'results/unified_exact_round87/campaign/identity.json'
    fixed_path = ROOT/'results/unified_exact_round96/fixed_route_cases.json'
    prior, historical, fixed = map(read, [prior_path, historical_path, fixed_path])
    panels = {role: dict(next(r['panel'] for r in prior['launches'] if r['id']==role))
              for role in ['F5', 'V1', 'F2']}
    d7 = dict(next(r['panel'] for r in fixed['cases'] if r['role']=='D7'))
    historical_d7 = next(r['panel'] for r in historical['launches'] if r['panel']['id']=='D7')
    for key in ['input_sha256', 'instance_path', 'T_seconds', 'lambda', 'pickup_seconds', 'drop_seconds']:
        assert d7[key] == historical_d7[key]
    d7['input_path'] = d7['instance_path']
    d7['reference'] = historical['references']['D7']
    assert d7['reference']['optimizer_calls'] == 0
    panels['D7'] = d7
    assert [panels[r]['T_seconds'] for r in ['F5','D7','V1','F2']] == [7200,18000,7200,3600]
    schedule = [('F5',arm,3600) for arm in ['OLD-FEEDBACK','FEEDBACK','OFF','P-GRB']]
    schedule += [('D7',arm,3600) for arm in ['P-GRB','OFF','FEEDBACK']]
    schedule += [('V1',arm,1800) for arm in ['OFF','FEEDBACK','P-GRB']]
    schedule += [('F2',arm,900) for arm in ['FEEDBACK','P-GRB','OFF']]
    prereg = q['prereg']
    launches = []
    for role, arm, cap in schedule:
        panel = dict(panels[role], cap_seconds=cap)
        panel['instance_path'] = panel['input_path']
        assert sha(ROOT/panel['input_path']) == panel['input_sha256']
        number = len(launches)+1
        mode = 'off' if arm=='P-GRB' else 'observe' if arm=='OFF' else 'feedback'
        operator = 'r96' if arm=='FEEDBACK' else 'r83'
        dest = CAMP/'raw'/f'{number:02d}_{role}_{arm}'
        command = (r90.audited_runner_utilities.command_for(prereg,panel,arm,dest) if arm=='P-GRB'
                   else r90.command_for(prereg,panel,'ENS-C',dest)+
                   ['--round97-native-closure',mode,'--round97-native-operator',operator])
        launches.append(dict(number=number,id=role,arm=arm,mode=mode,operator=operator,
            panel=panel,destination=str(dest),stage='complete_development',
            cap_seconds=cap,hard_stop_seconds=cap-2,command=command))
    assert len(launches)==13 and sum(r['cap_seconds'] for r in launches)==33300
    identity = dict(q, schema='round97-v2-complete-development-v1',
        source_ref=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        launches=launches,maximum_starts=13,maximum_process_seconds=33300,
        runner_sha256=sha(campaign.__file__),development_runner_sha256=sha(__file__),
        helper_hashes=campaign.helper_bindings(),qualification_gate_sha256=sha(GATE),
        inherited_reference_bindings={p.relative_to(ROOT).as_posix():sha(p)
                                     for p in [prior_path,historical_path,fixed_path]},
        question='Four-role complete original proof comparison. F5 same-build old/combined operator attribution; D7 opportunity, V1 known regression role, F2 certification protection. No confirmation data used.',
        audit_reference_scope='Original compact zero-Optimize references only, matched input/physics. All timed arms use the same new v2 binary; no historical times reused.')
    write(CAMP/'identity.json', identity)
    print(json.dumps(dict(prepared='development02',starts=13,seconds=33300)))


def run(number):
    identity = read(CAMP/'identity.json')
    assert identity['development_runner_sha256']==sha(__file__)
    assert identity['qualification_gate_sha256']==sha(GATE)
    qualified()
    for path, expected in identity['inherited_reference_bindings'].items():
        assert sha(ROOT/path)==expected,path
    campaign.run('development02',number)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('--number',type=int)
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:run(args.number)
