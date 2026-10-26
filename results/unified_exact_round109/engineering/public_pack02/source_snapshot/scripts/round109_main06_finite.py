"""Actual fault/interval/coupon counterexamples; imports never invoke a solver."""
import copy,itertools,json,sys
from pathlib import Path
import round109_main06_recovery as n
import round109_prepaid_wrapper as w
import round109_interval_pairs as ip
import round108_decisions as old

def run(root,dest):
    root=Path(root).resolve();dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    proof=n.verify(root);identity=n.read(root/n.REL/'campaign/identity.json');launch=identity['launches'][16]
    d=n.core.portable(root,launch['destination']);r=n.read(d/'result.json');c=n.read(d/'completion.json')
    phases=n.core.rows(d/'phases.csv');text=(d/'native.log').read_text();cases=[]
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError,KeyError,TypeError):cases.append(dict(name=name,rejected=True))
        else:raise AssertionError('counterexample accepted: '+name)
    n.functional(r,c,phases,text)
    for name,changes in [('optimize_error',{'gurobi_optimize_return_code':1}),('native_rc_missing',{'native_mipopt_return_code':None}),
        ('wrong_count',{'gurobi_optimize_count':2}),('not_finalized',{'native_mip_solver_finalization_reached':False}),('nonoptimal_status',{'gurobi_status':9})]:
        reject(name,lambda changes=changes:n.functional(dict(r,**changes),c,phases,text))
    for k in ['native_mip_evidence_capture_complete','native_mip_problem_freed','native_mip_environment_closed','native_mip_lifecycle_valid']:
        reject('false_'+k,lambda k=k:n.functional(dict(r,**{k:False}),c,phases,text))
    for k in ['native_mip_freeprob_return_code','native_mip_close_return_code']:
        reject('error_'+k,lambda k=k:n.functional(dict(r,**{k:1}),c,phases,text))
    for k in ['native_mip_environment_count','native_mip_problem_count','native_mip_model_read_count','native_mip_mipopt_count','native_mip_freeprob_count','native_mip_close_count']:
        reject('wrong_'+k,lambda k=k:n.functional(dict(r,**{k:0}),c,phases,text))
    for name,changes in [('process_rc_error',{'returncode':1}),('hard_stop',{'stop_reason':'hard_stop'}),('out_of_cap',{'within_cap':False})]:
        reject(name,lambda changes=changes:n.functional(r,dict(c,**changes),phases,text))
    reject('missing_final_log',lambda:n.functional(r,c,phases,text.replace('Optimal solution found','Missing final solution')))
    reject('nonzero_final_log',lambda:n.functional(r,c,phases,text.replace('Best objective 0.000000000000e+00','Best objective 1.000000000000e-10')))
    reject('missing_serialization',lambda:n.functional(r,c,[v for v in phases if v['event']!='final_result_serialization_complete'],text))
    reject('wrong_exit_rc',lambda:n.functional(r,c,phases[:-1]+[dict(phases[-1],detail='rc=1')],text))
    reject('reversed_lifecycle',lambda:n.functional(r,c,list(reversed(phases)),text))
    call=next(v['payload'] for v in n.read(d/'observations.json') if v['payload']['kind']=='call')
    for name,changes in [('wrong_scope',{'model_scope':'local'}),('wrong_model',{'model_sha256':'0'*64}),('wrong_domain',{'full_original':0}),('false_precondition',{'native_preconditions':0})]:
        reject(name,lambda changes=changes:n.prior.scope(dict(call,**changes),c,launch['command'],launch['command'],call['model_sha256']))
    wrong=copy.deepcopy(call);wrong['settings']['Seed']=1
    reject('wrong_seed',lambda:n.prior.scope(wrong,c,launch['command'],launch['command'],call['model_sha256']))
    reject('altered_native_argv',lambda:n.prior.scope(call,c,launch['command']+['--new'],launch['command'],call['model_sha256']))
    q=n.core.evidence.instance(root,launch['panel']);_,model=n.core.model_contract(root,launch['panel'],d/'compact.lp','P-GRB')
    args=[launch['panel']['lambda'],q['w'][1:],q['D'][1:],model['objective'],model['bounds']]
    assert n.prior.floor(*args)==0
    for name,index,value in [('negative_lambda',0,-.1),('nonfinite_lambda',0,float('nan')),('negative_weight',1,[-1]),('zero_target',2,[0]),('negative_objective',3,([('G',1.)],-1.)),('negative_G_domain',4,dict(model['bounds'],G=(-1.,1.)))]:
        bad=copy.deepcopy(args);bad[index]=value;reject(name,lambda bad=bad:n.prior.floor(*bad))
    original_sha=n.sha
    paths=[root/launch['panel']['input_path'],d/'compact.lp',d/'result.json',d/'audit.json',d/'observations.json',d/'journal/event_142.json',d/'journal/event_142.commit',
        d/'native.log',d/'completion.json',d/'phases.csv',root/n.REL/'fees/main06/receipt.json',root/n.PREFIX,root/'scripts/round109_reader.py',root/'scripts/round109_prepaid_wrapper.py']
    for path in paths:
        n.sha=lambda p,path=path:'0'*64 if Path(p).resolve()==path.resolve() else original_sha(p)
        try:reject('altered_'+path.name,lambda:n.verify(root))
        finally:n.sha=original_sha
    original_read=n.read
    for name,path,change in [('near_zero_is_not_exact_zero',d/'result.json',{'native_mip_objective':1e-10}),
        ('false_raw_certificate',d/'result.json',{'strict_certified_original_problem':False}),
        ('failure_erased',d/'audit.json',{'passed':True})]:
        n.read=lambda p,path=path,change=change:dict(original_read(p),**change) if Path(p).resolve()==path.resolve() else original_read(p)
        try:reject(name,lambda:n.verify(root))
        finally:n.read=original_read
    receipt=n.read(root/n.REL/'fees/main06/receipt.json');receipt['SHA']=n.sha(root/n.REL/'fees/main06/receipt.json');coupon=proof['prepaid_coupon'];l18=identity['launches'][17]
    w.coupon_validate(coupon,receipt,l18,False,False,False)
    for name,cp,rc,la,before,used,started in [
        ('wrong_coupon_receipt',dict(coupon,original_receipt_SHA='0'*64),receipt,l18,False,False,False),
        ('wrong_coupon_ordinal',dict(coupon,ordinal=2),receipt,l18,False,False,False),
        ('wrong_coupon_argv',dict(coupon,command=l18['command']+['--altered']),receipt,l18,False,False,False),
        ('coupon_refund',dict(coupon,no_refund=False),receipt,l18,False,False,False),
        ('coupon_duplicate',coupon,receipt,l18,False,True,False),('native_already_started',coupon,receipt,l18,False,False,True),
        ('old_before_exists',coupon,receipt,l18,True,False,False),('wrong_paid_fee',coupon,dict(receipt,conservative_process_starts=3),l18,False,False,False)]:
        reject(name,lambda cp=cp,rc=rc,la=la,before=before,used=used,started=started:w.coupon_validate(cp,rc,la,before,used,started))
    def arm(t=None,interval=None):
        a=dict(arm='A',U=0.,L=0.,gap=0.,certificate=True,certificate_qualified=True,numbers_qualified=True,complete_seconds=t,cap_seconds=3600)
        if interval:a.update(complete_seconds_interval=interval,original_whole_clock_unknown=True,numerical_reader_recovery=n.SIDE.as_posix())
        return a
    pair_cases=[]
    for name,a,b,expected,severe in [('30exact_WIN',arm(70),arm(100),'WIN',False),('30inside_TIE',arm(70.001),arm(100),'TIE',False),
        ('300kink_WIN',arm(interval=[269,270]),arm(interval=[300,301]),'WIN',False),
        ('cross30_UNEVALUABLE',arm(interval=[69,71]),arm(100),'UNEVALUABLE',None),
        ('invariant_TIE',arm(interval=[80,90]),arm(100),'TIE',False),
        ('invariant_LOSS',arm(interval=[131,140]),arm(100),'LOSS',False),
        ('cross_severity_UNEVALUABLE',arm(interval=[219,221]),arm(100),'UNEVALUABLE',None),
        ('both_severe',arm(interval=[240,250]),arm(interval=[100,110]),'LOSS',True),
        ('ratio2_exact_extra120',arm(240),arm(120),'LOSS',True),
        ('ratio2_below120',arm(200),arm(100),'LOSS',False)]:
        result=ip.pair(a,b);assert result['classification']==expected and result['severe_regression']==severe,name
        if a['complete_seconds'] is None or b['complete_seconds'] is None:
            assert result['certified_time_ratio'] is None and result['time_improvement'] is None
            assert result['candidate_seconds']==a['complete_seconds'] and result['control_seconds']==b['complete_seconds']
            for ca,co in itertools.product([ip.clock(a)[0],sum(ip.clock(a))/2,ip.clock(a)[1]],[ip.clock(b)[0],sum(ip.clock(b))/2,ip.clock(b)[1]]):
                v=old.pair(dict(a,complete_seconds=ca),dict(b,complete_seconds=co))
                if expected!='UNEVALUABLE':assert v['classification']==expected and v['severe_regression']==severe
        else:assert result==old.pair(a,b)
        pair_cases.append(dict(name=name,result=result))
    for name,changes in [('unknown_unbound_clock',{'numerical_reader_recovery':None}),('negative_interval',{'complete_seconds_interval':[-1,2]}),
        ('reversed_interval',{'complete_seconds_interval':[2,1]}),('at_cap',{'complete_seconds_interval':[3599,3600]}),('clock_flag_missing',{'original_whole_clock_unknown':False})]:
        reject(name,lambda changes=changes:ip.pair(dict(arm(interval=[643,646]),**changes),arm(110)))
    proof2=n.verify(root);assert proof==proof2 and not (d/'whole_arm_receipt.json').exists() and not w.COUPON.exists()
    p=n.read(w.PLAN);assert p['total_newly_billed_starts']+p['original_budget_before']['paid_starts']==72 and p['new_driver_processes']==0
    assert p['remaining_native_numbers']==list(range(18,43)) and p['supplemental_wrapper_argv']==w.wrapper_commands()
    raw=[json.loads(line) for line in (root/n.REL/'campaign/summary.jsonl').read_text().splitlines()]
    view=n.record_view(root,raw);assert raw[16]['audit_passed'] is False and raw[16]['endpoint'] is None and all(v['audit_passed'] for v in view)
    assert view[16]['raw_audit_passed'] is False and view[16]['computed_mathematical_qualification'] is True
    assert view[16]['endpoint']==dict(U=0.,L=0.,gap=0.,certificate=True,source='own_full_domain_floor_and_exact_physical_zero',status='optimal')
    assert (root/n.PREFIX).read_bytes()==(root/n.REL/'campaign/summary.jsonl').read_bytes()
    n.write(dest/'audit.json',dict(decision='ACCEPT',source_SHA=n.sha(Path(__file__)),source_bindings=proof['current_reader_source_bindings'],sidecar_SHA=n.sha(root/n.SIDE),
        supplemental_plan_SHA=n.sha(w.PLAN),cases=cases,interval_pair_cases=pair_cases,checks=len(cases)+len(pair_cases),zero_Optimize=True,zero_native_environment=True,
        no_fabricated_return_or_exact_clock=True,all_original_fee_charges_retained=True))
    print('Fault, interval and coupon cases accepted:',len(cases)+len(pair_cases),'zero Optimize.')

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
