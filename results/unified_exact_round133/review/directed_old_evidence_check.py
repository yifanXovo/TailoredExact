"""Independent finite read-only R132 check; no native/optimizer imports.

Maps the own-zero fleet into every column, checks actual binary64 LP
coefficients as exact rationals, and retains the failure of tight mathematical
auxiliaries separately from a possible rounded-matrix feasible completion.
"""
from pathlib import Path
from fractions import Fraction as F
import ast, csv, hashlib, json, math, re, runpy, sys, time

OLD = Path(sys.argv[1]) if len(sys.argv)>1 else Path('E:/codes/ExactEBRP-work/worktrees/round132')
DEST = Path(__file__).resolve().parent
READS = {}

def raw(p):
    b=p.read_bytes(); READS[str(p)]=dict(SHA256=hashlib.sha256(b).hexdigest(),bytes=len(b)); return b
def read(p): return json.loads(raw(p))
def rows(p): return list(csv.DictReader(raw(p).decode('utf-8-sig').splitlines()))
def number(s): return F.from_float(float(s))
def expression(s):
    t=s.split(); out=[]; i=0; sign=F(1)
    while i<len(t):
        if t[i] in ('+','-'): sign=F(1 if t[i]=='+' else -1);i+=1
        q=t[i];i+=1
        if re.fullmatch(r'[A-Za-z_]\w*',q): out.append((q,sign));sign=F(1);continue
        c=sign*number(q);sign=F(1)
        if i<len(t) and re.fullmatch(r'[A-Za-z_]\w*',t[i]):out.append((t[i],c));i+=1
        else:out.append((None,c))
    return out
def value(terms,point):return sum((c*(1 if n is None else point[n]) for n,c in terms),F(0))
def rational(x):return dict(exact=str(x),display=float(x))

def model(p):
    text=raw(p).decode(); section=None; bounds={}; types={}; constraints=[];objective=None
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('\\'):continue
        if line in ('Minimize','Subject To','Bounds','Generals','Binaries','End'):section=line;continue
        if section=='Minimize': assert objective is None;objective=expression(line.split(':',1)[1])
        elif section=='Subject To':
            label,body=line.split(':',1);m=re.fullmatch(r'(.*) (<=|>=|=) (\S+)',body.strip());assert m,line
            constraints.append((label,expression(m[1]),m[2],number(m[3])))
        elif section=='Bounds':
            t=line.split();assert len(t)==5 and t[1]==t[3]=='<='
            assert t[2] not in bounds;bounds[t[2]]=(number(t[0]),number(t[4]))
        elif section in ('Generals','Binaries'):
            for n in line.split(): assert n not in types;types[n]='I' if section=='Generals' else 'B'
        else:raise AssertionError((section,line))
    assert section=='End' and objective is not None and constraints and bounds
    return bounds,types,constraints,objective

def zero_point(bounds,witness,initial,target,adjust=False,constraints=()):
    y=initial[:];direct={}
    for route in witness['routes']:
        k=route['vehicle'];ns=route['nodes'];ops={x['station']:x for x in route['operations']};load=0
        for pos,(i,j) in enumerate(zip(ns,ns[1:]),1):
            if i==j:continue
            direct[f'x_{k}_{i}_{j}']=F(1);direct[f'conn_{k}_{i}_{j}']=F(len(ns)-1-pos)
        for pos,i in enumerate(ns[1:-1],1):
            op=ops[i];p,d=op['pickup'],op['drop'];load+=p-d;y[i]+=d-p
            for pre,v in [('z',1),('mode',int(p>0)),('p',p),('d',d),('ord',pos),('load',load)]:direct[f'{pre}_{k}_{i}']=F(v)
    assert y[1:]==target[1:]
    r={i:F(1) for i in range(1,len(y))}
    if adjust:
        for label,terms,sense,rhs in constraints:
            # Actual ratio equations: r_i - binary64(1/D_i) Y_i = 0.
            if sense!='=' or rhs or len(terms)!=2:continue
            rr=next(((n,c) for n,c in terms if n and re.fullmatch(r'r_\d+',n)),None)
            yy=next(((n,c) for n,c in terms if n and re.fullmatch(r'Y_\d+',n)),None)
            if rr and yy:
                i=int(rr[0][2:]);assert yy[0]=='Y_'+str(i);r[i]=-yy[1]*y[i]/rr[1]
    # A rational auxiliary epigraph slack; objective remains far below 1e-7.
    # This is a diagnostic feasible point, not a changed model or policy.
    g=F(1,2**40) if adjust else F(0)
    e={i:abs(r[i]-1) for i in r};point={}
    # Actual W_SP inequalities only need a feasible value, checked below.
    weights=read_weights
    penalty=sum((F.from_float(float(weights[i]))*e[i] for i in r),F(0));S=sum(r.values())
    for n in bounds:
        if n in direct:v=direct[n]
        elif re.fullmatch(r'(x|conn)_\d+_\d+_\d+|(z|mode|p|d|ord|load)_\d+_\d+',n):v=F(0)
        elif n=='G':v=g
        elif n=='r_min':v=min(r.values())
        elif n=='r_max':v=max(r.values())
        elif n=='W_SP':v=S*penalty
        elif m:=re.fullmatch(r'(Y|r|e|zprod)_(\d+)',n):
            family,i=m[1],int(m[2]);v={'Y':F(y[i]),'r':r[i],'e':e[i],'zprod':g*y[i]}[family]
        elif m:=re.fullmatch(r'(h|state|state_g)_(\d+)_(\d+)',n):
            family,i,j=m[1],int(m[2]),int(m[3]);v=abs(r[i]-r[j]) if family=='h' else F(y[i]==j)*(g if family=='state_g' else 1)
        else:raise AssertionError(('unmapped',n))
        point[n]=v
    return point

def audit(bounds,types,constraints,obj,point):
    failures=[];maximum=F(0);equalities=0;exact_nonzero_equalities=[]
    for n,(l,u) in bounds.items():
        v=point[n];bad=max(l-v,v-u,F(0))
        if bad:failures.append(dict(kind='bound',name=n,residual=rational(bad)))
        if n in types and (v.denominator!=1 or (types[n]=='B' and v not in (0,1))):raise AssertionError(('integer',n,v))
    for name,terms,sense,rhs in constraints:
        d=value(terms,point)-rhs
        violation=abs(d) if sense=='=' else max(d if sense=='<=' else -d,F(0))
        maximum=max(maximum,violation)
        if sense=='=':
            equalities+=1
            if d:exact_nonzero_equalities.append(dict(name=name,residual=rational(d)))
        if violation:failures.append(dict(kind='row',name=name,sense=sense,residual=rational(violation)))
    return dict(rows=len(constraints),columns=len(bounds),equalities=equalities,all_types_checked=True,
        completion_SHA256=hashlib.sha256('\n'.join(n+'='+str(point[n]) for n in sorted(point)).encode()).hexdigest(),
        exactly_feasible=not failures,maximum_violation=rational(maximum),failure_count=len(failures),
        failures=failures[:80],nonzero_equalities=exact_nonzero_equalities[:40],objective=rational(value(obj,point)))

start=time.perf_counter();r=OLD/'results/unified_exact_round132';camp=r/'campaign'
prior_checker=r/'review/source_loss_narrow_check.py'
raw(prior_checker)
prior=runpy.run_path(str(prior_checker))['check']()
assert prior['status']=='FINITE_ONE_ARM_FINDINGS_CONFIRMED' and prior['no_Optimize'] and prior['no_native_import']
d=camp/'D_group24/raw/02_X-35-U_S1_R1_S2';scope=read(d/'journal/event_9.json');w=read(d/'journal/event_21.json')
assert scope['call']==w['call']==4 and w['objective']==w['G']==w['P']==0
expected=[2.2155204177669103e-7,2.3794866331140976e-7,2.889725344877011e-7]
assert [read(d/f'journal/event_{i}.json')['native_bound'] for i in [17,18,19]]==expected
assert scope['lower_g']==0 and scope['upper_g']==scope['cutoff']==0.16038610038610038
inp=read(camp/'D_group24/identity.json')['launches'][0]['panel']['input_path'];it=raw(OLD/inp).decode()
vec=lambda name:ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',it,re.M)[1])
b,target,read_weights=vec('initial'),vec('target'),vec('weights')
recorded_model=scope['model_path'].replace('\\','/')
assert '/results/' in recorded_model
mp=OLD/'results'/recorded_model.split('/results/',1)[1]
bounds,types,cons,obj=model(mp)
assert READS[str(mp)]['SHA256']=='a630251059be795777416ea1d63e6d8881c17baf1b75ccba776b5004a7294bc1'
tight=audit(bounds,types,cons,obj,zero_point(bounds,w,b,target))
adjusted=audit(bounds,types,cons,obj,zero_point(bounds,w,b,target,True,cons))
trace=rows(d/'external/global_bound_trace.csv');hits=[x for x in trace if x['active_leaf_valid_lower_bound'] and float(x['active_leaf_valid_lower_bound']) in expected]
assert len(hits)==3 and [float(x['valid_global_lower_bound']) for x in hits]==expected
events=rows(d/'external/paper_tree_events.csv');ledger=rows(d/'external/paper_optimize_ledger.csv');targets=rows(d/'external/native_target_ledger.csv')
assert len(ledger)==4 and [q['solve_kind'] for q in ledger]==['LP','LP','LP','MIP'] and not targets
assert [q['event'] for q in events]==['lp_complete','terminal_mip_complete']
geom=camp/'C_group03/raw/02_SC-B20-S_S0_R1_S2R';launch=read(geom/'launch.json');cr=read(geom/'result.json')
assert launch['expression']=='geom' and cr['strict_certified_original_problem'] is False
log=raw(geom/'external/native_logs/L0_terminal_mip.gurobi.log').decode()
assert 'Optimal solution found' in log and 'in 705.47 seconds' in log
gap=cr['upper_bound']-cr['lower_bound'];assert gap>1e-7
receipt=dict(scope='finite independent read-only original evidence and exact rounded-matrix extension check',
    C_R1_decision='new native reproduction unnecessary: archived own physical and rounded-matrix counterexamples independently checked; native internal cause remains UNKNOWN',
    C_R2_decision='new vector acquisition required for deeper mapping diagnosis',
    reused_prior_physical_and_seal_check=prior,
    D24=dict(scope=scope,original_bounds=expected,own_witness_sequence=21,physical_objective=0,
        tight_mathematical_completion=tight,rounded_matrix_completion=adjusted,trace_pollution=hits,
        actual_Optimize=len(ledger),target_phases=len(targets),tree_events=events,
        outer_bad_bound_consumption_proven=False,native_internal_pruning='UNKNOWN'),
    C03=dict(expression=launch['expression'],physical_U=cr['upper_bound'],native_bound=cr['lower_bound'],physical_gap=gap,
        native_return='OPTIMAL',native_runtime_seconds=705.47,actual_native_vector_saved=False,qualification='qualified-open unless separate source failure'),
    reads=READS,optimizer_calls=0,native_modules=0,compilations=0,outer_seconds=time.perf_counter()-start)
(DEST/'directed_old_evidence_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(tight=tight,adjusted=adjusted,seconds=receipt['outer_seconds']),ensure_ascii=False))
