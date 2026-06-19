import re, ast, math, time, itertools
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, csr_matrix


def parse(path):
    txt=open(path).read()
    first=txt.strip().splitlines()[0].strip().split(maxsplit=2)
    V=int(first[0]); M=int(first[1]); Qs=ast.literal_eval(first[2])
    def get(name):
        m=re.search(rf'{name}\s*=\s*(\[[\s\S]*?\])', txt)
        return ast.literal_eval(m.group(1))
    C=get('capacities'); I=get('initial'); Tar=get('target'); w=get('weights')
    m=re.search(r'distances\s*=\s*\[([\s\S]*?)\]\s*$', txt)
    rows=[]
    for line in m.group(1).splitlines():
        line=line.strip().strip(',')
        if line.startswith('{'):
            rows.append([float(x) for x in line.strip('{}').split(',')])
    return V,M,Qs,C,I,Tar,w,np.array(rows)

def min_cycles(dist,V):
    INF=1e18
    nmask=1<<V
    dp={}
    for i in range(1,V+1): dp[(1<<(i-1),i)]=dist[0,i]
    for mask in range(1,nmask):
        # iterate keys? simple
        for last in range(1,V+1):
            val=dp.get((mask,last))
            if val is None: continue
            rem=(nmask-1)^mask
            b=rem
            while b:
                lsb=b&-b; j=lsb.bit_length()
                nm=mask|lsb; nv=val+dist[last,j]
                key=(nm,j)
                if nv<dp.get(key,INF): dp[key]=nv
                b-=lsb
    L=[0.0]*nmask
    for mask in range(1,nmask):
        best=INF
        for last in range(1,V+1):
            if mask>>(last-1)&1:
                val=dp.get((mask,last),INF)+dist[last,0]
                if val<best: best=val
        L[mask]=best
    return L

class MB:
    def __init__(self,inst,tau=60,T=3600,lam=0.15,ub=None, add_subset_cuts=True):
        self.V,self.M,self.Qs,self.C,self.I,self.Tar,self.w,self.dist=inst
        self.tau=tau; self.T=T; self.lam=lam; self.ub_obj=ub; self.add_subset_cuts=add_subset_cuts
        self.nvar=0; self.vi={}; self.names=[]; self.c=[]; self.lb=[]; self.ub=[]; self.integ=[]
        self.rows=[]; self.lbs=[]; self.ubs=[]
    def addv(self,name,lb=0,ub=np.inf,obj=0,integ=0):
        idx=self.nvar; self.nvar+=1; self.vi[name]=idx; self.names.append(name)
        self.lb.append(lb); self.ub.append(ub); self.c.append(obj); self.integ.append(integ); return idx
    def con(self,co,lb=-np.inf,ub=np.inf): self.rows.append(co); self.lbs.append(lb); self.ubs.append(ub)
    def build(self):
        V,M=self.V,self.M; stations=range(1,V+1)
        a={}; mode={}; p={}; d={}
        for k in range(M):
            Q=self.Qs[k]
            for i in stations:
                a[k,i]=self.addv(('a',k,i),0,1,0,1)
                mode[k,i]=self.addv(('mode',k,i),0,1,0,1)
                p[k,i]=self.addv(('p',k,i),0,min(self.I[i],Q),0,1)
                d[k,i]=self.addv(('d',k,i),0,min(self.C[i]-self.I[i],Q),0,1)
        dep={}
        for k in range(M): dep[k]=self.addv(('dep',k),0,self.Qs[k],0,1)
        theta={}; rho={}; e={}
        for i in stations:
            theta[i]=self.addv(('theta',i),0,self.C[i],0,1)
            rho[i]=self.addv(('rho',i),0,self.C[i]/self.Tar[i],0,0)
            e[i]=self.addv(('e',i),0,max(1,self.C[i]/self.Tar[i]-1),self.lam*self.w[i],0)
        h={}
        for i in stations:
            for j in stations:
                if i<j: h[i,j]=self.addv(('h',i,j),0,self.C[i]/self.Tar[i]+self.C[j]/self.Tar[j],0,0)
        G=self.addv(('G',),0,1,1,0)
        bits={}; prod={}; zprod={}
        for i in stations:
            zprod[i]=self.addv(('zprod',i),0,self.C[i],0,0) # G * theta_i
            L=math.ceil(math.log2(self.C[i]+1))
            for b in range(L):
                bits[i,b]=self.addv(('bit',i,b),0,1,0,1)
                prod[i,b]=self.addv(('prod',i,b),0,1,0,0)
        # station assignment and op bounds
        for i in stations:
            self.con({a[k,i]:1 for k in range(M)},0,1)
        for k in range(M):
            Q=self.Qs[k]
            for i in stations:
                Pmax=min(self.I[i],Q); Dmax=min(self.C[i]-self.I[i],Q)
                self.con({p[k,i]:1,a[k,i]:-Pmax},ub=0)
                self.con({d[k,i]:1,a[k,i]:-Dmax},ub=0)
                self.con({mode[k,i]:1,a[k,i]:-1},ub=0)
                self.con({p[k,i]:1,mode[k,i]:-Pmax},ub=0)
                self.con({d[k,i]:1,a[k,i]:-Dmax,mode[k,i]:Dmax},ub=0)
                self.con({p[k,i]:1,d[k,i]:1,a[k,i]:-1},lb=0)
            # dep = sum p-d; net in [0,Q]
            co={dep[k]:1}
            for i in stations:
                co[p[k,i]]=co.get(p[k,i],0)-1
                co[d[k,i]]=co.get(d[k,i],0)+1
            self.con(co,0,0)
            # aggregate route duration weak: 120 sum all p + mincycle(assigned) via subset cuts below
            self.con({p[k,i]:self.tau*2 for i in stations},ub=self.T)  # no travel lower, weak
        # subset TSP lower-bound cuts
        if self.add_subset_cuts:
            Lcyc=min_cycles(self.dist,V)
            big=10000.0 # safe: LHS max 3600+ maybe, RHS relax enough
            for k in range(M):
                for mask in range(1,1<<V):
                    S=[i for i in stations if mask>>(i-1)&1]
                    # if all S assigned then 2tau sum_{i in S} p_i + Lcyc[S] <= T
                    co={}
                    for i in S:
                        co[p[k,i]]=co.get(p[k,i],0)+2*self.tau
                        co[a[k,i]]=co.get(a[k,i],0)+big
                    # 2tau p + big*sum a <= T - L + big*|S|
                    self.con(co,ub=self.T - Lcyc[mask] + big*len(S))
        # final inventory
        for i in stations:
            co={theta[i]:1}
            for k in range(M):
                co[p[k,i]]=co.get(p[k,i],0)+1
                co[d[k,i]]=co.get(d[k,i],0)-1
            self.con(co,self.I[i],self.I[i])
            self.con({rho[i]:1,theta[i]:-1/self.Tar[i]},0,0)
            self.con({e[i]:1,rho[i]:-1},lb=-1)
            self.con({e[i]:1,rho[i]:1},lb=1)
        # h abs
        for (i,j),var in h.items():
            self.con({var:1,rho[i]:-1,rho[j]:1},lb=0)
            self.con({var:1,rho[i]:1,rho[j]:-1},lb=0)
        # bits, products
        for i in stations:
            L=math.ceil(math.log2(self.C[i]+1))
            co={theta[i]:1}
            for b in range(L): co[bits[i,b]]=co.get(bits[i,b],0)-(1<<b)
            self.con(co,0,0)
            co={zprod[i]:1}
            for b in range(L): co[prod[i,b]]=co.get(prod[i,b],0)-(1<<b)
            self.con(co,0,0)
            # continuous McCormick z=G*theta, theta in [0,C]
            C=self.C[i]
            self.con({zprod[i]:1,G:-C},ub=0) # z<=C G
            self.con({zprod[i]:1,theta[i]:-1},ub=0) # z<=theta
            self.con({zprod[i]:1,theta[i]:-1,G:-C},lb=-C) # z>=theta+C G-C
            for b in range(L):
                self.con({prod[i,b]:1,bits[i,b]:-1},ub=0)
                self.con({prod[i,b]:1,G:-1},ub=0)
                self.con({prod[i,b]:1,G:-1,bits[i,b]:-1},lb=-1)
        # Gini product
        co={}
        for i in stations:
            co[zprod[i]]=co.get(zprod[i],0)+V/self.Tar[i]
        for var in h.values(): co[var]=co.get(var,0)-1
        self.con(co,lb=0)
        # valid linear Gini lower cut with Smax
        Smax=sum(self.C[i]/self.Tar[i] for i in stations)
        co={G:Smax*V}
        for var in h.values(): co[var]=co.get(var,0)-1
        self.con(co,lb=0)
        # objective upper bound if supplied
        if self.ub_obj is not None:
            co={G:1}
            for i in stations: co[e[i]]=co.get(e[i],0)+self.lam*self.w[i]
            self.con(co,ub=self.ub_obj)
        A=lil_matrix((len(self.rows),self.nvar))
        for r,co in enumerate(self.rows):
            for idx,val in co.items():
                if abs(val)>1e-12: A[r,idx]=val
        return np.array(self.c), Bounds(np.array(self.lb),np.array(self.ub)), np.array(self.integ), LinearConstraint(csr_matrix(A),np.array(self.lbs),np.array(self.ubs))

def obj_components(V,I,Tar,w,theta,lam):
    r=[theta[i-1]/Tar[i] for i in range(1,V+1)]
    S=sum(r); G=sum(abs(a-b) for a in r for b in r)/(2*V*S) if S>0 else 0
    P=sum(w[i]*abs(r[i-1]-1) for i in range(1,V+1))
    return G,P,G+lam*P

def route_feasible(V,dist,T,Q,tau,q):
    # q list length V, positive pickup, negative drop, zero absent. Operation time 2 tau total pickups.
    inds=[i for i,a in enumerate(q, start=1) if a!=0]
    if not inds: return True, []
    P=sum(max(0,a) for a in q)
    budget=T-2*tau*P
    if budget < -1e-9: return False, None
    n=len(inds); idx={inds[i]:i for i in range(n)}
    # dp dict (mask,last_index,load)->travel; last station actual
    from collections import defaultdict
    INF=1e18
    dp={}
    parent={}
    for pos,i in enumerate(inds):
        nl=q[i-1]
        if 0 <= nl <= Q:
            m=1<<pos; key=(m,pos,nl); val=dist[0,i]
            dp[key]=val; parent[key]=None
    full=(1<<n)-1
    best=INF; bestkey=None
    for mask_size in range(1,n+1):
        # iterate current list snapshot of mask size
        items=[(key,val) for key,val in dp.items() if key[0].bit_count()==mask_size]
        for (mask,lastpos,load),travel in items:
            last=inds[lastpos]
            # close
            if travel+dist[last,0] < best and mask==full:
                best=travel+dist[last,0]; bestkey=(mask,lastpos,load)
            rem=full^mask
            b=rem
            while b:
                lsb=b&-b; pos=lsb.bit_length()-1; j=inds[pos]
                nl=load+q[j-1]
                if 0<=nl<=Q:
                    nm=mask|lsb; nv=travel+dist[last,j]
                    key=(nm,pos,nl)
                    if nv < dp.get(key,INF)-1e-9:
                        dp[key]=nv; parent[key]=(mask,lastpos,load)
                b-=lsb
    if best <= budget+1e-9:
        # reconstruct
        seq=[]; key=bestkey
        while key is not None:
            seq.append(inds[key[1]]); key=parent[key]
        seq=seq[::-1]
        return True, seq
    return False, None

if __name__=='__main__':
    import sys, os
    path=sys.argv[1] if len(sys.argv)>1 else '/mnt/data/regen_candidate_V12_M1_average.txt'
    inst=parse(path)
    mb=MB(inst)
    c,bounds,integ,lc=mb.build()
    print('vars',len(c),'cons',lc.A.shape)
    t=time.time(); res=milp(c,integrality=integ,bounds=bounds,constraints=lc,options={'time_limit':40,'mip_rel_gap':0,'disp':False})
    print('status',res.status,res.message,'fun',res.fun,'gap',getattr(res,'mip_gap',None),'nodes',getattr(res,'mip_node_count',None),'time',time.time()-t)
    if res.x is not None:
        x=res.x; V,M,Qs,C,I,Tar,w,dist=inst
        theta=[round(x[mb.vi[('theta',i)]]) for i in range(1,V+1)]
        print('theta',theta,'comp',obj_components(V,I,Tar,w,theta,mb.lam))
        for k in range(M):
            q=[]
            for i in range(1,V+1): q.append(round(x[mb.vi[('p',k,i)]])-round(x[mb.vi[('d',k,i)]]))
            print('k',k,'q',q,'P',sum(max(0,a) for a in q),'feas',route_feasible(V,dist,mb.T,Qs[k],mb.tau,q))
