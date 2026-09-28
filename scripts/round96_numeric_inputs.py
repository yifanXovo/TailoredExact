"""Zero-Optimize audit of actual original objectives/duration rows and input scales."""
import math
import re
from round96_prepare import ROOT,OUT,read,write,sha,citi

NUM=r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
TERM=re.compile(r'\s*([+-]?)\s*(?:('+NUM+r')\s+)?([A-Za-z_][A-Za-z_0-9]*)')
def expression(s):
    out={};pos=0
    while pos<len(s.rstrip()):
        m=TERM.match(s,pos);assert m,(s[pos:pos+50],pos)
        sign,num,var=m.groups();out[var]=out.get(var,0)+(-1 if sign=='-' else 1)*(float(num) if num else 1)
        pos=m.end()
    return out

def main():
    identity=read(OUT/'external/identity.json');records=[]
    for p in read(OUT/'external_inputs.json')['roles']:
        data=citi.parse_instance_mirror(ROOT/p['input_path']);n=data['V']
        path=OUT/'external/reference'/p['id']/'original.lp'
        assert sha(path)==identity['references'][p['id']]['canonical_sha256']
        lines=path.read_text().splitlines();obj=expression(next(s for s in lines if s.startswith(' obj:')).split(':',1)[1])
        expected={'G':1.};expected.update({f'e_{i}':p['lambda']*data['weights'][i] for i in range(1,n+1)})
        assert obj==expected
        durations=[];maxdiff=0
        for line in lines:
            if not line.startswith(' c') or ': 120 p_' not in line:continue
            expr,sense,rhs=re.split(r'\s+(<=|>=|=)\s+',line.split(':',1)[1]);terms=expression(expr)
            if not any(v.startswith('x_') for v in terms):continue
            k=int(next(v for v in terms if v.startswith('p_')).split('_')[1])
            required={f'p_{k}_{i}':120. for i in range(1,n+1)}
            for i in range(n+1):
                for j in range(n+1):
                    if i==j:continue
                    dx=data['points'][i][0]-data['points'][j][0];dy=data['points'][i][1]-data['points'][j][1]
                    required[f'x_{k}_{i}_{j}']=math.sqrt(dx*dx+dy*dy)/1.5
            assert set(terms)==set(required)
            delta=max(abs(terms[key]-value) for key,value in required.items());maxdiff=max(maxdiff,delta)
            assert delta<1e-10 and sense=='<=' and float(rhs)==p['T_seconds']
            durations.append(k)
        assert sorted(durations)==list(range(p['M']))
        coeff=[p['lambda']*w for w in data['weights'][1:]]+[1/d for d in data['target'][1:]]+[120.]
        coeff += [data['distances'][i][j] for i in range(n+1) for j in range(n+1) if i!=j]
        coeff += [y/data['target'][i] for i in range(1,n+1) for y in range(data['capacities'][i]+1) if y]
        assert all(c>1e-12 and (c==1 or abs(c-1)>1e-12) for c in coeff)
        records.append(dict(id=p['id'],objective_exact_binary64_match=True,duration_rows=len(durations),
            maximum_duration_coefficient_difference=maxdiff,minimum_nonzero_checked_coefficient=min(coeff),
            minimum_nonunit_distance_to_one=min(abs(c-1) for c in coeff if c!=1),
            maximum_station_capacity=max(data['capacities'][1:]),maximum_ratio=max(c/d for c,d in zip(data['capacities'][1:],data['target'][1:])),
            input_sha256=p['input_sha256'],canonical_sha256=sha(path)))
    write(OUT/'numeric_input_audit.json',dict(passed=True,optimizer_calls=0,records=records,
        limitation='Checks actual input/objective/full duration rows and finite inventory-state scales. Does not claim arbitrary real input fidelity or exact rational solver certificates. Dynamic leaf coefficients remain governed by inherited numerical contract.'))

if __name__=='__main__':main()
