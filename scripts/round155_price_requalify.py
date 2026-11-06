"""Construct immutable, source-linked corrections without rerunning prices."""
from copy import deepcopy
from fractions import Fraction as F
from round143_math import outward
from round155_price_certificate import recover_actual,corrected_result
from round155_common import *


def run(label='price_transport_requalification_v1'):
    configure();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    index_path=OUT/'review/native_price_corrections.json';assert not index_path.exists()
    index=dict(schema='round155-historical-price-corrections-v1',decision='INDEPENDENT_READBACK_REQUIRED',
        prices={},phases={},constructor_label=label,source_SHA=sha(__file__),
        price_certificate_SHA=sha(ROOT/'scripts/round155_price_certificate.py'),Optimize=0)
    summary=[]
    for role in ['K-35-U','N-C20-U']:
        folder=OUT/'coupled'/f'{role}_feasible_level_deep_v2';raw_path=folder/'result.json'
        raw=read(raw_path);plan=read(folder/'plan.json');prior=read(plan['source'])
        result=deepcopy(raw);supports=deepcopy(prior['supports']);records=[];lower=prior['lower']
        corrected_prices=0;corrected_rows=0
        for original_record in raw['records']:
            iteration=original_record['iteration'];step=folder/f'iter{iteration:06}'
            path=step/'pricing/result.json';original=read(path);direction=read(step/'direction.json')
            correction=recover_actual(path,original)
            assert correction['actual_cost_bounds_cover_complete_domain']
            qualified=corrected_result(original,correction)
            qualified.update(raw_result_SHA=sha(path),raw_result_path=path.relative_to(ROOT).as_posix(),
                derived_certificate_correction_not_new_optimization=True)
            qp=target/role/f'iter{iteration:06}'/'price.json';write(qp,qualified)
            index['prices'][path.relative_to(ROOT).as_posix()]=dict(raw_result_SHA=sha(path),
                qualified_price=qp.relative_to(ROOT).as_posix(),qualified_price_SHA=sha(qp))
            corrected_prices+=qualified['lower']!=original['lower']
            sp=step/'support.json';old_support=read(sp);support=deepcopy(old_support)
            support['row']['rhs']=min(support['row']['rhs'],outward(F(qualified['lower'])+F(support['transport_exact']),False))
            corrected_rows+=support['row']['rhs']!=old_support['row']['rhs']
            support.update(raw_support_SHA=sha(sp),qualified_price_path=qp.relative_to(ROOT).as_posix(),
                qualified_price_SHA=sha(qp),actual_Native_coefficient_transport_applied=True)
            assert old_support==raw['supports'][len(supports)]
            supports.append(support)
            lm=F(qualified['lower']);cq=F(direction['C_Q_exact']);aK=F(direction['a_K_exact'])
            lower=max(lower,outward(cq+min(aK,lm),False))
            record=dict(original_record,price_lower=qualified['lower'],
                raw_recorded_price_lower=original['lower'],qualified_price_SHA=sha(qp))
            assert record['lower']==lower
            assert record['target_proved']==(lm>=F(direction['tau_exact']))
            records.append(record)
        assert len(supports)==len(raw['supports']) and lower==raw['lower']
        result.update(supports=supports,records=records,prior_results=[str(raw_path)],
            raw_phase_result_SHA=sha(raw_path),raw_phase_result_path=raw_path.relative_to(ROOT).as_posix(),
            derived_certificate_correction_not_new_optimization=True,qualification_constructor_label=label,
            numerical_upper_and_inventory_columns_unchanged=True,
            raw_solve_times_are_not_new_measurements=True)
        output=target/role/'result.json';write(output,result)
        index['phases'][raw_path.relative_to(ROOT).as_posix()]=dict(raw_result_SHA=sha(raw_path),
            qualified_result=output.relative_to(ROOT).as_posix(),qualified_result_SHA=sha(output))
        summary.append(dict(role=role,prices=len(records),changed_price_lowers=corrected_prices,
            changed_support_RHS=corrected_rows,lower=result['lower'],upper=result['upper'],
            columns=len(result['columns']),supports=len(supports),qualified_result_SHA=sha(output)))
    write(target/'result.json',dict(decision='CORRECTIONS_CONSTRUCTED_INDEPENDENT_READBACK_REQUIRED',
        phases=summary,Optimize=0,raw_evidence_unchanged=True,source_SHA=sha(__file__)))
    index['constructor_result_SHA']=sha(target/'result.json');write(index_path,index)
    print(json.dumps(dict(decision=index['decision'],phases=summary,Optimize=0)),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
