"""Zero-Optimize reader fixtures; source-binding stubs are synthetic unit data.

Uses an actual saved zero-lower full model and a separate positive-S support
schema from the strict fixture. Neither is a new performance/LP observation.
"""
import csv
from round148_context import root_context,source_call_check
from round148_common import *
configure()


def case(name,text,panel,meta,positive):
    folder=OUT/'qualification/reader_boundary'/name;models=folder/'models'
    models.mkdir(parents=True,exist_ok=False)
    source=models/'L0_epoch_0_generation_2.lp';source.write_bytes(text)
    # Real source bytes coexist with an earlier generation and the new suffix.
    (models/'L0_epoch_0_generation_1.lp').write_bytes(text+b'\n\\ earlier-generation reader-fixture comment\n')
    (models/'L0_epoch_0_generation_2_round148_shared_S.lp').write_bytes(text+b'\n\\ suffix-interference reader fixture, not a Native input\n')
    write(models/'round146_root.json',meta)
    selection=dict(source_call=1,source_model_SHA=sha(source),ready=False,
        fixture_only=True,not_a_Native_call_or_performance_result=True)
    write(folder/'round148_selection.json',selection)
    block,support,actual=root_context(models,panel,True,folder/'rows.json',[])
    assert block['applicable']==positive and not block['rows']
    # These are explicit unit stubs, not fabricated journal/call observations.
    logfile=str(folder/'synthetic_unit_LP.log')
    stub=[dict(payload=dict(kind='call',call=1,model_sha256=sha(source),leaf='L0',
        native_preconditions=True,native_log_path=logfile))]
    ledger=[dict(leaf_id='L0',model_sha256=sha(source),native_log=logfile,
        solve_kind='LP',optimize_return_code='0')]
    source_call_check(selection,stub,ledger)
    negatives=[]
    def rejected(label,action):
        try:action()
        except AssertionError as error:negatives.append(dict(case=label,rejected=True,reason=str(error)))
        else:raise AssertionError('failed to reject '+label)
    duplicate=models/'duplicate_source.lp';duplicate.write_bytes(text)
    rejected('duplicate_source_SHA',lambda:root_context(models,panel,True,folder/'duplicate_rows.json',[]))
    # This is a reconstructible fixture file, never a science/old/user object.
    duplicate.rename(folder/'duplicate_source_negative_case.lp')
    bad=dict(selection,source_model_SHA='0'*64);write(folder/'round148_selection.json',bad)
    rejected('missing_source_SHA',lambda:root_context(models,panel,True,folder/'missing_rows.json',[]))
    write(folder/'round148_selection.json',selection)
    rejected('missing_source_call',lambda:source_call_check(selection,[],ledger))
    rejected('mismatched_source_call_SHA',lambda:source_call_check(bad,stub,ledger))
    rejected('duplicate_source_call',lambda:source_call_check(selection,stub+stub,ledger))
    rejected('missing_source_controller',lambda:source_call_check(selection,stub,[]))
    rejected('source_not_LP',lambda:source_call_check(selection,stub,[dict(ledger[0],solve_kind='MIP')]))
    return dict(name=name,positive_S=positive,old_GD_rows=0,source_model_SHA=sha(source),
        current_generation_chosen_by_SHA=True,interfering_affine_suffix=True,
        actual_supports={str(i):sorted(s) for i,s in support.items()},negatives=negatives)


def main():
    configure();old=ROOT/'results/unified_exact_round146/qualification/writer/zero_lower'
    meta=read(old/'round146_root.json')
    facts=[case('saved_zero_lower',(old/'off.lp').read_bytes(),dict(total_initial=3,Q_vector=[3]),meta,False)]
    text='''Minimize
 obj: G
Subject To
 ratio_1: r_1 - Y_1 = 0
 ratio_2: r_2 - Y_2 = 0
 mass_1: state_1_1 + state_1_2 = 1
 mass_2: state_2_1 + state_2_2 = 1
 link_1: Y_1 - state_1_1 - 2 state_1_2 = 0
 link_2: Y_2 - state_2_1 - 2 state_2_2 = 0
Bounds
 0 <= G <= 1
 1 <= Y_1 <= 2
 1 <= Y_2 <= 2
 1 <= r_1 <= 2
 1 <= r_2 <= 2
 0 <= state_1_1 <= 1
 0 <= state_1_2 <= 1
 0 <= state_2_1 <= 1
 0 <= state_2_2 <= 1
Binaries
 state_1_1 state_1_2 state_2_1 state_2_2
Generals
 Y_1 Y_2
End
'''
    meta=dict(applicable=True,rows=0,Bminus=2,B=4,source_solves=0,new_columns=0)
    facts.append(case('positive_S_support_schema',text.encode(),dict(total_initial=4,Q_vector=[2]),meta,True))
    assert root_context(OUT/'qualification/reader_boundary/absent',{},True,
        OUT/'qualification/reader_boundary/absent_unused.json',[])==(None,None,None)
    write(OUT/'qualification_reader_boundary.json',dict(PASS=True,Optimize=0,Native_load=0,
        facts=facts,H_no_model_omission_retained=True,
        synthetic_binding_stubs_are_unit_tests_not_Native_evidence=True,
        positive_schema_is_not_a_complete_routing_model=True,
        positive_zero_GD_nonzero_affine_validity='qualification_arithmetic.json strict_zero_old_GD',
        helper_SHA=sha(ROOT/'scripts/round148_context.py')))
    print('PASS zero-GD source-SHA context, interference/missing/duplicate/call negatives, H no model')


def real():
    configure();matrix=read(OUT/'qualification_matrix.json');d=Path(matrix['groups'][0]['launch']['destination'])
    closeout_path=d/'verification_closeout.json';before=sha(closeout_path);closeout=read(closeout_path)
    for key,name in [('audit_SHA','audit.json'),('own_evidence_SHA','independent_evidence.json'),
        ('claims_SHA','native_claims.json'),('rejection_SHA','claim_rejections.json'),('producer_receipt_SHA','producer_receipt.json')]:
        assert sha(d/name)==closeout[key]
    for name,digest in read(d/'producer_seal.json')['required_SHA'].items():assert sha(d/name)==digest
    selection=read(d/'external/round148_selection.json')
    with (d/'external/paper_optimize_ledger.csv').open(newline='',encoding='utf-8-sig') as stream:
        linked=source_call_check(selection,read(d/'observations.json'),list(csv.DictReader(stream)))
    assert linked['call']['native_preconditions']==1 and linked['controller_LP']['solve_kind']=='LP'
    assert before==sha(closeout_path)
    write(OUT/'qualification_reader_real_source_binding.json',dict(PASS=True,Optimize=0,Native_load=0,
        source_call=selection['source_call'],source_model_SHA=selection['source_model_SHA'],
        raw_integer_preconditions_before_relaxation=linked['call']['native_preconditions'],
        accepted_controller_kind=linked['controller_LP']['solve_kind'],closed_producer_and_verification_hashes_unchanged=True,
        closed_verification_not_reentered=True,helper_SHA=sha(ROOT/'scripts/round148_context.py')))
    print('PASS real sealed source call SHA/leaf/log/actual LP binding; immutable closeout retained')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='real':real()
    else:main()
