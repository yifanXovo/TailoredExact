"""Link an initial retained route to its historical verified HGA event.

Objective equality alone is never sufficient. The canonical full route hash
must match both the published event and the retained-candidate result field.
Generation completion gives a conservative publication timestamp after the
synchronous verifier/copy callback has returned.
"""
import hashlib
import package_round69 as package
run=package.run
audit=package.shared.analyze_round68

def candidate_hash(witness):
    parts=[]
    for route in sorted(witness['routes'],key=lambda r:r['vehicle']):
        operations=[]
        for op in route['operations']:
            operations.append((op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else tuple(op))
        parts.append('v='+str(route['vehicle'])+';nodes='+''.join(str(i)+',' for i in route['nodes'])+
            ';ops='+''.join(':'.join(map(str,op))+',' for op in sorted(operations))+'|')
    return hashlib.sha256(''.join(parts).encode('ascii')).hexdigest()

def link(folder,p,result,overhead=0):
    witness=run.read(folder/'external/initial_witness.json')
    physical=audit.physical_module.physical(p,witness)
    digest=candidate_hash(witness)
    if result.get('hga_candidate_observer_failed') or not result.get('hga_retained_verified_event_candidate'):
        return dict(linked=False,reason='No qualified retained event path')
    if digest!=result.get('hga_retained_candidate_sha256'):
        return dict(linked=False,reason='Full route hash differs from retained HGA hash')
    events=[r for r in audit.rows(folder/'hga_events.csv') if r['published']=='1' and
        r['verifier_passed']=='1' and r['content_sha256']==digest]
    if not events:return dict(linked=False,reason='No matching published full-content hash')
    event=events[0];assert abs(float(event['objective'])-physical['F'])<=1e-7
    generations=audit.rows(folder/'hga.csv')
    if not generations:return dict(linked=False,reason='No generation-completion trace')
    generation=int(event['generation'])
    point=next((r for r in generations if int(r['generation'])==generation),None)
    assert point is not None
    elapsed=[float(r['elapsed_seconds']) for r in generations]
    assert all(a<=b for a,b in zip(elapsed,elapsed[1:]))
    phases=audit.rows(folder/'phases.csv')
    completed=next(float(r['process_seconds']) for r in phases if r['event']=='hga_generation_loop_complete')
    epoch_upper=completed-elapsed[-1]
    assert epoch_upper>=0
    published_upper=epoch_upper+float(point['elapsed_seconds'])+overhead
    assert 0<=published_upper<=completed+overhead+1e-7
    return dict(linked=True,canonical_full_route_sha256=digest,witness_sha256=run.sha(folder/'external/initial_witness.json'),
        event_generation=generation,event_objective=float(event['objective']),independent_F=physical['F'],
        conservative_publication_process_seconds=published_upper,conservative_ga_epoch_process_seconds=epoch_upper,
        event_generation_end_elapsed_seconds=float(point['elapsed_seconds']),last_generation_end_elapsed_seconds=elapsed[-1],
        loop_complete_process_seconds=completed,external_overhead_shift=overhead,
        event_source_seconds=float(event['source_elapsed_seconds']),
        timing_scope='Generation end after synchronous publication; GA epoch upper-bounded by loop-complete phase minus last generation elapsed, plus full external overhead',
        witness_scope='Complete retained initial route hash linked to contemporaneous published/verified event; no native final witness backdating')

def main():
    package.bind();records=[]
    for entry in run.runner.entries():
        folder=run.ROOT/entry['destination']
        if not entry['charged'] or entry['arm']=='P-GRB' or not (folder/'completion.json').exists():continue
        if not (folder/'external/initial_witness.json').exists():continue
        result=run.read(folder/'result.json');done=run.read(folder/'completion.json')
        assert done['returncode']==0 and not done['watchdog']
        overhead=max(0,done['wall_seconds']-result['final_process_wall_time_seconds'])
        records.append(dict(number=entry['charged_number'],id=entry['id'],arm=entry['arm'],
            **link(folder,run.panel()[entry['id']],result,overhead)))
    run.write(run.OUT/'hga_witness_provenance.json',dict(records=records,optimizer_calls=0,script_sha256=run.sha(__file__),
        scope='Content and conservative publication-time checks; no assertion that an early objective alone identifies a route'))
    print('HGA full-route provenance',sum(r['linked'] for r in records),'of',len(records),'linked; no optimizer calls')

if __name__=='__main__':main()
