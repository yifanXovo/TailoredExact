"""Offline exact current cold26 counterexample after the actual cross guard.

The current25 vector is only a mathematical locator. Every current cold row,
type and bound is rechecked; no other arm's fleet becomes P26's own incumbent.
"""
from round110_common import *
import round110_evidence as rule
import round108_reader as core
from fractions import Fraction
from collections import Counter
import math


def prepare(label):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();assert not budget()['unclosed']
    ident=read(OUT/'campaign/identity.json');launch=ident['launches'][25];p=launch['panel'];d=Path(launch['destination'])
    assert [launch['number'],launch['id'],launch['seed'],launch['arm']]==[26,'G100-C1',0,'P-GRB']
    c=read(d/'completion.json');r=read(d/'result.json');obs=read(d/'observations.json')
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert not (d/'whole_arm_receipt.json').exists() and read(d/'audit.json')['passed'] is True
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call'];assert len(calls)==1
    call=calls[0];assert call['full_original']==call['native_preconditions']==1 and call['call']==1
    assert call['lower_g']==0 and call['upper_g']==call['gmax'] and call['cutoff']==0
    model=d/'compact.lp';model_SHA=sha(model);assert model_SHA==p['reference']['canonical_sha256']==call['model_sha256']
    info,m=core.model_contract(ROOT,p,model,'P-GRB');a=core.evidence.instance(ROOT,p)
    rule.floor(p['lambda'],a['w'][1:],a['D'][1:],m['objective'],m['bounds'])
    locator=OUT/'campaign/reader_recovery/scoped25_vector02/exact_vector.json';source=read(locator)
    assert source['current_key']==[25,'G100-C1',0,'M-B'] and not source['row_violations']
    assert source['production_PE_SHA']==production['production_PE_SHA']
    values={n:Fraction(*source['complete_column_values'][n]) for n in m['bounds'] if n in source['complete_column_values']}
    for n in set(m['bounds'])-set(values):
        family,customer,bit=n.split('_')
        assert family in ('bit','prod'),'unmapped current cold column; HOLD'
        stock=values['Y_'+customer];assert stock.denominator==1
        binary=Fraction((int(stock)>>int(bit))&1)
        values[n]=binary if family=='bit' else values['G']*binary
    assert set(values)==set(m['bounds'])
    coefficients={}
    def exact(x):
        if x not in coefficients:coefficients[x]=Fraction(x)
        return coefficients[x]
    bad=[]
    for n,(lo,hi) in m['bounds'].items():
        assert (not math.isfinite(lo) or values[n]>=exact(lo)) and (not math.isfinite(hi) or values[n]<=exact(hi)),('bound',n)
        assert m['types'][n]=='C' or values[n].denominator==1,('type',n)
    for number,(terms,sense,rhs) in enumerate(m['rows'],1):
        lhs=sum((values[n]*exact(x) for n,x in terms if values[n]),Fraction(0));target=exact(rhs)
        valid=lhs==target if sense=='=' else lhs<=target if sense=='<=' else lhs>=target
        if not valid:bad.append(dict(row=number,sense=sense,violation=float(abs(lhs-target))))
    obj=sum((values[n]*exact(x) for n,x in m['objective'][0] if values[n]),exact(m['objective'][1]))
    out=OUT/'campaign/reader_recovery'/label;out.mkdir(parents=True,exist_ok=False)
    vp=out/'current_exact_binary64_matrix_witness.json'
    write(vp,dict(complete_column_values={n:[v.numerator,v.denominator] for n,v in values.items()},
        current_model_SHA=model_SHA,current_key=[26,'G100-C1',0,'P-GRB'],current_campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        current_production_PE_SHA=production['production_PE_SHA'],input_SHA=sha(ROOT/p['input_path']),
        mathematical_vector_source=locator.relative_to(ROOT).as_posix(),mathematical_vector_source_SHA=sha(locator),
        mathematical_locator_is_not_current_native_or_own_incumbent_authority=True,
        exact_objective=[obj.numerator,obj.denominator],row_violations=bad,model_info=info,column_type_counts=dict(Counter(m['types'].values()))))
    print(json.dumps(dict(rows=len(m['rows']),columns=len(values),exact_objective=float(obj),bad_rows=bad[:20],bad_count=len(bad))),flush=True)
    assert not bad,'no exact current cold matrix counterexample yet; HOLD'
    claims=[v['payload']['native_bound'] for v in obs if v['payload']['kind']=='bound']+[r['native_mip_best_bound']]
    assert any(exact(lb)>obj+Fraction(1,10**7) for lb in claims)
    rule.returned_lifecycle(r,c,core.rows(d/'phases.csv'),(d/'native.log').read_text(encoding='utf-8'),m)
    physical=core.full_fleet(ROOT,p,r);assert physical['F']>0.
    fee=OUT/'fees/main09_tail01';fl=read(fee/'launch.json');fr=read(fee/'receipt.json')
    assert fl['command'][4:6]==['26','27'] and fr['exit_code']==1
    interval=rule.clock_interval(read(d/'native_end_receipt.json')['complete_seconds_until_native_end'],fr['outer_seconds'],[],p['cap_seconds'])
    paths=[v for v in d.rglob('*') if v.is_file() and '__pycache__' not in v.parts]
    paths += [v for v in fee.rglob('*') if v.is_file() and '__pycache__' not in v.parts]
    paths += [vp,locator,OUT/'campaign/identity.json',OUT/'candidate_identity.json',OUT/'production_identity.json',OUT/'evidence_policy.json',
        OUT/'review/performance_admission.json',ROOT/'scripts/round110_cold26_proof.py',ROOT/'scripts/round110_evidence.py',
        ROOT/'scripts/round110_reader.py',ROOT/'src/GurobiBaseline.cpp',ROOT/'src/NativeEvidenceJournal.cpp']
    proposal=dict(schema='round110-current-cold-call-rejection-v1',key=[26,'G100-C1',0,'P-GRB'],
        production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        command=launch['command'],input_SHA=sha(ROOT/p['input_path']),model_SHA=model_SHA,
        exact_vector_path=vp.relative_to(ROOT).as_posix(),exact_vector_SHA=sha(vp),raw_bindings={v.relative_to(ROOT).as_posix():sha(v) for v in paths},
        reject_all_call_native_lower_claims=True,withdraw_necessary_dependent_closures=True,qualified_L=0.,
        qualified_L_source='independently_proved_own_original_full_domain_nonnegative_floor',own_U=physical['F'],certificate_from_own_exact_zero=False,
        original_fee_path=fee.relative_to(ROOT).as_posix(),time=dict(exact_seconds=None,interval=interval,enclosing_fee_label='main09_tail01',
            preceding_complete_receipts=[],later_repair_engineering_in_original_interval=False),no_solver_invoked=True,
        raw_flags_and_missing_original_whole_clock_preserved=True,no_cross_arm_incumbent_transfer=True)
    write(out/'proposal.json',proposal)
    print(json.dumps(dict(proposal=(out/'proposal.json').relative_to(ROOT).as_posix(),own_U=physical['F'],qualified_L=0.,time=proposal['time'],Optimize=0)),flush=True)


if __name__=='__main__':prepare(sys.argv[1])
