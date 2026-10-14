"""Explicit R120 evidence adapter, retaining original raw labels and bytes."""
from round120_common import *
import collections,contextlib,inspect,types
import round114_audit as audit
import round108_reader as core
import round111_seed_audit as models
import round100_campaign as old_campaign
import round118_call_logs as logs
from round120_math_audit import coefficients,native_endpoints,binary

NEW=['MB-D0','MB-D1']
class ArmModels(models.ArmModels):
    def model_contract(self,root,p,path,arm):
        fact,m=super().model_contract(root,p,path,'M-B' if arm in NEW else arm)
        if arm not in NEW or 'r120_h' not in m['types']:return fact,m
        receipt=read(str(path)+'.round120.json');proof=read(path.parent.parent/'round120_root_pair.json')
        check=coefficients(path);assert receipt['conditional']==(arm=='MB-D1')
        assert m['types']['r120_h']=='B' and m['bounds']['r120_h']==(0.,1.)
        base_name=path.name.replace('_round120_'+arm[-2:].lower(),'')
        base=path.parent/base_name;assert sha(base)==receipt['base_SHA']
        baseline=core.lp_model(base)
        assert m['objective']==baseline['objective']
        assert {k:v for k,v in m['types'].items() if k!='r120_h'}==baseline['types']
        assert {k:v for k,v in m['bounds'].items() if k!='r120_h'}==baseline['bounds']
        assert m['rows'][:-3]==baseline['rows'] and len(m['rows'])==len(baseline['rows'])+3
        ld,ud,fd=[float(receipt[k]) for k in ['lower_delta','upper_delta','objective_delta']]
        obj=dict(m['objective'][0]);obj['r120_h']=-fd
        if not fd:obj.pop('r120_h')
        expected=[(tuple(sorted({'G':1.,'r120_h':-ld}.items())),'>=',float(receipt['lower_base'])),
            (tuple(sorted({'G':1.,'r120_h':-ud}.items())),'<=',float(receipt['upper_base'])),
            (tuple(sorted(obj.items())),'>=',float(receipt['objective_base']))]
        assert m['rows'][-3:]==expected,'actual extension does not match complete objective and three declared rows'
        assert proof['input_SHA']==p['input_sha256']
        for side in [0,1]:
            c=proof['proofs'][side];raw=min(c['bound'],c['cutoff'])
            beta=proof['beta0' if side==0 else 'beta1']
            if raw>=1e-7:assert binary(beta)<=binary(raw)-binary(1e-7)
            else:assert beta==0,'nonnegative objective fallback is explicit'
            assert sha(core.portable(root,c['path']))==c['model']
        fact.update(original_rows_types_bounds_objective_equal=True,base_SHA=sha(base),root_proof_pair_SHA=sha(path.parent.parent/'round120_root_pair.json'),
            extension=check,added_columns=1,added_rows=3)
        return fact,m

def extend(fn):
    source=inspect.getsource(fn)
    needle="'M-B':'research-round99-ensc-discrete-structure-m-binary'"
    source=source.replace(needle,needle+",'MB-D0':'research-round120-native-proof-d0','MB-D1':'research-round120-native-proof-d1'")
    source=source.replace("['ENS-C','M-B']","['ENS-C','M-B','MB-D0','MB-D1']")
    source=source.replace("=='M-B'"," in ['M-B','MB-D0','MB-D1']")
    namespace=fn.__globals__;exec(compile(source,__file__+'::explicit_R120_evidence','exec'),namespace)
    return namespace[fn.__name__]
@contextlib.contextmanager
def extension():
    changed=[]
    for module,names in [(audit,['return_chain','rejected_mandatory','adapter']),(old_campaign,['adapter']),(core,['endpoint']),(logs,['build'])]:
        for name in names:
            fn=getattr(module,name);changed.append((module,name,fn));setattr(module,name,extend(fn))
    original=models.ArmModels;models.ArmModels=ArmModels
    try:yield
    finally:
        models.ArmModels=original
        for module,name,fn in reversed(changed):setattr(module,name,fn)

def event_chain(root,l,d,j):
    path=d/'external/round120_events.jsonl'
    if l['arm'] not in NEW:
        assert not path.exists();return dict(enabled=False,installed=0,extra_proof_triggered_interrupts=0)
    assert '--round120-native-proof-'+l['arm'][-2:].lower() in l['command']
    assert '--round119-proof-contraction' not in l['command']
    if not path.exists():
        physical=core.full_fleet(root,l['panel'],read(d/'result.json'))
        assert j['started']==0 and abs(physical['F'])<=1e-12
        return dict(enabled=True,installed=0,not_exposed_original_verified_zero_H=True)
    events=[json.loads(row) for row in path.read_text().splitlines()]
    assert [x['sequence'] for x in events]==list(range(1,len(events)+1))
    assert not any(x['kind']=='revoked' for x in events),'PROOF_RELIABILITY_PRIORITY'
    paid=[x for x in events if x['kind']=='paid_root_LP_returned'];install=[x for x in events if x['kind']=='root_formulation_installed']
    assert len(paid)<=2 and len(install)<=1
    for x in paid:
        call=j['calls'][x['call']];assert x['call'] in j['returned_ids']
        assert (call['model_sha256'],call['leaf'],call['lower_g'],call['upper_g'],call['cutoff'])==(x['model'],'L0.'+str(x['side']),x['lower'],x['upper'],x['cutoff'])
        assert x['status']=='OPTIMAL' and sha(core.portable(root,x['path']))==x['model']
        for w in j['witnesses']:
            if x['lower']<=w['G']<=x['upper'] and w['F']<=x['cutoff']:assert x['bound']<=w['F']+1e-7
    audits=[];pair=None
    if install:
        assert len(paid)==2 and all(x['process_seconds']<=install[0]['process_seconds'] for x in paid)
        pair=read(d/'external/round120_root_pair.json')
        assert pair['input_SHA']==l['panel']['input_sha256']
        native=core.evidence.controller_tables(d,read(d/'result.json'))['controller_native']
        mip=[q for q in native if q['solve_kind']!='LP'];assert mip
        assert mip[0]['leaf_id']=='L0' and mip[0]['model_sha256']==install[0]['model']
        for q in mip:
            cid=next(cid for cid,c in j['calls'].items() if c['native_log_path'].replace('\\','/')==q['native_log'].replace('\\','/') and c['model_sha256']==q['model_sha256'])
            c=j['calls'][cid];assert pair['a']<=c['lower_g']<=c['upper_g']<=pair['b']
            path_native=core.portable(root,q['native_log']);check=native_endpoints(str(path_native)+'.round120.native.json',pair);audits.append(check)
            assert 'r120_h' in core.lp_model(core.portable(root,c['model_path']))['types']
        # Retain the actual original target -> terminal identities and every
        # epoch/domain change; no inferred whole-tree retention statement.
        continuity=[dict(call=cid,model=c['model_sha256'],leaf=c['leaf'],lower=c['lower_g'],upper=c['upper_g'],cutoff=c['cutoff']) for cid,c in j['calls'].items() if c['native_preconditions']]
    else:continuity=[]
    returns=[x for x in events if x['kind']=='extended_native_returned']
    for x in returns:assert x['call'] in j['returned_ids'] and x['return_code']==0
    assert all(x['kind'] not in ['termination_requested','atomic_contraction_committed'] for x in events)
    value=dict(enabled=True,installed=len(install),paid_root_proofs=paid,pair=pair,install_events=install,returns=returns,
        actual_extended_Optimize=len([x for x in returns if x['attempted']]),native_request_continuity=continuity,native_audits=audits,
        native_incumbent_samples=[x for x in events if x['kind']=='native_incumbent_observed'],
        native_relaxation_samples=[x for x in events if x['kind']=='first_optimal_native_root_relaxation'],
        extra_proof_triggered_interrupts=0,new_proof_triggered_contraction_or_Optimize_requests=0,native_h_fixing_or_branching='unknown',events_SHA=sha(path))
    write(d/'round120_event_contract.json',value);return value

def verify(l,i):
    import round115_verify as inherited
    d=Path(l['destination']);j=audit.journal(ROOT,l,d,read(d/'observations.json'));context=ArmModels();contracts=[]
    try:
        for cid,c in j['calls'].items():
            path=core.portable(ROOT,c['model_path'])
            if c['full_original']:
                m=core.lp_model(path);assert sha(path)==l['panel']['reference']['canonical_sha256'];fact=dict(full_original=True,SHA=sha(path))
            else:fact,m=context.model_contract(ROOT,l['panel'],path,l['arm'])
            contracts.append(dict(fact,call=cid,scope=context.model_scope_contract(c,m,l['panel'])))
            if len(context.models)>2:context.models.clear()
        with extension():view=logs.build(ROOT,l,d,j,read(d/'result.json'))
    finally:context.clear()
    write(d/'round120_model_contracts.json',dict(contracts=contracts,Optimize=0,original_M_B_quantity_type='C' if l['arm'] in NEW+['M-B'] else None))
    write(d/'call_log_views.json',dict(schema='round118-call-log-views-v1',bindings=view['bindings'],producer_receipt_SHA=sha(d/'producer_receipt.json'),
        raw_bytes_unchanged=True,generated_after_seal=True,actual_Optimize=len(view['actual']),not_started=sorted(j['not_started_ids'])))
    with extension(),logs.activate(view):value=inherited.verify(l,i)
    mechanism=event_chain(ROOT,l,d,j)
    write(d/'round120_extended_verification.json',dict(event_contract=mechanism,normal_return_and_inherited_full_checks=True,postseal_Optimize=0))
    return value
