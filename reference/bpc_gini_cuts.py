"""
GF-RL-BPC with subset-row cuts and pair co-route branching.
This is a research prototype extending bpc_gini_frontier.py.
It solves fixed Gini-cap subproblems min P s.t. G<=gamma with an exact
route-load column-generation LP at each branch node.
"""
from __future__ import annotations
import os, sys, time, math, itertools, json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Any, Optional
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack

# import base code safely
import importlib.util
_spec=importlib.util.spec_from_file_location('bpc_base','/mnt/data/bpc_gini_frontier.py')
bpc_base=importlib.util.module_from_spec(_spec); sys.modules['bpc_base']=bpc_base; _spec.loader.exec_module(bpc_base)
parse_instance=bpc_base.parse_instance
Column=bpc_base.Column
make_col=bpc_base.make_col
eval_y=bpc_base.eval_y
minimal_seed_columns=bpc_base.minimal_seed_columns
reconstruct_master_solution=bpc_base.reconstruct_master_solution

@dataclass
class CutNode:
    node_id: int
    depth: int
    y_lb: Dict[int,int] = field(default_factory=dict)
    y_ub: Dict[int,int] = field(default_factory=dict)
    station_lb: Dict[int,int] = field(default_factory=dict)
    station_ub: Dict[int,int] = field(default_factory=dict)
    pair_lb: Dict[Tuple[int,int],int] = field(default_factory=dict)  # co-route pair variable >= 0/1
    pair_ub: Dict[Tuple[int,int],int] = field(default_factory=dict)  # co-route pair variable <= 0/1

class CutMasterBuilder:
    def __init__(self, ins: Dict[str,Any], columns: List[Column], gcap: float, lam=0.15,
                 artificial_penalty=1e5, node: Optional[CutNode]=None,
                 sr_cuts: Optional[List[Tuple[int,int,int]]]=None):
        self.ins=ins; self.columns=columns; self.gcap=gcap; self.lam=lam; self.penalty=artificial_penalty
        self.node=node or CutNode(0,0)
        self.sr_cuts=sr_cuts or []
        self.V=ins['V']; self.pairs=[(i,j) for i in range(1,self.V+1) for j in range(i+1,self.V+1)]
        self.ncol=len(columns); self.names=[]; self.z=list(range(self.ncol)); self.names=[f'z_{c}' for c in range(self.ncol)]
        self.y={}; self.r={}; self.e={}; self.h={}
        self._build_indices()
    def _add(self,name):
        idx=len(self.names); self.names.append(name); return idx
    def _build_indices(self):
        V=self.V
        self.y={i:self._add(f'y_{i}') for i in range(1,V+1)}
        self.r={i:self._add(f'r_{i}') for i in range(1,V+1)}
        self.e={i:self._add(f'e_{i}') for i in range(1,V+1)}
        self.h={(i,j):self._add(f'h_{i}_{j}') for i,j in self.pairs}
        self.S=self._add('S'); self.H=self._add('H'); self.cap_slack=self._add('cap_slack')
    def build_lp(self):
        ins=self.ins; V=self.V; Capa=ins['capacities']; Y0=ins['initial']; target=ins['target']; w=ins['weights']
        n=len(self.names); c=np.zeros(n)
        for i in range(1,V+1): c[self.e[i]]=w[i]
        c[self.cap_slack]=self.penalty
        lb=np.zeros(n); ub=np.full(n,np.inf)
        # column z bounds
        for ci in range(self.ncol): lb[ci]=0; ub[ci]=1
        # variable bounds
        for i in range(1,V+1):
            lb[self.y[i]]=self.node.y_lb.get(i,0); ub[self.y[i]]=self.node.y_ub.get(i,Capa[i])
            lb[self.r[i]]=0; ub[self.r[i]]=Capa[i]/target[i]
            lb[self.e[i]]=0; ub[self.e[i]]=max(1.0,abs(Capa[i]/target[i]-1.0))
        ub[self.S]=sum(Capa[i]/target[i] for i in range(1,V+1))
        ub[self.H]=sum(max(Capa[i]/target[i],Capa[j]/target[j]) for i,j in self.pairs)
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
        add_ub({ci:1 for ci in range(self.ncol)},ins['M'],'vehicle')
        # station packing and branching
        for i in range(1,V+1):
            co={ci:1 for ci,col in enumerate(self.columns) if col.visitmask & (1<<(i-1))}
            add_ub(co,self.node.station_ub.get(i,1),f'station_{i}')
            if self.node.station_lb.get(i,0)>0:
                add_ub({idx:-val for idx,val in co.items()},-float(self.node.station_lb[i]),f'station_lb_{i}')
        # co-route pair branching constraints
        for (i,j),ubv in sorted(self.node.pair_ub.items()):
            co={ci:1 for ci,col in enumerate(self.columns) if (col.visitmask&(1<<(i-1))) and (col.visitmask&(1<<(j-1)))}
            add_ub(co,float(ubv),f'pair_ub_{i}_{j}')
        for (i,j),lbv in sorted(self.node.pair_lb.items()):
            co={ci:-1 for ci,col in enumerate(self.columns) if (col.visitmask&(1<<(i-1))) and (col.visitmask&(1<<(j-1)))}
            add_ub(co,-float(lbv),f'pair_lb_{i}_{j}')
        # subset-row cuts for triples: sum floor(|S cap route|/2) z <= 1. For |S|=3 coeff is 1 iff route covers >=2.
        for (a,b,c3) in self.sr_cuts:
            mask=(1<<(a-1))|(1<<(b-1))|(1<<(c3-1))
            co={ci:1 for ci,col in enumerate(self.columns) if ((col.visitmask & mask).bit_count()>=2)}
            add_ub(co,1.0,f'sr_{a}_{b}_{c3}')
        # inventory equations
        for i in range(1,V+1):
            co={self.y[i]:1}
            for ci,col in enumerate(self.columns):
                di=col.delta[i-1]
                if di: co[ci]=co.get(ci,0)-di
            add_eq(co,Y0[i],f'inventory_{i}')
        # ratios and penalty
        for i in range(1,V+1):
            add_eq({self.r[i]:1,self.y[i]:-1.0/target[i]},0,f'ratio_{i}')
            add_ub({self.r[i]:1,self.e[i]:-1},1,f'e_pos_{i}')
            add_ub({self.r[i]:-1,self.e[i]:-1},-1,f'e_neg_{i}')
        for i,j in self.pairs:
            add_ub({self.r[i]:1,self.r[j]:-1,self.h[i,j]:-1},0,f'h1_{i}_{j}')
            add_ub({self.r[i]:-1,self.r[j]:1,self.h[i,j]:-1},0,f'h2_{i}_{j}')
        co={self.S:-1}
        for i in range(1,V+1): co[self.r[i]]=co.get(self.r[i],0)+1
        add_eq(co,0,'S_def')
        co={self.H:-1}
        for ij in self.pairs: co[self.h[ij]]=co.get(self.h[ij],0)+1
        add_eq(co,0,'H_def')
        add_ub({self.H:1,self.S:-V*self.gcap,self.cap_slack:-1},0,'gcap')
        A_ub=vstack(Aub).tocsr() if Aub else None; A_eq=vstack(Aeq).tocsr() if Aeq else None
        return c,A_ub,np.array(bub),A_eq,np.array(beq),[(lb[i],ub[i]) for i in range(n)],row_names,eq_names
    def solve_lp(self):
        c,Aub,bub,Aeq,beq,bounds,row_names,eq_names=self.build_lp()
        res=linprog(c,A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs',options={'presolve':True})
        return res,row_names,eq_names
    def solve_milp_generated(self,time_limit=60,verbose=False):
        c,Aub,bub,Aeq,beq,bounds,row_names,eq_names=self.build_lp()
        rows=[]; lows=[]; ups=[]
        if Aub is not None: rows.append(Aub); lows += [-np.inf]*Aub.shape[0]; ups += list(bub)
        if Aeq is not None: rows.append(Aeq); lows += list(beq); ups += list(beq)
        A=vstack(rows).tocsr(); lb=np.array([b[0] for b in bounds]); ub=np.array([b[1] for b in bounds])
        integrality=np.zeros(len(bounds),dtype=int)
        for ci in range(self.ncol): integrality[ci]=1
        for i in range(1,self.V+1): integrality[self.y[i]]=1
        res=milp(c,integrality=integrality,bounds=Bounds(lb,ub),constraints=LinearConstraint(A,np.array(lows),np.array(ups)),
                 options={'time_limit':time_limit,'mip_rel_gap':1e-9,'disp':verbose,'presolve':True})
        return res,row_names,eq_names

# Label pricing with cut duals.
def _dominates(a,b,eps=1e-10):
    return a.travel <= b.travel+eps and a.cost <= b.cost+eps

@dataclass
class PLabel:
    mask:int; last:int; load:int; pick:int; travel:float; cost:float; path:Tuple[int,...]; q:Tuple[int,...]

def price_columns_with_cuts(ins:Dict[str,Any], mu:float, pi:np.ndarray, sigma:np.ndarray, existing:Set[Tuple],
                            T=3600,taup=60,taud=60,Q:Optional[int]=None,max_return_cols=80,
                            forbidden_stations:Set[int]=set(), forbidden_pairs:Set[Tuple[int,int]]=set(),
                            pair_duals:Dict[Tuple[int,int],float]=None, sr_duals:Dict[Tuple[int,int,int],float]=None,
                            label_limit:Optional[int]=None):
    V=ins['V']; Y0=ins['initial']; C=ins['capacities']; dist=ins['distances']; cunit=taup+taud
    if Q is None: Q=max(ins['Q'])
    pair_duals=pair_duals or {}; sr_duals=sr_duals or {}
    start=PLabel(0,0,0,0,0.0,0.0,tuple(),tuple([0]*V))
    labels={(0,0,0,0):[start]}; stack=[start]
    import heapq
    heap=[]; counter=0; best_rc=math.inf; expanded=generated=pruned_dom=0
    fbits={i:1<<(i-1) for i in range(1,V+1)}
    forbidden_pair_masks={i:0 for i in range(1,V+1)}
    for i,j in forbidden_pairs:
        forbidden_pair_masks[i] |= fbits[j]; forbidden_pair_masks[j] |= fbits[i]
    while stack:
        lab=stack.pop(); expanded+=1
        if lab.path:
            total_time=lab.travel+dist[lab.last][0]+cunit*lab.pick
            if total_time<=T+1e-9:
                adj=0.0
                if pair_duals:
                    for (i,j),dual in pair_duals.items():
                        if (lab.mask&fbits[i]) and (lab.mask&fbits[j]): adj -= dual
                if sr_duals:
                    for tri,dual in sr_duals.items():
                        cnt=(lab.mask & (fbits[tri[0]]|fbits[tri[1]]|fbits[tri[2]])).bit_count()
                        if cnt>=2: adj -= dual
                rc=lab.cost - mu + adj
                if rc<best_rc: best_rc=rc
                if rc < -1e-8:
                    col=make_col(lab.path,lab.q,ins,taup,taud)
                    if col.signature not in existing:
                        counter+=1; item=(-rc,counter,col)
                        if len(heap)<max_return_cols: heapq.heappush(heap,item)
                        elif item[0]>heap[0][0]: heapq.heapreplace(heap,item)
        if label_limit is not None and expanded>label_limit:
            break
        for i in range(1,V+1):
            bit=fbits[i]
            if lab.mask & bit: continue
            if i in forbidden_stations: continue
            if forbidden_pair_masks[i] & lab.mask: continue
            tr2=lab.travel+dist[lab.last][i]
            if tr2+dist[i][0]+cunit*lab.pick>T+1e-9: continue
            rem_pick_budget=int(math.floor((T-tr2-dist[i][0])/cunit+1e-9))
            maxp=min(Y0[i],Q-lab.load,rem_pick_budget-lab.pick)
            if maxp>0:
                for qv in range(1,maxp+1):
                    ql=list(lab.q); ql[i-1]=qv; qtuple=tuple(ql)
                    nl=PLabel(lab.mask|bit,i,lab.load+qv,lab.pick+qv,tr2,lab.cost-pi[i]-sigma[i]*qv,lab.path+(i,),qtuple)
                    key=(nl.mask,nl.last,nl.load,nl.pick); lst=labels.get(key,[])
                    if any(_dominates(old,nl) for old in lst): pruned_dom+=1; continue
                    labels[key]=[old for old in lst if not _dominates(nl,old)]+[nl]; stack.append(nl); generated+=1
            maxd=min(C[i]-Y0[i],lab.load)
            if maxd>0:
                for dval in range(1,maxd+1):
                    ql=list(lab.q); ql[i-1]=-dval; qtuple=tuple(ql)
                    nl=PLabel(lab.mask|bit,i,lab.load-dval,lab.pick,tr2,lab.cost-pi[i]+sigma[i]*dval,lab.path+(i,),qtuple)
                    key=(nl.mask,nl.last,nl.load,nl.pick); lst=labels.get(key,[])
                    if any(_dominates(old,nl) for old in lst): pruned_dom+=1; continue
                    labels[key]=[old for old in lst if not _dominates(nl,old)]+[nl]; stack.append(nl); generated+=1
    cols=[it[2] for it in sorted(heap,reverse=True)]
    stats={'expanded':expanded,'generated':generated,'states':len(labels),'labels_kept':sum(len(v) for v in labels.values()),'pruned_dom':pruned_dom,'best_rc':best_rc,'returned':len(cols),'terminated_by_limit':label_limit is not None and expanded>label_limit}
    return best_rc,cols,stats

def duals_from_lp(ins,row_names,eq_names,lp_res,sr_cuts):
    V=ins['V']; ubm=lp_res.ineqlin.marginals; eqm=lp_res.eqlin.marginals
    mu=ubm[row_names.index('vehicle')]
    pi=np.zeros(V+1); sigma=np.zeros(V+1)
    for i in range(1,V+1):
        val=ubm[row_names.index(f'station_{i}')]
        nm=f'station_lb_{i}'
        if nm in row_names: val -= ubm[row_names.index(nm)]
        pi[i]=val; sigma[i]=eqm[eq_names.index(f'inventory_{i}')]
    pair_duals={}
    for nm,dual in zip(row_names,ubm):
        if nm.startswith('pair_ub_'):
            _,_,a,b=nm.split('_'); key=(int(a),int(b)); pair_duals[key]=pair_duals.get(key,0.0)+dual
        elif nm.startswith('pair_lb_'):
            _,_,a,b=nm.split('_'); key=(int(a),int(b)); pair_duals[key]=pair_duals.get(key,0.0)-dual
    sr_duals={}
    for tri in sr_cuts:
        nm=f'sr_{tri[0]}_{tri[1]}_{tri[2]}'
        if nm in row_names: sr_duals[tri]=ubm[row_names.index(nm)]
    return mu,pi,sigma,pair_duals,sr_duals

def separate_sr_cuts(ins, cols, x, existing_cuts:Set[Tuple[int,int,int]], max_add=10, tol=1e-6):
    V=ins['V']; z=x[:len(cols)]; viol=[]
    for tri in itertools.combinations(range(1,V+1),3):
        if tri in existing_cuts: continue
        mask=sum(1<<(i-1) for i in tri)
        lhs=sum(z[ci] for ci,c in enumerate(cols) if ((c.visitmask&mask).bit_count()>=2))
        if lhs>1+tol: viol.append((lhs-1,tri,lhs))
    viol.sort(reverse=True,key=lambda t:t[0])
    return [(tri,lhs) for _,tri,lhs in viol[:max_add]]

def solve_node(ins, cols, seen, node:CutNode, gcap, sr_cuts, lam=0.15,T=3600,taup=60,taud=60,
               node_time=60,max_cg_iter=60,max_cols_per_iter=80,separate_sr=True,max_sr_rounds=3,verbose=False):
    start=time.time(); logs=[]; lp_res=None; builder=None; row_names=[]; eq_names=[]
    # local SR cut separation loop interleaved with CG
    sr_set=set(sr_cuts)
    sr_rounds=0
    for it in range(max_cg_iter):
        if time.time()-start>=node_time: break
        builder=CutMasterBuilder(ins,cols,gcap,lam,node=node,sr_cuts=list(sr_set))
        lp_res,row_names,eq_names=builder.solve_lp()
        if not lp_res.success:
            return {'status':'lp_fail','lp_success':False,'message':lp_res.message,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs}
        # Separate SR cuts before pricing if violated.
        if separate_sr and sr_rounds<max_sr_rounds:
            new=separate_sr_cuts(ins,cols,lp_res.x,sr_set,max_add=10,tol=1e-5)
            if new:
                for tri,lhs in new: sr_set.add(tri)
                sr_rounds+=1
                logs.append({'iter':it+1,'event':'add_sr','added':len(new),'max_lhs':float(new[0][1]),'n_sr':len(sr_set),'lp_obj':float(lp_res.fun)})
                continue
        mu,pi,sigma,pair_duals,sr_duals=duals_from_lp(ins,row_names,eq_names,lp_res,list(sr_set))
        forbidden_stations={i for i,u in node.station_ub.items() if u<=0}
        forbidden_pairs={p for p,u in node.pair_ub.items() if u<=0}
        best_rc,newcols,stats=price_columns_with_cuts(ins,mu,pi,sigma,set(c.signature for c in cols),T,taup,taud,Q=max(ins['Q']),
                                                      max_return_cols=max_cols_per_iter,forbidden_stations=forbidden_stations,
                                                      forbidden_pairs=forbidden_pairs,pair_duals=pair_duals,sr_duals=sr_duals)
        added=0
        for c in newcols:
            # duplicates may be okay but avoid them for stability
            if c.signature not in seen:
                seen.add(c.signature); cols.append(c); added+=1
        logs.append({'iter':it+1,'event':'pricing','lp_obj':float(lp_res.fun),'cap_slack':float(lp_res.x[builder.cap_slack]),'ncols':len(cols),'n_sr':len(sr_set),'best_rc':float(best_rc),'added':added,**stats})
        if verbose: print('node',node.node_id,logs[-1],flush=True)
        if stats.get('terminated_by_limit'):
            return {'status':'pricing_limit','lp_success':True,'lp_certified':False,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs,'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}
        if best_rc>=-1e-7 or added==0:
            return {'status':'ok','lp_success':True,'lp_certified':True,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs,'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}
    return {'status':'time','lp_success':lp_res is not None,'lp_certified':False,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs,'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}

def choose_branch(ins,cols,builder,x,node:CutNode):
    V=ins['V']; z=x[:len(cols)]
    # First: pair co-route branching on fractional b_ij = sum columns containing both i,j.
    cand=[]
    for i,j in itertools.combinations(range(1,V+1),2):
        if node.pair_lb.get((i,j),0)==1 or node.pair_ub.get((i,j),1)==0: continue
        val=sum(z[ci] for ci,c in enumerate(cols) if (c.visitmask&(1<<(i-1))) and (c.visitmask&(1<<(j-1))))
        if 1e-6<val<1-1e-6: cand.append((abs(val-0.5),i,j,float(val)))
    if cand:
        _,i,j,val=min(cand,key=lambda t:t[0])
        # child A: b_ij <=0; child B: b_ij >=1
        pub=dict(node.pair_ub); pub[(i,j)]=0
        plb=dict(node.pair_lb); plb[(i,j)]=1
        c0=CutNode(-1,node.depth+1,dict(node.y_lb),dict(node.y_ub),dict(node.station_lb),dict(node.station_ub),dict(node.pair_lb),pub)
        c1=CutNode(-1,node.depth+1,dict(node.y_lb),dict(node.y_ub),dict(node.station_lb),dict(node.station_ub),plb,dict(node.pair_ub))
        return f'pair_{i}_{j}={val:.3f} -> 0/1',[c0,c1]
    # Second: final inventory branch
    frac=[]
    for i in range(1,V+1):
        v=x[builder.y[i]]
        if abs(v-round(v))>1e-6: frac.append((abs(v-round(v)),i,float(v)))
    if frac:
        _,i,v=max(frac,key=lambda t:t[0]); fl=math.floor(v); ce=math.ceil(v); children=[]
        if node.y_lb.get(i,0)<=fl:
            yub=dict(node.y_ub); yub[i]=min(yub.get(i,ins['capacities'][i]),fl)
            if node.y_lb.get(i,0)<=yub[i]: children.append(CutNode(-1,node.depth+1,dict(node.y_lb),yub,dict(node.station_lb),dict(node.station_ub),dict(node.pair_lb),dict(node.pair_ub)))
        if ce<=node.y_ub.get(i,ins['capacities'][i]):
            ylb=dict(node.y_lb); ylb[i]=max(ylb.get(i,0),ce)
            if ylb[i]<=node.y_ub.get(i,ins['capacities'][i]): children.append(CutNode(-1,node.depth+1,ylb,dict(node.y_ub),dict(node.station_lb),dict(node.station_ub),dict(node.pair_lb),dict(node.pair_ub)))
        return f'y_{i}={v:.3f} -> <= {fl}/>= {ce}',children
    # Third: station service branch
    u=[]
    for i in range(1,V+1):
        val=sum(z[ci] for ci,c in enumerate(cols) if c.visitmask&(1<<(i-1)))
        if 1e-6<val<1-1e-6: u.append((abs(val-0.5),i,float(val)))
    if u:
        _,i,val=min(u,key=lambda t:t[0]); children=[]
        sub=dict(node.station_ub); sub[i]=0
        if node.station_lb.get(i,0)<=0: children.append(CutNode(-1,node.depth+1,dict(node.y_lb),dict(node.y_ub),dict(node.station_lb),sub,dict(node.pair_lb),dict(node.pair_ub)))
        slb=dict(node.station_lb); slb[i]=1
        if slb[i]<=node.station_ub.get(i,1): children.append(CutNode(-1,node.depth+1,dict(node.y_lb),dict(node.y_ub),slb,dict(node.station_ub),dict(node.pair_lb),dict(node.pair_ub)))
        return f'u_{i}={val:.3f} -> 0/1',children
    return 'no_branch',[]

def branch_price_cap_cuts(path_or_ins, gcap:float, lam=0.15,T=3600,taup=60,taud=60,total_time=300,node_time=60,max_nodes=1000,
                          seed_q_cap=8, verbose=False, incumbent_P:Optional[float]=None, rich_seed:bool=False):
    ins=parse_instance(path_or_ins) if isinstance(path_or_ins,str) else path_or_ins
    start=time.time(); cols=minimal_seed_columns(ins,T,taup,taud,q_cap=seed_q_cap)
    # Optional rich seed; default keeps the restricted master compact and lets pricing add columns.
    if rich_seed:
        try:
            extra=bpc_base.simple_seed_columns(ins,T,taup,taud,max_pair_q=seed_q_cap)
            cols += extra
        except Exception:
            pass
    seen=set(); uniq=[]
    for c in cols:
        if c.signature not in seen:
            seen.add(c.signature); uniq.append(c)
    cols=uniq
    bestP=incumbent_P if incumbent_P is not None else math.inf; bestsol=None
    root=CutNode(0,0); active=[root]; next_id=1; processed=0; pruned=0; unresolved=0; node_logs=[]; global_sr=[]
    best_open_lb=math.inf
    while active and time.time()-start<total_time and processed<max_nodes:
        node=active.pop()
        rem=total_time-(time.time()-start)
        nt=min(node_time,max(1,rem))
        res=solve_node(ins,cols,seen,node,gcap,global_sr,lam,T,taup,taud,node_time=nt,verbose=verbose)
        # update global SR cuts found at this node
        global_sr=list({tuple(c) for c in (global_sr+res.get('sr_cuts',[]))})
        processed+=1
        rec={'node':node.node_id,'depth':node.depth,'status':res['status'],'time':res['time'],'ncols':len(cols),'n_sr':len(global_sr)}
        if not res.get('lp_success'):
            pruned+=1; rec['prune']='lp_fail'; node_logs.append(rec); continue
        lp_res=res['lp_res']; builder=res['builder']; rec['lp_obj']=float(lp_res.fun); rec['cap_slack']=float(lp_res.x[builder.cap_slack]); rec['lp_certified']=res.get('lp_certified',False)
        if not res.get('lp_certified'):
            unresolved+=1; rec['prune']='pricing_unresolved'; node_logs.append(rec); break
        if lp_res.x[builder.cap_slack]>1e-6:
            pruned+=1; rec['prune']='cap_infeasible'; node_logs.append(rec); continue
        lb=float(lp_res.fun); best_open_lb=min(best_open_lb,lb)
        if lb>=bestP-1e-8:
            pruned+=1; rec['prune']='bound'; node_logs.append(rec); continue
        # restricted integer master for incumbent at each node but with short time.
        rem=total_time-(time.time()-start)
        if rem>1:
            milp_res,_,_=builder.solve_milp_generated(time_limit=min(15,rem),verbose=False)
            rec['rmp_milp_status']=int(milp_res.status) if milp_res is not None else None
            if milp_res.x is not None:
                sol=reconstruct_master_solution(ins,cols,builder,milp_res.x,lam=lam); sol['cap_slack']=float(milp_res.x[builder.cap_slack])
                if sol['cap_slack']<=1e-6 and sol['P']<bestP-1e-8:
                    bestP=sol['P']; bestsol=sol; rec['new_bestP']=bestP; rec['best_obj']=sol['obj']
        x=lp_res.x; z=x[:len(cols)]
        frac_z=[v for v in z if 1e-6<v<1-1e-6]
        frac_y=[x[builder.y[i]] for i in range(1,ins['V']+1) if abs(x[builder.y[i]]-round(x[builder.y[i]]))>1e-6]
        if not frac_z and not frac_y:
            sol=reconstruct_master_solution(ins,cols,builder,x,lam=lam); sol['cap_slack']=0.0
            if sol['P']<bestP-1e-8: bestP=sol['P']; bestsol=sol; rec['new_bestP']=bestP
            pruned+=1; rec['prune']='integral_lp'; node_logs.append(rec); continue
        branch,children=choose_branch(ins,cols,builder,x,node)
        if not children:
            unresolved+=1; rec['prune']='no_branch'; node_logs.append(rec); break
        for child in children:
            child.node_id=next_id; next_id+=1
        rec['branch']=branch; rec['children']=len(children); node_logs.append(rec)
        # Depth-first but visit b=1/served branches first often improves incumbents; reverse insertion keeps first child processed last.
        active.extend(children)
    status='optimal' if not active and unresolved==0 else ('time_limit' if time.time()-start>=total_time or processed>=max_nodes else 'unresolved')
    return {'instance':os.path.basename(ins['path']) if 'path' in ins else None,'status':status,'gcap':gcap,'time':time.time()-start,'processed_nodes':processed,'active_nodes':len(active),'pruned':pruned,'unresolved':unresolved,'ncols':len(cols),'n_sr':len(global_sr),'bestP':bestP,'best_solution':bestsol,'best_open_lb':best_open_lb,'node_logs':node_logs}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap',type=float,required=True); ap.add_argument('--time',type=float,default=300); ap.add_argument('--node-time',type=float,default=60); ap.add_argument('--verbose',action='store_true')
    args=ap.parse_args()
    out=branch_price_cap_cuts(args.file,args.cap,total_time=args.time,node_time=args.node_time,verbose=args.verbose)
    print(json.dumps(out,indent=2))

# --- MIP pricing with cut duals (defined after main block for import use) ---
def price_mip_column_with_cuts(ins:Dict[str,Any], mu:float, pi:np.ndarray, sigma:np.ndarray,
                               T=3600,taup=60,taud=60,time_limit=20,
                               forbidden_stations:Set[int]=set(), forbidden_pairs:Set[Tuple[int,int]]=set(),
                               pair_duals:Dict[Tuple[int,int],float]=None, sr_duals:Dict[Tuple[int,int,int],float]=None,
                               verbose=False):
    """Exact single-route pricing MIP including dual terms from co-route pair rows and 3-subset-row cuts."""
    pair_duals=pair_duals or {}; sr_duals=sr_duals or {}
    # Local variable builder compatible with base.
    VB=bpc_base.VB
    V=ins['V']; Q=max(ins['Q']); C=ins['capacities']; Y0=ins['initial']; dist=ins['distances']; cunit=taup+taud
    stations=range(1,V+1); nodes=range(V+1); maxpick=int(T//cunit)
    b=VB(); x={}; z={}; mode={}; p={}; d={}; L={}; u={}
    for i in nodes:
        for j in nodes:
            if i!=j: x[i,j]=b.add(f'x_{i}_{j}',binary=True)
    for i in stations:
        z[i]=b.add(f'z_{i}',binary=True); mode[i]=b.add(f'mode_{i}',binary=True)
        p[i]=b.add(f'p_{i}',lb=0,ub=min(Y0[i],Q,maxpick),integer=True)
        d[i]=b.add(f'd_{i}',lb=0,ub=min(C[i]-Y0[i],Q,maxpick),integer=True)
        L[i]=b.add(f'L_{i}',lb=0,ub=Q,integer=True); u[i]=b.add(f'u_{i}',lb=0,ub=V)
    bp={}
    for key in pair_duals:
        bp[key]=b.add(f'bpair_{key[0]}_{key[1]}',binary=True)
    bsr={}
    for tri in sr_duals:
        bsr[tri]=b.add(f'bsr_{tri[0]}_{tri[1]}_{tri[2]}',binary=True)
    n=len(b.names); rows=[]; lows=[]; ups=[]
    def add(co,lo=-np.inf,up=np.inf):
        row=lil_matrix((1,n))
        for idx,val in co.items():
            if abs(val)>1e-12: row[0,idx]=val
        rows.append(row.tocsr()); lows.append(lo); ups.append(up)
    # depot degree <=/== one: pricing should generate nonempty route exactly one departure/return
    add({x[0,j]:1 for j in stations},1,1); add({x[i,0]:1 for i in stations},1,1)
    for i in stations:
        add({**{x[i,j]:1 for j in nodes if j!=i}, z[i]:-1},0,0)
        add({**{x[j,i]:1 for j in nodes if j!=i}, z[i]:-1},0,0)
        add({mode[i]:1,z[i]:-1},-np.inf,0)
        up_p=min(Y0[i],Q,maxpick); up_d=min(C[i]-Y0[i],Q,maxpick)
        add({p[i]:1,mode[i]:-up_p},-np.inf,0)
        add({d[i]:1,z[i]:-up_d,mode[i]:up_d},-np.inf,0)
        add({p[i]:1,d[i]:1,z[i]:-1},0,np.inf)
        add({L[i]:1,z[i]:-Q},-np.inf,0)
        add({u[i]:1,z[i]:-V},-np.inf,0); add({u[i]:1,z[i]:-1},0,np.inf)
        if i in forbidden_stations: add({z[i]:1},0,0)
    # forbidden pair branches
    for i,j in forbidden_pairs:
        add({z[i]:1,z[j]:1},-np.inf,1)
    # MTZ subtour elimination
    for i in stations:
        for j in stations:
            if i!=j: add({u[i]:1,u[j]:-1,x[i,j]:V,z[j]:V},-np.inf,2*V-1)
    # load propagation
    big=Q+maxpick+5
    for i in stations:
        add({L[i]:1,p[i]:-1,d[i]:1,x[0,i]:big},-np.inf,big)
        add({L[i]:1,p[i]:-1,d[i]:1,x[0,i]:-big},-big,np.inf)
        for j in stations:
            if i!=j:
                add({L[j]:1,L[i]:-1,p[j]:-1,d[j]:1,x[i,j]:big},-np.inf,big)
                add({L[j]:1,L[i]:-1,p[j]:-1,d[j]:1,x[i,j]:-big},-big,np.inf)
    add({**{p[i]:1 for i in stations}, **{d[i]:-1 for i in stations}},0,np.inf)
    co={}
    for i in nodes:
        for j in nodes:
            if i!=j: co[x[i,j]]=co.get(x[i,j],0)+dist[i][j]
    for i in stations: co[p[i]]=co.get(p[i],0)+cunit
    add(co,-np.inf,T)
    # AND variables for pair duals: bpair = z_i AND z_j
    for (i,j),var in bp.items():
        add({var:1,z[i]:-1},-np.inf,0); add({var:1,z[j]:-1},-np.inf,0); add({var:1,z[i]:-1,z[j]:-1},-1,np.inf)
    # 3-subset-row coefficient variable: bsr=1 iff at least two stations in tri are visited.
    for tri,var in bsr.items():
        s={z[i]:1 for i in tri}
        add({var:1, **{z[i]:-0.5 for i in tri}}, -np.inf,0)  # b <= sum/2
        add({var:1, **{z[i]:-0.5 for i in tri}}, -0.5, np.inf) # b >= (sum-1)/2 -> b - .5sum >= -.5
    c=np.zeros(n)
    for i in stations:
        c[z[i]] += -pi[i]; c[p[i]] += -sigma[i]; c[d[i]] += sigma[i]
    for key,var in bp.items(): c[var] += -pair_duals[key]
    for tri,var in bsr.items(): c[var] += -sr_duals[tri]
    A=vstack(rows).tocsr(); cons=LinearConstraint(A,np.array(lows),np.array(ups)); bounds=Bounds(np.array(b.lb),np.array(b.ub))
    t0=time.time(); res=milp(c,integrality=np.array(b.integrality),bounds=bounds,constraints=cons,
                             options={'time_limit':time_limit,'mip_rel_gap':1e-9,'presolve':True,'disp':verbose})
    elapsed=time.time()-t0
    stats={'status':int(res.status),'success':bool(res.success),'fun':float(res.fun) if res.fun is not None else None,'time':elapsed,'gap':getattr(res,'mip_gap',None),'nodes':getattr(res,'mip_node_count',None)}
    if res.x is None:
        return None, math.inf, stats
    vals=res.x; q=[0]*V; arcs={}
    for i in stations: q[i-1]=int(round(vals[p[i]]))-int(round(vals[d[i]]))
    for i in nodes:
        for j in nodes:
            if i!=j and vals[x[i,j]]>0.5: arcs[i]=j
    path=[]; cur=0; seen_nodes=set()
    while cur in arcs and arcs[cur]!=0 and arcs[cur] not in seen_nodes:
        cur=arcs[cur]; path.append(cur); seen_nodes.add(cur)
    col=make_col(tuple(path),tuple(q),ins,taup,taud); rc=float(res.fun-mu)
    stats.update({'rc':rc,'path':path,'q':q,'time_route':col.time})
    return col,rc,stats

def solve_node_mippricing(ins, cols, seen, node:CutNode, gcap, sr_cuts, lam=0.15,T=3600,taup=60,taud=60,
                          node_time=60,max_cg_iter=40,pricing_time=15,separate_sr=True,max_sr_rounds=2,verbose=False):
    start=time.time(); logs=[]; lp_res=None; builder=None; row_names=[]; eq_names=[]; sr_set=set(sr_cuts); sr_rounds=0
    for it in range(max_cg_iter):
        if time.time()-start>=node_time: break
        builder=CutMasterBuilder(ins,cols,gcap,lam,node=node,sr_cuts=list(sr_set))
        lp_res,row_names,eq_names=builder.solve_lp()
        if not lp_res.success:
            return {'status':'lp_fail','lp_success':False,'message':lp_res.message,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs}
        if separate_sr and sr_rounds<max_sr_rounds:
            new=separate_sr_cuts(ins,cols,lp_res.x,sr_set,max_add=8,tol=1e-5)
            if new:
                for tri,lhs in new: sr_set.add(tri)
                sr_rounds+=1; logs.append({'iter':it+1,'event':'add_sr','added':len(new),'max_lhs':float(new[0][1]),'n_sr':len(sr_set),'lp_obj':float(lp_res.fun)})
                continue
        mu,pi,sigma,pair_duals,sr_duals=duals_from_lp(ins,row_names,eq_names,lp_res,list(sr_set))
        forbidden_stations={i for i,u in node.station_ub.items() if u<=0}; forbidden_pairs={p for p,u in node.pair_ub.items() if u<=0}
        rem=max(1,min(pricing_time,node_time-(time.time()-start)))
        col,rc,stats=price_mip_column_with_cuts(ins,mu,pi,sigma,T,taup,taud,time_limit=rem,forbidden_stations=forbidden_stations,forbidden_pairs=forbidden_pairs,pair_duals=pair_duals,sr_duals=sr_duals,verbose=False)
        added=0
        if col is not None and stats.get('success',False) and rc < -1e-7:
            cols.append(col); seen.add(col.signature); added=1
        logs.append({'iter':it+1,'event':'pricing_mip','lp_obj':float(lp_res.fun),'cap_slack':float(lp_res.x[builder.cap_slack]),'ncols':len(cols),'n_sr':len(sr_set),'rc':float(rc),'added':added,'pricing':stats})
        if verbose: print('node',node.node_id,logs[-1],flush=True)
        if not stats.get('success',False):
            return {'status':'pricing_fail','lp_success':True,'lp_certified':False,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs,'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}
        if rc>=-1e-7 or added==0:
            return {'status':'ok','lp_success':True,'lp_certified':True,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs,'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}
    return {'status':'time','lp_success':lp_res is not None,'lp_certified':False,'time':time.time()-start,'sr_cuts':list(sr_set),'logs':logs,'lp_res':lp_res,'builder':builder,'row_names':row_names,'eq_names':eq_names}

def branch_price_cap_cuts_mip(path_or_ins, gcap:float, lam=0.15,T=3600,taup=60,taud=60,total_time=300,node_time=60,max_nodes=1000,
                              seed_q_cap=8, verbose=False, incumbent_P:Optional[float]=None):
    ins=parse_instance(path_or_ins) if isinstance(path_or_ins,str) else path_or_ins
    start=time.time(); cols=minimal_seed_columns(ins,T,taup,taud,q_cap=seed_q_cap)
    seen=set(); uniq=[]
    for c in cols:
        if c.signature not in seen: seen.add(c.signature); uniq.append(c)
    cols=uniq; bestP=incumbent_P if incumbent_P is not None else math.inf; bestsol=None
    active=[CutNode(0,0)]; next_id=1; processed=pruned=unresolved=0; node_logs=[]; global_sr=[]; lb_values=[]
    while active and time.time()-start<total_time and processed<max_nodes:
        node=active.pop(); rem=total_time-(time.time()-start); nt=min(node_time,max(1,rem))
        res=solve_node_mippricing(ins,cols,seen,node,gcap,global_sr,lam,T,taup,taud,node_time=nt,verbose=verbose)
        global_sr=list({tuple(c) for c in (global_sr+res.get('sr_cuts',[]))})
        processed+=1; rec={'node':node.node_id,'depth':node.depth,'status':res['status'],'time':res['time'],'ncols':len(cols),'n_sr':len(global_sr)}
        if not res.get('lp_success'):
            pruned+=1; rec['prune']='lp_fail'; node_logs.append(rec); continue
        lp_res=res['lp_res']; builder=res['builder']; rec['lp_obj']=float(lp_res.fun); rec['cap_slack']=float(lp_res.x[builder.cap_slack]); rec['lp_certified']=res.get('lp_certified',False)
        if not res.get('lp_certified'):
            unresolved+=1; rec['prune']='pricing_unresolved'; node_logs.append(rec); break
        if lp_res.x[builder.cap_slack]>1e-6:
            pruned+=1; rec['prune']='cap_infeasible'; node_logs.append(rec); continue
        lb=float(lp_res.fun); lb_values.append(lb)
        if lb>=bestP-1e-8:
            pruned+=1; rec['prune']='bound'; node_logs.append(rec); continue
        rem=total_time-(time.time()-start)
        if rem>1 and (math.isinf(bestP) or node.depth==0):
            milp_res,_,_=builder.solve_milp_generated(time_limit=min(10,rem),verbose=False)
            rec['rmp_milp_status']=int(milp_res.status) if milp_res is not None else None
            if milp_res.x is not None:
                sol=reconstruct_master_solution(ins,cols,builder,milp_res.x,lam=lam); sol['cap_slack']=float(milp_res.x[builder.cap_slack])
                if sol['cap_slack']<=1e-6 and sol['P']<bestP-1e-8:
                    bestP=sol['P']; bestsol=sol; rec['new_bestP']=bestP; rec['best_obj']=sol['obj']
        x=lp_res.x; z=x[:len(cols)]
        if not any(1e-6<v<1-1e-6 for v in z) and not any(abs(x[builder.y[i]]-round(x[builder.y[i]]))>1e-6 for i in range(1,ins['V']+1)):
            sol=reconstruct_master_solution(ins,cols,builder,x,lam=lam); sol['cap_slack']=0.0
            if sol['P']<bestP-1e-8: bestP=sol['P']; bestsol=sol; rec['new_bestP']=bestP
            pruned+=1; rec['prune']='integral_lp'; node_logs.append(rec); continue
        branch,children=choose_branch(ins,cols,builder,x,node)
        if not children:
            unresolved+=1; rec['prune']='no_branch'; node_logs.append(rec); break
        for child in children: child.node_id=next_id; next_id+=1
        rec['branch']=branch; rec['children']=len(children); node_logs.append(rec); active.extend(children)
    status='optimal' if not active and unresolved==0 else ('time_limit' if time.time()-start>=total_time or processed>=max_nodes else 'unresolved')
    global_lb=min(lb_values) if lb_values else math.inf
    return {'instance':os.path.basename(ins['path']) if 'path' in ins else None,'status':status,'gcap':gcap,'time':time.time()-start,'processed_nodes':processed,'active_nodes':len(active),'pruned':pruned,'unresolved':unresolved,'ncols':len(cols),'n_sr':len(global_sr),'bestP':bestP,'best_solution':bestsol,'global_lb_processed_min':global_lb,'node_logs':node_logs}
