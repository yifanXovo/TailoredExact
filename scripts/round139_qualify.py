"""Targeted role/epoch exports and exact actual-matrix checks. Explicit actions only."""
from round139_common import *
import collections,csv
import round108_reader as core
from round138_repair import scaled_rows

def idle_or_own_meter():
    pending=budget()['unclosed'];own=os.environ.get('ROUND139_METERED_PARENT_LABEL')
    assert not pending or (own and len(pending)==1 and pending[0]['label']==own),pending

def exporter():
    assert not budget()['unclosed']
    b=read(OUT/'candidate_build.json');code=(ROOT/'scripts/round138_export.cpp').read_text(encoding='utf-8-sig')
    code=code.replace('#include "Round138Research.hpp"','#include "Round139Research.hpp"')
    code=code.replace('if(argc!=10)','if(argc!=11)')
    code=code.replace('    if(variant!="off" && variant!="stock")throw std::runtime_error("Round138 export variant");\n    ebrp::round138().stock_rlt=variant=="stock";',
        '    ebrp::round139().set(variant);\n    const std::string role=argv[10];\n    if(role!="LP" && role!="MIP")throw std::runtime_error("Round139 export role");\n    ebrp::Round139StockWriterScope writer_scope(ebrp::round139().stock(role=="MIP"));')
    code=code.replace('check(setintparam(env,"OutputFlag",0));check(startenv(env));',
        'check(setintparam(env,"OutputFlag",0));check(setintparam(env,"Seed",0));check(setintparam(env,"Threads",1));check(startenv(env));')
    path=ROOT/'scripts/round139_role_export.cpp';path.write_text(code,encoding='utf-8',newline='\n')
    target=BUILD/'Round139RoleExport.exe'
    system=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    cmd=[COMPILER,*b['flags'],path,*b['linked_objects'],b['archive']['path'],*system,'-o',target]
    assert metered('compile_role_exporter','build',cmd,timeout=180)==0
    write(OUT/'qualification_exporter.json',dict(PE=str(target),PE_SHA=sha(target),source_SHA=sha(path),command=list(map(str,cmd)),Optimize=0))

def exports():
    assert not budget()['unclosed'];matrix=read(OUT/'qualification_matrix.json')
    l=matrix['groups'][0]['launch'];p=l['panel'];d=Path(l['destination'])
    call=next(r['payload'] for r in read(d/'observations.json') if r['payload']['kind']=='call')
    alpha,beta=call['lower_g'],call['upper_g'];cutoff=call['cutoff'];exe=read(OUT/'qualification_exporter.json')['PE']
    assert 0<=alpha<beta and math.isfinite(cutoff)
    cases=[dict(name='root',alpha=alpha,beta=beta,cutoff=cutoff),
           dict(name='child',alpha=alpha,beta=(alpha+beta)/2,cutoff=cutoff),
           dict(name='cutoff_refresh',alpha=alpha,beta=min(beta,cutoff-1e-4),cutoff=cutoff-1e-4)]
    plan=dict(UTC=utc(),cases=cases,placement=['lp-only','mip-only'],roles=['LP','MIP'],Seed=0,Threads=1,H_seed=None,
        scope='Deterministic zero-Optimize export of real root/child and representative refreshed cutoff; no physical incumbent or solve result claimed by refresh export',panel=p)
    write(OUT/'qualification/export_plan.json',plan)
    for c in cases:
        for placement in plan['placement']:
            for role in plan['roles']:
                dest=OUT/'qualification/exports'/c['name']/placement/role
                cmd=[exe,ROOT/p['input_path'],p['T_seconds'],c['alpha'],c['beta'],c['cutoff'],'ms2',dest,p['lambda'],placement,role]
                label='_'.join(['export',c['name'],placement,role])
                assert metered(label,'diagnostic',cmd,timeout=60)==0

def exact_matrix(path,p,enabled,native=False):
    m=core.lp_model(path);data=core.evidence.instance(ROOT,p);alpha,beta=m['bounds']['G']
    B=sum(data['b'][1:]);Bm=max(0,B-sum(p['Q_vector']));expected=collections.Counter(scaled_rows(p['V'],alpha,beta,Bm,B))
    actual=collections.Counter(m['rows'])
    for row,n in expected.items():assert actual[row]==(n if enabled else 0),(path,enabled,n,actual[row])
    fact=dict(path=Path(path).relative_to(ROOT).as_posix(),SHA=sha(path),stock=enabled,
        rows=4 if enabled else 0,exact_multiplicity=True,alpha=alpha,beta=beta,B=B,Bminus=Bm,
        canonical_integer_types_preserved=all(m['types'][n] in ['I','B'] for n in m['order'] if n.startswith(('x_','Y_','load_'))))
    assert fact['canonical_integer_types_preserved']
    if native:
        from round100_gurobi_runtime import gp,binding
        assert binding()['sha256']==DLL_SHA
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
            with gp.read(str(path),env=env) as model:
                assert model.NumVars==len(m['order']) and model.NumConstrs==len(m['rows'])
                assert {v.VarName:v.VType for v in model.getVars()}==m['types']
                if enabled:
                    for j,row in enumerate(m['rows']):
                        if row not in expected:continue
                        terms,sense,rhs=row;c=model.getConstrs()[j];r=model.getRow(c)
                        assert {r.getVar(k).VarName:r.getCoeff(k) for k in range(r.size())}==dict(terms)
                        assert c.RHS==rhs and c.Sense=={'<=':'<','>=':'>','=':'='}[sense]
        fact.update(native_exact_coefficients_RHS_and_types=True,Seed=0,Threads=1,Optimize=0)
    return fact,m

def actual(batch='qualification',native=False):
    idle_or_own_meter();matrix=read(OUT/f'{batch}_matrix.json');reports=[];seen={};by={}
    for g in matrix['groups']:
        l=g['launch'];d=Path(l['destination']);assert (d/'verification_closeout.json').exists(),d
        obs=read(d/'observations.json');calls=[r['payload'] for r in obs if r['payload']['kind']=='call']
        ledger=list(csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline='')))
        checks=[]
        for c in calls:
            r=next(r for r in ledger if r['model_sha256']==c['model_sha256'] and r['native_log']==c['native_log_path'])
            lp=r['solve_kind']=='LP';stock=l['placement']=='both' or l['placement']==('lp-only' if lp else 'mip-only')
            path=core.portable(ROOT,c['model_path']);key=(str(path),stock)
            if key not in seen:seen[key]=exact_matrix(path,l['panel'],stock,native)
            fact,m=seen[key];assert fact['SHA']==c['model_sha256']
            checks.append(dict(call=c['call'],leaf=c['leaf'],kind=r['solve_kind'],native_log=r['native_log'],
                reused=int(r['in_memory_model_reused']),restored=int(r['integer_domain_restored']),**fact))
            if lp:assert int(r['integer_domain_restored'])==1
            if batch=='qualification':by.setdefault((c['leaf'],lp),{})[l['placement']]=m
        legacy=[]
        if batch=='qualification' and l['placement'] in ['base','both']:
            b=next(b for b in read(OUT/'baseline_reuse.json')['positions'] if b['role']==l['id'])
            oldd=Path(b[l['placement']]['destination'])
            oldcalls=[r['payload'] for r in read(oldd/'observations.json') if r['payload']['kind']=='call']
            for fact in checks:
                same=[c for c in oldcalls if c['leaf']==fact['leaf'] and c['model_sha256']==fact['SHA']]
                assert same,('00/11 changed historical canonical bytes',l['placement'],fact)
                legacy.append(dict(leaf=fact['leaf'],kind=fact['kind'],old_source=str(oldd),canonical_SHA=fact['SHA'],exact_legacy_model_bytes=True))
        reports.append(dict(position=g['position'],role=l['id'],placement=l['placement'],checks=checks,legacy_equivalence=legacy,
            control_audit_SHA=sha(d/'round139_control_audit.json'),endpoint=read(d/'round135_endpoint.json')))
    comparisons=[]
    if batch=='qualification':
        for (leaf,lp),mm in by.items():
            for x,y in [('base','both'),('base','lp-only'),('base','mip-only')]:
                if x not in mm or y not in mm:continue
                a,b=mm[x],mm[y]
                assert all(a[k]==b[k] for k in ['order','bounds','types','objective'])
                enabled=y=='both' or y==('lp-only' if lp else 'mip-only')
                delta=collections.Counter(b['rows'])-collections.Counter(a['rows'])
                assert not collections.Counter(a['rows'])-collections.Counter(b['rows'])
                assert sum(delta.values())==(4 if enabled else 0)
                comparisons.append(dict(leaf=leaf,LP=lp,base_vs=y,only_new_rows=sum(delta.values()),common_matrix_exact=True))
    write(OUT/'qualification'/f'{batch}_actual.json',dict(PASS=True,batch=batch,positions=reports,
        comparisons=comparisons,unique_actual_models=len(seen),all_stock_row_multiplicities_exact=True,
        native_reads=native,Optimize=0,full_clock_includes_rebuild=True,
        cutoff_refresh_lifecycle='Original epoch invalidation retained; representative writer refresh exported separately, no forced controller/Start changes'))
    print(f'Exact actual matrices pass: {batch}, {len(reports)} positions, {len(seen)} unique models')

def check_exports():
    idle_or_own_meter();plan=read(OUT/'qualification/export_plan.json');facts=[]
    for c in plan['cases']:
        for placement in plan['placement']:
            models={}
            for role in plan['roles']:
                path=OUT/'qualification/exports'/c['name']/placement/role/'original.lp'
                stock=placement==('lp-only' if role=='LP' else 'mip-only')
                fact,m=exact_matrix(path,plan['panel'],stock,True);facts.append(dict(case=c['name'],placement=placement,role=role,**fact));models[role]=m
            a,b=models['LP'],models['MIP'];assert all(a[k]==b[k] for k in ['order','bounds','types','objective'])
            assert abs(len(a['rows'])-len(b['rows']))==4
    write(OUT/'qualification/role_refresh_checks.json',dict(PASS=True,cases=facts,Optimize=0,
        new_rows_only_four=True,new_columns=0,V2_scaling_unchanged=True,all_declared_roles_and_endpoints_checked=True))
    print('12 root/child/refreshed-cutoff role matrices pass exact Native coefficient/type readback')

def prepare_exports():
    exporter();exports()

if __name__=='__main__':
    if sys.argv[1]=='actual':actual(sys.argv[2] if len(sys.argv)>2 else 'qualification','--native' in sys.argv)
    else:globals()[sys.argv[1]]()
