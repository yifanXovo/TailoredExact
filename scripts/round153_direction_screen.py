"""Paid finite-stock screen of saved fixed-dual continuation opportunities.

No Optimize, Native model read, new lower certificate, RMP solve, or production
selection occurs. A true feasible price upper limits only the particular
saved C_Q/a_K certificate, not the full hull or combined support family.
"""
from fractions import Fraction as F
from round143_math import outward
from round153_pricing import stock_value
from round153_common import *


DIRECTIONS = {
    'K-35-U': [
        ('price_deep/iter00003', 'saved_direction_long'),
        ('near_optimal_zero_pool/iter00010', None),
    ],
    'N-C20-U': [
        ('level_zero_continued/iter00008', 'saved_direction_long'),
        ('near_optimal_zero_pool/iter00016', None),
    ],
}


def run(label, selection_plan):
    configure(); tick = time.perf_counter()
    assert read(OUT/'followthrough_status.json')['state'] == 'REGISTERED_QUEUE_CLOSED'
    selection_path = ROOT/selection_plan; selection = read(selection_path)
    assert set(selection['roles']) == set(DIRECTIONS)
    target = OUT/'diagnostics'/label
    target.mkdir(parents=True, exist_ok=False)
    inputs = []; records = []
    for role, choices in DIRECTIONS.items():
        selected = selection['roles'][role]
        source = ROOT/selected['result']
        receipt_path = OUT/'fees'/selected['fee']/'receipt.json'
        receipt = read(receipt_path)
        assert receipt['exit_observed'] and receipt['exit_code']==0
        assert not receipt['timeout'] and not receipt['supervisor_failure']
        runtime_path=OUT/'engineering/exact_integer_runtime'/f"{selected['fee']}.json"
        runtime=read(runtime_path);arguments=runtime['arguments']
        assert runtime['outer_fee_label']==selected['fee'] and runtime['script']=='round153_primal_pool.py'
        assert runtime['script_SHA']==selection['unchanged_primal_source_SHA']
        assert runtime['wrapper_SHA']==selection['worker_SHA'] and runtime['active_process_digit_limit']==0
        assert len(arguments)>=6 and arguments[0]=='run' and arguments[1]==role
        assert (OUT/'coupled'/f'{role}_{arguments[2]}'/'result.json').resolve()==source.resolve()
        assert (ROOT/arguments[3]).resolve()==(ROOT/selected['resume']).resolve()
        assert float(arguments[4])==selected['internal_seconds']
        assert float(arguments[5])==selected['absolute_target']
        launch=read(receipt_path.parent/'launch.json');command=launch['command']
        at=next(i for i,v in enumerate(command) if Path(v).name=='round153_exact_worker.py')
        assert command[at+1:]==['execute',selected['fee'],'round153_primal_pool.py',
            selection['worker_qualification'],*arguments]
        qualification_path=OUT/'qualification'/selection['worker_qualification']/'result.json'
        assert runtime['qualification_SHA']==sha(qualification_path)
        assert read(qualification_path)['PASS']
        data = read(source); scope = data['scope']
        assert data['role'] == role
        assert data['primal_discovery_only'] and data['no_new_lower_claim']
        assert data['decision'] not in ('INITIALIZED_PRIMAL_DISCOVERY','RUNNING_PRIMAL_DISCOVERY')
        assert data['Q_SHA'] == sha(OUT/'reference'/role/'direct/model.mps')
        assert data['upper'] is not None and data['lower'] <= data['upper']
        tolerance = 1e-4 if role == 'K-35-U' else 1e-5
        pool = {tuple(Y) for Y in data['columns']}; values = {}

        def value(Y):
            Y = tuple(Y)
            if Y not in values:
                v = stock_value(scope, Y)
                assert v['feasible']
                values[Y] = v['f']
            return values[Y]

        for Y in pool: value(Y)
        inputs.append(dict(role=role, result=source.relative_to(ROOT).as_posix(),
            result_SHA=sha(source), Q_SHA=data['Q_SHA'], lower=data['lower'],
            upper=data['upper'], columns=len(pool), absolute_target=tolerance,
            final_probe_decision=data['decision'], fee=selected['fee'],
            fee_receipt_SHA=sha(receipt_path), fee_G1_seconds=receipt['G1_seconds'],
            runtime_record_SHA=sha(runtime_path), launch_SHA=sha(receipt_path.parent/'launch.json'),
            interval_target_met=data['upper']-data['lower'] <= tolerance))
        for suffix, refinement in choices:
            iteration = OUT/'coupled'/f'{role}_{suffix}'
            cert_path = iteration/'certificate.json.gz'; cert = load_gz(cert_path)
            plan_path = iteration.parent/'plan.json'; plan = read(plan_path)
            assert cert['qualified'] and plan['Q_SHA'] == data['Q_SHA'] and plan['scope'] == scope
            paths = [iteration/'pricing/result.json']
            if refinement:
                paths.append(OUT/'coupled'/f'{role}_{refinement}'/'pricing/result.json')
            prices = [read(p) for p in paths]; first = prices[0]
            beta = F(first['beta'])
            d = {tuple(map(int,k.split(':'))):F(v) for k,v in first['d_exact'].items()}
            assert beta >= 0 and F(cert['beta']) == beta
            assert set(d) == {(s['i'], y) for s in scope['stations'] for y in s['support']}
            assert all(F(cert['pi'].get(f'{i}:{y}',0.)) == -v for (i,y),v in d.items())
            candidates = set(pool)
            for price in prices:
                assert price['scope'] == scope and price['complete_domain']
                assert price['beta'] == first['beta'] and price['d_exact'] == first['d_exact']
                candidates.update(tuple(v['Y']) for v in price['stocks'])
            def true_price(Y):
                return beta*value(Y) + sum((d[s['i'],y] for s,y in zip(scope['stations'],Y)),F(0))
            witness = min(candidates, key=lambda Y:(true_price(Y),Y))
            upper = true_price(witness)
            lower = max(F(p['lower']) for p in prices)
            assert lower <= upper
            cq = F(cert['lower_exact']); a = F(cert['a_true_RMP_exact'])
            assert cq + a == F(cert['D_K_exact'])
            ceiling = cq + min(a, upper)
            fixed_lower = cq + min(a, lower)
            gap = F(data['upper'])-F(data['lower'])
            material = max(F(tolerance),gap/10)
            records.append(dict(role=role, source_iteration=iteration.relative_to(ROOT).as_posix(),
                certificate_SHA=sha(cert_path), source_plan_SHA=sha(plan_path),
                current_result=source.relative_to(ROOT).as_posix(), current_result_SHA=sha(source),
                price_sources=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p)) for p in paths],
                beta=float(beta), C_Q_exact=str(cq), a_K_exact=str(a),
                candidate_count=len(candidates), current_pool_columns=len(pool),
                best_true_price_witness=list(witness), best_true_f_exact=str(value(witness)),
                refreshed_price_upper_exact=str(upper), refreshed_price_upper=outward(upper,True),
                retained_price_lower_exact=str(lower), retained_price_lower=outward(lower,False),
                price_width=float(upper-lower), fixed_certificate_lower=outward(fixed_lower,False),
                fixed_certificate_ceiling_exact=str(ceiling), fixed_certificate_ceiling=outward(ceiling,True),
                ceiling_above_current_L=outward(ceiling-F(data['lower']),True),
                price_lower_needed_to_match_current_L_exact=str(F(data['lower'])-cq),
                price_threshold_is_necessary_and_also_requires_sufficient_fixed_intercept=True,
                fixed_intercept_can_reach_current_L=cq+a >= F(data['lower']),
                fixed_intercept_can_reach_material_gain=cq+a >= F(data['lower'])+material,
                material_research_gain_threshold=float(material),
                material_direct_potential=ceiling-F(data['lower']) >= material,
                scope_of_ceiling='Only this fixed C_Q/a_K correction; not z_Gamma or a combined support-family upper',
                screening_is_not_a_new_full_price_lower=True))
    result = dict(UTC=utc(),inputs=inputs,directions=records,
        selection_plan=selection_path.relative_to(ROOT).as_posix(),selection_plan_SHA=sha(selection_path),
        original_afterqueue_state=read(OUT/'afterqueue_status.json')['state'],
        selected_primal_probes_closed_successfully=True,
        rule='Refresh four preselected saved directions on all post-probe legal stocks; no automatic continuation',
        no_Optimize_or_Native_model_read=True, Q_bytes_read_for_identity_hash=True,
        no_new_lower_or_RMP_upper_claim=True,
        no_production_outcome_used=True, seconds=time.perf_counter()-tick,
        source_SHA=sha(ROOT/'scripts/round153_direction_screen.py'))
    write(target/'result.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__': run(*sys.argv[1:])
