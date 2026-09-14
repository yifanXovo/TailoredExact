"""Compact paired gates from independently verified Round65 runs; no optimizer."""
import csv,itertools
import verify_round65 as audit
from round65_research import OUT,RAW,read

def main():
    runs=audit.rows(OUT/'runs.csv');pairs=[];prefixes=[]
    groups={}
    for r in runs:
        if r.get('failure')=='True':continue
        groups.setdefault((r['id'],r['stage'],r['build'],r['cap']),{})[r['arm']]=r
    proposed=[('bounded','proof'),('bounded','sparse'),('proof','sparse'),
              ('cold-bounded','cold-proof'),('cold-bounded','cold-sparse'),
              ('bounded','seed-bounded'),('seed-bounded','seed-proof'),
              ('seed-bounded','seed-proof-free'),('seed-proof','seed-proof-free'),
              ('seed-proof-free','seed-sparse-free'),('cold-seed-bounded','cold-seed-proof-free'),
              ('joint','seed-bounded-joint'),('joint','bounded-joint'),
              ('off','reliable'),('K1-H','candidate'),('P-GRB','candidate')]
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
            f0=RAW/stage/identity/a/'hga.csv';f1=RAW/stage/identity/b/'hga.csv'
            h0,h1=audit.rows(f0),audit.rows(f1)
            if h0 and h1:
                keys=['generation','best_fitness','strict_improvement'];n=min(len(h0),len(h1))
                equal=all(all(u[k]==v[k] for k in keys) for u,v in zip(h0,h1))
                prefixes.append(dict(id=identity,stage=stage,control=a,candidate=b,control_rows=len(h0),candidate_rows=len(h1),
                                     common_prefix=n,identical_common_logical_prefix=equal))
    audit.table('pairs.csv',pairs);audit.table('all_hga_prefixes.csv',prefixes)
    print('paired comparisons',len(pairs),'HGA comparisons',len(prefixes))
if __name__=='__main__':main()
