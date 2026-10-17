"""Second standard-library implementation: exact arithmetic and finite counterexamples.

Does not import production, campaign, reader, generator or decision functions.
Finite enumeration is explicitly not a native LP proof.
"""
from pathlib import Path
from fractions import Fraction as Q
import ast,collections,datetime,hashlib,itertools,json,math,re,time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round123'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def compare(c,p):
    good=all(x.get('numbers_qualified') and all(isinstance(x.get(k),(int,float)) and math.isfinite(x[k]) for k in ['U','L']) for x in [c,p])
    if c['certificate']!=p['certificate']:return ('WIN',False) if c['certificate'] else ('LOSS',True)
    if c['certificate']:
        excess=c['complete_seconds']-p['complete_seconds']; threshold=max(30.,p['complete_seconds']/10)
        return ('LOSS' if excess>=threshold else 'WIN' if excess<=-threshold else 'TIE',excess>=120 and c['complete_seconds']>=2*p['complete_seconds'])
    if not good:return 'UNEVALUABLE',False
    du=c['U']-p['U'];dg=c['gap']-p['gap'];tu=max(.001,abs(p['U'])/100);tg=max(.001,abs(p['gap'])/10)
    improves=du<=-tu or dg<=-tg;worsens=du>=tu or dg>=tg
    return ('MIXED' if improves and worsens else 'WIN' if improves else 'LOSS' if worsens else 'TIE',
        du>=max(.001,.05*abs(p['U'])) and dg>=max(.005,.25*abs(p['gap'])))

def deficit_check():
    path=ROOT/'reference/round122_paper_benchmark/PB-C50-S.txt';text=path.read_text(encoding='utf-8')
    values={}
    for line in text.splitlines()[1:]:
        n,v=line.split('=',1);values[n.strip()]=v.strip()
    b=ast.literal_eval(values['initial'])[1:];D=ast.literal_eval(values['target'])[1:];C=ast.literal_eval(values['capacities'])[1:]
    w=[Q(s.strip()) for s in values['weights'][1:-1].split(',')][1:]
    assert sum(b)==495 and sum(D)==562 and all(d<=c for d,c in zip(D,C)) and min(w)>0
    costs=[Q(3,20)*x/d for x,d in zip(w,D)]
    # Order individual deficit units, independently of the first greedy routine.
    units=sorted((cost,i,j) for i,(cost,d) in enumerate(zip(costs,D)) for j in range(d))
    best=sum(x[0] for x in units[:67]);delta=units[0][0]
    assert best==Q('0.26064825') and 67*delta==Q('0.24814831875')
    binary_costs=[Q.from_float(.15)*Q.from_float(float(x))/d for x,d in zip(w,D)]
    binary_units=sorted((cost,i,j) for i,(cost,d) in enumerate(zip(binary_costs,D)) for j in range(d))
    recorded=read(OUT/'mathematics/positive_objective.json')
    assert Q(recorded['decimal']['L_pen'])==best and Q(recorded['decimal']['simple_bound'])==67*delta
    assert Q(recorded['parsed_binary64_as_exact_real_inputs']['L_pen'])==sum(x[0] for x in binary_units[:67])
    # Brute-force complete toy inventory relaxations against the shortage form.
    enumerated=0
    for targets in [(1,2),(2,2),(1,2,3)]:
        caps=tuple(d+1 for d in targets);cost=tuple(Q(i+1,7) for i in range(len(targets)))
        for B in range(sum(targets)):
            full=min(sum(c*abs(y-d) for c,y,d in zip(cost,Y,targets))
                for Y in itertools.product(*(range(c+1) for c in caps)) if sum(Y)<=B)
            shortage=sum(targets)-B
            reduced=min(sum(c*u for c,u in zip(cost,U))
                for U in itertools.product(*(range(d+1) for d in targets)) if sum(U)==shortage)
            assert full==reduced;enumerated+=1
    # Necessary-premise counterexamples, each actually evaluated.
    # External departure supply permits targets even though station B<Dsum.
    targets=(2,2);initial=(1,1);final=(2,2);return_load=0;departure_supply=2
    assert sum(final)+return_load==sum(initial)+departure_supply and sum(final)>sum(initial)
    # Zero weights and uniform ratios permit F=0 despite a station shortage.
    ratios=[Q(1,2),Q(1,2)];g=abs(ratios[0]-ratios[1])/(2*sum(ratios));pen=sum(Q(0)*abs(r-1) for r in ratios)
    assert g+pen==0
    # Target capacity is needed for equality with the unrestricted deficit form.
    targets=(2,2);caps=(1,3);cost=(Q(10),Q(1));B=3
    constrained=min(sum(c*abs(y-d) for c,y,d in zip(cost,Y,targets)) for Y in itertools.product(*(range(c+1) for c in caps)) if sum(Y)<=B)
    uncapacitated_deficit=min(sum(c*u for c,u in zip(cost,U)) for U in itertools.product(range(3),repeat=2) if sum(U)==1)
    assert constrained>uncapacitated_deficit
    return dict(simple_decimal=str(67*delta),L_pen_decimal=str(best),finite_toy_full_inventory_equal_deficit_cases=enumerated,
        counterexamples=dict(external_supply_breaks_station_mass_bound=True,zero_weights_do_not_imply_strict_positive_F=True,
            target_capacity_failure_changes_deficit_optimum=[str(constrained),str(uncapacitated_deficit)]),
        not_a_new_production_bound=True,input_SHA=sha(path))

def redundancy_check():
    results=[]
    for role in ['PB-C35-U','PB-B35-B']:
        folder=OUT/'mathematics/d1_saved_models'/role;paths=list(folder.glob('*.lp'));assert len(paths)==1
        p=paths[0];meta=read(str(p)+'.round120.json');native_path=next(folder.glob('*.native.json'));native=read(native_path)
        assert sha(p)==native['model_SHA']==meta['SHA']
        named={};objective=None;bounds={};section=None
        for line in p.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if line in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:section=line;continue
            if section=='Minimize':objective=line.split(':',1)[1].strip()
            if section=='Bounds':
                lo,_,name,__,hi=line.split();bounds[name]=(Q(lo),Q(hi))
            if line.startswith(('r120_g_lower:','r120_g_upper:','r120_f_lower:')):
                name,body=line.split(':',1);named[name]=body.strip()
        assert objective and objective.startswith('G + ') and Q.from_float(native['objective_constant'])==0
        penalties=re.findall(r'([0-9.eE+-]+) (e_\d+)',objective)
        assert len(penalties)==35 and all(Q(coeff)>0 and bounds[name][0]>=0 for coeff,name in penalties)
        low=re.fullmatch(r'G - (\S+) r120_h >= (\S+)',named['r120_g_lower']);assert low
        body=named['r120_f_lower'];lhs,rhs=body.rsplit('>=',1);base_lhs,hterm=lhs.strip().rsplit(' - ',1)
        hcoef,hname=hterm.split();assert hname=='r120_h' and base_lhs==objective
        A,D,B,E=Q(low[2]),Q(low[1]),Q(rhs.strip()),Q(hcoef)
        decimal=[A-B,A+D-B-E];assert min(decimal)>=0
        aa,dd,bb,ee=[Q.from_float(native[n]) for n in ['lower_base','lower_delta','objective_base','objective_delta']]
        actual=[aa-bb,aa+dd-bb-ee];assert min(actual)>=0
        for denominator in range(1,21):
            for numerator in range(denominator+1):
                h=Q(numerator,denominator);assert A+D*h>=B+E*h and aa+dd*h>=bb+ee*h
        results.append(dict(role=role,actual_ObjCon=0,model_SHA=sha(p),decimal_endpoint_slacks=list(map(str,decimal)),
            native_binary64_endpoint_slacks=list(map(str,actual)),complete_objective_row_checked=True,nonnegative_e_bounds=35))
    cases=0
    for a,m,b in [(Q(0),Q(1,2),Q(1)),(Q(1,4),Q(1,2),Q(3,4))]:
        for beta0,beta1 in [(Q(0),Q(0)),(a,m),(a,m-Q(1,100))]:
            for gstep in range(13):
                g=a+(b-a)*Q(gstep,12)
                for penalty in [Q(0),Q(1,10),Q(1)]:
                    f=g+penalty
                    valid=[h for h in [Q(0),Q(1)] if a+(m-a)*h<=g<=m+(b-m)*h and f>=beta0+(beta1-beta0)*h]
                    assert valid;cases+=1
    # Actually reject a feasible original point if beta0>a.
    a,m,b=Q(0),Q(1,2),Q(1);g=f=Q(0);beta0,beta1=Q(1,4),m
    assert not [h for h in [Q(0),Q(1)] if a+(m-a)*h<=g<=m+(b-m)*h and f>=beta0+(beta1-beta0)*h]
    # If f>=g fails (e.g. negative objective constant), the row need not follow.
    h=Q(0);g=Q(0);objcon=Q(-1,4);f=g+objcon
    assert g>=a+(m-a)*h and f<Q(0)
    return dict(actual_models=results,finite_exact_binary_extension_cases=cases,
        counterexamples=dict(beta0_above_a_can_shrink_projection=True,negative_ObjCon_breaks_f_ge_g=True),
        finite_checks_not_native_LP_proof=True)

def prior_pairs():
    root=ROOT/'results/unified_exact_round122';arms=read(root/'all32_arms.json');pairs=read(root/'all48_pairs.json')
    by={(a['group_number'],a['arm']):a for a in arms};bad=[];counts=collections.Counter()
    for q in pairs:
        found=compare(by[q['group_number'],q['candidate']],by[q['group_number'],q['control']])
        assert found==(q['classification'],q['severe_regression']);counts[q['classification']]+=1
        if q['classification'] in ['LOSS','MIXED','UNEVALUABLE'] or q['severe_regression']:bad.append(q)
    assert len(arms)==32 and len(pairs)==48 and len(bad)==9
    return dict(arms=32,pairs=48,independently_recomputed_classes=dict(counts),all_nine_negative_or_mixed=bad,
        prior_native_reproduction=False,does_not_revote_D1_promotion=True,
        exact_sources={name:sha(root/name) for name in ['all32_arms.json','all48_pairs.json']})

def main():
    tick=time.perf_counter();result=dict(method='Self-review using an independently written exact arithmetic/enumeration/comparison implementation; no separate executor claimed',
        strict_positivity=deficit_check(),D1_actual_redundancy=redundancy_check(),R122=prior_pairs(),
        new_native_starts=0,Optimize=0,no_new_route_or_production_bound=True)
    result.update(decision='ACCEPT_WITH_STATED_SCOPE',seconds=time.perf_counter()-tick,script_SHA=sha(__file__),UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write(OUT/'review/independent_math_and_R122.json',result)
    print(json.dumps(dict(decision=result['decision'],seconds=result['seconds'],R122_pairs=48,negative_or_mixed=9)))

if __name__=='__main__':main()
