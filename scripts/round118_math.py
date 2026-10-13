"""Exact-rational offline scale analysis; no native bound or inventory oracle."""
from fractions import Fraction as F
import itertools,json,sys,time
from round118_data import ROOT,OUT,REF,read,write,sha

def greedy(D,B,a):
    s=sum(D)-B;assert s>0 and B>=0 and all(d>0 for d in D) and all(x>0 for x in a)
    u=[0]*len(D);remaining=s
    for i in sorted(range(len(D)),key=lambda i:(a[i],i)):
        u[i]=min(D[i],remaining);remaining-=u[i]
    assert remaining==0
    return sum((x*y for x,y in zip(a,u)),F(0)),u

def enumerations():
    cases=[]
    for D,C,B,w in [([2,3],[3,4],3,['.2','1']),([1,3],[2,3],0,['1','.1']),
        ([2,1,3],[3,2,4],4,['.25','.5','1']),([1,2,2],[1,3,3],3,['.5','1','1'])]:
        for kind in ['input_decimal','parsed_binary64']:
            lam=F('.15') if kind=='input_decimal' else F.from_float(.15)
            weights=[F(x) if kind=='input_decimal' else F.from_float(float(x)) for x in w]
            a=[lam*x/d for x,d in zip(weights,D)];L,u=greedy(D,B,a)
            Ys=[Y for Y in itertools.product(*(range(c+1) for c in C)) if sum(Y)<=B]
            exact=min(sum((x*abs(y-d) for x,y,d in zip(a,Y,D)),F(0)) for Y in Ys)
            assert exact==L and sum(D)-B==sum(u) and L>=min(a)*(sum(D)-B)>0
            cases.append(dict(D=D,C=C,B=B,coefficient_interpretation=kind,enumerated_vectors=len(Ys),
                exact_minimum=str(exact),greedy_minimum=str(L),allocation=u,passed=True))
    return cases

def analyze():
    tick=time.perf_counter();p=read(OUT/'input_manifest.json')['roles'][0]
    landscape=read(ROOT/p['landscape_path']);D=landscape['target'];b=landscape['initial'];C=landscape['capacities'];weights=landscape['weights']
    assert all(0<d<=c and 0<=x<=c for d,x,c in zip(D,b,C)) and all(w>0 for w in weights)
    B=sum(b);s=sum(D)-B;assert s>0;analyses=[]
    for kind in ['input_decimal','parsed_binary64_values_as_exact_rationals','binary64_computed_a']:
        lam=F('.15') if kind=='input_decimal' else F.from_float(.15)
        w=[F(f'{x:.6f}') if kind=='input_decimal' else F.from_float(x) for x in weights]
        a=[lam*x/d for x,d in zip(w,D)]
        if kind=='binary64_computed_a':a=[F.from_float(.15*x/d) for x,d in zip(weights,D)]
        delta=min(a);L,u=greedy(D,B,a);ratios=[F(x,d) for x,d in zip(b,D)];S=sum(ratios,F(0))
        G=sum((abs(x-y) for i,x in enumerate(ratios) for y in ratios[i+1:]),F(0))/(len(D)*S) if S else F(0)
        penalty=sum((x*abs(y-d) for x,y,d in zip(a,b,D)),F(0))
        analyses.append(dict(coefficient_interpretation=kind,a=[str(x) for x in a],delta=str(delta),delta_times_s=str(delta*s),
            delta_times_s_float=float(delta*s),L_pen=str(L),L_pen_float=float(L),allocation_u=u,
            minimizing_relaxed_Y=[d-x for d,x in zip(D,u)],W=str(sum(w,F(0))),W_float=float(sum(w,F(0))),
            lambda_W=str(lam*sum(w,F(0))),lambda_W_float=float(lam*sum(w,F(0))),
            initial_no_service_G=str(G),initial_no_service_G_float=float(G),initial_penalty=str(penalty),
            initial_penalty_float=float(penalty),initial_F_float=float(G+penalty)))
    write(OUT/'positive_objective_analysis.json',dict(input_SHA=p['input_sha256'],stock_B=B,Dsum=sum(D),shortage_s=s,
        Delta_stock=landscape['generation_trace']['delta_amount'],clipping_boundary_applied=B==0,
        B_lo=max(0,B-sum(p['Q_vector'])),B_hi=B,K_initial=sum(abs(x-d) for x,d in zip(b,D)),
        service_stations_only=True,depot_excluded=True,positive_target_capacity_weight_premises=True,analyses=analyses,
        finite_rational_enumerations=enumerations(),formal_input_algorithm='O(V log V) bulk greedy; no inventory/route enumeration',
        injected_into_H_model_Start_cutoff_online_bound_or_formal_LB=False,not_original_problem_optimum=True,
        native_starts=0,Optimize=0,engineering_seconds=time.perf_counter()-tick))
    text='''# Why this one original problem has strictly positive optimum

For service stations 1..V only, Y_i=b_i+sum_k(d_ki-p_ki), r_i=Y_i/D_i and F=G_true+lambda sum_i w_i|r_i-1|. G_true is the Gini of inventory-to-target ratios, sum_{i<j}|r_i-r_j|/(V sum r_i), with the inherited zero-denominator convention G=0. The penalty is two-sided relative target deviation, not just shortage or observed rental/return failures. min_ratio adds no inventory floor.

Vehicles start empty. Every station admits at most one vehicle and one nonzero one-way integer service. Prefix and return loads lie in [0,Q_k]; loaded return is legal and depot unloading is paid. Complete duration is travel+(pickup_seconds+drop_seconds)*total pickups. Q bounds simultaneous load, not cumulative pickups.

Let B=sum_i b_i. With nonnegative return loads L_k, sum_i Y_i+sum_k L_k=B. Therefore max(0,B-sum_k Q_k)<=sum_i Y_i<=B. Station stock need not be conserved; returned load completes whole-system conservation. Positive integer targets satisfy D_i<=C_i and all weights/lambda are positive. Put a_i=lambda*w_i/D_i, delta=min_i a_i and s=sum_i D_i-B>0. Then K=sum_i|Y_i-D_i|>=sum_i(D_i-Y_i)>=s, and F>=delta*K>=delta*s>0. An empty no-service fleet remains feasible. Unattainable complete target stock does not make the original problem infeasible.

An optional offline penalty relaxation minimizes sum_i a_i u_i with integer 0<=u_i<=D_i and sum_i u_i=s. Ignoring routes, a minimizing inventory can have sum Y=B and 0<=Y<=D: when a station exceeds D, transfer a unit to an under-target station and strictly decrease penalty; when total is below B, add a unit at an under-target station and decrease penalty. A receiving station always exists because B<sum D; D<=C preserves capacities, and strictly positive coefficients supply the strict decrease. Thus deficits of total s can be filled in ascending (a_i, station index), using capacities D_i in bulk. This yields L_pen, the exact optimum of that penalty relaxation, and original F>=L_pen>=delta*s. It is not the route-plus-fairness optimum, new theory, or an algorithm performance result.

`positive_objective_analysis.json` separates exact input-decimal coefficients, exact rationals of parsed binary64 lambda/weights, and rounded binary64 computed a_i. Small n=2/3 rational enumerations compare the greedy relaxation to every capacity-bounded inventory vector with total<=B. The V40 calculation is O(V log V), with no inventory or route enumeration. W, lambda*W, K, and the no-service G/penalty distinction are disclosed. Fixed lambda and max-normalized weights do not hold the aggregate penalty tradeoff constant across V.

This analysis is never injected into H, a model, Start, cutoff, online bound, official LB, or certification. Only existing sealed native evidence and the inherited nonnegative floor0 determine experimental bounds. Rational arithmetic here does not upgrade native floating-point certificates.
'''
    (OUT/'positive_objective_proof.md').write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps(dict(B=B,Dsum=sum(D),shortage=s,delta_s=analyses[0]['delta_times_s_float'],L_pen=analyses[0]['L_pen_float'],Optimize=0)))

if __name__=='__main__':analyze()
