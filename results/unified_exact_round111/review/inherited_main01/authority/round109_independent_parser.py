"""R109 independent stdlib input, physical fleet and strict LP parser.

The mathematical parser/functions below are inherited byte-for-byte from the
audited R108 independent reviewer, rather than the campaign reconstruction.
The caller replaces IO/require functions with explicit-root guarded versions.
No import, call or operation creates a native environment or solves a model.
"""
from pathlib import Path
import ast, csv, hashlib, json, math, re
def data(path):return Path(path).read_bytes()
def txt(path):return data(path).decode('utf-8-sig')
def require(condition,message):
    if not condition:raise AssertionError(message)
def near(a,b,tol=1e-7):return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol

def input_file(p):
    t=txt(p); h=t.splitlines()[0]; m=re.fullmatch(r'(\d+)\s+(\d+)\s+(\[.*\])',h)
    require(m is not None,'input header independently parsed '+str(p))
    q={'V':int(m[1]),'M':int(m[2]),'Q':ast.literal_eval(m[3])}
    for k in ['capacities','initial','target','weights','min_ratio','points']:
        line=next(x for x in t.splitlines() if re.match(k+r'\s*=',x))
        q[k]=ast.literal_eval(line.split('=',1)[1].strip())
        require(len(q[k])==q['V']+1,'input vector length includes depot '+k+' '+str(p))
    require(len(q['Q'])==q['M'],'input capacity vector '+str(p))
    # Parser.cpp retained legacy max-10 rule, although no qualification input uses it.
    if abs(max(q['weights'][1:])-10)<=1e-6:q['weights']=[x/10 for x in q['weights']]
    require(all(q['target'][i]>0 and q['weights'][i]>=0 and math.isfinite(q['weights'][i]) for i in range(1,q['V']+1)), 'positive station targets and nonnegative finite weights '+str(p))
    return q

def physical(q, routes, T, lam=.15, pickup=60, drop=60):
    inventory=list(q['initial']); seen=set(); vehicles=set(); route_results=[]
    for r in routes:
        k=r['vehicle']; ns=r['nodes']; ops=r['operations']
        require(k not in vehicles and 0<=k<q['M'],'unique valid vehicle '+str(k)); vehicles.add(k)
        require(ns[0]==ns[-1]==0 and 0 not in ns[1:-1] and len(ns)==len(ops)+2,'depot round trip and one operation per visited node '+str(k))
        load=0; profile=[0]; pu=dr=0
        opmap={o['station']:o for o in ops}
        require(len(opmap)==len(ops) and set(opmap)==set(ns[1:-1]),'unique operation map matches visited node set '+str(k))
        for node in ns[1:-1]:
            op=opmap[node]
            i=op['station']; p=op['pickup']; d=op['drop']
            require(i==node and 1<=i<=q['V'] and i not in seen,'unique matching station '+str(i)); seen.add(i)
            require(all(isinstance(x,(int,float)) and math.isfinite(x) and abs(x-round(x))<=1e-5 and x>=0 for x in [p,d]),'integer finite nonnegative handling at '+str(i))
            require((p==0 or d==0) and p+d>=1,'one direction and nonzero visited service '+str(i))
            require(p<=q['initial'][i] and d<=q['capacities'][i]-q['initial'][i],'station handling upper bounds '+str(i))
            load+=p-d;profile.append(load); pu+=p;dr+=d;inventory[i]+=d-p
            require(0<=load<=q['Q'][k],'prefix vehicle capacity '+str(k)+' '+str(i))
        travel=sum(math.sqrt((q['points'][a][0]-q['points'][b][0])**2+(q['points'][a][1]-q['points'][b][1])**2)/1.5 for a,b in zip(ns,ns[1:]))
        handling=pickup*pu+drop*(dr+load)
        require(near(handling,(pickup+drop)*pu) and travel+handling<=T+1e-6,'return depot unload and total route duration '+str(k))
        route_results.append(dict(vehicle=k,travel_seconds=travel,handling_seconds=handling,duration_seconds=travel+handling,prefix_loads=profile,return_load=load,total_pickup=pu,total_station_drop=dr))
    require(len(vehicles)==q['M'],'all vehicles independently represented')
    require(all(0<=inventory[i]<=q['capacities'][i] for i in range(1,q['V']+1)),'final station bounds independently checked')
    rr=[inventory[i]/q['target'][i] for i in range(1,q['V']+1)]
    S=sum(rr); H=sum(abs(a-b) for i,a in enumerate(rr) for b in rr[i+1:]); G=H/(q['V']*S) if S>0 else 0
    P=sum(q['weights'][i]*abs(rr[i-1]-1) for i in range(1,q['V']+1))
    return dict(U=G+lam*P,G=G,P=P,S=S,H=H,final_inventories=inventory,routes=route_results)

NUM=r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
VAR=r'[A-Za-z_][A-Za-z_0-9]*'
def terms(s):
    # These writer files have a strict linear grammar and explicit section/row lines.
    result={}; pattern=re.compile(r'\s*([+-]?)\s*(?:('+NUM+r')\s+)?('+VAR+r')')
    at=0
    while at<len(s.strip()):
        m=pattern.match(s,at)
        if not m:raise AssertionError('unparsed LP term '+s[at:])
        coef=(-1 if m[1]=='-' else 1)*(float(m[2]) if m[2] else 1.0)
        result[m[3]]=result.get(m[3],0)+coef;at=m.end()
    return tuple(sorted((k,v) for k,v in result.items() if v))

def lp(p):
    sec=None; bounds={}; types={}; row=[]; objective=None; names=[]
    for line in txt(p).splitlines():
        s=line.strip()
        if not s or s.startswith('\\'):continue
        if s in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:sec=s;continue
        if sec=='Minimize':objective=terms(s.split(':',1)[1].strip())
        elif sec=='Subject To':
            lhs=s.split(':',1)[1].strip();m=re.fullmatch(r'(.*?)\s*(<=|>=|=)\s*([+-]?'+NUM+r')',lhs)
            require(m is not None,'linear row independently parsed')
            row.append(({'<=':'<','>=':'>','=':'='}[m[2]],float(m[3]),terms(m[1].strip())))
        elif sec=='Bounds':
            m=re.fullmatch(r'([+-]?'+NUM+r')\s*<=\s*('+VAR+r')\s*<=\s*([+-]?'+NUM+r')',s)
            if not m:raise AssertionError('unparsed LP bound '+s)
            require(m[2] not in bounds,'unique LP column bound')
            bounds[m[2]]=(float(m[1]),float(m[3]));names.append(m[2]);types[m[2]]='C'
        elif sec in ['Generals','Binaries']:
            require(s in bounds,'declared variable in bounds '+s);types[s]='I' if sec=='Generals' else 'B'
        else:raise AssertionError('unexpected LP line '+s)
    return dict(bounds=bounds,types=types,rows=row,objective=dict(objective),names=names)

