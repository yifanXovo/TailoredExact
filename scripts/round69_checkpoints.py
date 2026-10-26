"""Read-only common-horizon evidence from completed whole runs.

Intermediate P incumbents are native telemetry, not independently retained
physical witnesses. Final routes are never assigned to an earlier timestamp.
Unexplained process overhead is conservatively charged before all trace events.
"""
import math
import package_round69 as package
import round69_hga_provenance as provenance
run=package.run
audit=package.shared.analyze_round68

def conservative_frontier_trace(folder,overhead=0):
    trace=audit.rows(folder/'external/global_bound_trace.csv');adjustments=[]
    source='gurobi_cb_mip_objbnd_valid_native_bound'
    for row in trace:row['time']=float(row['process_elapsed_seconds'])+overhead
    index=0
    while index<len(trace):
        if trace[index]['event_source']!=source:
            index+=1;continue
        end=index
        while end<len(trace) and trace[end]['event_source']==source:end+=1
        assert end<len(trace),'Buffered native events need a subsequent real process-clock event'
        last=max(float(row['process_elapsed_seconds']) for row in trace[index:end])
        after=float(trace[end]['process_elapsed_seconds'])
        assert after+1e-7>=last,'Clock/order inconsistency requires review'
        # C++ adds callback-relative elapsed to the earlier solve launch. Its
        # missing setup offset is <= after-last. Charging the entire difference
        # before every callback event is conservative, including an unobserved
        # tail with no further bound improvements. No Gurobi Runtime assumption.
        shift=max(0,after-last)
        for row in trace[index:end]:row['time']+=shift
        adjustments.append(dict(first_data_row=index+1,last_data_row=end,
            leaf=trace[index]['active_leaf'],recorded_last_callback_process_seconds=last,
            following_actual_process_seconds=after,following_event=trace[end]['event_type'],
            conservative_setup_and_unobserved_tail_shift_seconds=shift,callback_records=end-index))
        index=end
    return trace,adjustments

def main():
    package.bind()
    assert not (run.OUT/'active_run.lock').exists()
    records=[];adjustments_all=[]
    for entry in run.runner.entries():
        if not entry['charged'] or entry['id'] not in ['D6','D7']:continue
        folder=run.ROOT/entry['destination']
        if not (folder/'completion.json').exists():continue
        done=run.read(folder/'completion.json');result=run.read(folder/'result.json')
        assert done['returncode']==0 and not done['watchdog'] and done['within_budget']
        wall=done['wall_seconds'];internal=result['final_process_wall_time_seconds']
        overhead=max(0,wall-internal)
        if entry['arm']=='P-GRB':
            phases=audit.rows(folder/'phases.csv')
            launch=next(float(p['process_seconds']) for p in phases if p['event']=='plain_gurobi_optimize_launch')
            trace=audit.rows(run.ROOT/result['gurobi_progress_path'])
            # telemetry_start is constructed before optimize_launch in the
            # frozen source. Adding launch is a conservative time overestimate.
            trace=[dict(row,time=launch+float(row['elapsed_runtime_seconds'])+overhead)
                for row in trace if row['context']!='solver_final']
            for row in trace:
                if row['best_bound_available']=='true':
                    value=float(row['best_bound'])
                    assert math.isfinite(value) and value<=result['upper_bound']+1e-7,'Historical P bound exceeds a verified feasible objective'
            initial=None;initial_time=None;linked=None
        else:
            trace,adjustments=conservative_frontier_trace(folder,overhead)
            for row in trace:
                value=float(row['valid_global_lower_bound'])
                assert math.isfinite(value) and value<=result['upper_bound']+1e-7,'Historical frontier bound exceeds a verified feasible objective'
                assert value<=float(row['verified_global_upper_bound'])+1e-7,'Historical frontier bound/UB inconsistency'
            adjustments_all.extend(dict(number=entry['charged_number'],id=entry['id'],arm=entry['arm'],**r)
                for r in adjustments)
            initial=run.read(folder/'external/initial_witness.json')
            initial=audit.physical_module.physical(run.panel()[entry['id']],initial)['F']
            initial_time=next(row['time'] for row in trace if row['event_type']=='exact_tree_initialization')
            linked=provenance.link(folder,run.panel()[entry['id']],result,overhead)
            if linked['linked']:initial_time=min(initial_time,linked['conservative_publication_process_seconds'])
        assert all(a['time']<=b['time']+1e-7 for a,b in zip(trace,trace[1:]))
        for horizon in [300,600,1200,1800,2400,3600]:
            if horizon>entry['cap_seconds']:continue
            eligible=[row for row in trace if row['time']<=horizon]
            record=dict(number=entry['charged_number'],id=entry['id'],arm=entry['arm'],
                run_cap=entry['cap_seconds'],checkpoint=horizon,conservative_overhead_shift=overhead,
                trace_event_count=len(eligible),trace_last_time=eligible[-1]['time'] if eligible else None,
                final_witness_backdated=False,certificate=False)
            if wall<=horizon:
                upper=result['upper_bound'];lower=result['lower_bound']
                record.update(verified_retained_UB=upper,comparison_UB=upper,LB=lower,
                    certificate=result['strict_certified_original_problem'],
                    UB_scope='Completed run: independently checked final routes',LB_scope='Completed full original-problem bound',
                    completed_wall=wall)
            elif entry['arm']=='P-GRB':
                incumbents=[float(r['incumbent']) for r in eligible if r['incumbent_available']=='true']
                bounds=[float(r['best_bound']) for r in eligible if r['best_bound_available']=='true']
                upper=min(incumbents) if incumbents else None;lower=max([0.0]+bounds)
                record.update(verified_retained_UB=None,comparison_UB=upper,LB=lower,
                    UB_scope='Native incumbent telemetry; no complete intermediate vector retained',
                    LB_scope='Original compact MIP callback bound')
            else:
                bounds=[float(r['valid_global_lower_bound']) for r in eligible]
                upper=initial if initial_time<=horizon else None;lower=max([0.0]+bounds)
                record.update(verified_retained_UB=upper,comparison_UB=upper,LB=lower,
                    algorithm_reported_verified_UB=float(eligible[-1]['verified_global_upper_bound']) if eligible else None,
                    UB_scope='Retained initial witness linked by full hash to its verified HGA event; conservative generation-completion timestamp' if upper is not None and linked['linked'] else ('Retained initial witness available after exact initialization' if upper is not None else 'No retained contemporaneous witness supplied'),
                    initial_witness_available_by=initial_time,
                    hga_full_route_hash=linked.get('canonical_full_route_sha256'),
                    LB_scope='Complete-frontier trace, or mathematical nonnegative bound before exact initialization')
            assert math.isfinite(lower)
            if upper is not None:
                assert math.isfinite(upper) and lower<=upper+1e-7
                record['signed_gap']=upper-lower
                record['relative_gap']=(upper-lower)/abs(upper) if upper else None
            else:
                record['signed_gap']=None
                record['relative_gap']=None
            records.append(record)
    audit.table('within_run_checkpoints.csv',records)
    run.write(run.OUT/'frontier_time_adjustments.json',dict(adjustments=adjustments_all,optimizer_calls=0,
        method='Shift each buffered native-bound group so its last recorded improvement coincides with the subsequent actual process-clock event; this upper-bounds missing setup plus an unobserved tail',
        effect='Conservative intermediate availability only. Whole-run endpoints, solver source, parameters and completed wall costs are unchanged.'))
    run.write(run.OUT/'checkpoint_scope.json',dict(script_sha256=run.sha(__file__),optimizer_calls=0,
        records=len(records),final_witness_backdated=False,
        all_historical_LB_checked_against_final_verified_UB=True,
        relative_gap_definition='(UB-LB)/abs(UB) for an available nonzero UB; otherwise unavailable. Signed numerical discrepancies are preserved.',
        timing='Process trace plus nonnegative external-minus-internal wall overhead up front. Buffered frontier callbacks additionally receive a conservative setup/tail shift. P callbacks use optimize launch after their epoch.',
        comparison='Intermediate P UB is native telemetry. Candidate initial routes require full-hash event linkage and conservative publication time, or exact initialization. Objective equality alone never supplies a historical witness. Full-run endpoints are independently verified.'))
    print('Common-horizon records',len(records),'no optimizer calls')

if __name__=='__main__':main()
