"""Count-aware extension of the accepted pure complete-method reader.

The immutable schema1 records and producer clocks are never edited. Existing
physical/H/Start/Native parameter/quality/seal/lifecycle checks are reused.
"""
from round141_common import *
from fractions import Fraction as F
import collections, csv, types
import round135_read as base
import round137_read as accepted
from round140_qualify import exact_matrix
from round141_math import membership,model_counts,serializable,child_rows

def count_scope(scope):
    payload=scope.get('settings',{}).get('round141_count_scope')
    if payload is None:return None
    a=payload.split(';');assert len(a)>=8 and a[0]=='v1'
    t=int(a[1])*F(2)**int(a[2]);pivot,side,n=map(int,a[3:6])
    assert t>0 and side in [0,1] and len(a)==n+8
    supports={};ratios={}
    for i in range(1,n+1):
        fields=a[i+7].split(',');ratios[i]=F(float(fields[0]));supports[i]=list(map(int,fields[1:]))
        assert ratios[i]>0 and supports[i]==sorted(set(supports[i]))
    return dict(threshold=t,pivot=pivot,side=side,n=n,root_SHA=a[6],support_SHA=a[7],supports=supports,ratios=ratios)

def same_count(c,Y):
    assert len(Y)==c['n']+1
    if any(Y[i] not in c['supports'][i] for i in c['supports']):return False
    K=sum(c['ratios'][i]*Y[i]>=c['threshold'] for i in c['supports'])
    return K<=c['pivot'] if c['side']==0 else K>=c['pivot']+1

def verify(launch,identity):
    d=Path(launch['destination']);p=launch['panel']
    assert read(d/'round140_parameters.json')==dict(counts='tc2',stock=True,placement='both',
        gurobi_seed=launch['seed'],H_seed=20260626,loaded_after_presets=True)
    actual=read(d/'round141_parameters.json')
    assert actual==dict(mode=launch['proof_mode'],threshold_rule='max_weighted_remainder',pivot='lp_floor',
        root_once=True,BranchPriority=0,counts='tc2',stock=True,Seed=launch['seed'],H_seed=20260626)
    stable_controls=read(d/'round137_parameters.json')
    assert stable_controls==dict(split_threshold=launch.get('AM_threshold',.08),delete_ab=False,
        delete_cr=False,delete_cg=False,loaded_after_presets=True)
    events=[json.loads(line) for line in (d/'external/round141_events.jsonl').read_text().splitlines()]
    choice=next((e for e in events if e['kind']=='root_count_selected'),None)
    probes=[e for e in events if e['kind']=='count_probe_returned']
    pair=next((e for e in events if e['kind']=='pair_ready'),None)
    outcome=read(d/'round141_outcome.json')
    if pair:
        assert len(probes)==2 and all(e['qualified'] for e in probes) and outcome['pair_ready']
        assert pair['cover']==min(pair['beta0'],pair['beta1'])
        for e in probes:
            want=max(0.,math.nextafter(min(e['raw_bound'],choice['model_cutoff'])-1e-7,-math.inf))
            assert e['beta']==want and not e['physical_side_deleted']
        root=read(d/'external/round141_root_selectors.json')
        assert root['model_SHA']==choice['root_SHA'] and root['extra_Optimize']==0
    else:assert not outcome['pair_ready']

    class ArmModels(accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            fact,model=super().model_contract(root,p,path,arm)
            added,_=exact_matrix(path,p,'tc2',True,False);fact['round140_counts']=added
            # Ordinary rows remain present; every extra row is checked below.
            return fact,model
        def model_scope_contract(self,scope,model,p):
            fact=super().model_scope_contract(scope,model,p)
            counter=collections.Counter(model['rows']);c=count_scope(scope)
            if c:
                assert choice and c['root_SHA']==choice['root_SHA'] and c['support_SHA']==choice['support_SHA']
                assert c['threshold']==int(choice['threshold_units'])*F(2)**choice['threshold_exponent']
                assert c['pivot']==choice['pivot']
                add=json.loads(json.dumps(serializable(model_counts(model,p['total_initial']-sum(p['Q_vector']),p['total_initial']))))
                keys=membership(add,c['threshold']);side='low' if c['side']==0 else 'high'
                wanted=(tuple(sorted((k,1.) for k in keys)),'<=' if c['side']==0 else '>=',float(c['pivot']+(c['side']==1)))
                assert counter[wanted]==1
                child=child_rows(add,c['threshold'],c['pivot'],side)
                terms={n:1. for n in model['order'] if n.startswith('h_')}
                terms.update({k:-v for k,v in child['coefficients'].items()})
                smallest=min(abs(v) for v in terms.values() if v);exponent=0
                while math.ldexp(smallest,exponent)<1e-12:exponent+=1
                wanted=(tuple(sorted((n,math.ldexp(v,exponent)) for n,v in terms.items())), '>=',math.ldexp(child['constant'],exponent))
                assert counter[wanted]>=1
                assert scope['cover']==[] and scope['leaf'].startswith('round141_count_')
                assert 'r141_b' not in model['order']
                fact=dict(fact,round141_count_side=c['side'],global_Gini_cover=False)
            if 'r141_b' in model['order']:
                assert choice and pair and model['types']['r141_b']=='B' and model['bounds']['r141_b']==(0.,1.)
                add=json.loads(json.dumps(serializable(model_counts(model,p['total_initial']-sum(p['Q_vector']),p['total_initial']))))
                threshold=int(choice['threshold_units'])*F(2)**choice['threshold_exponent']
                K={k:1. for k in membership(add,threshold)};m=choice['pivot']
                upper={**K,'r141_b':float(-(choice['u']-m))};lower={**K,'r141_b':float(-(m+1-choice['ell']))}
                assert counter[(tuple(sorted(upper.items())),'<=',float(m))]==1
                assert counter[(tuple(sorted(lower.items())),'>=',float(choice['ell']))]==1
                obj,constant=model['objective'];found=[]
                for terms,sense,rhs in model['rows']:
                    coeff=dict(terms);delta=-coeff.pop('r141_b',0.)
                    if sense=='>=' and coeff==dict(obj):found.append((rhs,delta))
                assert len(found)==1
                rhs,delta=found[0];b0,b1=(pair['beta0'],pair['beta1']) if launch['proof_mode']=='d1' else (pair['cover'],pair['cover'])
                assert F(rhs)+F(constant)<=F(b0) and F(rhs)+F(delta)+F(constant)<=F(b1)
                assert abs(rhs+constant-b0)<1e-13 and abs(delta-(b1-b0))<1e-13
                assert scope['lower_g']>=choice.get('root_g_lower',0.)
                fact=dict(fact,round141_mode=launch['proof_mode'],ObjCon=constant,endpoints_conservative=True)
            return fact

    ns=dict(vars(base),ROOT=ROOT,OUT=OUT)
    # Rebind local helpers to one fresh namespace: no historical module or raw
    # object is mutated, and all recursive domain checks see count membership.
    for name,fn in vars(base).items():
        if isinstance(fn,types.FunctionType) and fn.__globals__ is vars(base):
            ns[name]=types.FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
    original_same=ns['_same_domain'];original_global=ns['strict_global_bound']
    def same_domain(scope,witness):
        if not original_same(scope,witness):return False
        c=count_scope(scope)
        return c is None or same_count(c,witness['Y'])
    def global_bound(scope,value,witnesses):
        assert count_scope(scope) is None,'count side is local; no implicit global/Gini coverage'
        return original_global(scope,value,witnesses)
    ns['_same_domain']=same_domain;ns['strict_global_bound']=global_bound
    def gini_inputs(journal,controller):
        # Count LPs are real audited Native calls, but are not Gini leaves or
        # proof pieces. Their floors enter only via the independently checked
        # canonical embedding. Keep every raw call in lifecycle/quality audits;
        # give the inherited Gini-only coverage algebra its actual obligations.
        count_ids={cid for cid,s in journal['calls'].items() if count_scope(s) is not None}
        gini_j=dict(journal,calls={cid:s for cid,s in journal['calls'].items() if cid not in count_ids},
            bounds=[b for b in journal['bounds'] if b['call'] not in count_ids],
            returned_native_proofs=[b for b in journal.get('returned_native_proofs',[]) if b['call'] not in count_ids])
        gini_controller=dict(controller,controller_native=[r for r in controller['controller_native']
            if not r['leaf_id'].startswith('round141_count_')])
        return gini_j,gini_controller
    def gini_cover(journal,controller,U):
        return base.core.chronological_cover(*gini_inputs(journal,controller),U)
    def complete_gini_cover(destination,U,journal,controller,gmax):
        gini_j,gini_controller=gini_inputs(journal,controller)
        return base.core.complete_cover(destination,U,gini_j,gini_controller,gmax)
    ns['core']=types.SimpleNamespace(**dict(vars(base.core),chronological_cover=gini_cover,complete_cover=complete_gini_cover))
    ns['models']=types.SimpleNamespace(**dict(vars(base.models),ArmModels=ArmModels))
    value=ns['verify'](launch,identity)
    leaves=base.core.rows(d/'external/paper_leaf_ledger.csv')
    assert not any(r['leaf_id'].startswith('round141_count_') for r in leaves)
    native_audits=[read(path) for path in (d/'external/native_logs').glob('*.round141.native.json')]
    assert all(row['PASS'] and row['Optimize_extra']==0 for row in native_audits)
    write(d/'round141_control_audit.json',dict(PASS=True,actual=actual,stable_controls=stable_controls,outcome=outcome,probes=probes,
        choice=choice,pair=pair,native_added_row_audits=native_audits,
        count_sides_not_in_Gini_frontier=True,source_membership_uses_verified_Y=True,Optimize=0))
    return value

def postverify(batch,position):
    """Re-read a sealed producer after a pure reader correction; no admission
    bypass can start Native because this action has no producer code path.
    """
    matrix=read(OUT/f'{batch}_matrix.json');group=matrix['groups'][position-1]
    camp=OUT/group['group'];assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists()
    assert read(d/'producer_receipt.json')['native_stopped_no_reentry']
    result=verify(launch,identity)
    write(d/'round141_reader_correction.json',dict(pure_reader_SHA=sha(__file__),Optimize=0,
        producer_rerun=False,original_matrix_SHA=sha(OUT/f'{batch}_matrix.json'),original_identity_SHA=group['identity_SHA']))
    print(json.dumps(result['arm']),flush=True)

if __name__=='__main__':postverify(sys.argv[1],int(sys.argv[2]))
