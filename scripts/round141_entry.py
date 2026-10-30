"""Bind the separate research entry and check frozen/default-off semantics."""
from round141_common import *

def profile():
    manifest=read(OUT/'candidate_manifest.json');config=read(ROOT/'config/gi_tbc_round137.json')
    config.update(algorithm='GI-TBC + BOTH stock/TC/TC2 + root threshold-count conditional objective bounds (research only)',
        source_commit=manifest['source_commit'],research_head=manifest['source_commit'],
        default_executable=manifest['production_PE'],verified_PE_SHA256=manifest['production_PE_SHA'],round=141,
        parent_profile='config/gi_tbc_round137.json',parent_profile_SHA256=sha(ROOT/'config/gi_tbc_round137.json'),
        research_only=True,counts='tc2',stock=True,placement='both',proof_mode='d1',root_once=True,
        source_manifest='results/unified_exact_round141/candidate_manifest.json',
        authority=dict(schema='round141-research-entry-v1',candidate_manifest='results/unified_exact_round141/candidate_manifest.json',candidate_manifest_SHA=sha(OUT/'candidate_manifest.json')))
    config['argv']+=['--round138-stock-rlt','--round140-counts','tc2','--round141-count-proof','d1']
    write(ROOT/'config/gi_tbc_count_disjunction_round141.json',config)

def check():
    paths=['scripts/paper_s2.py','config/gi_tbc_round137.json','scripts/paper_s2_stock_rlt.py',
           'config/gi_tbc_stock_rlt_round138.json','scripts/paper_s2_stock_placement.py',
           'config/gi_tbc_stock_placement_round139.json','scripts/paper_s2_tc2.py','config/gi_tbc_tc2_round140.json']
    facts=[]
    for path in paths:
        inherited=git('show',BASE+':'+path);actual=(ROOT/path).read_bytes()
        assert inherited==actual,path
        facts.append(dict(path=path,SHA=sha(ROOT/path),byte_identical_to=BASE))
    plans=[]
    for mode in ['d1','d0']:
        args=[PYTHON,'-B',ROOT/'scripts/paper_s2_count_disjunction.py','--input',ROOT/'results/unified_exact_round132/inputs/K-20-S.txt',
            '--out-dir',TEMP/f'entry_check_{mode}','--T','5400','--lambda','.15','--cap','1200','--seed','0','--mode',mode,'--json']
        run=subprocess.run(list(map(str,args)),capture_output=True,env=environment(),timeout=30);assert run.returncode==0,run.stderr
        plan=json.loads(run.stdout);cmd=plan['command']
        for flag,value in [('--round140-counts','tc2'),('--round141-count-proof',mode),('--gurobi-seed','0')]:assert cmd[cmd.index(flag)+1]==value
        assert '--round138-stock-rlt' in cmd and plan['matches_verified_PE'] and not Path(plan['output_directory']).exists()
        plans.append(plan)
    write(OUT/'entry_check.json',dict(PASS=True,stable_and_historical=facts,research_plans=plans,Optimize=0))

if __name__=='__main__':globals()[sys.argv[1]]()
