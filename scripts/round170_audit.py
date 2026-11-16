"""Read-only R170 adapter of the qualified R169 journal/model/Start reader.

No optimization, solver API, H production or raw receipt mutation. P uses its
full original compact domain, while B/M/C retain complete interval coverage.
"""
from round170_common import *
import argparse, importlib.util, inspect, re, types

path=ROOT/'results/unified_exact_round169/review/round169_complete_audit.py'
spec=importlib.util.spec_from_file_location('r169_readonly',path)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
old.OUT=OUT
core,proof,call_logs,models=old.core,old.proof,old.call_logs,old.models
TOL=old.TOL

def full_H(p,d):
    answer=old.full_H(p,d)
    prior=read(ROOT/'results/unified_exact_round169/h_path_results.json')['rows']
    facts=[]
    for x in answer['paths']:
        earlier=next(v for v in prior if v['role']==p['id'] and v['name']==x['path'])
        meta=read(d/'primal'/x['path']/'path.json')
        assert meta['fleet_SHA256']==earlier['fleet_SHA256']
        assert meta['initial_random_orders_SHA256']==earlier['initial_random_orders_SHA256']
        for key in ['effective_seed','search_lambda','evaluation_lambda','G','P','F',
                    'physical_R169_SHA256','decoded_checks','physical_work_counter_sum']:
            assert meta[key]==earlier[key],(p['id'],x['path'],key,meta[key],earlier[key])
        facts.append(dict(path=x['path'],same_R169_fleet_orders_parameters_objective_and_work=True,
            inherited_source='c9fcb1f1ee8a2ea07004ad6162831f4bcf01443a:results/unified_exact_round169/h_path_results.json'))
    answer['fixed_H_matches_R169']=facts
    return answer

def tailored(position):
    source=inspect.getsource(old.audit)
    edits=[("def audit(position):","def tailored_readback(position):"),
        ("matrix_execution_frozen.json","matrix_frozen.json"),
        ("h_panel_frozen.json","inputs_frozen.json"),
        ("p=dict(p,cap_seconds=registered['cap'])","p=dict(p,cap_seconds=registered['cap'],reference=p['compact_reference']['metadata'])"),
        ("version='candidate',seed=0,","version='candidate',seed=registered['Native_Seed'],"),
        ("round169-independent-new-runner-postreturn-audit-v1","round170-qualified-tailored-postreturn-audit-v1")]
    for before,after in edits:
        assert before in source,before;source=source.replace(before,after)
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,full_H=full_H)
    exec(compile(source,__file__+'::tailored_readback','exec'),ns)
    out=ns['tailored_readback'](position)
    d=Path(read(OUT/'matrix_frozen.json')['positions'][position-1]['directory'])
    out['actual_Optimize_parameters']=[dict(call=v['call'],settings=v['settings'],model_SHA256=v['model_sha256'])
        for q in sorted((d/'journal').glob('event_*.json')) if (v:=read(q))['kind']=='call']
    out.update(Native_Seed=read(OUT/'matrix_frozen.json')['positions'][position-1]['Native_Seed'],
        raw_reader_semantics='native necessary_H_complete is diagnostic-only; complete_arm_initialization is required',
        exact_first_hit_global_seconds=None,first_hit_missing_reason='no new timing callbacks; buffered logs do not identify exact global discovery')
    return out

def plain(position):
    tick=time.perf_counter();registered=read(OUT/'matrix_frozen.json')['positions'][position-1]
    assert registered['position']==position and registered['arm']=='P'
    d=Path(registered['directory']);inv=read(d/'invocation.json');completion=read(d/'completion.json');r=result(d/'result.json')
    assert inv['argv']==registered['argv'] and inv['PE']['SHA256']==PE_SHA and inv['DLL']['SHA256']==DLL_SHA
    assert completion['rc']==0 and not completion['affinity'].get('wrapper_killed')
    assert completion['process_outer_seconds']<=registered['cap']+2
    assert completion['result']['SHA256']==sha(d/'result.json')
    assert r['process_return_code']==0 and r['process_shutdown_margin_seconds']==6
    assert r['nominal_process_wall_budget_seconds']==600 and r['process_wall_time_comparable'] is True
    assert r['overall_deadline_started_at_process_entry'] is True and r['algorithm_preset']=='custom'
    candidate=read(OUT/'candidate_manifest.json')
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest,name
    p=next(x for x in read(OUT/'inputs_frozen.json')['roles'] if x['id']==registered['role'])
    p=dict(p,cap_seconds=600,reference=p['compact_reference']['metadata'])
    assert sha(ROOT/p['input_path'])==p['input_sha256']
    launch=dict(id=p['id'],arm='P-GRB',method='P',arm_id=d.name,version='candidate',seed=registered['Native_Seed'],
        configuration=dict(MIPFocus=0,Cuts=-1),command=inv['argv'],cap_seconds=600,panel=p)
    js,records=old.journal(launch,d);assert not js['failure'] and not js['unreturned_ids']
    assert len(js['calls'])==js['started']==js['returned']==r['gurobi_optimize_count']==1
    assert all(c['full_original'] and c['native_preconditions'] for c in js['calls'].values())
    assert r['gurobi_hga_start_requested'] is False and r['gurobi_native_domain_audit_passed'] is True
    params=read(d/'round127_parameters.json')
    assert params==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=0,loaded_after_presets=True,authoritative_model_environment=True)
    assert not (d/'primal').exists() and not (d/'hga.csv').exists()
    for name in ['round166_parameters.json','round130_parameters.json','round153_parameters.json',
                 'round154_parameters.json','round160_parameters.json','round162_parameters.json']:
        assert not (d/name).exists(),('unexpected research mechanism',name)
    assert 'Loaded user MIP start' not in (d/'native.log').read_text(encoding='utf-8')
    assert sha(d/'compact.lp')==p['reference']['canonical_sha256']
    for key,field in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:
        assert r[field]==p['reference'][key],(key,r[field],p['reference'][key])
    legacy,kinds=proof._legacy_view(js,launch,d);kinds={cid:'MIP' for cid in js['calls']}
    phase=old.phases(d,600);physical=core.full_fleet(ROOT,p,r)
    assert abs(physical['F']-r['upper_bound'])<TOL
    context=models.ArmModels();contracts=[];data=core.evidence.instance(ROOT,p)
    try:
        emitter=proof.emitter_scope_policy(launch,dict(source_hashes=candidate['source_hashes']))
        for cid,call in js['calls'].items():
            model_path=core.portable(ROOT,call['model_path'])
            fact,model=context.model_contract(ROOT,p,model_path,'P-GRB')
            # P has the original integer-Y compact formulation, not B's
            # one-hot stock interface. Its byte-exact qualified compact matrix
            # plus type/domain/fingerprint checks are the applicable contract.
            assert not any(name.startswith('state_') for name in model['order'])
            ap=dict(enabled=False,one_hot_AP_contract_applicable=False,
                original_compact_reference_SHA256=p['reference']['canonical_sha256'],
                full_matrix_byte_identity_verified=True)
            scope=context.model_scope_contract(call,model,p)
            shortcut=proof.no_improver_shortcut_analysis(launch,call,model,emitter,physical['F'])
            assert not shortcut['model_scope_issue']
            contracts.append(dict(call=cid,model=fact,scope=scope,AP=ap,no_improver_shortcut_check=shortcut))
        view=call_logs.build(ROOT,launch,d,legacy,r,model_parser=lambda q:context.data(q)[1][0])
        assert len(view['actual'])==len(view['bindings'])==1 and view['ledger']==[]
        chain=dict(actual=view['actual'],ledger=[],logs=[dict(call=b['call'],text=view['views'][b['call']]['text']) for b in view['bindings']])
        own=js['witnesses']+[dict(physical,source='actual_R170_return_result',input_SHA=p['input_sha256'],
            physical_verified=True,available=completion['process_outer_seconds'])]
        quality=proof.independent_source_checks(launch,js,kinds,chain,r,own)
        claims=proof._claims(launch,js,chain,r);rejection=proof.reconcile(claims,own)
        assert not rejection['rejections'] and not js['source_rejections']
        with call_logs.activate(view),proof.strict_bound_context():
            final=core.cold_returned_bound(ROOT,d,legacy,r)
        lower=max([0.,final['L']]+[b['global_bound'] for b in legacy['bounds'] if b['global_available']])
        upper=physical['F'];certificate=r['gurobi_status']==2 and upper-lower<=TOL
        assert abs(lower-r['lower_bound'])<=TOL and lower<=upper+TOL
        assert certificate==r['strict_certified_original_problem']
        out=dict(schema='round170-qualified-cold-P-postreturn-audit-v1',UTC=utc(),passed=True,
            position=position,role=p['id'],research_arm='P',Native_Seed=registered['Native_Seed'],Optimize_run_by_reviewer=0,
            actual_invocation=bind(d/'invocation.json'),input=bind(ROOT/p['input_path']),completion=completion,
            U=upper,L=lower,absolute_gap=upper-lower,relative_gap=(upper-lower)/max(abs(upper),1e-12),certificate=certificate,
            certificate_basis='complete_original_cold_compact_native_OPTIMAL_and_physical_UB' if certificate else 'complete_original_cold_compact_qualified_native_bound_open',
            true_final_physical=physical,full_paid_H=None,Start_checks=[],cold_parameters=params,models=contracts,
            journal_events=len(records),actual_Optimize=1,LP=0,MIP=1,Native_seconds=r['gurobi_runtime'],
            actual_call_log_bindings=view['bindings'],actual_native_quality=quality,qualified_cold_bound=final,
            actual_Optimize_parameters=[dict(call=v['call'],settings=v['settings'],model_SHA256=v['model_sha256'])
                for v in js['calls'].values()],
            phase_event_count=len(phase),phase_files=sorted({x['file'] for x in phase}),
            exact_first_hit_global_seconds=None,first_hit_missing_reason='no exact global first-hit clock; rounded solver discovery times not promoted',
            raw_bytes_unchanged=True,audit_seconds=time.perf_counter()-tick)
        return out
    finally:context.clear()

def audit(position):
    registered=read(OUT/'matrix_frozen.json')['positions'][position-1]
    return plain(position) if registered['arm']=='P' else tailored(position)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('positions',nargs='*',type=int);args=ap.parse_args()
    positions=args.positions or [p['position'] for p in read(OUT/'matrix_frozen.json')['positions']
        if (Path(p['directory'])/'completion.json').is_file() and not (OUT/f"review/complete_audit_{p['position']:02}.json").exists()]
    for n in positions:
        tick=time.perf_counter();started=time.time();ok=False;error=None
        try:
            value=audit(n);write(OUT/f'review/complete_audit_{n:02}.json',value);ok=True
            print(json.dumps({k:value[k] for k in ['position','role','research_arm','U','L','certificate','actual_Optimize','audit_seconds']}),flush=True)
        except Exception as e:
            error=repr(e);write(OUT/f'review/complete_audit_{n:02}_failure.json',dict(UTC=utc(),error=error,Optimize=0));raise
        finally:
            path=OUT/'review/complete_audit_attempts.json';records=read(path) if path.is_file() else []
            records.append(dict(position=n,start_epoch=started,UTC=utc(),PASS=ok,error=error,Optimize=0,
                audit_inclusive_seconds=time.perf_counter()-tick));write(path,records)
if __name__=='__main__':main()
