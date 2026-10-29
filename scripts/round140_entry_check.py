"""Actual dry-run vectors for every entered count configuration; no Optimize."""
from round140_common import *
import copy

def main():
    assert not budget()['unclosed']
    import paper_s2 as baseline
    profile=read(ROOT/'config/gi_tbc_tc2_round140.json');checked=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        for g in read(path)['groups']:
            l=g['launch'];p=l['panel'];target=TEMP/'entry-check'/l['arm_id'];assert not target.exists()
            cmd=[PYTHON,ROOT/'scripts/paper_s2_tc2.py','--input',ROOT/p['input_path'],'--out-dir',target,
                '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
                '--lambda',p['lambda'],'--cap',p['cap_seconds'],'--seed',l['seed'],'--counts',l['counts'],'--json']
            r=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
            assert r.returncode==0,r.stderr
            actual=json.loads(r.stdout);config=copy.deepcopy(profile);config['argv'][-1]=l['counts']
            assert baseline.normalize(actual['command'],config)==baseline.normalize(l['command'],config)
            assert actual['dry_run'] and actual['matches_verified_PE'] and actual['matches_verified_DLL'] and not target.exists()
            checked.append(dict(arm_id=l['arm_id'],input_SHA=actual['input_SHA256'],command=actual['command'],PE_SHA=actual['executable_SHA256']))
    default_mode=profile.get('default_counts','tc2')
    default_launch=next(g['launch'] for path in sorted(OUT.glob('*_matrix.json')) if path.name!='qualification_matrix.json'
        for g in read(path)['groups'] if g['launch']['counts']==default_mode and g['launch']['seed']==0)
    p=default_launch['panel'];default_target=TEMP/'entry-check/default-research-mode';assert not default_target.exists()
    command=[PYTHON,ROOT/'scripts/paper_s2_tc2.py','--input',ROOT/p['input_path'],'--out-dir',default_target,
        '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
        '--lambda',p['lambda'],'--cap',p['cap_seconds'],'--seed',0,'--json']
    result=subprocess.run(list(map(str,command)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    default_actual=json.loads(result.stdout)
    assert default_actual['counts']==default_mode and default_actual['dry_run'] and not default_target.exists()
    default_config=copy.deepcopy(profile);default_config['argv'][-1]=default_mode
    assert baseline.normalize(default_actual['command'],default_config)==baseline.normalize(default_launch['command'],default_config)
    p=read(OUT/'primary_matrix.json')['groups'][0]['launch']['panel'];target=TEMP/'entry-refusal'
    common=[PYTHON,ROOT/'scripts/paper_s2_tc2.py','--input',ROOT/p['input_path'],'--out-dir',target,
        '--T',p['T_seconds'],'--cap',p['cap_seconds'],'--seed',0,'--counts','tc2','--json']
    refused=[]
    for name,flag,value in [('negative_seed','--seed',-1),('small_cap','--cap',36),('unknown_counts','--counts','adaptive')]:
        cmd=list(map(str,common));cmd[cmd.index(flag)+1]=str(value)
        r=subprocess.run(cmd,cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert r.returncode!=0 and not target.exists();refused.append(name)
    stable=['scripts/paper_s2.py','config/gi_tbc_round137.json','scripts/paper_s2_stock_rlt.py',
        'config/gi_tbc_stock_rlt_round138.json','scripts/paper_s2_stock_placement.py','config/gi_tbc_stock_placement_round139.json']
    unchanged={}
    for name in stable:
        raw=git('show',BASE+':'+name);local=(ROOT/name).read_bytes()
        assert raw==local or raw.replace(b'\n',b'\r\n')==local,(name,'stable bytes changed')
        unchanged[name]=dict(actual_SHA=sha(ROOT/name),pinned_Git_SHA=hashlib.sha256(raw).hexdigest(),only_existing_line_ending_transport=True)
    write(OUT/'entry_check.json',dict(PASS=True,UTC=utc(),checked=checked,refusals=refused,Optimize=0,vendor_DLL_loads=0,
        output_directories_created=0,profile_SHA=sha(ROOT/'config/gi_tbc_tc2_round140.json'),stable_entries=unchanged,
        default_research_counts=default_mode,default_command=default_actual['command'],default_matches_frozen_arm=default_launch['arm_id']))
    print(f'{len(checked)} actual count-command vectors and {len(refused)} refusals pass; stable entries unchanged')

if __name__=='__main__':main()
