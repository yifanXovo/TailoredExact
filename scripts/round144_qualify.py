"""Targeted Fraction/C++/Native transport checks; no resource-generator revival."""
import gzip,collections
from fractions import Fraction as F
from round144_lp import projected
from round143_lp import residual,semantics
from round143_qualify import point_residual
import round108_reader as parser
from round144_build import COMPILER,SYSTEM
from round144_common import *
configure()

def compile_driver():
    m=read(OUT/'candidate_manifest.json');b=Path(m['production_PE']).parent;pe=b/'Round144Project.exe'
    assert metered('compile_project_driver'+os.environ.get('R144_QUAL_SUFFIX',''),'build',[COMPILER,*m['flags'],ROOT/'scripts/round144_project.cpp',b/'ObjectiveResourceCompression.o','-o',pe],timeout=120)==0
    write(OUT/'qualification_driver.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round144_project.cpp')))

def writer():
    m=read(OUT/'candidate_manifest.json');b=Path(m['production_PE']).parent;pe=b/'Round144Writer.exe'
    assert metered('compile_writer_driver','build',[COMPILER,*m['flags'],ROOT/'scripts/round144_writer.cpp',*m['objects'],m['archive']['path'],*SYSTEM,'-o',pe],timeout=180)==0
    write(OUT/'qualification_writer_build.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round144_writer.cpp')))
    assert metered('writer_cpp','diagnostic',[pe,OUT/'qualification/writer',ROOT/'results/unified_exact_round132/inputs/K-35-U.txt',OUT/'qualification/project/K-35-U_row.txt'],30,60)==0

def writer_native():
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA;root=OUT/'qualification/writer';facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for a,b in [('tiny_base','tiny_compact'),('tiny_child_base','tiny_child_compact'),('K35_off','K35_compact')]:
            old=parser.lp_model(root/(a+'.lp'));new=parser.lp_model(root/(b+'.lp'))
            assert all(old[k]==new[k] for k in ['order','bounds','types','objective'])
            difference=collections.Counter(new['rows'])-collections.Counter(old['rows'])
            assert sum(difference.values())==1 and collections.Counter(new['rows'])==collections.Counter(old['rows'])+difference
            assert not any(k.startswith('rn_') for k in new['order'])
            if a=='tiny_base':
                p=read(root/'tiny_start.json');check=point_residual(new,p);assert set(p)==set(new['order']) and max(check.values())<=1e-6
            else:check=None
            if a=='K35_off':assert old==parser.lp_model(ROOT/'results/unified_exact_round143/inherited/roots/K-35-U/inherited/original.lp')
            with gp.read(str(root/(b+'.lp')),env=env) as m:
                c=m.getConstrByName('r144_PC');e=m.getRow(c)
                wanted=next(iter(difference));actual=(tuple(sorted((e.getVar(i).VarName,e.getCoeff(i)) for i in range(e.size()))),{'<':'<=','>':'>=','=':'='}[c.Sense],c.RHS)
                assert actual==wanted
                assert {v.VarName:v.VType for v in m.getVars()}==new['types']
                for v in m.getVars():assert (v.LB,v.UB)==new['bounds'][v.VarName]
            facts.append(dict(base=a,compact=b,all_terms_RHS_types_bounds_read_back=True,columns=len(new['order']),PC_rows=1,RN_columns=0,complete_Start_residual=check))
    write(OUT/'qualification_native_writer.json',dict(PASS=True,Optimize=0,Native=binding(),facts=facts,actual_off_K35_equals_historical_BASE=True))
    print('PASS actual canonical compact writer, Native readback, physical complete Start, scope containment and off matrix')

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
    bounds={k:(c['LB'],c['UB']) for k,c in cols.items()};oracle=projected(rows,bounds)
    a={k:-F(v) for k,v in oracle['exact_terms'].items()};b=-F(oracle['exact_projected_rhs'])
    margin=F(0)
    for k in set(a)|set(cpp['terms']):
        error=F(cpp['terms'].get(k,0))-a.get(k,F(0));lo,hi=bounds[k];margin+=max(error*F(lo),error*F(hi))
    slack=F(cpp['rhs'])-b-margin;assert slack>=0,slack
    assert not any(k.startswith('rn_') for k in cpp['terms'])
    return dict(PASS=True,exact_safe_rhs=str(b+margin),actual_rhs=cpp['rhs'],exact_nonnegative_validity_margin=str(slack),
        numerical_validity_margin=float(slack),nonzeros=len(cpp['terms']),sign_repairs=oracle['sign_repairs'],RN_columns=0,
        ideal_projected_rhs=str(b),conversion_box_correction=str(margin))

def fraction():
    tick=time.perf_counter();q=read(OUT/'qualification_driver.json');assert sha(q['PE'])==q['PE_SHA'];facts=[]
    target=OUT/'qualification/project';target.mkdir(parents=True,exist_ok=True)
    if (OUT/'math/fixtures.json').exists():write(OUT/'math/history/fixtures_before_zero_dual_fix.json',read(OUT/'math/fixtures.json'))
    cases=[]
    cols={'G':dict(LB=-4.,UB=5.),'state_1_0':dict(LB=0.,UB=1.),'state_1_1':dict(LB=0.,UB=1.),'rn_z':dict(LB=-2.,UB=3.)}
    rows=[dict(name='rn_eq_neg',sense='=',rhs=.1,Pi=-.7,terms={'G':.5,'rn_z':1.}),
        dict(name='rn_ge',sense='>',rhs=-.2,Pi=.3,terms={'state_1_0':.2,'state_1_1':1e-14,'rn_z':.25}),
        dict(name='rn_le',sense='<',rhs=1.3,Pi=-.4,terms={'G':1.,'rn_z':-.5}),
        dict(name='rn_eq_pos',sense='=',rhs=.2,Pi=.15,terms={'G':-.2,'rn_z':.3}),
        dict(name='rn_bad_ge',sense='>',rhs=99.,Pi=-1e-15,terms={'G':1.}),
        dict(name='rn_bad_le',sense='<',rhs=-99.,Pi=1e-15,terms={'G':1.})]
    cases.append(('mixed_sense_signed_box_and_tiny_deletion',cols,rows))
    cases.append(('zero_RN_dual_redundant',cols,[dict(r,Pi=0.) for r in rows]))
    for role in ['K-35-U','R-X20-S-T1']:
        p=OUT/'LP'/f'{role}_base'/'primal_dual_matrix.json.gz';v=json.loads(gzip.decompress(p.read_bytes()))
        cases.append((role,v['columns'],[r for r in v['rows'] if r['name'].startswith('rn_')]))
    for tag,cols,rows in cases:
        source=target/(tag+'.txt');dump_input(source,cols,rows);evidence=target/(tag+'.json')
        r=subprocess.run([q['PE'],str(source),str(evidence)],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert r.returncode==0,r.stderr;cpp=json.loads(r.stdout);assert cpp['reset_test']
        check=exact_check(cols,rows,cpp);write(target/(tag+'_check.json'),check)
        evidence_data=read(evidence);assert len(evidence_data['variables'])==len(cols)
        assert evidence_data['sign_repairs']==len(check['sign_repairs'])
        if tag.startswith('mixed'):
            assert len(check['sign_repairs'])==2 and 'state_1_1' not in cpp['terms']
        else:
            with (target/(tag+'_row.txt')).open('w',encoding='utf-8') as f:
                f.write(f'{cpp["rhs"]:.17g} {len(cpp["terms"])}\n')
                for k,v in cpp['terms'].items():f.write(f'{k} {v:.17g}\n')
        facts.append(dict(tag=tag,**check,input_SHA=sha(source),evidence_SHA=sha(evidence),state_reset=True))
    # Exact local old-product witness, extended with an independent penalty p.
    # Raising p preserves this declared block and meets the scalar floor, while
    # the selector/G structural row still cuts it. No full routing claim.
    g=F(1,3);s10=F(0);s20=F(1,2);s31=F(0);floor=F(5,12);penalty=F(1,12)
    rhs=1-s10+s20/2-3*s31;assert rhs-3*g==F(1,4) and g+penalty==floor
    from itertools import product
    physical=[]
    for y in product([0,1],repeat=3):
        if not 1<=sum(y)<=2:continue
        G=sum(abs(F(y[i],sum(y))-F(y[j],sum(y))) for i in range(3) for j in range(i+1,3))/3
        R=1-(1-y[0])+F(1-y[1],2)-3*y[2];assert 3*G>=R
        physical.append(dict(y=y,G=str(G),slack=str(3*G-R)))
    write(OUT/'math/fixtures.json',dict(PASS=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,
        compiled_fraction_checks=facts,integer_local_physical_checks=physical,
        floor_separation=dict(scope='Three-site old Gini/stock/TC/TC2/endpoint-product block plus independent nonnegative penalty epigraph; not full routing P',
            old_g='1/3',PC_requires='5/12',penalty='1/12',scalar_objective_floor='5/12',PC_violation='1/4',
            conclusion='A structural PC can exclude a floor-feasible point in this declared rational block. No universal/full-routing dominance claimed.')))
    print('PASS compiled mixed-sense/sign repair/box/transport/reset + two actual Native-Pi Fraction checks; Optimize=0')

def native():
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for role in ['K-35-U','R-X20-S-T1']:
            folder=OUT/'LP'/f'{role}_base';row=read(OUT/'qualification/project'/(role+'.json'))['row']
            target=OUT/'qualification/native'/role;target.mkdir(parents=True,exist_ok=False)
            with gp.read(str(folder/'base.mps'),env=env) as m:
                old=semantics(m);names={v.VarName for v in m.getVars()};oldrows={c.ConstrName for c in m.getConstrs()}
                e=gp.quicksum(v*m.getVarByName(k) for k,v in row['terms'].items());m.addConstr(e<=row['rhs'],name='r144_PC');m.update()
                assert semantics(m,names,oldrows)==old and not any(v.VarName.startswith('rn_') for v in m.getVars())
                m.write(str(target/'compact.mps'))
            with gp.read(str(target/'compact.mps'),env=env) as m:
                c=m.getConstrByName('r144_PC');e=m.getRow(c)
                assert c.Sense=='<' and c.RHS==row['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==row['terms']
                assert semantics(m,names,oldrows)==old
                m.Params.Seed=0;m.Params.Threads=1;m.Params.TimeLimit=120;m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
                write(target/'call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',Seed=0,Threads=1,model_SHA=sha(target/'compact.mps')))
                m.optimize();assert m.Status==gp.GRB.OPTIMAL
                src=read(folder/'result.json');quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
                assert max(quality.values())<=1e-6
                point={v.VarName:v.X for v in m.getVars()};check=residual(m,point)
                assert max(check['constraints'],check['bounds'])<=1e-6
                result=dict(role=role,L=m.ObjVal,old_L=src['old_L'],RN_L=src['source']['L'],
                    retention_loss=src['source']['L']-m.ObjVal,retention_fraction=(m.ObjVal-src['old_L'])/src['source_gain'],
                    columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs,Runtime=m.Runtime,Work=m.Work,iterations=m.IterCount,
                    quality=quality,residual=check,RN_columns=0,PC_rows=1,actual_all_terms_and_RHS_read_back=True,
                    model_SHA=sha(target/'compact.mps'),cpp_evidence_SHA=sha(OUT/'qualification/project'/(role+'.json')),Seed=0,Threads=1)
                write(target/'result.json',result);facts.append(result)
    write(OUT/'qualification_native_transport.json',dict(PASS=True,facts=facts,LP_Optimize=2,MIP_Optimize=0,Native=binding()))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='native_meter':assert metered('native_transport','diagnostic',[LP_PYTHON,'-B',__file__,'native'],300,360)==0
    elif action=='writer_native_meter':assert metered('writer_native','diagnostic',[LP_PYTHON,'-B',__file__,'writer_native'],30,60)==0
    else:globals()[action]()
