"""Only the predeclared five serial groups; existing seals are never rerun."""
from round128_common import *
from round128_campaign import prepare_group

def prepare():
    gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
    assert gate['PE_SHA']==sha(E2) and source_bindings()==read(OUT/'E2_frozen.json')['source_bindings']
    for g in read(OUT/'experiment_manifest.json')['groups']:
        if not (OUT/g['name']/'identity.json').exists():prepare_group(g['name'],'E2',g['role'],g['methods'],g['seed'])
    write(OUT/'execution_binding.json',dict(UTC=utc(),protocol_SHA=sha(OUT/'experiment_manifest.json'),E2_frozen_SHA=sha(OUT/'E2_frozen.json'),
        groups={g['name']:sha(OUT/g['name']/'identity.json') for g in read(OUT/'experiment_manifest.json')['groups']},
        adapters={p:sha(ROOT/p) for p in ['scripts/round128_campaign.py','scripts/round128_evidence.py','scripts/round128_formal.py']},
        formal_methods=['P','MB','MD-R','MS2'],formal_arms=16,formal_pairs=17,serial=True))

def remaining():
    total=0
    for g in read(OUT/'experiment_manifest.json')['groups']:
        if not (OUT/g['name']/'reconstructed.json').exists():total+=len(g['methods'])*g['role']['cap_seconds']
    return total

def run():
    assert source_bindings()==read(OUT/'E2_frozen.json')['source_bindings']
    binding=read(OUT/'execution_binding.json')
    for p,h in binding['adapters'].items():assert sha(ROOT/p)==h
    for g in read(OUT/'experiment_manifest.json')['groups']:
        name=g['name'];assert sha(OUT/name/'identity.json')==binding['groups'][name]
        if (OUT/name/'reconstructed.json').exists():continue
        assert budget()['remaining_outer_seconds']>=remaining()+1800
        print(json.dumps(dict(group=name,action='START_OR_READ_ONLY_RESUME',remaining_nominal=remaining(),budget=budget())),flush=True)
        label=name.replace('/','_');attempt=len(list((OUT/'fees').glob(label+'*')))+1
        rc=metered(label+f'_{attempt:02d}','formal',[PYTHON,ROOT/'scripts/round128_campaign.py',name],reservation=remaining()+1800)
        if rc:raise SystemExit(rc)
    (OUT/'RESUME.md').write_text('Round128: all 16 fixed formal arms sealed. No additional experiment is authorized. Analysis, review, manuscript, PR, one empty-root recovery and safe owned cleanup remain.\n',encoding='utf-8')
    print('ALL_16_FORMAL_ARMS_SEALED',flush=True)

if __name__=='__main__':{'prepare':prepare,'run':run}[sys.argv[1]]()
