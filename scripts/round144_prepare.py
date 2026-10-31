"""Freeze the sole candidate/profile and admit only its short health qualifier."""
import copy
from round144_campaign import qualification
from round144_common import *
configure()
def main():
    m=read(OUT/'candidate_manifest.json');parent=ROOT/'config/gi_tbc_round137.json';c=copy.deepcopy(read(parent))
    c.update(schema='round144-RN-projection-frozen-argv-v1',round=144,algorithm='GI-TBC + one once-root original-variable RN projection',source_commit=m['source_commit'],research_head=m['source_commit'],
        default_executable=m['production_PE'],verified_PE_SHA256=m['production_PE_SHA'],parent_profile_SHA256=sha(parent),research_profile=True,RN_P=True,source_manifest='results/unified_exact_round144/candidate_manifest.json')
    c['argv']+=['--round144-projection','on'];write(ROOT/'config/gi_tbc_rnp_round144.json',c)
    checked=[];p=read(ROOT/'results/unified_exact_round143/inherited/roots/K-35-U/scope.json')['panel']
    for mode in ['off','on']:
        destination=TEMP/'entry-check'/mode;args=[PYTHON,'-B',ROOT/'scripts/paper_s2_rnp.py','--input',ROOT/p['input_path'],'--out-dir',destination,'--T',p['T_seconds'],'--lambda',p['lambda'],'--cap',p['cap_seconds'],'--seed',0,'--projection',mode,'--json']
        r=subprocess.run(list(map(str,args)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30);assert r.returncode==0,r.stderr
        v=json.loads(r.stdout);assert v['dry_run'] and v['matches_verified_PE'] and v['matches_verified_DLL'] and not destination.exists()
        assert v['command'][-2:]==['--round144-projection',mode];checked.append(v)
    write(OUT/'entry_check.json',dict(PASS=True,checked=checked,Optimize=0,Native_load=0,stable_entry_SHA=sha(ROOT/'scripts/paper_s2.py'),stable_profile_SHA=sha(parent)))
    for p in ['qualification_native_transport.json','qualification_native_writer.json','math/fixtures.json']:assert read(OUT/p)['PASS']
    write(OUT/'candidate_freeze.json',dict(UTC=utc(),candidate='RN-P single full-RN-block dual box projection',manifest_SHA=sha(OUT/'candidate_manifest.json'),
        exact_compiled_native_checks=True,source_once=True,persistent_RN_columns=0,Seed=0,H_seed=20260626,Threads=1,AM_threshold=.08,
        source_commit=m['source_commit'],PE_SHA=m['production_PE_SHA'],no_placement_callback_aggregation_or_seed_grid=True))
    qualification();path=OUT/'qualification_matrix.json'
    write(OUT/'review/qualification_admission.json',dict(decision='ACCEPT',matrix_SHA=sha(path),independent_nonimplementer_review=False,
        scope='Short health qualifier only, following independent conditional pre-review, reset fix and passed compiled Fraction/Native/writer/Start fixtures',expensive_full_test_admission=False))
    print('One candidate frozen; short complete health qualification admitted, expensive full admission pending independent readback')
if __name__=='__main__':main()
