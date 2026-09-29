"""Full fixed-order quantity diagnostic, exact one-hot Gini MILP, Gurobi C API.

Research-only time cap. No production hook, no global-bound claim. Retains all
served stations as optional DAG nodes; changing sign/deleting zeros is allowed.
"""
import argparse
import ctypes as ct
import itertools
import json
import math
import os
import time
from pathlib import Path

from round96_prepare import ROOT, OUT, read, write, sha, citi, evidence

class Model:
    def __init__(self): self.bounds={}; self.binary=[]; self.rows=[]; self.objective={}
    def var(self,name,lo=0,hi=None,binary=False):
        assert name not in self.bounds
        self.bounds[name]=(lo,hi)
        if binary: self.binary.append(name)
        return name
    def row(self,terms,sense,rhs):
        assert all(k in self.bounds and math.isfinite(v) for k,v in terms.items())
        self.rows.append((terms,sense,rhs))
    @staticmethod
    def expr(d):
        return ' '.join(('+' if v>=0 else '-')+f' {abs(v):.17g} {k}' for k,v in d.items() if v!=0) or '0 G'
    def export(self,path):
        with path.open('x') as f:
            f.write('Minimize\n obj: '+self.expr(self.objective)+'\nSubject To\n')
            for j,(d,s,b) in enumerate(self.rows): f.write(f' c{j}: {self.expr(d)} {s} {b:.17g}\n')
            f.write('Bounds\n')
            for k,(a,b) in self.bounds.items():
                f.write(f' {a:.17g} <= {k}'+(f' <= {b:.17g}' if b is not None else '')+'\n')
            f.write('Binary\n '+'\n '.join(self.binary)+'\nEnd\n')
    def verify(self,x):
        assert set(x)==set(self.bounds)
        violation=0.
        for k,(a,b) in self.bounds.items():
            violation=max(violation,a-x[k],x[k]-b if b is not None else 0)
        for k in self.binary: violation=max(violation,abs(x[k]-round(x[k])))
        for d,s,b in self.rows:
            lhs=sum(v*x[k] for k,v in d.items())
            violation=max(violation,abs(lhs-b) if s=='=' else lhs-b if s=='<=' else b-lhs)
        assert violation<1e-6, ('mapped witness violates diagnostic',violation)
        return violation

def build(p,w):
    ins=citi.parse_instance_mirror(ROOT/p['instance_path']); n=ins['V']; b=ins['initial']; d=ins['target']; cap=ins['capacities']
    m=Model(); gmax=(n-1)/n; m.var('G',0,gmax);m.objective={'G':1.}
    served={i for r in w['routes'] for i in r['nodes'][1:-1]}; states={}; y=b.copy()
    for r in w['routes']:
        for op in r['operations']: y[op['station']]+=op['drop']-op['pickup']
    ratios=[y[i]/d[i] for i in range(1,n+1)]; total=sum(ratios)
    g=sum(abs(a-bb) for j,a in enumerate(ratios) for bb in ratios[j+1:])/(n*total) if total else 0
    x={'G':g}
    for i in range(1,n+1):
        states[i]=range(cap[i]+1) if i in served else [b[i]]
        m.var(f'r{i}',0,cap[i]/d[i]);m.var(f'e{i}',0)
        m.objective[f'e{i}']=float(p['lambda'])*ins['weights'][i]
        x[f'r{i}']=y[i]/d[i];x[f'e{i}']=abs(x[f'r{i}']-1)
        sums={};sumq={'G':-1};ratio={f'r{i}':1}
        for yy in states[i]:
            s=m.var(f's{i}_{yy}',0,1,True);q=m.var(f'q{i}_{yy}',0,gmax)
            sums[s]=1;sumq[q]=1;ratio[s]=-yy/d[i]
            m.row({q:1,s:-gmax},'<=',0)
            m.row({q:1,'G':-1},'<=',0)
            m.row({q:1,'G':-1,s:-gmax},'>=',-gmax)
            x[s]=float(yy==y[i]);x[q]=g*x[s]
        m.row(sums,'=',1);m.row(sumq,'=',0);m.row(ratio,'=',0)
        m.row({f'e{i}':1,f'r{i}':-1},'>=',-1);m.row({f'e{i}':1,f'r{i}':1},'>=',1)
    epigraph={}
    for i in range(1,n+1):
        for j in range(i+1,n+1):
            h=m.var(f'h{i}_{j}');epigraph[h]=1
            m.row({h:1,f'r{i}':-1,f'r{j}':1},'>=',0)
            m.row({h:1,f'r{i}':1,f'r{j}':-1},'>=',0)
            x[h]=abs(x[f'r{i}']-x[f'r{j}'])
        for yy in states[i]: epigraph[f'q{i}_{yy}']=-n*yy/d[i]
    m.row(epigraph,'<=',0)
    for route in w['routes']:
        k=route['vehicle']; nodes=route['nodes']; length=len(nodes); edges={};duration={}
        for a in range(length-1):
            for z in range(a+1,length):
                name=m.var(f'a{k}_{a}_{z}',0,1,True);edges[a,z]=name
                duration[name]=ins['distances'][nodes[a]][nodes[z]]
                x[name]=float(z==a+1)
        m.row({edges[0,z]:1 for z in range(1,length)},'=',1)
        m.row({edges[a,length-1]:1 for a in range(length-1)},'=',1)
        prefix={}; initial_sum=0
        for pos,i in enumerate(nodes[1:-1],1):
            # Both in and out equal 1-s[i,b_i]; the DAG excludes extraneous cycles.
            inc={edges[a,pos]:1 for a in range(pos)};inc[f's{i}_{b[i]}']=1;m.row(inc,'=',1)
            out={edges[pos,z]:1 for z in range(pos+1,length)};out[f's{i}_{b[i]}']=1;m.row(out,'=',1)
            initial_sum+=b[i]
            for yy in states[i]:
                prefix[f's{i}_{yy}']=yy
                duration[f's{i}_{yy}']=(p['pickup_seconds']+p['drop_seconds'])*max(0,b[i]-yy)
            m.row(dict(prefix),'<=',initial_sum)
            m.row(dict(prefix),'>=',initial_sum-ins['Q'][k])
        # Same mathematical T; no feasibility tolerance added to the RHS.
        m.row(duration,'<=',p['T_seconds'])
    return m,x,ins,states

class Gurobi:
    def __init__(self):
        self.dll=ct.CDLL('D:/gurobi1302/win64/bin/gurobi130.dll')
        ptr=ct.c_void_p; pp=ct.POINTER(ptr); st=ct.c_char_p; ip=ct.POINTER(ct.c_int);dp=ct.POINTER(ct.c_double)
        specs={'GRBloadenvinternal':[pp,st,ct.c_int,ct.c_int,ct.c_int], 'GRBreadmodel':[ptr,st,pp],
            'GRBsetintparam':[ptr,st,ct.c_int],'GRBsetdblparam':[ptr,st,ct.c_double],
            'GRBgetintparam':[ptr,st,ip],'GRBgetdblparam':[ptr,st,dp],
            'GRBgetintattr':[ptr,st,ip],'GRBgetdblattr':[ptr,st,dp],
            'GRBgetdblattrarray':[ptr,st,ct.c_int,ct.c_int,dp],
            'GRBgetstrattrarray':[ptr,st,ct.c_int,ct.c_int,ct.POINTER(st)],
            'GRBgetvarbyname':[ptr,st,ip],'GRBsetdblattrelement':[ptr,st,ct.c_int,ct.c_double],
            'GRBoptimize':[ptr],'GRBwrite':[ptr,st]}
        for name,args in specs.items():
            fun=getattr(self.dll,name);fun.argtypes=args;fun.restype=ct.c_int
        self.dll.GRBgetenv.argtypes=[ptr];self.dll.GRBgetenv.restype=ptr
        self.dll.GRBgeterrormsg.argtypes=[ptr];self.dll.GRBgeterrormsg.restype=st
        self.dll.GRBfreemodel.argtypes=[ptr];self.dll.GRBfreemodel.restype=None
        self.dll.GRBfreeenv.argtypes=[ptr];self.dll.GRBfreeenv.restype=None
    def call(self,name,*args):
        rc=getattr(self.dll,name)(*args)
        if rc: raise RuntimeError((name,rc))
    def attr(self,model,name,integer=False):
        value=ct.c_int() if integer else ct.c_double()
        self.call('GRBgetintattr' if integer else 'GRBgetdblattr',model,name.encode(),ct.byref(value));return value.value

def solve(case,dest,start):
    p=case['panel'];w=read(ROOT/case['witness_path'])
    assert sha(ROOT/case['witness_path'])==case['witness_sha256']
    assert sha(ROOT/p['instance_path'])==p['input_sha256']
    before=evidence.physical_module.physical(p,w);assert before['original_T_feasible']
    m,x,ins,states=build(p,w); residual=m.verify(x)
    dest.mkdir(parents=True,exist_ok=False);m.export(dest/'model.lp')
    write(dest/'mapping.json',dict(original_witness_residual=residual,initial=before,
        model_sha256=sha(dest/'model.lp'),variables=len(m.bounds),rows=len(m.rows),
        set_definition='unserved fixed; original owner and relative order; optional zero deletion; both service signs',
        scope='restricted diagnostic only; bounds are NOT original problem global bounds'))
    api=Gurobi();env=ct.c_void_p();model=ct.c_void_p()
    api.call('GRBloadenvinternal',ct.byref(env),str(dest/'native.log').encode(),13,0,2)
    try:
        api.call('GRBreadmodel',env,str(dest/'model.lp').encode(),ct.byref(model))
        menv=api.dll.GRBgetenv(model);settings={}
        for name,val in {'Threads':1,'Seed':0,'Presolve':-1,'OutputFlag':1,'LogToConsole':0}.items():
            api.call('GRBsetintparam',menv,name.encode(),val);out=ct.c_int();api.call('GRBgetintparam',menv,name.encode(),ct.byref(out));assert out.value==val;settings[name]=val
        for name,val in {'MIPGap':0.,'MIPGapAbs':0.,'FeasibilityTol':1e-6,'IntFeasTol':1e-5,'OptimalityTol':1e-6}.items():
            api.call('GRBsetdblparam',menv,name.encode(),val);out=ct.c_double();api.call('GRBgetdblparam',menv,name.encode(),ct.byref(out));assert out.value==val;settings[name]=val
        # The historical witness is allowed only in this independent diagnostic.
        for name,val in x.items():
            index=ct.c_int();api.call('GRBgetvarbyname',model,name.encode(),ct.byref(index));assert index.value>=0
            api.call('GRBsetdblattrelement',model,b'Start',index.value,val)
        remaining=case['cap_seconds']-(time.perf_counter()-start)-2
        assert remaining>0
        api.call('GRBsetdblparam',menv,b'TimeLimit',remaining)
        write(dest/'optimize_started.json',dict(settings=settings,time_limit=remaining,started_unix=time.time(),optimizer_calls=1))
        api.call('GRBoptimize',model)
        status=api.attr(model,'Status',True); count=api.attr(model,'SolCount',True)
        result=dict(status=status,solcount=count,restricted_bound=api.attr(model,'ObjBound'),
            runtime=api.attr(model,'Runtime'),nodes=api.attr(model,'NodeCount'),initial_F=before['F'],
            original_global_bound=False,optimizer_calls=1,certificate=False,improved=False)
        if count:
            size=api.attr(model,'NumVars',True);vals=(ct.c_double*size)();names=(ct.c_char_p*size)()
            api.call('GRBgetdblattrarray',model,b'X',0,size,vals);api.call('GRBgetstrattrarray',model,b'VarName',0,size,names)
            values={names[j].decode():vals[j] for j in range(size)}
            final_y=ins['initial'].copy()
            for i,domain in states.items():
                hits=[yy for yy in domain if values[f's{i}_{yy}']>.5];assert len(hits)==1;final_y[i]=hits[0]
            routes=[]
            for r in w['routes']:
                nodes=[i for i in r['nodes'][1:-1] if final_y[i]!=ins['initial'][i]]
                routes.append(dict(vehicle=r['vehicle'],nodes=[0]+nodes+[0],operations=[dict(station=i,
                    pickup=max(0,ins['initial'][i]-final_y[i]),drop=max(0,final_y[i]-ins['initial'][i])) for i in nodes]))
            ratio=[final_y[i]/ins['target'][i] for i in range(1,ins['V']+1)];ss=sum(ratio)
            gg=sum(abs(a-b) for j,a in enumerate(ratio) for b in ratio[j+1:])/(ins['V']*ss) if ss else 0
            penalty=sum(ins['weights'][i]*abs(ratio[i-1]-1) for i in range(1,ins['V']+1))
            witness=dict(routes=routes,inventory=final_y,F=gg+p['lambda']*penalty,G=gg,P=penalty)
            checked=evidence.physical_module.physical(p,witness);assert checked['original_T_feasible']
            assert result['restricted_bound']<=checked['F']+1e-7
            result.update(final=checked,model_objective=api.attr(model,'ObjVal'),
                          restricted_gap=checked['F']-result['restricted_bound'],
                          certificate=status==2 and abs(checked['F']-result['restricted_bound'])<=1e-7,
                          improved=checked['F']<before['F']-1e-12)
            write(dest/'witness.json',witness);api.call('GRBwrite',model,str(dest/'solution.sol').encode())
        result['elapsed_before_result_write']=time.perf_counter()-start
        write(dest/'result.json',result)
    finally:
        if model: api.dll.GRBfreemodel(model)
        api.dll.GRBfreeenv(env)

def main():
    start=time.perf_counter();parser=argparse.ArgumentParser();parser.add_argument('id');args=parser.parse_args()
    cases=read(OUT/'fixed_route_cases.json')['cases'];case=next(c for c in cases if c['id']==args.id)
    # Same physical core as the formal historical campaigns; restore is automatic at exit.
    kernel=ct.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ct.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ct.c_void_p,ct.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    solve(case,OUT/'fixed_route'/args.id,start)

if __name__=='__main__': main()
