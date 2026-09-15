"""Paid startup attribution from completed results; no model scan or optimizer."""
import csv,hashlib,json
import package_round71 as package
run=package.run

def main():
    package.bind();records=[];hga=[]
    for e in run.runner.entries():
        folder=run.ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists():continue
        result=run.read(folder/'result.json');done=run.read(folder/'completion.json')
        initial=folder/'external/initial_witness.json'
        witness=run.read(initial) if initial.exists() else None
        deadline=package.startup_deadline.matches(result)
        if deadline:witness=result
        records.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],kind=e['kind'],
            paid_wall=done['wall_seconds'],startup_wall=result.get('hga_wall_time_seconds',0),
            initial_UB=witness.get('F',witness.get('objective')) if witness else None,
            startup_witness_scope='Retained HGA deadline result before proof; no initial tree witness exists' if deadline else 'Initial exact-phase witness when present',
            final_UB=result['upper_bound'],global_LB=result['lower_bound'],certificate=result['strict_certified_original_problem'],
            total_HGA_generations=result.get('hga_total_generations',0),
            uncached_decoder_calls=result.get('hga_decoder_calls',0),
            descent_complete=result.get('decoded_descent_complete',False),
            completed_seeds=result.get('decoded_descent_seeds_completed',0),
            descent_passes=result.get('decoded_descent_passes',0),
            descent_checks_including_cache_hits=result.get('decoded_descent_checks',0),
            cross_route_enabled=result.get('decoded_descent_cross_route_enabled',False),
            cross_route_neighbors=result.get('decoded_descent_cross_route_neighbors',0),
            cross_route_checks=result.get('decoded_descent_cross_route_checks',0),
            cross_route_moves=result.get('decoded_descent_cross_route_moves',0),
            initial_route_sha256=result.get('hga_retained_candidate_sha256'),result_sha256=run.sha(folder/'result.json')))
        if e['arm'] in ['VD-S','K1-R'] and witness:
            with (folder/'hga.csv').open(encoding='utf-8') as f:trace=list(csv.DictReader(f))
            logical=[[r[k] for k in ['generation','best_fitness','strict_improvement']] for r in trace]
            hga.append(dict(id=e['id'],arm=e['arm'],wall=result['hga_wall_time_seconds'],
                search_completed=not deadline,
                generations=result['hga_total_generations'],decodes=result['hga_decoder_calls'],
                route_sha256=package.route_hash(witness),
                logical_trace_sha256=hashlib.sha256(json.dumps(logical,separators=(',',':')).encode('ascii')).hexdigest()))
    if records:
        with (run.OUT/'startup_attribution.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    run.write(run.OUT/'startup_attribution_scope.json',dict(script_sha256=run.sha(__file__),optimizer_calls=0,
        scope='Attribution only: startup is never subtracted from formal paid wall. DS checks include cached decodes; uncached decoder calls are separate. Initial and final U may differ.'))
    pairs=[]
    for identity in sorted({r['id'] for r in hga}):
        arms={r['arm']:r for r in hga if r['id']==identity}
        if not {'VD-S','K1-R'}<=arms.keys():continue
        a,b=arms['K1-R'],arms['VD-S']
        pairs.append(dict(id=identity,k1_hga_wall=a['wall'],vds_hga_wall=b['wall'],vds_over_k1_wall=b['wall']/a['wall'],
            both_searches_completed=a['search_completed'] and b['search_completed'],
            k1_search_completed=a['search_completed'],vds_search_completed=b['search_completed'],
            k1_decoder_calls=a['decodes'],vds_decoder_calls=b['decodes'],same_total_generations=a['generations']==b['generations'],
            same_decoder_calls=a['decodes']==b['decodes'],same_generation_best_trace=a['logical_trace_sha256']==b['logical_trace_sha256'],
            same_full_initial_routes=a['route_sha256']==b['route_sha256'],logical_trace_sha256=b['logical_trace_sha256']))
    run.write(run.OUT/'hga_timing_pairs.json',dict(pairs=pairs,optimizer_calls=0,script_sha256=run.sha(__file__),
        scope='HGA arms only, with completion/censoring explicit. Matching generations/uncached calls/best-history/full routes do not reveal all offspring or prove timing stability. Ratios involving interrupted searches are paid-cost ratios, not equal-work timing comparisons. Actual wall is never corrected.'))

if __name__=='__main__':main()
