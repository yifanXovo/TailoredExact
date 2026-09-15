"""Reuse conservative whole-run checkpoint logic with a DS publication clock.

No optimizer calls. Every legacy module binding is explicitly redirected;
the historical stage is never written. DS generation0 is not a time source.
"""
from types import SimpleNamespace
import round69_checkpoints as inherited
import round69_hga_provenance as hga
import package_round71 as package

run=package.run
audit=package.shared.analyze_round68

def link(folder,p,result,overhead=0):
    if not result.get('hga_stop_mode','').startswith('decoded-descent'):
        return hga.link(folder,p,result,overhead)
    witness=run.read(folder/'external/initial_witness.json')
    digest=package.route_hash(witness)
    physical=audit.physical_module.physical(p,witness)
    if result.get('hga_candidate_observer_failed') or not result.get('hga_retained_verified_event_candidate'):
        return dict(linked=False,reason='No qualified retained event path')
    if digest!=result.get('hga_retained_candidate_sha256'):
        return dict(linked=False,reason='Full route hash differs from retained candidate hash')
    events=[r for r in audit.rows(folder/'hga_events.csv') if r['published']=='1' and r['verifier_passed']=='1' and r['content_sha256']==digest]
    if not events:return dict(linked=False,reason='No matching full-content published event')
    assert abs(float(events[0]['objective'])-physical['F'])<=1e-7
    assert int(events[0]['generation'])==0
    # The synchronous publication/physical verification callback has returned
    # before the bridge emits this process-clock event. Charging all unexplained
    # external overhead first only delays availability. No final route is used.
    phases=audit.rows(folder/'phases.csv')
    completed=next(float(r['process_seconds']) for r in phases if r['event']=='decoded_descent_complete')
    return dict(linked=True,canonical_full_route_sha256=digest,
        conservative_publication_process_seconds=completed+overhead,
        witness_sha256=run.sha(folder/'external/initial_witness.json'),
        timing_scope='Full retained DS witness available by decoded_descent_complete after synchronous verifier; generation0 is unused')

def main():
    package.bind();run.assert_frozen()
    inherited.package=package;inherited.run=run;inherited.audit=audit
    hga.run=run;hga.audit=audit
    inherited.provenance=SimpleNamespace(link=link)
    entries=run.runner.entries()
    startup=[]
    for entry in entries:
        folder=run.ROOT/entry['destination']
        if not entry['charged'] or not (folder/'completion.json').exists():continue
        result=run.read(folder/'result.json')
        if package.startup_deadline.matches(result):startup.append((entry,folder,result))
    excluded={entry['charged_number'] for entry,_,_ in startup}
    original_entries=run.runner.entries
    try:
        # The legacy helper requires a started exact frontier. Keep its checks
        # intact and qualify the separate no-proof deadline case below.
        run.runner.entries=lambda:[e for e in entries if e.get('charged_number') not in excluded]
        inherited.main()
    finally:run.runner.entries=original_entries
    records=audit.rows(run.OUT/'within_run_checkpoints.csv')
    for r in records:
        if 'hga_full_route_hash' in r:r['startup_full_route_sha256']=r.pop('hga_full_route_hash')
        if r['arm'] in ['DS','DS-X'] and 'generation-completion' in r.get('UB_scope',''):
            r['UB_scope']='Retained DS initial witness linked by full hash to verified event; conservative decoded_descent_complete timestamp'
    for entry,folder,result in startup:
        checked=package.startup_deadline.check(folder,run.panel()[entry['id']],result,run,audit,package.route_hash)
        done=run.read(folder/'completion.json');wall=done['wall_seconds']
        overhead=max(0,wall-result['final_process_wall_time_seconds'])
        available=checked['conservative_witness_available_by']+overhead
        for horizon in [300,600,1200,1800,2400,3600]:
            if horizon>entry['cap_seconds']:continue
            upper=result['upper_bound'] if horizon>=available else None
            records.append(dict(number=entry['charged_number'],id=entry['id'],arm=entry['arm'],
                run_cap=entry['cap_seconds'],checkpoint=horizon,conservative_overhead_shift=overhead,
                trace_event_count=0,trace_last_time=None,final_witness_backdated=False,certificate=False,
                verified_retained_UB=upper,comparison_UB=upper,LB=0,
                UB_scope='Completed startup-only run: independently checked retained HGA routes' if wall<=horizon else 'No earlier availability inferred for the retained startup-deadline witness',
                LB_scope='Universal nonnegative objective on the full original domain; exact proof never started',
                signed_gap=upper,relative_gap=1 if upper is not None else None,
                completed_wall=wall if wall<=horizon else None,initial_witness_available_by=available,
                startup_full_route_sha256=checked['full_retained_route_sha256']))
    records.sort(key=lambda r:(int(r['number']),int(r['checkpoint'])))
    audit.table('within_run_checkpoints.csv',records)
    scope=run.read(run.OUT/'checkpoint_scope.json')
    scope.update(round71_wrapper_sha256=run.sha(__file__),hga_provenance_helper_sha256=run.sha(hga.__file__),
        records=len(records),startup_deadline_runs=len(startup),
        current_package_sha256=run.sha(package.__file__),
        DS_clock='Synchronous verified-event hash plus decoded_descent_complete phase, never generation0',
        horizons='300/600 for D6 and300/600/1200 for D7; no new run or internal stopping rule',
        limitation='Intermediate P UB is native telemetry; candidate early UB is only the retained initial physical witness. Conservative buffered-bound shifts can understate early progress and differ across arms. Only final endpoints enter performance pairs.')
    run.write(run.OUT/'checkpoint_scope.json',scope)

if __name__=='__main__':main()
