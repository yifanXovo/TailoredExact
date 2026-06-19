"""
Prototype Gini-frontier route-load branch-price-and-cut components for the
Equity-aware BRP.  The implementation focuses on exact column-generation
pricing for fixed Gini-cap subproblems.  It uses only scipy.optimize.linprog
and scipy.optimize.milp, so it is portable in the current environment.

Important: the root column-generation certificate is exact for the LP
relaxation of the route-load column master if pricing terminates with no
negative reduced-cost column.  The optional final MILP is exact only with
respect to the generated column pool unless the branch-price tree is fully
explored.  This file is intended as a research prototype rather than a
production CPLEX/SCIP callback implementation.
"""
from __future__ import annotations
import ast, heapq, json, math, os, re, time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set, Any
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack


def parse_instance(path: str) -> Dict[str, Any]:
    text=open(path).read(); lines=text.splitlines()
    m=re.match(r'(\d+)\s+(\d+)\s+\[(.*)\]', lines[0].strip())
    V=int(m.group(1)); M=int(m.group(2)); Qs=[int(x) for x in re.findall(r'\d+',m.group(3))]
    data={'path':path,'name':os.path.basename(path),'V':V,'M':M,'Q':Qs}
    for key in ['capacities','initial','target','weights','min_ratio']:
        mm=re.search(key+r'\s*=\s*(\[[^\n]+\])', text)
        if mm: data[key]=ast.literal_eval(mm.group(1))
    mat=[]; inmat=False
    for line in lines:
        if line.strip().startswith('distances'):
            inmat=True; continue
        if inmat:
            if line.strip().startswith(']'): break
            nums=[float(x) for x in re.findall(r'[-+]?\d+\.\d+', line)]
            if nums: mat.append(nums)
    data['distances']=mat
    return data


def eval_y(ins: Dict[str, Any], yv: List[int], lam: float=0.15) -> Tuple[float,float,float,float,float]:
    V=ins['V']; target=ins['target']; w=ins['weights']
    rr=[yv[i-1]/target[i] for i in range(1,V+1)]
    S=sum(rr)
    H=sum(abs(rr[i]-rr[j]) for i in range(V) for j in range(i+1,V))
    G=H/(V*S) if S>0 else 0.0
    P=sum(w[i]*abs(rr[i-1]-1.0) for i in range(1,V+1))
    return G,P,G+lam*P,S,H


@dataclass(frozen=True)
class Column:
    path: Tuple[int, ...]
    q: Tuple[int, ...]       # length V; q_i = pickup - drop at station i+1
    delta: Tuple[int, ...]   # final inventory change = -q
    visitmask: int
    pickup: int
    travel: float
    time: float
    signature: Tuple[Tuple[int,...], Tuple[int,...]]


def make_col(path: Tuple[int,...], qtuple: Tuple[int,...], ins: Dict[str,Any], taup=60, taud=60) -> Column:
    V=ins['V']; dist=ins['distances']; cunit=taup+taud
    tr=0.0; prev=0; mask=0; pick=0
    for node in path:
        tr += dist[prev][node]
        mask |= 1<<(node-1)
        qi=qtuple[node-1]
        if qi>0: pick += qi
        prev=node
    if path:
        tr += dist[prev][0]
    delta=tuple(-x for x in qtuple)
    return Column(path=path,q=qtuple,delta=delta,visitmask=mask,pickup=pick,travel=tr,time=tr+cunit*pick,signature=(path,qtuple))


def simple_seed_columns(ins: Dict[str,Any], T=3600, taup=60, taud=60, max_pair_q: Optional[int]=None) -> List[Column]:
    """Generate a generic initial pool: all feasible one-stop pickup columns,
    one pickup/drop pair columns, and a few nearest-neighbor 3-stop columns.
    This is not sample-specific; it only seeds RMP feasibility and CG stability.
    """
    V=ins['V']; Q=max(ins['Q']); Y0=ins['initial']; C=ins['capacities']; dist=ins['distances']; cunit=taup+taud
    cols=[]; seen=set()
    def add(path, qlist):
        col=make_col(tuple(path), tuple(qlist), ins, taup, taud)
        if col.time <= T+1e-9 and col.signature not in seen:
            seen.add(col.signature); cols.append(col)
    for i in range(1,V+1):
        # pickup only and return to depot; route unloads at depot
        maxq=min(Y0[i], Q, int((T-dist[0][i]-dist[i][0])//cunit))
        if max_pair_q is not None: maxq=min(maxq,max_pair_q)
        for q in range(1,maxq+1):
            ql=[0]*V; ql[i-1]=q; add([i], ql)
    for i in range(1,V+1):
        for j in range(1,V+1):
            if i==j: continue
            travel=dist[0][i]+dist[i][j]+dist[j][0]
            maxp=min(Y0[i], Q, int((T-travel)//cunit))
            if max_pair_q is not None: maxp=min(maxp,max_pair_q)
            if maxp<=0: continue
            maxd=min(C[j]-Y0[j], Q)
            for p in range(1,maxp+1):
                for d in range(1,min(p,maxd)+1):
                    ql=[0]*V; ql[i-1]=p; ql[j-1]=-d; add([i,j],ql)
    # three-stop chains: pickup at first, then two drops OR two pickups then one drop
    # capped to keep seed small; pricing will add exact columns.
    for i in range(1,V+1):
        neigh=sorted([j for j in range(1,V+1) if j!=i], key=lambda j: dist[i][j])[:5]
        for j in neigh:
            for k in neigh:
                if k==i or k==j: continue
                travel=dist[0][i]+dist[i][j]+dist[j][k]+dist[k][0]
                maxp=min(Y0[i], Q, int((T-travel)//cunit), 8)
                if maxp<=0: continue
                for p in range(1,maxp+1):
                    maxdj=min(C[j]-Y0[j], p)
                    if maxdj<=0: continue
                    for d1 in range(1,maxdj+1):
                        maxd2=min(C[k]-Y0[k], p-d1)
                        if maxd2<=0: continue
                        # a small number of quantities is enough for seed
                        for d2 in {1, maxd2}:
                            if d1+d2<=p:
                                ql=[0]*V; ql[i-1]=p; ql[j-1]=-d1; ql[k-1]=-d2; add([i,j,k],ql)
    return cols


class MasterBuilder:
    def __init__(self, ins: Dict[str,Any], columns: List[Column], gcap: float, lam=0.15, artificial_penalty=1e5,
                 fixed_cols: Optional[Dict[int,float]]=None, banned_cols: Optional[Set[Tuple]]=None,
                 y_lb: Optional[Dict[int,int]]=None, y_ub: Optional[Dict[int,int]]=None,
                 station_lb: Optional[Dict[int,int]]=None, station_ub: Optional[Dict[int,int]]=None):
        self.ins=ins; self.columns=columns; self.gcap=gcap; self.lam=lam; self.penalty=artificial_penalty
        self.fixed_cols=fixed_cols or {}; self.banned_cols=banned_cols or set()
        self.y_lb=y_lb or {}; self.y_ub=y_ub or {}
        self.station_lb=station_lb or {}; self.station_ub=station_ub or {}
        self.V=ins['V']; self.pairs=[(i,j) for i in range(1,self.V+1) for j in range(i+1,self.V+1)]
        self.ncol=len(columns)
        self.idx={}
        self.names=[]
        self._build_indices()

    def _add(self, name):
        idx=len(self.names); self.names.append(name); return idx

    def _build_indices(self):
        C=self.ncol; V=self.V
        self.z=list(range(C)); self.names=[f'z_{c}' for c in range(C)]
        self.y={i:self._add(f'y_{i}') for i in range(1,V+1)}
        self.r={i:self._add(f'r_{i}') for i in range(1,V+1)}
        self.e={i:self._add(f'e_{i}') for i in range(1,V+1)}
        self.h={(i,j):self._add(f'h_{i}_{j}') for (i,j) in self.pairs}
        self.S=self._add('S'); self.H=self._add('H'); self.cap_slack=self._add('cap_slack')

    def build_lp(self):
        ins=self.ins; V=self.V; Capa=ins['capacities']; Y0=ins['initial']; target=ins['target']; w=ins['weights']
        n=len(self.names); c=np.zeros(n)
        for i in range(1,V+1): c[self.e[i]]=w[i]
        c[self.cap_slack]=self.penalty
        lb=np.zeros(n); ub=np.full(n, np.inf)
        for ci,col in enumerate(self.columns):
            lb[ci]=0; ub[ci]=1
            if ci in self.fixed_cols:
                lb[ci]=ub[ci]=self.fixed_cols[ci]
        for i in range(1,V+1):
            lb[self.y[i]]=self.y_lb.get(i,0); ub[self.y[i]]=self.y_ub.get(i,Capa[i])
            lb[self.r[i]]=0; ub[self.r[i]]=Capa[i]/target[i]
            lb[self.e[i]]=0; ub[self.e[i]]=max(1.0, abs(Capa[i]/target[i]-1.0))
        ub[self.S]=sum(Capa[i]/target[i] for i in range(1,V+1))
        ub[self.H]=sum(max(Capa[i]/target[i], Capa[j]/target[j]) for (i,j) in self.pairs)
        # Constraints
        Aub=[]; bub=[]; Aeq=[]; beq=[]; row_names=[]; eq_names=[]
        def add_ub(co,b,name):
            row=lil_matrix((1,n))
            for idx,val in co.items():
                if abs(val)>1e-12: row[0,idx]=val
            Aub.append(row.tocsr()); bub.append(b); row_names.append(name)
        def add_eq(co,b,name):
            row=lil_matrix((1,n))
            for idx,val in co.items():
                if abs(val)>1e-12: row[0,idx]=val
            Aeq.append(row.tocsr()); beq.append(b); eq_names.append(name)
        # vehicle count
        add_ub({ci:1 for ci in range(self.ncol)}, ins['M'], 'vehicle')
        # each station at most once, with optional branching lower/upper bounds
        for i in range(1,V+1):
            co={ci:1 for ci,col in enumerate(self.columns) if (col.visitmask & (1<<(i-1)))}
            add_ub(co,self.station_ub.get(i,1.0),f'station_{i}')
            if self.station_lb.get(i,0)>0:
                add_ub({idx:-val for idx,val in co.items()},-float(self.station_lb[i]),f'station_lb_{i}')
        # inventory equations
        for i in range(1,V+1):
            co={self.y[i]:1}
            for ci,col in enumerate(self.columns):
                di=col.delta[i-1]
                if di: co[ci]=co.get(ci,0)-di
            add_eq(co,Y0[i],f'inventory_{i}')
        # ratio equations
        for i in range(1,V+1): add_eq({self.r[i]:1, self.y[i]:-1.0/target[i]},0,f'ratio_{i}')
        # e abs
        for i in range(1,V+1):
            add_ub({self.r[i]:1,self.e[i]:-1},1,f'e_pos_{i}')      # r-e<=1
            add_ub({self.r[i]:-1,self.e[i]:-1},-1,f'e_neg_{i}')    # -r-e<=-1
        # h abs
        for i,j in self.pairs:
            add_ub({self.r[i]:1,self.r[j]:-1,self.h[i,j]:-1},0,f'h1_{i}_{j}')
            add_ub({self.r[i]:-1,self.r[j]:1,self.h[i,j]:-1},0,f'h2_{i}_{j}')
        # S and H equalities
        co={self.S:-1};
        for i in range(1,V+1): co[self.r[i]]=co.get(self.r[i],0)+1
        add_eq(co,0,'S_def')
        co={self.H:-1};
        for ij in self.pairs: co[self.h[ij]]=co.get(self.h[ij],0)+1
        add_eq(co,0,'H_def')
        # gcap with artificial slack: H - V*g*S - slack <= 0
        add_ub({self.H:1,self.S:-V*self.gcap,self.cap_slack:-1},0,'gcap')
        A_ub=vstack(Aub).tocsr() if Aub else None
        A_eq=vstack(Aeq).tocsr() if Aeq else None
        return c,A_ub,np.array(bub),A_eq,np.array(beq),[(lb[i],ub[i]) for i in range(n)],row_names,eq_names

    def solve_lp(self, verbose=False):
        c,Aub,bub,Aeq,beq,bounds,row_names,eq_names=self.build_lp()
        res=linprog(c,A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs',options={'presolve':True})
        return res,row_names,eq_names

    def solve_milp_generated(self, time_limit=120, verbose=False):
        c,Aub,bub,Aeq,beq,bounds,row_names,eq_names=self.build_lp()
        # combine into LinearConstraint; integrality z binary, y integer; others continuous
        rows=[]; lows=[]; ups=[]
        if Aub is not None:
            rows.append(Aub); lows += [-np.inf]*Aub.shape[0]; ups += list(bub)
        if Aeq is not None:
            rows.append(Aeq); lows += list(beq); ups += list(beq)
        A=vstack(rows).tocsr()
        lb=np.array([b[0] for b in bounds]); ub=np.array([b[1] for b in bounds])
        integrality=np.zeros(len(bounds), dtype=int)
        for ci in range(self.ncol): integrality[ci]=1
        for i in range(1,self.V+1): integrality[self.y[i]]=1
        res=milp(c,integrality=integrality,bounds=Bounds(lb,ub),constraints=LinearConstraint(A,np.array(lows),np.array(ups)),
                 options={'time_limit':time_limit,'mip_rel_gap':1e-9,'disp':verbose,'presolve':True})
        return res,row_names,eq_names


def reconstruct_master_solution(ins, columns, builder: MasterBuilder, x, lam=0.15):
    V=ins['V']
    zvals=np.array(x[:len(columns)]) if len(columns)>0 else np.array([])
    selected=[i for i,z in enumerate(zvals) if z>0.5]
    y=[]
    for i in range(1,V+1): y.append(int(round(x[builder.y[i]])))
    G,P,obj,S,H=eval_y(ins,y,lam)
    routes=[]; ops=[]
    for ci in selected:
        col=columns[ci]
        routes.append(list(col.path)); ops.append(list(col.q))
    return {'selected_indices':selected,'routes':routes,'q_vectors':ops,'y':y,'G':G,'P':P,'obj':obj,'S':S,'H':H,
            'z_fractional': [(i,float(z)) for i,z in enumerate(zvals) if z>1e-7 and z<1-1e-7]}


@dataclass
class Label:
    mask: int
    last: int
    load: int
    pick: int
    travel: float
    cost: float
    path: Tuple[int,...]
    q: Tuple[int,...]


def dominates(a: Label, b: Label, eps=1e-10) -> bool:
    return a.travel <= b.travel + eps and a.cost <= b.cost + eps


def price_columns(ins: Dict[str,Any], mu: float, pi: np.ndarray, sigma: np.ndarray,
                  existing: Set[Tuple], T=3600, taup=60, taud=60, Q: Optional[int]=None,
                  max_return_cols=50, verbose=False, label_limit: Optional[int]=None) -> Tuple[float,List[Column],Dict[str,Any]]:
    """Exact label-setting pricing for missing route-load columns under current master duals.

    Reduced cost of a route-load column is
        -mu - sum_i pi_i a_i + sum_i sigma_i delta_i.
    pi and sigma are indexed 1..V in arrays of length V+1.
    """
    V=ins['V']; Y0=ins['initial']; C=ins['capacities']; dist=ins['distances']; cunit=taup+taud
    if Q is None: Q=max(ins['Q'])
    start=Label(mask=0,last=0,load=0,pick=0,travel=0.0,cost=0.0,path=tuple(),q=tuple([0]*V))
    labels: Dict[Tuple[int,int,int,int], List[Label]]={(0,0,0,0):[start]}
    queue=[start]
    best_rc=math.inf
    heap=[] # max heap by -rc? store (-rc,counter,col)
    counter=0; expanded=0; generated=0; pruned_dom=0
    while queue:
        lab=queue.pop()
        expanded+=1
        # feasible completed route with return
        if lab.path:
            total_time=lab.travel + dist[lab.last][0] + cunit*lab.pick
            if total_time <= T + 1e-9:
                rc=lab.cost - mu
                if rc < best_rc: best_rc=rc
                if rc < -1e-8:
                    col=make_col(lab.path, lab.q, ins, taup, taud)
                    # make_col recomputes travel/time; it should match
                    if col.signature not in existing:
                        counter+=1
                        item=(-rc,counter,col)  # largest -rc = most negative rc
                        if len(heap)<max_return_cols:
                            heapq.heappush(heap,item)
                        elif item[0] > heap[0][0]:
                            heapq.heapreplace(heap,item)
        if label_limit is not None and expanded>label_limit:
            break
        # Extend to unvisited station
        for i in range(1,V+1):
            bit=1<<(i-1)
            if lab.mask & bit: continue
            tr2=lab.travel + dist[lab.last][i]
            # even one operation and return must be feasible
            if tr2 + dist[i][0] + cunit*lab.pick > T + 1e-9:
                continue
            rem_pick_budget=int(math.floor((T - tr2 - dist[i][0]) / cunit + 1e-9))
            # pickup options
            maxp=min(Y0[i], Q-lab.load, rem_pick_budget-lab.pick)
            if maxp>0:
                # Enumerate all pickup quantities. Q<=30 in current samples.
                for qv in range(1, maxp+1):
                    load2=lab.load+qv; pick2=lab.pick+qv
                    qlist=list(lab.q); qlist[i-1]=qv; qtuple=tuple(qlist)
                    cost2=lab.cost - pi[i] - sigma[i]*qv  # delta=-q
                    nl=Label(mask=lab.mask|bit,last=i,load=load2,pick=pick2,travel=tr2,cost=cost2,path=lab.path+(i,),q=qtuple)
                    key=(nl.mask,nl.last,nl.load,nl.pick)
                    lst=labels.get(key,[])
                    if any(dominates(old,nl) for old in lst):
                        pruned_dom+=1; continue
                    newlst=[old for old in lst if not dominates(nl,old)]
                    newlst.append(nl); labels[key]=newlst; queue.append(nl); generated+=1
            # drop options
            maxd=min(C[i]-Y0[i], lab.load)
            if maxd>0:
                for dval in range(1, maxd+1):
                    load2=lab.load-dval; pick2=lab.pick
                    # time unaffected except travel, already checked
                    qlist=list(lab.q); qlist[i-1]=-dval; qtuple=tuple(qlist)
                    cost2=lab.cost - pi[i] + sigma[i]*dval  # q=-d, delta=+d
                    nl=Label(mask=lab.mask|bit,last=i,load=load2,pick=pick2,travel=tr2,cost=cost2,path=lab.path+(i,),q=qtuple)
                    key=(nl.mask,nl.last,nl.load,nl.pick)
                    lst=labels.get(key,[])
                    if any(dominates(old,nl) for old in lst):
                        pruned_dom+=1; continue
                    newlst=[old for old in lst if not dominates(nl,old)]
                    newlst.append(nl); labels[key]=newlst; queue.append(nl); generated+=1
    # return columns ordered by most negative rc
    cols=[item[2] for item in sorted(heap, reverse=True)]
    stats={'expanded':expanded,'generated':generated,'states':len(labels),'labels_kept':sum(len(v) for v in labels.values()),
           'pruned_dom':pruned_dom,'best_rc':best_rc,'returned':len(cols),'terminated_by_limit': label_limit is not None and expanded>label_limit}
    return best_rc, cols, stats


def column_generation_cap(ins: Dict[str,Any], gcap: float, lam=0.15, T=3600, taup=60, taud=60,
                          max_iter=100, max_cols_per_iter=50, time_limit=120, seed_pair_q=None,
                          verbose=False, label_limit=None) -> Dict[str,Any]:
    start=time.time()
    cols=simple_seed_columns(ins,T,taup,taud,max_pair_q=seed_pair_q)
    # unique
    uniq=[]; seen=set()
    for c in cols:
        if c.signature not in seen:
            seen.add(c.signature); uniq.append(c)
    cols=uniq
    logs=[]; lp_res=None; row_names=[]; eq_names=[]
    no_new_count=0
    while time.time()-start < time_limit and len(logs)<max_iter:
        builder=MasterBuilder(ins, cols, gcap, lam=lam, artificial_penalty=1e5)
        lp_res,row_names,eq_names=builder.solve_lp()
        if not lp_res.success:
            return {'status':'lp_fail','message':lp_res.message,'time':time.time()-start,'ncols':len(cols),'logs':logs}
        # extract duals
        ubm=lp_res.ineqlin.marginals; eqm=lp_res.eqlin.marginals
        mu=ubm[row_names.index('vehicle')]
        pi=np.zeros(ins['V']+1); sigma=np.zeros(ins['V']+1)
        for i in range(1,ins['V']+1):
            pi[i]=ubm[row_names.index(f'station_{i}')]
            sigma[i]=eqm[eq_names.index(f'inventory_{i}')]
        best_rc,newcols,stats=price_columns(ins,mu,pi,sigma,set(c.signature for c in cols),T,taup,taud,Q=max(ins['Q']),
                                           max_return_cols=max_cols_per_iter,verbose=verbose,label_limit=label_limit)
        added=0
        for c in newcols:
            if c.signature not in seen:
                seen.add(c.signature); cols.append(c); added+=1
        cap_slack=lp_res.x[builder.cap_slack]
        logs.append({'iter':len(logs)+1,'lp_obj':float(lp_res.fun),'cap_slack':float(cap_slack),'ncols':len(cols),
                     'best_rc':float(best_rc),'added':added,**stats})
        if verbose:
            print('CG',logs[-1])
        if added==0 or best_rc >= -1e-7:
            break
    # final restricted MILP
    builder=MasterBuilder(ins, cols, gcap, lam=lam, artificial_penalty=1e5)
    milp_res,row_names,eq_names=builder.solve_milp_generated(time_limit=max(1,time_limit-(time.time()-start)), verbose=False)
    sol=None
    if milp_res.x is not None:
        sol=reconstruct_master_solution(ins, cols, builder, milp_res.x, lam=lam)
        sol['cap_slack']=float(milp_res.x[builder.cap_slack])
        sol['P_model']=float(milp_res.fun - 1e5*milp_res.x[builder.cap_slack])
    lp_bound=float(lp_res.fun) if lp_res is not None and lp_res.success else None
    # If pricing ended with no missing negative column, lp_bound is full LP bound for penalized LP.
    lp_cert= bool(logs and (logs[-1]['best_rc']>=-1e-7 or logs[-1]['added']==0) and not logs[-1].get('terminated_by_limit',False))
    return {'status':'done','time':time.time()-start,'gcap':gcap,'ncols':len(cols),'lp_bound':lp_bound,'lp_certified':lp_cert,
            'lp_cap_slack': float(lp_res.x[builder.cap_slack]) if lp_res is not None and lp_res.success else None,
            'milp_status': int(milp_res.status) if milp_res is not None else None,
            'milp_success': bool(milp_res.success) if milp_res is not None else None,
            'milp_fun': float(milp_res.fun) if milp_res is not None and milp_res.fun is not None else None,
            'solution':sol,'logs':logs}


# A very small frontier driver: it uses generated-column cap subproblems to look for incumbent improvements.
def bpc_frontier(path: str, lam=0.15, T=3600, taup=60, taud=60, total_time=300, cap_time=60, verbose=False):
    ins=parse_instance(path)
    y0=[ins['initial'][i] for i in range(1,ins['V']+1)]
    G0,P0,UB,S0,H0=eval_y(ins,y0,lam)
    best={'y':y0,'G':G0,'P':P0,'obj':UB,'routes':[]}
    cap=min(1.0,UB)
    start=time.time(); logs=[]; certified=False; lower=0.0
    while cap>1e-8 and time.time()-start<total_time:
        tl=min(cap_time,total_time-(time.time()-start))
        if tl<=2: break
        ans=column_generation_cap(ins,cap,lam,T,taup,taud,time_limit=tl,max_iter=50,max_cols_per_iter=40,seed_pair_q=None,verbose=verbose)
        logs.append(ans)
        sol=ans.get('solution')
        if sol and sol.get('cap_slack',1)>1e-6:
            # RMP did not find feasible integer under cap. If LP is certified with positive slack, cap infeasible for full LP;
            # this is strong but rare. Continue lower cap is impossible; stop.
            break
        if sol and sol['obj'] < UB-1e-9 and sol.get('cap_slack',0)<=1e-6:
            UB=sol['obj']; best=sol
        # P lower bound: if full LP is certified and slack zero, lp_bound is a lower bound on P for cap region.
        if ans.get('lp_certified') and ans.get('lp_cap_slack',1)<=1e-6:
            # lower bound on any solution with G<=cap is at least lam*LP_P (relaxed); for frontier exact, need integer P*. This is LP only.
            lower=max(lower, lam*ans['lp_bound'])
        if not sol or sol.get('cap_slack',1)>1e-6:
            break
        newcap=sol['G']-1e-7
        if newcap>=cap-1e-8:
            newcap=cap*0.7
        cap=max(0,newcap)
        if verbose:
            print('frontier cap ->',cap,'UB',UB)
    return {'instance':os.path.basename(path),'time':time.time()-start,'UB':UB,'best':best,'logs':logs,'lower_LP_only':lower,'certified_original':certified}


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--cap',type=float,default=None)
    ap.add_argument('--time',type=float,default=120)
    ap.add_argument('--frontier',action='store_true')
    ap.add_argument('--verbose',action='store_true')
    args=ap.parse_args()
    if args.frontier:
        out=bpc_frontier(args.file,total_time=args.time,cap_time=min(60,args.time),verbose=args.verbose)
    else:
        ins=parse_instance(args.file)
        cap=args.cap if args.cap is not None else min(1.0, eval_y(ins,[ins['initial'][i] for i in range(1,ins['V']+1)])[2])
        out=column_generation_cap(ins,cap,time_limit=args.time,verbose=args.verbose)
    print(json.dumps(out,indent=2))

# ---------- MILP pricing alternative ----------
class VB:
    def __init__(self): self.names=[]; self.lb=[]; self.ub=[]; self.integrality=[]
    def add(self,name,lb=0,ub=np.inf,integer=False,binary=False):
        idx=len(self.names); self.names.append(name)
        if binary: lb=0; ub=1; integ=1
        elif integer: integ=1
        else: integ=0
        self.lb.append(lb); self.ub.append(ub); self.integrality.append(integ); return idx

def precompute_tsp(V, dist):
    N=1<<V; INF=1e100
    dp=np.full((N,V), INF)
    for j in range(V): dp[1<<j,j]=dist[0][j+1]
    for mask in range(N):
        for j in range(V):
            val=dp[mask,j]
            if val>=INF: continue
            rem=(N-1)^mask
            while rem:
                lb=rem & -rem; k=lb.bit_length()-1; nm=mask|lb
                nv=val+dist[j+1][k+1]
                if nv<dp[nm,k]: dp[nm,k]=nv
                rem-=lb
    tsp=np.zeros(N)
    for mask in range(1,N):
        best=INF; m=mask
        while m:
            lb=m & -m; j=lb.bit_length()-1
            best=min(best, dp[mask,j]+dist[j+1][0])
            m-=lb
        tsp[mask]=best
    return tsp

def price_milp_column(ins: Dict[str,Any], mu: float, pi: np.ndarray, sigma: np.ndarray,
                      existing: Optional[Set[Tuple]]=None, T=3600, taup=60, taud=60,
                      time_limit=20, use_subset=True, no_good: Optional[List[Tuple[int,Tuple[int,...]]]]=None,
                      forbidden_stations: Optional[Set[int]]=None,
                      verbose=False) -> Tuple[Optional[Column], float, Dict[str,Any]]:
    """Solve the single-route pricing problem as a compact exact MIP.
    Returns (column, reduced_cost, stats). Existing/no_good signatures can be excluded by exact q-vector cuts.
    """
    existing=existing or set(); no_good=no_good or []; forbidden_stations=forbidden_stations or set()
    V=ins['V']; Q=max(ins['Q']); C=ins['capacities']; Y0=ins['initial']; dist=ins['distances']; cunit=taup+taud
    stations=range(1,V+1); nodes=range(V+1); maxpick=int(T//cunit)
    b=VB(); x={}; z={}; mode={}; p={}; d={}; L={}; u={}
    for i in nodes:
        for j in nodes:
            if i!=j: x[i,j]=b.add(f'x_{i}_{j}',binary=True)
    for i in stations:
        z[i]=b.add(f'z_{i}',binary=True)
        mode[i]=b.add(f'mode_{i}',binary=True)
        p[i]=b.add(f'p_{i}',lb=0,ub=min(Y0[i],Q,maxpick),integer=True)
        d[i]=b.add(f'd_{i}',lb=0,ub=min(C[i]-Y0[i],Q,maxpick),integer=True)
        L[i]=b.add(f'L_{i}',lb=0,ub=Q,integer=True)
        u[i]=b.add(f'u_{i}',lb=0,ub=V)
    n=len(b.names); rows=[]; lows=[]; ups=[]
    def add(co,lo=-np.inf,up=np.inf):
        row=lil_matrix((1,n))
        for idx,val in co.items():
            if abs(val)>1e-12: row[0,idx]=val
        rows.append(row.tocsr()); lows.append(lo); ups.append(up)
    # route nonempty and depot degree exactly one in/out
    add({x[0,j]:1 for j in stations},1,1)
    add({x[i,0]:1 for i in stations},1,1)
    for i in stations:
        add({**{x[i,j]:1 for j in nodes if j!=i}, z[i]:-1},0,0)
        add({**{x[j,i]:1 for j in nodes if j!=i}, z[i]:-1},0,0)
        add({mode[i]:1,z[i]:-1},-np.inf,0)
        up_p=min(Y0[i],Q,maxpick); up_d=min(C[i]-Y0[i],Q,maxpick)
        add({p[i]:1,mode[i]:-up_p},-np.inf,0)
        add({d[i]:1,z[i]:-up_d,mode[i]:up_d},-np.inf,0)
        add({p[i]:1,d[i]:1,z[i]:-1},0,np.inf)
        add({L[i]:1,z[i]:-Q},-np.inf,0)
        add({u[i]:1,z[i]:-V},-np.inf,0)
        add({u[i]:1,z[i]:-1},0,np.inf)
        if i in forbidden_stations:
            add({z[i]:1},0,0)
    # MTZ
    for i in stations:
        for j in stations:
            if i!=j:
                add({u[i]:1,u[j]:-1,x[i,j]:V,z[j]:V},-np.inf,2*V-1)
    # load propagation
    big=Q+maxpick+5
    for i in stations:
        add({L[i]:1,p[i]:-1,d[i]:1,x[0,i]:big},-np.inf,big)
        add({L[i]:1,p[i]:-1,d[i]:1,x[0,i]:-big},-big,np.inf)
        for j in stations:
            if i!=j:
                add({L[j]:1,L[i]:-1,p[j]:-1,d[j]:1,x[i,j]:big},-np.inf,big)
                add({L[j]:1,L[i]:-1,p[j]:-1,d[j]:1,x[i,j]:-big},-big,np.inf)
    # final load nonnegative: sum p >= sum d
    add({**{p[i]:1 for i in stations}, **{d[i]:-1 for i in stations}},0,np.inf)
    # route duration
    co={}
    for i in nodes:
        for j in nodes:
            if i!=j: co[x[i,j]]=co.get(x[i,j],0)+dist[i][j]
    for i in stations: co[p[i]]=co.get(p[i],0)+cunit
    add(co,-np.inf,T)
    if use_subset and V<=16:
        tsp=precompute_tsp(V,dist); BIG=1e5
        for mask in range(1,1<<V):
            co={}; cnt=0; m=mask
            while m:
                lb=m & -m; ii=lb.bit_length(); cnt+=1; m-=lb
                co[p[ii]]=co.get(p[ii],0)+cunit
                co[z[ii]]=co.get(z[ii],0)+BIG
            add(co,-np.inf,T-tsp[mask]+BIG*cnt)
    # Exclude exact q-vector signatures if requested.  Since route order may differ for same q, exclude q+visitmask only optionally.
    # no_good list entries are (visitmask, qtuple).  Linear no-good: sum matches <= m-1 over selected station q equalities is hard; use simple
    # station-set no-good when qtuple exactly known: sum_{i in mask} z_i <= |mask|-1. This is stronger and may cut other columns with same support.
    # It is only used for k-best pricing in experiments, not for exact certificate.
    for mask,qtuple in no_good:
        inds=[i+1 for i in range(V) if mask & (1<<i)]
        if inds:
            add({z[i]:1 for i in inds},-np.inf,len(inds)-1)
    c=np.zeros(n)
    for i in stations:
        c[z[i]] += -pi[i]
        c[p[i]] += -sigma[i]
        c[d[i]] += sigma[i]
    A=vstack(rows).tocsr(); cons=LinearConstraint(A,np.array(lows),np.array(ups)); bounds=Bounds(np.array(b.lb),np.array(b.ub))
    t0=time.time()
    res=milp(c,integrality=np.array(b.integrality),bounds=bounds,constraints=cons,
             options={'time_limit':time_limit,'mip_rel_gap':1e-9,'presolve':True,'disp':verbose})
    elapsed=time.time()-t0
    stats={'status':int(res.status),'success':bool(res.success),'fun':float(res.fun) if res.fun is not None else None,
           'time':elapsed,'gap':getattr(res,'mip_gap',None),'nodes':getattr(res,'mip_node_count',None)}
    if res.x is None:
        return None, math.inf, stats
    vals=res.x
    q=[0]*V; arcs={}
    for i in stations:
        pv=int(round(vals[p[i]])); dv=int(round(vals[d[i]])); q[i-1]=pv-dv
    for i in nodes:
        for j in nodes:
            if i!=j and vals[x[i,j]]>0.5: arcs[i]=j
    path=[]; cur=0; seen_nodes=set()
    while cur in arcs and arcs[cur]!=0 and arcs[cur] not in seen_nodes:
        cur=arcs[cur]; path.append(cur); seen_nodes.add(cur)
    col=make_col(tuple(path), tuple(q), ins, taup, taud)
    rc=float(res.fun - mu)
    stats['rc']=rc; stats['path']=path; stats['q']=q; stats['time_route']=col.time
    return col,rc,stats


def column_generation_cap_mippricing(ins: Dict[str,Any], gcap: float, lam=0.15, T=3600, taup=60, taud=60,
                                      max_iter=30, time_limit=120, pricing_time=20, verbose=False) -> Dict[str,Any]:
    start=time.time(); cols=minimal_seed_columns(ins,T,taup,taud,q_cap=8)
    seen=set(); uniq=[]
    for c in cols:
        if c.signature not in seen:
            seen.add(c.signature); uniq.append(c)
    cols=uniq; logs=[]; lp_res=None
    while time.time()-start < time_limit and len(logs)<max_iter:
        builder=MasterBuilder(ins, cols, gcap, lam=lam, artificial_penalty=1e5)
        lp_res,row_names,eq_names=builder.solve_lp()
        if not lp_res.success:
            return {'status':'lp_fail','message':lp_res.message,'time':time.time()-start,'ncols':len(cols),'logs':logs}
        ubm=lp_res.ineqlin.marginals; eqm=lp_res.eqlin.marginals
        mu=ubm[row_names.index('vehicle')]
        pi=np.zeros(ins['V']+1); sigma=np.zeros(ins['V']+1)
        for i in range(1,ins['V']+1):
            pi[i]=ubm[row_names.index(f'station_{i}')]
            sigma[i]=eqm[eq_names.index(f'inventory_{i}')]
        rem=max(1,min(pricing_time,time_limit-(time.time()-start)))
        col,rc,stats=price_milp_column(ins,mu,pi,sigma,set(c.signature for c in cols),T,taup,taud,time_limit=rem,use_subset=False,verbose=False)
        added=0
        if col is not None and rc < -1e-7:
            # Adding a duplicate column is projection-safe because station-packing constraints
            # couple identical columns; it can remove upper-bound degeneracy in LP pricing.
            cols.append(col); seen.add(col.signature); added=1
        logs.append({'iter':len(logs)+1,'lp_obj':float(lp_res.fun),'lp_cap_slack':float(lp_res.x[builder.cap_slack]),
                     'ncols':len(cols),'rc':float(rc),'added':added,'pricing':stats})
        if verbose: print('CG-MIP',logs[-1])
        if not stats.get('success',False): break
        if rc >= -1e-7 or added==0: break
    builder=MasterBuilder(ins, cols, gcap, lam=lam, artificial_penalty=1e5)
    rem=max(1,time_limit-(time.time()-start))
    milp_res,row_names,eq_names=builder.solve_milp_generated(time_limit=rem, verbose=False)
    sol=None
    if milp_res.x is not None:
        sol=reconstruct_master_solution(ins, cols, builder, milp_res.x, lam=lam)
        sol['cap_slack']=float(milp_res.x[builder.cap_slack])
        sol['P_model']=float(milp_res.fun - 1e5*milp_res.x[builder.cap_slack])
    lp_cert=bool(logs and logs[-1]['pricing'].get('success') and logs[-1]['rc']>=-1e-7)
    return {'status':'done','time':time.time()-start,'gcap':gcap,'ncols':len(cols),'lp_bound':float(lp_res.fun) if lp_res is not None and lp_res.success else None,
            'lp_cap_slack':float(lp_res.x[builder.cap_slack]) if lp_res is not None and lp_res.success else None,
            'lp_certified':lp_cert,'milp_status':int(milp_res.status),'milp_success':bool(milp_res.success),
            'milp_fun':float(milp_res.fun) if milp_res.fun is not None else None,'solution':sol,'logs':logs}

# ---------- Simple branch-price over final-inventory and station-service branching ----------
@dataclass
class BPNode:
    node_id: int
    depth: int
    y_lb: Dict[int,int]
    y_ub: Dict[int,int]
    station_lb: Dict[int,int]
    station_ub: Dict[int,int]


def _dual_arrays(ins, row_names, eq_names, lp_res):
    V=ins['V']; ubm=lp_res.ineqlin.marginals; eqm=lp_res.eqlin.marginals
    mu=ubm[row_names.index('vehicle')]
    pi=np.zeros(V+1); sigma=np.zeros(V+1)
    for i in range(1,V+1):
        val=ubm[row_names.index(f'station_{i}')]
        nm=f'station_lb_{i}'
        if nm in row_names:
            val -= ubm[row_names.index(nm)]
        pi[i]=val
        sigma[i]=eqm[eq_names.index(f'inventory_{i}')]
    return mu,pi,sigma


def solve_node_cg_mippricing(ins: Dict[str,Any], cols: List[Column], seen: Set[Tuple], node: BPNode,
                              gcap: float, lam=0.15, T=3600, taup=60, taud=60,
                              max_iter=20, node_time=60, pricing_time=10,
                              verbose=False) -> Dict[str,Any]:
    start=time.time(); logs=[]; lp_res=None; builder=None; row_names=[]; eq_names=[]
    while time.time()-start < node_time and len(logs)<max_iter:
        builder=MasterBuilder(ins, cols, gcap, lam=lam, artificial_penalty=1e5,
                              y_lb=node.y_lb, y_ub=node.y_ub,
                              station_lb=node.station_lb, station_ub=node.station_ub)
        lp_res,row_names,eq_names=builder.solve_lp()
        if not lp_res.success:
            return {'status':'lp_infeasible_or_fail','lp_success':False,'message':lp_res.message,'time':time.time()-start,'logs':logs}
        mu,pi,sigma=_dual_arrays(ins,row_names,eq_names,lp_res)
        forbidden={i for i,u in node.station_ub.items() if u<=0}
        rem=max(1,min(pricing_time,node_time-(time.time()-start)))
        col,rc,stats=price_milp_column(ins,mu,pi,sigma,set(c.signature for c in cols),T,taup,taud,
                                       time_limit=rem,use_subset=False,forbidden_stations=forbidden,verbose=False)
        added=0
        if col is not None and rc < -1e-7:
            # Adding a duplicate column is projection-safe because station-packing constraints
            # couple identical columns; it can remove upper-bound degeneracy in LP pricing.
            cols.append(col); seen.add(col.signature); added=1
        logs.append({'iter':len(logs)+1,'lp_obj':float(lp_res.fun),'cap_slack':float(lp_res.x[builder.cap_slack]),
                     'ncols':len(cols),'rc':float(rc),'added':added,'pricing':stats})
        if verbose: print('NODE',node.node_id,'CG',logs[-1], flush=True)
        if not stats.get('success',False):
            return {'status':'pricing_time_or_fail','lp_success':True,'lp_certified':False,'time':time.time()-start,'logs':logs,
                    'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}
        if rc >= -1e-7 or added==0:
            break
    lp_cert=bool(logs and logs[-1]['pricing'].get('success') and logs[-1]['rc']>=-1e-7)
    return {'status':'ok','lp_success':True,'lp_certified':lp_cert,'time':time.time()-start,'logs':logs,
            'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}


def branch_price_cap(ins: Dict[str,Any], gcap: float, lam=0.15, T=3600, taup=60, taud=60,
                     total_time=120, node_time=30, pricing_time=8, max_nodes=200,
                     verbose=False) -> Dict[str,Any]:
    """A research-prototype branch-price for the fixed-Gini-cap subproblem.

    Branching priority: fractional final inventory y_i, then fractional station-service u_i.
    It produces a rigorous lower bound for processed nodes whose pricing is certified.  If the
    full tree is processed, the returned best solution is a certificate for P*(gcap).  Otherwise
    status is 'time_limit' with a valid incumbent and partial lower bound.
    """
    start=time.time()
    cols=minimal_seed_columns(ins,T,taup,taud,q_cap=8)
    seen=set(); uniq=[]
    for c in cols:
        if c.signature not in seen:
            seen.add(c.signature); uniq.append(c)
    cols=uniq
    # incumbent from generated-column MILP at root after a short CG
    bestP=math.inf; bestsol=None
    root=BPNode(0,0,{}, {}, {}, {})
    active=[root]; next_id=1; processed=0; pruned=0; unresolved=0; node_logs=[]; global_lb=math.inf
    # DFS/LIFO with lower-bound sorting after each insertion (small tree)
    while active and time.time()-start < total_time and processed < max_nodes:
        node=active.pop()
        rem_total=total_time-(time.time()-start)
        nt=min(node_time, max(1,rem_total))
        res=solve_node_cg_mippricing(ins,cols,seen,node,gcap,lam,T,taup,taud,max_iter=20,node_time=nt,pricing_time=pricing_time,verbose=verbose)
        processed+=1
        rec={'node':node.node_id,'depth':node.depth,'status':res['status'],'time':res['time'],'ncols':len(cols),'children':0}
        if not res.get('lp_success'):
            pruned+=1; rec['prune']='lp_fail'; node_logs.append(rec); continue
        lp_res=res['lp_res']; builder=res['builder']
        rec['lp_obj']=float(lp_res.fun); rec['cap_slack']=float(lp_res.x[builder.cap_slack]); rec['lp_certified']=res.get('lp_certified',False)
        # If pricing was not certified, cannot safely branch further for an exact result.
        if not res.get('lp_certified'):
            unresolved+=1; rec['prune']='unresolved_pricing'; node_logs.append(rec); break
        if lp_res.x[builder.cap_slack] > 1e-6:
            pruned+=1; rec['prune']='cap_infeasible'; node_logs.append(rec); continue
        lb=float(lp_res.fun)  # P lower bound for this node
        if lb >= bestP-1e-8:
            pruned+=1; rec['prune']='bound'; node_logs.append(rec); continue
        # Restricted MILP gives a valid incumbent, but not a proof by itself.
        # It is relatively expensive with a large column pool, so solve it only at the root
        # and at shallow nodes where it can materially improve pruning.
        if node.depth <= 0 or (math.isinf(bestP) and node.depth <= 2):
            milp_res,_,_=builder.solve_milp_generated(time_limit=max(1,min(5,total_time-(time.time()-start))), verbose=False)
            if milp_res.x is not None and milp_res.status in (0,1):
                sol=reconstruct_master_solution(ins, cols, builder, milp_res.x, lam=lam)
                sol['cap_slack']=float(milp_res.x[builder.cap_slack])
                Pval=sol['P'] if sol['cap_slack']<=1e-6 else math.inf
                rec['rmp_milp_P']=Pval; rec['rmp_milp_status']=int(milp_res.status)
                if Pval < bestP-1e-8:
                    bestP=Pval; bestsol=sol
        x=lp_res.x; V=ins['V']
        # check z integrality
        z=x[:len(cols)]
        frac_z=[(ci,float(val)) for ci,val in enumerate(z) if 1e-6<val<1-1e-6]
        yvals=[x[builder.y[i]] for i in range(1,V+1)]
        frac_y=[(i+1,float(v),abs(v-round(v))) for i,v in enumerate(yvals) if abs(v-round(v))>1e-6]
        if not frac_y and not frac_z:
            sol=reconstruct_master_solution(ins, cols, builder, x, lam=lam); sol['cap_slack']=0.0
            if sol['P'] < bestP-1e-8:
                bestP=sol['P']; bestsol=sol
            pruned+=1; rec['prune']='integral_lp'; node_logs.append(rec); continue
        # Branch
        children=[]
        if frac_y:
            # choose largest fractional inventory, preferring high objective sensitivity weight/target
            i,v,fr=max(frac_y, key=lambda t: t[2])
            fl=math.floor(v); ce=math.ceil(v)
            # left y_i <= floor(v)
            if node.y_lb.get(i,0) <= fl:
                yub=dict(node.y_ub); yub[i]=min(yub.get(i,ins['capacities'][i]),fl)
                if node.y_lb.get(i,0) <= yub[i]:
                    children.append(BPNode(next_id,node.depth+1,dict(node.y_lb),yub,dict(node.station_lb),dict(node.station_ub))); next_id+=1
            # right y_i >= ceil(v)
            if ce <= node.y_ub.get(i,ins['capacities'][i]):
                ylb=dict(node.y_lb); ylb[i]=max(ylb.get(i,0),ce)
                if ylb[i] <= node.y_ub.get(i,ins['capacities'][i]):
                    children.append(BPNode(next_id,node.depth+1,ylb,dict(node.y_ub),dict(node.station_lb),dict(node.station_ub))); next_id+=1
            rec['branch']=f'y_{i} <= {fl} / >= {ce}'
        else:
            # branch on fractional station service if available
            u=[]
            for i in range(1,V+1):
                val=sum(z[ci] for ci,c in enumerate(cols) if c.visitmask & (1<<(i-1)))
                if 1e-6<val<1-1e-6: u.append((i,float(val),abs(val-0.5)))
            if u:
                i,val,_=min(u,key=lambda t:t[2])
                # u_i=0 and u_i=1
                sub=dict(node.station_ub); sub[i]=0
                if node.station_lb.get(i,0)<=0:
                    children.append(BPNode(next_id,node.depth+1,dict(node.y_lb),dict(node.y_ub),dict(node.station_lb),sub)); next_id+=1
                slb=dict(node.station_lb); slb[i]=1
                if slb[i] <= node.station_ub.get(i,1):
                    children.append(BPNode(next_id,node.depth+1,dict(node.y_lb),dict(node.y_ub),slb,dict(node.station_ub))); next_id+=1
                rec['branch']=f'u_{i}=0/1'
            else:
                # Fallback unresolved: z fractional but no compatible branch implemented.
                unresolved+=1; rec['prune']='fractional_z_no_branch'; node_logs.append(rec); break
        rec['children']=len(children)
        node_logs.append(rec)
        # Add children; simple best-bound: solve order not known yet, so LIFO with deeper first.
        active.extend(children)
    status='optimal' if not active and unresolved==0 else ('time_limit' if time.time()-start>=total_time else 'unresolved')
    return {'status':status,'gcap':gcap,'time':time.time()-start,'processed_nodes':processed,'active_nodes':len(active),
            'pruned':pruned,'unresolved':unresolved,'ncols':len(cols),'bestP':bestP,'best_solution':bestsol,
            'node_logs':node_logs[-50:]}

def minimal_seed_columns(ins: Dict[str,Any], T=3600, taup=60, taud=60, q_cap=8) -> List[Column]:
    V=ins['V']; Q=max(ins['Q']); Y0=ins['initial']; C=ins['capacities']; dist=ins['distances']; cunit=taup+taud
    cols=[]; seen=set()
    def add(path, qlist):
        col=make_col(tuple(path), tuple(qlist), ins, taup, taud)
        if col.time <= T+1e-9 and col.signature not in seen:
            seen.add(col.signature); cols.append(col)
    # Include all single-station pickup quantities up to q_cap and all target-oriented pair transfers up to q_cap.
    for i in range(1,V+1):
        maxq=min(Y0[i], Q, int((T-dist[0][i]-dist[i][0])//cunit), q_cap)
        for q in range(1,maxq+1):
            ql=[0]*V; ql[i-1]=q; add([i],ql)
    for i in range(1,V+1):
        for j in range(1,V+1):
            if i==j: continue
            travel=dist[0][i]+dist[i][j]+dist[j][0]
            maxp=min(Y0[i], Q, int((T-travel)//cunit), q_cap)
            maxd=min(C[j]-Y0[j], Q, q_cap)
            for q in range(1,min(maxp,maxd)+1):
                ql=[0]*V; ql[i-1]=q; ql[j-1]=-q; add([i,j],ql)
    return cols
