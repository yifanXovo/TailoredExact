"""Small independent Fraction/compiled-writer/actual-transport qualifications."""
import gzip,collections
from round145_math import F,project,joint_rows,row_activity
from round143_qualify import expected_rows
from round145_lp import domain,semantics,residual,add_rows,save_gz
from round145_common import *
configure()

def dump_input(path,cols,rows):
    names=list(cols);index={k:i for i,k in enumerate(names)}
    with path.open('w',encoding='utf-8',newline='\n') as f:
        f.write(f'{len(names)} {len(rows)}\n')
        for k,c in cols.items():f.write(f'{k} {c["LB"]:.17g} {c["UB"]:.17g} {c.get("X",0):.17g} {c.get("RC",0):.17g} {c.get("VBasis",0)}\n')
        for r in rows:
            f.write(f'{r["name"]} {r["sense"]} {r["rhs"]:.17g} {r["Pi"]:.17g} {r.get("CBasis",0)} {len(r["terms"])}')
            for k,v in r['terms'].items():f.write(f' {index[k]} {v:.17g}')
            f.write('\n')

def exact_check(cols,rows,cpp):
    bounds={k:(c['LB'],c['UB']) for k,c in cols.items()};oracle=project(rows,bounds)
    a={k:-F(v) for k,v in oracle['exact_terms'].items()};b=-F(oracle['exact_projected_rhs']);margin=F(0)
    for k in set(a)|set(cpp['terms']):
        error=F(cpp['terms'].get(k,0))-a.get(k,F(0));lo,hi=map(F,bounds[k]);margin+=max(error*lo,error*hi)
    slack=F(cpp['rhs'])-b-margin;assert slack>=0,slack
    assert not any(k.startswith('rn_') for k in cpp['terms'])
    return dict(PASS=True,exact_nonnegative_validity_margin=str(slack),margin=float(slack),
        complete_source_rows=len(rows),nonzeros=len(cpp['terms']),sign_repairs=oracle['sign_repairs'],RN_columns=0)

def compiled_block(spec,target):
    q=read(OUT/'qualification_driver.json');assert sha(q['PE'])==q['PE_SHA'];support={int(i):ys for i,ys in spec['supports'].items()}
    inp=target.with_suffix('.txt');inp.parent.mkdir(parents=True,exist_ok=True)
    with inp.open('w') as f:
        f.write(f'{len(support)} {spec["Bminus"]} {spec["B"]}\n')
        for i,ys in support.items():f.write(f'{spec["c_binary64"][str(i)]:.17g} {len(ys)} '+ ' '.join(map(str,ys))+'\n')
    r=subprocess.run([q['PE'],'block',str(inp),str(target)],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr
    return read(target)

def production_joint_rows(spec):
    """Independent Fraction oracle for the R140-down coefficients and TS RHS."""
    from round140_math import count_rows
    from round134_count_bound import downward
    support={int(i):ys for i,ys in spec['supports'].items()};ratios={int(i):F(c) for i,c in spec['c_binary64'].items()}
    count=count_rows(support,ratios,spec['Bminus'],spec['B']);n=len(support);rows=[]
    H={f'rn_h_{i}_{j}':1. for i in support for j in support if i<j}
    for number,key,b in [(1,'TC',0),(2,'TC2',count['constant'])]:
        terms=dict(H);terms.update({f'rn_w_{i}_{y}':-downward(v) for (i,y),v in count[key].items() if v})
        if number==2 and b:terms['rn_t']=-downward(b)
        rows.append(dict(name=f'r145_NC{number}',sense='>',rhs=0.,terms=terms))
    for k,slope,endpoint,sense in [(1,spec['L_t'],count['Bminus'],'>'),(2,spec['U_t'],count['B'],'>'),(3,spec['U_t'],count['Bminus'],'<'),(4,spec['L_t'],count['B'],'<')]:
        terms={f'rn_Y_{i}':1. for i in support};terms.update({f'Y_{i}':-slope for i in support})
        if endpoint:terms['rn_t']=-float(endpoint)
        rows.append(dict(name=f'r145_TS{k}',sense=sense,rhs=math.nextafter(-slope*float(endpoint),-math.inf if sense=='>' else math.inf),terms=terms))
    for r in rows:
        smallest=min([1.]+[abs(v) for v in r['terms'].values() if v]);scale=0
        while math.ldexp(smallest,scale)<1e-12:scale+=1
        r['terms']={k:math.ldexp(v,scale) for k,v in r['terms'].items() if v};r['rhs']=math.ldexp(r['rhs'],scale)
    return rows

def fixtures():
    configure();tick=time.perf_counter();facts=[]
    from round143_math import denominator,outward
    cases=[('binary4',{i:[0,1] for i in range(1,5)},{i:1. for i in range(1,5)},1,3),
        ('heterogeneous_holey',{1:[0,2],2:[1,3],3:[0,1,4]},{1:.1,2:.2,3:.3},4,6)]
    for role in ('K-35-U','R-X20-S-T1','K-20-S'):
        d=domain(role);cases.append((role,{int(i):ys for i,ys in d['spec']['supports'].items()},
            {int(i):c for i,c in d['spec']['c_binary64'].items()},d['spec']['Bminus'],d['spec']['B']))
    for tag,s,c,bm,b in cases:
        spec=denominator(c,s,bm,b)
        spec['L_t']=math.nextafter(1/outward(F(spec['S_U_exact']),True),-math.inf)
        spec['U_t']=math.nextafter(1/outward(F(spec['S_L_exact']),False),math.inf)
        spec=json.loads(json.dumps(spec));actual=compiled_block(spec,OUT/'qualification/blocks'/(tag+'.json'))
        expected=expected_rows(spec)+production_joint_rows(spec);assert actual['rows']==expected
        assert len([r for r in actual['rows'] if r['name'].startswith('r145_')])==6
        physical=[]
        if tag=='binary4':
            vectors=[{i:int(i==j) for i in s} for j in s]+[{i:int(i!=j) for i in s} for j in s]
        elif tag=='heterogeneous_holey':vectors=[{1:0,2:1,3:4},{1:2,2:3,3:0}]
        else:vectors=[]
        for y in vectors:
            S=sum(F(c[i])*y[i] for i in s);t=1/S;p={'rn_t':t}
            for i,ys in s.items():
                p[f'Y_{i}']=F(y[i]);p[f'rn_Y_{i}']=t*y[i]
                for z in ys:p[f'state_{i}_{z}']=F(z==y[i]);p[f'rn_w_{i}_{z}']=t*(z==y[i])
            A=sum(abs(F(c[i])*y[i]-F(c[j])*y[j]) for i in s for j in s if i<j)
            p['G']=A/(len(s)*S)
            for i in s:
                for j in s:
                    if i<j:p[f'rn_h_{i}_{j}']=abs(F(c[i])*y[i]-F(c[j])*y[j])*t
            for r in actual['rows']:
                lhs=sum(F(a)*p[k] for k,a in r['terms'].items());rhs=F(r['rhs'])
                assert lhs>=rhs if r['sense']=='>' else lhs<=rhs if r['sense']=='<' else lhs==rhs
            for k,(lo,hi) in actual['columns'].items():assert F(lo)<=p[k]<=F(hi)
            physical.append(dict(y=y,G=str(p['G']),all_RN_NC_TS_and_caps_exact=True))
        facts.append(dict(tag=tag,rows=len(expected),columns=len(actual['columns']),actual_all_coefficients_senses_RHS_equal_independent_oracle=True,physical=physical))
    # Signed coefficients, NC constant*t, Y retention and zero projection/reset.
    q=read(OUT/'qualification_driver.json');root=OUT/'qualification/project';root.mkdir(parents=True,exist_ok=True)
    cols={'G':dict(LB=0.,UB=1.),'Y_1':dict(LB=0.,UB=5.),'state_1_0':dict(LB=0.,UB=1.),'rn_t':dict(LB=.1,UB=.5),'rn_z':dict(LB=-2.,UB=3.)}
    rows=[dict(name='rn_eq',sense='=',rhs=.1,Pi=-.7,terms={'G':.5,'rn_z':1.}),
        dict(name='r145_NC2',sense='>',rhs=0.,Pi=.3,terms={'rn_z':1.,'rn_t':-2.,'state_1_0':-.2}),
        dict(name='r145_TS4',sense='<',rhs=-.5,Pi=-.4,terms={'Y_1':-.1,'rn_t':-5.,'rn_z':1.}),
        dict(name='rn_bad_sign',sense='>',rhs=99.,Pi=-1e-15,terms={'G':1.})]
    for tag,rr in [('mixed',rows),('zero',[dict(r,Pi=0.) for r in rows])]:
        inp=root/(tag+'.txt');evidence=root/(tag+'.json');dump_input(inp,cols,rr)
        result=subprocess.run([q['PE'],'project',str(inp),str(evidence)],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr;cpp=json.loads(result.stdout);assert cpp['reset_test']
        check=exact_check(cols,rr,cpp)
        if tag=='mixed':assert 'Y_1' in cpp['terms'] and len(check['sign_repairs'])==1
        else:assert not cpp['terms'] and cpp['rhs']>=0
        facts.append(dict(tag=tag,**check))
    write(OUT/'qualification_exact_writer.json',dict(PASS=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,facts=facts,driver_SHA=q['PE_SHA']))
    print('PASS exact NC/TS production rows, signed/mixed projection, complete block, zero/reset and physical extensions')

def compact(role):
    configure()
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    source=OUT/'LP'/f'{role}_joint';raw=json.loads(gzip.decompress((source/'primal_dual_matrix.json.gz').read_bytes()))
    extra=read(source/'new_rows.json')['actually_added'];wanted={r['name'] for r in expected_rows(domain(role)['spec'])}|set(extra)
    rows=[r for r in raw['rows'] if r['name'] in wanted];assert len(rows)==len(wanted)
    target=OUT/'compact'/role;target.mkdir(parents=True,exist_ok=False);inp=target/'projection_input.txt';dump_input(inp,raw['columns'],rows)
    q=read(OUT/'qualification_driver.json');assert sha(q['PE'])==q['PE_SHA']
    r=subprocess.run([q['PE'],'project',str(inp),str(target/'compiled_projection.json')],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr;cpp=json.loads(r.stdout);check=exact_check(raw['columns'],rows,cpp)
    assert read(target/'compiled_projection.json')['source_rows']==[r['name'] for r in rows]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(domain(role)['base']),env=env) as model:
            old=semantics(model);names={v.VarName for v in model.getVars()};oldrows={c.ConstrName for c in model.getConstrs()}
            row=dict(name='r145_PC',sense='<',rhs=cpp['rhs'],terms=cpp['terms']);add_rows(model,[row],gp)
            assert semantics(model,names,oldrows)==old and not any(v.VarName.startswith('rn_') for v in model.getVars())
            model.write(str(target/'compact.mps'))
        with gp.read(str(target/'compact.mps'),env=env) as model:
            assert semantics(model,names,oldrows)==old;c=model.getConstrByName('r145_PC');e=model.getRow(c)
            assert c.Sense=='<' and c.RHS==cpp['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==cpp['terms']
            model.Params.Seed=0;model.Params.Threads=1;model.Params.TimeLimit=120;model.Params.OutputFlag=1;model.Params.LogToConsole=0;model.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',model_SHA=sha(target/'compact.mps'),Seed=0,Threads=1))
            tick=time.perf_counter();model.optimize();elapsed=time.perf_counter()-tick
            write(target/'return.json',dict(UTC=utc(),Status=model.Status,Runtime=model.Runtime,Work=model.Work,optimize_wall=elapsed));assert model.Status==gp.GRB.OPTIMAL
            xp={v.VarName:v.X for v in model.getVars()};quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']};res=residual(model,xp)
            assert max(quality.values())<=1e-6 and max(res['constraints'],res['bounds'])<=1e-6
            sr=read(source/'result.json');baseline=read(ROOT/'results/unified_exact_round144/LP'/f'{role}_base'/'result.json')['old_L']
            result=dict(role=role,L=model.ObjVal,joint_source_L=sr['L'],root_retention_loss=sr['L']-model.ObjVal,
                increment_over_BASE=model.ObjVal-baseline,retention_fraction=(model.ObjVal-baseline)/(sr['L']-baseline),
                NC_TS_increment_retained_fraction=(model.ObjVal-sr['inherited_RN_L'])/sr['gain_over_RN'],
                Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs,
                qualified=True,quality=quality,residual=res,PC_rows=1,PC_nonzeros=len(cpp['terms']),RN_columns=0,
                complete_block_exact_check=check,actual_Native_readback=True,model_SHA=sha(target/'compact.mps'),source_SHA=sha(source/'model.mps'),Seed=0,Threads=1,LP_Optimize=1)
            save_gz(target/'solution.json.gz',xp);write(target/'result.json',result)
    print(json.dumps(result),flush=True)

def run(role):
    configure();assert metered('compact_'+role,'diagnostic',[LP_PYTHON,'-B',__file__,'compact',role],180,240)==0
if __name__=='__main__':
    if sys.argv[1] in ('run','compact'):globals()[sys.argv[1]](sys.argv[2])
    else:globals()[sys.argv[1]]()
