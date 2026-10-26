"""Read integer MASTER incumbents; paid serial exact oracle diagnostics.

Nonoptimal master incumbents are diagnostic sources only. This script does
not feed them into a production run or import a historical/P witness.
"""
import ast,csv,json,math,re,sys,subprocess,time
from pathlib import Path
from round105_common import *
import analyze_round61 as physical

def vector(text,name):
    m=re.search(r'(?m)^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text)
    return ast.literal_eval(m[1])
def values(path):
    out={}
    for line in Path(path).read_text().splitlines():
        if line.startswith('#') or not line.strip():continue
        n,v=line.split();out[n]=float(v)
    return out
def extract(campaign,label):
    dest=OUT/'modes'/label;dest.mkdir(parents=True,exist_ok=False)
    identity=read(OUT/campaign/'identity.json');manifest=[]
    for launch in identity['launches']:
        p=launch['panel'];folder=Path(launch['destination'])/'external/round105'
        solution=folder/'master_1.lp.sol'
        if not solution.exists():continue # explicit unstarted/unknown-without-incumbent roles are not modes
        calls=list(csv.DictReader((folder/'calls.csv').open(newline='')))
        first=next(c for c in calls if c['phase']=='master' and c['stage']=='after')
        assert int(first['status']) in [2,9,11] and int(first['solutions'])>0
        v=values(solution)
        text=(ROOT/p['input_path']).read_text();initial=vector(text,'initial');target=vector(text,'target');weights=vector(text,'weights')
        if abs(max(weights[1:])-10)<=1e-6:weights=[a/10 for a in weights]
        def integer(n):
            x=v[n];assert math.isfinite(x) and abs(x-round(x))<=1e-5,(n,x)
            return round(x)
        Y=[initial[0]]+[integer('Y_'+str(i)) for i in range(1,p['V']+1)]
        for i in range(1,p['V']+1):assert integer(f'state_{i}_{Y[i]}')==1
        r=[Y[i]/target[i] for i in range(1,p['V']+1)];S=sum(r)
        G=sum(abs(a-b) for i,a in enumerate(r) for b in r[i+1:])/(len(r)*S) if S else 0
        F=G+p['lambda']*sum(weights[i]*abs(Y[i]/target[i]-1) for i in range(1,p['V']+1))
        obj=v['G']+p['lambda']*sum(weights[i]*v['e_'+str(i)] for i in range(1,p['V']+1))
        assert obj+1e-7>=F,(obj,F)
        operations=[];visits=[0]*(p['V']+1)
        for k in range(p['M']):
            op=[]
            for i in range(1,p['V']+1):
                tail=f'{k}_{i}';z=integer('z_'+tail);pick=integer('p_'+tail);drop=integer('d_'+tail)
                assert z in [0,1] and pick>=0 and drop>=0 and not(pick and drop)
                assert bool(z)==bool(pick or drop)
                if z:assert pick==max(initial[i]-Y[i],0) and drop==max(Y[i]-initial[i],0)
                visits[i]+=z;op.append(pick-drop)
            operations.append(op)
        assert all(visits[i]==int(Y[i]!=initial[i]) for i in range(1,p['V']+1))
        for k,op in enumerate(operations):
            if not any(op):continue
            mode=dest/f'{p["id"]}_k{k}';mode.mkdir()
            with (mode/'pattern.txt').open('x') as f:f.write(' '.join(map(str,op))+'\n')
            record=dict(id=p['id'],panel=p,vehicle=k,operations=op,stations=sum(x!=0 for x in op),
                inventory=Y,master_F=F,master_objective=obj,master_model_sha256=sha(folder/'master_1.lp'),
                master_solution_sha256=sha(solution),source=str(solution.relative_to(ROOT)),
                source_status=int(first['status']),
                source_class=('optimal_integer_master_candidate' if int(first['status'])==2 else
                              'nonoptimal_integer_master_incumbent_diagnostic_only'),path=str(mode.relative_to(ROOT)))
            write(mode/'mode.json',record);manifest.append(record)
    write(dest/'manifest.json',dict(modes=manifest,count=len(manifest),production_handoff=False))
    print(json.dumps(dict(label=label,modes=len(manifest),stations=[m['stations'] for m in manifest])))

def run(label,number,cap,core):
    manifest=read(OUT/'modes'/label/'manifest.json');m=manifest['modes'][number-1];p=m['panel'];dest=ROOT/m['path']/'native'
    assert not dest.exists();cmd=[BUILD/'Round105Oracle.exe',ROOT/p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],
        p['lambda'],m['vehicle'],ROOT/m['path']/'pattern.txt',dest,cap,int(core)]
    write(ROOT/m['path']/'native_launch.json',dict(command=list(map(str,cmd)),binary_sha256=sha(BUILD/'Round105Oracle.exe'),
        master_model_sha256=m['master_model_sha256'],pattern_sha256=sha(ROOT/m['path']/'pattern.txt')))
    start=time.perf_counter();r=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),timeout=cap+20)
    write(ROOT/m['path']/'native_completion.json',dict(returncode=r.returncode,outer_seconds=time.perf_counter()-start))
    assert r.returncode==0
    result=read(dest/'result.json')
    if result['status']==0:
        v=values(dest/'oracle/full.lp.sol');current=0;nodes=[0];ops=[];seen=set()
        while True:
            nxt=[j for j in range(p['V']+1) if j!=current and v[f'x_{current}_{j}']>0.5]
            assert len(nxt)==1
            j=nxt[0];nodes.append(j)
            if not j:break
            assert j not in seen;seen.add(j);q=m['operations'][j-1];assert q
            ops.append(dict(station=j,pickup=max(q,0),drop=max(-q,0)));current=j
        assert seen=={i+1 for i,x in enumerate(m['operations']) if x}
        witness=dict(routes=[dict(vehicle=m['vehicle'],nodes=nodes,operations=ops)])
        # Independent physical reader requires a reported objective; recompute
        # local-route resulting inventory from input and the fixed operations.
        text=(ROOT/p['input_path']).read_text();Y=vector(text,'initial');target=vector(text,'target');weights=vector(text,'weights')
        if abs(max(weights[1:])-10)<=1e-6:weights=[x/10 for x in weights]
        for i,q in enumerate(m['operations'],1):Y[i]-=q
        ratios=[Y[i]/target[i] for i in range(1,p['V']+1)];S=sum(ratios)
        G=sum(abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:])/(p['V']*S) if S else 0
        witness['objective']=G+p['lambda']*sum(weights[i]*abs(Y[i]/target[i]-1) for i in range(1,p['V']+1))
        checked=physical.physical(p,witness);assert checked['original_T_feasible']
        write(dest/'independent_route.json',dict(witness=witness,check=checked))
    print(json.dumps(dict(id=m['id'],vehicle=m['vehicle'],stations=m['stations'],result=result)))

def controls(campaign,label):
    dest=OUT/'modes'/label;dest.mkdir(parents=True,exist_ok=False)
    identity=read(OUT/campaign/'identity.json');manifest=[]
    launch=next(a for a in identity['launches'] if a['id']=='R98-C2')
    seed=Path(launch['destination'])/'external/round105/seed.json';w=read(seed);p=launch['panel']
    for k in [0,1]:
        route=next(r for r in w['routes'] if r['vehicle']==k);op=[0]*p['V']
        for o in route['operations']:
            assert op[o['station']-1]==0
            op[o['station']-1]=o['pickup']-o['drop']
        assert any(op);mode=dest/f'R98-C2_seed_k{k}';mode.mkdir()
        (mode/'pattern.txt').write_text(' '.join(map(str,op))+'\n')
        record=dict(id='R98-C2',panel=p,vehicle=k,operations=op,stations=sum(x!=0 for x in op),
            master_model_sha256=None,source_sha256=sha(seed),source=str(seed.relative_to(ROOT)),
            source_class='self_paid_current_run_seed_positive_control',path=str(mode.relative_to(ROOT)))
        write(mode/'mode.json',record);manifest.append(record)
    write(dest/'manifest.json',dict(modes=manifest,count=len(manifest),production_handoff=False))
    print(json.dumps(dict(label=label,controls=len(manifest))))

def batch(plan_path):
    plan=read(plan_path);jobs=plan['jobs'];assert 1<=len(jobs)<=12
    assert len({(j['label'],j['number']) for j in jobs})==len(jobs)
    # This is a finite diagnostic campaign, never a production per-car cap.
    # One outer recorder bills elapsed time once; each child launch is exposed.
    target=OUT/plan['output'];assert not target.exists();target.mkdir()
    write(target/'launch.json',dict(plan_sha256=sha(plan_path),declared_children=len(jobs),
          production_handoff=False,jobs=jobs,oracle_binary_sha256=sha(BUILD/'Round105Oracle.exe')))
    for seq,j in enumerate(jobs,1):
        write(target/f'{seq:02d}_before.json',dict(job=j,started_unix=time.time()))
        start=time.perf_counter();run(j['label'],int(j['number']),float(j['cap_seconds']),j['mode']=='core')
        write(target/f'{seq:02d}_after.json',dict(job=j,outer_seconds=time.perf_counter()-start,completed=True))
    write(target/'completion.json',dict(children=len(jobs),completed=True))

def summarize():
    rows=[];proofs=[]
    for label in ['F2_01','C2_01','F5_01','C2_controls01']:
        for m in read(OUT/'modes'/label/'manifest.json')['modes']:
            dest=ROOT/m['path']/'native';result=read(dest/'result.json')
            calls=list(csv.DictReader((dest/'calls.csv').open(newline='')))
            after=[c for c in calls if c['stage']=='after'];assert len(after)*2==len(calls)
            timing={phase:sum(float(c['seconds']) for c in after if c['phase']==phase)
                    for phase in ['oracle','iis','core_confirm']}
            core=result['core'];pos=sum(m['operations'][i-1]!=0 for i in core);neg=len(core)-pos
            row=dict(label=label,id=m['id'],vehicle=m['vehicle'],stations=m['stations'],
                     source_class=m['source_class'],status=result['status'],core_confirmed=result['core_confirmed'],
                     groups=len(core),positive_groups=pos,negative_groups=neg,
                     **timing,outer_seconds=read(ROOT/m['path']/'native_completion.json')['outer_seconds'])
            if result['status']==1:
                v=values(ROOT/m['source']);start=values((ROOT/m['source']).parent/'start.mst')
                text=(ROOT/m['panel']['input_path']).read_text();b=vector(text,'initial');coeff={}
                for i in core:
                    op=m['operations'][i-1];z=f'z_{m["vehicle"]}_{i}'
                    coeff[z]=1 if op else -1
                    if op:coeff[f'state_{i}_{b[i]-op}']=1
                rhs=2*pos-1
                current=sum(c*v[n] for n,c in coeff.items());seed=sum(c*start[n] for n,c in coeff.items())
                assert abs(current-rhs-1)<1e-5 and seed<=rhs+1e-7
                if result['core_confirmed']:
                    full=(dest/'oracle/full.lp').read_text();free=(dest/'oracle/core_confirm.lp').read_text()
                    pattern=r'(?m)^\s*a_[0-9]+_[zpd]:[^\n]*\n'
                    assert re.sub(pattern,'',full)==re.sub(pattern,'',free)
                    names=set(int(i) for i in re.findall(r'(?m)^\s*a_([0-9]+)_[zpd]:',free))
                    assert names==set(core)
                    assert next(c for c in after if c['phase']=='core_confirm')['status']=='3'
                quality=read(str(ROOT/m['source']).removesuffix('.sol')+'.quality.json')
                assert quality['ConstrVio']<=1e-6 and quality['IntVio']<=1e-5
                row.update(current_violation=current-rhs,seed_slack=rhs-seed,
                           nonredundant_at_verified_master_point=True,literal_region_strictly_larger=len(core)<m['panel']['V'])
                proofs.append(dict(path=m['path'],core=core,coefficients=coeff,rhs=rhs,
                    current_activity=current,seed_activity=seed,source_sha256=sha(ROOT/m['source']),
                    free_template_nonassumption_bytes_identical=result['core_confirmed']))
            else:
                assert result['status']==0 and (dest/'independent_route.json').exists()
                row.update(current_violation=None,seed_slack=None,nonredundant_at_verified_master_point=None,
                           literal_region_strictly_larger=None)
            rows.append(row)
    write(OUT/'real_modes_report01.json',dict(rows=rows,proofs=proofs,
        native_master_modes=9,positive_controls=2,qualified_infeasible=sum(r['status']==1 for r in rows),
        stronger_core_scope='Strict literal-region inclusion; no count of additional feasible master points asserted',
        rational_infeasibility_certificate=False,third_perspective=False))
    with (OUT/'real_modes.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(dict(modes=len(rows),infeasible=sum(r['status']==1 for r in rows),
        confirmed_cores=sum(r['core_confirmed'] for r in rows),seconds=sum(r['outer_seconds'] for r in rows))))

if __name__=='__main__':
    if sys.argv[1]=='extract':extract(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='run':run(sys.argv[2],int(sys.argv[3]),float(sys.argv[4]),sys.argv[5]=='core')
    elif sys.argv[1]=='batch':batch(sys.argv[2])
    elif sys.argv[1]=='controls':controls(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='summarize':summarize()
    else:raise ValueError('extract|run|batch|controls|summarize only')
