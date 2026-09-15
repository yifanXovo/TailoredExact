"""Paid startup attribution from completed results; no model scan or optimizer."""
import csv
import round70_research_v2 as run

def main():
    records=[]
    for e in run.runner.entries():
        folder=run.ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists():continue
        result=run.read(folder/'result.json');done=run.read(folder/'completion.json')
        initial=folder/'external/initial_witness.json'
        witness=run.read(initial) if initial.exists() else None
        records.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],kind=e['kind'],
            paid_wall=done['wall_seconds'],startup_wall=result.get('hga_wall_time_seconds',0),
            initial_UB=witness.get('F',witness.get('objective')) if witness else None,
            final_UB=result['upper_bound'],global_LB=result['lower_bound'],certificate=result['strict_certified_original_problem'],
            total_HGA_generations=result.get('hga_total_generations',0),
            uncached_decoder_calls=result.get('hga_decoder_calls',0),
            descent_complete=result.get('decoded_descent_complete',False),
            completed_seeds=result.get('decoded_descent_seeds_completed',0),
            descent_passes=result.get('decoded_descent_passes',0),
            descent_checks_including_cache_hits=result.get('decoded_descent_checks',0),
            initial_route_sha256=result.get('hga_retained_candidate_sha256'),result_sha256=run.sha(folder/'result.json')))
    if records:
        with (run.OUT/'startup_attribution.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    run.write(run.OUT/'startup_attribution_scope.json',dict(script_sha256=run.sha(__file__),optimizer_calls=0,
        scope='Attribution only: startup is never subtracted from formal paid wall. DS checks include cached decodes; uncached decoder calls are separate. Initial and final U may differ.'))

if __name__=='__main__':main()
