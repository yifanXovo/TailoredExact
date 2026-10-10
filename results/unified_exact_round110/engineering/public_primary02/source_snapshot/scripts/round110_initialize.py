"""Bind original data and measured build before native qualification."""
from round110_common import *
import hashlib, shutil, struct

def main():
    d=OUT/'engineering/initialization01';d.mkdir(parents=True,exist_ok=False)
    shutil.copyfile('C:/Users/Administrator/.codex/attachments/ba9c6107-0f4f-45a1-b2e2-ca343fc66e47/已粘贴的文本.txt',OUT/'goal.md')
    original=Path('E:/codes/ExactEBRP-round109')
    old=read(original/'results/unified_exact_round109/candidate_identity.json')
    current=bindings();changes={k:dict(old_SHA=v,new_SHA=current.get(k)) for k,v in old['source_bindings'].items() if current.get(k)!=v}
    assert set(changes)=={'src/Parser.cpp'},changes
    old_parser=d/'old_Parser.cpp';old_parser.write_bytes((original/'src/Parser.cpp').read_bytes())
    assert sha(old_parser)==old['source_bindings']['src/Parser.cpp']
    manifest=read(original/'results/unified_exact_round109/input_manifest.json')
    data=[]
    for role in manifest['roles']:
        for suffix in ['', '_selection', '_landscape', '_parsed']:
            p=Path(role['input_path']) if not suffix else Path(role['input_path']).with_name(role['id']+suffix+'.json')
            if (original/p).is_file():
                target=ROOT/p;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((original/p).read_bytes())
                data.append(dict(path=p.as_posix(),SHA=sha(target),bytes=target.stat().st_size,original_SHA=sha(original/p)))
        assert sha(ROOT/role['input_path'])==role['input_sha256']
    write(OUT/'input_manifest.json',manifest)
    for name in ['generation_recipe.json','source_subset_overlap.json','structure_statistics.json']:
        shutil.copyfile(original/'results/unified_exact_round109'/name,OUT/name)
    protocol=read(original/'results/unified_exact_round109/protocol.json')
    protocol.update(version='round110-entry-repair-frozen-panel-confirmation-v1',maximum_starts=96,maximum_outer_seconds=110000,
        qualification_starts_reserved=13,qualification_outer_seconds_reserved=2000,qualification_maximum_starts=20,
        qualification_maximum_outer_seconds=2000,planned_formal_starts=57,start_reserve=26,
        original_protocol_SHA=sha(original/'results/unified_exact_round109/protocol.json'),restoration_confirmation=True,
        initial_prospective_freeze_round=109,historical_observed_main_roles=8)
    write(OUT/'protocol.json',protocol)
    user_paths=['results/gf_compact_bc_round/handling_convention_test/handling_convention.json',
        'results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv',
        'results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json']
    write(OUT/'baseline.json',dict(base_HEAD=BASE,local_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        PR171=json.loads(subprocess.check_output(['gh','pr','view','171','--json','url,headRefName,headRefOid,baseRefName,state,isDraft'],cwd=ROOT,text=True)),
        original_user_file_SHA={p:sha(Path('E:/codes/ExactEBRP')/p) for p in user_paths},AGENTS_found=False,
        active_native_processes_before_start=0,existing_round110_native_progress=False,data=data,production_changes=changes,
        inherited_original_PE_SHA=OLD_PE_SHA,actual_original_PE_SHA=sha(original/'build/research/round109-inherited-mb-v1/ExactEBRP.exe'),
        DLL_SHA=sha(DLL),managed_worktree_failure=dict(operation_id='da95c463-6860-406b-8baa-851f41b32ed7',
            reason='C disk no space copying unrelated historical results; tool cleaned failed checkout',solver_starts=0,
            exact_full_internal_command_and_engineering_duration='unknown'),
        sparse_worktree=str(ROOT),unrelated_user_configuration_changed=False))
    assert sha(DLL)==DLL_SHA
    previous_build=Path('C:/Users/Administrator/.codex/worktrees/round107-ens-frontier-route-events/ExactEBRP/build/research/round107-frontier-v1')
    for name in ['CMakeCache.txt','build.ninja']:
        shutil.copyfile(previous_build/name,d/('inherited_'+name))
    write(d/'receipt.json',dict(passed=True,zero_Optimize=True,conservative_solver_starts=0,production_changes=changes,
        inherited_original_sources=old['source_bindings'],data=data))
    q=OUT/'qualification';q.mkdir(exist_ok=True)
    write(q/'plan.json',dict(conservative_process_starts=13,maximum_starts=20,maximum_outer_seconds=2000,
        graph=[dict(label='parser_equivalence01',wrappers=1,children=2),dict(label='main_entry01',wrappers=1,children=3),
            dict(label='functional01',wrappers=1,children=5)],
        native_children=10,reference_export_processes=0,reference_exact_reuse=True,
        functional_fixture='reference/round100_confirmation/H100.txt',functional_V=20,functional_M=2,each_functional_cap_seconds=120,
        frozen_formal_reserve=dict(starts=57,nominal_seconds=88200,group_overhead_seconds=1800),zero_V100_solver_pilots=True))
    print('original12 exact inputs and 13-start qualification plan frozen; no native launch')

if __name__=='__main__': main()
