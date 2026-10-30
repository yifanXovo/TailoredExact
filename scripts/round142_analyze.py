"""Compact evidence and complete-method tables; pure reads, no Native load."""
from round142_common import *
import round141_analyze as legacy
from round142_math import F
import csv,types
configure()

def require_idle():
    assert not budget()['unclosed'],'analysis/export waits for timed producers'

def csv_write(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=keys);w.writeheader();w.writerows(rows)

def LP():
    require_idle();positions=[];groups=[]
    specs=read(OUT/'LP_plan.json')['positions']
    for spec in specs:
        for mode in ['selected','all']:
            p=OUT/'LP'/(spec['label']+'_'+mode)/'result.json';r=read(p)
            assert r['qualified'] and r['Seed']==0 and r['Threads']==1 and r['LP_Optimize']==1
            assert sha(p.parent/'model.mps')==r['canonical_SHA'] and sha(p.parent/'solution.json.gz')==r['solution_SHA']
            assert r['range_control']['same_objective_witness']
            positions.append(dict(role=spec['role'],side=spec['side'],mode=mode,old_L=spec['old_L'],L=r['L'],
                old_floor=spec['old_beta'],floor=r['beta'],gain=r['difference'],
                source_SHA=spec['source_SHA'],canonical_SHA=r['canonical_SHA'],solution_SHA=r['solution_SHA'],
                rows_before=r['before']['rows'],rows_after=r['after']['rows'],
                nonzeros_before=r['before']['nonzeros'],nonzeros_after=r['after']['nonzeros'],
                range_rows=r['added_range_rows'],CP_rows=r['added_CP_rows'],
                construction_seconds=r['construction_seconds'],solve_seconds=r['optimize_wall_seconds'],
                Runtime=r['Runtime'],Work=r['Work'],range_control_Optimize=0,
                range_control_residual=r['range_control']['new_range_max_violation'],
                **r['diagnostic'],result_path=p.relative_to(ROOT).as_posix(),result_SHA=sha(p)))
    for role in dict.fromkeys(p['role'] for p in specs):
        by={(p['mode'],p['side']):p for p in positions if p['role']==role}
        r=dict(role=role,old_cover=min(by['selected',s]['old_L'] for s in ['low','high']))
        for mode in ['selected','all']:
            r[mode+'_cover']=min(by[mode,s]['L'] for s in ['low','high'])
            r[mode+'_floor']=min(by[mode,s]['floor'] for s in ['low','high'])
            r[mode+'_gain']=r[mode+'_cover']-r['old_cover']
        r['ALL_minus_selected']=r['all_cover']-r['selected_cover'];groups.append(r)
    write(OUT/'reports/LP.json',dict(positions=positions,covers=groups,LP_Optimize=12,MIP_Optimize=0,
        C_Optimize=0,C_same_objective_witnesses=12,all_continuous=True,
        actual_source_objective_cutoff_support_g_retained=True,
        tolerance_policy='Unchanged FeasibilityTol/OptimalityTol=1e-6; qualified floors min(L,cutoff)-1e-7 outward',
        new_floor_native_not_injected_from_this_diagnostic=True))
    csv_write(OUT/'reports/LP.csv',positions);csv_write(OUT/'reports/cover.csv',groups)
    write(OUT/'candidate_freeze.json',dict(UTC=utc(),uniform_candidate='selected',D1=True,
        source_only=True,extra_columns=0,extra_probes=0,main_configuration_per_instance=False,
        rationale='All three weak-source/min-cover gains exceed rounding scale, but are small. ALL adds no optimized information; finite four-role pilot checks full value.',
        S_LP_report_SHA=sha(OUT/'LP_selected_summary.json'),ALL_LP_report_SHA=sha(OUT/'LP_all_summary.json'),
        stable_default_retained='R137 GI-TBC',expansion_and_Seed1_conditional=True))
    print(json.dumps(groups,indent=2))

def full():
    require_idle()
    # Reuse the accepted collector, including the complete clocks, actual
    # returned Native attributes, probe costs and all qualification/failures.
    ns=dict(vars(legacy),ROOT=ROOT,OUT=OUT,require_idle=require_idle,budget=budget,csv_write=csv_write)
    collector=types.FunctionType(legacy.full.__code__,ns,'full',legacy.full.__defaults__,legacy.full.__closure__)
    collector()
    data=read(OUT/'reports/full.json');old=read(ROOT/'results/unified_exact_round141/reports/full.json')
    assert json.loads(git('show',SCIENCE141+':results/unified_exact_round141/reports/full.json'))==old
    old_d1=[dict(r,reference_science_commit=SCIENCE141,reused_new_Optimize=0,
                 source_identity_policy='Original R141 source/PE/full costs; cross-version reference')
            for r in old['new_arms'] if r['method']=='D1']
    data['reused_arms']+=old_d1;matched=[]
    for candidate in data['new_arms']:
        candidate['products']='selected' if candidate['method']=='CP' else 'off'
        for reference in old_d1:
            if (candidate['role'],candidate['seed'])!=(reference['role'],reference['seed']):continue
            for key in ['input_SHA','physical_T','lambda_value','cap','H_semantic_SHA','H_fleet_SHA']:assert candidate[key]==reference[key],(candidate['role'],key)
            matched.append(dict(role=candidate['role'],seed=candidate['seed'],candidate=candidate['method'],
                reference='R141_D1',same_PE=False,delta_U=candidate['U']-reference['U'],delta_L=candidate['L']-reference['L'],
                delta_T_produce=candidate['T_produce']-reference['T_produce'],delta_T_total=candidate['T_total']-reference['T_total']))
    bridges=[]
    for candidate in [r for r in data['new_arms'] if r['method']=='CP']:
        for bridge in [r for r in data['new_arms'] if r['method']=='D1' and (r['role'],r['seed'])==(candidate['role'],candidate['seed'])]:
            for key in ['input_SHA','physical_T','lambda_value','cap','PE_SHA','source_commit','H_semantic_SHA','H_fleet_SHA','root_SHA','root_pivot']:assert candidate[key]==bridge[key],(candidate['role'],key)
            cm,cf=legacy.first_integer_matrix(candidate['destination']);bm,bf=legacy.first_integer_matrix(bridge['destination'])
            assert cm==bm and cf['base_SHA']==bf['base_SHA']
            bridges.append(dict(role=candidate['role'],seed=candidate['seed'],same_PE=True,
                parent_selection_pivot_links_equal=True,first_integer_equal_except_floor=True,
                candidate_floor=cf,bridge_floor=bf,delta_U=candidate['U']-bridge['U'],delta_L=candidate['L']-bridge['L'],
                delta_T_produce=candidate['T_produce']-bridge['T_produce'],delta_T_total=candidate['T_total']-bridge['T_total'],
                CP_source_floors=[candidate['beta0'],candidate['beta1']],old_source_floors=[bridge['beta0'],bridge['beta1']]))
    data.update(R141_D1_pairs=matched,same_PE_bridges=bridges,budget=budget())
    write(OUT/'reports/full.json',data)
    csv_write(OUT/'reports/new_arms.csv',data['new_arms']);csv_write(OUT/'reports/reused_arms.csv',data['reused_arms'])
    csv_write(OUT/'reports/R141_pairs.csv',matched);csv_write(OUT/'reports/same_PE_bridges.csv',bridges)
    print(json.dumps([dict(role=r['role'],method=r['method'],U=r['U'],L=r['L'],T_total=r['T_total']) for r in data['new_arms']],indent=2))

if __name__=='__main__':globals()[sys.argv[1]]()
