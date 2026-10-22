"""Exactly ten frozen serial groups; never rerun a sealed producer."""
from round129_common import *
from round129_campaign import prepare_group

def prepare():
    identity();m=read(OUT/'input_manifest.json');protocol=read(OUT/'experiment_manifest.json')
    by={p['id']:p for p in m['roles']}
    for g in protocol['groups']:
        p=by[g['role']['id']]
        for k,v in g['role'].items():assert p[k]==v,(p['id'],k)
        if not (OUT/g['name']/'identity.json').exists():prepare_group(g['name'],'E2',p,g['methods'],g['seed'])
    adapters={p:sha(ROOT/p) for p in ['scripts/round129_campaign.py','scripts/round129_common.py','scripts/round129_formal.py',
        'scripts/round128_evidence.py','scripts/round127_evidence.py','scripts/round122_evidence.py']}
    plans=[read(OUT/g['name']/'identity.json') for g in protocol['groups']]
    for g,i in zip(protocol['groups'],plans):
        assert [l['method'] for l in i['launches']]==g['methods']
        for l in i['launches']:
            cmd=l['command'];mode='p' if l['method']=='P' else l['method'].lower()
            assert cmd[0]==str(E2) and cmd.count('--round127-mode')==1 and cmd[cmd.index('--round127-mode')+1]==mode
            assert '--round128-mode' not in cmd and '--round127-p-parameters' not in cmd
            assert cmd[cmd.index('--gurobi-seed')+1]==str(g['seed'])
            assert cmd[cmd.index('--time-limit')+1]==str(l['cap_seconds']-6)
    write(OUT/'argv_freeze.json',dict(UTC=utc(),full_plans=plans,formal_arms=30,Optimize=0,PE_SHA=E2_SHA,DLL_SHA=DLL_SHA,
        actual_modes=['p','mb','ms2'],round128_mode_not_present=True,each_own_H_and_cold_P=True))
    write(OUT/'execution_binding.json',dict(UTC=utc(),protocol_SHA=sha(OUT/'experiment_manifest.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        E2_identity_SHA=sha(OUT/'E2_identity.json'),groups={g['name']:sha(OUT/g['name']/'identity.json') for g in protocol['groups']},
        adapters=adapters,formal_methods=['P','MB','MS2'],formal_arms=30,formal_pairs=30,serial=True))
    print('THIRTY_ARGV_FROZEN; no formal producer started')

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
        print(json.dumps(dict(group=name,action='START_OR_READ_ONLY_RESUME',remaining_nominal=remaining(),budget=budget())),flush=True)
        label=name.replace('/','_');attempt=len(list((OUT/'fees').glob(label+'*')))+1
        assert attempt==1,'A failed group requires a separately recorded engineering decision, never automatic retry'
        rc=metered(label+'_01','formal',[PYTHON,ROOT/'scripts/round129_campaign.py',name],reservation=remaining()+2400)
        if rc:raise SystemExit(rc)
    (OUT/'RESUME.md').write_text('Round129: all 30 fixed formal arms sealed. No extra experiments authorized. Analysis, separate review, manuscript, Draft PR, one public empty-root recovery and safe owned cleanup remain.\n',encoding='utf-8')
    print('ALL_30_FORMAL_ARMS_SEALED',flush=True)

if __name__=='__main__':{'prepare':prepare,'run':run}[sys.argv[1]]()
