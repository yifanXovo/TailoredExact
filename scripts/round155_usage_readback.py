"""Reconcile saved column-use observations with feedback and sparse primals.

This is an evidence reader, not another optimization or a reconstruction of
unrecorded primal points. Run under its own outer meter after the serial lane
is idle. Full-Q numerical feasibility is covered by round155_audit separately.
"""
from round155_common import *


def run(label='column_usage_readback_v1', phase='all'):
    configure()
    target = OUT/'qualification'/label
    target.mkdir(parents=True, exist_ok=False)
    facts = []
    for path in sorted((OUT/'coupled').glob('*/result.json')):
        if phase != 'all' and path.parent.name != phase:
            continue
        result = read(path)
        folder = path.parent
        plan = read(folder/'plan.json')
        prior = read(plan['source'])
        assert sha(plan['source']) == plan['source_SHA']
        assert not result['refresh_required']
        assert result['scope'] == prior['scope'] == plan['scope']
        short = {'K-35-U': 'K35', 'N-C20-U': 'NC20'}[result['role']]
        receipt_path = OUT/'fees'/(short+'_'+result['label'])/'receipt.json'
        receipt = read(receipt_path)
        assert receipt['exit_observed'] and receipt['exit_code'] == 0
        assert not receipt['timeout'] and not receipt['supervisor_failure']
        pool = {tuple(Y): j for j, Y in enumerate(prior['columns'])}
        assert len(pool) == len(prior['columns'])
        tracked = {tuple(row['Y']): {k: v for k, v in row.items() if k != 'Y'}
                   for row in prior.get('new_column_usage', [])}
        assert set(tracked) <= set(pool)
        events = []
        actual_records = []

        def usage(usage_path, iteration, primal_path, rmp_path, final=False):
            observed = read(rmp_path)
            assert observed['Status'] == 2 and observed['primal']['qualified']
            data = load_gz(usage_path)
            assert data['positive_weight_threshold'] == 1e-10
            assert data['includes_prior_Round155_phases']
            stocks = data['stocks']
            weights = {}
            marginal_terms = {}
            for row in stocks:
                Y = tuple(row['Y'])
                assert Y in tracked and Y in pool and Y not in weights
                weight = row['weight']
                assert math.isfinite(weight) and weight > 1e-10
                meta = tracked[Y]
                assert (row['origin_phase'], row['added_iteration']) == (
                    meta['origin_phase'], meta['added_iteration'])
                weights[Y] = weight
                for station, y in zip(result['scope']['stations'], Y):
                    marginal_terms.setdefault(f'{station["i"]}:{y}', []).append(weight)
            marginals = {k: math.fsum(v) for k, v in marginal_terms.items()}
            assert marginals == data['marginal_contributions']
            primal_sha = None
            if primal_path.exists():
                witness = load_gz(primal_path)
                assert witness['missing_variables_are_zero'] and witness['check']['qualified']
                point = witness['sparse_point']
                all_weights = {}
                for row in witness['stocks']:
                    Y = tuple(row['Y'])
                    assert Y in pool and Y not in all_weights
                    name = f'hull_lambda_{pool[Y]:05}'
                    assert row['column'] == name and row['weight'] == point[name]
                    all_weights[Y] = row['weight']
                for Y, index in pool.items():
                    assert all_weights.get(Y, 0.) == point.get(f'hull_lambda_{index:05}', 0.)
                expected = {Y: weight for Y, weight in all_weights.items()
                            if Y in tracked and weight > 1e-10}
                assert expected == weights
                primal_sha = sha(primal_path)
            for Y, weight in weights.items():
                meta = tracked[Y]
                meta['used_iterations'] += 1
                meta['maximum_weight'] = max(meta['maximum_weight'], weight)
                if meta['first_used_iteration'] is None:
                    meta['first_used_iteration'] = iteration
                    meta['first_used_phase'] = result['label']
            event = dict(iteration=iteration, final_refresh=final,
                usage_SHA=sha(usage_path), RMP_result_SHA=sha(rmp_path),
                positive_columns=len(weights), total_weight=math.fsum(weights.values()),
                marginal_coordinates=len(marginals),
                full_saved_primal_projection_checked=primal_sha is not None,
                primal_SHA=primal_sha)
            events.append(event)
            return event

        rmp_paths = sorted(folder.glob('iter*/RMP/result.json'))
        for rp in rmp_paths:
            step = rp.parent.parent
            iteration = int(step.name.removeprefix('iter'))
            rr = read(rp)
            usage_path = step/'new_column_usage.json.gz'
            qualified = rr['Status'] == 2 and rr.get('primal', {}).get('qualified', False)
            assert usage_path.exists() == qualified
            if qualified:
                event = usage(usage_path, iteration, step/'primal.json.gz', rp)
            feedback_path = step/'column_feedback.json.gz'
            record_path = step/'result.json'
            assert feedback_path.exists() == record_path.exists()
            if not record_path.exists():
                continue
            assert qualified
            record = read(record_path)
            actual_records.append(record)
            assert record['iteration'] == iteration
            assert record['new_columns_used'] == event['positive_columns']
            assert record['new_column_total_weight'] == event['total_weight']
            added = 0
            for row in load_gz(feedback_path):
                Y = tuple(row['stock']['Y'])
                fresh = Y not in pool
                assert row['new'] == fresh
                if fresh:
                    added += 1
                    pool[Y] = len(pool)
                    tracked[Y] = dict(origin_phase=result['label'], added_iteration=iteration,
                        used_iterations=0, maximum_weight=0.,
                        first_used_iteration=None, first_used_phase=None)
            assert record['added'] == added and record['columns'] == len(pool)
        assert actual_records == result['records']
        final_rmp = folder/'final_RMP/result.json'
        final_usage = folder/'final_column_usage.json.gz'
        if final_rmp.exists():
            returned = read(final_rmp)
            qualified = returned['Status'] == 2 and returned.get('primal', {}).get('qualified', False)
            assert final_usage.exists() == qualified
            if qualified:
                # Both executed loops increment the counter after every saved
                # feedback record and use that counter for the final refresh.
                usage(final_usage, len(actual_records), folder/'final_primal.json.gz',
                      final_rmp, final=True)
        else:
            assert not final_usage.exists()
        assert list(pool) == [tuple(Y) for Y in result['columns']]
        expected_tracking = [dict(Y=list(Y), **meta) for Y, meta in tracked.items()]
        assert expected_tracking == result['new_column_usage']
        full = sum(event['full_saved_primal_projection_checked'] for event in events)
        facts.append(dict(phase=folder.name, result_SHA=sha(path), plan_SHA=sha(folder/'plan.json'),
            receipt_SHA=sha(receipt_path), events=events,
            usage_observations=len(events), observations_with_full_saved_primal=full,
            observations_with_tracking_only=len(events)-full,
            cumulative_tracked_columns=len(tracked),
            cumulative_columns_ever_recorded_above_threshold=sum(meta['maximum_weight'] > 1e-10
                                                               for meta in tracked.values()),
            maximum_recorded_weight=max((meta['maximum_weight'] for meta in tracked.values()), default=0.),
            all_usage_marginals_and_cumulative_metadata_reconciled=True))
    assert facts, ('no completed phase selected', phase)
    write(target/'result.json', dict(PASS=True, phases=facts, selected_phase=phase,
        source_SHA=sha(__file__), Optimize=0, Native_model_reads=0,
        positive_weight_threshold=1e-10,
        full_primal_projection_checked_only_where_a_saved_primal_exists=True,
        no_reconstruction_of_unrecorded_intermediate_primal_points=True,
        no_claim_of_exact_zero_from_numerical_nonuse=True,
        full_Q_primal_feasibility_is_a_separate_general_readback=True,
        nonimplementer_agent_review=False))
    print(json.dumps(dict(PASS=True, phases=len(facts),
        usage_observations=sum(v['usage_observations'] for v in facts),
        saved_primal_projections=sum(v['observations_with_full_saved_primal'] for v in facts),
        Optimize=0)), flush=True)


if __name__ == '__main__':
    globals()[sys.argv[1]](*sys.argv[2:])
