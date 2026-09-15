"""Small completed-run HGA event attribution, never a replayed stopping rule."""
import package_round69 as package
import round69_hga_provenance as provenance
import hashlib,json
run=package.run
audit=package.shared.analyze_round68

def main():
    package.bind();records=[]
    for entry in run.runner.entries():
        folder=run.ROOT/entry['destination']
        if not entry['charged'] or entry['arm']=='P-GRB' or not (folder/'completion.json').exists():continue
        result=run.read(folder/'result.json');done=run.read(folder/'completion.json')
        assert done['returncode']==0 and not done['watchdog']
        witness=run.read(folder/'external/initial_witness.json')
        initial=witness.get('F',witness.get('objective'))
        events=[r for r in audit.rows(folder/'hga_events.csv') if r['published']=='1' and r['verifier_passed']=='1']
        matching=[r for r in events if abs(float(r['objective'])-initial)<=1e-12]
        event=matching[0] if matching else None
        hga=result['hga_wall_time_seconds']
        generations=audit.rows(folder/'hga.csv')
        logical_trace=[[r[k] for k in ['generation','best_fitness','strict_improvement']]
            for r in generations]
        logical_hash=hashlib.sha256(json.dumps(logical_trace,separators=(',',':')).encode('ascii')).hexdigest()
        linked=provenance.link(folder,run.panel()[entry['id']],result,
            max(0,done['wall_seconds']-result['final_process_wall_time_seconds']))
        records.append(dict(number=entry['charged_number'],id=entry['id'],arm=entry['arm'],
            full_wall=done['wall_seconds'],hga_wall=hga,post_hga_wall=done['wall_seconds']-hga,
            hga_total_generations=result['hga_total_generations'],hga_decoder_calls=result['hga_decoder_calls'],
            logical_trace_sha256=logical_hash,
            retained_route_sha256=linked.get('canonical_full_route_sha256'),
            hga_share=hga/done['wall_seconds'],initial_verified_objective=initial,
            published_events=len(events),first_event_with_same_objective_generation=int(event['generation']) if event else None,
            first_event_with_same_objective_seconds=float(event['source_elapsed_seconds']) if event else None,
            remaining_hga_after_that_event=hga-float(event['source_elapsed_seconds']) if event else None,
            first_event_hash=event['content_sha256'] if event else None,
            early_identical_route_not_established=not linked['linked'],
            retained_route_linked_generation=linked.get('event_generation'),
            retained_route_available_by=linked.get('conservative_publication_process_seconds'),
            first_same_objective_event_is_retained_route=event['content_sha256']==linked.get('canonical_full_route_sha256') if event else None,
            scope='Observed same-objective event; no counterfactual algorithm or timing gain claimed'))
    audit.table('startup_telemetry.csv',records)
    pairs=[]
    for identity in sorted({r['id'] for r in records}):
        arms={r['arm']:r for r in records if r['id']==identity}
        if not {'K1-R','VD-S'}<=arms.keys():continue
        a,b=arms['K1-R'],arms['VD-S']
        pairs.append(dict(id=identity,k1_hga_wall=a['hga_wall'],vds_hga_wall=b['hga_wall'],
            vds_over_k1_wall=b['hga_wall']/a['hga_wall'],
            same_total_generations=a['hga_total_generations']==b['hga_total_generations'],
            same_decoder_calls=a['hga_decoder_calls']==b['hga_decoder_calls'],
            k1_decoder_calls=a['hga_decoder_calls'],vds_decoder_calls=b['hga_decoder_calls'],
            same_generation_best_trace=a['logical_trace_sha256']==b['logical_trace_sha256'],
            same_retained_routes=a['retained_route_sha256']==b['retained_route_sha256'],
            logical_trace_sha256=b['logical_trace_sha256']))
    run.write(run.OUT/'hga_timing_pairs.json',dict(pairs=pairs,optimizer_calls=0,
        hash_encoding='SHA256 of compact ASCII JSON arrays of generation,best_fitness,strict_improvement strings in file order; elapsed times excluded',
        scope='Observed completed-run timing attribution. Matching counts/best-history/routes do not reveal all offspring or establish a cause. All actual wall remains paid; no counterfactual correction.'))
    print('Completed HGA telemetry',len(records),'no optimizer calls; attribution only')

if __name__=='__main__':main()
