"""One predeclared bounded conflict attempt, after inventory-time diagnostics."""
import ast
import csv
import json
import math
import re
from round61_research import ROOT, OUT, RAW, panel, oracle_one, sha, write

def read(p): return json.loads(p.read_text(encoding='utf-8'))

def proved(r):
    return r['classification'] in ['original_T_strictly_infeasible',
        'LP_infeasible_time_independent','MIP_infeasible_time_independent']

def main():
    if (OUT/'conflict_result.json').exists(): raise RuntimeError('conflict already completed')
    histories={x['id']:x for x in read(ROOT/'results/gf_verified_candidate_native_round60/fixed_inventory_selection.json')}
    candidates=[]
    for identity in ['D3','D4','D6']:
        for mode in ['lp','mip']:
            rr=read(RAW/'oracle_history'/identity/mode/'oracle_result.json')
            if proved(rr): candidates.append((math.inf if rr['time_independent_infeasible'] else rr['lower']/rr['T_original'],identity,mode,rr))
    if not candidates:
        write(OUT/'conflict_result.json',dict(status='no_proved_historical_pattern',attempted=0)); return
    _,identity,mode,proof=max(candidates,key=lambda a:(a[0],a[1],a[2]))
    p=panel()[identity]; source=ROOT/p['instance_path']; text=source.read_text()
    def vector(name): return ast.literal_eval(re.search(r'(?m)^'+name+r'\s*=\s*(.*)$',text)[1])
    initial=vector('initial');capacity=vector('capacities');points=vector('points')
    original=histories[identity]['fixed_inventory']; current=list(original)
    zero=[i for i in range(1,len(current)) if current[i]==initial[i]]
    order=sorted([i for i in range(1,len(current)) if i not in zero],
        key=lambda i:(abs(current[i]-initial[i]),math.dist(points[0],points[i]),i))
    releases=([zero] if zero else [])+[[i] for i in order]
    attempts=[];last_proof=str((RAW/'oracle_history'/identity/mode/'oracle_result.json').relative_to(ROOT))
    # The solver-free clique certificate already yields a four-station
    # conflict. Spend two of the original at-most-three MIP release slots;
    # the third slot funds one explicitly charged cheap-proof batch instead.
    for step,release in enumerate(releases[:2],1):
        trial=list(current)
        for i in release: trial[i]=-1
        stage='oracle_conflict_'+str(step)
        # Write the precise conditions before each optimizer call.
        write(OUT/('conflict_attempt_'+str(step)+'.json'),dict(id=identity,release=release,
            fixed_inventory=trial,previous_proof=last_proof,all_other_stations_retained=True))
        oracle_one(p,trial,'mip',120,stage)
        path=RAW/stage/identity/'mip'/'oracle_result.json'; rr=read(path)
        accepted=proved(rr)
        attempts.append(dict(step=step,release=release,accepted=accepted,**rr))
        if accepted: current=trial;last_proof=str(path.relative_to(ROOT));proof=rr
    names=[];coefficients=[];rhs=1
    for i in range(1,len(current)):
        if current[i]<0: continue
        for h in range(capacity[i].bit_length()):
            bit=(current[i]>>h)&1;names.append(f'bit_{i}_{h}');coefficients.append(-1 if bit else 1);rhs-=bit
    source_points=[ROOT/'results/gf_verified_candidate_native_round60/local_raw/fixed_120'/identity/'off'/'node_samples.csv',
        RAW/'fixed120_corrected'/identity/'off'/'node_samples.csv',RAW/'fixed120'/identity/'off'/'node_samples.csv']
    violations=[];bit_points=[]
    for path in source_points:
        if not path.exists(): continue
        points_by_sample={}
        with path.open(newline='') as f:
            for row in csv.DictReader(f):
                if row['variable'] not in names: continue
                key=(row['sample_kind'],row['root_callback_sequence'],row['node_bucket'])
                points_by_sample.setdefault(key,{})[row['variable']]=float(row['value'])
        for key,values in points_by_sample.items():
            if len(values)!=len(names): continue
            activity=sum(c*values[n] for n,c in zip(names,coefficients));violation=rhs-activity
            violations.append(dict(source=str(path.relative_to(ROOT)),source_sha256=sha(path),sample=key,
                activity=activity,rhs=rhs,violation=violation,violated=violation>1e-7))
            bit_points.append(dict(source=str(path.relative_to(ROOT)),sample=key,values=values))
    # Scope is original physical problem at this input's T. No Gini/cutoff domain was used.
    write(OUT/'conflict_result.json',dict(status='bounded_attempt_complete',id=identity,source_mode=mode,
        original_inventory=original,retained_inventory=current,attempts=attempts,final_proof=last_proof,
        fixed_stations=sum(v>=0 for v in current[1:]),original_fixed_stations=len(current)-1,
        scope='global original physical problem for this unchanged input and T; diagnostic proof only',
        no_good=dict(names=names,coefficients=coefficients,rhs=rhs),point_checks=violations,
        reusable_across_gini_leaves=True,
        static_trial_gate=any(v['violated'] for v in violations) and any(a['accepted'] for a in attempts),
        static_trial_decision='requires cost assessment; never submit automatically'))
    write(OUT/'conflict_bit_points.json',bit_points)
    print(identity,'retained stations',sum(v>=0 for v in current[1:]),'violations',[v['violation'] for v in violations])

if __name__=='__main__': main()
