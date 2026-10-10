"""Bind the actual paused scoped M-B call to its complete offline vector.

No generic numerical fallback, solver environment, or native submission.
"""
from round110_common import *
import round110_evidence as rule
import round108_reader as core


def prepare(label,vector_relative):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();assert not budget()['unclosed']
    ident=read(OUT/'campaign/identity.json');launch=ident['launches'][24]
    assert [launch['number'],launch['id'],launch['seed'],launch['arm']]==[25,'G100-C1',0,'M-B']
    d=Path(launch['destination']);obs=read(d/'observations.json');r=read(d/'result.json');c=read(d/'completion.json')
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert read(d/'audit.json')['passed'] is False and not (d/'whole_arm_receipt.json').exists()
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call'];assert len(calls)==4
    call=calls[-1];assert call['call']==4 and call['leaf']=='L0' and call['lower_g']==0 and call['upper_g']==call['cutoff']>0
    assert call['native_preconditions']==1 and call['full_original']==0
    vector_path=ROOT/vector_relative;v=read(vector_path)
    assert v['current_key']==[25,'G100-C1',0,'M-B'] and v['current_call']==4
    assert v['current_model_SHA']==call['model_sha256'] and not v['row_violations']
    physical=core.full_fleet(ROOT,launch['panel'],r)
    assert physical['F']==physical['G']==physical['P']==0.
    fee=OUT/'fees/main09';fl=read(fee/'launch.json');fr=read(fee/'receipt.json')
    assert fl['command'][4:6]==['25','27'] and fr['exit_code']==1
    interval=rule.clock_interval(read(d/'native_end_receipt.json')['complete_seconds_until_native_end'],fr['outer_seconds'],[],launch['panel']['cap_seconds'])
    out=OUT/'campaign/reader_recovery'/label;out.mkdir(parents=True,exist_ok=False)
    paths=[p for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for p in fee.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [vector_path,OUT/'campaign/identity.json',OUT/'candidate_identity.json',OUT/'production_identity.json',
        OUT/'evidence_policy.json',OUT/'review/performance_admission.json',ROOT/'scripts/round110_scoped25_proof.py',
        ROOT/'scripts/round110_scoped25_vector.py',ROOT/'scripts/round110_evidence.py',ROOT/'scripts/round110_reader.py',
        ROOT/'src/PaperExternalGiniTree.cpp',ROOT/'src/GurobiBaseline.cpp',ROOT/'src/NativeEvidenceJournal.cpp']
    proposal=dict(schema='round110-current-scoped-call-rejection-v1',key=[25,'G100-C1',0,'M-B'],
        production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        command=launch['command'],input_SHA=sha(ROOT/launch['panel']['input_path']),model_SHA=call['model_sha256'],
        exact_vector_path=vector_path.relative_to(ROOT).as_posix(),exact_vector_SHA=sha(vector_path),
        raw_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in paths},damaged_calls=[4],
        reject_all_call_native_lower_claims=True,withdraw_necessary_dependent_closures=True,
        preserved_distinct_LP_calls=[1,2,3],qualified_L=0.,
        qualified_L_source='independently_proved_own_original_full_domain_nonnegative_floor',own_U=0.,
        certificate_from_own_exact_zero=True,original_fee_path=fee.relative_to(ROOT).as_posix(),
        time=dict(exact_seconds=None,interval=interval,enclosing_fee_label='main09',preceding_complete_receipts=[],
            later_repair_engineering_in_original_interval=False),no_solver_invoked=True,
        raw_flags_and_missing_original_whole_clock_preserved=True)
    write(out/'proposal.json',proposal)
    print(json.dumps(dict(proposal=(out/'proposal.json').relative_to(ROOT).as_posix(),exact_objective=v['exact_objective_float'],
        own_U=0.,time=proposal['time'],Optimize=0,native_environment=0)),flush=True)


if __name__=='__main__':prepare(*sys.argv[1:])
