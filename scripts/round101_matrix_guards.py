"""Finite solver-free fault injection on an actual preserved ENS matrix.
Run only after performance is idle. Expected audit rejection is test success.
"""
import copy,sys,re
from round100_idle import ensure_idle
from round101_common import *

def main(label):
    ensure_idle();source=OUT/'diagnostics/lp01/F2';lines=(source/'matrix.txt').read_text().splitlines()
    n,R=map(int,lines[0].split());variables=[x.split() for x in lines[1:1+n]]
    rows=[]
    for line in lines[1+n:]:
        v=line.split();count=int(v[2]);assert len(v)==3+2*count
        rows.append([v[0],float(v[1]),{int(v[3+2*j]):float(v[4+2*j]) for j in range(count)}])
    assert len(rows)==R;columns={v[0]:j for j,v in enumerate(variables)}
    p=read(OUT/'development_inputs.json')['roles'][0];assert p['id']=='F2'
    folder=OUT/'diagnostics'/label;folder.mkdir(exist_ok=False);cases=[]
    def test(name,vs,rs,expected,extra=None):
        matrix=folder/(name+'.matrix');out=folder/(name+'.json')
        with matrix.open('x') as f:
            f.write(f'{n} {len(rs)}\n')
            for v in vs:f.write(' '.join(v)+'\n')
            for sense,rhs,a in rs:
                f.write(f'{sense} {rhs:.17g} {len(a)} '+' '.join(f'{j} {v:.17g}' for j,v in a.items())+'\n')
        cmd=[BUILD/'Round101FleetDiagnostic.exe',ROOT/p['input_path'],p['T_seconds'],60,60,matrix,source/'raw.point',out]
        tick=time.perf_counter();ret=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),capture_output=True,text=True,timeout=120)
        result=read(out);assert ret.returncode==(0 if expected else 2) and result['valid']==expected,(name,ret.returncode,result)
        if extra:extra(result['contract'])
        cases.append(dict(name=name,expected_valid=expected,observed_valid=result['valid'],reason=result['reason'],
            returncode=ret.returncode,outer_child_seconds=time.perf_counter()-tick,matrix_sha256=sha(matrix),output_sha256=sha(out)))
    vs=copy.deepcopy(variables);vs[columns['Y_1']][1]='C';test('nonintegral_inventory_rejected',vs,rows,False)
    states={j for name,j in columns.items() if re.fullmatch(r'state_1_\d+',name)}
    rs=copy.deepcopy(rows);changed=0
    for row in rs:
        if row[0]=='=' and row[1]==1 and set(row[2])==states and all(v==1 for v in row[2].values()):
            row[2][min(states)]=.5;changed+=1
    assert changed;test('broken_onehot_rejected',variables,rs,False)
    load={columns[f'p_0_{i}']:1 for i in range(1,p['V']+1)}|{columns[f'd_0_{i}']:-1 for i in range(1,p['V']+1)}
    rs=copy.deepcopy(rows);changed=0
    for row in rs:
        if row==['>',0,load]:row[1]=-1;changed+=1
    assert changed;test('nonnegative_return_premise_rejected',variables,rs,False)
    support={j for name,j in columns.items() if name.startswith('x_0_') or re.fullmatch(r'p_0_\d+',name)}
    duration=[r for r in range(R) if rows[r][0]=='<' and set(rows[r][2])==support]
    assert len(duration)==1;r=duration[0]
    rs=copy.deepcopy(rows)
    for name,j in columns.items():
        if re.fullmatch(r'p_0_\d+',name):rs[r][2][j]=119.999999
    def lowered(c):assert c['handling_lower']==119.999999
    test('smaller_imported_handling_relaxes_contract',variables,rs,True,lowered)
    rs=copy.deepcopy(rows);rs[r][1]=3600.5
    def raised(c):assert c['horizon_upper']>=3600.5
    test('larger_imported_rhs_relaxes_contract',variables,rs,True,raised)
    rs=copy.deepcopy(rows);rs.append(copy.deepcopy(rs[r]))
    test('ambiguous_duration_rejected',variables,rs,False)
    write(folder/'summary.json',dict(passed=True,optimizer_calls=0,source_matrix_sha256=sha(source/'matrix.txt'),
        diagnostic_binary_sha256=sha(BUILD/'Round101FleetDiagnostic.exe'),cases=cases,
        scope='Typed actual-matrix audit and safe coefficient/RHS relaxation; no native search or callback API rejection injection'))
    print(json.dumps(dict(passed=True,cases=len(cases),Optimize=0)))

if __name__=='__main__':main(sys.argv[1])
