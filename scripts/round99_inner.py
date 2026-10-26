"""One registered full-root MIP diagnostic, original production matrix and Start.

No sub-LP, intermediate target return, altered search parameter, or formal free UB.
Must be called only for an arm explicitly recorded in the inner protocol.
"""
import csv,json,math,sys,time
from round99_gurobi_runtime import gp,binding
from gurobipy import GRB
from round99_common import *
from round98_projection_vector_audit import check
from round70_affinity import inherited_core,read_masks
from round99_results import native_log
import round99_idle as admission
import analyze_round61 as physics
import generate_citibike443_regional_v1 as parser

MODES={'ENS-C':'off','R1':'aggregate','Q-I':'q-integer','M-B':'m-binary','R2':'projected'}

def decode(p,values):
    ind=parser.parse_instance_mirror(ROOT/p['input_path']);y=list(ind['initial']);routes=[]
    for n,x in values.items():
        assert math.isfinite(x),('nonfinite',n)
        if n.startswith(('p_','d_')):assert x>=-1e-6 and abs(x-round(x))<=1e-5,('physical quantity',n,x)
    for k in range(p['M']):
        arcs=[tuple(map(int,n.split('_')[2:])) for n,x in values.items() if n.startswith(f'x_{k}_') and x>.5]
        successor={a:b for a,b in arcs};assert len(successor)==len(arcs)
        if not arcs:continue
        nodes=[0];seen=set()
        while True:
            i=successor[nodes[-1]];nodes.append(i)
            if i==0:break
            assert i not in seen and 1<=i<=p['V'];seen.add(i)
        assert seen=={i for i in range(1,p['V']+1) if values[f'z_{k}_{i}']>.5}
        assert len(arcs)==len(nodes)-1,'disconnected selected arcs'
        ops=[]
        for i in nodes[1:-1]:
            a,b=round(values[f'p_{k}_{i}']),round(values[f'd_{k}_{i}']);y[i]+=b-a
            ops.append(dict(station=i,pickup=a,drop=b))
        routes.append(dict(vehicle=k,nodes=nodes,operations=ops))
    ratios=[y[i]/ind['target'][i] for i in range(1,p['V']+1)];S=sum(ratios)
    G=sum(abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:])/(p['V']*S) if S else 0
    weights=ind.get('weights',[0]+[1]*p['V'])
    if abs(max(weights[1:])-10)<=1e-6:weights=[w/10 for w in weights]
    P=sum(weights[i]*abs(ratios[i-1]-1) for i in range(1,p['V']+1))
    witness=dict(F=G+p['lambda']*P,inventory=y,routes=routes)
    physics.ROOT=ROOT;audited=physics.physical(dict(p,instance_path=p['input_path']),witness)
    assert audited['original_T_feasible'];return witness,audited

def run(protocol,number,label):
    admission.ensure_idle();runtime=binding();plan=read(protocol);a=plan['arms'][int(number)-1]
    assert int(number)==a['number'];p=a['role'];arm=a['arm'];mode=MODES[arm];cap=a['cap_seconds']
    assert plan['source_bindings']==bindings() and plan['binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    assert sha(ROOT/p['input_path'])==p['input_sha256']
    dest=OUT/'diagnostics'/label;dest.mkdir(parents=True,exist_ok=False)
    source=Path(a['source_destination']);initial=source/'external/initial_witness.json'
    assert sha(initial)==a['initial_witness_sha256']
    matrix=OUT/'exports'/p['id']/(mode+'.lp');assert sha(matrix)==a['model_sha256']
    candidates=[(path,read(path)) for path in (source/'external/native_logs').glob('*.round68.start.json')]
    path,j=next((path,j) for path,j in candidates if j['model_sha256']==sha(matrix) and j['submitted'] and abs(j['objective']-p['diagnostic_cutoff'])<=1e-7)
    assert all(j[k] for k in ['mapping_complete','rows_valid','objective_valid','readback_valid'])
    vector=path.with_name(path.name[:-5]+'.values.csv')
    assert sha(vector)==a['start_vector_sha256'];tick=time.monotonic();events=[]
    with inherited_core() as affinity,gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();assert gp.gurobi.version()==(13,0,2)
        with gp.read(str(matrix),env=env) as m:
            with vector.open(newline='') as f:table=list(csv.DictReader(f))
            assert [r['variable'] for r in table]==[v.VarName for v in m.getVars()]
            assert [r['type'] for r in table]==[v.VType for v in m.getVars()]
            values={r['variable']:float(r['value']) for r in table};start_check=check(m,values)
            assert start_check['maximum_absolute_residual']<=1e-7
            assert all(abs(values[v.VarName]-round(values[v.VarName]))<=1e-7 for v in m.getVars() if v.VType in ['B','I'])
            start_witness,start_physics=decode(p,values)
            assert abs(start_physics['F']-p['diagnostic_cutoff'])<=1e-7
            # A replay of the ACTUAL C++ mapper output, never column-copy across modes.
            for v in m.getVars():v.Start=values[v.VarName]
            m.update();assert all(abs(v.Start-values[v.VarName])<=1e-7 for v in m.getVars())
            m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
            m.Params.FeasibilityTol=1e-6;m.Params.IntFeasTol=1e-5;m.Params.OptimalityTol=1e-6
            m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(dest/'native.log')
            m.Params.TimeLimit=max(.001,cap-10-(time.monotonic()-tick))
            write(dest/'identity.json',dict(arm=a,protocol_sha256=sha(protocol),script_sha256=sha(__file__),
                model_sha256=sha(matrix),source_start_sha256=sha(path),start_vector_sha256=sha(vector),
                affinity=affinity,runtime=runtime,actual_types_checked=True,all_start_rows=start_check,
                scope='full initial improve domain; replayed self-paid factorial startup; acquisition cost excluded from diagnostic timing only'))
            def callback(model,where):
                if where==GRB.Callback.MIPSOL:
                    events.append(dict(kind='MIPSOL',solver_seconds=model.cbGet(GRB.Callback.RUNTIME),objective=model.cbGet(GRB.Callback.MIPSOL_OBJ)))
            with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',name=arm+'_full_root_MIP'))+'\n');f.flush()
            m.optimize(callback)
            with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='return',status=m.Status,runtime=m.Runtime))+'\n');f.flush()
            assert m.SolCount>0 and m.Status in [GRB.OPTIMAL,GRB.TIME_LIMIT]
            final_values={v.VarName:v.X for v in m.getVars()};residual=check(m,final_values)
            assert residual['maximum_absolute_residual']<=1e-6
            assert all(abs(v.X-round(v.X))<=1e-5 for v in m.getVars() if v.VType in ['I','B'])
            witness,physical=decode(p,final_values);assert physical['F']<=m.ObjVal+1e-7
            U=min(p['diagnostic_cutoff'],physical['F']);L=min(p['diagnostic_cutoff'],max(0,m.ObjBound));gap=U-L
            assert gap>=-1e-7
            summary=dict(passed=True,optimizer_calls=1,arm=arm,role=p['id'],status=m.Status,U=U,L=L,gap=gap,
                certificate=bool(m.Status==GRB.OPTIMAL and abs(gap)<=1e-7),solver_seconds=m.Runtime,work=m.Work,
                nodes=m.NodeCount,iterations=m.IterCount,start_physics=start_physics,final_physics=physical,
                matrix_residual=residual,objective=m.ObjVal,model_G=final_values['G'],true_G=physical['G'],
                outer_seconds=time.monotonic()-tick,scope='inner diagnostic; original-domain certificate conditional on replayed qualified U0; not formal end-to-end benefit')
            write(dest/'physical_witness.json',witness);write(dest/'events.json',events)
    structure,_,_=native_log(dest/'native.log');summary['production_log']=structure
    write(dest/'summary.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':run(sys.argv[1],sys.argv[2],sys.argv[3])
