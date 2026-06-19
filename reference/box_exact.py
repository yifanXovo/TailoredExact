import math, time, re, ast, os, json, heapq, glob
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack
from gcap_exact import parse_instance, precompute_tsp, eval_y, no_op, extract as extract_gcap

class VB:
    def __init__(self): self.names=[]; self.lb=[]; self.ub=[]; self.integrality=[]
    def add(self,name,lb=0,ub=np.inf,integer=False,binary=False):
        idx=len(self.names); self.names.append(name)
        if binary: lb=0; ub=1; integ=1
        elif integer: integ=1
        else: integ=0
        self.lb.append(lb); self.ub.append(ub); self.integrality.append(integ); return idx

def build_solve_box(ins,tsp,glo,ghi,plo,phi,lam=0.15,T=3600,taup=60,taud=60,time_limit=10,verbose=False,use_subset=True,objective='zero'):
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
            p[k,i]=b.add(f'p_{k}_{i}',0,min(Y0[i],Qs[k],maxpick),integer=True)
            d[k,i]=b.add(f'd_{k}_{i}',0,min(C[i]-Y0[i],Qs[k],maxpick),integer=True)
            L[k,i]=b.add(f'L_{k}_{i}',0,Qs[k],integer=True)
            u[k,i]=b.add(f'u_{k}_{i}',0,V)
    y={}; r={}; e={}
    for i in stations:
        y[i]=b.add(f'y_{i}',0,C[i],integer=True)
        r[i]=b.add(f'r_{i}',0,C[i]/target[i])
        e[i]=b.add(f'e_{i}',0,max(1.0,abs(C[i]/target[i]-1.0)))
    S=b.add('S',0,sum(C[i]/target[i] for i in stations))
    H=b.add('H',0,sum(max(C[i]/target[i],C[j]/target[j]) for i in stations for j in stations if i<j))
    h={}
    for i in stations:
        for j in stations:
            if i<j: h[i,j]=b.add(f'h_{i}_{j}',0,max(C[i]/target[i],C[j]/target[j]))
    n=len(b.names); rows=[]; lows=[]; ups=[]
    def add(co,lo=-np.inf,up=np.inf):
        row=lil_matrix((1,n))
        for idx,val in co.items():
            if abs(val)>1e-12: row[0,idx]=val
        rows.append(row.tocsr()); lows.append(lo); ups.append(up)
    # route/load constraints copied from gcap
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
                    lb=m&-m; ii=lb.bit_length(); cnt+=1; m-=lb
                    co[p[k,ii]]=co.get(p[k,ii],0)+cunit
                    co[z[k,ii]]=co.get(z[k,ii],0)+BIG
                add(co,-np.inf,T-tsp[mask]+BIG*cnt)
    for k in range(M-1):
        add({use[k]:1,use[k+1]:-1},0,np.inf)
        co={}
        for i in stations:
            co[z[k,i]]=co.get(z[k,i],0)+2**(i-1); co[z[k+1,i]]=co.get(z[k+1,i],0)-2**(i-1)
        add(co,0,np.inf)
    for i in stations:
        add({z[k,i]:1 for k in range(M)},-np.inf,1)
    # inventory/ratios/P/H
    Sco={S:-1}; Pco={}
    for i in stations:
        co={y[i]:1}
        for k in range(M): co[p[k,i]]=co.get(p[k,i],0)+1; co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,Y0[i],Y0[i])
        add({r[i]:1,y[i]:-1/target[i]},0,0)
        add({e[i]:1,r[i]:-1},-1,np.inf)
        add({e[i]:1,r[i]:1},1,np.inf)
        Sco[r[i]]=Sco.get(r[i],0)+1
        Pco[e[i]]=Pco.get(e[i],0)+w[i]
    add(Sco,0,0)
    Hco={H:-1}
    for i in stations:
        for j in stations:
            if i<j:
                add({h[i,j]:1,r[i]:-1,r[j]:1},0,np.inf)
                add({h[i,j]:1,r[i]:1,r[j]:-1},0,np.inf)
                Hco[h[i,j]]=Hco.get(h[i,j],0)+1
    add(Hco,0,0)
    # box constraints: V*glo*S <= H <= V*ghi*S, plo <= P <= phi
    add({H:1,S:-V*glo},0,np.inf)
    add({H:1,S:-V*ghi},-np.inf,0)
    add(Pco,plo,phi)
    c=np.zeros(n)
    if objective=='P':
        for idx,val in Pco.items(): c[idx]=val
    elif objective=='H':
        c[H]=1.0/V
    # else zero objective
    A=vstack(rows).tocsr(); cons=LinearConstraint(A,np.array(lows),np.array(ups)); bounds=Bounds(np.array(b.lb),np.array(b.ub))
    opts={'time_limit':time_limit,'mip_rel_gap':1e-9,'disp':verbose,'presolve':True}
    t0=time.time(); res=milp(c,integrality=np.array(b.integrality),bounds=bounds,constraints=cons,options=opts); elapsed=time.time()-t0
    return res,elapsed,b,(x,z,p,d,L,y,r,e,S,H,h)

def extract(ins,b,vt,sol,lam=0.15,T=3600,taup=60,taud=60):
    return extract_gcap(ins,b,vt,sol,lam,T,taup,taud)

def solve_boxbb(path,lam=0.15,T=3600,taup=60,taud=60,total_time=300,node_time=10,tol=1e-4,init_ub=None,verbose=False):
    ins=parse_instance(path); tsp=precompute_tsp(ins['V'],ins['distances']) if ins['V']<=20 else None
    best=no_op(ins,lam); UB=best['obj'] if init_ub is None else init_ub
    if init_ub is not None:
        best['obj']=init_ub
    # domain objective below UB only
    Gmax=min(1.0,UB); Pmax=UB/lam if lam>0 else 1e9
    pq=[]; counter=0
    def push(glo,ghi,plo,phi):
        nonlocal counter
        lb=glo+lam*plo
        if lb < UB-tol and ghi>glo+1e-9 and phi>plo+1e-9:
            heapq.heappush(pq,(lb,counter,glo,ghi,plo,phi)); counter+=1
    push(0.0,Gmax,0.0,Pmax)
    start=time.time(); processed=0; feas=0; infeas=0; timeouts=0; logs=[]
    while pq and time.time()-start<total_time:
        lb,_,glo,ghi,plo,phi=heapq.heappop(pq)
        if lb>=UB-tol: continue
        tl=max(1.0,min(node_time,total_time-(time.time()-start)))
        res,el,b,vt=build_solve_box(ins,tsp,glo,ghi,plo,phi,lam,T,taup,taud,time_limit=tl,objective='zero')
        processed+=1
        status=int(res.status)
        if res.x is None:
            if status==2:
                infeas+=1
            elif status==1:
                timeouts+=1
                # split large box to help
                if (ghi-glo) >= lam*(phi-plo):
                    mid=(glo+ghi)/2; push(glo,mid,plo,phi); push(mid,ghi,plo,phi)
                else:
                    mid=(plo+phi)/2; push(glo,ghi,plo,mid); push(glo,ghi,mid,phi)
            else:
                # treat as pruned if infeasible/other
                pass
        else:
            feas+=1
            sol=extract(ins,b,vt,res.x,lam,T,taup,taud)
            if sol['obj'] < UB-1e-9:
                UB=sol['obj']; best=sol
                # purge not necessary; lb checks will prune later
                if verbose: print('new UB',UB,'G',sol['G'],'P',sol['P'],'box',(glo,ghi,plo,phi),'time',time.time()-start)
            # split unless small enough/prunable
            # Remove regions that cannot improve due current UB by push function.
            if (ghi-glo) < tol and lam*(phi-plo) < tol:
                # box unresolved but within tolerance, lower bound within tol maybe not; keep tolerance
                pass
            else:
                # split around feasible solution values to isolate Pareto frontier
                gs=sol['G']; ps=sol['P']
                if (ghi-glo) >= lam*(phi-plo):
                    mid=gs if glo+0.1*(ghi-glo)<gs<ghi-0.1*(ghi-glo) else (glo+ghi)/2
                    push(glo,mid,plo,phi); push(mid,ghi,plo,phi)
                else:
                    mid=ps if plo+0.1*(phi-plo)<ps<phi-0.1*(phi-plo) else (plo+phi)/2
                    push(glo,ghi,plo,mid); push(glo,ghi,mid,phi)
        if verbose and processed%10==0:
            glb=pq[0][0] if pq else UB
            print('prog',processed,'UB',UB,'LB',glb,'gap',UB-glb,'q',len(pq),'feas',feas,'inf',infeas,'to',timeouts,'time',time.time()-start)
        logs.append({'box':[glo,ghi,plo,phi],'status':status,'time':el,'UB':UB,'q':len(pq)})
    LB=pq[0][0] if pq else UB
    status='optimal' if not pq or LB>=UB-tol else 'time_limit'
    return {'name':os.path.basename(path),'status':status,'objective':UB,'LB':LB,'gap':max(0,UB-LB),'time':time.time()-start,'processed':processed,'feasible_boxes':feas,'infeasible_boxes':infeas,'timeouts':timeouts,'queue':len(pq),'best':best,'logs':logs[-20:]}

if __name__=='__main__':
    import sys
    ans=solve_boxbb(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/regen_candidate_V12_M1_average.txt', total_time=float(sys.argv[2]) if len(sys.argv)>2 else 300, node_time=float(sys.argv[3]) if len(sys.argv)>3 else 10, verbose=True)
    print(json.dumps(ans,indent=2))
