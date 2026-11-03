"""Round150 independent confirmation admission; no inherited launch functions."""
from pathlib import Path
import ast, datetime, hashlib, json, subprocess, time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round150'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
    tick=time.perf_counter();p=OUT/'confirmation_matrix.json';matrix=read(p)
    assert sha(p)=='d7d86fef25eff960deb945a8237f0b85407415d2ad4cb6b7619c263e53c4b638'
    old=read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
    old={g['launch']['id']:g['launch'] for g in old['groups'] if g['launch']['method']=='S2' and g['launch']['seed']==0}
    candidate=read(OUT/'candidate_manifest.json');start=read(OUT/'start_receipt.json')
    assert sha(candidate['production_PE'])==candidate['production_PE_SHA']=='373efa9a596aaf02fb332685515fcfe88df1b169cbe53b295ab6027140620295'
    assert sha(candidate['DLL'])==candidate['DLL_SHA']=='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
    assert candidate['source_commit']=='380a85f866bffb914036190f8ee2700ce8b55978'
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert matrix['new_nominal_caps']==7200 and matrix['H_seed']==20260626 and matrix['Seed']==0
    assert matrix['serial'] and matrix['threads']==1 and matrix['all_own_H'] and matrix['affinity_mask']==4
    for f,h in candidate['source_hashes'].items():assert sha(ROOT/f)==h,f
    for f,h in matrix['helpers'].items():assert sha(ROOT/f)==h,f
    for f,h in start['protected_entry_bytes'].items():assert sha(ROOT/f)==h,f
    assert len(matrix['groups'])==4
    facts=[]
    expected=[('N-C20-U','B'),('N-C20-U','D'),('N-B35-S','B'),('N-B35-S','D')]
    for g,(role,method) in zip(matrix['groups'],expected):
        launch=g['launch'];original=old[role];command=launch['command'];panel=launch['panel']
        assert launch['id']==role and launch['R150_method']==method and launch['seed']==0
        assert launch['cap_seconds']==original['cap_seconds'] and launch['hard_stop_seconds']==original['hard_stop_seconds']
        tail=['--round146-gd','on' if method=='D' else 'off','--round149-penalty-feedback','off']
        assert command[-4:]==tail
        normalized=command[:-4];normalized[0]=original['command'][0]
        normalized=[v.replace(launch['destination'],original['destination']) for v in normalized]
        assert normalized==original['command'],'Unexpected token differs from full R137 argv'
        assert not any(flag in command for flag in ['--round135-aggregate-penalty','--round138-stock-rlt','--round148-shared-s'])
        for key in ['V','M','Q_vector','source','T_seconds','Omega','rho','lambda','total_initial','total_target','total_capacity','input_sha256']:
            assert panel[key]==original['panel'][key],key
        assert panel['known'] and panel['exposed'] and not panel['used_in_GD_selection']
        assert panel['lambda']==.15 and panel['pickup_seconds']==panel['drop_seconds']==60
        input_path=ROOT/panel['input_path'];assert sha(input_path)==panel['input_sha256']
        lines=input_path.read_text(encoding='utf-8').splitlines();values={}
        for line in lines[1:]:
            if '=' in line:
                name,value=line.split('=',1);values[name.strip()]=ast.literal_eval(value.strip())
        assert sum(values['initial'][1:])==panel['total_initial']
        assert sum(values['target'][1:])==panel['total_target']
        assert sum(values['capacities'][1:])==panel['total_capacity']
        assert abs(sum(values['weights'][1:])-panel['Omega'])<1e-12
        assert abs(panel['rho']-.15*panel['Omega'])<1e-12
        identity_path=OUT/g['group']/'identity.json';identity=read(identity_path)
        assert sha(identity_path)==g['identity_SHA']
        assert identity['launches']==[launch] and identity['no_cross_arm_information']
        assert identity['measured_source_commit']==candidate['source_commit']
        assert identity['candidate_binary_sha256']==candidate['production_PE_SHA']
        facts.append(dict(role=role,method=method,original_argv_exact_after_declared_path_PE_and_GD_PF_tail=True,
            cap=launch['cap_seconds'],lambda_value=panel['lambda'],physical_T=panel['T_seconds'],
            input_SHA=panel['input_sha256'],known=True,exposed=True,used_in_GD_selection=False))
    value=dict(decision='ACCEPT',matrix_SHA=sha(p),independent_nonimplementer_review=True,
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Native_load=0,Optimize=0,
        independent_script_SHA=sha(__file__),actual_check_seconds=time.perf_counter()-tick,
        facts=facts,production_source=candidate['source_commit'],PE_SHA=candidate['production_PE_SHA'],DLL_SHA=candidate['DLL_SHA'],
        code_review=['Narrow wrapper preserves own-H producer/seal/closeout/R134 chain',
        'Early closeout guard precedes PF and GD derivative checks',
        'Root context uses actual first Native call SHA and permits zero rows or no model',
        'No production C++ or stable entry/config edits',
        'Four arms fixed before results; experimental caps are not algorithm rules'],
        remaining_checks='After each arm inspect all actual Native calls, GD rows/readback, PF OFF, seals and verification; no fixed call-count assumption')
    (OUT/'review/confirmation_admission.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(value))
if __name__=='__main__':run()
