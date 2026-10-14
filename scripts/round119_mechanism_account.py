"""Read-only actual event/call cost account, with explicit clock semantics."""
from round119_common import *
import csv

def account():
    tick=time.perf_counter();rows=[];costs=[]
    for n in [1,2,3]:
        core=read(OUT/'reconstruction'/f'group{n:02d}'/'current_core.json')
        identity=read(OUT/core['group']['campaign']/'identity.json')
        native=list(csv.DictReader((OUT/'reconstruction'/f'group{n:02d}'/'controller_native.csv').open(encoding='utf-8')))
        clocks=list(csv.DictReader((OUT/'reconstruction'/f'group{n:02d}'/'time_partitions.csv').open(encoding='utf-8')))
        for a in core['arms']:
            calls=[c for c in native if c['arm']==a['arm']]
            costs.append(dict(id=core['group']['id'],arm=a['arm'],actual_Optimize=a['native_Optimize'],
                LP=sum(c['solve_kind']=='LP' for c in calls),MIP=sum(c['solve_kind']!='LP' for c in calls) if calls else a['native_Optimize'],
                unique_actual_scoped_models=len({c['model_sha256'] for c in calls}) if calls else a['native_Optimize'],
                time_partition=next(c for c in clocks if c['arm']==a['arm'])))
        launch=next(l for l in identity['launches'] if l['arm']=='MB-PC');d=Path(launch['destination'])
        events=[json.loads(s) for s in (d/'external/round119_events.jsonl').read_text(encoding='utf-8').splitlines()]
        observations=read(d/'observations.json');receipt=read(d/'producer_receipt.json');completion=read(d/'completion.json');end=read(d/'native_end_receipt.json')
        offset=end['complete_seconds_until_native_end']-completion['fully_observed_end_to_end_seconds']
        assert offset>=0
        for c in [e for e in events if e['kind']=='atomic_contraction_committed']:
            source=next(e for e in events if e['kind']=='paid_certificate_returned' and e['call']==c['proof_call'])
            request=next(e for e in events if e['kind']=='termination_requested' and source['sequence']<e['sequence']<c['sequence'])
            own=max((e for e in events if e['kind']=='own_verified' and e['sequence']<request['sequence']),key=lambda e:e['sequence'])
            returned=next(e for e in events if e['kind']=='native_returned' and e['call']==request['call'])
            assert source['process_seconds']<=own['process_seconds']<=request['process_seconds']<=returned['process_seconds']<=c['process_seconds']
            after=[o for o in observations if o['payload']['kind']=='call' and o['payload']['leaf']==c['new_leaf']]
            assert after
            new_lp=next(x for x in native if x['arm']=='MB-PC' and x['leaf_id']==c['new_leaf'] and x['solve_kind']=='LP')
            lp_status=list(csv.DictReader((OUT/'reconstruction'/f'group{n:02d}'/'controller_LP_status.csv').open(encoding='utf-8')))
            new_lp_bound=float(next(x for x in lp_status if x['arm']=='MB-PC' and x['leaf_id']==c['new_leaf'])['lower_bound'])
            rows.append(dict(id=core['group']['id'],source_call=source['call'],source_model=source['model'],source_scope=[source['lower'],source['upper']],
                source_cutoff=source['cutoff'],source_bound=source['bound'],source_registered_process_seconds=source['process_seconds'],
                own_verified_record_process_seconds=own['process_seconds'],own_U=own['U'],own_true_G=own['G_true'],integer_Y=own['Y'],
                termination_request_process_seconds=request['process_seconds'],actual_return_record_process_seconds=returned['process_seconds'],
                actual_return_status=returned['status'],actual_return_code=returned['return_code'],atomic_commit_process_seconds=c['process_seconds'],
                old_domain=[c['old_lower'],c['old_upper']],new_domain=[c['new_lower'],c['new_upper']],
                retained_width_ratio=(c['new_upper']-c['new_lower'])/(c['old_upper']-c['old_lower']),predicate_margin=c['margin'],
                old_left_LP=c['left_bound'],removed_right_LP=c['right_bound'],new_retained_root_LP=new_lp_bound,global_L_at_commit=c['global_L'],
                new_model=new_lp['model_sha256'],actual_subsequent_Optimize=[o['payload']['call'] for o in after],
                subsequent_requests=[dict(call=o['payload']['call'],model=o['payload']['model_sha256'],
                    request_record_data_close_process_seconds=o['data_close_seconds'],
                    first_external_observation_supervisor_seconds=o['effective_available_seconds'],
                    first_external_observation_T_produce_upper=o['effective_available_seconds']+offset) for o in after],
                rebuild_known_complete_by_next_request_record=True,exact_rebuild_start_or_Optimize_API_entry='unknown',
                Cpp_journal_and_event_clock='same processElapsedSeconds(options) origin',
                external_clock_conversion='inherited end-receipt offset; an observation upper bound, not internal first discovery',
                supervisor_to_producer_offset=offset,receipt_origin_perf=receipt['t0_perf'],
                U_initial_record_plus_strict_updates=sum(e['kind']=='own_verified' for e in events),
                strict_new_updates_after_initial=sum(e['kind']=='own_verified' for e in events)-1,
                one_used_strict_predicate_event=True,tree_cut_basis_migration_claim=False))
    write(OUT/'mechanism_account.json',dict(events=rows,costs=costs,Optimize=0,native_starts=0,
        engineering_seconds=time.perf_counter()-tick,causal_time_subtraction_or_unrun_counterfactual=False))
    print(json.dumps([dict(id=r['id'],source=r['source_registered_process_seconds'],own=r['own_verified_record_process_seconds'],
        request=r['termination_request_process_seconds'],returned=r['actual_return_record_process_seconds'],commit=r['atomic_commit_process_seconds'],
        new_LP=r['new_retained_root_LP']) for r in rows]),flush=True)
if __name__=='__main__':account()
