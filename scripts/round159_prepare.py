"""Finite read-only inheritance, protection, and original-J RN export."""
from fractions import Fraction as F
from round159_common import *
from round140_common import git

def metadata():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'goal.md').write_bytes((WORK/'plans/TailoredExact_Round159_Complete_Goal.md').read_bytes())
    facts=[]
    for tree in (Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round158'):
        names=git('diff','HEAD','--name-only','-z',cwd=tree).decode().split('\0')
        dirty={n:dict(SHA256=sha(tree/n),bytes=(tree/n).stat().st_size) for n in names if n and (tree/n).is_file()}
        facts.append(dict(tree=str(tree),head=git('rev-parse','HEAD',cwd=tree).decode().strip(),tracked_dirty=dirty))
    write(OUT/'infra/protected_initial.json',dict(UTC=utc(),trees=facts))
    assert not git('ls-files','*AGENTS.md',cwd=ROOT).strip()
    write(OUT/'infra/entry.json',dict(UTC=utc(),base=BASE,main=git('rev-parse','origin/main',cwd=ROOT).decode().strip(),
        origin=git('remote','get-url','origin',cwd=ROOT).decode().strip(),branch=git('branch','--show-current',cwd=ROOT).decode().strip(),
        worktree=str(ROOT),policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),TOTAL=TOTAL,old_producers_run=0,
        previous_R159_found=False,entry_process_check='No Python/Exact/Gurobi/compiler process observed at initial CIM inventory'))
    history={}
    for r in (76,83,96,103,105,106,107,133,134,135,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158):
        candidates=git('ls-tree','-r','--name-only','HEAD',f'results/unified_exact_round{r}',cwd=ROOT).decode().splitlines()
        chosen=[n for n in candidates if n.endswith(('final_report.md','mathematical_analysis.md','ap_math_and_history.md'))]
        history[str(r)]=[]
        for name in chosen[:3]:
            content=git('show',f'HEAD:{name}',cwd=ROOT)
            p=OUT/'infra/history'/f'{r}_{Path(name).name}';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
            history[str(r)].append(dict(path=name,source_commit=BASE,SHA256=sha(p),local=str(p.relative_to(ROOT))))
    write(OUT/'history_sources.json',history)

def prepare():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round157_inventory import instance,value
    from round157_floor import objective,attach
    from round153_pricing import Oracle
    from round157_resource import travel_bounds
    from round158_level import envelope,budgets
    from round157_fleet import verify
    affinity();assert binding()['sha256']==DLL_SHA
    sources=read(ROOT/'results/unified_exact_round157/inventory_sources.json')
    families=read(ROOT/'results/unified_exact_round157/inventory_families.json')
    refs=[]
    for role,source in sources.items():
        folder=OUT/'inputs_v2'/role;folder.mkdir(parents=True,exist_ok=False)
        scope=source['scope'];data=instance(source['panel'])
        package_path=WORK/'worktrees/round158/results/unified_exact_round158/qualification/coefficient_v2'/(source['panel']['input_sha256']+'.json')
        package=read(package_path);assert package['input_SHA']==source['panel']['input_sha256']
        data['distance']=package['distance']
        # Directly bind sqrt(dx*dx+dy*dy)/1.5 at every ordered pair.
        rebuilt=[[math.sqrt((a[0]-b[0])*(a[0]-b[0])+(a[1]-b[1])*(a[1]-b[1]))/1.5 for b in data['points']] for a in data['points']]
        assert rebuilt==data['distance']
        physical=families[role]['positive_control']['witness'];checked=verify(data,physical)
        assert checked['original_T_feasible']
        owners=[-1]*data['n']
        for route in physical['routes']:
            for i in route['nodes'][1:-1]:owners[i-1]=route['vehicle']
        Y=list(checked['Y'])
        if role=='R-X35-S-T2':
            assert Y[2]==6 and Y[15]==6 and owners[2]==owners[15]==2
            Y[2]=5;Y[15]=7
        val=value(scope,Y);assert val['feasible'] and scope['gamma_L']==0
        md,contract=envelope(data,package)
        bounds=travel_bounds(md,list(range(1,data['n']+1)));plan=budgets(md,bounds)
        rawbounds=travel_bounds(data,list(range(1,data['n']+1)))
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.start()
            o=Oracle(scope,env,old_joint=True);transport=objective(o);o.model.write(str(folder/'rn.mps'))
            native_map={v.VarName:dict(LB=v.LB,UB=v.UB if math.isfinite(v.UB) else 'Infinity',type=v.VType,Obj=v.Obj) for v in o.model.getVars()}
            o.close()
        lines=[f"{data['n']} {len(data['Q'])} {scope['Bminus']} {scope['B']} {scope['gamma_U']:.17g} {md['pickup']:.17g} {md['T']:.17g} {data['T']:.17g}",
            ' '.join(map(str,data['Q']))]
        for s in scope['stations']:
            i=s['i'];lines.append(' '.join(map(str,[data['initial'][i],data['capacity'][i],format(s['c'],'.17g'),format(s['omega'],'.17g'),len(s['support']),*s['support']])))
        lines+=[' '.join(format(v,'.17g') for v in row) for row in data['distance']]
        lines.append(f"{plan['U']} {len(plan['kept'])}")
        for row in plan['kept']:lines.append(' '.join(map(str,[len(row['stations']),*row['stations'],row['budget']])))
        lines+=[' '.join(map(str,Y)),' '.join(map(str,owners))]
        (folder/'data.txt').write_text('\n'.join(lines)+'\n',encoding='ascii')
        write(folder/'source.json',dict(role=role,source=source,data=data,scope=scope,initial_Y=Y,owner=owners,
            J=float(val['phi']),J_exact=str(val['phi']),physical=checked,physical_witness=physical,
            coefficient_package=dict(path=str(package_path),SHA256=sha(package_path),fixed_science='163b1b3d0dbcc7be3a84d94108ef4a26ae9baba3'),
            contract=contract,budget_plan=plan,rawbounds=rawbounds,native_map=native_map,
            transport=dict(scale=transport['scale'],anchors_exact={str(k):str(v) for k,v in transport['anchors'].items()},
                guard=transport['guard'],correction_exact=str(transport['correction'])),
            initial_owner_keeps_zero_service_membership=True,old_quarter_cutoff_installed=False))
        refs.append(dict(role=role,input_SHA=source['panel']['input_sha256'],data_SHA=sha(folder/'data.txt'),RN_SHA=sha(folder/'rn.mps'),
            coefficient_SHA=sha(package_path),start_J=float(val['phi']),baseline_physical_J=checked['J']))
    write(OUT/'inputs_v2/manifest.json',dict(UTC=utc(),roles=refs,DLL=binding(),Optimize=0))

if __name__=='__main__': globals()[sys.argv[1]]()
