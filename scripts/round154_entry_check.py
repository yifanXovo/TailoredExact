"""Dry launch checks only: match every preregistered complete arm."""
from round154_common import *

def run(label='entry_v1'):
    configure();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    matrix=read(OUT/'confirmation_matrix.json');profile=read(ROOT/'config/gi_tbc_proof_floor_round154.json');facts=[]
    output={'--out','--log','--process-phase-ledger','--external-gini-artifact-dir','--primal-heuristic-generation-log','--progress-log','--native-evidence-dir'}
    numeric={'--lambda','--T','--pickup-time','--drop-time','--time-limit','--process-wall-time-limit','--gurobi-seed'}
    helper={'--round153-python','--round153-helper','--round153-helper-sha','--round153-manifest','--round153-manifest-sha'}
    for group in matrix['groups']:
        launch=group['launch'];panel=launch['panel'];method=launch['R154_method'];destination=WORK/'temp/round154'/f'entry_{label}_{group["position"]:03}'
        assert not destination.exists()
        command=[PYTHON,'-B',ROOT/'scripts/paper_s2_proof_floor.py','--input',ROOT/panel['input_path'],
            '--out-dir',destination,'--T',panel['T_seconds'],'--lambda',panel['lambda'],
            '--pickup-time',panel['pickup_seconds'],'--drop-time',panel['drop_seconds'],
            '--cap',launch['cap_seconds'],'--seed',launch['seed'],'--floor',{'B':'off','E':'on','J':'native'}[method],'--json']
        p=subprocess.run(list(map(str,command)),cwd=ROOT,text=True,capture_output=True);assert p.returncode==0,p.stderr
        plan=json.loads(p.stdout);assert plan['dry_run'] and not destination.exists()
        assert plan['matches_verified_PE'] and plan['matches_verified_DLL'] and plan['complete_own_H']
        expected=launch['command'];actual=plan['command'];assert Path(expected[0]).resolve()==Path(actual[0]).resolve()
        ed=dict(zip(expected[1::2],expected[2::2]));ad=dict(zip(actual[1::2],actual[2::2]))
        assert len(ed)*2+1==len(expected) and len(ad)*2+1==len(actual)
        assert set(ed)<=set(ad) and (not(set(ad)-set(ed)) or method=='B' and set(ad)-set(ed)<=helper)
        for flag,value in ed.items():
            if flag in output:continue
            if flag=='--input':assert Path(value).resolve()==Path(ad[flag]).resolve()
            elif flag in numeric:assert float(value)==float(ad[flag])
            else:assert value==ad[flag],(flag,value,ad[flag])
        write(target/f'launch_{group["position"]:03}.json',plan)
        facts.append(dict(position=group['position'],role=launch['id'],method=method,matched_frozen_semantic_argv=True))
    assert sha(ROOT/'config/gi_tbc_round137.json')==profile['parent_profile_SHA256']
    write(target/'result.json',dict(PASS=True,facts=facts,Optimize=0,producer=0,stable_entry_profile_unmodified=True,
                                  core_switch_default_OFF=True,named_E_entry_defaults_ON=True))
    print(json.dumps(dict(PASS=True,launches=len(facts))),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
