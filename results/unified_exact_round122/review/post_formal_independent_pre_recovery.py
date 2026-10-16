"""Independent R122 pair/stage implementation and sealed-evidence review.

Preparation tests use invented in-memory data only. `review` is an explicit
later action and first requires every formal wrapper and producer to be sealed.
No production pair/decision function is imported or called.
"""
from pathlib import Path
from fractions import Fraction
import collections,copy,csv,datetime,hashlib,json,math,sys,time
import independent_contract_round122 as contract
import independent_qualification_round122 as raw
import independent_review_round122 as inputs

ROOT=contract.ROOT;OUT=contract.OUT;REVIEW=contract.REVIEW
METHODS=('P-GRB','ENS-C','M-B','MB-D1')
PAIRS=(('MB-D1','P-GRB'),('M-B','P-GRB'),('ENS-C','P-GRB'),('MB-D1','M-B'),('MB-D1','ENS-C'),('M-B','ENS-C'))
TOL=1e-7;ZERO=1e-12
read=inputs.read;sha=inputs.sha

class InvalidEvidence(ValueError):pass
def require(ok,message):
    if not ok:raise InvalidEvidence(message)
def real(value):return type(value) in (int,float) and math.isfinite(value)

def validate_arm(a):
    require(a.get('arm') in METHODS,'unknown method')
    require(type(a.get('certificate')) is bool,'certificate must be Boolean')
    require(type(a.get('certificate_qualified')) is bool,'certificate qualification must be Boolean')
    require(type(a.get('numbers_qualified')) is bool,'number qualification must be Boolean')
    if a['numbers_qualified']:
        require(all(real(a.get(k)) for k in ('U','L','gap')),'qualified endpoints must be finite real numbers')
        require(a['L']<=a['U']+TOL,'contradictory lower bound must not be clipped')
        require(abs(a['gap']-(a['U']-a['L']))<=1e-12,'signed gap inconsistent with endpoints')
    if a['certificate']:
        require(a['certificate_qualified'] and a['numbers_qualified'],'complete certificate needs qualified values')
        require(a['gap']<=TOL,'complete certificate has an open gap')
        require(real(a.get('complete_seconds')) and a['complete_seconds']>0,'complete certificate needs positive finite whole-producer time')
    return a

def independent_pair(candidate,control):
    """Separate implementation of the user R108 absolute-materiality rules."""
    c=validate_arm(candidate);p=validate_arm(control)
    require(c['arm']!=p['arm'],'self-comparison is not a prescribed pair')
    require(c['certificate_qualified'] and p['certificate_qualified'],'unresolved certificate qualification')
    cc,pc=c['certificate'],p['certificate']
    v=dict(candidate=c['arm'],control=p['arm'],candidate_U=c.get('U'),candidate_L=c.get('L'),
        control_U=p.get('U'),control_L=p.get('L'),candidate_gap=c.get('gap'),control_gap=p.get('gap'),
        candidate_certified=cc,control_certified=pc,candidate_seconds=c.get('complete_seconds'),control_seconds=p.get('complete_seconds'),
        severe_regression=False,UB_improvement=None,gap_improvement=None,LB_change=None,certified_time_ratio=None,
        UB_ratio=None,gap_ratio=None,percentage_gap_path_applicable=False)
    good=c['numbers_qualified'] and p['numbers_qualified']
    if good:
        v['UB_improvement']=p['U']-c['U'];v['gap_improvement']=p['gap']-c['gap'];v['LB_change']=c['L']-p['L']
        v['a_U']=max(.001,.01*abs(p['U']));v['a_gap']=max(.001,.10*abs(p['gap']))
        if abs(p['U'])>ZERO:v['UB_ratio']=c['U']/p['U']
        if p['gap']>TOL and c['gap']>=0:
            v['gap_ratio']=c['gap']/p['gap'];v['percentage_gap_path_applicable']=True
        elif c['gap']<0 or p['gap']<0:
            v['gap_ratio_null_reason']='tiny_negative_signed_gap_retained_no_percentage_division'
    if cc!=pc:
        v.update(classification='WIN' if cc else 'LOSS',basis='candidate_only_complete_certificate' if cc else 'control_only_complete_certificate',severe_regression=pc)
    elif cc:
        # Both certificates: windows of open arms are never treated as proof times.
        seconds=p['complete_seconds']-c['complete_seconds'];threshold=max(30.,.1*p['complete_seconds'])
        label='WIN' if seconds>=threshold else 'LOSS' if seconds<=-threshold else 'TIE'
        v.update(a_t=threshold,time_improvement=seconds,certified_time_ratio=c['complete_seconds']/p['complete_seconds'],
            classification=label,basis='both_complete_certificate_time',
            severe_regression=c['complete_seconds']>=2*p['complete_seconds'] and c['complete_seconds']-p['complete_seconds']>=120.)
    elif not good:v.update(classification='UNEVALUABLE',basis='both_uncertified_missing_qualified_finite_U_L')
    else:
        ub_up=v['UB_improvement']>=v['a_U'];gap_up=v['gap_improvement']>=v['a_gap']
        ub_down=-v['UB_improvement']>=v['a_U'];gap_down=-v['gap_improvement']>=v['a_gap']
        up=ub_up or gap_up;down=ub_down or gap_down
        label='MIXED' if up and down else 'WIN' if up else 'LOSS' if down else 'TIE'
        severe=(c['U']-p['U']>=max(.001,.05*abs(p['U'])) and c['gap']-p['gap']>=max(.005,.25*abs(p['gap'])))
        v.update(classification=label,basis='both_uncertified_absolute_materiality',material_UB_improvement=ub_up,
            material_gap_improvement=gap_up,material_UB_worsening=ub_down,material_gap_worsening=gap_down,severe_regression=severe)
    v['evaluable']=v['classification']!='UNEVALUABLE'
    return v

def independent_stage(groups,new_identity_valid=True,proof_risk=False,blockers=()):
    """Separate implementation of all five prioritized user exits."""
    blocked=list(blockers)
    if not new_identity_valid:blocked.append('necessary_source_or_input_identity_invalid')
    numbers=[g['group']['number'] for g in groups]
    complete=len(groups)==8 and set(numbers)==set(range(1,9)) and len(set(numbers))==8
    arms=[a for g in groups for a in g['arms']];pairs=[p for g in groups for p in g['pairs']]
    complete=complete and len(arms)==32 and len(pairs)==48
    for g in groups:
        labels=[a['arm'] for a in g['arms']];directions=[(p['candidate'],p['control']) for p in g['pairs']]
        complete=complete and len(labels)==4 and set(labels)==set(METHODS) and len(set(labels))==4
        complete=complete and len(directions)==6 and set(directions)==set(PAIRS) and len(set(directions))==6
    complete=complete and all(a.get('formal_protocol_qualified') is True and a.get('actually_executed') is True for a in arms)
    fresh=[g for g in groups if g['group']['number'] in range(1,7)];repeats=[g for g in groups if g['group']['number'] in (7,8)]
    def primary(g):return next((p for p in g['pairs'] if (p['candidate'],p['control'])==('MB-D1','P-GRB')),None)
    primary_new=[primary(g) for g in fresh];primary_seed=[primary(g) for g in repeats]
    primary_all=[primary(g) for g in groups];primary_new=[p for p in primary_new if p];primary_seed=[p for p in primary_seed if p]
    seen=[];gain=[];large=[]
    for g in fresh:
        entries=[e for e in g['mechanism'] if e['arm']=='MB-D1'];e=entries[0] if len(entries)==1 else {}
        exposure=e.get('installed',0)>0 and e.get('actual_extended_Optimize',0)>0
        by={a['arm']:a for a in g['arms']}
        comparison=next((p for p in g['pairs'] if (p['candidate'],p['control'])==('MB-D1','M-B')),None)
        new_certificate=by.get('MB-D1',{}).get('certificate',False) and not by.get('M-B',{}).get('certificate',False)
        seen.append(exposure);gain.append(exposure and (new_certificate or comparison is not None and comparison['classification']=='WIN'))
        large.append(exposure and g['group']['V'] in (35,50))
    d1=sum(a['certificate'] for g in fresh for a in g['arms'] if a['arm']=='MB-D1')
    mb=sum(a['certificate'] for g in fresh for a in g['arms'] if a['arm']=='M-B')
    conditions=dict(six_once_only_new_inputs=bool(new_identity_valid) and len(fresh)==6,
        six_new_D1_P_evaluable=len(primary_new)==6 and all(p['evaluable'] for p in primary_new),
        at_least_four_new_WIN_at_most_one_LOSS=sum(p['classification']=='WIN' for p in primary_new)>=4 and sum(p['classification']=='LOSS' for p in primary_new)<=1,
        at_least_three_new_D1_exposures=sum(seen)>=3,at_least_one_V35_or_V50_exposure=any(large),
        at_least_two_exposed_material_M_B_gains_or_new_certificates=sum(gain)>=2,new_certificate_count_preserved=d1>=mb,
        both_Seed1_primary_evaluable_and_nonLOSS=len(primary_seed)==2 and all(p['evaluable'] and p['classification']!='LOSS' and not p['severe_regression'] for p in primary_seed),
        no_unresolved_proof_reliability_risk=not proof_risk)
    veto=dict(any_eight_primary_severe=any(p and p['severe_regression'] for p in primary_all),
        at_least_two_new_primary_LOSS=sum(p['classification']=='LOSS' for p in primary_new)>=2)
    if proof_risk:stage='PROOF_RELIABILITY_PRIORITY'
    elif blocked or not complete:stage='BLOCKED'
    elif veto['any_eight_primary_severe'] or veto['at_least_two_new_primary_LOSS']:stage='DO_NOT_SELECT_D1_AS_PAPER_PRIMARY'
    elif all(conditions.values()):stage='FREEZE_D1_AS_PAPER_BENCHMARK_CANDIDATE'
    else:stage='BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION'
    return dict(execution_stage='COMPLETE' if complete and not blocked else 'BLOCKED',stage=stage,conditions=conditions,veto=veto,
        formal_arms=len(arms),formal_pairs=len(pairs),formal_arm_denominator=32,formal_pair_denominator=48,new_problem_denominator=6,
        fixed_input_Seed1_blocks=2,new_certificate_counts=dict(D1=d1,M_B=mb),new_D1_exposed=sum(seen),new_exposed_M_B_gains=sum(gain),
        blockers=blocked,default_ENS_changed=False,D0_not_promoted=True,MB_PC_stopped=True,no_automatic_further_batch=True,statistical_significance_claim=False)

def editorial_arm(a,g):
    # Derive current-panel labels without importing the reporting implementation.
    r=dict(a);r.update(legacy_panel_formal_flag=a.get('formal_performance'),formal_performance=True,
        seed=g['seed'],group_number=g['number'],source=g['source'],panel_kind=g['panel_kind'])
    r['nonzero_numerical_certificate']=bool(a['certificate'] and not a['own_exact_zero'] and not a['source_reduced'] and a['native_proof_qualified'])
    r['independent_zero_certificate']=bool(a['certificate'] and a['own_exact_zero'])
    r['reliable_open_bound']=bool(not a['certificate'] and a['numbers_qualified'] and not a['source_reduced'])
    r['source_reduced_result']=bool(a['source_reduced'])
    return r

def normalize(value,roots):
    if isinstance(value,dict):return {k:normalize(v,roots) for k,v in value.items()}
    if isinstance(value,list):return [normalize(v,roots) for v in value]
    if isinstance(value,str):
        for root in roots:
            prefix=str(root)
            for form in (prefix,prefix.replace('\\','/'),prefix.replace('/','\\')):
                if value==form or value.startswith(form+'/') or value.startswith(form+'\\'):
                    return '<ROOT>'+value[len(form):].replace('\\','/')
    return value

def typed_equal(a,b,path=''):
    require(type(a) is type(b),'JSON type mismatch '+path)
    if isinstance(a,dict):
        require(a.keys()==b.keys(),'JSON keys mismatch '+path)
        for k in a:typed_equal(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        require(len(a)==len(b),'JSON array length mismatch '+path)
        for i,(x,y) in enumerate(zip(a,b)):typed_equal(x,y,path+'/'+str(i))
    else:
        require(a==b,'JSON value mismatch '+path)
        if isinstance(a,float) and a==0:require(math.copysign(1.,a)==math.copysign(1.,b),'signed zero changed '+path)

def memory_tests():
    cases=[]
    def arm(method='P-GRB',U=10.,L=8.,cert=False,seconds=100.,**kw):
        return dict(arm=method,U=U,L=L,gap=U-L,certificate=cert,certificate_qualified=True,numbers_qualified=True,complete_seconds=seconds,**kw)
    p=arm();c=arm('MB-D1')
    tests=[('open_tie',arm('MB-D1'),p,'TIE',False),('open_WIN',arm('MB-D1',9.,8.),p,'WIN',False),
        ('open_LOSS',arm('MB-D1',10.2,8.),p,'LOSS',False),('open_MIXED',arm('MB-D1',9.8,7.),p,'MIXED',False),
        ('open_two_component_severe',arm('MB-D1',10.5,8.),p,'LOSS',True),
        ('open_UB_loss_alone_not_severe',arm('MB-D1',10.5,8.5),p,'LOSS',False),
        ('candidate_certificate_priority',arm('MB-D1',.1,.1,True),p,'WIN',False),
        ('control_certificate_priority',c,arm(U=.1,L=.1,cert=True),'LOSS',True),
        ('cert_time_WIN',arm('MB-D1',.1,.1,True,70.),arm(U=.1,L=.1,cert=True,seconds=100.),'WIN',False),
        ('cert_time_TIE',arm('MB-D1',.1,.1,True,71.),arm(U=.1,L=.1,cert=True,seconds=100.),'TIE',False),
        ('cert_time_severe',arm('MB-D1',.1,.1,True,240.),arm(U=.1,L=.1,cert=True,seconds=120.),'LOSS',True)]
    for name,c,p,expected,severe in tests:
        r=independent_pair(c,p);require(r['classification']==expected and r['severe_regression']==severe,name);cases.append(name)
    c=arm('MB-D1');c.update(U=None,L=None,gap=None,numbers_qualified=False)
    require(independent_pair(c,arm())['classification']=='UNEVALUABLE','missing values');cases.append('open_missing_values_UNEVALUABLE')
    c=arm('MB-D1',0.,0.,True);p=arm(U=0.,L=0.,cert=True)
    r=independent_pair(c,p);require(r['UB_ratio'] is None and r['gap_ratio'] is None,'zero ratios');cases.append('zero_certificate_no_percentage_division')
    c=arm('MB-D1',1.,math.nextafter(1.,math.inf),True);r=independent_pair(c,arm(U=1.,L=1.,cert=True))
    require(r['candidate_gap']<0 and r['gap_ratio'] is None,'tiny signed gap preserved');cases.append('tiny_negative_gap_preserved')
    invalid=[dict(arm('MB-D1'),U=float('nan')),dict(arm('MB-D1'),U=True),dict(arm('MB-D1'),gap=.1),
        dict(arm('MB-D1'),L=11.,gap=-1.),dict(arm('MB-D1'),certificate_qualified=False),
        dict(arm('MB-D1',1.,1.,True),complete_seconds=0.),dict(arm('MB-D1'),certificate=1)]
    for j,a in enumerate(invalid):
        try:independent_pair(a,arm())
        except InvalidEvidence:cases.append('invalid_pair_input_rejected_'+str(j))
        else:raise AssertionError(('invalid evidence accepted',j))
    values=[]
    for n in range(1,9):
        values.append(dict(group=dict(number=n,V=20 if n<3 else 35 if n in (3,4,7) else 50),
            arms=[arm(a,formal_protocol_qualified=True,actually_executed=True) for a in METHODS],
            pairs=[dict(candidate=a,control=b,evaluable=True,classification='WIN' if a=='MB-D1' else 'TIE',severe_regression=False) for a,b in PAIRS],
            mechanism=[dict(arm='MB-D1',installed=1,actual_extended_Optimize=1)]))
    def stage_case(name,v,expected,**kw):
        require(independent_stage(v,**kw)['stage']==expected,name);cases.append(name)
    stage_case('positive_all_literal_conditions',values,'FREEZE_D1_AS_PAPER_BENCHMARK_CANDIDATE')
    stage_case('source_error_priority_over_missing_groups',values[:-1],'PROOF_RELIABILITY_PRIORITY',proof_risk=True)
    stage_case('invalid_input_BLOCKED',values,'BLOCKED',new_identity_valid=False)
    stage_case('missing_group_BLOCKED',values[:-1],'BLOCKED')
    v=copy.deepcopy(values);v[1]['group']['number']=1;stage_case('duplicate_group_BLOCKED',v,'BLOCKED')
    v=copy.deepcopy(values);v[0]['arms'][1]=v[0]['arms'][0];stage_case('duplicate_method_BLOCKED',v,'BLOCKED')
    v=copy.deepcopy(values);v[0]['pairs'][1]=v[0]['pairs'][0];stage_case('duplicate_pair_BLOCKED',v,'BLOCKED')
    v=copy.deepcopy(values)
    for g in v[:2]:g['pairs'][0]['classification']='LOSS'
    stage_case('two_new_LOSS_veto',v,'DO_NOT_SELECT_D1_AS_PAPER_PRIMARY')
    v=copy.deepcopy(values);v[7]['pairs'][0]['severe_regression']=True;stage_case('Seed1_severe_veto',v,'DO_NOT_SELECT_D1_AS_PAPER_PRIMARY')
    v=copy.deepcopy(values)
    for g in v:g['mechanism'][0]['installed']=0
    stage_case('no_exposure_is_complete_MIXED',v,'BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION')
    v=copy.deepcopy(values);v[6]['pairs'][0]['classification']='LOSS';stage_case('one_Seed1_LOSS_prevents_positive',v,'BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION')
    require(normalize('E:/ROOT/file',['E:/ROOT'])=='<ROOT>/file','root prefix normalization')
    require(normalize('E:/ROOT-other/file',['E:/ROOT'])=='E:/ROOT-other/file','component boundary normalization')
    typed_equal(normalize({'x':'E:\\ROOT\\a','n':-0.},['E:/ROOT']),{'x':'<ROOT>/a','n':-0.})
    for a,b in [(0.,-0.),(1,1.),({'a':1},{'a':1,'b':2}),([1,2],[2,1])]:
        try:typed_equal(a,b)
        except InvalidEvidence:pass
        else:raise AssertionError('typed equality normalized meaningful data')
    cases.append('path_only_typed_signed_zero_validation')
    labelled=editorial_arm(dict(certificate=True,own_exact_zero=True,source_reduced=True,native_proof_qualified=False,numbers_qualified=True,formal_performance=False),
        dict(seed=0,number=1,source='CITI',panel_kind='new_problem_Seed0'))
    require(labelled['independent_zero_certificate'] and labelled['source_reduced_result'] and not labelled['nonzero_numerical_certificate'],
        'independent zero and source reduction may overlap')
    cases.append('proof_columns_preserve_zero_source_reduced_overlap')
    return dict(decision='PENDING',scope='Independent post-formal implementation prepared and finite in-memory tests executed; no formal raw read.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_SHA=sha(__file__),
        cases=cases,test_count=len(cases),independent_pair_and_stage=True,production_pair_or_decide_called=False,
        actual_formal_review='PENDING_REQUIRED_ALL_EIGHT_SEALED_GROUPS_AND_REPORTS',native_starts=0,Optimize=0,formal_raw_read=False,
        source_normalization='Complete root component prefixes only; typed JSON, arrays, float values and signed zero retained.',seconds=0.)

def required_sealed():
    """Metadata-only gate executed only on the parent's explicit later request."""
    missing=[]
    for n in range(1,9):
        fee=OUT/'fees'/f'formal{n:02d}'/'receipt.json'
        if not fee.exists():missing.append(str(fee));continue
        r=read(fee)
        if r['exit_code']!=0 or not r['actual_exit_observed']:missing.append(str(fee)+' not successful/closed')
        core=OUT/f'reconstruction/group{n:02d}/current_core.json'
        if not core.exists():missing.append(str(core))
    for name in ['all32_arms.json','all48_pairs.json','stage_decision.json','major_negative_results.json','mechanism_account.json','resource_summary.json','proof_reliability.json']:
        if not (OUT/name).exists():missing.append(str(OUT/name))
    require(not missing,'Actual post-formal review remains PENDING: '+repr(missing))

def clocks_and_seals(l,endpoint):
    d=Path(l['destination']);p=l['panel'];a=raw.instance(p)
    producer=raw.rd(d/'producer_receipt.json');seal=raw.rd(d/'producer_seal.json');total=raw.rd(d/'arm_total_receipt.json')
    require(producer['producer_seal_SHA']==sha(d/'producer_seal.json'),'producer seal identity')
    for name,h in seal['required_SHA'].items():require(sha(d/name)==h,'sealed producer changed '+name);raw.USED[str(d/name)]=h
    require(producer['T_produce']==producer['t_produce_perf']-producer['t0_perf'],'producer clock arithmetic')
    require(total['T_verify']==total['t_verified_perf']-producer['t_produce_perf'],'verification clock arithmetic')
    require(total['T_total']==total['t_verified_perf']-producer['t0_perf'],'total clock arithmetic')
    require(abs(total['T_total']-producer['T_produce']-total['T_verify'])<1e-8,'three clocks identity')
    require(producer['T_produce']<=l['cap_seconds'],'producer exceeded fixed cap')
    for key in ('T_produce','T_verify','T_total'):
        actual=producer[key] if key=='T_produce' else total[key];require(endpoint[key]==actual,'endpoint clock changed')
    completion=raw.rd(d/'completion.json');audit=raw.rd(d/'audit.json');close=raw.rd(d/'verification_closeout.json')
    require(completion['returncode']==0 and completion['stop_reason']=='normal_return' and completion['within_cap'],'normal complete producer return')
    require(audit['passed'] or audit.get('claim_rejection_recorded') and audit.get('independent_evidence_audit_passed'),'necessary audit result')
    require(total['verification_closeout_SHA']==sha(d/'verification_closeout.json') and close['audit_SHA']==sha(d/'audit.json'),'verification closeout binding')
    require(total['producer_receipt_SHA']==close['producer_receipt_SHA']==sha(d/'producer_receipt.json'),'producer identity in verification')
    saved=raw.rd(d/'launch.json');birth=raw.rd(d/'child_process_origin.json')
    require(saved['command']==birth['command']==l['command'] and saved['panel']==p,'actual argv/panel binding')
    require(birth['seed']==l['seed'] and birth['PE_SHA']==contract.PE_SHA and birth['creation_from_live_OS_handle'],'actual birth/Seed/PE')
    owner=raw.rd(OUT/'fees'/f"formal{l['group_number']:02d}"/'receipt.json')
    require(birth['parent_pid']==owner['wrapper_pid'],'actual child belongs to closed group wrapper')
    affinity=raw.rd(d/'affinity.json')
    require(affinity['pid']==birth['pid'] and affinity['child']['process_mask']==4,'actual frozen child affinity')
    result=raw.rd(d/'result.json');physical=raw.physical(p,a,result)
    require(abs(physical['F']-endpoint['U'])<=TOL,'independent whole fleet objective')
    require(len(physical['fleet'])==p['M'],'missing assigned vehicle in independent complete fleet')
    observations=raw.rd(d/'observations.json');view=raw.rd(d/'call_log_views.json')
    calls={q['payload']['call']:q['payload'] for q in observations if q['payload']['kind']=='call'}
    require(len(calls)==sum(q['payload']['kind']=='call' for q in observations),'duplicate native call identity')
    returned={q['payload']['call'] for q in observations if q['payload']['kind']=='returned'}
    skipped={q['payload']['call'] for q in observations if q['payload']['kind']=='not_started'}
    require(not returned&skipped and returned|skipped<=set(calls),'conflicting native dispositions')
    actual={b['call'] for b in view['bindings']}
    require(actual==set(calls)-skipped and view['actual_Optimize']==len(actual),'call-scoped actual/not_started accounting')
    expected=dict(read_return_code=0,Threads=1,Seed=l['seed'],Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    scopes=[];model_hashes={}
    for cid,c in calls.items():
        require(c['settings']==expected,'actual native parameter readback')
        if l['seed']==1:require(not c['native_preconditions'],'Seed1 raw prerequisite flag was promoted')
        require(0<=c['lower_g']<=c['upper_g']<=(p['V']-1)/p['V']+TOL,'invalid actual call domain')
        require(real(c['cutoff']) and c['cutoff']>=0,'invalid actual cutoff')
        path=raw.portable(c['model_path'])
        if str(path) not in model_hashes:model_hashes[str(path)]=sha(path);raw.USED[str(path)]=model_hashes[str(path)]
        require(model_hashes[str(path)]==c['model_sha256'],'declared call model hash')
        scopes.append(dict(call=cid,model_SHA=c['model_sha256'],leaf=c['leaf'],lower_g=c['lower_g'],upper_g=c['upper_g'],cutoff=c['cutoff'],
            returned=cid in returned,explicit_not_started=cid in skipped))
    for q in observations:
        e=q['payload']
        if e['kind']=='returned':require(e['return_code']==0,'returned native API code')
        if e['kind']=='not_started':require(e['actual_Optimize'] is False and e['reason']=='no_remaining_original_work_window','explicit native not_started disposition')
        if e['kind']=='bound' and l['seed']==1:
            require(not e['global_available'] and e['global_bound'] is None,'Seed1 raw callback availability was promoted')
    if l['arm']=='P-GRB':
        require(actual==returned=={1} and not skipped,'cold baseline must have its own single actual returned Optimize')
        require(calls[1]['full_original'] and calls[1]['model_sha256']==p['reference']['canonical_sha256'],'cold full original model authority')
        require(result['gurobi_hga_start_requested'] is False,'cold baseline received a heuristic Start')
    elif not actual:
        require(endpoint['certificate'] and endpoint['own_exact_zero'] and abs(physical['F'])<=ZERO,'zero-call closure needs own verified physical zero')
        require(p['lambda']>=0 and all(w>=0 for w in a['weights'][1:]),'zero-call independent global nonnegative floor')
    if l['seed']==1:
        seed_file=d/'computed_seed_scope.json'
        if seed_file.exists():
            projected=raw.rd(seed_file)
            require(projected['actual_seed']==1 and projected['raw_flags_preserved'],'computed Seed1 proof did not preserve raw facts')
    for b in view['bindings']:
        c=calls[b['call']];data=raw.checked_bytes(ROOT/b['raw_log'])
        require(hashlib.sha256(data).hexdigest()==b['raw_log_SHA'],'sealed raw log identity')
        segment=data[b['byte_begin']:b['byte_end']]
        require(hashlib.sha256(segment).hexdigest()==b['segment_SHA'],'native log segment identity')
        require(segment.count(b'Optimize a model with ')==1,'one complete model per bound log view')
        require(b['model_SHA']==c['model_sha256'] and b['true_G_interval']==[c['lower_g'],c['upper_g']] and b['cutoff']==c['cutoff'],'call/model/scope/cutoff log binding')
        if b['call'] not in returned:
            require(b['missing_return_requires_unchanged_narrow_gate'] and audit.get('independent_evidence_audit_passed'),'missing return requires preserved narrow gate')
    event=raw.rd(d/'round120_extended_verification.json')['event_contract']
    if l['arm']=='MB-D1':
        require(event['enabled'] and event['installed'] in (0,1),'D1 flag/one-install contract')
        if event['installed']:
            require(event.get('actual_extended_Optimize',0)>0,'installed D1 lacks actual extended search')
            pair=raw.rd(d/'external/round120_root_pair.json');require(pair['input_SHA']==p['input_sha256'],'own D1 root proof input')
            for proof in pair['proofs']:
                require(proof['call'] in returned and proof['model']==calls[proof['call']]['model_sha256'],'D1 proof depends on own successful paid call')
        else:
            require(event.get('actual_extended_Optimize',0)==0,'uninstalled D1 has extended search')
    else:require(not event['enabled'] and event['installed']==0,'non-D1 arm has D1 installation')
    return dict(group=l['group_number'],id=l['id'],arm=l['arm'],seed=l['seed'],birth=birth,
        producer_receipt_SHA=sha(d/'producer_receipt.json'),seal_SHA=sha(d/'producer_seal.json'),audit_SHA=sha(d/'audit.json'),
        T_produce=producer['T_produce'],T_verify=total['T_verify'],T_total=total['T_total'],
        G=physical['G'],lambda_P=p['lambda']*physical['P'],F=physical['F'],fleet=physical['fleet'],
        certificate=endpoint['certificate'],proof_evidence=endpoint['proof_evidence'],source_reduced=endpoint['source_reduced'],
        call_scopes=scopes,explicit_not_started_count=len(skipped),missing_return_ids=sorted(actual-returned),
        D1_enabled=event['enabled'],D1_installed=event['installed'],D1_extended_Optimize=event.get('actual_extended_Optimize',0)),a

def actual_d1_model_review(l,a):
    """All call scopes/Starts in one actually exposed D1 arm, bounded parse cache."""
    d=Path(l['destination']);p=l['panel'];observations=raw.rd(d/'observations.json');view=raw.rd(d/'call_log_views.json')
    calls={r['payload']['call']:r['payload'] for r in observations if r['payload']['kind']=='call'}
    pair=raw.rd(d/'external/round120_root_pair.json')
    require(pair['input_SHA']==p['input_sha256'],'own actual D1 proof input')
    for j,proof in enumerate(pair['proofs']):
        expected=max(0.,math.nextafter(min(proof['bound'],proof['cutoff'])-TOL,-math.inf))
        require(pair['beta'+str(j)]==expected,'actual conservative beta')
    models=collections.OrderedDict();facts=[];starts=[]
    for binding in view['bindings']:
        c=calls[binding['call']];path=raw.portable(c['model_path']);require(sha(path)==c['model_sha256'],'actual D1 model bytes')
        model=models.pop(c['model_sha256'],None)
        if model is None:model=raw.model_check(p,a,path,c,'MB-D1')
        models[c['model_sha256']]=model
        if len(models)>2:models.popitem(last=False)
        if binding['solve_kind']=='LP':continue
        log=raw.portable(c['native_log_path']);start=raw.start_check(model,log,p,a,d)
        require(start is not None,'actual D1 MIP Start absent');starts.append(start)
        native=raw.rd(Path(str(log)+'.round120.native.json'))
        require(native['model_SHA']==c['model_sha256'] and native['h_type']=='B' and native['h_BranchPriority']==0,'actual D1 h type/identity/priority')
        require(model[2]['r120_h']=='B' and model[1]['r120_h']==(0.,1.),'saved D1 binary selector')
        receipt=raw.rd(Path(str(path)+'.round120.json'))
        base=path.with_name(path.name.replace('_round120_d1',''))
        require(sha(base)==receipt['base_SHA'],'D1 frozen original base identity');raw.USED[str(base)]=sha(base)
        baseline=contract.lp_reference(base)
        require(model[4]==baseline[4] and model[3][:-3]==baseline[3],'D1 preserves full objective and every preceding row')
        require({k:v for k,v in model[1].items() if k!='r120_h'}==baseline[1],'D1 preserves every original bound')
        require({k:v for k,v in model[2].items() if k!='r120_h'}==baseline[2],'D1 preserves every original type')
        objective=dict(model[4][0]);objective['r120_h']=-native['objective_delta']
        objective={k:v for k,v in objective.items() if v}
        expected_rows=[({'G':1.,'r120_h':-native['lower_delta']},'>=',native['lower_base']),
            ({'G':1.,'r120_h':-native['upper_delta']},'<=',native['upper_base']),
            (objective,'>=',native['objective_base'])]
        cleaned=lambda row:({k:v for k,v in row[0].items() if v},row[1],row[2])
        require([cleaned(row) for row in model[3][-3:]]==[cleaned(row) for row in expected_rows],'actual complete D1 three-row coefficients')
        q=lambda x:Fraction.from_float(float(x))
        require(q(native['lower_base'])<=q(pair['a']) and q(native['lower_base'])+q(native['lower_delta'])<=q(pair['m']),'outward G lower endpoint')
        require(q(native['upper_base'])>=q(pair['m']) and q(native['upper_base'])+q(native['upper_delta'])>=q(pair['b']),'outward G upper endpoint')
        require(q(native['objective_base'])+q(native['objective_constant'])<=q(pair['beta0']),'outward h=0 ObjCon endpoint')
        require(q(native['objective_base'])+q(native['objective_delta'])+q(native['objective_constant'])<=q(pair['beta1']),'outward h=1 ObjCon endpoint')
        facts.append(dict(call=c['call'],leaf=c['leaf'],model_SHA=c['model_sha256'],rows=len(model[3]),columns=len(model[0]),
            lower_g=c['lower_g'],upper_g=c['upper_g'],cutoff=c['cutoff'],native_audit_SHA=sha(Path(str(log)+'.round120.native.json'))))
    require(facts and starts,'no actually extended D1 native model in selected role')
    return dict(group=l['group_number'],id=l['id'],seed=l['seed'],V=p['V'],native_models=facts,all_actual_Starts=starts,
        physical_models_types_A_B_scope_and_complete_Start_vectors_independently_recomputed=True)

def review():
    tick=time.perf_counter();required_sealed();candidate,binding=contract.frozen_bindings()
    require(read(REVIEW/'pre_contract.json')['candidate_identity_SHA']==sha(OUT/'candidate_identity.json'),'pre-formal candidate identity')
    inputs.input_review();manifest=read(OUT/'input_manifest.json');argv=read(OUT/'argv_freeze.json')
    groups=[];independent_pairs=[];all_arms=[];fleets=[];exposed_launches=[];proof_risk=False;blockers=[];births=set()
    for n in range(1,9):
        v=raw.rd(OUT/f'reconstruction/group{n:02d}/current_core.json');g=v['group'];p=manifest['roles'][n-1]
        require(g==argv['groups'][n-1] and g['number']==n,'exact preregistered group')
        require(g['id']==p['id'] and g['seed']==p['gurobi_seed'] and g['source']==p['source'],'source/input/Seed identity')
        require(g['methods']==inputs.ORDERS[n-1],'method order')
        identity=raw.rd(OUT/g['campaign']/'identity.json')
        require(identity['helpers']==candidate['helpers'] and identity['source_hashes']==candidate['source_bindings'],'frozen helper/source identity')
        require(sha(OUT/g['campaign']/'identity.json')==candidate['campaign_identities'][g['campaign']],'campaign identity digest')
        require([l['arm'] for l in identity['launches']]==g['methods'],'exact four argv positions')
        by={a['arm']:a for a in v['arms']};require(set(by)==set(METHODS) and len(v['arms'])==4,'exact four observed methods')
        for l in identity['launches']:
            endpoint=validate_arm(by[l['arm']]);fact,a=clocks_and_seals(l,endpoint);fleets.append(fact)
            key=(fact['birth']['pid'],fact['birth']['actual_creation_unix']);require(key not in births,'reused OS child identity');births.add(key)
            if not endpoint['formal_protocol_qualified'] or not endpoint['numbers_qualified']:blockers.append(dict(group=n,arm=l['arm'],reason='unqualified necessary protocol/numbers'))
            all_arms.append(editorial_arm(endpoint,g))
            event=next(e for e in v['mechanism'] if e['arm']==l['arm'])
            if l['arm']=='MB-D1' and event.get('installed',0)>0 and event.get('actual_extended_Optimize',0)>0:exposed_launches.append((l,a))
        pairs=[]
        for c,p0 in PAIRS:
            result=independent_pair(by[c],by[p0]);dU=by[c]['U']-by[p0]['U'];dL=by[c]['L']-by[p0]['L'];dgap=by[c]['gap']-by[p0]['gap']
            require(abs(dgap-dU+dL)<=1e-12,'endpoint decomposition')
            record=dict(id=g['id'],group_number=n,seed=g['seed'],**result,dU=dU,dL=dL,dgap=dgap,identity_dgap_equals_dU_minus_dL=True,causal_shares=False)
            pairs.append(record);independent_pairs.append(record)
        typed_equal(pairs,v['pairs'])
        proof_risk=proof_risk or bool(v['adjudication']['rejections'])
        groups.append(dict(group=g,arms=v['arms'],pairs=pairs,mechanism=v['mechanism']))
    require(len(births)==len(fleets)==32,'exact 32 actual native producers')
    typed_equal(independent_pairs,raw.rd(OUT/'all48_pairs.json'))
    typed_equal(normalize(all_arms,[ROOT]),normalize(raw.rd(OUT/'all32_arms.json'),[ROOT]))
    decision=independent_stage(groups,new_identity_valid=True,proof_risk=proof_risk,blockers=blockers)
    typed_equal(decision,raw.rd(OUT/'stage_decision.json'))
    V50=[f for f in fleets if next(p for p in manifest['new_roles'] if p['id']==f['id'])['V']==50]
    require(V50 and all(len(f['fleet'])==4 for f in V50),'complete V50 fleet')
    selected_V50=next((f for f in V50 if f['arm']=='MB-D1'),V50[0])
    if exposed_launches:
        selected=next(((l,a) for l,a in exposed_launches if l['panel']['V']==50),exposed_launches[0])
        actual_model=actual_d1_model_review(*selected)
    else:
        # Exposure is an observed scientific outcome, never an engineering gate.
        # Preserve the complete no-exposure panel and use already-paid actual
        # qualification only to check the D1 wiring, without a new Optimize.
        known=raw.rd(OUT/'qualification/h100_seed1/identity.json')
        l=next(l for l in known['launches'] if l['arm']=='MB-D1')
        actual_model=actual_d1_model_review(l,raw.instance(l['panel']))
        actual_model.update(scope='actual known-fixture qualification only; no formal D1 extended model existed',
            formal_D1_actual_exposure_count=0,formal_nonexposure_is_not_an_engineering_blocker=True)
    negatives=[p for p in independent_pairs if p['classification'] in ('LOSS','MIXED','UNEVALUABLE') or p['severe_regression']]
    saved_negative=raw.rd(OUT/'major_negative_results.json');typed_equal(negatives,saved_negative['all_negative_or_mixed_pairs'])
    major=[];byfleet={(f['group'],f['arm']):f for f in fleets}
    for p in negatives:
        c,t=[byfleet[p['group_number'],p[k]] for k in ('candidate','control')]
        major.append(dict(group=p['group_number'],id=p['id'],seed=p['seed'],pair=[p['candidate'],p['control']],classification=p['classification'],
            severe=p['severe_regression'],basis=p['basis'],dU=p['dU'],dL=p['dL'],dgap=p['dgap'],dG=c['G']-t['G'],
            d_lambda_P=c['lambda_P']-t['lambda_P'],candidate_proof=c['proof_evidence'],control_proof=t['proof_evidence']))
    fees=[];controllers=set()
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        r=raw.rd(path.parent/'receipt.json');require(r['actual_exit_observed'],'all fee exits actually closed');fees.append((raw.rd(path),r))
    for path in sorted((OUT/'controller').glob('*/launch.json')):
        r=raw.rd(path);controllers.add((r['controller_pid'],r['controller_actual_creation_unix']))
    paid=sum(r['outer_seconds_upper'] for l,r in fees);qual=sum(r['outer_seconds_upper'] for l,r in fees if l['qualification'])
    require(paid<=100000 and qual<=6000,'authorized outer resource ceiling')
    resource=raw.rd(OUT/'resource_summary.json')
    require(resource['paid_outer_seconds']==paid and resource['qualification_seconds']==qual,'reported outer fee sum')
    require(resource['total_observed_or_conservative_starts']==sum(r['conservative_process_starts'] for l,r in fees)+len(controllers),'startup ledger total')
    require(not any(r['nested_native_seconds_added'] for l,r in fees),'native components charged twice')
    contract.frozen_bindings()
    require(all(sha(Path(path))==digest for path,digest in raw.USED.items()),'reviewed sealed evidence changed')
    result=dict(decision='ACCEPT',scope='Actual independent post-formal 32-position/48-pair/stage and bounded raw model/Start/fleet review',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_SHA=sha(__file__),
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),all32_arms_SHA=sha(OUT/'all32_arms.json'),all48_pairs_SHA=sha(OUT/'all48_pairs.json'),
        stage_decision_SHA=sha(OUT/'stage_decision.json'),independent_stage=decision,independent_pairs=independent_pairs,
        major_negative_results_review=major,complete_V50_fleet=selected_V50,actual_D1_model_Start_scope=actual_model,
        all_32_physical_objective_and_clocks=[{k:v for k,v in f.items() if k not in ('fleet','birth')} for f in fleets],
        source_and_helper_identity=binding,outer_seconds=paid,qualification_seconds=qual,additional_distinct_controllers=len(controllers),
        no_instance_or_Seed_selection=True,all_fixed_denominators_retained=True,signed_gaps_and_source_reduced_flags_retained=True,
        typed_JSON_path_only_normalization=True,native_starts=0,Optimize=0,production_pair_or_decide_called=False,
        reviewed_evidence_files=len(raw.USED),all_reviewed_bytes_unchanged=True,seconds=time.perf_counter()-tick,
        limitations=['No native LP was resolved. Numerical proof reliability uses the frozen source/PE contract and sealed call-scoped evidence; the extra model/Start/scope replay is bounded and is not a claim to independently prove every native branch.',
            'Public-carrier export/empty-root recovery and safe cleanup are separately required and are not certified by this post-formal performance review.'])
    inputs.save_receipt('post_formal_independent.json',result)
    text='\n'.join(['# Independent Round122 post-formal review','',f'**ACCEPT: {decision["stage"]}.**','',
        'A separate pair/stage implementation recomputed all 48 directed comparisons and the prioritized finite stage rule. Exact eight groups, four methods, six new Seed0 roles and two fixed Seed1 repeats were checked. All 32 physical fleets, objectives, actual child identities, producer seals, source/helper bindings and three clocks were replayed. Signed tiny gaps and source-reduced flags were preserved.','',
        f'The review explicitly examined all {len(major)} LOSS/MIXED/UNEVALUABLE or severe pairs. Their endpoint and G/weighted-penalty differences are retained as explanations, without internal causal fractions or selected-Seed replacements.','',
        'At least one complete V50 fleet and one actually exposed D1 model were independently checked, including saved p/d declarations, frozen A/B, actual G/cutoff scope, binary selector, native model identity and complete Start bounds/row/integrality/objective/readback residuals.','',
        'No native process or Optimize was launched, no measured source/helper or raw was changed, and no production pair/decision function was called. Public restore and final cleanup remain separately required.',''])
    with (REVIEW/'post_formal_independent.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)

if __name__=='__main__':
    require(len(sys.argv)==2 and sys.argv[1] in ('prepare-tests','review'),'explicit prepare-tests or later review action required')
    if sys.argv[1]=='prepare-tests':
        start=time.perf_counter();result=memory_tests();result['seconds']=time.perf_counter()-start
        name='post_formal_preparation.json';revision=1
        while (REVIEW/name).exists():
            revision+=1;name=f'post_formal_preparation{revision:02d}.json'
        if revision>1:result['prior_preparation_receipt']='post_formal_preparation.json'
        inputs.save_receipt(name,result)
    else:review()
