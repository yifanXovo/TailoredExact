"""Compact paired gates from independently verified Round65 runs; no optimizer."""
import csv,itertools,math
import verify_round65 as audit
from round65_research import OUT,RAW,read,sha

def main():
    runs=audit.rows(OUT/'runs.csv');pairs=[];prefixes=[];states=[];zero_events=[];timings=[]
    groups={}
    for r in runs:
        if r.get('failure')=='True':continue
        groups.setdefault((r['id'],r['stage'],r['build'],r['cap']),{})[r['arm']]=r
    proposed=[('bounded','proof'),('bounded','sparse'),('proof','sparse'),
              ('cold-bounded','cold-proof'),('cold-bounded','cold-sparse'),
              ('bounded','seed-bounded'),('seed-bounded','seed-proof'),
              ('seed-bounded','seed-proof-free'),('seed-proof','seed-proof-free'),
              ('seed-proof-free','seed-sparse-free'),('cold-seed-bounded','cold-seed-proof-free'),
              ('cold-off','cold-seed-bounded'),
              ('joint','seed-bounded-joint'),('joint','bounded-joint'),
              ('off','reliable'),('K1-H','candidate'),('P-GRB','candidate'),('joint','candidate')]
    for (identity,stage,build,cap),group in groups.items():
        for a,b in proposed:
            if a not in group or b not in group:continue
            x,y=group[a],group[b];tx,ty=float(x['wall']),float(y['wall']);gx,gy=float(x['gap']),float(y['gap'])
            cx,cy=x['certificate']=='True',y['certificate']=='True'
            time_delta=tx-ty;gap_delta=gx-gy
            time_gate=abs(time_delta)>=10 and abs(time_delta)>=.1*tx
            gap_gate=abs(gap_delta)>=.001 and abs(gap_delta)>=.05*gx
            outcome=('certificate_gain' if cy else 'certificate_loss') if cx!=cy else (
                ('time_gain' if time_delta>0 else 'time_loss') if cx and time_gate else
                ('gap_gain' if gap_delta>0 else 'gap_loss') if not cx and gap_gate else 'below_dual_gates')
            pairs.append(dict(id=identity,stage=stage,build=build,cap=cap,control=a,candidate=b,
                              control_number=x['number'],candidate_number=y['number'],control_cert=cx,candidate_cert=cy,
                              control_wall=tx,candidate_wall=ty,control_gap=gx,candidate_gap=gy,
                              time_saved=time_delta,gap_reduced=gap_delta,outcome=outcome,
                              native_calls_control=x['optimizer_calls'],native_calls_candidate=y['optimizer_calls']))
            p0,p1=RAW/stage/identity/a,RAW/stage/identity/b
            w0,w1=p0/'external/initial_witness.json',p1/'external/initial_witness.json'
            d0,d1=p0/'external/initial_decomposition_ledger.csv',p1/'external/initial_decomposition_ledger.csv'
            if w0.exists() and w1.exists() and int(x['native_calls']) and int(y['native_calls']):
                assert w0.read_bytes()==w1.read_bytes(),('startup route mismatch',identity,stage,a,b)
                assert d0.read_bytes()==d1.read_bytes(),('initial coverage mismatch',identity,stage,a,b)
                c0,c1=audit.rows(p0/'external/paper_optimize_ledger.csv'),audit.rows(p1/'external/paper_optimize_ledger.csv')
                same_formulation_required=(a,b)!=('joint','candidate')
                same_model=c0[0]['model_sha256']==c1[0]['model_sha256']
                if same_formulation_required:assert same_model,('initial canonical model mismatch',identity,stage,a,b)
                states.append(dict(id=identity,stage=stage,control=a,candidate=b,identical_startup_routes_U=True,
                                   identical_initial_coverage=True,identical_initial_canonical_model=same_model,
                                   same_formulation_required=same_formulation_required))
            f0=RAW/stage/identity/a/'hga.csv';f1=RAW/stage/identity/b/'hga.csv'
            h0,h1=audit.rows(f0),audit.rows(f1)
            if h0 and h1:
                keys=['generation','best_fitness','strict_improvement'];n=min(len(h0),len(h1))
                equal=all(all(u[k]==v[k] for k in keys) for u,v in zip(h0,h1))
                prefixes.append(dict(id=identity,stage=stage,control=a,candidate=b,control_rows=len(h0),candidate_rows=len(h1),
                                     common_prefix=n,identical_common_logical_prefix=equal))
    for r in runs:
        if r.get('failure')=='True':continue
        folder=RAW/r['stage']/r['id']/r['arm']
        events=audit.rows(folder/'hga_events.csv');phases=audit.rows(folder/'phases.csv')
        event=next((e for e in events if e['verifier_passed']=='1' and 0<=float(e['objective'])<=1e-12),None)
        if not event:continue
        phase=lambda name:next((float(p['process_seconds']) for p in phases if p['event']==name),None)
        ub=next((e for e in audit.rows(folder/'ub_events.csv') if e['accepted']=='true' and 0<=float(e['objective'])<=1e-12),None)
        zero_events.append(dict(number=r['number'],id=r['id'],arm=r['arm'],generation=event['generation'],
            complete_cached_decode_event_HGA_seconds=event['source_elapsed_seconds'],
            separate_decode_seconds='individual winning-decode duration not exported; aggregate timing is a separate diagnostic',
            original_verifier_seconds=event['verification_seconds'],published_verified_memory=event['published'],
            zero_certificate_process_seconds=phase('round65_verified_zero'),
            hga_loop_complete_process_seconds=phase('hga_generation_loop_complete'),
            final_UB_publication_process_seconds=ub['time_seconds'] if ub else None,
            result_serialization_complete_process_seconds=phase('final_result_serialization_complete'),
            process_exit_seconds=phase('process_exit'),wall_seconds=r['wall']))
    audit.table('pairs.csv',pairs);audit.table('all_hga_prefixes.csv',prefixes)
    audit.table('paired_initial_states.csv',states)
    audit.table('zero_event_phases.csv',zero_events)
    for r in runs:
        if r.get('stage') not in ['timing_v5','timing_decoder_v5'] or r.get('failure')=='True':continue
        folder=RAW/r['stage']/r['id']/r['arm'];timing=read(folder/'hga_timing.json')
        assert timing['optimizer_calls']==0 and r['optimizer_calls']=='0'
        assert all(math.isfinite(v) and v>=0 for k,v in timing.items() if k.endswith('seconds'))
        control,a=audit.timing_reference(r['id']);b=audit.rows(folder/'hga.csv')
        keys=['generation','best_fitness','strict_improvement']
        assert len(a)==len(b) and all(all(x[k]==y[k] for k in keys) for x,y in zip(a,b)),('timing changed HGA trajectory',r['id'])
        measured=dict(timing);enabled=r['stage']=='timing_decoder_v5'
        measured['decoder_counter_available']=enabled
        measured['decoder_seconds_raw']=timing['decoder_seconds']
        measured['decoder_seconds']=timing['decoder_seconds'] if enabled else None
        if enabled:assert timing['decoder_seconds']>0
        timings.append(dict(number=r['number'],id=r['id'],wall_seconds=r['wall'],
                            reference_trajectory=str(control),reference_trajectory_sha256=sha(control),
                            identical_complete_logical_prefix=True,**measured))
    audit.table('hga_timing_summary.csv',timings)
    # A cause check for observed cross-build HGA wall variation, never a
    # cross-build performance pairing or input to policy selection.
    old=next((r for r in runs if r['id']=='C5' and r['stage']=='reliability_v1' and r['arm']=='off'),None)
    new=next((r for r in runs if r['id']=='C5' and r['stage']=='protection_v5' and r['arm']=='K1-H'),None)
    if old and new:
        a=audit.rows(RAW/'reliability_v1/C5/off/hga.csv');b=audit.rows(RAW/'protection_v5/C5/K1-H/hga.csv')
        assert a and b and audit.hga_logical_digest(a)==audit.hga_logical_digest(b)
        event=next(e for e in audit.rows(RAW/'protection_v5/C5/candidate/hga_events.csv')
                   if e['verifier_passed']=='1' and 0<=float(e['objective'])<=1e-12)
        generation=event['generation']
        found=lambda items:next(e['elapsed_seconds'] for e in items if e['generation']==generation)
        audit.table('hga_wall_variation.csv',[dict(control_number=old['number'],current_number=new['number'],
            scope='cross-build cause check only; not performance attribution',identical_complete_logical_trace=True,
            records=len(a),verified_zero_generation=generation,old_zero_generation_seconds=found(a),
            current_zero_generation_seconds=found(b),old_last_generation_seconds=a[-1]['elapsed_seconds'],
            current_last_generation_seconds=b[-1]['elapsed_seconds'],cause='unidentified timing variation after zero discovery')])
    print('paired comparisons',len(pairs),'HGA comparisons',len(prefixes))
if __name__=='__main__':main()
