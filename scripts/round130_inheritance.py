"""Retain narrowly scoped existing Start and inclusive-root qualification."""
from round130_common import *

def run():
    old=Path('E:/codes/ExactEBRP-round112/results/unified_exact_round112/qualification/start_fault01')
    q=read(old/'necessary_audit.json')
    unchanged=['src/Round112CompactStart.inc']
    for n in unchanged:assert sha(ROOT/n)==q['source_bindings'][n]
    rows=[json.loads(s) for s in (old/'cases.jsonl').read_text().splitlines()]
    assert len(rows)==13 and all(x['passed'] and x['native_Optimize_calls']==0 for x in rows)
    out=OUT/'qualification/inherited';out.mkdir(exist_ok=True)
    shutil.copyfile(old/'cases.jsonl',out/'R112_Start_cases.jsonl')
    delta=git('diff','9165e69bf41d1eb323fd52b8cb4a8230dcb4edd4..'+BASE,'--','src/MipStartMapping.cpp')
    (out/'R112_to_E2_mapper.diff').write_bytes(delta)
    boundaries=[]
    prior=WORK/'worktrees/round128/results/unified_exact_round128/qualification'
    for name in ['native_zero_S_duration60','native_zero_S_duration3600','native_tiny_positive_U','native_R98-C2_MD_R_open_final']:
        d=prior/name;i=read(d/'identity.json');a=read(d/'reconstructed.json')['arms'][0]
        l=i['launches'][0];raw=Path(l['destination']);r=read(raw/'result.json')
        boundaries.append(dict(name=name,method='MD-R (full three-station predecessor)',actual_new_native_run=False,
            PE_SHA=i['candidate_binary_sha256'],input_SHA=l['panel']['input_sha256'],
            own_result_SHA=sha(raw/'result.json'),reconstructed_SHA=sha(d/'reconstructed.json'),
            native_Optimize=a['native_Optimize'],status=a['status'],certificate=a['certificate'],U=a['U'],L=a['L'],
            signed_gap=a['U']-a['L'],actual_root_LP=r['external_gini_tree_lp_optimize_count'],
            actual_root_MIP=r['external_gini_tree_terminal_mip_optimize_count']))
    write(OUT/'qualification/inherited_contracts.json',dict(UTC=utc(),Optimize=0,
        R112_cases=rows,R112_cases_source_SHA=sha(old/'cases.jsonl'),unchanged_actual_mapper_sources={n:sha(ROOT/n) for n in unchanged},
        general_mapper_evolution='Since R112 only the optional R120Pair argument and r120_h-column branch were added; PS has neither R120 pair nor r120_h. See exact retained diff. No R130 mapper edit.',
        general_mapper_old_SHA=q['source_bindings']['src/MipStartMapping.cpp'],general_mapper_current_SHA=sha(ROOT/'src/MipStartMapping.cpp'),
        valid_physical_cases=['actual_heterogeneous_H','empty_vehicle_0','loaded_return'],
        injected_fault_cases_are_not_real_Gurobi_failures=True,R128_boundary_returns=boundaries,
        inheritance_scope='Unchanged mapper and R128 return/deadline logic; new pair-only root gets fresh full matrix, sentinel, own Start and real two-call checks',
        not_a_repeat_of_historical_campaign=True))
    print('FINITE_EXISTING_START_AND_BOUNDARY_CONTRACTS_RETAINED')
if __name__=='__main__':run()
