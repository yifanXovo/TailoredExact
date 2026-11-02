"""Focused production arithmetic/writer/Native qualifications; no broad panel."""
import gzip
from fractions import Fraction as F
from itertools import product
import collections
import round108_reader as parser
from round143_qualify import point_residual, actual_spec
from round146_math import oracle
from round148_math import station_data, alpha
from round148_lp import inherited
from round148_build import BUILD, COMPILER, SYSTEM
from round148_common import *
configure()
DRIVER_ROOT=OUT/'qualification/driver'


def check_actual(block,point,actual):
    c,data=station_data(block);n=len(c)
    assert actual['applicable']
    beta=sum(F(v) for v in actual['slopes'])
    terms=actual['row']['terms'];loss=F(0);ideal=F(0)
    if actual['kind'].startswith('moment_'):
        lower=actual['kind']=='moment_lower';matches=[]
        for chosen in c:
            valid=True
            bounds={st['y']:st['lo'] if lower else st['hi'] for st in data[chosen]}
            for i,states in data.items():
                for st in states:
                    q=(bounds[st['y']] if i==chosen else F(0))-c[i]*st['y']
                    if not lower:q=-q
                    if -F(terms.get(f"state_{i}_{st['y']}",0.))>q:valid=False
            if valid:matches.append(chosen)
        assert matches and not terms.get('G')
        return dict(exact_RHS_direction_PASS=True,valid_moment_station_candidates=matches,
            actual_violation=actual['violation'],negative_RHS_terms=sum(v>0 for v in terms.values()))
    for i,states in data.items():
        b=F(actual['slopes'][i-1])
        for state in states:
            name=f"state_{i}_{state['y']}"
            if actual['kind']=='affine_low':q=alpha(state,b)+beta*c[i]*state['y']
            else:continue
            transported=-F(terms.get(name,0.))
            assert transported<=q,(name,transported,q)
            loss+=q-transported;ideal+=q*F(point[name])
    if actual['kind']=='affine_low':assert terms.get('G')==1.
    return dict(exact_RHS_direction_PASS=True,loss_bound=float(loss),
        exact_affine_violation=float(ideal-F(point['G'])),actual_violation=actual['violation'],
        negative_RHS_terms=sum(v>0 for k,v in terms.items() if k!='G'))


def driver_case(name,spec,point,block=None):
    driver=read(OUT/'rows_driver.json');assert sha(driver['PE'])==driver['PE_SHA']
    target=DRIVER_ROOT/name;target.mkdir(parents=True,exist_ok=False)
    s={int(i):ys for i,ys in spec['supports'].items()};c={int(i):v for i,v in spec['c_binary64'].items()}
    text=[f"{len(s)} {spec['Bminus']} {spec['B']}"]
    text += [f'{c[i]:.17g} {len(ys)} '+' '.join(map(str,ys)) for i,ys in sorted(s.items())]
    text += [str(len(point))]+[f'{k} {v:.17g}' for k,v in sorted(point.items())]
    (target/'input.txt').write_text('\n'.join(text)+'\n',encoding='utf-8')
    result=subprocess.run([driver['PE'],target/'input.txt'],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    actual=json.loads(result.stdout);write(target/'actual.json',actual)
    if block is None:
        root,states=oracle(spec)
        assert actual['applicable']==root['applicable']
        if not root['applicable']:return dict(name=name,omitted=True,reason=root['reason'])
        # Read the actual outward conditional bounds from the already qualified
        # R146 arithmetic PE, not from rounded-to-nearest oracle endpoints.
        from round146_math import compiled
        block=compiled(spec,target/'gd_bounds.json');configure()
    check=check_actual(block,point,actual)
    write(target/'exact_check.json',check)
    return dict(name=name,old_GD_rows=actual['old_GD_rows'],kind=actual['kind'],**check)


def arithmetic(attempt='initial'):
    global DRIVER_ROOT
    configure();facts=[]
    DRIVER_ROOT=OUT/'qualification'/('driver' if attempt=='initial' else 'driver_'+attempt)
    for role,carrier in ROLES:
        folder,old,block,point=inherited(role,carrier)
        facts.append(driver_case(f'{role}_{carrier}',block['scope'],point,block))
    strict=dict(supports={1:[1,2],2:[1,2]},c_binary64={1:1.,2:1.},Bminus=2,B=4)
    point={'G':0.,'Y_1':1.5,'Y_2':2.,'state_1_1':.5,'state_1_2':.5,'state_2_1':0.,'state_2_2':1.}
    fact=driver_case('strict_zero_old_GD',strict,point)
    assert fact['old_GD_rows']==0 and fact['actual_violation']>0.08 and fact['negative_RHS_terms']>0
    facts.append(fact)
    for name,s,c,bm,b in [
        ('fixed_denominator',{1:[1],2:[2]},{1:1.,2:1.},3,3),
        ('zero_domain',{1:[0,1],2:[0,2]},{1:.2,2:.7},0,3),
        ('holes',{1:[0,2,5],2:[1,4],3:[0,3]},{1:.1,2:1/3,3:1.7},3,7)]:
        ys=next(v for v in product(*s.values()) if bm<=sum(v)<=b)
        p={'G':0.}|{f'Y_{i}':float(v) for i,v in zip(s,ys)}
        p.update({f'state_{i}_{v}':float(v==y) for (i,values),y in zip(s.items(),ys) for v in values})
        facts.append(driver_case(name,dict(supports=s,c_binary64=c,Bminus=bm,B=b),p))
    # Explicit outside-moment input must produce a valid finite moment row.
    bad=dict(point,Y_1=100.)
    fact=driver_case('moment_upper',strict,bad)
    assert fact['kind']=='moment_upper';facts.append(fact)
    write(OUT/'qualification_arithmetic.json',dict(PASS=True,Optimize=0,Native_load=0,facts=facts,
        actual_Cpp_slopes_fraction_checked=True,header_SHA=sha(ROOT/'include/Round148Research.hpp')))
    print('PASS production arithmetic: exact Fraction direction at actual slopes, 5 saved domains + focused fixtures')


def build_writer():
    configure();m=read(OUT/'candidate_manifest.json');pe=BUILD/'Round148Writer.exe'
    assert metered('compile_writer','build',[COMPILER,*m['flags'],ROOT/'scripts/round148_writer.cpp',*m['objects'],m['archive']['path'],*SYSTEM,'-o',pe],timeout=180)==0
    write(OUT/'writer_driver.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round148_writer.cpp')))


def native_writer():
    configure();from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    facts=[];root=OUT/'qualification/writer'
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for tag in ('positive','fixed','zero_lower'):
            folder=root/tag;off=parser.lp_model(folder/'off.lp');gd=parser.lp_model(folder/'gd.lp');on=parser.lp_model(folder/'on.lp')
            evidence=read(folder/'row.json');rows=evidence['rows']
            assert all(off[k]==on[k] for k in ('order','bounds','types','objective'))
            assert collections.Counter(on['rows'])==collections.Counter(gd['rows'])+collections.Counter((tuple(sorted(r['terms'].items())),'>=',0.) for r in rows)
            for label in ('physical_start','nonminimal_epigraph'):
                point=read(folder/(label+'.json'));assert set(point)==set(on['order'])
                res=point_residual(on,point);assert max(res.values())<=1e-6,(tag,label,res)
                facts.append(dict(tag=tag,Start=label,complete=True,residual=res))
            for name in ('on','child_on') if tag=='positive' else ('on',):
                with gp.read(str(folder/(name+'.lp')),env=env) as model:
                    for row in rows:
                        r=model.getConstrByName(row['name']);e=model.getRow(r)
                        expected={k:v for k,v in row['terms'].items() if model.getVarByName(k) is not None}
                        assert {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==expected
                    facts.append(dict(tag=tag,model=name,Native_readback=True,new_rows=len(rows)))
    write(OUT/'qualification_native_writer.json',dict(PASS=True,Optimize=0,Native=binding(),facts=facts))
    print('PASS actual writer, subset inheritance, complete/nonminimal Start, Native signed row readback')


def run(action):
    configure()
    if action=='arithmetic':
        assert metered('qualification_arithmetic','diagnostic',[PYTHON,'-B',__file__,'arithmetic'],120,180)==0
    elif action=='writer':
        pe=read(OUT/'writer_driver.json')['PE']
        assert metered('qualification_writer_cpp','diagnostic',[pe,OUT/'qualification/writer'],60,90)==0
        assert metered('qualification_native_writer','diagnostic',[LP_PYTHON,'-B',__file__,'native_writer'],60,90)==0
    else:raise ValueError(action)


if __name__=='__main__':
    if sys.argv[1]=='run':run(sys.argv[2])
    elif sys.argv[1]=='arithmetic':arithmetic(*sys.argv[2:])
    else:globals()[sys.argv[1]]()
