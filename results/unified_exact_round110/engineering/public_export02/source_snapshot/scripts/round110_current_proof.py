"""Prepare a current cold-call proof only after actual paused failure; no solve."""
from round110_common import *
import round110_evidence as rule
import round108_reader as core
from fractions import Fraction
import shutil


def prepare(number, label, fee_label):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();ident=read(OUT/'campaign/identity.json')
    launch=ident['launches'][number-1];assert launch['number']==number and launch['arm']=='P-GRB'
    d=Path(launch['destination']);fee=OUT/'fees'/fee_label
    fl=read(fee/'launch.json');fr=read(fee/'receipt.json');assert fr['exit_code']==1
    first,last=map(int,fl['command'][4:6]);assert first<=number<=last
    assert not (d/'whole_arm_receipt.json').exists() and not budget()['unclosed']
    model_SHA=sha(d/'compact.lp');p=launch['panel']
    assert model_SHA==p['reference']['canonical_sha256']
    fixture=OUT/'qualification/regression_fixture/results/unified_exact_round109'
    candidates=[]
    for folder in (fixture/'campaign/raw').iterdir():
        if sha(folder/'compact.lp')==model_SHA:
            old_key=read(folder/'launch.json')
            vector_folder='cross_arm_diagnosis02' if old_key['number']==15 else 'main06_diagnosis02'
            candidates.append(fixture/'review'/vector_folder/'exact_binary64_matrix_witness.json')
    assert len(candidates)==1,'no unique inherited mathematical vector matching exact current matrix; HOLD'
    original_vector=candidates[0];old=read(original_vector)
    values={n:Fraction(*v) for n,v in old['complete_column_values'].items()}
    m=core.lp_model(d/'compact.lp');a=core.evidence.instance(ROOT,p)
    rule.floor(p['lambda'],a['w'][1:],a['D'][1:],m['objective'],m['bounds'])
    assert set(values)==set(m['bounds'])
    for n,(lo,hi) in m['bounds'].items():
        assert (not rule.math.isfinite(lo) or values[n]>=Fraction(lo)) and (not rule.math.isfinite(hi) or values[n]<=Fraction(hi))
        assert m['types'][n]=='C' or values[n].denominator==1
    for terms,sense,rhs in m['rows']:
        lhs=sum((values[n]*Fraction(v) for n,v in terms),Fraction(0));rhs=Fraction(rhs)
        assert lhs==rhs if sense=='=' else lhs<=rhs if sense=='<=' else lhs>=rhs
    terms,constant=m['objective'];obj=sum((values[n]*Fraction(v) for n,v in terms),Fraction(constant))
    obs=read(d/'observations.json');r=read(d/'result.json');c=read(d/'completion.json')
    claims=[v['payload']['native_bound'] for v in obs if v['payload']['kind']=='bound']+[r['native_mip_best_bound']]
    assert any(Fraction(lb)>obj+Fraction(1,10**7) for lb in claims)
    rule.returned_lifecycle(r,c,core.rows(d/'phases.csv'),(d/'native.log').read_text(encoding='utf-8'),m)
    proof_dir=OUT/'campaign/reader_recovery'/label;proof_dir.mkdir(parents=True,exist_ok=False)
    vector_path=proof_dir/'current_exact_binary64_matrix_witness.json'
    write(vector_path,dict(complete_column_values=old['complete_column_values'],current_model_SHA=model_SHA,
        current_key=[number,launch['id'],launch['seed'],launch['arm']],current_campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        current_production_PE_SHA=production['production_PE_SHA'],input_SHA=sha(ROOT/p['input_path']),
        mathematical_vector_source=original_vector.relative_to(ROOT).as_posix(),mathematical_vector_source_SHA=sha(original_vector),
        historical_call_metadata_is_not_current_authority=True,exact_objective=[obj.numerator,obj.denominator]))
    preceding=[];prior_paths=[]
    for ordinal in range(first,number):
        path=Path(ident['launches'][ordinal-1]['destination'])/'whole_arm_receipt.json'
        preceding.append(read(path)['complete_seconds']);prior_paths.append(path)
    native_end=read(d/'native_end_receipt.json')
    interval=rule.clock_interval(native_end['complete_seconds_until_native_end'],fr['outer_seconds'],preceding,p['cap_seconds'])
    physical=core.full_fleet(ROOT,p,r)
    paths=[f for f in d.rglob('*') if f.is_file() and '__pycache__' not in f.parts]
    paths += [fee/'launch.json',fee/'receipt.json',fee/'failure.txt',*prior_paths,vector_path,original_vector,
        OUT/'campaign/identity.json',OUT/'candidate_identity.json',OUT/'production_identity.json',OUT/'evidence_policy.json',
        OUT/'review/performance_admission.json',ROOT/'scripts/round110_evidence.py',ROOT/'scripts/round110_reader.py',
        ROOT/'scripts/round110_current_proof.py',ROOT/'src/GurobiBaseline.cpp',ROOT/'src/NativeEvidenceJournal.cpp']
    raw_bindings={path.relative_to(ROOT).as_posix():sha(path) for path in paths}
    proposed=dict(schema='round110-current-cold-call-rejection-v1',key=[number,launch['id'],launch['seed'],launch['arm']],
        production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        command=launch['command'],input_SHA=sha(ROOT/p['input_path']),model_SHA=model_SHA,
        exact_vector_path=vector_path.relative_to(ROOT).as_posix(),exact_vector_SHA=sha(vector_path),raw_bindings=raw_bindings,
        reject_all_call_native_lower_claims=True,withdraw_necessary_dependent_closures=True,qualified_L=0.,
        qualified_L_source='independently_proved_own_original_full_domain_nonnegative_floor',own_U=physical['F'],
        certificate_from_own_exact_zero=physical['F']==0.,original_fee_path=fee.relative_to(ROOT).as_posix(),
        time=dict(exact_seconds=None,interval=interval,enclosing_fee_label=fee_label,
            preceding_complete_receipts=[p.relative_to(ROOT).as_posix() for p in prior_paths],
            later_repair_engineering_in_original_interval=False),no_solver_invoked=True,
        raw_flags_and_missing_original_whole_clock_preserved=True)
    write(proof_dir/'proposal.json',proposed)
    print(json.dumps(dict(proposal=(proof_dir/'proposal.json').relative_to(ROOT).as_posix(),
        exact_objective=float(obj),own_U=physical['F'],time=proposed['time'],Optimize=0)))


if __name__=='__main__':prepare(int(sys.argv[1]),sys.argv[2],sys.argv[3])
