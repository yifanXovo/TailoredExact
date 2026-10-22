"""Exactly six serial groups and 24 once-only complete formal producers."""
from round130_common import *
from round130_campaign import prepare_group

def prepare():
    identity();protocol=read(OUT/'experiment_manifest.json');roles={p['id']:p for p in read(OUT/'input_manifest.json')['roles']}
    for g in protocol['groups']:
        assert roles[g['role']['id']]==g['role']
        if not (OUT/g['name']/'identity.json').exists():prepare_group(g['name'],'E3',g['role'],g['methods'],g['seed'])
    plans=[read(OUT/g['name']/'identity.json') for g in protocol['groups']]
    for g,i in zip(protocol['groups'],plans):
        assert [l['method'] for l in i['launches']]==g['methods']
        for l in i['launches']:
            cmd=l['command'];method=l['method']
            assert cmd[0]==str(E3) and '--round128-mode' not in cmd and '--round127-p-parameters' not in cmd
            if method=='PS':assert '--round112-ens-start-compact' in cmd and '--round127-mode' not in cmd
            else:
                assert cmd.count('--round127-mode')==1 and cmd[cmd.index('--round127-mode')+1]==dict(P='p',S2='ms2',S2R='s2-root')[method]
            assert cmd[cmd.index('--gurobi-seed')+1]==str(g['seed'])
            assert cmd[cmd.index('--time-limit')+1]=='1194' and cmd[cmd.index('--process-wall-time-limit')+1]=='1200'
    adapters={p:sha(ROOT/p) for p in ['scripts/round130_campaign.py','scripts/round130_common.py','scripts/round130_formal.py',
        'scripts/round130_evidence.py','scripts/round128_evidence.py','scripts/round127_evidence.py','scripts/round122_evidence.py']}
    write(OUT/'argv_freeze.json',dict(UTC=utc(),full_plans=plans,formal_arms=24,typed_comparisons=30,Optimize=0,PE_SHA=sha(E3),DLL_SHA=DLL_SHA,
        actual_modes=dict(P='p',PS='round112_ens_start_compact; round127=off',S2='ms2',S2R='s2-root'),each_own_H_and_cold_P=True))
    write(OUT/'execution_binding.json',dict(UTC=utc(),protocol_SHA=sha(OUT/'experiment_manifest.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        E3_identity_SHA=sha(OUT/'E3_frozen.json'),groups={g['name']:sha(OUT/g['name']/'identity.json') for g in protocol['groups']},
        adapters=adapters,formal_methods=['P','PS','S2','S2R'],formal_arms=24,formal_pairs=30,serial=True))
    print('ALL_24_ARGV_FROZEN; no formal producer started')

def remaining():
    return sum(len(g['methods'])*g['role']['cap_seconds'] for g in read(OUT/'experiment_manifest.json')['groups']
        if not (OUT/g['name']/'reconstructed.json').exists())

def run():
    identity();binding=read(OUT/'execution_binding.json');gate=read(OUT/'review/performance_admission.json')
    assert gate['decision']=='ACCEPT' and gate['execution_binding_SHA']==sha(OUT/'execution_binding.json')
    assert sha(OUT/'experiment_manifest.json')==binding['protocol_SHA'] and sha(OUT/'input_manifest.json')==binding['input_manifest_SHA']
    for p,h in binding['adapters'].items():assert sha(ROOT/p)==h,p
    for g in read(OUT/'experiment_manifest.json')['groups']:
        name=g['name'];assert sha(OUT/name/'identity.json')==binding['groups'][name]
        if (OUT/name/'reconstructed.json').exists():continue
        assert budget()['remaining_outer_seconds']>=remaining()+2400
        label=name.replace('/','_')+'_01'
        assert not (OUT/'fees'/label).exists(),'External failure requires an explicit budgeted whole-group recovery record; never an automatic retry'
        print(json.dumps(dict(group=name,action='START',remaining_nominal=remaining(),budget=budget())),flush=True)
        rc=metered(label,'formal',[PYTHON,ROOT/'scripts/round130_campaign.py',name],reservation=remaining()+2400)
        if rc:raise SystemExit(rc)
    (OUT/'RESUME.md').write_text('Round130 all 24 fixed formal arms sealed. No extra experiment authorized. Analysis, independent delivery review, manuscript/PDF, Draft PR, one public recovery and owned cleanup remain.\n',encoding='utf-8')
    print('ALL_24_FORMAL_ARMS_SEALED',flush=True)
if __name__=='__main__':{'prepare':prepare,'run':run}[sys.argv[1]]()
