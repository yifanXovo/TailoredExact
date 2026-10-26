"""Light completed-endpoint checks; model/vector audits wait for a queue boundary."""
import argparse,math
import package_round71 as package
run=package.run
audit=package.shared.analyze_round68

def check(number):
    package.bind()
    entry=next(e for e in run.runner.entries() if e['charged'] and e['charged_number']==number)
    folder=run.ROOT/entry['destination']
    done=run.read(folder/'completion.json')
    assert done['returncode']==0 and not done['watchdog'] and done['within_budget']
    result=run.read(folder/'result.json');p=run.panel()[entry['id']]
    physical=audit.physical_module.physical(p,result)
    assert physical['original_T_feasible']
    upper=float(result['upper_bound']);lower=float(result['lower_bound'])
    assert math.isfinite(upper) and math.isfinite(lower) and lower<=upper+1e-7
    assert abs(upper-physical['F'])<=1e-7 and abs(upper-result['objective'])<=1e-7
    if result['strict_certified_original_problem']:assert upper-lower<=1e-7
    coverage=None
    if entry['arm']=='P-GRB':
        for name,value in [('threads',1),('seed',0),('presolve',-1),('mip_gap',0),('mip_gap_abs',0)]:
            assert result['gurobi_'+name+'_effective']==value
            assert result['gurobi_'+name+'_set_return_code']==result['gurobi_'+name+'_get_return_code']==0
        assert result['gurobi_native_domain_audit_passed'] and result['gurobi_lifecycle_valid']
        assert result['gurobi_model_fingerprint']==run.read(run.OUT/'fingerprints.json')[entry['id']]['fingerprint']
        assert not result['gurobi_hga_start_requested']
        assert result['gurobi_obj_bound_c_available'] and result['gurobi_obj_bound_c']==lower
        calls=1
    elif package.startup_deadline.matches(result):
        coverage=package.startup_deadline.check(folder,p,result,run,audit,package.route_hash)
        calls=0
    else:
        assert result['external_gini_tree_root_coverage_valid'] and result['external_gini_tree_parent_child_coverage_valid']
        assert not result['external_gini_tree_internal_budget_scheduling']
        assert not (folder/'external/optional_budget.csv').exists()
        ledger=audit.rows(folder/'external/paper_optimize_ledger.csv');calls=len(ledger)
        if ledger:assert result['external_gini_tree_backend_parameter_roundtrip_valid']
        for call in ledger:
            if call['solve_kind']=='LP':assert call['integer_domain_restored']=='1'
        leaves=audit.rows(folder/'external/paper_leaf_ledger.csv')
        if leaves:
            coverage=audit.tree_coverage(folder,leaves,p)
            active=[leaf for leaf in leaves if leaf['status'] not in ['replaced','coalesced']]
            if active:assert lower<=min(upper,min(float(leaf['lower_bound']) for leaf in active))+1e-7
    report=dict(number=number,id=entry['id'],arm=entry['arm'],cap=entry['cap_seconds'],
        wall=done['wall_seconds'],UB=upper,LB=lower,signed_gap=upper-lower,
        certificate=result['strict_certified_original_problem'],physical=physical,
        endpoint_settings_and_coverage_checks=True,
        independent_interval_union=coverage if not package.startup_deadline.matches(result) else None,
        pre_proof_full_domain_bound=coverage if package.startup_deadline.matches(result) else None,
        optimize_calls=calls,result_sha256=run.sha(folder/'result.json'),script_sha256=run.sha(__file__),
        scope='Light completed endpoint only; full model, Start-vector and trajectory audits remain required at queue boundary')
    run.write(run.OUT/'endpoint_checks'/f'{number}.json',report)
    print(report)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('number',type=int)
    check(parser.parse_args().number)
