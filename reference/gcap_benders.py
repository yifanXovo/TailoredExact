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
        rem=(N-1)^mask
        for j in range(V):
            val=dp[mask,j]
            if val>=INF: continue
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
            best=min(best, dp[mask,j]+dist[j+1][0])
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
    P=sum(ins['weights'][i]*abs(rr[i-1]-1) for i in range(1,V+1))
    return G,P,G+lam*P,S,H

def no_op(ins,lam=0.15):
    yv=[ins['initial'][i] for i in range(1,ins['V']+1)]
    G,P,obj,S,H=eval_y(ins,yv,lam)
    return {'obj':obj,'G':G,'P':P,'S':S,'H':H,'y':yv,'routes':[[] for _ in range(ins['M'])], 'p':[], 'd':[], 'travel':[0]*ins['M'], 'op':[0]*ins['M']}

def route_oracle(ins, pvals, dvals, k, T=3600, taup=60, taud=60):
    V=ins['V']; Q=ins['Q'][k]; dist=ins['distances']
    p=[0]*(V+1); d=[0]*(V+1)
    for i in range(1,V+1): p[i]=int(round(pvals[i])); d[i]=int(round(dvals[i]))
    S=[i for i in range(1,V+1) if p[i]+d[i]>0]
    totalp=sum(p); totald=sum(d)
    if not S: return True, [], 0.0, 0.0
    if totald>totalp: return False,None,math.inf,None
    op=taup*totalp + taud*totald + taud*(totalp-totald)
    if op>T+1e-9: return False,None,math.inf,op
    n=len(S); N=1<<n; INF=1e100
    dp=[ [ [INF]*(Q+1) for _ in range(n)] for __ in range(N)]
    par={}
    for a,node in enumerate(S):
        if d[node]<=0:
            load=p[node]
            if 0<=load<=Q:
                dp[1<<a][a][load]=dist[0][node]
                par[(1<<a,a,load)]=(-1,-1,-1)
    for mask in range(N):
        rem=(N-1)^mask
        for a,last in enumerate(S):
            arr=dp[mask][a]
            for load,val in enumerate(arr):
                if val>=INF: continue
                m=rem
                while m:
                    lb=m&-m; b=lb.bit_length()-1; node=S[b]
                    if load>=d[node]:
                        nl=load-d[node]+p[node]
                        if 0<=nl<=Q:
                            nm=mask|lb; nv=val+dist[last][node]
                            if nv<dp[nm][b][nl]-1e-9:
                                dp[nm][b][nl]=nv; par[(nm,b,nl)]=(mask,a,load)
                    m-=lb
    full=N-1; final=totalp-totald; best=INF; beststate=None
    for a,last in enumerate(S):
        if 0<=final<=Q:
            val=dp[full][a][final]
            if val<INF:
                tv=val+dist[last][0]
                if tv<best: best=tv; beststate=(full,a,final)
    if best>=INF/2 or best+op>T+1e-7: return False,None,best,op
    route=[]; st=beststate
    while st and st[0]!=-1:
        mask,a,load=st; route.append(S[a]); st=par.get(st,(-1,-1,-1))
    route=route[::-1]
    return True,route,best,op

def build_master(ins,tsp,gcap,nogoods,lam=0.15,T=3600,taup=60,taud=60,time_limit=30,verbose=False,incumbent_obj=None,use_subset=True):
    V=ins['V']; M=ins['M']; Qs=ins['Q']; C=ins['capacities']; Y0=ins['initial']; target=ins['target']; w=ins['weights']
    stations=range(1,V+1); cunit=taup+taud; maxpick=int(T//cunit)
    b=VB(); z={}; mode={}; p={}; d={}
    for k in range(M):
        for i in stations:
            z[k,i]=b.add(f'z_{k}_{i}',binary=True)
            mode[k,i]=b.add(f'mode_{k}_{i}',binary=True)
            p[k,i]=b.add(f'p_{k}_{i}',lb=0,ub=min(Y0[i],Qs[k],maxpick),integer=True)
            d[k,i]=b.add(f'd_{k}_{i}',lb=0,ub=min(C[i]-Y0[i],Qs[k],maxpick),integer=True)
    y={}; r={}; e={}
    for i in stations:
        y[i]=b.add(f'y_{i}',lb=0,ub=C[i],integer=True)
        r[i]=b.add(f'r_{i}',lb=0,ub=C[i]/target[i])
        e[i]=b.add(f'e_{i}',lb=0,ub=max(1.0,abs(C[i]/target[i]-1.0)))
    Svar=b.add('S',lb=0,ub=sum(C[i]/target[i] for i in stations))
    Hvar=b.add('H',lb=0,ub=sum(max(C[i]/target[i],C[j]/target[j]) for i in stations for j in stations if i<j))
    h={}
    for i in stations:
        for j in stations:
            if i<j: h[i,j]=b.add(f'h_{i}_{j}',lb=0,ub=max(C[i]/target[i],C[j]/target[j]))
    # no-good abs vars
    ng_abs=[]
    for gidx,(kg,pstar,dstar) in enumerate(nogoods):
        ad={}
        for i in stations:
            ad['p',i]=b.add(f'ng{gidx}_ap_{i}',lb=0,ub=maxpick)
            ad['d',i]=b.add(f'ng{gidx}_ad_{i}',lb=0,ub=maxpick)
        ng_abs.append(ad)
    n=len(b.names); rows=[]; lows=[]; ups=[]
    def add(co,lo=-np.inf,up=np.inf):
        row=lil_matrix((1,n))
        for idx,val in co.items():
            if abs(val)>1e-12: row[0,idx]=val
        rows.append(row.tocsr()); lows.append(lo); ups.append(up)
    # assignment/ops
    for k in range(M):
        for i in stations:
            up_p=min(Y0[i],Qs[k],maxpick); up_d=min(C[i]-Y0[i],Qs[k],maxpick)
            add({mode[k,i]:1,z[k,i]:-1},up=0)
            add({p[k,i]:1,mode[k,i]:-up_p},up=0)
            add({d[k,i]:1,z[k,i]:-up_d,mode[k,i]:up_d},up=0)
            add({p[k,i]:1,d[k,i]:1,z[k,i]:-1},lo=0)
        co={}
        for i in stations:
            co[p[k,i]]=co.get(p[k,i],0)+1; co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,lo=0)
        add({p[k,i]:cunit for i in stations},up=T)
        if use_subset and tsp is not None:
            BIG=1e5
            for mask in range(1,1<<V):
                co={}; cnt=0; m=mask
                while m:
                    lb=m&-m; ii=lb.bit_length(); cnt+=1; m-=lb
                    co[p[k,ii]]=co.get(p[k,ii],0)+cunit
                    co[z[k,ii]]=co.get(z[k,ii],0)+BIG
                add(co,up=T-tsp[mask]+BIG*cnt)
    for i in stations: add({z[k,i]:1 for k in range(M)},up=1)
    for k in range(M-1):
        co={}
        for i in stations:
            co[z[k,i]]=co.get(z[k,i],0)+2**(i-1)
            co[z[k+1,i]]=co.get(z[k+1,i],0)-2**(i-1)
        add(co,lo=0)
    # final inventory, S,H,e
    Sco={Svar:-1}
    for i in stations:
        co={y[i]:1}
        for k in range(M):
            co[p[k,i]]=co.get(p[k,i],0)+1
            co[d[k,i]]=co.get(d[k,i],0)-1
        add(co,Y0[i],Y0[i])
        add({r[i]:1,y[i]:-1.0/target[i]},0,0)
        add({e[i]:1,r[i]:-1},lo=-1)
        add({e[i]:1,r[i]:1},lo=1)
        Sco[r[i]]=Sco.get(r[i],0)+1
    add(Sco,0,0)
    Hco={Hvar:-1}
    for i in stations:
        for j in stations:
            if i<j:
                add({h[i,j]:1,r[i]:-1,r[j]:1},lo=0)
                add({h[i,j]:1,r[i]:1,r[j]:-1},lo=0)
                Hco[h[i,j]]=Hco.get(h[i,j],0)+1
    add(Hco,0,0)
    add({Hvar:1,Svar:-V*gcap},up=1e-9)
    # objective cutoff: since G>=0, P<=UB/lambda necessary
    if incumbent_obj is not None and math.isfinite(incumbent_obj) and lam>0:
        co={}
        for i in stations: co[e[i]]=co.get(e[i],0)+w[i]
        add(co,up=incumbent_obj/lam + 1e-9)
    # no-good cuts
    for gidx,(kg,pstar,dstar) in enumerate(nogoods):
        ad=ng_abs[gidx]
        for i in stations:
            add({ad['p',i]:1,p[kg,i]:-1},lo=-pstar[i])
            add({ad['p',i]:1,p[kg,i]:1},lo=pstar[i])
            add({ad['d',i]:1,d[kg,i]:-1},lo=-dstar[i])
            add({ad['d',i]:1,d[kg,i]:1},lo=dstar[i])
        co={}
        for i in stations:
            co[ad['p',i]]=co.get(ad['p',i],0)+1
            co[ad['d',i]]=co.get(ad['d',i],0)+1
        add(co,lo=1)
    c=np.zeros(n)
    for i in stations: c[e[i]] += w[i]
    A=vstack(rows).tocsr(); cons=LinearConstraint(A,np.array(lows),np.array(ups)); bounds=Bounds(np.array(b.lb),np.array(b.ub))
    opts={'time_limit':time_limit,'mip_rel_gap':1e-9,'disp':verbose,'presolve':True}
    t0=time.time(); res=milp(c,integrality=np.array(b.integrality),bounds=bounds,constraints=cons,options=opts); elapsed=time.time()-t0
    return res,elapsed,b,(p,d,y,r,e,Svar,Hvar,h)

def extract(ins,b,vars_tuple,sol,lam=0.15):
    p,d,y,r,e,Svar,Hvar,h=vars_tuple; vals={name:sol[i] for i,name in enumerate(b.names)}
    V=ins['V']; M=ins['M']; stations=range(1,V+1)
    yv=[int(round(vals[f'y_{i}'])) for i in stations]
    G,P,obj,S,H=eval_y(ins,yv,lam)
    pks=[]; dks=[]
    for k in range(M):
        pks.append({i:int(round(vals[f'p_{k}_{i}'])) for i in stations})
        dks.append({i:int(round(vals[f'd_{k}_{i}'])) for i in stations})
    return {'obj':obj,'G':G,'P':P,'S':S,'H':H,'y':yv,'p':pks,'d':dks,'P_model':sum(ins['weights'][i]*vals[f'e_{i}'] for i in stations)}

def solve_cap_exact(ins,tsp,gcap,nogoods,lam=0.15,T=3600,taup=60,taud=60,time_limit=30,verbose=False,UB=None):
    local_cuts=0; start=time.time(); logs=[]
    while True:
        rem=max(1.0,time_limit-(time.time()-start))
        res,el,b,vars_tuple=build_master(ins,tsp,gcap,nogoods,lam,T,taup,taud,time_limit=rem,verbose=False,incumbent_obj=UB,use_subset=(ins['V']<=16))
        if res.x is None:
            return {'status':'no_solution' if res.status==2 else 'time_limit','res':res,'time':time.time()-start,'logs':logs,'nogoods_added':local_cuts}
        sol=extract(ins,b,vars_tuple,res.x,lam)
        # even if MIP time-limited, try update UB if route feasible; but cap not certified
        feasible=True; routes=[]; travel=[]; op=[]; bad=[]
        for k in range(ins['M']):
            ok,rt,tr,oo=route_oracle(ins,sol['p'][k],sol['d'][k],k,T,taup,taud)
            if not ok:
                feasible=False; bad.append(k)
            routes.append(rt); travel.append(tr); op.append(oo)
        sol.update({'routes':routes,'travel':travel,'op':op})
        logs.append({'mip_status':int(res.status),'success':bool(res.success),'fun':float(res.fun) if res.fun is not None else None,'dual':float(getattr(res,'mip_dual_bound',math.nan)) if hasattr(res,'mip_dual_bound') and getattr(res,'mip_dual_bound',None) is not None else None,'feasible':feasible,'G':sol['G'],'P':sol['P'],'obj':sol['obj'],'bad':bad,'elapsed':el})
        if not feasible:
            for k in bad:
                nogoods.append((k,sol['p'][k],sol['d'][k])); local_cuts+=1
            if time.time()-start>=time_limit:
                return {'status':'time_limit','res':res,'time':time.time()-start,'logs':logs,'nogoods_added':local_cuts,'candidate':sol}
            continue
        if res.success:
            return {'status':'optimal','Pstar':res.fun,'solution':sol,'res':res,'time':time.time()-start,'logs':logs,'nogoods_added':local_cuts}
        else:
            return {'status':'time_limit','Pbound':getattr(res,'mip_dual_bound',None),'solution':sol,'res':res,'time':time.time()-start,'logs':logs,'nogoods_added':local_cuts}

def solve_frontier(path,lam=0.15,T=3600,taup=60,taud=60,cap_time=30,total_time=300,tol=1e-7,verbose=False):
    ins=parse_instance(path); tsp=precompute_tsp(ins['V'],ins['distances']) if ins['V']<=20 else None
    best=no_op(ins,lam); UB=best['obj']; cap=min(1.0,UB); start=time.time(); nogoods=[]; logs=[]; certLB=0.0; it=0
    while cap>tol and time.time()-start<total_time:
        it+=1
        tl=min(cap_time,total_time-(time.time()-start))
        ans=solve_cap_exact(ins,tsp,cap,nogoods,lam,T,taup,taud,time_limit=tl,verbose=False,UB=UB)
        if ans['status']=='no_solution':
            certLB=UB; break
        sol=ans.get('solution') or ans.get('candidate')
        if sol is not None and sol['obj']<UB-1e-10:
            UB=sol['obj']; best=sol
        if ans['status']!='optimal':
            # not certified; use bound if any
            pbd=ans.get('Pbound')
            if pbd is not None and math.isfinite(pbd): certLB=max(certLB, lam*pbd)
            logs.append({'cap':cap,'status':ans['status'],'time':ans['time'],'UB':UB,'certLB':certLB,'inner_logs':ans['logs']})
            if verbose: print('it',it,'cap',cap,'NOTCERT',ans['status'],'UB',UB,'LB',certLB,'time',time.time()-start)
            break
        Pstar=ans['Pstar']; sol=ans['solution']
        bandLB=sol['G'] + lam*Pstar
        # band [sol.G, cap] is certified to have objective >= bandLB, and sol attains it (within rounding)
        if sol['obj']<UB-1e-10:
            UB=sol['obj']; best=sol
        logs.append({'cap':cap,'status':'optimal','Pstar':float(Pstar),'Gsol':sol['G'],'objsol':sol['obj'],'bandLB':bandLB,'UB':UB,'time':ans['time'],'nogoods':len(nogoods),'inner_logs':ans['logs']})
        if verbose: print('it',it,'cap',cap,'P*',Pstar,'G',sol['G'],'obj',sol['obj'],'UB',UB,'bandLB',bandLB,'cuts',len(nogoods),'time',time.time()-start)
        # lower-G remaining region: objective >= lambda*P_min(new cap) unknown; continue. If lambda*Pstar >= UB and sol.G is very small? Actually P_min for lower cap >= Pstar.
        if lam*Pstar >= UB - tol:
            certLB=lam*Pstar; break
        newcap=sol['G']-tol/10
        if newcap>=cap-1e-12:
            newcap=cap-1e-6
        cap=max(0.0,newcap)
    status='optimal' if certLB>=UB-tol or cap<=tol else 'time_limit'
    return {'status':status,'objective':UB,'LB':certLB,'gap':max(0,UB-certLB),'best':best,'iterations':it,'time':time.time()-start,'logs':logs,'final_cap':cap,'nogoods':len(nogoods)}

if __name__=='__main__':
    import sys
    ans=solve_frontier(sys.argv[1],cap_time=float(sys.argv[2]) if len(sys.argv)>2 else 30,total_time=float(sys.argv[3]) if len(sys.argv)>3 else 300,verbose=True)
    print(json.dumps(ans,indent=2))
