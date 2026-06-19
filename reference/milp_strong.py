# Stronger arc MILP for EB-BRP. Based on milp_test, with operation time simplification, McCormick strengthening, TSP subset cuts, and optional UB.
import re, ast, math, time
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, csr_matrix


def parse(path):
    txt=open(path).read(); first=txt.strip().splitlines()[0].split(maxsplit=2)
    V=int(first[0]); M=int(first[1]); Qs=ast.literal_eval(first[2])
    def get(name):
        m=re.search(rf'{name}\s*=\s*(\[[\s\S]*?\])', txt); return ast.literal_eval(m.group(1))
    C=get('capacities'); I=get('initial'); Tar=get('target'); w=get('weights')
    m=re.search(r'distances\s*=\s*\[([\s\S]*?)\]\s*$', txt); rows=[]
    for line in m.group(1).splitlines():
        line=line.strip().strip(',')
        if line.startswith('{'): rows.append([float(x) for x in line.strip('{}').split(',')])
    return V,M,Qs,C,I,Tar,w,np.array(rows)

def min_cycles(dist,V):
    INF=1e18;nmask=1<<V;dp={}
    for i in range(1,V+1): dp[(1<<(i-1),i)]=dist[0,i]
    for mask in range(1,nmask):
        for last in range(1,V+1):
            val=dp.get((mask,last))
            if val is None: continue
            b=(nmask-1)^mask
            while b:
                lsb=b&-b; j=lsb.bit_length(); nm=mask|lsb; nv=val+dist[last,j]; key=(nm,j)
                if nv<dp.get(key,INF): dp[key]=nv
                b-=lsb
    L=[0.0]*nmask
    for mask in range(1,nmask):
        L[mask]=min(dp.get((mask,last),INF)+dist[last,0] for last in range(1,V+1) if mask>>(last-1)&1)
    return L

class Strong:
    def __init__(self, inst, tau=60, T=3600, lam=0.15, ub_obj=None, subset_cuts=True):
        self.V,self.M,self.Qs,self.C,self.I,self.Tar,self.w,self.dist=inst
        self.tau=tau; self.T=T; self.lam=lam; self.ub_obj=ub_obj; self.subset_cuts=subset_cuts
        self.n=0; self.vi={}; self.names=[]; self.c=[]; self.lb=[]; self.ub=[]; self.integr=[]
        self.rows=[]; self.lbs=[]; self.ubs=[]
    def v(self,name,lb=0,ub=np.inf,obj=0,integ=0):
        idx=self.n; self.n+=1; self.vi[name]=idx; self.names.append(name); self.lb.append(lb); self.ub.append(ub); self.c.append(obj); self.integr.append(integ); return idx
    def con(self,co,lb=-np.inf,ub=np.inf): self.rows.append(co); self.lbs.append(lb); self.ubs.append(ub)
    def build(self):
        V,M=self.V,self.M; nodes=range(V+1); stations=range(1,V+1)
        x={}
        for k in range(M):
            for i in nodes:
                for j in nodes:
                    if i!=j: x[k,i,j]=self.v(('x',k,i,j),0,1,0,1)
        y={}; mode={}; p={}; d={}; load={}; order={}
        for k in range(M):
            Q=self.Qs[k]
            for i in stations:
                y[k,i]=self.v(('y',k,i),0,1,0,1)
                mode[k,i]=self.v(('mode',k,i),0,1,0,1)
                p[k,i]=self.v(('p',k,i),0,min(self.I[i],Q),0,1)
                d[k,i]=self.v(('d',k,i),0,min(self.C[i]-self.I[i],Q),0,1)
                load[k,i]=self.v(('load',k,i),0,Q,0,1)
                order[k,i]=self.v(('ord',k,i),0,V,0,0)
        dep={k:self.v(('dep',k),0,self.Qs[k],0,1) for k in range(M)}
        theta={};rho={};e={}
        for i in stations:
            theta[i]=self.v(('theta',i),0,self.C[i],0,1)
            rho[i]=self.v(('rho',i),0,self.C[i]/self.Tar[i],0,0)
            e[i]=self.v(('e',i),0,max(1,self.C[i]/self.Tar[i]-1),self.lam*self.w[i],0)
        h={}
        for i in stations:
            for j in stations:
                if i<j: h[i,j]=self.v(('h',i,j),0,self.C[i]/self.Tar[i]+self.C[j]/self.Tar[j],0,0)
        G=self.v(('G',),0,1,1,0)
        bits={}; prod={}; zprod={}
        for i in stations:
            zprod[i]=self.v(('zprod',i),0,self.C[i],0,0)
            for b in range(math.ceil(math.log2(self.C[i]+1))):
                bits[i,b]=self.v(('bit',i,b),0,1,0,1)
                prod[i,b]=self.v(('prod',i,b),0,1,0,0)
        # route flow
        for k in range(M):
            self.con({x[k,0,j]:1 for j in stations},0,1)
            co={}
            for j in stations: co[x[k,0,j]]=co.get(x[k,0,j],0)+1
            for i in stations: co[x[k,i,0]]=co.get(x[k,i,0],0)-1
            self.con(co,0,0)
            for i in stations:
                self.con({**{x[k,i,j]:1 for j in nodes if j!=i}, y[k,i]:-1},0,0)
                self.con({**{x[k,j,i]:1 for j in nodes if j!=i}, y[k,i]:-1},0,0)
        for i in stations: self.con({y[k,i]:1 for k in range(M)},0,1)
        # MTZ
        for k in range(M):
            for i in stations:
                self.con({order[k,i]:1,y[k,i]:-1},lb=0)
                self.con({order[k,i]:1,y[k,i]:-V},ub=0)
            for i in stations:
                for j in stations:
                    if i!=j: self.con({order[k,i]:1,order[k,j]:-1,x[k,i,j]:V},ub=V-1)
        # ops/load/time
        for k in range(M):
            Q=self.Qs[k]
            for i in stations:
                Pmax=min(self.I[i],Q); Dmax=min(self.C[i]-self.I[i],Q)
                self.con({p[k,i]:1,y[k,i]:-Pmax},ub=0)
                self.con({d[k,i]:1,y[k,i]:-Dmax},ub=0)
                self.con({mode[k,i]:1,y[k,i]:-1},ub=0)
                self.con({p[k,i]:1,mode[k,i]:-Pmax},ub=0)
                self.con({d[k,i]:1,y[k,i]:-Dmax,mode[k,i]:Dmax},ub=0)
                self.con({p[k,i]:1,d[k,i]:1,y[k,i]:-1},lb=0)
                self.con({load[k,i]:1,y[k,i]:-Q},ub=0)
                self.con({load[k,i]:1,p[k,i]:-1,d[k,i]:1,x[k,0,i]:Q},ub=Q)
                self.con({load[k,i]:1,p[k,i]:-1,d[k,i]:1,x[k,0,i]:-Q},lb=-Q)
            for i in stations:
                for j in stations:
                    if i==j: continue
                    self.con({load[k,j]:1,load[k,i]:-1,p[k,j]:-1,d[k,j]:1,x[k,i,j]:Q},ub=Q)
                    self.con({load[k,j]:1,load[k,i]:-1,p[k,j]:-1,d[k,j]:1,x[k,i,j]:-Q},lb=-Q)
            co={dep[k]:1}
            for i in stations: co[p[k,i]]=co.get(p[k,i],0)-1; co[d[k,i]]=co.get(d[k,i],0)+1
            self.con(co,0,0)
            # strengthened duration: travel + 2*tau*sum(p) <= T exactly when dep=sum p-d
            co={}
            for i in nodes:
                for j in nodes:
                    if i!=j: co[x[k,i,j]]=self.dist[i,j]
            for i in stations: co[p[k,i]]=co.get(p[k,i],0)+2*self.tau
            self.con(co,ub=self.T)
        if self.subset_cuts:
            Lcyc=min_cycles(self.dist,V); big=10000.0
            for k in range(M):
                for mask in range(1,1<<V):
                    S=[i for i in stations if mask>>(i-1)&1]
                    co={}
                    for i in S:
                        co[p[k,i]]=co.get(p[k,i],0)+2*self.tau
                        co[y[k,i]]=co.get(y[k,i],0)+big
                    self.con(co,ub=self.T-Lcyc[mask]+big*len(S))
        # final/rho/e
        for i in stations:
            co={theta[i]:1}
            for k in range(M): co[p[k,i]]=co.get(p[k,i],0)+1; co[d[k,i]]=co.get(d[k,i],0)-1
            self.con(co,self.I[i],self.I[i])
            self.con({rho[i]:1,theta[i]:-1/self.Tar[i]},0,0)
            self.con({e[i]:1,rho[i]:-1},lb=-1)
            self.con({e[i]:1,rho[i]:1},lb=1)
        for (i,j),var in h.items():
            self.con({var:1,rho[i]:-1,rho[j]:1},lb=0)
            self.con({var:1,rho[i]:1,rho[j]:-1},lb=0)
        for i in stations:
            L=math.ceil(math.log2(self.C[i]+1)); co={theta[i]:1}
            for b in range(L): co[bits[i,b]]=co.get(bits[i,b],0)-(1<<b)
            self.con(co,0,0)
            co={zprod[i]:1}
            for b in range(L): co[prod[i,b]]=co.get(prod[i,b],0)-(1<<b)
            self.con(co,0,0)
            C=self.C[i]
            self.con({zprod[i]:1,G:-C},ub=0); self.con({zprod[i]:1,theta[i]:-1},ub=0); self.con({zprod[i]:1,theta[i]:-1,G:-C},lb=-C)
            for b in range(L):
                self.con({prod[i,b]:1,bits[i,b]:-1},ub=0)
                self.con({prod[i,b]:1,G:-1},ub=0)
                self.con({prod[i,b]:1,G:-1,bits[i,b]:-1},lb=-1)
        co={}
        for i in stations: co[zprod[i]]=co.get(zprod[i],0)+V/self.Tar[i]
        for var in h.values(): co[var]=co.get(var,0)-1
        self.con(co,lb=0)
        Smax=sum(self.C[i]/self.Tar[i] for i in stations); co={G:Smax*V}
        for var in h.values(): co[var]=co.get(var,0)-1
        self.con(co,lb=0)
        if self.ub_obj is not None:
            co={G:1}
            for i in stations: co[e[i]]=co.get(e[i],0)+self.lam*self.w[i]
            self.con(co,ub=self.ub_obj)
        A=lil_matrix((len(self.rows),self.n))
        for r,co in enumerate(self.rows):
            for idx,val in co.items():
                if abs(val)>1e-12: A[r,idx]=val
        return np.array(self.c), Bounds(np.array(self.lb),np.array(self.ub)), np.array(self.integr), LinearConstraint(csr_matrix(A),np.array(self.lbs),np.array(self.ubs))

def solve(path,tl=30):
    inst=parse(path); mb=Strong(inst); c,b,i,lc=mb.build(); print('vars',len(c),'cons',lc.A.shape)
    t=time.time(); res=milp(c,integrality=i,bounds=b,constraints=lc,options={'time_limit':tl,'mip_rel_gap':0,'disp':False})
    print('status',res.status,'fun',res.fun,'gap',getattr(res,'mip_gap',None),'nodes',getattr(res,'mip_node_count',None),'time',time.time()-t)
    if res.x is not None:
        V,M,Qs,C,I,Tar,w,dist=inst; x=res.x
        print('theta',[round(x[mb.vi[('theta',k)]]) for k in range(1,V+1)])
        for kk in range(M):
            print('k',kk,[(j,round(x[mb.vi[('p',kk,j)]]),round(x[mb.vi[('d',kk,j)]])) for j in range(1,V+1) if x[mb.vi[('y',kk,j)]]>0.5])
    return res
if __name__=='__main__':
    import sys
    solve(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/regen_candidate_V12_M1_average.txt', float(sys.argv[2]) if len(sys.argv)>2 else 30)
