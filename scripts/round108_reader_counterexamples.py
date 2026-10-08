"""Finite zero-solver checks for the frozen qualification-first decision rules."""
import argparse, copy, json, sys
from pathlib import Path
import round108_decisions as d

def arm(role='F2',method='M-B',U=.2,L=.1,cert=False,t=100.):
    return dict(id=role,arm=method,U=U,L=L,gap=None if U is None or L is None else U-L,
        certificate=cert,certificate_qualified=True,numbers_qualified=U is not None and L is not None,
        complete_seconds=t,PE_SHA='same-frozen-PE',DLL_SHA='same-frozen-DLL')

def checks():
    cases=[]
    def check(name,condition):assert condition,name;cases.append(dict(name=name,passed=True))
    def rejects(name,call):
        try:call()
        except AssertionError:cases.append(dict(name=name,passed=True,rejected=True));return
        raise AssertionError(name+' failed to reject')
    p=arm(method='P-GRB');c=arm()
    check('single candidate certificate has priority over missing control bounds',d.pair(arm(cert=True),arm(method='P-GRB',U=None,L=None))['classification']=='WIN')
    q=d.pair(arm(U=None,L=None),arm(method='P-GRB',cert=True))
    check('single control certificate priority is severe LOSS',q['classification']=='LOSS' and q['severe_regression'])
    check('two uncertified with missing bounds are UNEVALUABLE',d.pair(c,arm(method='P-GRB',U=None,L=None))['classification']=='UNEVALUABLE')
    check('two certificates ignore UB last bits and use complete time',d.pair(arm(U=.2-1e-15,L=.2,cert=True,t=70),arm(method='P-GRB',U=.2,L=.2,cert=True,t=100))['classification']=='WIN')
    q=d.pair(arm(U=.25,L=.20),p)
    check('opposed material UB and gap effects stay MIXED',q['classification']=='MIXED' and not q['severe_regression'])
    check('sub-threshold differences remain TIE',d.pair(arm(U=.1999,L=.1001),p)['classification']=='TIE')
    check('zero objective has null relative gap',d.relative(arm(U=0,L=0,cert=True))==(None,'original_zero_objective_tolerance'))
    q=arm(U=.2,L=.2+1e-15)
    check('tiny negative signed gap retained and relative signed',d.relative(q)[0]<0 and q['gap']<0)
    check('negative signed gap never produces a gap percentage',d.pair(q,p)['gap_ratio'] is None)
    rejects('contradictory bounds never clipped',lambda:d.qualified_numbers(arm(U=.2,L=.2001)))
    bad=arm();bad['certificate_qualified']=False
    rejects('unresolved certificate qualification cannot be classified',lambda:d.pair(bad,p))
    arms=[arm(role=r,method=m,U=.2,L=.1) for r in ['F2','C2'] for m in ['P-GRB','ENS-C','M-B']]
    b=copy.deepcopy(arms);b[-1]['PE_SHA']='other-PE'
    rejects('cross-PE bridge cannot pass',lambda:d.bridge(b))
    # C2 percentage path succeeds; F2 numerically closed without certificates
    # must not be converted into an automatic resource admission.
    b=copy.deepcopy(arms)
    for a in b:
        if a['id']=='C2' and a['arm']=='M-B':a.update(U=.19,L=.12,gap=.07)
        if a['id']=='F2':a.update(U=.2,L=.2,gap=0.)
    check('uncertified near-zero reference gap cannot use bridge percentage',not d.bridge(b)['bridge_pass'])
    all_arms=[arm(role=r,method=m,cert=True,U=.2,L=.2,t=50. if m=='M-B' else 100.) for r in ['F2','C2','S12','B24','L48','F5','N36'] for m in ['P-GRB','ENS-C','M-B']]
    positive=d.selection(all_arms,dict(bridge_pass=True),{r:True for r in d.UNSEEN})
    check('complete eligible frozen seven-role example SELECTS',positive['stage']=='SELECT_MB_FOR_BROAD_EVALUATION')
    eligibility={r:r!='S12' for r in d.UNSEEN}
    check('seen input cannot be relabeled unseen to SELECT',d.selection(all_arms,dict(bridge_pass=True),eligibility)['stage']=='NO_NEW_UNIFORM_CANDIDATE_SELECTED')
    check('any confirmation cancellation prohibits SELECT',d.selection(all_arms,dict(bridge_pass=True),{r:True for r in d.UNSEEN},['one cancellation'])['stage']=='NO_NEW_UNIFORM_CANDIDATE_SELECTED')
    check('severe P regression makes positive selection unreachable',d.early_impossible([arm(cert=False),arm(method='P-GRB',cert=True)])['positive_selection_unreachable'])
    return dict(passed=True,cases=cases,Optimize=0,solver_processes=0,IIS=0,performance_arms_added=0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    result=checks();path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as file:json.dump(result,file,indent=2);file.write('\n')
    print(json.dumps(dict(passed=True,cases=len(result['cases']),Optimize=0)))
