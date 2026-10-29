"""Exact TC2 arithmetic, selective historical recovery and zero-Optimize checks."""
from round140_common import *
from fractions import Fraction as F
from round134_count_bound import count_coefficients, downward
import bisect, collections, csv, gzip, itertools, re, zipfile
import round108_reader as core

ROLES=['K-20-S','R-B35-S-T2','R-X35-S-T2','K-35-U','R-X20-S-T1']

def count_rows(supports,ratios,Bminus,B):
    supports={i:sorted(set(ys)) for i,ys in supports.items()}
    ratios={i:F(v) for i,v in ratios.items()}
    old=count_coefficients(supports,ratios,B)
    lo=max(F(Bminus),sum(min(v) for v in supports.values()))
    hi=min(F(B),sum(max(v) for v in supports.values()))
    if old['inventory_domain_infeasible'] or lo>hi:
        return dict(inventory_domain_infeasible=True)
    n=len(supports);coef={key:F(0) for key in old['coefficients']};constant=F(0);rows=[]
    for row in old['thresholds']:
        t=F(row['t']);delta=F(row['delta']);H=[];L=[];O=[];c0=0
        for i,ys in supports.items():
            k=bisect.bisect_left([ratios[i]*y for y in ys],t)
            if k==0:H.append(i);c0+=ys[-1]
            elif k==len(ys):L.append(i);c0+=ys[-1]
            else:O.append((ys[-1]-ys[k-1],i,ys[k-1]));c0+=ys[k-1]
        gains=sorted(O,reverse=True);q=0;total=c0
        while total<lo and q<len(gains):total+=gains[q][0];q+=1
        if total<lo or len(H)+q>row['u']:
            return dict(inventory_domain_infeasible=True)
        ell=len(H)+q;u=row['u'];slope=n-ell-u
        for i,ys in supports.items():
            for y in ys:
                if ratios[i]*y>=t:coef[i,y]+=delta*slope
        constant+=delta*ell*u
        rows.append(dict(row,ell=ell,forced_low=L,optional_maximum_gains=gains,C0=c0,
                         lower_activations=q,slope=slope))
    return dict(inventory_domain_infeasible=False,TC=old['coefficients'],TC2=coef,
                constant=constant,thresholds=rows,Bminus=lo,B=hi)

def model_counts(model,Bminus,B):
    supports=collections.defaultdict(list);ratios={}
    for name in model['order']:
        match=re.fullmatch(r'state_(\d+)_(\d+)',name)
        if match:supports[int(match[1])].append(int(match[2]))
    for terms,sense,rhs in model['rows']:
        d=dict(terms)
        if sense=='=' and rhs==0 and len(d)==2:
            for name,c in terms:
                match=re.fullmatch(r'r_(\d+)',name)
                if match and c==1 and f'Y_{match[1]}' in d:ratios[int(match[1])]=F(-d[f'Y_{match[1]}'])
    assert set(supports)==set(ratios)
    result=count_rows(supports,ratios,Bminus,B)
    result.update(supports=supports,ratios=ratios)
    return result

def serializable(c):
    return dict(inventory_domain_infeasible=c['inventory_domain_infeasible'],
        TC={f'state_{i}_{y}':downward(v) for (i,y),v in c['TC'].items() if v},
        TC2={f'state_{i}_{y}':downward(v) for (i,y),v in c['TC2'].items() if v},
        TC_exact={f'state_{i}_{y}':str(v) for (i,y),v in c['TC'].items() if v},
        TC2_exact={f'state_{i}_{y}':str(v) for (i,y),v in c['TC2'].items() if v},
        constant=downward(c['constant']),constant_exact=str(c['constant']),
        Bminus=str(c['Bminus']),B=str(c['B']),thresholds=c['thresholds'],
        supports=c['supports'],ratios={str(i):str(v) for i,v in c['ratios'].items()},
        lower_positive=sum(r['ell']>0 for r in c['thresholds']),
        negative_slopes=sum(r['slope']<0 for r in c['thresholds']),
        negative_coefficients=sum(v<0 for v in c['TC2'].values()))

def evaluate(point,add,n):
    H=math.fsum(v for name,v in point.items() if re.fullmatch(r'h_\d+_\d+',name))
    old=math.fsum(v*point[name] for name,v in add['TC'].items())
    new=add['constant']+math.fsum(v*point[name] for name,v in add['TC2'].items())
    return dict(H_sum=H,TC_rhs=old,TC2_rhs=new,TC2_violation=new-H,
        G=point['G'],tau=math.fsum(point[f'Y_{i}'] for i in range(1,n+1)),
        J=math.fsum(point[f'zprod_{i}'] for i in range(1,n+1)))

def tiny():
    c=count_rows({i:[0,1,2] for i in range(1,5)},{i:F(1) for i in range(1,5)},3,5)
    assert [(r['ell'],r['u']) for r in c['thresholds']]==[(2,4),(0,2)]
    s={key:F(1,2) if key[1]==0 else F(1,4) for key in c['TC']}
    old=sum(v*s[k] for k,v in c['TC'].items());new=c['constant']+sum(v*s[k] for k,v in c['TC2'].items())
    assert (old,new)==(2,6)
    checked=0
    # Exhaustive integer-selector validity, including restricted/nonuniform supports.
    cases=[({i:[0,1,2] for i in range(1,5)},{i:F(1) for i in range(1,5)},3,5),
           ({1:[0,2],2:[1,3],3:[0,1,4]},{1:F(.1),2:F(.2),3:F(.3)},4,6)]
    for supports,ratios,bm,b in cases:
        a=count_rows(supports,ratios,bm,b)
        for ys in itertools.product(*supports.values()):
            if not bm<=sum(ys)<=b:continue
            r=[ratios[i]*y for i,y in zip(supports,ys)]
            A=sum(abs(x-y) for j,x in enumerate(r) for y in r[j+1:])
            rhs=a['constant']+sum(a['TC2'][i,y] for i,y in zip(supports,ys))
            assert rhs<=A
            for row in a['thresholds']:
                K=sum(x>=F(row['t']) for x in r);assert row['ell']<=K<=row['u']
            checked+=1
    write(OUT/'math/tiny_exact.json',dict(PASS=True,Optimize=0,scope='strict product/selector/Gini relaxation block; no full BRP strictness or objective gain claimed',
        intervals=[[2,4],[0,2]],selector=['1/2','1/4','1/4'],tau='3',K=['2','1'],
        TC_rhs=str(old),TC2_rhs=str(new),H_sum='2',g='1/6',J='1/2',
        exact_products=True,stock_four_rows_satisfied=True,integer_points_checked=checked))

def recover():
    tick=time.perf_counter();old=ROOT/'results/unified_exact_round138';dest=OUT/'inherited';dependencies=[]
    manifest=read(old/'carrier_manifest.json')
    for archive_name in ['diagnostics_and_failures','campaign_007']:
        path=old/f'artifacts/{archive_name}.zip';info=next(x for x in manifest['carriers'] if x['path']==path.relative_to(ROOT).as_posix())
        assert sha(path)==info['SHA256'];members=[]
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                keep=('roots/' in name and name.endswith(('scope.json','additions.json','result.json','solution.json.gz','original.lp','plan.json')))
                if archive_name=='campaign_007':keep=name.endswith(('L0_epoch_0_generation_1.lp','round127_root_lp.csv','round127_root_lp_status.json','initial_witness.json','paper_optimize_ledger.csv','lp_status_ledger.csv'))
                if not keep:continue
                relative=name.split('results/unified_exact_round138/',1)[1]
                target=dest/relative;data=z.read(name)
                if target.exists():assert target.read_bytes()==data
                else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        dependencies.append(dict(pin='1b19897ab5819ab3b7485ddc978954b45225f361',path=info['path'],SHA256=info['SHA256'],members=members))
    histories=[];positions=[]
    reuse=read(ROOT/'results/unified_exact_round139/baseline_reuse.json')
    write(OUT/'baseline_reuse.json',dict(reuse,source='Round139 accepted BASE/BOTH records; original costs and V1/V2 identities retained',new_Optimize=0))
    for role in ROLES:
        folder=OUT/'roots'/role;folder.mkdir(parents=True,exist_ok=True)
        if role!='R-B35-S-T2':
            scope=read(dest/'roots'/role/'scope.json');added=read(dest/'roots'/role/'additions.json')
            base=dest/'roots'/role/'inherited/original.lp'
            stock=dest/Path(added['stock_model']).relative_to('results/unified_exact_round138')
            assert sha(stock)==added['stock_export_SHA'] and sha(base)==added['base_SHA']
            source_results={}
            for variant in ['base','stock','tc','tc_stock']:
                result=read(dest/'roots'/role/variant/'result.json');point_path=dest/'roots'/role/variant/'solution.json.gz'
                assert sha(point_path)==result['solution_SHA']
                with gzip.open(point_path,'rt') as f:point=json.load(f)
                source_results[variant]=(result,point)
        else:
            b=next(x for x in reuse['positions'] if x['role']==role);p=b['panel']
            raw=next((dest/'campaign/007/raw').iterdir())/'external'
            base=None;stock=raw/'models/L0_epoch_0_generation_1.lp';m=core.lp_model(stock)
            point={r['name']:float(r['value']) for r in csv.DictReader((raw/'round127_root_lp.csv').open())}
            calls=list(csv.DictReader((raw/'paper_optimize_ledger.csv').open()))
            call=next(x for x in calls if x['leaf_id']=='L0' and x['solve_kind']=='LP')
            assert sha(stock)==call['model_sha256'] and set(point)==set(m['order'])
            data=core.evidence.instance(ROOT,p);B=sum(data['b'][1:]);Bm=max(0,B-sum(p['Q_vector']))
            physical=core.evidence.physical(ROOT,p,read(raw/'initial_witness.json'))
            scope=dict(panel=p,alpha=m['bounds']['G'][0],beta=m['bounds']['G'][1],B=B,Bminus=Bm,validated_U=physical['F'])
            scope['L_saved']=sum(v*point[k] for k,v in m['objective'][0])+m['objective'][1]
            source_results={'stock_saved':(dict(L=scope['L_saved']),point)}
        model=core.lp_model(stock);start=time.perf_counter();counts=model_counts(model,scope['Bminus'],scope['B']);add=serializable(counts)
        add['construction_seconds']=time.perf_counter()-start
        scope.update(stock_model=str(stock),base_model=str(base) if base else None,stock_SHA=sha(stock),base_SHA=sha(base) if base else None)
        write(folder/'scope.json',scope);write(folder/'additions.json',add)
        facts=[]
        for variant,(result,point) in source_results.items():
            if role!='R-B35-S-T2':assert add['TC']==added['TC']
            facts.append(dict(variant=variant,L=result['L'],**evaluate(point,add,scope['panel']['V'])))
        histories.append(dict(role=role,points=facts,thresholds=len(add['thresholds']),lower_positive=add['lower_positive'],negative_coefficients=add['negative_coefficients']))
        variants=['stock','tc_stock','tc2_stock'] if role=='R-B35-S-T2' else ['tc2_stock']
        if role in ['K-20-S','R-B35-S-T2']:variants+=['tc2']
        for v in variants:positions.append(dict(position=len(positions)+1,role=role,variant=v,seed=0,cap_seconds=120))
    write(OUT/'historical_points.json',dict(UTC=utc(),Optimize=0,roles=histories,dependencies=dependencies,seconds=time.perf_counter()-tick))
    write(OUT/'LP_plan.json',dict(UTC=utc(),positions=positions,Seed=0,Threads=1,serial=True,affinity_mask=4,
        scope='Frozen historical continuous LP domains; numerical optimum, not Native MIP root or complete method',no_new_Optimize=True))
    write(OUT/'start_receipt.json',dict(UTC=utc(),base=BASE,main=git('rev-parse','origin/main').decode().strip(),R139_in_main=False,
        branch=git('branch','--show-current').decode().strip(),PR_base='codex/round139-stock-rlt-placement',
        no_active_solver_at_start=True,protected_original='E:/codes/ExactEBRP',compute_limit_seconds=43200,
        Gurobi_Seed=0,H_seed=20260626,goal_SHA=sha(OUT/'goal.md'),
        workspace_policy='New build/raw/temp/restore under ExactEBRP-work; bounded current-round cleanup after evidence and public acceptance'))
    print(json.dumps(histories,indent=2))

if __name__=='__main__':globals()[sys.argv[1]]()
