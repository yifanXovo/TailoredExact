import re, ast, math, time, os, json, glob
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
            lb=m&-m; j=lb.bit_length()-1
            val=dp[mask,j]+dist[j+1][0]
            if val<best: best=val
            m-=lb
        tsp[mask]=best
    return tsp

def S_bounds_reachable(ins,T=3600,taup=60,taud=60):
    V=ins['V']; M=ins['M']; B=sum(int(T//(taup+taud)) for _ in range(M))
    Y=ins['initial']; C=ins['capacities']; target=ins['target']
    inv=[0.0]+[1.0/target[i] for i in range(1,V+1)]
    S0=sum(Y[i]*inv[i] for i in range(1,V+1))
    # S can decrease by picking bikes and possibly unloading at depot; lower bound by best decreases.
    units=sorted([(inv[i],Y[i]) for i in range(1,V+1)], reverse=True)
    rem=B; dec=0.0
    for val,cap in units:
        q=min(cap,rem); dec+=q*val; rem-=q
        if rem<=0: break
    Smin=max(1e-6,S0-dec)
    # S can increase only by moving picked bikes from low inverse-target stations to high inverse-target stations.
    sources=sorted([(inv[i],Y[i]) for i in range(1,V+1)])
    sinks=sorted([(inv[j],C[j]-Y[j]) for j in range(1,V+1)], reverse=True)
    si=tj=0; rem=B; inc=0.0
    while rem>0 and si<len(sources) and tj<len(sinks):
        sval,scap=sources[si]; tval,tcap=sinks[tj]
        if tval <= sval+1e-15: break
        q=min(scap,tcap,rem); inc += q*(tval-sval); rem-=q; scap-=q; tcap-=q
        if scap<=1e-12: si+=1
        else: sources[si]=(sval,scap)
        if tcap<=1e-12: tj+=1
        else: sinks[tj]=(tval,tcap)
    Smax=S0+inc
    return Smin,Smax,S0

def eval_y(ins,yv,lam=0.15):
    V=ins['V']; rr=[yv[i-1]/ins['target'][i] for i in range(1,V+1)]
    S=sum(rr); H=sum(abs(rr[i]-rr[j]) for i in range(V) for j in range(i+1,V))
    G=H/(V*S) if S>0 else 0.0
    P=sum(ins['weights'][i]*abs(rr[i-1]-1.0) for i in range(1,V+1))
    return G,P,G+lam*P,S,H

def no_op(ins,lam=0.15):
    yv=[ins['initial'][i] for i in range(1,ins['V']+1)]
    G,P,obj,S,H=eval_y(ins,yv,lam)
    return {'obj':obj,'G':G,'P':P,'S':S,'H':H,'y':yv,'routes':[[] for _ in range(ins['M'])]}

class VB:
    def __init__(self): self.names=[]; self.lb=[]; self.ub=[]; self.integrality=[]
    def add(self,name,lb=0,ub=np.inf,integer=False,binary=False):
        idx=len(self.names); self.names.append(name)
        if binary: lb=0; ub=1; integ=1
        elif integer: integ=1
        else: integ=0
        self.lb.append(lb); self.ub.append(ub); self.integrality.append(integ); return idx

def build_ccbi(ins,tsp=None,lam=0.15,T=3600,taup=60,taud=60,time_limit=300,ub_obj=None,verbose=False,subset_cuts=True,fix_gcap=None):
    V=ins['V']; M=ins['M']; Qs=ins['Q']; C=ins['capacities']; Y0=ins['initial']; target=ins['target']; wgt=ins['weights']; dist=ins['distances']
    stations=range(1,V+1); nodes=range(V+1); cunit=taup+taud; maxpick=int(T//cunit)
    Slo,Shi,S0=S_bounds_reachable(ins,T,taup,taud)
    tlo=1.0/Shi; thi=1.0/Slo
    b=VB(); x={}; z={}; mode={}; p={}; d={}; L={}; u={}; use={}
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
    y={}; r={}; e={}; bits={}; tb={}; qscaled={}; us={}
    tvar=b.add('t',lb=tlo,ub=thi)
    for i in stations:
        y[i]=b.add(f'y_{i}',lb=0,ub=C[i],integer=True)
        r[i]=b.add(f'r_{i}',lb=0,ub=C[i]/target[i])
        e[i]=b.add(f'e_{i}',lb=0,ub=max(1.0,abs(C[i]/target[i]-1.0)))
        # qscaled_i = t*y_i, us_i=qscaled_i/target_i
        qscaled[i]=b.add(f'qscaled_{i}',lb=0,ub=C[i]*thi)
        us[i]=b.add(f'uScaled_{i}',lb=0,ub=(C[i]/target[i])*thi)
        for bb in range(math.ceil(math.log2(C[i]+1))):
            bits[i,bb]=b.add(f'bit_{i}_{bb}',binary=True)
            tb[i,bb]=b.add(f'tbit_{i}_{bb}',lb=0,ub=thi)
    hu={}
    for i in stations:
        for j in stations:
            if i<j: hu[i,j]=b.add(f'hu_{i}_{j}',lb=0,ub=(C[i]/target[i]+C[j]/target[j])*thi)
    n=len(b.names); rows=[]; lows=[]; ups=[]
    def add(co,lo=-np.inf,up=np.inf):
        row=lil_matrix((1,n))
        for idx,val in co.items():
            if abs(val)>1e-12: row[0,idx]=val
        rows.append(row.tocsr()); lows.append(lo); ups.append(up)
    # routing constraints
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
            add({p[k,i]:1,d[k,i]:1,z[k,i]:-1},0,np.inf)  # if visited, positive operation
            add({L[k,i]:1,z[k,i]:-Qs[k]},-np.inf,0)
            add({u[k,i]:1,z[k,i]:-V},-np.inf,0)
            add({u[k,i]:1,z[k,i]:-1},0,np.inf)
        # MTZ
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
        # total drops <= total pickups
        co={}
        for i in stations:
            co[p[k,i]]=co.get(p[k,i],0)+1; co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,0,np.inf)
        # duration: travel + (taup+taud)*total pickups <=T
        co={}
        for i in nodes:
            for j in nodes:
                if i!=j: co[x[k,i,j]]=co.get(x[k,i,j],0)+dist[i][j]
        for i in stations: co[p[k,i]]=co.get(p[k,i],0)+cunit
        add(co,-np.inf,T)
        if subset_cuts and V<=16 and tsp is not None:
            BIG=1e5
            for mask in range(1,1<<V):
                co={}; cnt=0; m=mask
                while m:
                    lb=m&-m; ii=lb.bit_length(); cnt+=1; m-=lb
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
    # inventory and ratio/penalty
    for i in stations:
        co={y[i]:1}
        for k in range(M):
            co[p[k,i]]=co.get(p[k,i],0)+1; co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,Y0[i],Y0[i])
        add({r[i]:1,y[i]:-1.0/target[i]},0,0)
        add({e[i]:1,r[i]:-1},-1,np.inf)
        add({e[i]:1,r[i]:1},1,np.inf)
        # bit expansion y_i = sum 2^b bit
        co={y[i]:1}
        for bb in range(math.ceil(math.log2(C[i]+1))): co[bits[i,bb]]=co.get(bits[i,bb],0)-(1<<bb)
        add(co,0,0)
        # tbit = t * bit, exact by binary-continuous McCormick
        co={qscaled[i]:1}
        for bb in range(math.ceil(math.log2(C[i]+1))):
            # tbit <= thi*bit; tbit >= t - thi*(1-bit); tbit <= t - tlo*(1-bit); tbit >= tlo*bit
            add({tb[i,bb]:1,bits[i,bb]:-thi},-np.inf,0)
            add({tb[i,bb]:1,tvar:-1,bits[i,bb]:-thi},-thi,np.inf)
            add({tb[i,bb]:1,tvar:-1,bits[i,bb]:-tlo},-np.inf,-tlo)
            add({tb[i,bb]:1,bits[i,bb]:-tlo},0,np.inf)
            co[tb[i,bb]]=co.get(tb[i,bb],0)-(1<<bb)
        add(co,0,0)
        add({us[i]:1,qscaled[i]:-1.0/target[i]},0,0)
    # normalization: sum_i us_i = 1
    add({us[i]:1 for i in stations},1,1)
    # Gini numerator on scaled ratios u_i = r_i/S
    for i in stations:
        for j in stations:
            if i<j:
                add({hu[i,j]:1,us[i]:-1,us[j]:1},0,np.inf)
                add({hu[i,j]:1,us[i]:1,us[j]:-1},0,np.inf)
    # optional Gini cap if used: (1/V) sum hu <= cap
    if fix_gcap is not None:
        add({hu[i,j]:1 for (i,j) in hu},-np.inf,V*fix_gcap)
    # incumbent cutoff
    if ub_obj is not None and math.isfinite(ub_obj):
        co={}
        for (i,j),var in hu.items(): co[var]=co.get(var,0)+1.0/V
        for i in stations: co[e[i]]=co.get(e[i],0)+lam*wgt[i]
        add(co,-np.inf,ub_obj-1e-10)
    c=np.zeros(n)
    for var in hu.values(): c[var]+=1.0/V
    for i in stations: c[e[i]] += lam*wgt[i]
    A=vstack(rows).tocsr(); cons=LinearConstraint(A,np.array(lows),np.array(ups)); bounds=Bounds(np.array(b.lb),np.array(b.ub))
    opts={'time_limit':time_limit,'mip_rel_gap':1e-9,'disp':verbose,'presolve':True}
    t0=time.time(); res=milp(c,integrality=np.array(b.integrality),bounds=bounds,constraints=cons,options=opts); elapsed=time.time()-t0
    return res,elapsed,b,(x,z,p,d,L,y,r,e,tvar,qscaled,us,hu)

def extract(ins,b,vars_tuple,sol,lam=0.15,T=3600,taup=60,taud=60):
    x,z,p,d,L,y,r,e,tvar,qscaled,us,hu=vars_tuple; vals={name:sol[i] for i,name in enumerate(b.names)}
    V=ins['V']; M=ins['M']; stations=range(1,V+1); nodes=range(V+1)
    yv=[int(round(vals[f'y_{i}'])) for i in stations]
    G,P,obj,S,H=eval_y(ins,yv,lam)
    routes=[]; pks=[]; dks=[]; travel=[]; op=[]; loads=[]
    for k in range(M):
        pv={i:int(round(vals.get(f'p_{k}_{i}',0))) for i in stations}
        dv={i:int(round(vals.get(f'd_{k}_{i}',0))) for i in stations}
        pks.append(pv); dks.append(dv)
        arcs={}
        for i in nodes:
            for j in nodes:
                if i!=j and vals.get(f'x_{k}_{i}_{j}',0)>0.5: arcs[i]=j
        route=[]; cur=0; seen=set(); tr=0.0; ld=0; lseq=[]; prev=0
        while cur in arcs and arcs[cur]!=0 and arcs[cur] not in seen:
            nxt=arcs[cur]; route.append(nxt); tr+=ins['distances'][cur][nxt]
            ld+=pv[nxt]-dv[nxt]; lseq.append(ld); seen.add(nxt); cur=nxt
        if route: tr+=ins['distances'][cur][0]
        routes.append(route); travel.append(tr)
        totalp=sum(pv.values()); totald=sum(dv.values()); op.append(taup*totalp+taud*totald+taud*(totalp-totald)); loads.append(lseq)
    return {'obj':obj,'G':G,'P':P,'S':S,'H':H,'y':yv,'routes':routes,'p':pks,'d':dks,'travel':travel,'op':op,'loads':loads,'t':vals.get('t')}

def solve(path,lam=0.15,T=3600,taup=60,taud=60,time_limit=300,verbose=False,use_noop_ub=True):
    ins=parse_instance(path); tsp=precompute_tsp(ins['V'],ins['distances']) if ins['V']<=20 else None
    ub=no_op(ins,lam)['obj'] if use_noop_ub else None
    # do not set ub by no-op as cutoff? yes safe but can slow if too tight? keep.
    res,elapsed,b,vt=build_ccbi(ins,tsp,lam,T,taup,taud,time_limit,ub_obj=ub,verbose=verbose,subset_cuts=(ins['V']<=16))
    sol=None
    if res.x is not None:
        sol=extract(ins,b,vt,res.x,lam,T,taup,taud)
    return {'name':os.path.basename(path),'status':int(res.status),'success':bool(res.success),'message':res.message,'fun':None if res.fun is None else float(res.fun),'time':elapsed,'mip_gap':getattr(res,'mip_gap',None),'nodes':getattr(res,'mip_node_count',None),'dual_bound':getattr(res,'mip_dual_bound',None),'solution':sol}

if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='--all':
        out=[]
        for p in sorted(glob.glob('/mnt/data/regen_candidate*.txt')):
            ans=solve(p,time_limit=float(sys.argv[2]) if len(sys.argv)>2 else 120,verbose=False)
            print(json.dumps(ans,indent=2)); out.append(ans)
        open('/mnt/data/ccbi_results.json','w').write(json.dumps(out,indent=2))
    else:
        path=sys.argv[1] if len(sys.argv)>1 else '/mnt/data/regen_candidate_V12_M1_average.txt'
        tl=float(sys.argv[2]) if len(sys.argv)>2 else 300
        ans=solve(path,time_limit=tl,verbose=True)
        print(json.dumps(ans,indent=2))
