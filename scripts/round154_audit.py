"""Finite actual-matrix/price/coupling audit. Native reads, zero Optimize."""
from fractions import Fraction as F
from itertools import combinations
import inspect
from round143_math import outward,denominator
from round152_math import states,s_bounds,unary_dp
from round153_pricing import stock_value
from round153_audit import audit_price as audit_RN,exact_matrix,replay_q_bounds,independent_residual
from round153_lp import primal_record
from round154_common import *

def compact(terms):return {k:F(v) for k,v in terms.items() if v}

def stop_control(path,p):
    planpath=path.parent/'target_stop_plan.json'
    if not planpath.exists():return False
    c=read(path.parent/'call.json');plan=read(planpath);tau=F(plan['tau_exact'])
    qualified=read(OUT/'qualification/goal_stop_v1/result.json')
    assert qualified['PASS'] and plan['wrapper_SHA']==qualified['goal_oracle_SHA']==sha(ROOT/'scripts/round154_goal_oracle.py')
    assert plan['generated_source_SHA']==qualified[f'generated_{plan["kind"]}_source']['generated_SHA']
    assert plan['model_SHA']==sha(path.parent/'model.mps') and plan['generated_source_SHA']==sha(path.parent/'target_stop_source.txt')
    assert plan['guard_already_paid'] and plan['no_model_changes']
    if plan['kind']=='RN':
        expected=(tau-sum((F(v) for v in c['anchors_exact'].values()),F(0)))/F(c['scale'])+F(c['numerical_guard_scaled'])+F(c['objective_correction_scaled_exact'])
    else:
        assert plan['kind']=='residual';expected=F(c['residual_guard_scaled'])
    assert F(plan['bound_stop_exact'])==expected and F(plan['Native_BestBdStop'])>=expected
    q=p['calls'][0]
    if q['Status']==11 and q['bound_status_qualified']:
        witness=read(path.parent/'counterexample_stop.json');d={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}
        v=stock_value(p['scope'],witness['stock']['Y'],F(p.get('beta_exact',p['beta'])),d)
        assert v['feasible'] and v['price']<tau and v['price']==F(witness['original_price_exact'])
    return True

def normalized_price(path,seen):
    p=read(path);directed=stop_control(path,p)
    if not directed:return audit_RN(path,seen)
    source=inspect.getsource(audit_RN)
    needle="assert q['Status'] in ((2,9) if c.get('node_limit') is None else (2,8))"
    assert source.count(needle)==1
    source=source.replace(needle,"assert q['Status'] in ((2,9,11,15) if c.get('node_limit') is None else (2,8,11,15))")
    ns=dict(audit_RN.__globals__);exec(compile(source,__file__+'::target_native_status_audit','exec'),ns)
    return ns['audit_price'](path,seen)

def residual_matrix(gp,env,path,c):
    """Check the written model without importing its producer or reconstructing it."""
    domain=c['scope'];ss=domain['stations'];l,u=map(F,c['positive_S_bounds']);checked=set()
    with gp.read(str(path),env=env) as m:
        assert m.ModelSense==1 and m.ObjCon==0 and m.NumQNZs==m.NumQConstrs==m.NumGenConstrs==m.NumSOS==0
        rows={r.ConstrName:r for r in m.getConstrs()};vs={v.VarName:v for v in m.getVars()}
        assert len(rows)==m.NumConstrs and len(vs)==m.NumVars
        assert all(v.VType=='C' for name,v in vs.items() if not name.startswith('x['))
        def row(name,terms,sense,rhs):
            r=rows[name];e=m.getRow(r);actual={e.getVar(j).VarName:F(e.getCoeff(j)) for j in range(e.size())}
            assert actual==compact(terms) and r.Sense==sense and F(r.RHS)==F(rhs),(str(path),name)
            checked.add(name)
        assert F(vs['S'].LB)==l and F(vs['S'].UB)==u and vs['residual_scaled'].LB<-1e90
        assert vs['residual_scaled'].UB>1e90
        assert all(v.Obj==(1. if name=='residual_scaled' else 0.) for name,v in vs.items())
        for s in ss:
            i=s['i'];ys=s['support']
            assert vs[f'Y[{i}]'].LB==vs[f'r[{i}]'].LB==0
            assert vs[f'Y[{i}]'].UB>1e90 and vs[f'r[{i}]'].UB>1e90
            row(f'onehot_{i}',{f'x[{i},{y}]':1 for y in ys},'=',1)
            row(f'inventory_{i}',{f'Y[{i}]':1}|{f'x[{i},{y}]':-y for y in ys},'=',0)
            row(f'ratio_{i}',{f'r[{i}]':1,f'Y[{i}]':-F(s['c'])},'=',0)
            row(f'product_mass_{i}',{'S':-1}|{f'Sx[{i},{y}]':1 for y in ys},'=',0)
            for y in ys:
                x,z=f'x[{i},{y}]',f'Sx[{i},{y}]'
                assert vs[x].VType=='B' and 0<=vs[x].LB<=vs[x].UB<=1
                assert vs[z].LB==0 and F(vs[z].UB)==u
                row(f'product_lx_{i}_{y}',{z:1,x:-l},'>',0)
                row(f'product_ux_{i}_{y}',{z:1,x:-u},'<',0)
                row(f'product_Su_{i}_{y}',{z:1,'S':-1,x:-u},'>',-u)
                row(f'product_Sl_{i}_{y}',{z:1,'S':-1,x:-l},'<',-l)
        row('denominator',{'S':1}|{f'r[{s["i"]}]':-1 for s in ss},'=',0)
        total={f'Y[{s["i"]}]':1 for s in ss}
        row('hard_lower',total,'>',domain['Bminus']);row('hard_upper',total,'<',domain['B'])
        A={}
        for i,j in combinations([s['i'] for s in ss],2):
            a=f'abs[{i},{j}]';A[a]=F(1);assert vs[a].LB==0 and vs[a].UB>1e90
            row(f'abs_p_{i}_{j}',{a:1,f'r[{i}]':-1,f'r[{j}]':1},'>',0)
            row(f'abs_m_{i}_{j}',{a:1,f'r[{i}]':1,f'r[{j}]':-1},'>',0)
        physical=rows['physical_G_upper_outward'];e=m.getRow(physical)
        coefficients={e.getVar(j).VarName:F(e.getCoeff(j)) for j in range(e.size())}
        cap=-coefficients.get('S',F(0));assert cap>=len(ss)*F(domain['gamma_U'])
        row('physical_G_upper_outward',A|{'S':-cap},'<',0)
        product={f'Sx[{i},{y}]':F(y) for i,y in states(domain)}
        row('total_product_lower',product|{'S':-F(domain['Bminus'])},'>',0)
        row('total_product_upper',product|{'S':-F(domain['B'])},'<',0)
        written=c['residual_coefficients'];cost={tuple(map(int,k.split(':'))):F(v) for k,v in written['state'].items()}
        W={f'Sx[{i},{y}]':-v for (i,y),v in cost.items()}
        row('floor_residual',W|{'S':-F(written['S_floor']),'residual_scaled':1},'>',0)
        row('G_residual',W|{'S':-F(written['S_G']),'residual_scaled':1}|{a:-F(written['A']) for a in A},'>',0)
        extpath=path.parent/'strengthening.json'
        if extpath.exists():
            ext=read(extpath);cmap={s['i']:F(s['c']) for s in ss};supports={s['i']:s['support'] for s in ss}
            for item in ext['conditional_S_bounds']:
                i,y=item['i'],item['y'];x,z=f'x[{i},{y}]',f'Sx[{i},{y}]'
                for active in [True,False]:
                    part=item['parts'][str(active)];ys=[y] if active else [v for v in supports[i] if v!=y]
                    b=denominator(cmap,supports|{i:ys},domain['Bminus'],domain['B']) if ys else {}
                    if part.get('impossible') or part.get('impossible_positive_branch'):
                        assert not b or 'S_U_exact' not in b or F(b['S_U_exact'])<l
                        assert vs[x].UB==0 if active else vs[x].LB==1
                        continue
                    assert F(part['lower'])<=max(l,F(b['S_L_exact'])) and F(part['upper'])>=min(u,F(b['S_U_exact']))
                    lo,hi=map(F,(part['lower'],part['upper']))
                    if active:
                        row(f'conditional_Sx_lower_{i}_{y}',{z:1,x:-lo},'>',0)
                        row(f'conditional_Sx_upper_{i}_{y}',{z:1,x:-hi},'<',0)
                    else:
                        row(f'conditional_complement_lower_{i}_{y}',{'S':1,z:-1,x:lo},'>',lo)
                        row(f'conditional_complement_upper_{i}_{y}',{'S':1,z:-1,x:hi},'<',hi)
            lo=unary_dp(domain,cost);hi=unary_dp(domain,{k:-v for k,v in cost.items()})
            a,b=map(F,ext['tight_cost_bounds']);assert a<=F(lo['exact']) and b>=-F(hi['exact'])
            assert F(vs['hard_cost_D'].LB)==a and F(vs['hard_cost_D'].UB)==b
            assert vs['hard_cost_W'].LB<-1e90 and vs['hard_cost_W'].UB>1e90
            row('hard_cost_D_definition',{'hard_cost_D':1}|{f'x[{i},{y}]':-v for (i,y),v in cost.items()},'=',0)
            row('hard_cost_W_definition',{'hard_cost_W':1}|{f'Sx[{i},{y}]':-v for (i,y),v in cost.items()},'=',0)
            for name,slope,endpoint,sense in [('ll',l,a,'>'),('uu',u,b,'>'),('ul',u,a,'<'),('lu',l,b,'<')]:
                rhs=outward(-slope*endpoint,sense=='<')
                row('tight_DP_cost_product_'+name,{'hard_cost_W':1,'hard_cost_D':-slope,'S':-endpoint},sense,rhs)
        assert checked==set(rows),'unexpected unqualified model row'
        return dict(path=str(path.relative_to(ROOT)),SHA256=sha(path),variables=m.NumVars,rows=m.NumConstrs,binaries=m.NumBinVars,
                    actual_rows_checked=len(checked),strong=extpath.exists(),Optimize=0)

def audit_residual(gp,env,path):
    p=read(path);c=read(path.parent/'call.json');scope=p['scope'];beta=F(p['beta_exact']);tau=F(p['tau_exact'])
    assert c['scope']==scope and c['beta_exact']==p['beta_exact'] and c['d_exact']==p['d_exact']
    assert c['tau_exact']==p['tau_exact'] and c['model_SHA']==sha(path.parent/'model.mps')
    assert c['Seed']==0 and c['Threads']==1 and c['full_support'] and c['matrix_readback'] and c['q_can_be_negative']
    costs={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()};ss=scope['stations']
    anchors={s['i']:(min(costs[s['i'],y] for y in s['support'])+max(costs[s['i'],y] for y in s['support']))/2 for s in ss}
    assert {int(i):F(v) for i,v in c['anchors_exact'].items()}==anchors
    scale=F(c['scale']);assert scale>0;anchor=sum(anchors.values(),F(0))
    written=c['residual_coefficients'];wc={tuple(map(int,k.split(':'))):F(v) for k,v in written['state'].items()}
    for k in states(scope):
        error=(costs[k]-anchors[k[0]])/scale-wc[k]
        assert error>=0 and F(c['state_downward_errors_exact'][f'{k[0]}:{k[1]}'])==error
    assert F(written['S_floor'])<=(anchor+beta*F(scope['gamma_L'])-tau)/scale
    assert F(written['S_G'])<=(anchor-tau)/scale
    assert 0<=F(written['A'])<=beta/F(len(ss))/scale
    bounds=json.loads(json.dumps(s_bounds(scope)));assert c['bounds']==bounds
    l,u=map(F,c['positive_S_bounds']);assert [float(l),float(u)]==[bounds['lower'],bounds['upper']]
    guard=outward(F(1e-6)*(1+sum(max(abs(wc[s['i'],y]) for y in s['support']) for s in ss)*u+
        max(abs(F(written['S_floor'])),abs(F(written['S_G'])))*u+F(written['A'])*len(ss)*F(scope['gamma_U'])*u),True)
    assert guard==c['residual_guard_scaled'] and float(scale)*guard==c['residual_guard_original']
    q=p['calls'][0];returned=read(path.parent/'return.json');assert q==returned
    dp=unary_dp(scope,costs);fallback=beta*F(scope['gamma_L'])+F(dp['exact']);positive=fallback;ell=None
    directed=stop_control(path,p)
    if q['bound_status_qualified']:
        assert q['Status'] in ((2,8,9,11,15) if directed else (2,8,9)) and math.isfinite(q['native_bound'])
        ell=scale*(F(q['native_bound'])-F(guard))
    for t in p['prior_residual_transports']:
        source=read(t['source']);assert source['scope']==scope and source['beta_exact']==p['beta_exact'] and source['d_exact']==p['d_exact']
        delta=tau-F(source['tau_exact']);v=F(source['residual_lower_exact'])-max(delta*l,delta*u)
        assert v==F(t['transported_lower_exact']);ell=v if ell is None else max(ell,v)
    assert p['residual_lower_exact']==(str(ell) if ell is not None else None)
    if ell is not None:positive=max(positive,tau+ell/(u if ell>=0 else l))
    lower=positive
    if bounds['zero_possible']:lower=min(lower,stock_value(scope,[0]*len(ss),beta,costs)['price'])
    assert p['inherited_lower'] is None,'study raw lower must exclude inherited information'
    assert p['lower']==outward(lower,False) and p['fallback_lower']==outward(fallback,False)
    stocks=[]
    for rec in p['stocks']:
        v=stock_value(scope,rec['Y'],beta,costs);assert v['feasible'] and v['price']==F(rec['price_exact']) and v['f']==F(rec['f_exact'])
        stocks.append(v['price'])
    assert stocks and F(p['lower'])<=min(stocks)<=F(p['upper'])
    matrix=residual_matrix(gp,env,path.parent/'model.mps',c)
    return dict(path=str(path.relative_to(ROOT)),SHA256=sha(path),lower=p['lower'],upper=p['upper'],
                stocks=len(stocks),residual_recovery_independent=True,matrix=matrix)

def primal_check(m,scope,columns,path,claimed):
    data=load_gz(path);point=data['point'];base=primal_record(m,point);assert base['qualified']
    objective=F(m.ObjCon)+sum(F(v.Obj)*F(point[v.VarName]) for v in m.getVars())
    assert objective<=F(claimed)+F(1e-9)
    base['objective']=float(objective)
    # An inherited witness may use the old column ordering. Its explicit
    # inventory distribution is a witness in its own right; never reassign
    # old lambda indices to a subsequently sorted/enlarged pool.
    stocks=data['stocks'];pool={tuple(Y) for Y in columns};weights=[r['weight'] for r in stocks]
    mass=math.fsum(weights);negative=math.fsum(max(0.,-z) for z in weights)
    assert abs(mass-1)<=1e-8 and negative<=1e-8
    expected=F(0);marg={k:0. for k in states(scope)};active=0
    for rec,z in zip(stocks,weights):
        Y=rec['Y'];assert tuple(Y) in pool
        if not z:continue
        v=stock_value(scope,Y);assert v['feasible'] and v['f']==F(rec['f_exact']);expected+=F(z)*v['f'];active+=1
        for s,y in zip(scope['stations'],Y):marg[s['i'],y]+=z
    mismatch=max(abs(value-point[f'state_{i}_{y}']) for (i,y),value in marg.items())
    assert mismatch<=1e-8 and F(point['G'])>=expected
    return dict(path=str(path.relative_to(ROOT)),SHA256=sha(path),original_Q_primal=base,
        mass=mass,negative_mass=negative,marginal_mismatch=mismatch,active=active,
        true_completion_slack=float(F(point['G'])-expected),upper=claimed,numerical_policy=True,
        rational_primal_claim=False)

def sources():
    candidate=read(OUT/'candidate_manifest.json');matrix=read(OUT/'confirmation_matrix.json');helper=read(OUT/'helper_manifest.json')
    assert sha(OUT/'goal.md')=='6d42d706fc675a32c8ad1e3157f7e192925b3fac82de0532599b7909a61ab990'
    checked={}
    for mapping in [candidate['source_hashes'],matrix['helpers'],helper['helper_dependencies']]:
        for name,digest in mapping.items():
            assert name not in checked or checked[name]==digest
            assert sha(ROOT/name)==digest;checked[name]=digest
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert matrix['helper_manifest_SHA']==sha(OUT/'helper_manifest.json')
    assert sha(candidate['production_PE'])==candidate['production_PE_SHA'] and sha(DLL)==DLL_SHA
    stable={}
    for name in ['scripts/paper_s2.py','config/gi_tbc_round137.json','scripts/paper_s2_root_floor.py','config/gi_tbc_root_floor_round153.json']:
        raw=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==sha(ROOT/name);stable[name]=sha(ROOT/name)
    snapshots=[];saved={}
    for p in sorted((OUT/'engineering/source_snapshots').glob('*.json')):
        value=read(p)
        for name,digest in value['files'].items():
            source=OUT/'engineering/source_bytes'/f'{digest}.txt';assert sha(source)==digest
            saved[digest]=dict(path=str(source.relative_to(ROOT)),bytes=source.stat().st_size)
        snapshots.append(dict(path=str(p.relative_to(ROOT)),SHA256=sha(p),files=len(value['files'])))
    coverage=[]
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        snapshot=OUT/'engineering/source_snapshots'/f'{p.parent.name}.json'
        coverage.append(dict(label=p.parent.name,launch_SHA=sha(p),snapshot_SHA=sha(snapshot) if snapshot.exists() else None,
            binding='per-run sources' if snapshot.exists() else 'candidate/build record',universal_snapshot_coverage_claimed=False))
    value=dict(UTC=utc(),production_measured_source_commit=candidate['source_commit'],production_PE=candidate['production_PE'],
        production_PE_SHA=candidate['production_PE_SHA'],DLL_SHA=DLL_SHA,fixed_R153_science=SCIENCE153,temporary_base=BASE,
        frozen_matrix_SHA=sha(OUT/'confirmation_matrix.json'),checked_frozen_files=checked,stable_entry_profiles=stable,
        snapshots=snapshots,saved_source_bytes=saved,snapshot_coverage=coverage,
        current_research_sources={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'scripts').glob('round154*')) if p.is_file()},
        adopted_goal_SHA=sha(OUT/'goal.md'),source_snapshot_setup_and_history_bookkeeping_not_fully_timed=True)
    write(OUT/'source_manifest.json',value);return value

def loop_evidence(gp,env,prices,legacy,primals):
    checked=[];reads=0
    for planpath in sorted((OUT/'coupled').glob('*/plan.json')):
        plan=read(planpath)
        if 'implementation' not in plan:continue
        folder=planpath.parent;prior=read(plan['prior_result']);scope=plan['scope']
        assert sha(plan['prior_result'])==plan['prior_SHA'] and scope==prior['scope']
        qp=OLD153/'reference'/plan['role']/'direct/model.mps';assert sha(qp)==plan['Q_SHA']==prior['Q_SHA']
        pool=dict.fromkeys(tuple(Y) for Y in prior['columns']);steps=[];lower=prior['lower'];upper=prior['upper']
        with gp.read(str(qp),env=env) as m:
            reads+=1;matrix=exact_matrix(m);bounds=replay_q_bounds(matrix,load_gz(folder/'Q_bounds.json.gz'))
            for dp in sorted(folder.glob('iter*/direction.json')):
                d=read(dp);assert d['scope']==scope and d['Q_SHA']==plan['Q_SHA'] and d['columns_before']==len(pool)
                costs={tuple(map(int,k.split(':'))):F(v) for k,v in d['d_exact'].items()}
                cert=load_gz(dp.parent/'provisional_certificate.json.gz')
                independent_residual(matrix,bounds,cert,scope)
                minimum=min(stock_value(scope,Y,d['beta'],costs)['price'] for Y in pool)
                assert F(d['a_K_exact'])==min(F(cert['a_raw']),minimum) and F(d['initial_true_price_upper_exact'])==minimum
                assert F(d['C_Q_exact'])==F(cert['lower_exact']) and F(d['zeta_exact'])==F(d['C_Q_exact'])+F(d['tau_exact'])
                pp=dp.parent/'pricing/result.json'
                if not pp.exists():
                    assert F(d['ceiling_exact'])<F(d['zeta_exact']);continue
                p=read(pp);assert p['scope']==scope and p['beta']==d['beta'] and p['d_exact']==d['d_exact']
                if 'tau_exact' in p:prices.append(audit_residual(gp,env,pp));reads+=1
                else:normalized_price(pp,legacy)
                rec=read(dp.parent/'result.json');true_upper=min([minimum]+[F(v['price_exact']) for v in p['stocks']])
                cq,aK=F(d['C_Q_exact']),F(d['a_K_exact'])
                assert rec['target_proved']==(F(p['lower'])>=F(d['tau_exact']))
                assert rec['target_disproved']==(true_upper<F(d['tau_exact']))
                assert F(rec['fixed_certificate_ceiling'])>=cq+min(aK,true_upper)
                before=len(pool)
                for v in p['stocks']:pool.setdefault(tuple(v['Y']),None)
                assert rec['columns']==len(pool) and rec['added']==len(pool)-before
                finalcert=load_gz(dp.parent/'certificate.json.gz');independent_residual(matrix,bounds,finalcert,scope)
                assert F(finalcert['coupled_lower'])<=cq+min(aK,F(p['lower']))
                lower=max(lower,outward(cq+min(aK,F(p['lower'])),False));upper=min(upper,rec['RMP_objective'])
                assert rec['lower']==lower and rec['upper']==upper and rec['gap']==upper-lower
                steps.append(dict(direction_SHA=sha(dp),price_SHA=sha(pp),all_current_column_min=True,C_Q=True,targets=True,columns=len(pool)))
            rp=folder/'result.json'
            if rp.exists():
                data=read(rp);assert not data['refresh_required'] and data['last_columns_evaluated']
                assert data['lower']==lower and data['upper']<=upper and data['gap']==data['upper']-lower
                assert list(pool)==[tuple(Y) for Y in data['columns']]
                witness=data.get('upper_witness_source')
                if witness:primals.append(primal_check(m,scope,data['columns'],Path(witness),data['upper']))
                checked.append(dict(path=str(rp.relative_to(ROOT)),SHA256=sha(rp),steps=steps,all_columns_evaluated=True))
            else:
                assert not steps,'an interrupted scientific phase needs explicit handling'
                checked.append(dict(path=str(planpath.relative_to(ROOT)),no_pricing=True,failed_selection_not_a_negative_result=True))
    return checked,reads

def complete_support_matrix(original,actual,rows):
    assert original['variables']==actual['variables'] and original['constant']==actual['constant']
    expected=dict(original['rows'])
    for row in rows:
        assert row['name'] not in expected
        expected[row['name']]=dict(sense=row['sense'],rhs=F(row['rhs']),terms=compact(row['terms']))
    assert actual['rows']==expected,'support replay must be exactly original free Q plus all declared supports'

def endpoint_chains(state):
    """Bind reported scalars to qualified new contributions and fixed history."""
    old=read(OLD153/'public_manifest.json');oldhash={r['path']:r['SHA256'] for r in old['files']}
    for a in old['archives']:
        index=ROOT/a['member_index']['path'];assert sha(index)==a['member_index']['SHA256']
        oldhash.update({r['member']:r['SHA256'] for r in load_gz(index)})
    cache={};active=set()
    def visit(path):
        p=Path(path).resolve();name=p.relative_to(ROOT).as_posix()
        if name in cache:return cache[name]
        assert name not in active;active.add(name);data=read(p)
        if OLD153.resolve() in p.parents:
            assert oldhash[name]==sha(p);value=(data['lower'],data['upper'])
        else:
            assert OUT.resolve() in p.parents
            previous=[visit(x) for x in data['prior_results']];assert previous
            lo=max(r[0] for r in previous);up=min(r[1] for r in previous)
            pool={tuple(Y) for Y in data['columns']}
            for source in data['prior_results']:
                parent=read(source);assert data['scope']==parent['scope'] and data['Q_SHA']==parent['Q_SHA']
                assert {tuple(Y) for Y in parent['columns']}<=pool
                assert all(s in data['supports'] for s in parent['supports'])
            for cp in p.parent.glob('iter*/certificate.json.gz'):lo=max(lo,load_gz(cp)['coupled_lower'])
            if data['decision']=='PAID_PRICE_BOUND_AND_TRUE_COLUMN_INGEST':
                assert data['upper']==up
                for fact in data['records']:
                    pf=Path(fact['path']);assert sha(pf)==fact['SHA256'];price=read(pf);d=read(fact['direction'])
                    effective=max(F(price['lower']),F(d['inherited_price_lower']))
                    lo=max(lo,outward(F(d['C_Q_exact'])+min(F(d['a_K_exact']),effective),False))
            if 'support_replay' in data and p.parent.parent.name=='support_LP':
                lo=max(lo,load_gz(p.parent/'certificate.json.gz')['lower'])
                assert data['upper']==up,'finite-support upper cannot replace full-hull upper'
            if data['decision'] in ('FULL_Q_RMP_REFRESH_ALL_CURRENT_COLUMNS','DIRECTION_PREPARATION_ALSO_REFRESHED_ALL_COLUMNS'):
                assert data['upper']==min(up,data['refresh']['RMP_objective'])
            assert data['lower']==lo and data['upper']<=up+1e-12 and data['gap']==data['upper']-data['lower']
            value=(data['lower'],data['upper'])
        active.remove(name);cache[name]=value;return value
    for role,rec in state['roles'].items():
        visit(rec['result']);assert read(rec['result'])['role']==role
    return [dict(path=k,SHA256=sha(ROOT/k),lower=v[0],upper=v[1]) for k,v in sorted(cache.items())]

def support_transport(data):
    checks=[]
    for s in data['supports']:
        path=s.get('price_path','')
        if 'unified_exact_round154' not in path:continue
        p=read(ROOT/path);scope=p['scope'];row=s['row'];terms={k:F(v) for k,v in row['terms'].items()}
        beta=F(p['beta']);costs={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}
        error=min((terms.get('G',F(0))-beta)*F(scope[k]) for k in ['gamma_L','gamma_U'])
        for st in scope['stations']:
            error+=min(terms.get(f'state_{st["i"]}_{y}',F(0))-costs[st['i'],y] for y in st['support'])
        assert set(terms)<={'G'}|{f'state_{i}_{y}' for i,y in states(scope)}
        assert row['sense']=='>' and F(row['rhs'])<=F(p['lower'])+error
        assert F(s['transport_exact'])==error
        checks.append(dict(row=row['name'],price_SHA=sha(ROOT/path),signed_transport=True))
    return checks

def run(label='final_evidence_v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    tick=time.perf_counter();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    prices=[];legacy={};directions=[];supports=[];primal=[];native_reads=0
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for path in sorted((OUT/'fixed_prices').glob('*/*/result.json')):
            if not (path.parent/'hull_result.json').exists():continue
            if 'tau_exact' in read(path):prices.append(audit_residual(gp,env,path));native_reads+=1
            else:normalized_price(path,legacy)
            h=read(path.parent/'hull_result.json');p=read(path)
            dp=next(q for q in (OUT/'directions').glob('*/direction.json') if sha(q)==h['direction_SHA']);d=read(dp)
            assert d['scope']==p['scope'] and d['d_exact']==p['d_exact'] and d['beta']==p['beta']
            cq,aK=F(d['C_Q_exact']),F(d['a_K_exact']);effective=max(F(p['lower']),F(d['inherited_price_lower']))
            assert F(h['fixed_certificate_lower'])<=cq+min(aK,effective)
            upper=min([F(d['initial_true_price_upper_exact'])]+[F(v['price_exact']) for v in p['stocks']])
            assert F(h['true_price_upper'])>=upper and F(h['fixed_certificate_ceiling'])>=cq+min(aK,upper)
            assert h['target_proved']==(effective>=F(d['tau_exact'])) and h['target_disproved']==(upper<F(d['tau_exact']))
        for dp in sorted((OUT/'directions').glob('*/direction.json')):
            d=read(dp);scope=d['scope'];cert=load_gz(dp.parent/'certificate.json.gz');assert cert['qualified']
            assert F(d['C_Q_exact'])==F(cert['lower_exact']) and F(d['a_K_exact'])==F(cert['a_true_RMP_exact'])
            prior=read(d['prior_result']);assert sha(d['prior_result'])==d['prior_result_SHA']
            costs={tuple(map(int,k.split(':'))):F(v) for k,v in d['d_exact'].items()}
            fallback=F(d['beta'])*F(scope['gamma_L'])+F(unary_dp(scope,costs)['exact']);inherited=[fallback]
            for rec in d['inherited_price_sources']:
                source=read(rec['path']);assert sha(rec['path'])==rec['SHA256']
                assert source['scope']==scope and source['beta']==d['beta'] and source['d_exact']==d['d_exact']
                inherited.append(F(source['lower']))
            assert F(d['inherited_price_lower'])<=max(inherited)
            assert d['inherited_hull_lower']==prior['lower']
            assert all(F(cert['pi'].get(f'{i}:{y}',0.))==-v for (i,y),v in costs.items())
            true_min=None
            for Y in prior['columns']:
                v=stock_value(scope,Y,d['beta'],costs);assert v['feasible']
                true_min=v['price'] if true_min is None else min(true_min,v['price'])
            assert F(cert['a_true_RMP_exact'])<=min(F(cert['a_raw']),true_min)
            assert true_min==F(d['initial_true_price_upper_exact'])
            assert F(d['zeta_exact'])==F(d['C_Q_exact'])+F(d['tau_exact'])
            assert F(d['zeta_exact'])<=F(d['C_Q_exact'])+min(F(d['a_K_exact']),true_min)
            if d['source_iteration'] is not None:
                original=load_gz(Path(d['source_iteration'])/'certificate.json.gz');assert cert==original
                reused=True
            else:
                qp=Path(d['Q_path']);assert sha(qp)==d['Q_SHA']
                with gp.read(str(qp),env=env) as m:
                    native_reads+=1;matrix=exact_matrix(m);bounds=replay_q_bounds(matrix,load_gz(dp.parent/'Q_bounds.json.gz'))
                    independent_residual(matrix,bounds,cert,scope)
                    if d.get('source_loop_iteration'):
                        original=Path(d['source_loop_iteration'])
                        assert sha(original/'certificate.json.gz')==d['source_certificate_SHA'] and sha(original/'direction.json')==d['source_direction_SHA']
                        assert not prior['refresh_required'] and d['mode']=='saved_updated_midpoint'
                        ceiling=F(d['C_Q_exact'])+min(F(d['a_K_exact']),true_min)
                        assert F(d['zeta_exact'])==min((F(prior['lower'])+F(prior['upper']))/2,ceiling-F(1e-7))
                    elif (dp.parent/'refreshed_pool.json').exists():
                        r=read(dp.parent/'refreshed_pool.json')
                        assert not r['refresh_required'] and r['refresh']['primal']['qualified']
                        primal.append(primal_check(m,scope,r['columns'],dp.parent/'primal.json.gz',r['refresh']['RMP_objective']))
                    else:
                        # The first admitted fresh direction predates the
                        # optional post-ingest refresh metadata. It already
                        # saved its full original-pool primal distribution.
                        assert d['mode']=='fresh_near_optimal' and d['columns']==len(prior['columns'])
                        assert OLD153.resolve() in Path(d['prior_result']).resolve().parents
                        assert not prior.get('refresh_required',False)
                        primal.append(primal_check(m,scope,prior['columns'],dp.parent/'primal.json.gz',d['inherited_hull_upper']))
                reused=False
            directions.append(dict(path=str(dp.relative_to(ROOT)),SHA256=sha(dp),C_Q_qualified=True,all_true_column_min=True,reused_fixed_R153_CQ=reused))
        for cp in sorted((OUT/'support_LP').glob('*/certificate.json.gz')):
            data=read(cp.parent/'result.json');mp=cp.parent/'solve/model.mps'
            with gp.read(str(mp),env=env) as m:
                native_reads+=1;matrix=exact_matrix(m);bounds=replay_q_bounds(matrix,load_gz(cp.parent/'Q_bounds.json.gz'))
                qp=OLD153/'reference'/data['role']/'direct/model.mps';assert sha(qp)==data['Q_SHA']
                with gp.read(str(qp),env=env) as original:
                    native_reads+=1;complete_support_matrix(exact_matrix(original),matrix,[s['row'] for s in data['supports']])
                cert=load_gz(cp);independent_residual(matrix,bounds,cert)
            assert cert['lower']==data['support_replay']['L']
            supports.append(dict(path=str(cp.relative_to(ROOT)),SHA256=sha(cp),support_rows=data['support_replay']['supports'],full_free_Q=True))
        for rp in sorted((OUT/'coupled').glob('*/result.json')):
            data=read(rp)
            if data.get('decision')!='FULL_Q_RMP_REFRESH_ALL_CURRENT_COLUMNS':continue
            assert not data['refresh_required'] and data['refresh']['primal']['qualified']
            qp=OLD153/'reference'/data['role']/'direct/model.mps';assert sha(qp)==data['Q_SHA']
            with gp.read(str(qp),env=env) as m:
                native_reads+=1;primal.append(primal_check(m,data['scope'],data['columns'],rp.parent/'primal.json.gz',data['refresh']['RMP_objective']))
        loops,more_reads=loop_evidence(gp,env,prices,legacy,primal);native_reads+=more_reads
    matrix=read(OUT/'confirmation_matrix.json');arms=[]
    for group in matrix['groups']:
        d=Path(group['launch']['destination']);close=read(d/'verification_closeout.json');arm=read(d/'round154_endpoint.json')
        assert close['implementation_qualified'] and close['performance_eligible'] and close['evidence_complete']
        assert sha(d/'audit.json')==close['audit_SHA']==arm['audit_SHA']
        assert sha(d/'verification_closeout.json')==arm['verification_closeout_SHA']
        sealed=read(d/'audit.json')['endpoint']
        for key in ['U','L','gap','certificate','T_produce','T_cert','arm_id','PE_SHA','input_SHA']:
            assert arm[key]==sealed[key],(arm['arm_id'],key)
        clock=read(d/'arm_total_receipt.json');produce=read(d/'producer_receipt.json')
        assert arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
        assert arm['T_produce']==produce['T_produce'] and arm['T_verify']==clock['T_verify'] and arm['T_total']==clock['T_total']
        assert clock['producer_receipt_SHA']==sha(d/'producer_receipt.json')==close['producer_receipt_SHA']
        assert clock['verification_closeout_SHA']==sha(d/'verification_closeout.json')
        assert arm['T_total']==arm['T_produce']+arm['T_verify']
        assert sha(OUT/group['group']/'identity.json')==group['identity_SHA']
        assert arm['PE_SHA']==read(OUT/'candidate_manifest.json')['production_PE_SHA']
        hp=d/'external/round153_floor/pricing/result.json'
        if hp.exists():audit_RN(hp,legacy)
        if not arm['certificate']:assert arm['T_cert'] is None
        arms.append(dict(position=group['position'],arm_id=arm['arm_id'],qualified=True,U=arm['U'],L=arm['L'],certificate=arm['certificate']))
    state=read(OUT/'science_state.json')
    transport=[]
    for role,rec in state['roles'].items():
        final=read(rec['result']);assert not final.get('refresh_required',False)
        transport.extend(support_transport(final))
        replaypath=Path(rec['support_result']).resolve();replay=read(replaypath)
        assert replay['Q_SHA']==final['Q_SHA']
        if OUT.resolve() in replaypath.resolve().parents:
            assert replay['scope']==final['scope'] and replay['supports']==final['supports']
            assert replay['support_replay']['all_original_variables_free'] and replay['support_replay']['supports']==len(final['supports'])
            assert str((replaypath.parent/'certificate.json.gz').relative_to(ROOT)) in {s['path'] for s in supports}
        else:
            assert OLD153.resolve() in replaypath.resolve().parents
            reused=next(r for r in read(OUT/'reuse_index.json')['dependencies'] if r['member']==replaypath.relative_to(ROOT).as_posix())
            assert sha(replaypath)==reused['SHA256']
            source=read(Path(replay['coupled_source'])/'result.json')
            assert source['scope']==final['scope'] and source['supports']==final['supports']
            last=next(r for r in replay['records'] if r['stage']=='all_supports')
            assert last['all_original_variables_free'] and last['added_rows']==replay['rows']==len(final['supports'])
    chains=endpoint_chains(state)
    history=read(OLD153/'reports/scientific_table.json')['rows']
    for row in read(OUT/'reports/scientific_table.json')['rows']:
        final=read(state['roles'][row['role']]['result']);old=next(r for r in history if r['role']==row['role'])
        assert row['lower']==max(final['lower'],old['coupled_L']) and row['upper']==min(final['upper'],old['coupled_U'])
        assert row['width']==row['upper']-row['lower'] and row['columns']==len(final['columns']) and row['supports']==len(final['supports'])
    source=sources()
    result=dict(PASS=True,UTC=utc(),prices=prices,legacy_price_evidence=legacy,directions=directions,
        complete_free_Q_supports=supports,qualified_numerical_primals=primal,complete_arms=arms,coupled_phases=loops,signed_support_transport=transport,endpoint_scalar_chains=chains,
        Native_model_reads=native_reads,Native_Optimize=0,source_manifest_SHA=sha(OUT/'source_manifest.json'),
        seconds=time.perf_counter()-tick,old_performance_or_producer_repeated=False)
    write(target/'result.json',result)
    print(json.dumps(dict(PASS=True,prices=len(prices)+len(legacy),directions=len(directions),Native_reads=native_reads,Optimize=0)),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
