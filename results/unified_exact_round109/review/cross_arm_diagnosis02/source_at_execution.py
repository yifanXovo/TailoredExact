"""Independent offline proof for the main05 numerical contradiction.
No native environment, solver, Start submission, production edits or rerun.
The cross-arm vector is a diagnostic witness, never supplied to production.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import argparse,copy,csv,hashlib,json,math,re,runpy,sys,time,traceback

ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
ROOT=Path(args.root).resolve();OUT=ROOT/'results/unified_exact_round109';DEST=Path(args.out).resolve();assert DEST.is_relative_to(OUT/'review');DEST.mkdir(exist_ok=False)
class Tee:
    def __init__(self,terminal,path):self.terminal=terminal;self.file=Path(path).open('x',encoding='utf-8',newline='\n')
    def write(self,s):self.terminal.write(s);self.file.write(s);self.file.flush();return len(s)
    def flush(self):self.terminal.flush();self.file.flush()
sys.stdout=Tee(sys.stdout,DEST/'stdout.log')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def obj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def need(x,m):
    if not x:raise AssertionError(m)
def emit(v):
    s=json.dumps(v,ensure_ascii=False,allow_nan=False);print(s,flush=True)

start=time.perf_counter();error=None;value={};save(DEST/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0))
(DEST/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
try:
    oldargv=sys.argv[:];sys.argv=[str(OUT/'review/round109_independent_raw.py'),'--root',str(ROOT),'--mode','final','--out',str(DEST),'--dll','D:/gurobi1302/win64/bin/gurobi130.dll']
    core=runpy.run_path(str(OUT/'review/round109_independent_raw.py'));sys.argv=oldargv
    core['DEST']=DEST
    identity=obj(OUT/'campaign/identity.json');launches=identity['launches'][12:15]
    need([(x['number'],x['id'],x['arm'],x['seed']) for x in launches]==[(13,'G50-C1','M-B',0),(14,'G50-C1','ENS-C',0),(15,'G50-C1','P-GRB',0)],'three exact frozen affected actual launches')
    arms=[]
    for launch in launches:
        a,_,_=core['audit_arm'](launch,identity,launch['number']!=15);arms.append(a);core['cache'].clear()
    mb,ens,plain=arms;plain['complete_seconds']=None
    q=core['input_file'](ROOT/launches[0]['panel']['input_path']);p=launches[0]['panel']
    need(ens['physical']['U']==ens['physical']['G']==ens['physical']['P']==0 and ens['physical']['final_inventories'][1:]==q['target'][1:],'all50 target stocks reached by own complete physical integer fleet')
    need(p['lambda']>=0 and all(w>=0 for w in q['weights'][1:]),'original true-G and penalty globally nonnegative')
    fleet,mapping=core['normalize_existing_start_routes'](q,ens['physical']['full_routes']);ph=core['full_physics'](q,fleet,p)
    need(ph['U']==0 and ph['final_inventories']==ens['physical']['final_inventories'],'pure equalQ relabeling leaves original physical zero witness unchanged')
    cold=Path(launches[2]['destination'])/'compact.lp';reference=OUT/'qualification/reference/G50-C1/original.lp';build=obj(reference.parent/'build.json')
    need(sha(cold)==sha(reference)==build['canonical_sha256'],'actual cold P bytes exactly frozen original reference')
    m=core['model'](cold);domain=core['domain_contract'](m,q,'P-GRB');families=Counter(n.split('_',1)[0] for n in m['bounds'])
    value['cold_column_families']=dict(families)
    vals={n:0. for n in m['bounds']};known=set()
    for route in fleet:
        k=route['vehicle'];nodes=route['nodes'];ops={o['station']:o for o in route['operations']};load=0
        for position,(i,j) in enumerate(zip(nodes,nodes[1:]),1):
            for n,v in ((f'x_{k}_{i}_{j}',1.),(f'conn_{k}_{i}_{j}',float(len(nodes)-1-position))):
                if n.startswith('conn_') and n not in vals:continue # Original cold uses its retained order rows, not extra connectivity flow columns.
                need(n in vals,'complete existing route family column '+n);vals[n]=v
        for position,i in enumerate(nodes[1:-1],1):
            o=ops[i];load+=o['pickup']-o['drop']
            for n,v in {f'p_{k}_{i}':o['pickup'],f'd_{k}_{i}':o['drop'],f'z_{k}_{i}':1.,f'mode_{k}_{i}':float(o['pickup']>0),f'load_{k}_{i}':load,f'ord_{k}_{i}':position}.items():need(n in vals,'complete original operation family '+n);vals[n]=float(v)
    for n in vals:
        f=n.split('_',1)[0]
        if f in {'x','conn','p','d','z','mode','load','ord'}:pass
        elif n=='G':vals[n]=0.
        elif n in ('r_min','r_max'):vals[n]=1.
        elif n=='W_SP':vals[n]=0.
        elif re.fullmatch(r'Y_\d+',n):vals[n]=float(ph['final_inventories'][int(n.split('_')[1])])
        elif re.fullmatch(r'r_\d+',n):vals[n]=1.
        elif re.fullmatch(r'e_\d+',n):vals[n]=0.
        elif re.fullmatch(r'h_\d+_\d+',n):vals[n]=0.
        elif re.fullmatch(r'state_\d+_\d+',n):_,i,y=n.split('_');vals[n]=float(ph['final_inventories'][int(i)]==int(y))
        elif re.fullmatch(r'state_g_\d+_\d+',n):vals[n]=0.
        elif re.fullmatch(r'bit_\d+_\d+',n):_,i,b=n.split('_');vals[n]=float((ph['final_inventories'][int(i)]>>int(b))&1)
        elif re.fullmatch(r'(prod_\d+_\d+|zprod_\d+)',n):vals[n]=0.
        else:raise AssertionError('unsupported cold diagnostic semantic column '+n)
    need(all(low-1e-12<=vals[n]<=hi+1e-12 and (m['types'][n]=='C' or vals[n].is_integer()) for n,(low,hi) in m['bounds'].items()),'all actual cold column types and finite bounds checked')
    core['validate_start_fleet_vector'](vals,q,fleet,ph)
    numeric=[]
    for index,(sense,rhs,terms) in enumerate(m['rows'],1):
        lhs=sum(vals[n]*a for n,a in terms);v=abs(lhs-rhs) if sense=='=' else max(0.,lhs-rhs) if sense=='<' else max(0.,rhs-lhs)
        numeric.append((v,index))
    numeric.sort(reverse=True);objective=sum(vals[n]*a for n,a in m['objective'].items())
    need(objective==0 and numeric[0][0]<1e-7,'same own zero fleet fits every actual cold numeric row strictly below unchanged closure tolerance')
    with (DEST/'cold_zero_diagnostic.values.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['variable','type','value']);writer.writerows((n,m['types'][n],repr(vals[n])) for n in sorted(vals))
    # Exact rational audit of the native binary64 coefficient matrix. The
    # physical ratios are exact1; stored reciprocal equalities introduce only
    # representational roundoff. Adjust continuous auxiliaries analytically,
    # not with an optimizer, and choose G=1e-12 with ample epigraph margin.
    exact={n:Fraction(v) for n,v in vals.items()};g=Fraction(1,10**12);exact['G']=g;ratios={}
    for i in range(1,q['V']+1):
        rn=f'r_{i}';yn=f'Y_{i}'
        rr=[(rhs,dict(t)) for sense,rhs,t in m['rows'] if sense=='=' and len(t)==2 and {n for n,a in t}=={rn,yn}]
        need(len(rr)==1,'unique actual stored reciprocal ratio equality '+rn)
        rhs,terms=rr[0];ratios[i]=(Fraction(rhs)-Fraction(terms[yn])*exact[yn])/Fraction(terms[rn]);exact[rn]=ratios[i];exact[f'e_{i}']=abs(ratios[i]-1)
    if 'r_min' in exact:exact['r_min']=min(ratios.values())
    if 'r_max' in exact:exact['r_max']=max(ratios.values())
    for n in exact:
        if re.fullmatch(r'h_\d+_\d+',n):_,i,j=n.split('_');exact[n]=abs(ratios[int(i)]-ratios[int(j)])
        elif re.fullmatch(r'state_g_\d+_\d+',n):_,_,i,y=n.split('_');exact[n]=g*Fraction(int(ph['final_inventories'][int(i)]==int(y)))
        elif re.fullmatch(r'prod_\d+_\d+',n):_,i,b=n.split('_');exact[n]=g*((ph['final_inventories'][int(i)]>>int(b))&1)
        elif re.fullmatch(r'zprod_\d+',n):exact[n]=g*ph['final_inventories'][int(n.split('_')[1])]
    exact_bad=[]
    for index,(sense,rhs,terms) in enumerate(m['rows'],1):
        lhs=sum((exact[n]*Fraction(a) for n,a in terms),Fraction(0));r=Fraction(rhs)
        v=abs(lhs-r) if sense=='=' else max(Fraction(0),lhs-r) if sense=='<' else max(Fraction(0),r-lhs)
        if v:exact_bad.append(dict(row=index,sense=sense,violation_numerator=v.numerator,violation_denominator=v.denominator,violation_float=float(v)))
    exact_bounds=[n for n,(lo,hi) in m['bounds'].items() if math.isfinite(lo) and exact[n]<Fraction(lo) or math.isfinite(hi) and exact[n]>Fraction(hi)]
    exact_objective=sum((exact[n]*Fraction(a) for n,a in m['objective'].items()),Fraction(0))
    save(DEST/'exact_binary64_matrix_witness.json',dict(complete_column_values={n:[v.numerator,v.denominator] for n,v in exact.items()},row_count=len(m['rows']),violated_rows=exact_bad,bound_violations=exact_bounds,objective=[exact_objective.numerator,exact_objective.denominator],objective_float=float(exact_objective),submitted_to_native=False,optimizer_calls=0))
    need(not exact_bad and not exact_bounds and exact_objective<Fraction(1,10**7),'analytical rational complete cold model feasible vector proves native positive bound impossible beyond closure tolerance')
    observations=obj(Path(launches[2]['destination'])/'observations.json');call=[r['payload'] for r in observations if r['payload']['kind']=='call'];bounds=[r['payload'] for r in observations if r['payload']['kind']=='bound']
    need(len(call)==1 and call[0]['full_original']==call[0]['native_preconditions']==1 and call[0]['model_sha256']==sha(cold),'single actual complete-original cold native bound scope')
    positive=[e for e in bounds if e['native_bound']>1e-7];need([e['sequence'] for e in positive]==[52,53] and all(e['global_available']==1 and e['global_bound']==e['native_bound'] for e in positive),'original positively contradictory committed native bounds preserved')
    fee=obj(OUT/'fees/main05/receipt.json');timing=[obj(Path(l['destination'])/'whole_arm_receipt.json') for l in launches[:2]];comp=obj(Path(launches[2]['destination'])/'completion.json')
    need(fee['exit_code']==1 and fee['actual_native_children_with_launch']==3 and fee['conservative_process_starts']==4,'all3 actual native children paid once in failed main05 wrapper')
    lower=comp['fully_observed_end_to_end_seconds'];upper=fee['outer_seconds']-sum(t['complete_seconds'] for t in timing)
    need(lower<=upper<=1800 and not (Path(launches[2]['destination'])/'whole_arm_receipt.json').exists(),'honest supervisor lower and enclosing outer-minus-prior upper bound within original cap')
    pair_results=[]
    d=runpy.run_path(str(OUT/'review/round109_independent_decision.py'))
    for second in [lower,upper]:
        pc=copy.deepcopy(plain);pc.update(L=0.,gap=pc['U'],complete_seconds=second,certificate=False,numbers_qualified=True,certificate_qualified=True)
        pair_results.append(dict(P_complete_seconds_sensitivity_endpoint=second,MB_P=d['pair'](mb,pc),MB_ENS=d['pair'](mb,ens),ENS_P=d['pair'](ens,pc)))
    need(all(v['MB_P']['classification']=='WIN' and v['MB_ENS']['classification']=='LOSS' and v['MB_ENS']['severe_regression'] and v['ENS_P']['classification']=='WIN' for v in pair_results),'allthree frozen pair classes invariant over entire P timing interval and separately proved floor0')
    value=dict(decision='ACCEPT_DIAGNOSIS',actual_issue='genuine native floating-numerical lower-bound contradiction; not an input/type/scope/Seed/reader reconstruction error',raw_native_L=plain['L'],same_input_exact_original_physical_optimum=0.,cold_exact_binary64_feasible_objective_upper=float(exact_objective),raw_positive_native_bound_sequences=[e['sequence'] for e in positive],mathematical_zero_floor_available_from_own_original_objective=True,
        raw_values_flags_and_files_unchanged=True,independent_arms=arms,physical_zero_certificate=ens['physical'],cold_model=dict(SHA=sha(cold),domain=domain,families=dict(families),columns=len(vals),rows=len(m['rows']),zero_float_objective=objective,maximum_numeric_row_violation=numeric[0][0],worst_numeric_rows=numeric[:10],equal_capacity_normalization=mapping,exact_binary64_witness_file='exact_binary64_matrix_witness.json',exact_binary64_witness_SHA=sha(DEST/'exact_binary64_matrix_witness.json')),
        P_complete_timing=dict(exact_seconds=None,lower=lower,upper=upper,basis='legacy full-supervisor observed lower; enclosing actual wrapper outer minus prior two disjoint complete-arm intervals upper',native_first_find_exact=False),hypothetical_floor_pair_sensitivity=pair_results,
        recovery_contract='pending independent explicit disqualification policy/source/admission; no automatic resume',prohibited_repairs=['weakening1e-7 closure tolerance','clipping or relabeling native bound as valid','importing ENS route/U/certificate into P','retrofitting exact full arm time','changing production/search/argv or rerunning'],raw_read_bindings=core['reads'],Optimize=0,native_environment=0,production_edits=0)
    emit(dict(decision=value['decision'],issue=value['actual_issue'],exact_cold_feasible_objective=float(exact_objective),numeric_max_violation=numeric[0][0],P_time_interval=[lower,upper]))
except Exception:
    error=traceback.format_exc();value.update(decision='HOLD',error=error);print(error,file=sys.stderr,flush=True)
(DEST/'stderr.log').write_text(error or '',encoding='utf-8');save(DEST/'audit.json',value);save(DEST/'receipt.json',dict(exit_code=int(error is not None),elapsed_engineering_seconds=time.perf_counter()-start,source_SHA=sha(__file__),audit_SHA=sha(DEST/'audit.json'),stdout_SHA=sha(DEST/'stdout.log') if (DEST/'stdout.log').exists() else None,stderr_SHA=sha(DEST/'stderr.log'),Optimize=0,native_environment=0))
if error:sys.exit(1)
