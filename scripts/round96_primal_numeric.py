"""Apply the R96 actual coefficient audit to the four new common-build roles."""
import math
import re
from round96_prepare import ROOT,OUT,read,write,sha,citi
from round96_numeric_inputs import expression

def main():
    identity=read(OUT/'primal/identity.json');records=[];seen=set()
    for launch in identity['launches']:
        p=launch['panel']
        if p['id'] in seen:continue
        seen.add(p['id']);data=citi.parse_instance_mirror(ROOT/p['input_path']);n=data['V']
        path=OUT/'primal/reference'/p['id']/'original.lp';assert sha(path)==p['reference']['canonical_sha256']
        lines=path.read_text().splitlines()
        obj=expression(next(s for s in lines if s.startswith(' obj:')).split(':',1)[1])
        expected={'G':1.};expected.update({f'e_{i}':p['lambda']*data['weights'][i] for i in range(1,n+1)})
        assert obj==expected
        durations=[];maxdiff=0.
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
                    value=math.sqrt(dx*dx+dy*dy)/1.5
                    if value:required[f'x_{k}_{i}_{j}']=value
            assert set(terms)==set(required)
            delta=max(abs(terms[key]-value) for key,value in required.items());maxdiff=max(maxdiff,delta)
            assert delta<1e-10 and sense=='<=' and float(rhs)==p['T_seconds'];durations.append(k)
        assert sorted(durations)==list(range(p['M']))
        coefficients=[p['lambda']*w for w in data['weights'][1:]]+[1/d for d in data['target'][1:]]+[120.]
        coefficients += [data['distances'][i][j] for i in range(n+1) for j in range(n+1) if i!=j]
        coefficients += [y/data['target'][i] for i in range(1,n+1) for y in range(1,data['capacities'][i]+1)]
        assert all(c==0 or c>1e-12 and (c==1 or abs(c-1)>1e-12) for c in coefficients)
        records.append(dict(id=p['id'],objective_exact_binary64_match=True,duration_rows=len(durations),
            maximum_duration_coefficient_difference=maxdiff,canonical_sha256=sha(path),
            minimum_nonzero_coefficient=min(c for c in coefficients if c),
            minimum_nonunit_distance_to_one=min(abs(c-1) for c in coefficients if c!=1)))
    write(OUT/'primal_numeric_audit.json',dict(passed=True,records=records,optimizer_calls=0,
        identity_sha256=sha(OUT/'primal/identity.json'),source_sha256=sha(__file__),
        limitation='Actual original objective/time rows and finite input/state scales; inherited floating dynamic-row contract, not arbitrary-real writer fidelity.'))

if __name__=='__main__':main()
