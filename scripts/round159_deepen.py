"""E1: one bounded fixed-Y, fully free-owner query using the qualified R157 oracle.

This is offline reuse of the old complex fleet interface, not the new online
core and not a Python production-candidate timing measurement.
"""
from fractions import Fraction as F
from round159_common import *

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round157_fleet import build,decode,verify,lift
    from round157_resource import native_quality
    from round158_level import envelope
    from round143_lp import residual,semantics
    from round159_verify import check_resource
    from round158_common import Durable
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OUT/'inputs_v2/R-X35-S-T2/source.json');p=read(OUT/'runs/joint_rx/best.json')
    accepted=check_resource(source,p);d=source['data'];package=read(source['coefficient_package']['path'])
    md,contract=envelope(d,package);folder=OUT/'deepening/free_owner_rx';folder.mkdir(parents=True,exist_ok=False)
    supports={i:[y] for i,y in enumerate(p['Y'],1)};tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();m,ref=build(md,supports,env)
        # Bound readback is essential: this is an assignment hint, not fixed owner.
        eligibility=[]
        for (k,i,y),v in ref['w'].items():
            assert v.LB==0 and v.UB==1 and v.VType=='B'
            v.Start=float(k==p['owner'][i-1]);eligibility.append([k,i,y])
        for (i,y),v in ref['z'].items():v.Start=1
        for v in ref['x'].values():assert v.LB==0 and v.UB==1
        m.Params.Threads=1;m.Params.Seed=0;m.Params.MIPFocus=1;m.Params.NodeLimit=8192
        m.Params.TimeLimit=1800;m.Params.SolutionLimit=1;m.Params.MIPGap=0;m.Params.MIPGapAbs=0;m.Params.IntFeasTol=1e-6;m.Params.DualReductions=0
        m.Params.LogFile=str(folder/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0
        m.write(str(folder/'model.mps'));m.write(str(folder/'start.mst'))
        with gp.read(str(folder/'model.mps'),env=env) as back:assert semantics(back)==semantics(m)
        write(folder/'condition.json',dict(UTC=utc(),role='R-X35-S-T2',Y=p['Y'],J=accepted['J'],J_exact=accepted['J_exact'],
            stock_fixed=True,all_eligible_owner_order_load_free=True,owner_Start_only=True,eligibility=eligibility,
            model_SHA=sha(folder/'model.mps'),original_T=d['T'],contract=contract,NodeLimit=8192,TimeLimit=1800,
            Seed=0,Threads=1,guarded_necessary_model=True,resource_start_not_claimed_physical=True,
            inherited_kernel='R157 fleet.build/decode/verify/lift; no master/core/IIS loop',Python_role='offline reuse only'))
        durable=Durable(folder);m.optimize(durable.observe);assert not durable.errors
        quality=native_quality(m,folder/'native.log');classification='UNKNOWN';physical=None;witness=None
        if m.SolCount:
            witness,decoded=decode(d,ref);assert decoded['Y']==p['Y']
            physical=verify(d,witness);point={v.VarName:v.X for v in m.getVars()};q=residual(m,point)
            integer=max([abs(v.X-round(v.X)) for v in m.getVars() if v.VType!='C']+[0])
            assert max(q['constraints'],q['bounds'],integer)<=1e-5 and quality['numeric_ok']
            save_gz(folder/'solution.json.gz',point);write(folder/'witness.json',witness)
            if physical['original_T_feasible']:classification='PHYSICAL_FEAS'
        elif m.Status==gp.GRB.INFEASIBLE and quality['numeric_ok']:classification='FIXED_Y_ALL_OWNER_INFEAS'
        write(folder/'result.json',dict(UTC=utc(),classification=classification,status=m.Status,SolCount=m.SolCount,
            Runtime=m.Runtime,Work=m.Work,NodeCount=m.NodeCount,IterCount=m.IterCount,quality=quality,
            physical=physical,physical_U=physical['J'] if classification=='PHYSICAL_FEAS' else None,
            global_lower_change=0,all_owner_bounds_readback=True,total_seconds=time.perf_counter()-tick,
            model_SHA=sha(folder/'model.mps'),normal_Optimize_return=True))
        m.dispose()

if __name__=='__main__':run()
