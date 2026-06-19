import math, time, re, ast, heapq, json, os
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack, csr_matrix


def parse_instance(path):
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


def precompute_tsp(V, dist):
    N=1<<V; INF=1e100
    dp=np.full((N,V), INF)
    for j in range(V): dp[1<<j,j]=dist[0][j+1]
    for mask in range(N):
        # iterate set bits as last
        for j in range(V):
            val=dp[mask,j]
            if val>=INF: continue
            rem=(N-1)^mask
            m=rem
            while m:
                lb=m & -m; k=lb.bit_length()-1; nm=mask|lb
                nv=val+dist[j+1][k+1]
                if nv<dp[nm,k]: dp[nm,k]=nv
                m-=lb
    tsp=np.zeros(N)
    for mask in range(1,N):
        best=INF; m=mask
        while m:
            lb=m & -m; j=lb.bit_length()-1
            val=dp[mask,j]+dist[j+1][0]
            if val<best: best=val
            m-=lb
        tsp[mask]=best
    return tsp


def S_bounds_reachable(ins,T=3600,taup=60,taud=60):
    # valid coarse bounds on S from at most M*floor(T/(taup+taud)) pickups.
    V=ins['V']; M=ins['M']; B=M*int(T//(taup+taud)); Y=ins['initial']; C=ins['capacities']; target=ins['target']
    inv=[0.0]+[1.0/target[i] for i in range(1,V+1)]
    S0=sum(Y[i]*inv[i] for i in range(1,V+1))
    units=sorted([(inv[i],Y[i]) for i in range(1,V+1)], reverse=True)
    rem=B; dec=0.0
    for val,cap in units:
        q=min(cap,rem); dec+=q*val; rem-=q
        if rem<=0: break
    Smin=max(0.0,S0-dec)
    sources=sorted([(inv[i],Y[i]) for i in range(1,V+1)])
    sinks=sorted([(inv[j],C[j]-Y[j]) for j in range(1,V+1)], reverse=True)
    si=tj=0; rem=B; inc=0.0
    while rem>0 and si<len(sources) and tj<len(sinks):
        sval,scap=sources[si]; tval,tcap=sinks[tj]
        if tval <= sval+1e-15: break
        q=min(scap,tcap,rem); inc += q*(tval-sval); rem-=q; scap-=q; tcap-=q
        if scap<=0: si+=1
        else: sources[si]=(sval,scap)
        if tcap<=0: tj+=1
        else: sinks[tj]=(tval,tcap)
    Smax=S0+inc
    return Smin,Smax,S0

class VB:
    def __init__(self): self.names=[]; self.lb=[]; self.ub=[]; self.integrality=[]
    def add(self,name,lb=0,ub=np.inf,integer=False,binary=False):
        idx=len(self.names); self.names.append(name)
        if binary: lb=0; ub=1; integ=1
        elif integer: integ=1
        else: integ=0
        self.lb.append(lb); self.ub.append(ub); self.integrality.append(integ); return idx


def build_solve_node(ins,tsp,Slo,Shi,lam=0.15,T=3600,taup=60,taud=60,time_limit=30,incumbent=None,verbose=False, use_subset=True, use_pairwise=True, extra_lorenz=None):
    V=ins['V']; M=ins['M']; Qs=ins['Q']; C=ins['capacities']; Y0=ins['initial']; target=ins['target']; wgt=ins['weights']; dist=ins['distances']
    stations=range(1,V+1); nodes=range(V+1); cunit=taup+taud
    b=VB(); x={}; z={}; mode={}; p={}; d={}; L={}; u={}; use={}
    # variable upper bounds
    maxpick_by_time=int(T//cunit)
    for k in range(M):
        use[k]=b.add(f'use_{k}',binary=True)
        for i in nodes:
            for j in nodes:
                if i!=j: x[k,i,j]=b.add(f'x_{k}_{i}_{j}',binary=True)
        for i in stations:
            z[k,i]=b.add(f'z_{k}_{i}',binary=True)
            mode[k,i]=b.add(f'mode_{k}_{i}',binary=True) # 1 pickup, 0 drop
            p[k,i]=b.add(f'p_{k}_{i}',lb=0,ub=min(Y0[i],Qs[k],maxpick_by_time),integer=True)
            d[k,i]=b.add(f'd_{k}_{i}',lb=0,ub=min(C[i]-Y0[i],Qs[k],maxpick_by_time),integer=True)
            L[k,i]=b.add(f'L_{k}_{i}',lb=0,ub=Qs[k],integer=True)
            u[k,i]=b.add(f'u_{k}_{i}',lb=0,ub=V,integer=False)
    y={}; r={}; e={}
    for i in stations:
        y[i]=b.add(f'y_{i}',lb=0,ub=C[i],integer=True)
        r[i]=b.add(f'r_{i}',lb=0,ub=C[i]/target[i])
        e[i]=b.add(f'e_{i}',lb=0,ub=max(1.0,abs(C[i]/target[i]-1.0)))
    S=b.add('S',lb=Slo,ub=Shi)
    H=b.add('H',lb=0,ub=sum(max(C[i]/target[i],C[j]/target[j]) for i in stations for j in stations if i<j))
    G=b.add('G',lb=0,ub=1)
    W=b.add('W',lb=0,ub=Shi) # W=G*S relaxation
    h={}
    if use_pairwise:
        for i in stations:
            for j in stations:
                if i<j: h[i,j]=b.add(f'h_{i}_{j}',lb=0,ub=max(C[i]/target[i],C[j]/target[j]))
    n=len(b.names); rows=[]; lows=[]; ups=[]
    def add(co,lo=-np.inf,up=np.inf):
        row=lil_matrix((1,n))
        for idx,val in co.items():
            if abs(val)>1e-12: row[0,idx]=val
        rows.append(row.tocsr()); lows.append(lo); ups.append(up)
    # routing constraints
    for k in range(M):
        # depot use
        add({**{x[k,0,j]:1 for j in stations}, use[k]:-1},0,0)
        add({**{x[k,i,0]:1 for i in stations}, use[k]:-1},0,0)
        for i in stations:
            add({**{x[k,i,j]:1 for j in nodes if j!=i}, z[k,i]:-1},0,0)
            add({**{x[k,j,i]:1 for j in nodes if j!=i}, z[k,i]:-1},0,0)
            add({z[k,i]:1,use[k]:-1},-np.inf,0)
            add({mode[k,i]:1,z[k,i]:-1},-np.inf,0)
            add({p[k,i]:1,mode[k,i]:-min(Y0[i],Qs[k],maxpick_by_time)},-np.inf,0)
            # if mode=0 and z=1, drop; if mode=1, d=0
            ub_d=min(C[i]-Y0[i],Qs[k],maxpick_by_time)
            add({d[k,i]:1,z[k,i]:-ub_d,mode[k,i]:ub_d},-np.inf,0)
            add({p[k,i]:1,d[k,i]:1,z[k,i]:-1},0,np.inf)
            add({L[k,i]:1,z[k,i]:-Qs[k]},-np.inf,0)
            add({u[k,i]:1,z[k,i]:-V},-np.inf,0)
            add({u[k,i]:1,z[k,i]:-1},0,np.inf)
        # MTZ (works with degree constraints to eliminate subtours)
        for i in stations:
            for j in stations:
                if i!=j:
                    add({u[k,i]:1,u[k,j]:-1,x[k,i,j]:V,z[k,j]:V},-np.inf,2*V-1)
        # load transition constraints
        Q=Qs[k]; big=Q+maxpick_by_time+5
        for i in stations:
            # arc depot->i: L_i = p_i - d_i; d_i must be 0 to be feasible if first, enforced by L lower plus equality
            add({L[k,i]:1,p[k,i]:-1,d[k,i]:1,x[k,0,i]:big},-np.inf,big)
            add({L[k,i]:1,p[k,i]:-1,d[k,i]:1,x[k,0,i]:-big},-big,np.inf)
            for j in stations:
                if i!=j:
                    add({L[k,j]:1,L[k,i]:-1,p[k,j]:-1,d[k,j]:1,x[k,i,j]:big},-np.inf,big)
                    add({L[k,j]:1,L[k,i]:-1,p[k,j]:-1,d[k,j]:1,x[k,i,j]:-big},-big,np.inf)
        # final load nonnegative automatically; total drops <= pickups valid/tightens
        co={}
        for i in stations:
            co[p[k,i]]=co.get(p[k,i],0)+1
            co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,0,np.inf)
        # exact time when taup,taud and depot unloading: (taup+taud) * total pickup + travel
        co={}
        for i in nodes:
            for j in nodes:
                if i!=j: co[x[k,i,j]]=co.get(x[k,i,j],0)+dist[i][j]
        for i in stations: co[p[k,i]]=co.get(p[k,i],0)+cunit
        add(co,-np.inf,T)
        # subset TSP cuts (only small V)
        if use_subset and V<=16:
            BIG=1e5
            for mask in range(1,1<<V):
                co={}; cnt=0; m=mask
                while m:
                    lb=m & -m; ii=lb.bit_length(); cnt+=1; m-=lb
                    co[p[k,ii]]=co.get(p[k,ii],0)+cunit
                    co[z[k,ii]]=co.get(z[k,ii],0)+BIG
                add(co,-np.inf,T-tsp[mask]+BIG*cnt)
    # vehicle symmetry: used vehicles packed, and lexicographic station mask nonincreasing
    for k in range(M-1):
        add({use[k]:1,use[k+1]:-1},0,np.inf)
        co={}
        for i in stations:
            co[z[k,i]]=co.get(z[k,i],0)+2**(i-1)
            co[z[k+1,i]]=co.get(z[k+1,i],0)-2**(i-1)
        add(co,0,np.inf)
    # station disjoint
    for i in stations:
        add({z[k,i]:1 for k in range(M)},-np.inf,1)
    # inventory/ratios/penalty
    Sco={S:-1}
    for i in stations:
        co={y[i]:1}
        for k in range(M):
            co[p[k,i]]=co.get(p[k,i],0)+1
            co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,Y0[i],Y0[i])
        add({r[i]:1,y[i]:-1.0/target[i]},0,0)
        add({e[i]:1,r[i]:-1},-1,np.inf)
        add({e[i]:1,r[i]:1},1,np.inf)
        Sco[r[i]]=Sco.get(r[i],0)+1
    add(Sco,0,0)
    # numerator H exact by pairwise abs, or by Lorenz cuts
    if use_pairwise:
        Hco={H:-1}
        for i in stations:
            for j in stations:
                if i<j:
                    add({h[i,j]:1,r[i]:-1,r[j]:1},0,np.inf)
                    add({h[i,j]:1,r[i]:1,r[j]:-1},0,np.inf)
                    Hco[h[i,j]]=Hco.get(h[i,j],0)+1
        add(Hco,0,0)
    else:
        # H >= permutation/ranking cuts. coefficients for ascending order.
        if extra_lorenz is None: extra_lorenz=[]
        coeffs=[2*(ell+1)-V-1 for ell in range(V)]
        # add a few deterministic cuts: increasing by current initial ratios and by target station index
        for perm in extra_lorenz:
            co={H:1}
            for rank,i in enumerate(perm): co[r[i]]=co.get(r[i],0)-coeffs[rank]
            add(co,0,np.inf)
    # McCormick relaxation for W=G*S on S in [Slo,Shi], G in [0,1]
    # w >= Slo*G; w >= Shi*G + S - Shi ; w <= Shi*G ; w <= Slo*G + S - Slo
    add({W:1,G:-Slo},0,np.inf)
    add({W:1,G:-Shi,S:-1},-Shi,np.inf)
    add({W:1,G:-Shi},-np.inf,0)
    add({W:1,G:-Slo,S:-1},-np.inf,-Slo)
    # W >= H/V
    add({W:1,H:-1.0/V},0,np.inf)
    # objective cutoff
    if incumbent is not None and math.isfinite(incumbent):
        co={G:1}
        for i in stations: co[e[i]]=co.get(e[i],0)+lam*wgt[i]
        add(co,-np.inf,incumbent-1e-10)
    c=np.zeros(n); c[G]=1.0
    for i in stations: c[e[i]] += lam*wgt[i]
    A=vstack(rows).tocsr(); cons=LinearConstraint(A,np.array(lows),np.array(ups)); bounds=Bounds(np.array(b.lb),np.array(b.ub))
    opts={'time_limit':time_limit,'mip_rel_gap':1e-9,'disp':verbose,'presolve':True}
    t0=time.time(); res=milp(c,integrality=np.array(b.integrality),bounds=bounds,constraints=cons,options=opts); elapsed=time.time()-t0
    return res,elapsed,b,(x,z,p,d,L,y,r,e,S,H,G,W)


def extract(ins,b,vars_tuple,sol,lam=0.15,T=3600,taup=60,taud=60):
    x,z,p,d,L,y,r,e,S,H,G,W=vars_tuple
    vals={name:sol[i] for i,name in enumerate(b.names)}
    V=ins['V']; M=ins['M']; stations=range(1,V+1); nodes=range(V+1)
    yv=[int(round(vals[f'y_{i}'])) for i in stations]
    rr=[yv[i-1]/ins['target'][i] for i in stations]
    Strue=sum(rr)
    Htrue=sum(abs(rr[i]-rr[j]) for i in range(V) for j in range(i+1,V))
    Gtrue=Htrue/(V*Strue) if Strue>0 else 0.0
    P=sum(ins['weights'][i]*abs(rr[i-1]-1.0) for i in stations)
    obj=Gtrue+lam*P
    routes=[]; pks=[]; dks=[]; travel=[]; op=[]; loads=[]
    for k in range(M):
        pv={i:int(round(vals.get(f'p_{k}_{i}',0))) for i in stations}
        dv={i:int(round(vals.get(f'd_{k}_{i}',0))) for i in stations}
        pks.append(pv); dks.append(dv)
        arcs={}
        for i in nodes:
            for j in nodes:
                if i!=j and vals.get(f'x_{k}_{i}_{j}',0)>0.5: arcs[i]=j
        route=[]; cur=0; seen=set()
        while cur in arcs and arcs[cur]!=0 and arcs[cur] not in seen:
            cur=arcs[cur]; route.append(cur); seen.add(cur)
        routes.append(route)
        tr=0.0; prev=0; ld=0; lseq=[]
        for node in route:
            tr += ins['distances'][prev][node]
            ld += pv[node]-dv[node]; lseq.append(ld)
            prev=node
        if route: tr += ins['distances'][prev][0]
        travel.append(tr)
        totalp=sum(pv.values()); totald=sum(dv.values())
        op.append(taup*totalp + taud*totald + taud*(totalp-totald))
        loads.append(lseq)
    return {'obj':obj,'G':Gtrue,'P':P,'S':Strue,'H':Htrue,'y':yv,'routes':routes,'p':pks,'d':dks,'travel':travel,'op':op,'loads':loads,
            'model_obj':float(np.dot(np.zeros(1),np.zeros(1))) if False else None,
            'Gvar':vals.get('G'), 'S_var': vals.get('S'), 'H_var': vals.get('H'), 'W_var': vals.get('W')}


def initial_noop(ins,lam=0.15):
    V=ins['V']; yv=[ins['initial'][i] for i in range(1,V+1)]
    rr=[yv[i-1]/ins['target'][i] for i in range(1,V+1)]; S=sum(rr); H=sum(abs(rr[i]-rr[j]) for i in range(V) for j in range(i+1,V))
    G=H/(V*S); P=sum(ins['weights'][i]*abs(rr[i-1]-1) for i in range(1,V+1))
    return {'obj':G+lam*P,'G':G,'P':P,'S':S,'H':H,'y':yv,'routes':[[] for _ in range(ins['M'])],'p':None,'d':None,'travel':[0]*ins['M'],'op':[0]*ins['M']}


def solve_spatial(path,lam=0.15,T=3600,taup=60,taud=60,node_time=30,total_time=300,tol=1e-6,verbose=False, use_pairwise=True):
    ins=parse_instance(path); tsp=precompute_tsp(ins['V'],ins['distances']) if ins['V']<=20 else None
    Smin,Smax,S0=S_bounds_reachable(ins,T,taup,taud)
    bestsol=initial_noop(ins,lam); best=bestsol['obj']
    pq=[]; counter=0; heapq.heappush(pq,(0.0,counter,Smin,Smax)); counter+=1
    start=time.time(); processed=0; solved=0; globalLB=0.0; logs=[]; timeouts=0
    while pq and time.time()-start < total_time:
        lbkey,_,lo,hi=heapq.heappop(pq)
        if lbkey >= best - tol:
            processed += 1; continue
        remaining=max(1.0,total_time-(time.time()-start))
        tl=min(node_time,remaining)
        res,el,b,vars_tuple=build_solve_node(ins,tsp,lo,hi,lam,T,taup,taud,time_limit=tl,incumbent=best,verbose=False,use_subset=(ins['V']<=16),use_pairwise=use_pairwise)
        solved += 1
        if res.x is None:
            # infeasible/cutoff/time with no solution. If optimal infeas/cutoff, prune; if time limit no x, cannot prune -> split.
            if res.status==1 and hi-lo>1e-5: # time limit
                db=getattr(res,'mip_dual_bound',lbkey)
                if db is None or not np.isfinite(db): db=lbkey
                mid=(lo+hi)/2
                heapq.heappush(pq,(db,counter,lo,mid)); counter+=1
                heapq.heappush(pq,(db,counter,mid,hi)); counter+=1
                timeouts += 1
            processed += 1
            if verbose: print('node no x',lo,hi,'status',res.status,'time',el,'queue',len(pq),'best',best)
            continue
        sol=extract(ins,b,vars_tuple,res.x,lam,T,taup,taud)
        if sol['obj'] < best - 1e-9:
            best=sol['obj']; bestsol=sol
            if verbose: print('new best',best,'G',sol['G'],'P',sol['P'],'S',sol['S'],'route',sol['routes'],'y',sol['y'])
        # Valid lower bound from relaxation if node solved or dual bound if not. res.fun is primal relaxation obj, dual bound is lower bound.
        nodeLB=res.fun if res.success else getattr(res,'mip_dual_bound',-math.inf)
        if nodeLB is None or not np.isfinite(nodeLB): nodeLB=-math.inf
        logs.append({'lo':lo,'hi':hi,'lb':nodeLB,'success':bool(res.success),'time':el,'cand_true':sol['obj'],'cand_model':res.fun,'S':sol['S']})
        if verbose:
            print('node',processed,'int',(lo,hi),'succ',res.success,'LB',nodeLB,'model',res.fun,'true',sol['obj'],'best',best,'gap',best-nodeLB,'S',sol['S'],'time',el,'q',len(pq))
        if nodeLB >= best - tol:
            processed += 1; continue
        # if interval is tiny, accept tolerance based on lower bound. Otherwise split.
        width=hi-lo
        if width <= 1e-7:
            # cannot improve bound with product branching; keep as residual with LB; if not pruned, global gap remains.
            heapq.heappush(pq,(nodeLB,counter,lo,hi)); counter+=1
            processed += 1
            break
        s=sol['S']
        # split at solution S if interior, otherwise midpoint
        if lo + 0.1*width < s < hi - 0.1*width:
            children=[(lo,s),(s,hi)]
        else:
            mid=(lo+hi)/2; children=[(lo,mid),(mid,hi)]
        for a,c_hi in children:
            if c_hi-a>1e-9:
                heapq.heappush(pq,(nodeLB,counter,a,c_hi)); counter+=1
        processed += 1
        globalLB=pq[0][0] if pq else best
        if verbose and processed%10==0:
            print('PROG proc',processed,'best',best,'LB',globalLB,'gap',best-globalLB,'queue',len(pq),'time',time.time()-start)
        if globalLB >= best - tol: break
    globalLB=pq[0][0] if pq else best
    status='optimal' if (not pq or globalLB >= best - tol) else 'time_limit'
    return {'status':status,'objective':best,'LB':globalLB,'gap':max(0,best-globalLB),'best':bestsol,'time':time.time()-start,'processed':processed,'solved':solved,'queue':len(pq),'Sbounds':(Smin,Smax,S0),'logs':logs[-20:]}

if __name__=='__main__':
    import sys
    ans=solve_spatial(sys.argv[1],node_time=float(sys.argv[2]) if len(sys.argv)>2 else 20,total_time=float(sys.argv[3]) if len(sys.argv)>3 else 300,verbose=True)
    print(json.dumps(ans,indent=2))
