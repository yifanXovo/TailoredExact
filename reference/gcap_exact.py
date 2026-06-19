import math, time, re, ast, os, json
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack


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
            val=dp[mask,j]+dist[j+1][0]
            if val<best: best=val
            m-=lb
        tsp[mask]=best
    return tsp

class VB:
    def __init__(self): self.names=[]; self.lb=[]; self.ub=[]; self.integrality=[]
    def add(self,name,lb=0,ub=np.inf,integer=False,binary=False):
        idx=len(self.names); self.names.append(name)
        if binary: lb=0; ub=1; integ=1
        elif integer: integ=1
        else: integ=0
        self.lb.append(lb); self.ub.append(ub); self.integrality.append(integ); return idx


def eval_y(ins,yv,lam=0.15):
    V=ins['V']; rr=[yv[i-1]/ins['target'][i] for i in range(1,V+1)]
    S=sum(rr); H=sum(abs(rr[i]-rr[j]) for i in range(V) for j in range(i+1,V))
    G=H/(V*S) if S>0 else 0.0
    P=sum(ins['weights'][i]*abs(rr[i-1]-1.0) for i in range(1,V+1))
    return G,P,G+lam*P,S,H


def no_op(ins,lam=0.15):
    yv=[ins['initial'][i] for i in range(1,ins['V']+1)]
    G,P,obj,S,H=eval_y(ins,yv,lam)
    return {'obj':obj,'G':G,'P':P,'S':S,'H':H,'y':yv,'routes':[[] for _ in range(ins['M'])], 'p':[], 'd':[], 'travel':[0]*ins['M'], 'op':[0]*ins['M']}


def build_solve_cap(ins,tsp,gcap,lam=0.15,T=3600,taup=60,taud=60,time_limit=30,verbose=False, incumbent_obj=None, use_subset=True, fixed_zero=None):
    V=ins['V']; M=ins['M']; Qs=ins['Q']; C=ins['capacities']; Y0=ins['initial']; target=ins['target']; w=ins['weights']; dist=ins['distances']
    stations=range(1,V+1); nodes=range(V+1); cunit=taup+taud; maxpick=int(T//cunit)
    b=VB(); x={}; use={}; z={}; mode={}; p={}; d={}; L={}; u={}
    for k in range(M):
        use[k]=b.add(f'use_{k}',binary=True)
        for i in nodes:
            for j in nodes:
                if i!=j: x[k,i,j]=b.add(f'x_{k}_{i}_{j}',binary=True)
        for i in stations:
            z[k,i]=b.add(f'z_{k}_{i}',binary=True)
            mode[k,i]=b.add(f'mode_{k}_{i}',binary=True)
            p[k,i]=b.add(f'p_{k}_{i}',lb=0,ub=min(Y0[i],Qs[k],maxpick),integer=True)
            d[k,i]=b.add(f'd_{k}_{i}',lb=0,ub=min(C[i]-Y0[i],Qs[k],maxpick),integer=True)
            L[k,i]=b.add(f'L_{k}_{i}',lb=0,ub=Qs[k],integer=True)
            u[k,i]=b.add(f'u_{k}_{i}',lb=0,ub=V)
    y={}; r={}; e={}
    for i in stations:
        y[i]=b.add(f'y_{i}',lb=0,ub=C[i],integer=True)
        r[i]=b.add(f'r_{i}',lb=0,ub=C[i]/target[i])
        e[i]=b.add(f'e_{i}',lb=0,ub=max(1.0,abs(C[i]/target[i]-1.0)))
    S=b.add('S',lb=0,ub=sum(C[i]/target[i] for i in stations))
    H=b.add('H',lb=0,ub=sum(max(C[i]/target[i],C[j]/target[j]) for i in stations for j in stations if i<j))
    h={}
    for i in stations:
        for j in stations:
            if i<j: h[i,j]=b.add(f'h_{i}_{j}',lb=0,ub=max(C[i]/target[i],C[j]/target[j]))
    n=len(b.names); rows=[]; lows=[]; ups=[]
    def add(co,lo=-np.inf,up=np.inf):
        row=lil_matrix((1,n))
        for idx,val in co.items():
            if abs(val)>1e-12: row[0,idx]=val
        rows.append(row.tocsr()); lows.append(lo); ups.append(up)
    # routing/load
    for k in range(M):
        add({**{x[k,0,j]:1 for j in stations}, use[k]:-1},0,0)
        add({**{x[k,i,0]:1 for i in stations}, use[k]:-1},0,0)
        for i in stations:
            add({**{x[k,i,j]:1 for j in nodes if j!=i}, z[k,i]:-1},0,0)
            add({**{x[k,j,i]:1 for j in nodes if j!=i}, z[k,i]:-1},0,0)
            add({z[k,i]:1,use[k]:-1},-np.inf,0)
            add({mode[k,i]:1,z[k,i]:-1},-np.inf,0)
            up_p=min(Y0[i],Qs[k],maxpick); up_d=min(C[i]-Y0[i],Qs[k],maxpick)
            add({p[k,i]:1,mode[k,i]:-up_p},-np.inf,0)
            add({d[k,i]:1,z[k,i]:-up_d,mode[k,i]:up_d},-np.inf,0)
            add({p[k,i]:1,d[k,i]:1,z[k,i]:-1},0,np.inf)
            add({L[k,i]:1,z[k,i]:-Qs[k]},-np.inf,0)
            add({u[k,i]:1,z[k,i]:-V},-np.inf,0)
            add({u[k,i]:1,z[k,i]:-1},0,np.inf)
        for i in stations:
            for j in stations:
                if i!=j:
                    add({u[k,i]:1,u[k,j]:-1,x[k,i,j]:V,z[k,j]:V},-np.inf,2*V-1)
        Q=Qs[k]; big=Q+maxpick+5
        for i in stations:
            add({L[k,i]:1,p[k,i]:-1,d[k,i]:1,x[k,0,i]:big},-np.inf,big)
            add({L[k,i]:1,p[k,i]:-1,d[k,i]:1,x[k,0,i]:-big},-big,np.inf)
            for j in stations:
                if i!=j:
                    add({L[k,j]:1,L[k,i]:-1,p[k,j]:-1,d[k,j]:1,x[k,i,j]:big},-np.inf,big)
                    add({L[k,j]:1,L[k,i]:-1,p[k,j]:-1,d[k,j]:1,x[k,i,j]:-big},-big,np.inf)
        co={}
        for i in stations: co[p[k,i]]=co.get(p[k,i],0)+1; co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,0,np.inf)
        co={}
        for i in nodes:
            for j in nodes:
                if i!=j: co[x[k,i,j]]=co.get(x[k,i,j],0)+dist[i][j]
        for i in stations: co[p[k,i]]=co.get(p[k,i],0)+cunit
        add(co,-np.inf,T)
        if use_subset and V<=16 and tsp is not None:
            BIG=1e5
            for mask in range(1,1<<V):
                co={}; cnt=0; m=mask
                while m:
                    lb=m & -m; ii=lb.bit_length(); cnt+=1; m-=lb
                    co[p[k,ii]]=co.get(p[k,ii],0)+cunit
                    co[z[k,ii]]=co.get(z[k,ii],0)+BIG
                add(co,-np.inf,T-tsp[mask]+BIG*cnt)
    # symmetry
    for k in range(M-1):
        add({use[k]:1,use[k+1]:-1},0,np.inf)
        co={}
        for i in stations:
            co[z[k,i]]=co.get(z[k,i],0)+2**(i-1)
            co[z[k+1,i]]=co.get(z[k+1,i],0)-2**(i-1)
        add(co,0,np.inf)
    for i in stations:
        add({z[k,i]:1 for k in range(M)},-np.inf,1)
    # inventory and objective terms
    Sco={S:-1}
    for i in stations:
        co={y[i]:1}
        for k in range(M): co[p[k,i]]=co.get(p[k,i],0)+1; co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,Y0[i],Y0[i])
        add({r[i]:1,y[i]:-1.0/target[i]},0,0)
        add({e[i]:1,r[i]:-1},-1,np.inf)
        add({e[i]:1,r[i]:1},1,np.inf)
        Sco[r[i]]=Sco.get(r[i],0)+1
    add(Sco,0,0)
    Hco={H:-1}
    for i in stations:
        for j in stations:
            if i<j:
                add({h[i,j]:1,r[i]:-1,r[j]:1},0,np.inf)
                add({h[i,j]:1,r[i]:1,r[j]:-1},0,np.inf)
                Hco[h[i,j]]=Hco.get(h[i,j],0)+1
    add(Hco,0,0)
    # Gini cap: H <= V*gcap*S
    add({H:1,S:-V*gcap},-np.inf,0)
    # optional objective cutoff P <= incumbent / lambda (or tighter using G>=0)
    if incumbent_obj is not None and math.isfinite(incumbent_obj) and lam>0:
        co={}
        for i in stations: co[e[i]]=co.get(e[i],0)+w[i]
        add(co,-np.inf,incumbent_obj/lam + 1e-9)
    if fixed_zero:
        # allow fixing some no-op? not used
        pass
    c=np.zeros(n)
    for i in stations: c[e[i]] += w[i]
    A=vstack(rows).tocsr(); cons=LinearConstraint(A,np.array(lows),np.array(ups)); bounds=Bounds(np.array(b.lb),np.array(b.ub))
    opts={'time_limit':time_limit,'mip_rel_gap':1e-9,'disp':verbose,'presolve':True}
    t0=time.time(); res=milp(c,integrality=np.array(b.integrality),bounds=bounds,constraints=cons,options=opts); elapsed=time.time()-t0
    return res,elapsed,b,(x,z,p,d,L,y,r,e,S,H,h)


def extract(ins,b,vars_tuple,sol,lam=0.15,T=3600,taup=60,taud=60):
    x,z,p,d,L,y,r,e,S,H,h=vars_tuple; vals={name:sol[i] for i,name in enumerate(b.names)}
    V=ins['V']; M=ins['M']; stations=range(1,V+1); nodes=range(V+1)
    yv=[int(round(vals[f'y_{i}'])) for i in stations]
    G,P,obj,Strue,Htrue=eval_y(ins,yv,lam)
    pks=[]; dks=[]; routes=[]; travel=[]; op=[]; loads=[]
    for k in range(M):
        pv={i:int(round(vals.get(f'p_{k}_{i}',0))) for i in stations}; dv={i:int(round(vals.get(f'd_{k}_{i}',0))) for i in stations}
        pks.append(pv); dks.append(dv)
        arcs={}
        for i in nodes:
            for j in nodes:
                if i!=j and vals.get(f'x_{k}_{i}_{j}',0)>0.5: arcs[i]=j
        route=[]; cur=0; seen=set();
        while cur in arcs and arcs[cur]!=0 and arcs[cur] not in seen:
            cur=arcs[cur]; route.append(cur); seen.add(cur)
        routes.append(route)
        tr=0.0; prev=0; ld=0; lseq=[]
        for node in route:
            tr+=ins['distances'][prev][node]; ld += pv[node]-dv[node]; lseq.append(ld); prev=node
        if route: tr+=ins['distances'][prev][0]
        travel.append(tr)
        totalp=sum(pv.values()); totald=sum(dv.values()); op.append(taup*totalp+taud*totald+taud*(totalp-totald)); loads.append(lseq)
    return {'obj':obj,'G':G,'P':P,'S':Strue,'H':Htrue,'y':yv,'routes':routes,'p':pks,'d':dks,'travel':travel,'op':op,'loads':loads,'P_model':sum(ins['weights'][i]*vals[f'e_{i}'] for i in stations)}


def solve_frontier(path,lam=0.15,T=3600,taup=60,taud=60,cap_time=60,total_time=600,tol=1e-7,verbose=False):
    ins=parse_instance(path); tsp=precompute_tsp(ins['V'],ins['distances']) if ins['V']<=20 else None
    best=no_op(ins,lam); UB=best['obj']; cap=1.0; start=time.time(); iterations=0; logs=[]; certLB=0.0
    # G cannot exceed UB because objective >=G; initial cap can be min(1, UB)
    cap=min(cap, UB)
    while cap>tol and time.time()-start<total_time:
        remaining=total_time-(time.time()-start)
        tl=max(1.0,min(cap_time,remaining))
        res,el,b,vars_tuple=build_solve_cap(ins,tsp,cap,lam,T,taup,taud,time_limit=tl,verbose=False,incumbent_obj=UB,use_subset=(ins['V']<=16))
        iterations += 1
        if res.x is None:
            if verbose: print('cap',cap,'no solution/status',res.status,'time',el)
            if res.status==2: # infeasible
                certLB=UB
                break
            # time limit no solution: not certified
            certLB=max(certLB, getattr(res,'mip_dual_bound',0) if hasattr(res,'mip_dual_bound') else 0)
            break
        # Need the MILP itself certified optimal for P*(cap). If time-limited, cannot certify; but may update incumbent.
        sol=extract(ins,b,vars_tuple,res.x,lam,T,taup,taud)
        if sol['obj'] < UB-1e-10:
            UB=sol['obj']; best=sol
        pstar=res.fun if res.success else getattr(res,'mip_dual_bound',None) # P bound if not success
        if pstar is None or not np.isfinite(pstar): pstar=sol['P']
        lower_for_remaining=lam*pstar
        certLB=lower_for_remaining
        logs.append({'cap':cap,'status':int(res.status),'success':bool(res.success),'time':el,'P_bound':float(pstar),'P_sol':sol['P'],'G_sol':sol['G'],'obj_sol':sol['obj'],'UB':UB,'mip_gap':getattr(res,'mip_gap',None),'nodes':getattr(res,'mip_node_count',None)})
        if verbose:
            print('iter',iterations,'cap',cap,'success',res.success,'P*',res.fun,'Pbound',pstar,'G',sol['G'],'obj',sol['obj'],'UB',UB,'LBrem',lower_for_remaining,'time',el,'nodes',getattr(res,'mip_node_count',None))
        if not res.success:
            # Cannot certify P*(cap); stop, but return incumbent and bound if available.
            break
        # If even zero G with this minimum penalty cannot beat incumbent, remaining lower-G region cannot improve.
        if lower_for_remaining >= UB - tol:
            certLB=lower_for_remaining
            break
        newcap=sol['G'] - tol/10
        if newcap >= cap - 1e-10:
            newcap=cap*0.5
        cap=max(0.0,newcap)
    status='optimal' if certLB >= UB - tol or cap<=tol else 'time_limit'
    return {'status':status,'objective':UB,'LB':certLB,'gap':max(0,UB-certLB),'best':best,'iterations':iterations,'time':time.time()-start,'logs':logs,'final_cap':cap}

if __name__=='__main__':
    import sys
    ans=solve_frontier(sys.argv[1],cap_time=float(sys.argv[2]) if len(sys.argv)>2 else 60,total_time=float(sys.argv[3]) if len(sys.argv)>3 else 600,verbose=True)
    print(json.dumps(ans,indent=2))
