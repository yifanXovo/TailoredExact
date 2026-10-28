"""Actual command expansion for the new candidate; no executable/DLL loading."""
from round138_common import *
import argparse,importlib.util

def main():
    assert not budget()['unclosed']
    import paper_s2 as baseline
    profile=read(ROOT/'config/gi_tbc_stock_rlt_round138.json');checked=[]
    matrix=read(OUT/'matrix_frozen.json')
    for g in matrix['groups']:
        l=g['launch']
        if l['method']!='STOCK':continue
        p=l['panel'];target=WORK/'temp/round138/entry-check'/g['arm_id']
        assert not target.exists()
        args=[PYTHON,ROOT/'scripts/paper_s2_stock_rlt.py','--input',ROOT/p['input_path'],
            '--out-dir',target,'--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],
            '--drop-time',p['drop_seconds'],'--lambda',p['lambda'],'--cap',p['cap_seconds'],
            '--seed',l['seed'],'--json']
        completed=subprocess.run(list(map(str,args)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert completed.returncode==0,completed.stderr
        actual=json.loads(completed.stdout)
        assert actual['dry_run'] and actual['stock_rlt'] and actual['source_commit']==read(OUT/'candidate_repair_manifest.json')['source_commit']
        assert actual['executable_SHA256']==sha(profile['default_executable']) and actual['matches_verified_PE'] and actual['matches_verified_DLL']
        assert baseline.normalize(actual['command'],profile)==baseline.normalize(l['command'],profile)
        assert actual['input_SHA256']==p['input_sha256'] and not target.exists()
        checked.append(dict(arm_id=l['arm_id'],command=actual['command'],input_SHA=p['input_sha256'],
            source_commit=actual['source_commit'],executable_SHA=actual['executable_SHA256']))
    assert len(checked)==9
    p=matrix['groups'][1]['launch']['panel'];temp=WORK/'temp/round138/entry-refusal'
    common=[PYTHON,ROOT/'scripts/paper_s2_stock_rlt.py','--input',ROOT/p['input_path'],'--out-dir',temp,
        '--T',p['T_seconds'],'--cap',p['cap_seconds'],'--seed',0,'--json']
    refusals=[]
    for name,flag,value in [('negative_seed','--seed',-1),('small_cap','--cap',36)]:
        cmd=list(map(str,common));cmd[cmd.index(flag)+1]=str(value)
        r=subprocess.run(cmd,cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert r.returncode!=0 and not temp.exists();refusals.append(name)
    write(OUT/'entry_check.json',dict(PASS=True,UTC=utc(),checked=checked,refusals=refusals,
        Optimize=0,vendor_DLL_loads=0,output_directories_created=0,
        main_paper_s2_SHA=sha(ROOT/'scripts/paper_s2.py'),baseline_config_SHA=sha(ROOT/'config/gi_tbc_round137.json'),
        candidate_profile_SHA=sha(ROOT/'config/gi_tbc_stock_rlt_round138.json'),
        candidate_entry_SHA=sha(ROOT/'scripts/paper_s2_stock_rlt.py'),
        measured_primary_PE_not_retagged=True,entry_version='V2 coefficient-transport repair',
        primary_model_bridge_SHA=sha(OUT/'repair/primary_native_bridge.json')))
    print('Candidate entry: nine actual STOCK vectors and two refusals pass, zero Optimize/DLL/output creation')

if __name__=='__main__':main()
