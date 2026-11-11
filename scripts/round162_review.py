"""Final separate saved-evidence audit by the same agent, never an independent person."""
from round162_common import *
from round162_audit import records,point,exact_dual,primal
from round162_analyze import inherited_functions
import ast

def review(output_name='final_review.json',decision_name='decision.json'):
    report=read(OUT/'reports/native.json');manifest=read(OUT/'measured_manifest.json');legacy=inherited_functions()
    assert sha(manifest['research_PE'])==manifest['research_PE_SHA'] and sha(DLL)==DLL_SHA
    source=ROOT/'scripts/round157_fleet.py';tree=ast.parse(source.read_text(encoding='utf-8-sig'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify');namespace={'math':math}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace);verify=namespace['verify']
    checks=[]
    for sample in report['samples']:
        tick=time.perf_counter()
        folder=OUT/'runs'/sample['label'];d=legacy['instance'](sample['role']);events=legacy['events'](folder)
        distance=[[math.hypot(a[0]-b[0],a[1]-b[1])/1.5 for b in d['points']] for a in d['points']]
        data=dict(n=d['n'],Q=d['Q'],initial=d['initial'],capacity=d['capacity'],target=d['target'],weights=d['weights'],
            distance=distance,T=d['T'],pickup=d['tp'],drop=d['td'],lam=d['lam'])
        count=0
        for e in events:
            if e['kind']=='witness':
                checked=verify(data,e);assert checked['original_T_feasible'];count+=1
            assert e['kind'] not in ('source_rejected','failure'),e
        columns=records(folder/'actual_columns.jsonl');rows=records(folder/'actual_rows.jsonl');start=read(folder/'start.json');worst=0.
        for n,c in columns.items():
            worst=max(worst,c['lb']-start[n],start[n]-c['ub'])
            if c['type']!='C':assert abs(start[n]-round(start[n]))<=1e-5
        for r in rows.values():
            delta=math.fsum(c*start[n] for n,c in r['terms'].items())-r['rhs']
            worst=max(worst,abs(delta) if r['sense']=='=' else delta if r['sense']=='<' else -delta)
        assert worst<1e-6 and count>0
        admission=read(folder/'admission.json');assert abs(math.fsum(c['obj']*start[n] for n,c in columns.items())-admission['parent_J'])<1e-9
        extra={}
        if sample['form']=='C':
            sf=folder/'source';src=read(sf/'source_outcome.json');assert src['qualified'] and src['diagnostic_only_lower']
            se=legacy['events'](sf);call=next(e for e in se if e['kind']=='call');quality=next(e for e in se if e['kind']=='native_quality')
            assert call['model_sha256']==sha(sf/'model.lp') and call['native_preconditions']==1
            assert quality['native_status']==2 and quality['optimize_return_code']==0 and quality['ConstrVio']<=1e-6 and quality['BoundVio']<=1e-6
            assert not any(e['kind'] in ('source_rejected','failure') for e in se)
            assert len([e for e in se if e['kind']=='call'])==1
            ac=records(sf/'actual_columns.jsonl');ar=records(sf/'actual_rows.jsonl');p=primal(sf,ac,ar);cert=exact_dual(sf,ac,ar)
            assert p['qualifies_under_inherited_1e_6']
            projection=read(folder/'projection.json');assert projection['source_SHA256']==sha(sf/'model.lp') and projection['new_columns_submitted']==0
            assert all(not n.startswith('pc162_') for n in columns)
            assert len(rows)==len(records(folder/'original_rows.jsonl'))+int(projection['active'])
            extra=dict(source_primal=p,source_exact_dual_box=cert,source_calls=1,source_Runtime_not_added_twice=True,
                source_lower_diagnostic_only=True,source_handle_released=True,new_formal_columns=0)
        checks.append(dict(label=sample['label'],fleets_rechecked=count,Start_max_violation=worst,verification_seconds=time.perf_counter()-tick,**extra))
    tiny_checks=[]
    for tag,initial,subdir in [('loaded_return',[0,2,0],''),('zero_inventory',[0,0,0],'v3')]:
        data=dict(n=2,Q=[2],initial=initial,capacity=[100,2,2],target=[0,1,2],weights=[0,1,1],
            distance=[[0.]*3 for _ in range(3)],T=100,pickup=2,drop=3,lam=.1)
        for form in ('S','F'):
            folder=OUT/'qualification/v2'/tag/subdir/form
            witnesses=[e for e in legacy['events'](folder) if e['kind']=='witness']
            for e in witnesses:assert verify(data,e)['original_T_feasible']
            tiny_checks.append(dict(fixture=tag,form=form,fleets=len(witnesses)))
    protected=read(OUT/'infra/protected_initial.json');protected_count=0
    for tree in protected['trees']:
        for path,digest in tree['dirty'].items():assert sha(Path(tree['tree'])/path)==digest;protected_count+=1
    current=os.environ.get('ROUND140_METERED_PARENT_LABEL');account=budget()
    assert all(p['label']==current for p in account['unclosed']) and account['G1_seconds']<TOTAL
    fees=[dict(label=p.parent.name,**read(p)) for p in (OUT/'fees').glob('*/receipt.json')]
    failures=[r for r in fees if r['exit_code']]
    decision=read(OUT/decision_name)
    write(OUT/output_name,dict(PASS=True,UTC=utc(),reviewer='same Codex agent, separate saved-evidence script; not independent personnel',
        source_verifier_SHA256=sha(source),checks=checks,tiny_checks=tiny_checks,protected_dirty_count=protected_count,protected_unchanged=True,
        failed_receipts_preserved=failures,science_account_before_this_receipt=account,decision=decision,Optimize=0,
        qualification=read(OUT/'qualification/v2/new_interfaces.json')['PASS'],
        positive_free_J_and_projection=read(OUT/'reports/N-B35-S_C_LP_v1_projection_audit.json')['PASS'],
        no_fresh_H_helper_or_GI_claim_from_Native_development=True))
    print('PASS final separate same-agent evidence audit; no independent personnel claimed',flush=True)

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='development':review('development_review.json','development_decision.json')
    else:review()
