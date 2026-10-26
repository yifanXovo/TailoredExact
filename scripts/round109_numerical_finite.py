"""Fault-specific, zero-solver counterexamples for the known-call reader repair."""
from pathlib import Path
import copy, sys
import round109_numerical_recovery as n
import round108_decisions as rule

def run(root,dest):
    root=Path(root).resolve();dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    proof=n.verify(root);identity=n.read(root/n.REL/'campaign/identity.json');launch=identity['launches'][14]
    d=n.core.portable(root,launch['destination']);obs=n.read(d/'observations.json')
    call=next(z['payload'] for z in obs if z['payload']['kind']=='call')
    completion=n.read(d/'completion.json');q=n.core.evidence.instance(root,launch['panel'])
    _,model=n.core.model_contract(root,launch['panel'],d/'compact.lp','P-GRB')
    cases=[]
    def reject(name,action):
        try:action()
        except (AssertionError,KeyError,ValueError):cases.append(dict(name=name,rejected=True))
        else:raise AssertionError('counterexample accepted: '+name)
    def badfloor(name,index,value):
        args=[launch['panel']['lambda'],copy.deepcopy(q['w'][1:]),copy.deepcopy(q['D'][1:]),copy.deepcopy(model['objective']),copy.deepcopy(model['bounds'])]
        if index==0:args[0]=value
        elif index in (1,2):args[index][0]=value
        elif index==3:args[3]=(args[3][0],value)
        elif index==4:args[4]['G']=(value,args[4]['G'][1])
        elif index==5:
            name_e=next(k for k,v in args[3][0] if k.startswith('e_'));args[4][name_e]=(value,args[4][name_e][1])
        elif index==6:args[3]=([(k,value if k.startswith('e_') else v) for k,v in args[3][0]],0)
        reject(name,lambda:n.floor(*args))
    assert n.floor(launch['panel']['lambda'],q['w'][1:],q['D'][1:],model['objective'],model['bounds'])==0.
    for name,index,value in [('negative_lambda',0,-.15),('nonfinite_lambda',0,float('nan')),('negative_weight',1,-1),('nonfinite_weight',1,float('inf')),('zero_target',2,0),('negative_target',2,-1),('negative_objective_constant',3,-1),('negative_G_domain',4,-1),('negative_e_domain',5,-1),('negative_penalty_coefficient',6,-.1)]:badfloor(name,index,value)
    for name,change in [('wrong_call',{'call':2}),('wrong_scope',{'model_scope':'local'}),('wrong_model',{'model_sha256':'0'*64}),('raw_precondition_false',{'native_preconditions':0}),('nonboolean_precondition',{'native_preconditions':'1'}),('not_full_original',{'full_original':0})]:
        reject(name,lambda change=change:n.scope(dict(call,**change),completion,launch['command'],launch['command'],proof['raw_files'][(d/'compact.lp').relative_to(root).as_posix()]))
    for name,field,value in [('wrong_seed','Seed',1),('wrong_threads','Threads',2),('changed_feasibility_tolerance','FeasibilityTol',1e-5),('changed_MIPGap','MIPGap',.01)]:
        c=copy.deepcopy(call);c['settings'][field]=value
        reject(name,lambda c=c:n.scope(c,completion,launch['command'],launch['command'],call['model_sha256']))
    for name,change in [('unsuccessful_return',{'returncode':1}),('hard_stop',{'stop_reason':'hard_stop'}),('out_of_cap',{'within_cap':False})]:
        reject(name,lambda change=change:n.scope(call,dict(completion,**change),launch['command'],launch['command'],call['model_sha256']))
    reject('changed_actual_argv',lambda:n.scope(call,completion,launch['command']+['--altered'],launch['command'],call['model_sha256']))
    for name,lo,hi in [('negative_time',-1,1771),('reversed_time',1772,1771),('time_at_cap',1770,1800),('nonfinite_time',1770,float('inf'))]:reject(name,lambda lo=lo,hi=hi:n.interval(lo,hi,1800))
    original=dict(U=n.read(d/'result.json')['objective'],certificate=False)
    # The guard protects own U, certificate status and the explicitly unknown clock.
    valid=dict(original,L=0.,gap=original['U'],complete_seconds=None,complete_seconds_interval=proof['complete_seconds_interval'],native_call_bounds_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source'])
    n.selected(valid,original,proof)
    for name,change in [('borrowed_UB',{'U':0.}),('certificate_promotion',{'certificate':True}),('invented_exact_clock',{'complete_seconds':1771.}),('native_relabel',{'native_call_bounds_mathematically_qualified':True}),('foreign_floor_source',{'lower_bound_source':'ENS_incumbent'})]:reject(name,lambda change=change:n.selected(dict(valid,**change),original,proof))
    old_sha=n.sha
    for name,path in [('altered_input',root/launch['panel']['input_path']),('altered_model',d/'compact.lp'),('altered_journal',next((d/'journal').glob('*'))),('altered_native_log',d/'native.log'),('altered_fee',root/n.REL/'fees/main05/receipt.json'),('altered_helper',Path(n.__file__)),('altered_reader',root/'scripts/round109_reader.py')]:
        def shim(p,path=path):return '0'*64 if Path(p).resolve()==path.resolve() else old_sha(p)
        n.sha=shim
        try:reject(name,lambda:n.verify(root))
        finally:n.sha=old_sha
    assert n.verify(root)==proof and not (d/'whole_arm_receipt.json').exists()
    n.write(dest/'audit.json',dict(decision='ACCEPT',zero_solver_calls=True,source_SHA=n.sha(Path(__file__)),helper_SHA=n.sha(Path(n.__file__)),reader_SHA=n.sha(root/'scripts/round109_reader.py'),sidecar_SHA=n.sha(root/n.SIDE),actual_raw_identity_verified=True,missing_original_clock_preserved=True,cases=cases,checks=len(cases)))
    print('Fault-specific finite rejection checks:',len(cases),'zero solver calls.')

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
