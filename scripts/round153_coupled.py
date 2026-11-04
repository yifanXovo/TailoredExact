"""Full routing LP coupled to the entire declared integer inventory domain.

Restricted masters supply numerical primal uppers on the strengthened LP.
Full-domain pricing plus exact original-Q dual residual support supply lowers.
"""
from fractions import Fraction as F
from round143_math import outward
from round153_lp import add_rows,finite_bounds,dual_certificate,primal_record,optimize,semantics
from round153_pricing import Oracle,stock_value,keyed,serial_stock
from round153_common import *

def seeds(role,scope):
    """Only reevaluated legal stock vectors; compatibility is not assumed."""
    columns={};sources=[]
    paths=list((OLD/'projection').glob(f'{role}_*/result.json'))+list((OLD/'global').glob(f'{role}_*/projection/result.json'))
    paths+=list((OLD/'discovery').glob(f'{role}_*/iter*/pricing/result.json'))
    paths+=list((OLD/'global').glob(f'{role}_*/iter*/pricing/result.json'))
    paths+=list((OLD/'oracle').glob(f'{role}_*/result.json'))
    paths+=list((OUT/'projection'/role).glob('result.json'))
    paths+=list((OUT/'floor').glob(f'{role}_*/pricing/result.json'))
    for p in paths:
        data=read(p)
        # Historical prices may have used active/complement subdomains. Reuse
        # only independently reevaluated stock vectors, never their price or
        # dual bounds. A legal vector remains a column in the current full R.
        for rec in data.get('stocks',[])+data.get('paths',[]):
            v=stock_value(scope,rec['Y'])
            if v['feasible']:columns[tuple(v['Y'])]=v
        sources.append(dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),commit=SCIENCE if OLD in p.parents else 'current_round153_paid_evidence',
                            identical_price_scope=data.get('scope')==scope,only_true_legal_columns_reused=True))
    return sorted(columns),sources

def support_row(scope,beta,pi,lower,index):
    bh=float(beta) if abs(beta)>=1e-12 else 0.;terms={'G':bh} if bh else {};correction=min((F(bh)-F(beta))*F(scope[k]) for k in ('gamma_L','gamma_U'))
    for s in scope['stations']:
        errors=[]
        for y in s['support']:
            original=-F(pi.get((s['i'],y),0.));v=float(original);v=v if abs(v)>=1e-12 else 0.
            errors.append(F(v)-original)
            if v:terms[f'state_{s["i"]}_{y}']=v
        correction+=min(errors)
    return dict(name=f'r153_coupled_support_{index:05}',terms=terms,sense='>',rhs=outward(F(lower)+correction,False)),str(correction)

class Master:
    def __init__(self,m,scope,gp,env=None):
        self.m=m;self.scope=scope;self.gp=gp;self.columns={};self.values={};self.art=[]
        self.env=env or m._env
        self.original={v.VarName:v.Obj for v in m.getVars()};self.original_names=set(self.original)
        self.original_constant=m.ObjCon
        self.original_rows={c.ConstrName for c in m.getConstrs()};self.original_semantics=semantics(m)
        # Bounds must come from Q before any finite inventory columns exist.
        self.bounds,self.derivations=finite_bounds(m)
        self.conv=m.addConstr(gp.LinExpr()==1,name='hull_convexity');self.links={}
        for s in scope['stations']:
            # One omitted link per site is implied by one-hot and convexity.
            for y in s['support'][1:]:
                self.links[s['i'],y]=m.addConstr(-m.getVarByName(f'state_{s["i"]}_{y}')==0,name=f'hull_link_{s["i"]}_{y}')
        self.gini=m.addConstr(m.getVarByName('G')>=1e-8,name='hull_gini')
        self.gini_margin=1e-8;m.update();self.phase=False

    def add(self,Y):
        Y=tuple(map(int,Y))
        if Y in self.columns:return False
        v=stock_value(self.scope,Y);assert v['feasible'];coeff=outward(v['f'],True)
        constraints=[self.conv,self.gini];coeffs=[1.,-coeff]
        for s,y in zip(self.scope['stations'],Y):
            if (s['i'],y) in self.links:constraints.append(self.links[s['i'],y]);coeffs.append(1.)
        var=self.m.addVar(lb=0.,obj=0.,column=self.gp.Column(coeffs,constraints),name=f'hull_lambda_{len(self.columns):05}')
        self.columns[Y]=var;self.values[Y]=v;return True

    def start_phase(self):
        assert not self.phase;self.phase=True
        self.m.ObjCon=0.
        for v in self.m.getVars():v.Obj=0.
        for k,c in self.links.items():
            for sign in [-1,1]:
                self.art.append(self.m.addVar(lb=0,obj=1,column=self.gp.Column([sign],[c]),name=f'hull_art_{k[0]}_{k[1]}_{sign}'))
        self.art.append(self.m.addVar(lb=0,obj=1,column=self.gp.Column([1.],[self.gini]),name='hull_art_gini'))
        self.m.update()

    def finish_phase(self):
        assert self.phase
        self.m.remove(self.art);self.art=[]
        for name,obj in self.original.items():self.m.getVarByName(name).Obj=obj
        self.m.ObjCon=self.original_constant
        self.phase=False;self.m.update()
        assert semantics(self.m,self.original_names,self.original_rows)==self.original_semantics

    def prices(self):
        return self.conv.Pi,{k:c.Pi for k,c in self.links.items()},max(0.,self.gini.Pi)

    def certificate(self,a,pi,beta,lower,multipliers=None):
        assert not self.phase
        # Excluding the artificial 1e-8 completion margin gives the intended
        # true hull's dual; no restricted-column-derived variable bounds enter.
        cert=dual_certificate(self.m,pi=multipliers,bounds=self.bounds,exclude_columns=[v.VarName for v in self.columns.values()],
                              exclude_rhs=['hull_convexity','hull_gini'])
        assert cert['qualified'],cert['unresolved_infinite']
        minK=min(F(beta)*v['f']-sum((F(pi.get((s['i'],y),0.)) for s,y in zip(self.scope['stations'],Y)),F(0)) for Y,v in self.values.items())
        aK=min(F(a),minK);DK=F(cert['lower_exact'])+aK;delta=max(F(0),aK-F(lower))
        cert.update(a_raw=a,a_true_RMP=outward(aK,False),a_true_RMP_exact=str(aK),true_column_min_exact=str(minK),
                    D_K=outward(DK,False),D_K_exact=str(DK),delta=outward(delta,True),delta_exact=str(delta),
                    coupled_lower=outward(DK-delta,False),beta=beta,pi=keyed(pi),pricing_lower=lower,
                    one_convexity_correction=True,completion_margin_not_in_lower=True,bounds_derived_only_from_Q=True)
        return cert

    def primal(self):
        assert not self.phase
        r=primal_record(self.m);lam=[(Y,var.X) for Y,var in self.columns.items()]
        mass=math.fsum(z for Y,z in lam);negative=sum(max(0.,-z) for Y,z in lam)
        expected=sum((F(z)*self.values[Y]['f'] for Y,z in lam),F(0))
        mismatch=max(abs(math.fsum(z for Y,z in lam if Y[j]==y)-self.m.getVarByName(f'state_{s["i"]}_{y}').X)
                     for j,s in enumerate(self.scope['stations']) for y in s['support'])
        completion=F(self.m.getVarByName('G').X)-expected
        r.update(mass=mass,negative_mass=negative,full_marginal_mismatch=mismatch,
                 true_expected_f_exact=str(expected),true_completion_slack_exact=str(completion),
                 true_completion_slack=float(completion),column_count=len(lam),positive_columns=sum(z>1e-10 for Y,z in lam),
                 upper_is_strengthened_LP_not_physical=True)
        r['qualified']=r['qualified'] and abs(mass-1)<=1e-8 and negative<=1e-8 and mismatch<=1e-8 and completion>=0
        return r

def run(role,label='initial',seconds=3000.,price_cap=30.,tolerance=1e-4,old_joint=False,resume=None,stabilize=False):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    seconds=float(seconds);price_cap=float(price_cap);tolerance=float(tolerance)
    old_joint=str(old_joint).lower() in ('true','1','yes')
    stabilization_mode=str(stabilize).lower()
    stabilize=stabilization_mode in ('true','1','yes','level','level_zero','level_zero_pool','level_zero_pool_bins4','zero_pool')
    level_mode=stabilization_mode.startswith('level')
    all_pool=stabilization_mode in ('level_zero_pool','level_zero_pool_bins4','zero_pool')
    bins4=stabilization_mode=='level_zero_pool_bins4'
    target=OUT/'coupled'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    ref=OUT/'reference'/role;scope=read(ref/'domain.json')['scope'];qpath=ref/'direct/model.mps';qresult=read(ref/'direct/result.json')
    columns,source=seeds(role,scope)
    lower=qresult['L'];upper=None;supports=[];records=[];inherited=[]
    if resume and resume!='none':
        previous=read(Path(resume)/'result.json');assert previous['scope']==scope and previous['Q_SHA']==sha(qpath)
        columns=sorted(set(columns)|{tuple(Y) for Y in previous['columns']});lower=max(lower,previous['lower']);upper=previous['upper']
        supports=previous['supports'];inherited=[str(Path(resume)/'result.json')]
    write(target/'plan.json',dict(UTC=utc(),role=role,scope=scope,Q_SHA=sha(qpath),initial_columns=len(columns),
          price_cap=price_cap,outer_cap=seconds,absolute_target=tolerance,old_joint_pricing=old_joint,
          default_Seed=0,Threads=1,prior_upper_source=inherited,stabilize_dual=stabilize,
          stabilization_mode=stabilization_mode,full_price_positive_S_parts=4 if bins4 else 1,
          upper_identity='strengthened LP value only'))
    write(target/'seed_sources.json',source)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(qpath),env=env) as m:
            master=Master(m,scope,gp,env)
            for Y in columns:master.add(Y)
            assert master.columns
            m.update()
            if bins4:
                from round153_partitioned import PartitionedOracle
                oracle=PartitionedOracle(scope,env,old_joint=old_joint)
            else:oracle=Oracle(scope,env,old_joint=old_joint)
            reason='outer_budget_checkpoint';iteration=0
            save_gz(target/'Q_bounds.json.gz',dict(bounds=master.bounds,derivations=master.derivations))
            result=dict(role=role,label=label,scope=scope,Q_SHA=sha(qpath),lower=lower,upper=upper,
                        gap=upper-lower if upper is not None else None,columns=[list(Y) for Y in master.columns],
                        records=records,supports=supports,prior_results=inherited,seconds=time.perf_counter()-tick,
                        decision='INITIALIZED_UNDECIDED',upper_is_not_physical=True,original_variables_free=True)
            write(target/'result.json',result)
            while time.perf_counter()-tick < seconds-price_cap-30:
                folder=target/f'iter{iteration:05}';rr=optimize(m,folder,cap=min(180.,seconds-(time.perf_counter()-tick)-10),save_model=(iteration==0))
                if rr['Status']==3 and not master.phase:
                    master.start_phase();write(folder/'phase_transition.json',dict(reason='restricted_columns_infeasible',full_hull_infeasibility_claim=False))
                    iteration+=1;continue
                assert rr['Status']==2,rr
                if master.phase and m.ObjVal<=1e-8:
                    master.finish_phase();write(folder/'phase_transition.json',dict(reason='artificial_objective_zero',normal_upper_not_taken_from_phase=True))
                    iteration+=1;continue
                a,pi,beta=master.prices();selected=None;selection_record=None;previous_lower=lower
                if stabilize and not master.phase:
                    from round153_stabilize import select_dual
                    available=seconds-(time.perf_counter()-tick)-price_cap-15.
                    if available<=1.:reason='outer_budget_checkpoint_before_dual_selection';break
                    # A level is only a candidate dual objective, never a
                    # certified lower. Every selected multiplier still passes
                    # the Q residual support and full-domain pricing below.
                    candidate_upper=min(m.ObjVal,upper) if upper is not None else m.ObjVal
                    band=max(min(1e-7,tolerance/10),m.ObjVal-(lower+candidate_upper)/2) if level_mode else min(1e-7,tolerance/10)
                    selected,selection_record=select_dual(master,folder/'dual_selection',band=band,cap=min(120.,available),center='zero' if stabilization_mode.startswith('level_zero') or stabilization_mode=='zero_pool' else 'AP')
                    if selected:
                        a=selected['hull_convexity'];pi={k:selected[c.ConstrName] for k,c in master.links.items()};beta=max(0.,selected['hull_gini'])
                d={k:-v for k,v in pi.items()}
                primal=None
                if not master.phase:
                    primal=master.primal()
                    if primal['qualified']:
                        if upper is None or m.ObjVal<upper:
                            upper=m.ObjVal;save_gz(target/'best_primal.json.gz',dict(point={v.VarName:v.X for v in m.getVars()},stocks=[dict(Y=list(Y),weight=v.X,f_exact=str(master.values[Y]['f'])) for Y,v in master.columns.items() if abs(v.X)>1e-14],check=primal))
                # Existing columns are true price uppers; warm only the best few
                # on the current actual potential, not a fixed active support.
                warm=sorted(master.values,key=lambda Y:F(beta)*master.values[Y]['f']+sum((F(d.get((s['i'],y),0.)) for s,y in zip(scope['stations'],Y)),F(0)))[:4]
                price=oracle.price(beta,d,folder/'pricing',cap=price_cap,warm=warm)
                assert price['lower'] is not None
                cert=None
                if not master.phase:
                    cert=master.certificate(a,pi,beta,price['lower'],selected);lower=max(lower,cert['coupled_lower'])
                    save_gz(folder/'certificate.json.gz',cert)
                    row,correction=support_row(scope,beta,pi,price['lower'],len(supports))
                    supports.append(dict(row=row,transport_exact=correction,price_path=str((folder/'pricing/result.json').relative_to(ROOT)),beta=beta))
                added=0;added_negative=0;columns_before=len(master.columns)
                for v in sorted(price['stocks'],key=lambda v:v['price']):
                    # Several true negative reduced-cost columns reduce master
                    # degeneracy without changing the full pricing domain.
                    negative=v['price'] < a-1e-9
                    if all_pool or negative:
                        fresh=master.add(v['Y']);added+=fresh;added_negative+=int(fresh and negative)
                m.update()
                rec=dict(iteration=iteration,phase_I=master.phase,RMP_objective=rr['objective'],primal=primal,
                         beta=beta,a=a,pricing_lower=price['lower'],pricing_upper=price['upper'],
                         reduced_cost_upper=price['upper']-a if price['upper'] is not None else None,
                         D_K=cert['D_K'] if cert else None,correction=cert['delta'] if cert else None,
                         lower=lower,upper=upper,gap=upper-lower if upper is not None else None,
                         columns=len(master.columns),columns_before=columns_before,added=added,added_negative=added_negative,
                         all_true_legal_pool_columns=all_pool,pricing_seconds=price['seconds'],elapsed_seconds=time.perf_counter()-tick,
                         dual_selection=selection_record['status'] if selection_record else 'BASIC_RMP_DUAL',
                         dual_band=selection_record['dual_band'] if selection_record else None,
                         selection_mode=stabilization_mode)
                records.append(rec);write(folder/'result.json',rec)
                result=dict(role=role,label=label,scope=scope,Q_SHA=sha(qpath),lower=lower,upper=upper,
                            gap=upper-lower if upper is not None else None,columns=[list(Y) for Y in master.columns],
                            records=records,supports=supports,prior_results=inherited,seconds=time.perf_counter()-tick,
                            decision='RUNNING',upper_is_not_physical=True,original_variables_free=True)
                write(target/'result.json',result)
                print(json.dumps({k:rec[k] for k in ['iteration','phase_I','RMP_objective','beta','lower','upper','gap','columns','added','elapsed_seconds']}),flush=True)
                if (target/'checkpoint_requested.json').exists():reason='reviewed_adaptive_checkpoint';break
                if upper is not None and upper-lower<=tolerance:reason='requested_interval_accuracy';break
                if added==0:
                    if not(level_mode and lower>previous_lower+max(1e-8,tolerance/100)):
                        reason='pricing_unresolved_no_new_negative_column' if price['lower']<a-1e-7 else 'numerical_or_primal_qualification_limit'
                        break
                iteration+=1
            result['phase_I_at_exit']=master.phase
            result['columns']=[list(Y) for Y in master.columns]
            m.write(str(target/'last_master.mps'))
            if m.Status==2:m.write(str(target/'last_master.bas'))
            oracle.close()
    result.update(decision=reason,seconds=time.perf_counter()-tick)
    write(target/'result.json',result);print(json.dumps(dict(role=role,label=label,lower=lower,upper=upper,decision=reason)),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
