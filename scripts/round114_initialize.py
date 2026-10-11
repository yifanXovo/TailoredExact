"""Pure offline preparation; no solver, qualification or reference build."""
from round114_common import *
import shutil, subprocess

def initialize():
    tick=time.perf_counter();oldroot=Path('E:/codes/ExactEBRP-round113');old=oldroot/'results/unified_exact_round113'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=oldroot,text=True).strip()==BASE
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'protocol.json').exists()
    shutil.copyfile('C:/Users/Administrator/.codex/attachments/af3c0606-67de-4a2f-b7e3-7061618be7e6/已粘贴的文本.txt',OUT/'goal.md')
    peold=oldroot/'build/research/round113-inherited/ExactEBRP.exe'
    assert sha(peold)==PE_SHA and sha(DLL)==DLL_SHA
    PE.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(peold,PE)
    production=read(old/'production_identity.json');assert production['source_bindings']==bindings()
    write(OUT/'production_identity.json',dict(production,round114_inherited_PE_origin=str(peold),round113_head=BASE,
        round113_scientific_payload='8dd38b790a4584f17aa75094f9451519e07bcdbe',production_recompiled=False))
    original=read(old/'input_manifest.json');role=dict(original['roles'][1],method_order=['P-GRB','ENS-C','P-S','M-B'])
    h=dict(original['qualification_roles'][0],method_order=['P-GRB','M-B'])
    for p in [role,h]:
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        dst=OUT/'qualification/reference'/p['id'];dst.mkdir(parents=True)
        for n in ['original.lp','build.json']:shutil.copyfile(old/'qualification/reference'/p['id']/n,dst/n)
        assert sha(dst/'original.lp')==read(dst/'build.json')['canonical_sha256']
    write(OUT/'input_manifest.json',dict(roles=[role],qualification_roles=[h],new_geographies=0))
    protocol=read(old/'protocol.json')
    protocol.update(round=114,base=BASE,roles=[role],formal_arms=4,formal_nominal_seconds=14400,
        total_start_limit=16,total_outer_seconds_limit=17000,qualification_start_limit=8,qualification_outer_seconds_limit=900,
        evidence_layer=LAYER,claim_policy_SHA=sha(OUT/'claim_policy.md'),full_goal_SHA=sha(OUT/'goal.md'),
        prior_round113_state='BLOCKED',old_cold_G50_clock_not_reconstructed=True,
        repairs=['typed source claim rejection and independent endpoints with complete closeout','zero-Optimize contradictory native fields'])
    protocol.update(qualification_driver_outer_cap=180,qualification_CLI_wrapper_and_native_children=3,
        qualification_CLI_outer_cap=360,qualification_fault_holder_in_wrapper=False,
        qualification_post_driver_outer_cap=120,qualification_planned_conservative_starts=5,
        qualification_planned_outer_cap_total=660)
    write(OUT/'protocol.json',protocol)
    dst=OUT/'inherited_r113';dst.mkdir()
    for n in ['production_identity.json','candidate_identity.json','fixed_manifest.json','input_manifest.json','protocol.json',
        'final_report.md','blocking_incident.json','blocking_incident.md','qualification.md','minimal_diff.md','numerical_policy.md',
        'physical_completion.json','next_research_decision.md','public_pack_receipt.json','public_dependency_closure.json']:
        shutil.copyfile(old/n,dst/n)
    for folder in ['reports_final','review']:
        (dst/folder).mkdir()
        for p in (old/folder).glob('*'):
            if p.is_file() and p.suffix in ['.csv','.json','.md']:shutil.copyfile(p,dst/folder/p.name)
    shutil.copytree(old/'inherited_r112',dst/'inherited_r112')
    names=['launch.json','result.json','audit.json','completion.json','observations.json','phases.csv','native_end_receipt.json',
        'postexit_audit_receipt.json','whole_arm_receipt.json','audit_execution_metrics.json','progress_publication_receipt.json',
        'result.json.round112.startup.json','native.log.round112.start.json','native.log.round112.native.json']
    for p in sorted((old/'campaign/raw').iterdir()):
        target=dst/'authoritative/campaign/raw'/p.name;target.mkdir(parents=True)
        for n in names:
            if (p/n).is_file():shutil.copyfile(p/n,target/n)
    shutil.copyfile(old/'campaign/identity.json',dst/'authoritative/campaign/identity.json')
    for key in ['04_G50-C1_S0_P-GRB/compact.lp','04_G50-C1_S0_P-GRB/native.log',
        '02_G50-C1_S0_ENS-C/result.json','03_G50-C1_S0_P-S/native.log.round112.start.before.matrix.json']:
        p=old/'campaign/raw'/key;t=OUT/'management_counterexample/source/campaign/raw'/key
        t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t)
    p=old/'campaign/raw/04_G50-C1_S0_P-GRB/journal'
    shutil.copytree(p,OUT/'management_counterexample/source/campaign/raw/04_G50-C1_S0_P-GRB/journal')
    shutil.copyfile(old/'campaign/raw/04_G50-C1_S0_P-GRB/result.json',OUT/'management_counterexample/source/campaign/raw/04_G50-C1_S0_P-GRB/result.json')
    write(dst/'dependency_manifest.json',dict(files={p.relative_to(dst).as_posix():sha(p) for p in dst.rglob('*') if p.is_file()},
        old15_qualified=True,old21_pairs_preserved=True,R113_cold_P_no_whole=True,full_old_carrier_copied=False))
    (OUT/'RESUME.md').write_text('# Round114 resume\n\nVerified PR175/head '+BASE+'. E-drive sparse isolated checkout; no applicable AGENTS.md.\n'
        'Inherited PE/DLL/206 source bytes unchanged. No qualification/formal starts yet. Never overwrite raw or repeat a started destination.\n'
        'R113 BLOCKED, old cold G50 P remains unqualified without whole. New fixed G100 order P/ENS/P-S/M-B.\n',encoding='utf-8')
    write(OUT/'engineering/initialization01/receipt.json',dict(Optimize=0,native_starts=0,seconds=time.perf_counter()-tick,
        managed_full_checkout_failed_and_cleaned=True,sparse_checkout=True,remote_head_verified=BASE))
    print('Round114 initialized; production/source/input/reference identity verified; no solver starts')

if __name__=='__main__':initialize()
