"""Finite S2R identity and actual-Seed paid compact evidence adapters.

Raw observations, return statuses and certificate booleans remain immutable.
Only the already supported returned-call projection obtains a new PS dispatch.
"""
from round130_common import *
import ast,contextlib,inspect,types
import round128_evidence as prior
import round127_evidence as inherited
import round122_evidence as seeds
import round114_ps as ps
import round112_audit as starts
import round109_seed_scope as computed
import round108_reader as core
import round118_call_logs as logs

def ps_seed(root,l,observations,completion,identity):
    root=Path(root);d=core.portable(root,l['destination']);p=l['panel'];seed=l['seed']
    assert l['arm']=='P-S' and l['method']=='PS' and seed in [0,1]
    assert p['gurobi_seed']==seed and l['command'][l['command'].index('--gurobi-seed')+1]==str(seed)
    assert '--round112-ens-start-compact' in l['command'] and '--round127-mode' not in l['command']
    assert completion['returncode']==0 and completion['stop_reason']=='normal_return' and completion['within_cap']
    assert observations==read(d/'observations.json') and completion==read(d/'completion.json')
    assert read(d/'launch.json')['command']==l['command'] and read(d/'launch.json')['panel']==p
    assert sha(root/p['input_path'])==p['input_sha256']
    for n,h in identity['source_hashes'].items():assert sha(root/n)==h
    r=read(d/'result.json');assert r['algorithm_preset']=='research-round112-self-paid-ens-start-original-compact'
    j=seeds._raw_journal(root,l,d,observations)
    assert not j['failure'] and not j['unreturned_ids']
    actual=[cid for cid in j['calls'] if cid not in j['not_started_ids']]
    assert len(actual)<=1 and set(actual)==j['actual_started_ids']
    proofs=[]
    if actual:
        assert actual==[1] and r['gurobi_optimize_count']==1 and r['gurobi_optimize_return_code']==0
        assert r['gurobi_native_domain_audit_passed'] and r['gurobi_lifecycle_valid']
        assert r['native_mip_strict_gap_parameters_valid'] and r['gurobi_hga_start_requested'] is False
        seeds._parameters(r,seed=seed,require_call=True,arm='P-GRB')
        start=starts.start_audit(root,p,d)
        params=read(d/'round130_parameters.json')
        assert params==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=1,loaded_after_presets=True,authoritative_model_environment=True)
        c=j['calls'][1]
        assert c['full_original'] and c['native_preconditions']==(seed==0) and c['settings']==computed.expected(seed)
        assert c['model_sha256']==p['reference']['canonical_sha256']==sha(d/'compact.lp')
        assert core.lp_model(d/'compact.lp')==core.lp_model(d.parents[1]/'reference'/p['id']/'original.lp')
        assert r['gurobi_num_vars']==p['reference']['columns'] and r['gurobi_num_constrs']==p['reference']['rows']
        view=logs.build(root,l,d,j,r)
        proofs.append(dict(call=1,raw_native_preconditions=bool(c['native_preconditions']),computed_native_prerequisites=True,
            successful_return=True,full_original=True,actual_settings=c['settings'],Start=start,
            call_scoped_log_binding=view['views'][1]['binding'],no_incumbent_adoption_assumed=True))
    else:
        own=core.full_fleet(root,p,read(d/'result.json.round112.startup.json'))
        assert r['status'] in ['startup_zero','startup_deadline']
        if r['status']=='startup_zero':assert own['F']<=1e-7
    return dict(schema='round130-paid-compact-actual-seed-v1',actual_seed=seed,recovered_calls=proofs,
        observations_SHA=sha(d/'observations.json'),completion_SHA=sha(d/'completion.json'),result_SHA=sha(d/'result.json'),
        raw_flags_preserved=True,raw_global_available_and_global_bound_unchanged=True,production_or_search_changed=False)

def clone(fn,replacements,extras=None):
    source=inspect.getsource(fn)
    for old,new in replacements:
        assert old in source,(fn.__name__,old)
        source=source.replace(old,new)
    namespace=dict(fn.__globals__,**(extras or {}))
    exec(compile(source,__file__+'::'+fn.__name__, 'exec'),namespace)
    return namespace[fn.__name__]

@contextlib.contextmanager
def extension():
    old_mdr=prior.is_mdr
    def is_root(d):
        i=read(d.parents[1]/'identity.json')
        return next(l for l in i['launches'] if core.portable(ROOT,l['destination'])==d)['method'] in ['MD-R','S2R']
    prior.is_mdr=is_root
    try:
        with prior.extension():
            saved=(inherited.qualify_seed,computed.qualify,ps.ps_journal,ps.validate_ps_lifecycle,ps.paid_endpoint,core.endpoint)
            def qualify(root,l,observations,completion,identity):
                return ps_seed(root,l,observations,completion,identity) if l['arm']=='P-S' else saved[0](root,l,observations,completion,identity)
            raw_ps=clone(saved[2],[
                ("e['native_preconditions'] and e['settings']==SETTINGS","e['native_preconditions']==(p.get('gurobi_seed',0)==0) and e['settings']==expected_settings(p.get('gurobi_seed',0))")],dict(expected_settings=computed.expected))
            def ps_journal(root,p,d,observations=None):
                j=raw_ps(root,p,d,observations)
                i=read(d.parents[1]/'identity.json');l=next(l for l in i['launches'] if core.portable(root,l['destination'])==d)
                proof=ps_seed(root,l,read(d/'observations.json'),read(d/'completion.json'),i)
                return computed.projected_journal(j,proof) if l['seed'] else j
            lifecycle=clone(saved[3],[
                ("parameters.parameter_readback(r,require_call=True,arm='P-GRB')","actual_parameters(r,seed=l['seed'],require_call=True,arm='P-GRB')"),
                ('expected=dict(threads=1,seed=0,presolve=-1,mip_gap=0.,mip_gap_abs=0.)',"expected=dict(threads=1,seed=l['seed'],presolve=-1,mip_gap=0.,mip_gap_abs=0.)")],dict(actual_parameters=seeds._parameters))
            # The original compact's own strict certificate can already be
            # true at Seed1. Preserve its original equality check, including
            # startup-zero; only journal native-scope flags need projection.
            endpoint=clone(saved[4],[],dict(validate_ps_lifecycle=lifecycle))
            # R128 already enforces full native optimal root return. Its
            # near-closed open-return exception must recognize the new identity.
            # Extract exactly the original function. inspect.getsource on the
            # older exec-created wrapper can return its whole original module.
            text=(ROOT/'scripts/round108_reader.py').read_text()
            node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='endpoint')
            source=ast.get_source_segment(text,node)
            needle='if U-L<=decision.CLOSURE_TOL and not certificate:raise AssertionError'
            assert source.count(needle)==1
            source=source.replace(needle,"if U-L<=decision.CLOSURE_TOL and not certificate and launch.get('method') not in ['MD-R','S2R']:raise AssertionError")
            namespace=dict(saved[5].__globals__,complete_cover=core.complete_cover)
            exec(compile(source,__file__+'::inclusive_root_endpoint','exec'),namespace)
            root_endpoint=namespace['endpoint']
            inherited.qualify_seed=qualify;computed.qualify=qualify
            ps.ps_journal=ps_journal;ps.validate_ps_lifecycle=lifecycle;ps.paid_endpoint=endpoint;core.endpoint=root_endpoint
            try:yield
            finally:
                inherited.qualify_seed,computed.qualify,ps.ps_journal,ps.validate_ps_lifecycle,ps.paid_endpoint,core.endpoint=saved
    finally:prior.is_mdr=old_mdr

def verify(l,i):
    d=Path(l['destination'])
    if l['method']=='P':
        p=read(d/'round127_parameters.json')
        assert p==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=0,loaded_after_presets=True,authoritative_model_environment=True)
    if l['method']=='PS':
        proof=ps_seed(ROOT,l,read(d/'observations.json'),read(d/'completion.json'),i)
        write(d/'round130_paid_compact_qualification.json',proof)
    fn=types.FunctionType(seeds.verify.__code__,dict(vars(seeds),extension=extension),'round130_full_verify')
    return fn(l,i)
