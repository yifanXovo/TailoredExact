"""Pure profile construction/actual launch expansion. Zero Optimize/vendor load."""
from round139_common import *
import copy

def prepare():
    assert not budget()['unclosed']
    parent=ROOT/'config/gi_tbc_round137.json';config=read(parent);manifest=read(OUT/'candidate_manifest.json')
    config.update(algorithm='GI-TBC with explicit inventory-product placement (Round139 research)',
        source_commit=manifest['source_commit'],default_executable=manifest['production_PE'],
        verified_PE_SHA256=manifest['production_PE_SHA'],parent_profile='config/gi_tbc_round137.json',
        parent_profile_SHA256=sha(parent),research_only=True,requires_explicit_placement=True,H_seed=20260626,
        candidate_manifest_path='results/unified_exact_round139/candidate_manifest.json',candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'))
    config['argv'] += ['--round139-stock-placement','${placement}']
    write(ROOT/'config/gi_tbc_stock_placement_round139.json',config)

def check():
    assert not budget()['unclosed']
    import paper_s2 as baseline
    profile=read(ROOT/'config/gi_tbc_stock_placement_round139.json');checked=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        for g in read(path)['groups']:
            l=g['launch'];p=l['panel'];target=TEMP/'entry-check'/l['arm_id'];assert not target.exists()
            cmd=[PYTHON,ROOT/'scripts/paper_s2_stock_placement.py','--input',ROOT/p['input_path'],
                '--out-dir',target,'--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
                '--lambda',p['lambda'],'--cap',p['cap_seconds'],'--seed',l['seed'],'--placement',l['placement'],'--json']
            r=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
            assert r.returncode==0,r.stderr
            actual=json.loads(r.stdout);config=copy.deepcopy(profile);config['argv'][-1]=l['placement']
            assert baseline.normalize(actual['command'],config)==baseline.normalize(l['command'],config)
            assert actual['dry_run'] and actual['matches_verified_PE'] and actual['matches_verified_DLL'] and not target.exists()
            checked.append(dict(arm_id=l['arm_id'],input_SHA=actual['input_SHA256'],command=actual['command'],PE_SHA=actual['executable_SHA256']))
    p=read(OUT/'pilot_matrix.json')['groups'][0]['launch']['panel'];target=TEMP/'entry-refusal'
    common=[PYTHON,ROOT/'scripts/paper_s2_stock_placement.py','--input',ROOT/p['input_path'],'--out-dir',target,
        '--T',p['T_seconds'],'--cap',p['cap_seconds'],'--seed',0,'--placement','lp-only','--json']
    refusals=[]
    for name,flag,value in [('negative_seed','--seed',-1),('small_cap','--cap',36),('unknown_placement','--placement','adaptive')]:
        cmd=list(map(str,common));cmd[cmd.index(flag)+1]=str(value)
        r=subprocess.run(cmd,cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert r.returncode!=0 and not target.exists();refusals.append(name)
    for name,args in [('no_placement',list(map(str,common[:-3]+common[-1:]))),
                      ('algorithm_override',list(map(str,common))+['--round137-am-threshold','.02'])]:
        r=subprocess.run(args,cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert r.returncode!=0 and not target.exists();refusals.append(name)
    write(OUT/'entry_check.json',dict(PASS=True,UTC=utc(),checked=checked,refusals=refusals,Optimize=0,vendor_DLL_loads=0,
        output_directories_created=0,profile_SHA=sha(ROOT/'config/gi_tbc_stock_placement_round139.json'),
        stable_entry_SHA=sha(ROOT/'scripts/paper_s2.py'),stable_profile_SHA=sha(ROOT/'config/gi_tbc_round137.json'),
        R138_entry_SHA=sha(ROOT/'scripts/paper_s2_stock_rlt.py'),R138_profile_SHA=sha(ROOT/'config/gi_tbc_stock_rlt_round138.json')))
    print(f'{len(checked)} actual placement command expansions and {len(refusals)} refusals pass')

if __name__=='__main__':globals()[sys.argv[1]]()
