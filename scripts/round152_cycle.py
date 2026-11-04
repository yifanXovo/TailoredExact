"""Finite uniform cut-loop diagnostic; no production entry or timed dispatch."""
from round152_common import *

def floor_bundle(role,target):
    source=OUT/'oracle'/f'{role}_strong_zero'/'result.json';r=read(source)
    if r['decision']!='SEPARATION':return None
    scope=read(OUT/'domains'/role/'domain.json')['scope'];assert scope==r['scope'] and all(v==0 for v in r['pi'].values())
    assert r['complete_cover'] and r['lower'] is not None
    terms={'G':1.};terms.update({f'e_{s["i"]}':s['omega'] for s in scope['stations'] if s['omega']})
    bundle=dict(qualified=True,scope=scope,source=str(source),source_SHA=sha(source),
                rows=[dict(name='r152_inventory_objective_floor',terms=terms,sense='>',rhs=r['lower'])])
    write(target,bundle);return target

def cycle(role,label='cycle',rounds=8):
    from round152_lp import solve
    from round152_projection import project
    from round152_discover import discover
    from round150_lp import affinity
    configure();affinity();target=OUT/'cycles'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();scope=read(OUT/'domains'/role/'domain.json')['scope'];base='strongCP2';current=base;records=[]
    floor=floor_bundle(role,target/'floor_rows.json')
    write(target/'plan.json',dict(UTC=utc(),role=role,base=base,maximum_support_rounds=rounds,
          scalar_floor_added_if_prior_complete_cover_separates=True,uniform_across_roles=True,
          stop_on_unqualified_pricing_or_joint_witness=True,do_not_stop_on_first_zero_root_gain=True))
    if floor:
        current=label+'_floor';solve(role,current,base,str(floor))
        records.append(dict(stage='floor',variant=current,L=read(OUT/'LP'/f'{role}_{current}'/'result.json')['L']))
    for k in range(1,rounds+1):
        discovery=OUT/'discovery'/f'{role}_{base}_first'/'result.json' if k==1 else None
        if k>1:
            pp=OUT/'projection'/f'{role}_{current}'
            pr=project(scope,load_gz(OUT/'LP'/f'{role}_{current}'/'solution.json.gz'),pp)
            if not pr['full_oracle_projection_feasible']:
                records.append(dict(stage='stop',reason='joint_witness_not_qualified',variant=current));break
            tag=f'{label}{k:02}';discover(role,current,tag)
            discovery=OUT/'discovery'/f'{role}_{current}_{tag}'/'result.json'
        dr=read(discovery)
        if not dr['qualified']:
            records.append(dict(stage='stop',reason='pricing_not_qualified_to_separate',variant=current,discovery=str(discovery)));break
        nxt=f'{label}_{k:02}';solve(role,nxt,current,str(discovery));lr=read(OUT/'LP'/f'{role}_{nxt}'/'result.json')
        assert lr['qualified'];records.append(dict(stage='support',round=k,variant=nxt,parent=current,L=lr['L'],gain=lr['gain'],discovery=str(discovery)))
        current=nxt
        write(target/'progress.json',dict(current=current,records=records))
        print(json.dumps(dict(role=role,round=k,L=lr['L'],gain=lr['gain'])),flush=True)
    result=dict(role=role,base=base,final_variant=current,records=records,seconds=time.perf_counter()-start,
                base_L=read(OUT/'LP'/f'{role}_{base}'/'result.json')['L'],final_L=read(OUT/'LP'/f'{role}_{current}'/'result.json')['L'])
    write(target/'result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':cycle(*sys.argv[1:3],rounds=int(sys.argv[3]) if len(sys.argv)>3 else 8)
