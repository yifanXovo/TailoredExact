"""Qualify a whole-run deadline before native proof, without inventing a tree."""
import ast,math,re

def matches(result):
    return result.get('status')=='paper_hga_global_deadline'

def check(folder,p,result,run,audit,route_hash):
    assert matches(result)
    done=run.read(folder/'completion.json')
    assert done['returncode']==0 and not done['watchdog'] and done['within_budget']
    assert result['strict_certificate_rejection_reason']=='exact_phase_not_started_after_global_deadline'
    assert not result['strict_certified_original_problem'] and result['lower_bound']==0
    assert math.isfinite(result['upper_bound']) and result['upper_bound']>0
    assert not result['external_gini_tree_root_coverage_valid']
    assert not result['external_gini_tree_parent_child_coverage_valid']
    assert not result['external_gini_tree_internal_budget_scheduling']
    assert not (folder/'external').exists(),'This narrow case permits no started proof service'
    phases=audit.rows(folder/'phases.csv')
    stop=next(r for r in phases if r['event']=='exact_phase_not_started')
    assert stop['status']=='deadline' and float(stop['work_deadline_remaining_seconds'])<=0
    assert 'conservative_lb=0;source=nonnegative_objective' in stop['detail']
    assert not any(r['event']=='exact_phase_start' for r in phases)
    completed=next(r for r in phases if r['event']=='hga_generation_loop_complete')
    assert completed['status']=='deadline_interrupted'
    # Check the mathematical premise of the universal lower bound on the
    # actual parsed-input family, not merely its nonnegative final objective.
    source=(run.ROOT/p['instance_path']).read_text(encoding='utf-8')
    def vector(name):
        found=re.search(r'(?m)^\s*'+name+r'\s*=\s*(\[[^\n]*\])',source)
        return ast.literal_eval(found[1]) if found else []
    target=vector('target');weights=vector('weights')
    assert float(p['lambda'])>=0 and all(v>0 for v in target[1:])
    assert not weights or all(math.isfinite(v) and v>=0 for v in weights[1:])
    physical=audit.physical_module.physical(p,result)
    assert physical['original_T_feasible'] and abs(physical['F']-result['upper_bound'])<=1e-7
    digest=route_hash(result)
    assert result['hga_retained_verified_event_candidate'] and digest==result['hga_retained_candidate_sha256']
    events=[r for r in audit.rows(folder/'hga_events.csv') if r['published']=='1' and r['verifier_passed']=='1' and r['content_sha256']==digest]
    assert events and abs(float(events[0]['objective'])-physical['F'])<=1e-7
    return dict(legal_global_lower_bound=0,physical=physical,native_optimize_calls=0,
        full_retained_route_sha256=digest,full_verified_event_link=True,
        conservative_witness_available_by=float(completed['process_seconds']),
        coverage_scope='Universal nonnegative objective covers the full original domain; no proof tree was started',
        certificate=False,raw_tree_flags_remain_false=True,script_sha256=run.sha(__file__))
