"""Finite read-only pre-study mathematics and prior proof obligations; no Optimize."""
from round123_common import *
from fractions import Fraction as F
import ast, collections, copy, csv, math, re
import round108_reader as core

OLD=WORK/'worktrees/round122'
PRIOR=OLD/'results/unified_exact_round122'

def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def positive():
    p=ROOT/'reference/round122_paper_benchmark/PB-C50-S.txt'; text=p.read_text()
    def tokens(n):return re.search(r'^'+n+r'\s*=\s*\[([^\n]*)\]',text,re.M)[1].split(',')
    b=list(map(int,tokens('initial')))[1:]; D=list(map(int,tokens('target')))[1:]
    C=list(map(int,tokens('capacities')))[1:]; w=[F(t.strip()) for t in tokens('weights')[1:]]
    assert sum(b)==495 and sum(D)==562 and all(0<d<=c for d,c in zip(D,C)) and all(x>0 for x in w)
    deficit=sum(D)-sum(b); lam=F(3,20)
    def fill(cost):
        left=deficit; alloc=[0]*len(D)
        for i in sorted(range(len(D)),key=lambda i:(cost[i],i)):
            alloc[i]=min(D[i],left); left-=alloc[i]
        assert left==0 and sum(alloc)==67
        return alloc,sum(c*u for c,u in zip(cost,alloc))
    c=[lam*x/d for x,d in zip(w,D)]; delta=min(c); alloc,pen=fill(c)
    bc=[F.from_float(.15)*F.from_float(float(x))/d for x,d in zip(w,D)]
    balloc,bpen=fill(bc); bdelta=min(bc)
    assert delta==F(592593,160000000) and 67*delta==F('0.24814831875') and pen==F('0.26064825')
    # Independent dynamic program on the 67-deficit relaxation, exact rationals.
    dp=[F(0)]+[None]*67
    for cost,capacity in zip(c,D):
        nd=[None]*68
        for total in range(68):
            vals=[dp[total-u]+u*cost for u in range(min(capacity,total)+1) if dp[total-u] is not None]
            nd[total]=min(vals) if vals else None
        dp=nd
    assert dp[67]==pen
    # Finite counterexamples protect necessary assumptions, not a full LP proof.
    assert sum([2,2])>sum([1,1]) # loaded departure/supply would destroy the conservation premise
    value=dict(input_SHA=sha(p),service_B=495,service_Dsum=562,shortage=67,total_Q=120,
        all_target_capacities_valid=True,all_weights_strictly_positive=True,
        decimal=dict(delta=str(delta),simple_bound=str(67*delta),simple_float=float(67*delta),
            L_pen=str(pen),L_pen_float=float(pen),deficit_allocation=alloc,exact_DP_equal_greedy=True),
        parsed_binary64_as_exact_real_inputs=dict(delta=str(bdelta),simple_bound=str(67*bdelta),
            simple_float=float(67*bdelta),L_pen=str(bpen),L_pen_float=float(bpen),deficit_allocation=balloc,
            difference_L_pen_from_decimal=str(bpen-pen),difference_simple_from_decimal=str(67*(bdelta-delta))),
        direct_binary64_greedy_sum=sum((.15*float(x)/d)*u for x,d,u in zip(w,D,balloc)),
        not_a_new_production_lower_bound=True,no_bound_injected_or_R122_endpoint_replaced=True,
        interpretation='Strict positivity of the exact objective with these parsed inputs, independent of floating arithmetic evaluation errors; solver certificates remain numerical.')
    write(OUT/'mathematics/positive_objective.json',value)
    return value

def redundant():
    findings=[]
    for group,ordinal,role in [(3,2,'PB-C35-U'),(4,1,'PB-B35-B')]:
        d=PRIOR/f'campaign/group{group:02d}/raw/{ordinal:02d}_{role}_S0_MB-D1'
        pair=read(d/'external/round120_root_pair.json')
        paths=list((d/'external/models').glob('*_round120_d1.lp')); assert len(paths)==1
        p=paths[0]; meta=read(str(p)+'.round120.json')
        nr=list((d/'external/native_logs').glob('*.round120.native.json')); assert len(nr)==1
        native=read(nr[0]); assert sha(p)==meta['SHA']==native['model_SHA']
        model=core.lp_model(p); objective,constant=model['objective']; obj=dict(objective)
        assert constant==meta['objective_constant']==native['objective_constant']==0
        assert obj.pop('G')==1 and all(n.startswith('e_') and v>0 and model['bounds'][n][0]>=0 for n,v in obj.items())
        text=p.read_text(); named={line.strip().split(':',1)[0]:line.strip().split(':',1)[1].strip()
            for line in text.splitlines() if line.strip().startswith(('r120_g_lower:','r120_g_upper:','r120_f_lower:'))}
        assert len(named)==3
        A,D,B,E=[F(meta[k]) for k in ['lower_base','lower_delta','objective_base','objective_delta']]
        assert named['r120_g_lower']==f'G - {meta["lower_delta"]} r120_h >= {meta["lower_base"]}'
        # Verify complete added f row against the entire saved objective, independently.
        fr=next(r for r in model['rows'] if dict(r[0]).get('r120_h')==-float(meta['objective_delta']) and 'e_1' in dict(r[0]) and r[1]=='>=')
        terms=dict(fr[0]); assert terms.pop('r120_h')==-float(meta['objective_delta'])
        assert terms==dict(objective) and fr[2]==float(meta['objective_base'])
        decimal_slacks=[A-B,A+D-B-E]; assert min(decimal_slacks)>=0
        nA,nD,nB,nE=[F.from_float(native[k]) for k in ['lower_base','lower_delta','objective_base','objective_delta']]
        binary_slacks=[nA-nB,nA+nD-nB-nE]; assert min(binary_slacks)>=0
        assert pair['beta0']<=pair['a'] and pair['beta1']<=pair['m']
        samples=[]
        for h in map(F,[0,F(1,10),F(1,3),F(1,2),F(9,10),1]):
            assert A+D*h>=B+E*h and nA+nD*h>=nB+nE*h
            samples.append(dict(h=str(h),decimal_slack=str(A+D*h-B-E*h)))
        target=OUT/'mathematics/d1_saved_models'/role; target.mkdir(parents=True,exist_ok=False)
        for src in [p,Path(str(p)+'.round120.json'),nr[0],d/'external/round120_root_pair.json']:
            shutil.copyfile(src,target/src.name)
        findings.append(dict(role=role,model_SHA=sha(p),rows=len(model['rows']),columns=len(model['order']),
            source_paths=[str(p),str(nr[0])],actual_ObjCon=constant,full_objective_nonnegative_penalty_verified=True,
            e_nonnegative_bound_count=len(obj),a=pair['a'],m=pair['m'],b=pair['b'],beta0=pair['beta0'],beta1=pair['beta1'],
            actual_decimal=dict(A=str(A),D=str(D),B=str(B),E=str(E),endpoint_slacks=list(map(str,decimal_slacks))),
            saved_native_binary64=dict(A=str(nA),D=str(nD),B=str(nB),E=str(nE),endpoint_slacks=list(map(str,binary_slacks))),
            samples=samples,original_variable_projection_equal=True,conditional_row_redundant_over_entire_D0_continuous_extension=True,
            support_level='Full saved LP bytes parsed now and exact arithmetic on original production API readback; no new native load/LP Optimize.',
            no_internal_search_or_time_invariance_claim=True))
    # Independent finite family covers both sides, midpoint, unequal and reversed beta.
    tests=0
    for a,m,b in [(F(0),F(1,3),F(1)),(F(1,10),F(2,5),F(7,10))]:
        for beta0 in [F(0),a]:
            for beta1 in [F(0),m-F(1,1000),m]:
                for g in [a,(a+m)/2,m,(m+b)/2,b]:
                    h=F(0) if g<=m else F(1)
                    assert a+(m-a)*h<=g<=m+(b-m)*h
                    assert g>=beta0+(beta1-beta0)*h
                    tests+=1
    # Dropping a premise invalidates the implication: not a universal D1 redundancy result.
    assert F(0)<F(1,10) # beta0>a=0 can cut f=g=0
    assert F(1,4)-F(1,5)<F(1,10) # negative penalty could invalidate f>=g
    value=dict(roles=findings,exact_finite_extension_cases=tests,Optimize=0,new_native_starts=0,
        universal_proof_in_paper='Affine endpoint nonnegativity on h in [0,1], f>=g from nonnegative e/objective coefficients.',
        R120_original_extended_space_nonredundancy_not_revoked=True,no_new_D1_candidate=True)
    write(OUT/'mathematics/d1_redundancy.json',value); return value

def obligations():
    records=[]; sources={}
    for group in [5,8]:
        i=read(PRIOR/f'campaign/group{group:02d}/identity.json')
        for l in i['launches']:
            d=Path(l['destination']); obs=read(d/'observations.json'); r=read(d/'result.json')
            p=l['panel']; fleet=core.full_fleet(OLD,p,r)
            witnesses=[]
            for row in obs:
                if row['payload']['kind']=='witness':
                    w=core.full_fleet(OLD,p,row['payload'])
                    witnesses.append(dict(sequence=row['sequence'],available_seconds=row['effective_available_seconds'],
                        data_close_seconds=row['data_close_seconds'],F=w['F'],G=w['G'],source=row['payload']['source']))
            first=min(witnesses,key=lambda x:x['available_seconds']) if witnesses else None
            events=rows(d/'external/paper_tree_events.csv') if l['arm']!='P-GRB' else []
            leaves=rows(d/'external/paper_leaf_ledger.csv') if l['arm']!='P-GRB' else []
            active=[v for v in leaves if v['status'] not in ['replaced']]
            live=[v for v in active if v['status'] not in ['empty','closed']]
            controlling=min(live,key=lambda v:float(v['lower_bound'])) if live else None
            if controlling: assert abs(float(controlling['lower_bound'])-r['lower_bound'])<=1e-7
            calls=[row for row in obs if row['payload']['kind']=='call']
            compat=[dict(call=row['payload']['call'],full_original=row['payload']['full_original'],
                interval=[row['payload']['lower_g'],row['payload']['upper_g']],cutoff=row['payload']['cutoff'],
                final_fleet_G=fleet['G'],final_fleet_F=fleet['F'],
                exact_g_embedding_interval_compatible=row['payload']['lower_g']-1e-7<=fleet['G']<=row['payload']['upper_g']+1e-7,
                cutoff_compatible=fleet['F']<=row['payload']['cutoff']+1e-7 if not row['payload']['full_original'] else True)
                for row in calls]
            files=['result.json','observations.json','producer_receipt.json']
            if events: files+=['external/paper_tree_events.csv','external/paper_leaf_ledger.csv','external/global_bound_trace.csv','external/paper_optimize_ledger.csv']
            for fn in files:sources[(d/fn).relative_to(OLD).as_posix()]=sha(d/fn)
            records.append(dict(group=group,seed=l['seed'],arm=l['arm'],U=fleet['F'],G=fleet['G'],L=r['lower_bound'],
                first_available_witness=first,best_observed=min(witnesses,key=lambda x:x['F']) if witnesses else None,
                actual_later_strict_witness_improvements=[v for k,v in enumerate(witnesses) if k and v['F']<min(w['F'] for w in witnesses[:k])-1e-12],
                atomic_splits=[v for v in events if v['event']=='atomic_split'],leaves=leaves,active_cover=active,
                controlling_leaf=controlling,complete_call_interval_compatibility=compat,
                T_produce=read(d/'producer_receipt.json')['T_produce'],source_directory=d.relative_to(OLD).as_posix()))
    write(OUT/'prior_proof_obligations.json',dict(source_commit=BASE,source_files_SHA=sources,records=records,
        source_reconstruction_not_a_new_R122_native_reproduction=True,Optimize=0))
    lines=['# Prior PB-C50-S proof obligations (finite read-only reconstruction)','',
        'The R122 Seed0 and Seed1 runs remain separate. Available journal times below are upper bounds on when an observation was usable, not an invented internal discovery time. The known own F=0.3723417754990474 is feasible; its optimality is unknown. No prior route, cutoff, bound, basis, tree or cache is an input to Round123.','',
        '| Seed | Method | First available F / G / time | Final U | Final L | Final controlling leaf |','|---:|---|---|---:|---:|---|']
    for q in records:
        f=q['first_available_witness']; first=f'{f["F"]:.15g} / {f["G"]:.15g} / {f["available_seconds"]:.9f}s' if f else 'unknown'
        leaf=q['controlling_leaf']['leaf_id'] if q['controlling_leaf'] else 'complete original compact model'
        lines.append(f'| {q["seed"]} | {q["arm"]} | {first} | {q["U"]:.16g} | {q["L"]:.16g} | {leaf} |')
    lines+=['','For all integrated Seed0/Seed1 runs the three original atomic splits have the recorded reasons shown in the JSON: the first two retain infeasible right halves as closed improvement regions; the third follows the original AM score. The final improving-domain cover contains two open depth-3 leaves [0,0.046542721937380925] and [0.046542721937380925,0.09308544387476185], the two closed right ancestors, and the analytic cutoff complement. Closed means exclusion of a strict improver under the recorded cutoff, not physical infeasibility of the unrestricted original problem. Replaced ancestors are not additional covering cells.','',
        'The global lower endpoint is the minimum of the valid cover and cutoff complement. It is supplied by L0.0.0.0, not by the larger sibling bound. In particular the final own G=0.050119584194518584 lies in L0.0.0.1 and outside the target MIP leaf L0.0.0.0. Absence of an exact-g Start for that target is therefore compatible with a valid global incumbent. The JSON checks every recorded call interval and cutoff against each own final fleet; it does not claim a free mapping into an incompatible leaf.','',
        'The journal gives directly replayable fleet/observation availability. Internal first-discovery times, native acceptance of each candidate and the complete internal reason for continued proof effort are not reconstructed where no record exists. The same final objective across runs does not prove optimality. Group08 P keeps its original final U, clocks and recovery waiting; the historical smaller legal witness remains a trajectory fact. No new root/terminal Optimize, fixed-U diagnostic or new lower bound was computed.']
    (OUT/'prior_proof_obligations.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return records

if __name__=='__main__':
    workspace(); tick=time.perf_counter(); positive(); redundant(); values=obligations()
    write(OUT/'mathematics/prestudy_receipt.json',dict(Optimize=0,new_native_starts=0,
        measured_seconds=time.perf_counter()-tick,prior_runs=len(values),script_SHA=sha(__file__),UTC=utc()))
    print('Exact positive-objective and actual D1 coefficient checks; eight finite prior run reconstructions complete')
