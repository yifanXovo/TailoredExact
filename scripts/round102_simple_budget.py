"""Solver-free analytical explanation of selected F2 supports, after idle.
This cannot reject the whole J family or replace a completed support proof.
"""
import sys,json
from pathlib import Path
from fractions import Fraction as F
from round102_common import *
from round102_support import exact
from round100_idle import ensure_idle

def main(label):
    ensure_idle();folder=OUT/'native02/raw/02_F2_J-SUBMIT/external/native_logs'
    file=folder/'L0_terminal_mip.gurobi.log.round102.certificates.jsonl'
    binding=read(Path(str(file).replace('.certificates.jsonl','.contract.json')))
    c=binding['column_contract']['resource'];T=exact(c['horizon_upper']);cost=exact(c['handling_lower'])
    ell=[exact(c['shortest_lower'][0][i])+exact(c['shortest_lower'][i][0]) for i in range(len(c['initial']))]
    assert cost>0
    e=min(ell[1:]);cap=max(0,int((T-e)//cost));records=[]
    for index,row in enumerate(json.loads(x) for x in file.read_text().splitlines()):
        alternatives=[]
        for p in row['proofs']:
            k=p['vehicle'];w=p['weights']
            max_pick=max(0,max(a for a,b,g in w));max_drop=max(0,max(b for a,b,g in w))
            simple=cap*(max_pick+max_drop)+sum(max(0,g) for a,b,g in w)
            fixed_implied=True;station_bounds=[]
            for i,(a,b,g) in enumerate(w[1:],1):
                qcap=max(0,int((T-ell[i])//cost))
                A=min(c['initial'][i],c['capacities'][k],qcap)
                B=min(c['station_capacity'][i]-c['initial'][i],c['capacities'][k],qcap)
                # For A/B=0 no corresponding nonzero operation is possible.
                station_max=max(0,*([a*A+g] if A and a>=0 else [a+g] if A else []),*([b*B+g] if B and b>=0 else [b+g] if B else []))
                fixed_implied&=station_max<=0
                station_bounds.append([i,qcap,A,B,station_max])
            alternatives.append(dict(vehicle=k,DP_upper=p['upper'],max_pickup_weight=max_pick,max_drop_weight=max_drop,cheap_total_profit_upper=simple,
                cheap_bound_equals_DP=simple==p['upper'],all_individual_operation_profits_nonpositive=fixed_implied,
                individual_caps_imply_DP_zero=fixed_implied and p['upper']==0,station_bounds=station_bounds))
        records.append(dict(certificate_line=index+1,alternatives=alternatives))
    write(OUT/'diagnostics'/label/'summary.json',dict(Optimize=0,passed=True,minimum_singleton_travel=str(e),
        mandatory_nonempty_pickup_integer_cap=cap,records=records,source=file.relative_to(ROOT).as_posix(),sha256=sha(file),script_sha256=sha(__file__),
        argument='P>0 implies at least one served station and singleton travel>=minimum ell; D<=P and integer P give P<=floor((T-minell)/c). Empty plan P=D=0 also satisfies this cap. Separate nonnegative maxima of pickup and drop weights give profit<=(maxalpha+maxbeta)*cap+sum positive gamma. Each visited station further implies p_i,d_i<=floor((T-ell_i)/c), and these caps times binary z imply individual signed profit bounds.',
        scope='Cheap strengthened integer bounds, not assumed to be explicit old-LP rows. Equality explains these literal F2 support values only; it does not show all signed J supports or required maximizations are redundant. No production change or new parameter search.'))
    print(json.dumps(dict(passed=True,cap=cap,records=records,Optimize=0)))

if __name__=='__main__':main(sys.argv[1])
