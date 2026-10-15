"""Actual-Seed, call-scoped read-only extension of the R120 audit.

The frozen PE's journal prerequisite predicate contains Seed==0. Seed1 is
qualified from returned complete actual matrices/settings/Starts and scopes;
raw flags and callback global-availability are never changed on disk.
"""
from round122_common import *
import contextlib,copy,inspect,types
import round120_evidence as prior
import round114_audit as audit
import round108_reader as core
import round118_call_logs as logs
import round109_seed_scope as computed
import round109_seed_audit as seed_audit
import round115_verify as verifier
ArmModels=prior.ArmModels
_JOURNAL_SOURCE=inspect.getsource(audit.journal)
_RETURN_SOURCE=inspect.getsource(audit.return_chain)
_OLD_JOURNAL=core.evidence.journal
PRESETS={'P-GRB':'custom','ENS-C':'research-round83-vds-equal-net-exchange','M-B':'research-round99-ensc-discrete-structure-m-binary',
    'MB-D0':'research-round120-native-proof-d0','MB-D1':'research-round120-native-proof-d1'}
def _compile(source,module,extras):
    namespace=dict(vars(module),**extras);exec(compile(source,__file__+'::explicit_actual_seed','exec'),namespace)
    return namespace[source.split('def ',1)[1].split('(',1)[0]]
def _raw_journal(root,l,d,observations):
    source=_JOURNAL_SOURCE.replace("e['settings']==SETTINGS","e['settings']==expected_settings(l['seed'])")
    source=source.replace("assert e['native_preconditions'] and e['lower_g']==0", "assert e['native_preconditions']==(l['seed']==0) and e['lower_g']==0")
    return _compile(source,audit,dict(expected_settings=computed.expected))(root,l,d,observations)
def _parameters(result,*,seed,require_call,arm):
    if require_call:
        for suffix in ['requested','effective']:assert result['gurobi_seed_'+suffix]==seed
        assert result['gurobi_seed_set_return_code']==result['gurobi_seed_get_return_code']==0
    projected=dict(result)
    for suffix in ['requested','effective']:
        if 'gurobi_seed_'+suffix in projected:projected['gurobi_seed_'+suffix]=0
    value=seed_audit._parameters(projected,require_call=require_call,arm=arm)
    if require_call:value['seed']={suffix:result['gurobi_seed_'+suffix] for suffix in ['requested','effective','set_return_code','get_return_code']}
    return value
def qualify_seed(root,l,observations,completion,identity):
    root=Path(root).resolve();d=core.portable(root,l['destination']);p=l['panel'];seed=l['seed']
    assert p['gurobi_seed']==seed and l['command'][l['command'].index('--gurobi-seed')+1]==str(seed)
    for r in observations:
        if r['payload']['kind']=='call':assert r['payload']['settings']==computed.expected(seed)
    if seed==0:return dict(schema='round121-computed-seed-scope-v1',actual_seed=0,recovered_calls=[],raw_flags_preserved=True)
    assert completion['stop_reason']=='normal_return' and completion['returncode']==0 and completion['within_cap']
    assert observations==read(d/'observations.json') and completion==read(d/'completion.json')
    saved=read(d/'launch.json');assert saved['command']==l['command'] and saved['panel']==p
    assert sha(root/p['input_path'])==p['input_sha256']
    for n,h in identity['source_hashes'].items():assert sha(root/n)==h
    forbidden=['--round60','--round63','--round65-projection','--round65-budget','--round65-controller','--round89','--round96','--round97','--round101','--round102','--round103','--round104','--round105','--round106','--round107','--round119','--round100-continuous-quantities','--round120-qualification']
    assert not any(any(arg.startswith(prefix) for prefix in forbidden) for arg in l['command'])
    result=read(d/'result.json');assert result['algorithm_preset']==PRESETS[l['arm']]
    j=_raw_journal(root,l,d,observations)
    assert not j['failure'] and not j['unreturned_ids']
    scope_owner=getattr(core.model_scope_contract,'__self__',None)
    if scope_owner is None:parser=core.lp_model
    else:
        assert isinstance(scope_owner,ArmModels),'unknown bound scope-check implementation'
        parser=lambda path:scope_owner.data(path)[1][0]
    view=logs.build(root,l,d,j,result,model_parser=parser)
    actual=[cid for cid in j['calls'] if cid not in j['not_started_ids']]
    ledger=view['ledger'];assert l['arm']=='P-GRB' or len(ledger)==len(actual)
    if l['arm']=='P-GRB':
        assert actual==[1] and result['gurobi_optimize_count']==1 and result['gurobi_optimize_return_code']==0
        assert result['gurobi_native_domain_audit_passed'] and result['gurobi_lifecycle_valid']
        assert result['native_mip_strict_gap_parameters_valid'] and result['gurobi_hga_start_requested'] is False
        for k,f in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:assert result[f]==p['reference'][k]
    elif actual:
        for field in ['backend_parameter_roundtrip_valid','feasibility_consistency_gate','lifecycle_complete','root_coverage_valid','parent_child_coverage_valid']:
            assert result['external_gini_tree_'+field] is True
        assert result['external_gini_tree_failure_reason'] in ['none','overall_global_deadline']
    else:
        physical=core.full_fleet(root,p,result);a=core.evidence.instance(root,p)
        assert p['lambda']>=0 and all(w>=0 for w in a['w'][1:]) and physical['F']<=1e-12
    proofs=[];context=ArmModels()
    try:
        for position,cid in enumerate(actual):
            c=j['calls'][cid]
            assert type(c['native_preconditions']) in [bool,int] and c['native_preconditions']==0 and cid in j['returned_ids']
            row=ledger[position] if ledger else None
            if row and row['solve_kind']=='LP':
                assert int(row['integer_domain_restored'])==1;continue
            path=core.portable(root,c['model_path'])
            assert sha(path)==c['model_sha256']
            if c['full_original']:
                assert l['arm']=='P-GRB' and sha(path)==p['reference']['canonical_sha256']==sha(d/'compact.lp')
                m=core.lp_model(path);fact=dict(SHA=sha(path),rows=len(m['rows']),columns=len(m['order']),full_original=True)
                assert 'Loaded user MIP start' not in view['views'][cid]['text']
            else:
                assert l['arm'] in ['ENS-C','M-B','MB-D0','MB-D1']
                fact,m=context.model_contract(root,p,path,l['arm'])
            scope=context.model_scope_contract(c,m,p)
            assert not any(q['payload']['kind']=='bound' and q['payload']['call']==cid and
                (q['payload']['global_available'] or q['payload']['global_bound'] is not None) for q in observations)
            proofs.append(dict(call=cid,raw_native_preconditions=False,computed_native_prerequisites=True,model=fact,scope=scope,
                call_scoped_log_binding=view['views'][cid]['binding'],successful_return=True,actual_settings=c['settings'],
                qualification_role='offline returned original-model scope proof; no callback/global flag promotion'))
    finally:context.clear()
    return dict(schema='round121-computed-seed-scope-v1',actual_seed=seed,recovered_calls=proofs,
        observations_SHA=sha(d/'observations.json'),completion_SHA=sha(d/'completion.json'),result_SHA=sha(d/'result.json'),
        producer_source_SHA=identity['source_hashes']['src/GurobiBaseline.cpp'],raw_flags_preserved=True,
        raw_global_available_and_global_bound_unchanged=True,production_or_search_changed=False)
def journal(root,l,d,observations):
    j=_raw_journal(root,l,d,observations)
    if l['seed']==1:
        proof=qualify_seed(root,l,observations,read(d/'completion.json'),read(d.parents[1]/'identity.json'))
        j=computed.projected_journal(j,proof)
    return j
def legacy_journal(root,p,d):
    value=_OLD_JOURNAL(root,p,d)
    if p.get('gurobi_seed',0)==1:
        identity=read(d.parents[1]/'identity.json');l=next(l for l in identity['launches'] if core.portable(root,l['destination'])==d)
        proof=qualify_seed(root,l,read(d/'observations.json'),read(d/'completion.json'),identity)
        value=computed.projected_journal(value,proof)
    return value
@contextlib.contextmanager
def extension():
    with prior.extension():
        old=(audit.journal,audit.return_chain,computed.qualify,core.evidence.journal)
        source=_RETURN_SOURCE.replace("['ENS-C','M-B']","['ENS-C','M-B','MB-D0','MB-D1']")
        source=source.replace("parameters.parameter_readback(r,require_call=True,arm='P-GRB')","actual_parameter_readback(r,seed=l['seed'],require_call=True,arm='P-GRB')")
        audit.journal=journal;audit.return_chain=_compile(source,audit,dict(actual_parameter_readback=_parameters))
        computed.qualify=qualify_seed;core.evidence.journal=legacy_journal
        try:yield
        finally:audit.journal,audit.return_chain,computed.qualify,core.evidence.journal=old
def event_chain(root,l,d,j):return prior.event_chain(root,l,d,j)
def verify(l,i):
    d=Path(l['destination'])
    with extension():
        j=audit.journal(ROOT,l,d,read(d/'observations.json'));context=ArmModels();contracts=[]
        try:
            for cid,c in j['calls'].items():
                path=core.portable(ROOT,c['model_path'])
                if c['full_original']:
                    m=core.lp_model(path);assert sha(path)==l['panel']['reference']['canonical_sha256'];fact=dict(full_original=True,SHA=sha(path))
                else:fact,m=context.model_contract(ROOT,l['panel'],path,l['arm'])
                contracts.append(dict(fact,call=cid,scope=context.model_scope_contract(c,m,l['panel'])))
            view=logs.build(ROOT,l,d,j,read(d/'result.json'))
        finally:context.clear()
        write(d/'round120_model_contracts.json',dict(contracts=contracts,Optimize=0,original_M_B_quantity_type='C' if l['arm'] in prior.NEW+['M-B'] else None))
        write(d/'call_log_views.json',dict(schema='round118-call-log-views-v1',bindings=view['bindings'],producer_receipt_SHA=sha(d/'producer_receipt.json'),
            raw_bytes_unchanged=True,generated_after_seal=True,actual_Optimize=len(view['actual']),not_started=sorted(j['not_started_ids'])))
        # Complete the added audit before the inherited final verification clock closes.
        mechanism=event_chain(ROOT,l,d,j)
        write(d/'round120_extended_verification.json',dict(event_contract=mechanism,event_contract_complete=True,
            inherited_full_verification_pending=True,final_inherited_status_source='audit.json and verification_closeout.json',postseal_Optimize=0))
        with logs.activate(view):value=verifier.verify(l,i)
    return value
