"""Offline preparation: retain the exact R112 production and reference bytes."""
from round113_common import *
import shutil
from round109_prepare import COMMON

def initialize():
    OUT.mkdir(parents=True,exist_ok=True)
    original=OLD_ROOT/'results/unified_exact_round112'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=OLD_ROOT,text=True).strip()==BASE
    assert subprocess.check_output(['git','rev-parse','origin/codex/round112-paid-start-backend-attribution'],text=True).strip()==BASE
    assert not (OUT/'protocol.json').exists()
    shutil.copyfile(Path('C:/Users/Administrator/.codex/attachments/a03f43c4-2fff-4315-90ac-8da5a6f15a83/已粘贴的文本.txt'),OUT/'goal.md')
    pe_old=OLD_ROOT/'build/research/round112-paid-v1/ExactEBRP.exe'
    assert sha(pe_old)==PE_SHA and sha(DLL)==DLL_SHA
    PE.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(pe_old,PE)
    production=read(original/'production_identity.json')
    assert production['source_bindings']==bindings() and len(bindings())==206
    assert production['measured_source_commit']==SOURCE
    write(OUT/'production_identity.json',dict(production,round113_inherited_PE_origin=str(pe_old),
        round112_head=BASE,round112_scientific_payload='a3cac1df0ee1d4eaaeb87343508e0af31cfc3b40',
        production_recompiled=False,production_algorithm_or_parameters_changed=False))
    old=read(original/'input_manifest.json')
    roles=old['roles'][3:];h=old['qualification_roles'][0]
    assert [r['id'] for r in roles]==['G50-C1','G100-R2']
    for p in roles+[h]:
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        dst=OUT/'qualification/reference'/p['id'];dst.mkdir(parents=True,exist_ok=False)
        for name in ['build.json','original.lp']:shutil.copyfile(original/'qualification/reference'/p['id']/name,dst/name)
        assert read(dst/'build.json')['canonical_sha256']==sha(dst/'original.lp')
    write(OUT/'input_manifest.json',dict(roles=roles,qualification_roles=[h],new_geographies=0,old_roles_repeated=False))
    write(OUT/'protocol.json',dict(round=113,base=BASE,roles=roles,common=COMMON,
        formal_arms=8,formal_nominal_seconds=21600,total_start_limit=28,total_outer_seconds_limit=26000,
        qualification_start_limit=12,qualification_outer_seconds_limit=1200,group_outer_administrative_reserve=120,
        primary_benchmark='cold P-GRB',default='ENS-C',evidence_layer=LAYER,
        pairs=read(original/'protocol.json')['pairs'],comparison_policy=read(original/'protocol.json')['comparison_policy'],
        startup_semantic_fields=read(original/'protocol.json')['startup_semantic_fields'],
        startup_metadata_exclusions=read(original/'protocol.json')['startup_metadata_exclusions'],
        cover_tolerance=1e-7,zero_tolerance=1e-7,no_formal_retry=True,full_goal_SHA=sha(OUT/'goal.md'),
        prior_round112_state='BLOCKED',prior_partial13_not_endpoint=True,
        repairs=['optional progress publication isolation','normal no-Optimize lifecycle audit support'],
        qualification_driver_declared_processes=1,qualification_driver_no_OS_children=True,
        qualification_CLI_wrapper_and_native_children=5,qualification_fault_holder_in_wrapper=True,
        qualification_driver_outer_cap=120,qualification_CLI_outer_cap=600))
    history=OUT/'inherited_r112';history.mkdir()
    for filename in ['production_identity.json','candidate_identity.json','fixed_manifest.json','input_manifest.json','protocol.json',
            'final_report.md','blocking_incident.json','blocking_incident.md','qualification.md','mathematical_algorithm.md',
            'numerical_policy.md','contribution_evidence_map.md','next_research_decision.md','RESUME.md']:
        shutil.copyfile(original/filename,history/filename)
    for folder in ['reports_final','review']:(history/folder).mkdir()
    for filename in ['arms.csv','pairs.csv','backend_conclusions.json','summary.json','same_H.csv','same_H_fleets.csv',
        'fleets.csv','startup_fleets.csv','compact_Starts.csv','time_partitions.csv','target_discovery.csv','checkpoints.csv','split_exposure.csv']:
        shutil.copyfile(original/'reports_final'/filename,history/'reports_final'/filename)
    for filename in ['performance_admission.json','history_review.json','final_reader_delta01.json','restored_root01.json','whole_goal01.json']:
        shutil.copyfile(original/'review'/filename,history/'review'/filename)
    for folder in ['postformal03']:
        for path in (original/'review'/folder).glob('*.json'):
            target=history/'review'/folder/path.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(path,target)
    write(history/'dependency_manifest.json',dict(old_root_read_for_copy=str(OLD_ROOT),files={p.relative_to(history).as_posix():sha(p) for p in history.rglob('*') if p.is_file()},
        review_mode='inherit signed R112 authority plus targeted lifecycle/endpoint replay; no whole LP-matrix reaudit',
        performance_clock_policy='original receipts only; new replay time is offline engineering',
        round112_qualified_arms=12,round112_pair_positions=30,round112_evaluable_pairs=18,round112_missing_pairs=12))
    (OUT/'RESUME.md').write_text('# Round113 resume\n\nIsolated sparse E-drive worktree from verified PR174 head '+BASE+'.\n'
        'No AGENTS.md was found in applicable ancestors or source/helper/input directories.\n'
        'Exact inherited production PE copied after SHA verification; no compilation.\n'
        'No qualification/formal starts yet. Two narrow helper changes and finite validation precede independent admission.\n'
        'Never overwrite raw or repeat any started formal destination. Current fee ledger is authoritative.\n',encoding='utf-8')
    print('Round113 prepared offline; inherited PE/source/reference identity verified; 0 qualification or formal starts')

if __name__=='__main__':initialize()
