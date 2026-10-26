"""Two saved domains, exactly two new LPs, and production AP coefficient checks."""
from round135_common import *
import collections, gzip, re, zipfile
from fractions import Fraction as F
import round108_reader as core

PIN='d3353749e6933e6685c7f0d92d153d0641816bcb'
ARCHIVE_SHA='9ef0dfada8b3ed06f5a0c7011e0c20b439a494823186c38bfbb28946ebe2a1a4'
ROLES=('K-20-S','K-35-U')
def prepare():
    archive=ROOT/'results/unified_exact_round134/artifacts/math_failures_and_costs.zip'
    assert sha(archive)==ARCHIVE_SHA
    members=[]
    with zipfile.ZipFile(archive) as z:
        for role in ROLES:
            folder=OUT/'roots'/role;old=folder/'inherited'
            for part in ('scope.json','current_export/original.lp','layer0/result.json','layer1/result.json'):
                name=f'results/unified_exact_round134/math/roots/{role}/{part}'
                data=z.read(name);target=old/part;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                members.append(dict(member=name,SHA256=sha(target),bytes=len(data)))
            scope=read(old/'scope.json');p=scope['panel'];call=scope['root_scope']
            for mode in ('off','ap'):
                target=folder/mode
                args=[BUILD/'Round135Export.exe',ROOT/p['input_path'],p['T_seconds'],call['lower_g'],call['upper_g'],call['cutoff'],'ms2',target]
                if mode=='ap':args.append('ap')
                assert metered(f'root_export_{role}_{mode}','C',args,reservation=60,timeout=60)==0
            before=core.lp_model(old/'current_export/original.lp')
            off=core.lp_model(folder/'off/original.lp');ap=core.lp_model(folder/'ap/original.lp')
            assert off==before,'Default-off writer changed the accepted R134 matrix'
            assert ap['bounds']==before['bounds'] and ap['types']==before['types'] and ap['objective']==before['objective']
            delta=collections.Counter(ap['rows'])-collections.Counter(before['rows'])
            removed=collections.Counter(before['rows'])-collections.Counter(ap['rows'])
            assert not removed and sum(delta.values())==1 and len(ap['rows'])==len(before['rows'])+1
            row=next(iter(delta));terms=dict(row[0]);assert row[1:]==('>=',0.)
            data=core.evidence.instance(ROOT,p);support=collections.defaultdict(list);ratios={}
            for n in before['bounds']:
                m=re.fullmatch(r'state_(\d+)_(\d+)',n)
                if m:support[int(m[1])].append(int(m[2]))
            for rr,sense,rhs in before['rows']:
                t=dict(rr)
                if sense=='=' and rhs==0 and len(t)==2:
                    for n,c in t.items():
                        m=re.fullmatch(r'r_(\d+)',n)
                        if m and c==1 and f'Y_{m[1]}' in t:ratios[int(m[1])]=-t[f'Y_{m[1]}']
            assert set(support)==set(ratios)==set(range(1,p['V']+1))
            checks=[]
            for i,ys in support.items():
                w=data['w'][i];assert terms.get(f'e_{i}',0.)==w
                for y in ys:
                    n=f'state_{i}_{y}';written=-terms.get(n,0.)
                    exact=F(w)*abs(F(ratios[i])*y-1)
                    assert 0<=F(written)<=exact,(n,written,str(exact))
                    checks.append(dict(name=n,exact=str(exact),written=written))
            assert set(terms)<=set(f'e_{i}' for i in support)|set(x['name'] for x in checks)
            starts=[]
            for source in ('startup_physical','archived_best_physical'):
                physical=scope[source];Y=physical['Y']
                if not all(Y[i] in support[i] for i in support):
                    starts.append(dict(source=source,inside_fixed_root_support=False));continue
                lhs=math.fsum(data['w'][i]*abs(Y[i]/data['D'][i]-1) for i in support)
                rhs=math.fsum(-terms.get(f'state_{i}_{Y[i]}',0.) for i in support)
                assert lhs-rhs>=-1e-7
                starts.append(dict(source=source,inside_fixed_root_support=True,lhs=lhs,rhs=rhs,slack=lhs-rhs,
                    full_physical_fleet_reused=True,selected_state_extension_valid=True))
            write(folder/'AP_row.json',dict(terms=terms,sense='>=',rhs=0,coefficient_checks=checks,
                loaded_ratios=ratios,supports=dict(support),all_coefficients_downward_safe=True,
                weighted_before_final_downward_step=True,small_RHS_terms_omitted_only_as_weakening=True))
            write(folder/'qualification.json',dict(default_off_canonical_equal=True,AP_only_one_added_row=True,
                same_bounds_types_objective=True,added_nonzeros=len(terms),new_variables=0,Start_checks=starts,
                inherited_matrix_SHA=sha(old/'current_export/original.lp'),AP_matrix_SHA=sha(folder/'ap/original.lp'),
                source_commit=PIN,ideal_B4_upper_bounds_valid=True,
                loaded_binary64_exact_rational_upper_bounds_have_machine_precision_exceptions=True))
    write(OUT/'roots/plan.json',dict(UTC=utc(),roles=list(ROLES),order=list(ROLES),new_LP_positions=2,
        original_and_IND_values_reused=True,cap_seconds=120,threads=1,seed=0,
        archive=dict(commit=PIN,path=str(archive.relative_to(ROOT)),SHA256=ARCHIVE_SHA,members=members),
        before_new_LP_results=True,production_row_exactly_audited=True))
    print('Default-off=R134; only AP row differs; exact coefficients and physical state extensions pass')

def solve(role):
    assert role in ROLES
    runtime=read(OUT/'roots/runtime.json')
    assert sha(sys.executable)==runtime['python_SHA256']
    from round100_gurobi_runtime import gp,binding
    folder=OUT/'roots'/role;target=folder/'LP';target.mkdir(exist_ok=False)
    tick=time.perf_counter();identity=binding();assert identity['sha256']==DLL_SHA
    row=read(folder/'AP_row.json');scope=read(folder/'inherited/scope.json')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(folder/'inherited/current_export/original.lp'),env=env) as m:
            m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.TimeLimit=120
            m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6
            m.Params.LogFile=str(target/'native.log');m.Params.LogToConsole=0;m.Params.OutputFlag=1
            for v in m.getVars():v.VType=gp.GRB.CONTINUOUS
            m.update();vs={v.VarName:v for v in m.getVars()}
            before=dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs)
            construct_tick=time.perf_counter()
            m.addConstr(gp.quicksum(c*vs[n] for n,c in row['terms'].items())>=0,name='r135_AP')
            m.update();constructed=time.perf_counter()
            after=dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs)
            assert after['rows']==before['rows']+1 and after['columns']==before['columns']
            assert m.IsMIP==0
            m.optimize();solved=time.perf_counter()
            assert m.Status==gp.GRB.OPTIMAL
            vector={v.VarName:v.X for v in m.getVars()}
            with gzip.open(target/'solution.json.gz','wt',encoding='utf-8') as stream:json.dump(vector,stream,separators=(',',':'))
            quality={n:m.getAttr(n) for n in ('ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio')}
            inherited=[read(folder/'inherited'/f'layer{k}/result.json') for k in (0,1)]
            result=dict(role=role,status='NUMERICAL_OPTIMAL_LP',L0_reused=inherited[0]['primal_objective'],
                L_IND_reused=inherited[1]['primal_objective'],L_AP=m.ObjVal,
                delta_AP_IND=m.ObjVal-inherited[1]['primal_objective'],quality=quality,
                AP_slack=math.fsum(c*vector[n] for n,c in row['terms'].items()),
                before=before,after=after,construct_AP_seconds=constructed-construct_tick,
                load_and_construct_seconds=constructed-tick,optimize_wall_seconds=solved-constructed,
                native_runtime=m.Runtime,Work=m.Work,iterations=m.IterCount,nodes=m.NodeCount,
                native_identity=identity,LP_Optimize=1,MIP_Optimize=0,
                original_domain_interval_cutoff_unchanged=True,numerical_confirmation_not_rational_certificate=True,
                preserves_IND_gain=abs(m.ObjVal-inherited[1]['primal_objective'])<=1e-7)
            assert result['preserves_IND_gain'] and result['AP_slack']>=-1e-7
            write(target/'result.json',result)
    print(json.dumps(result),flush=True)
def run():
    python=Path(read(OUT/'roots/runtime.json')['python'])
    for role in ROLES:
        assert metered('LP_'+role,'C',[python,ROOT/'scripts/round135_roots.py','solve',role],reservation=180,timeout=240)==0
if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run()
    else:solve(sys.argv[2])
