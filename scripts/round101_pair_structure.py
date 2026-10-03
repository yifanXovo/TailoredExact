"""Solver-free physical pair witnesses for the saved F5 large-support rank.
All direct two-pickup routes are checked; no cutoff/G-interval feasibility claim.
"""
import ast,itertools,math,re,time
from round101_common import *

def main(label):
    tick=time.perf_counter();p=next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']=='F5')
    source=OUT/'diagnostics/lp01/F5/raw.separation.json';saved=read(source)
    row=saved['rows'][0];events=row['proof']['events']
    assert len(events)==38 and row['proof']['rank']==16 and all(e[1]==-1 and e[2]==12 for e in events)
    text=(ROOT/p['input_path']).read_text()
    def vector(name):return ast.literal_eval(re.search(r'(?m)^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text)[1])
    points=vector('points');b=vector('initial');capacity=vector('capacities');Q=p['Q_vector']
    def distance(i,j):return math.hypot(points[i][0]-points[j][0],points[i][1]-points[j][1])/1.5
    checked=0;worst=None;cost=p['pickup_seconds']+p['drop_seconds']
    for a,e in itertools.combinations(events,2):
        i,j=a[0],e[0];q1,q2=a[2],e[2]
        assert i!=j and 0<=b[i]-q1<=capacity[i] and 0<=b[j]-q2<=capacity[j]
        assert q1+q2<=min(Q) # every physical vehicle can execute this pair
        routes=[([0,i,j,0],distance(0,i)+distance(i,j)+distance(j,0)),
                ([0,j,i,0],distance(0,j)+distance(j,i)+distance(i,0))]
        nodes,travel=min(routes,key=lambda v:v[1]);duration=travel+cost*(q1+q2)
        assert duration<=p['T_seconds']+1e-7
        witness=dict(vehicle=0,nodes=nodes,operations=[[i,q1,0],[j,q2,0]],
            load_prefix=[q1,q1+q2],return_load=q1+q2,travel=travel,duration=duration)
        if worst is None or duration>worst['duration']:worst=witness
        checked+=1
    write(OUT/'diagnostics'/label/'summary.json',dict(passed=True,optimizer_calls=0,
        physical_pairs=checked,all_vehicles_eligible=True,support=38,rank=16,
        largest_pair_duration=worst['duration'],smallest_T_margin=p['T_seconds']-worst['duration'],
        worst_pair_witness=worst,input_path=p['input_path'],input_sha256=p['input_sha256'],
        event_row_source=str(source.relative_to(ROOT)),event_row_sha256=sha(source),
        elapsed_offline_seconds=time.perf_counter()-tick,
        inference='Every pair in this particular 38-event pickup set admits a direct legal physical route, yet the conservative fleet upper rank is16. Its deficit cannot be certified by the R62 all-pairs-incompatible clique test on that set.',
        limitation='These are physical resource witnesses. They do not establish pair feasibility under the historical imported LP incumbent cutoff or G interval; no dominance over every R62 projection/support/native cut is claimed.'))
    print(json.dumps(dict(passed=True,physical_pairs=checked,worst_duration=worst['duration'],Optimize=0)))

if __name__=='__main__':
    import sys;main(sys.argv[1])
