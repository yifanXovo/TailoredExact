"""Freeze the separate research profile and audit its actual dry-run argv."""
import copy
from round143_common import *

def main():
    manifest=read(OUT/'candidate_manifest.json');parent=ROOT/'config/gi_tbc_round137.json'
    config=copy.deepcopy(read(parent));config.update(schema='round143-RN-frozen-argv-v1',round=143,
        algorithm='GI-TBC + reciprocal-normalized Gini research lift',source_commit=manifest['source_commit'],
        research_head=manifest['source_commit'],default_executable=manifest['production_PE'],verified_PE_SHA256=manifest['production_PE_SHA'],
        parent_profile_SHA256=sha(parent),research_profile=True,RN=True,source_manifest='results/unified_exact_round143/candidate_manifest.json')
    config['argv']+=['--round143-rn','on']
    target=ROOT/'config/gi_tbc_rn_round143.json';write(target,config)
    checked=[]
    p=read(OUT/'inherited/roots/K-35-U/scope.json')['panel']
    for mode in ['off','on']:
        destination=TEMP/'entry-check'/mode
        command=[PYTHON,'-B',ROOT/'scripts/paper_s2_rn.py','--input',ROOT/p['input_path'],'--out-dir',destination,
            '--T',p['T_seconds'],'--lambda',p['lambda'],'--cap',p['cap_seconds'],'--seed',0,'--rn',mode,'--json']
        r=subprocess.run(list(map(str,command)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert r.returncode==0,r.stderr
        v=json.loads(r.stdout);assert v['dry_run'] and v['matches_verified_PE'] and v['matches_verified_DLL']
        assert v['command'][-2:]==['--round143-rn',mode] and not destination.exists()
        assert '--round138-stock-rlt' not in v['command'] and '--round140-counts' not in v['command']
        checked.append(v)
    write(OUT/'entry_check.json',dict(PASS=True,Optimize=0,Native_load=0,checked=checked,
        stable_profile_SHA=sha(parent),stable_entry_SHA=sha(ROOT/'scripts/paper_s2.py'),new_profile_SHA=sha(target)))
    print('RN on/off actual entry expansion PASS; stable profile retained')

if __name__=='__main__':main()
