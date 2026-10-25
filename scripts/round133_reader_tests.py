"""Controlled journal lifecycle/transport faults; never a native experiment."""
from round133_common import *
import copy
from round133_read import validate_event_lifecycle, strict_global_bound, quality_predicate, independent_source_checks, validate_abandoned_control
from round86_native_evidence import receipt

def sequence(events):
    return [dict(schema=1,sequence=index+1,**event) for index,event in enumerate(events)]

def main():
    parent=OUT/'qualification/reader_faults';parent.mkdir(parents=True,exist_ok=True)
    folder=parent/f'attempt_{len(list(parent.glob("attempt_*")))+1:02d}'
    folder.mkdir(exist_ok=False)
    records=[]
    identity=dict(kind='identity',certificate='none_source_qualification_round133')
    call=dict(kind='call',call=1)
    callback=dict(kind='witness',call=1,source='native_MIPSOL_verified_original_routes')
    bound=dict(kind='bound',call=1)
    returned=dict(kind='returned',call=1,return_code=0)
    quality=dict(kind='native_quality',call=1,solution_count=1)
    final=dict(kind='witness',call=1,source='native_final_verified_original_routes')
    normal=[identity,call,callback,bound,returned,quality,final,bound]

    def check(name,events,valid,complete=True):
        payloads=sequence(events);failure=None
        try: result=validate_event_lifecycle(payloads,True,complete)
        except (AssertionError,KeyError,ValueError) as error:failure=str(error);result=None
        assert (failure is None)==valid,(name,failure,result)
        records.append(dict(fixture=name,expected='ACCEPT' if valid else 'REJECT',
            outcome='ACCEPT' if failure is None else 'REJECT',reason=failure,
            require_complete=complete,payload_SHA=text_sha(payloads)))

    check('normal_callbacks_and_postreturn_finalization',normal,True)
    check('interrupted_before_Optimize_return',normal[:4],False)
    check('missing_quality_tail_after_native_return',normal[:5],False)
    check('partial_prefix_observation_does_not_claim_complete',normal[:4],True,False)
    check('postreturn_bound_before_quality',[identity,call,returned,bound,quality],False)
    check('quality_before_native_return',[identity,call,quality,returned],False)
    check('callback_witness_after_return',[identity,call,returned,quality,callback],False)
    check('final_witness_before_return',[identity,call,final,returned,quality],False)
    check('unknown_native_return',[identity,returned],False)
    check('duplicate_native_return',[identity,call,returned,quality,returned],False)
    check('duplicate_quality',[identity,call,returned,quality,quality],False)
    check('overlapping_call',[identity,call,dict(kind='call',call=2)],False)
    check('new_call_before_previous_quality',[identity,call,returned,dict(kind='call',call=2)],False)
    revoked=dict(kind='source_rejected',call=1,reason='source_bound_witness_contradiction',
        dependent_control_state_requires_abandonment=True)
    check('late_source_revocation_retains_return',normal+[revoked],True)
    check('native_call_after_source_revocation',normal+[revoked,dict(kind='call',call=2)],False)
    check('not_started_without_fake_Optimize',[identity,call,dict(kind='not_started',call=1,
        actual_Optimize=False)],True)
    check('unsupported_event',normal+[dict(kind='unregistered_new_event')],False)

    payloads=sequence(normal)
    for name,broken in [('missing_event_sequence',payloads[:3]+payloads[4:]),
                         ('duplicate_event_sequence',payloads[:3]+[payloads[2]]+payloads[3:])]:
        rejected=False
        try:validate_event_lifecycle(broken,True,True)
        except AssertionError:rejected=True
        assert rejected,name
        records.append(dict(fixture=name,expected='REJECT',outcome='REJECT',payload_SHA=text_sha(broken)))

    good=json.dumps(sequence([identity])[0],separators=(',',':')).encode()+b'\n'
    digest=hashlib.sha256(good).hexdigest()
    commit=f'NEJ1 1 0.25 {len(good)} {digest}\n'.encode()
    for name,data,carrier,observed,cap,valid in [
        ('valid_closed_receipt',good,commit,.5,1,True),
        ('incomplete_receipt',good,commit[:-1],.5,1,False),
        ('content_identity_mismatch',good.replace(b'identity',b'identitY'),commit,.5,1,False),
        ('length_mismatch',good+b' ',commit,.5,1,False),
        ('late_first_observation',good,commit,2,1,False),
        ('missing_data_tail',good[:-3],commit,.5,1,False)]:
        case=folder/name;case.mkdir();(case/'event_1.json').write_bytes(data)
        (case/'event_1.commit').write_bytes(carrier)
        failure=None
        try:receipt(case/'event_1.commit',observed,cap)
        except (AssertionError,ValueError,OSError) as error:failure=str(error)
        assert (failure is None)==valid,(name,failure)
        records.append(dict(fixture=name,expected='ACCEPT' if valid else 'REJECT',
            outcome='ACCEPT' if failure is None else 'REJECT',reason=failure,
            data_SHA=sha(case/'event_1.json'),receipt_SHA=sha(case/'event_1.commit')))

    scope=dict(full_original=False,native_preconditions=1,precondition_reason='',
        leaf='right',model_sha256='a'*64,lower_g=.2,upper_g=.5,cutoff=.5,gmax=.5,
        cover=[dict(id='left',lower_g=0,upper_g=.2,lower=.05,cutoff=.5),
               dict(id='right',lower_g=.2,upper_g=.5,lower=.2,cutoff=.5)])
    outside=[dict(G=.2-1e-9,F=.2)]
    assert strict_global_bound(scope,.3,outside)==.05
    records.append(dict(fixture='near_boundary_outside_witness_does_not_refute_cover_piece',outcome='ACCEPT'))
    refuted=False
    try:strict_global_bound(scope,.6,[dict(G=.3,F=.5)])
    except AssertionError:refuted=True
    assert refuted
    records.append(dict(fixture='raw_restricted_claim_refuted_before_cutoff_complement',outcome='REJECT'))
    broken=copy.deepcopy(scope);broken['cover'][1]['lower_g']=broken['lower_g']=.20000000001
    refuted=False
    try:strict_global_bound(broken,.3,outside)
    except AssertionError:refuted=True
    assert refuted
    records.append(dict(fixture='tiny_actual_cover_gap_not_filled_by_tolerance',outcome='REJECT'))

    q=dict(solution_count=1,solution_count_read_return_code=0,native_status=2,native_status_read_return_code=0,
        optimize_return_code=0,ObjVal=.31538869722423574,ObjBoundC=.31538869722423574,
        ConstrVio=5e-7,BoundVio=0,IntVio=0,DualVio=None)
    assert quality_predicate(q,'MIP')['sufficient']
    assert quality_predicate(q,'MIP')['unknown_attributes']==['DualVio']
    bad=dict(q,ConstrVio=2e-6)
    assert not quality_predicate(bad,'MIP')['sufficient']
    dual=dict(q,DualVio=2e-6)
    assert quality_predicate(dual,'MIP')['sufficient'] and not quality_predicate(dual,'LP')['sufficient']
    assert not quality_predicate(q,'MIP')['objective_error_bound_claimed']
    unknown_count=dict(q,solution_count=None,solution_count_read_return_code=10001)
    assert not quality_predicate(unknown_count,'LP')['sufficient']
    assert not quality_predicate(dict(q,native_status=12),'MIP')['sufficient']
    assert not quality_predicate(dict(q,native_status=None,native_status_read_return_code=10001),'MIP')['sufficient']
    assert not quality_predicate(dict(q,optimize_return_code=10025),'MIP')['sufficient']
    records.append(dict(fixture='quality_residuals_LP_MIP_unknown_and_objective_gap_are_distinct',outcome='ACCEPT'))

    launch=dict(version='candidate',arm='M-B')
    frozen=dict(scope,lower_g=0,upper_g=.5,cutoff=.5)
    journal=dict(calls={1:frozen},native_quality=[],native_infeasible=[dict(call=1)],source_rejections=[])
    chain=dict(actual=[1],ledger=[dict(native_status='INFEASIBLE')])
    witness=dict(source='later_sealed_own_return',G=0,F=0)
    refused=False
    try:independent_source_checks(launch,journal,{1:'MIP'},chain,{},[witness])
    except AssertionError:refused=True
    assert refused
    journal['source_rejections']=[dict(call=1,reason='source_infeasibility_witness_contradiction')]
    assert independent_source_checks(launch,journal,{1:'MIP'},chain,{},[witness])['infeasibility'][0]['source_infeasibility_rejected']
    journal['source_rejections']=[]
    assert not independent_source_checks(launch,journal,{1:'MIP'},chain,{},[dict(witness,G=.6)])['infeasibility'][0]['source_infeasibility_rejected']
    assert not independent_source_checks(launch,journal,{1:'MIP'},chain,{},[dict(witness,F=.6)])['infeasibility'][0]['source_infeasibility_rejected']
    records.append(dict(fixture='late_infeasibility_contradiction_and_G_F_domain_isolation',outcome='ACCEPT'))

    header='leaf_id,gamma_L,gamma_U,claimed_lower,status,reason\n'
    row='dependent,0,0.5,0.3,closed,source_bound_witness_contradiction\n'
    for name,content,valid in [
        ('complete_abandoned_state',header+row,True),('header_only_abandoned_state',header,False),
        ('truncated_abandoned_state',header+row[:-1],False),('duplicate_abandoned_leaf',header+row+row,False),
        ('foreign_abandoned_source',header+row.replace('source_bound_witness_contradiction','wrong_source'),False),
        ('out_of_domain_abandoned_leaf',header+row.replace(',0.5,',',0.6,'),False)]:
        path=folder/(name+'.csv');path.write_text(content,encoding='utf-8',newline='\n')
        failure=None
        try:validate_abandoned_control(path,.5,'source_bound_witness_contradiction')
        except (AssertionError,ValueError,OSError) as error:failure=str(error)
        assert (failure is None)==valid,(name,failure)
        records.append(dict(fixture=name,expected='ACCEPT' if valid else 'REJECT',
            outcome='ACCEPT' if failure is None else 'REJECT',reason=failure,SHA=sha(path)))
    value=dict(UTC=utc(),PASS=True,records=records,
        script_SHA=sha(__file__),reader_SHA=sha(ROOT/'scripts/round133_read.py'),
        Optimize=0,native_imports=0,scope='Controlled lifecycle/transport/source/quality faults only; not a natural performance run')
    write(folder/'receipt.json',value);write(OUT/'qualification/reader_faults.json',value)
    print(json.dumps(dict(PASS=True,checks=len(records),Optimize=0)))

def text_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

if __name__=='__main__':main()
