"""One post-trace, same-block owner-fixed contrast. Never a global bound."""
from fractions import Fraction as F
from round159_common import *
from round159_verify import check_resource

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round143_lp import residual
    from round157_resource import native_quality
    from round157_floor import original_lower
    from round157_inventory import value
    affinity();assert binding()['sha256']==DLL_SHA
    events=read(OUT/'trajectory_analysis.json')['events']
    eligible=[r for r in events if r['role']=='R-X35-S-T2' and r['stage']=='joint' and r['owner_changes'] and r['quantity_stations']]
    assert eligible
    selected=next((r for r in eligible if any(r['quantity_net_on_old_owner']) and any(r['owner_net_compensation'])),eligible[0])
    iteration=selected['iteration'];folder=OUT/'review/owner_ablation';folder.mkdir(parents=True,exist_ok=False)
    source=read(OUT/'inputs_v2/R-X35-S-T2/source.json');d=source['data'];stem=OUT/'runs/joint_rx'/f'call_{iteration}'
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(stem)+'.mps',env=env) as m:
            m.read(str(stem)+'.mst');starts={v.VarName:v.Start for v in m.getVars()}
            Y=[next(y for y in s['support'] if starts[f'x[{s["i"]},{y}]']>.5) for s in source['scope']['stations']]
            owner=[-1]*d['n'];fixed=0
            for i,y in enumerate(Y,1):
                if y!=d['initial'][i]:owner[i-1]=next(k for k in range(len(d['Q'])) if starts.get(f'resource_service[{k},{i},{y}]',0)>.5)
            for v in m.getVars():
                if v.VarName.startswith('resource_service['):
                    k,i,y=map(int,v.VarName[len('resource_service['):-1].split(','))
                    if k!=owner[i-1] and v.UB!=0:v.UB=0;fixed+=1
            m.update();qs=residual(m,starts);assert max(qs['constraints'],qs['bounds'])<1e-7
            m.Params.Threads=1;m.Params.Seed=0;m.Params.MIPFocus=1;m.Params.NodeLimit=512;m.Params.TimeLimit=120
            m.Params.MIPGap=0;m.Params.MIPGapAbs=0;m.Params.IntFeasTol=1e-6;m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6;m.Params.DualReductions=0
            m.Params.LogFile=str(folder/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0
            m.write(str(folder/'model.mps'));m.write(str(folder/'start.mst'))
            write(folder/'condition.json',dict(UTC=utc(),selected=selected,selection='first recorded RX joint quantity/owner compensation event, else first joint quantity+owner event',
                posthoc_mechanism_diagnostic=True,source_model_SHA=sha(str(stem)+'.mps'),source_start_SHA=sha(str(stem)+'.mst'),
                only_difference='add fixed owner/absent-station bounds inside the exact same released block; no extra full-A budget',
                fixed_columns=fixed,NodeLimit=512,Seed=0,Threads=1,local_scope_only=True))
            m.optimize();quality=native_quality(m,folder/'native.log');assert quality['numeric_ok'] and m.SolCount
            vals={v.VarName:v.X for v in m.getVars()};q=residual(m,vals);assert max(q['constraints'],q['bounds'])<=1e-5
            p=dict(Y=[max(s['support'],key=lambda y:vals[f'x[{s["i"]},{y}]']) for s in source['scope']['stations']],owner=owner)
            p['J']=float(value(source['scope'],p['Y'])['phi']);accepted=check_resource(source,p)
            transport=source['transport'];local_lower=original_lower(m.ObjBound,dict(scale=transport['scale'],guard=transport['guard'],correction=F(transport['correction_exact']),anchors={int(k):F(v) for k,v in transport['anchors_exact'].items()}))
            save_gz(folder/'solution.json.gz',vals)
            result=dict(UTC=utc(),PASS=True,status=m.Status,NodeCount=m.NodeCount,Runtime=m.Runtime,Work=m.Work,
                true_J_fixed_owner=accepted['J'],restricted_J_lower=float(local_lower),joint_selected_J=selected['after_J'],
                owner_freedom_needed_for_this_improvement=local_lower>F(selected['after_J']),
                objective_transport_guard_applied=True,quality=quality,residual=q,scope='only the selected block and its fixed outside state',
                global_lower=None,global_proof_ledger_changes=0)
            write(OUT/'owner_ablation.json',result);print(json.dumps(result))

if __name__=='__main__':run()
