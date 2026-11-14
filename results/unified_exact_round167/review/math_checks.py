"""Independent, solver-free audit of emitted rows; no model or solver imports.

The checker recovers each actual network from LP balance rows, rather than
calling or reimplementing the C++ constructor. Small path traversal checks
serialized labels/costs; the general projection theorem is reviewed separately.
"""
from pathlib import Path
from fractions import Fraction as Q
from collections import defaultdict, Counter
from functools import lru_cache
import re, json, hashlib, time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round167'
START=time.perf_counter()

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def expression(s):
    tokens=s.split();result=defaultdict(Q);sign=Q(1);at=0
    while at<len(tokens):
        token=tokens[at]
        if token in ('+','-'):
            sign=Q(1 if token=='+' else -1);at+=1;continue
        try:
            amount=Q(token);at+=1;name=tokens[at]
        except ValueError:
            amount=Q(1);name=token
        assert re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name),(s,name)
        result[name]+=sign*amount;sign=Q(1);at+=1
    return {k:v for k,v in result.items() if v}

@lru_cache(maxsize=1)
def rows(path):
    text=path.read_text();section=text.split('Subject To\n',1)[1].split('\nBounds',1)[0]
    starts=list(re.finditer(r'(?m)^\s*([^\s:]+):',section));result={}
    for j,m in enumerate(starts):
        raw=section[m.end():starts[j+1].start() if j+1<len(starts) else len(section)]
        halves=re.split(r'\s(<=|>=|=)\s',raw.strip());assert len(halves)==3,(m[1],halves)
        result[m[1]]=(expression(halves[0]),halves[1],Q(halves[2].strip()))
    return text,result

def audit_network(folder,station,domain,mask):
    text,allrows=rows(folder/'model.lp');i=station;prefix=f'd167_f_{i}_';qp=f'd167_q_{i}_'
    selected={name:value for name,value in allrows.items() if name.startswith('d167_') and (name.startswith(f'd167_link_') and name.endswith('_'+str(i)) or re.match(r'd167_(?:mass|weight|lo|hi|delta|w)_'+str(i)+r'_',name))}
    # Recover incidence independently from the emitted f-balance rows.
    arcs=defaultdict(dict);mass={};weighted={};nzs=0
    for name,(terms,sense,rhs) in selected.items():
        nzs+=len(terms)
        if name.startswith(f'd167_mass_{i}_'):
            node=int(name.rsplit('_',1)[1]);mass[node]=(terms,sense,rhs)
            for var,coefficient in terms.items():
                assert var.startswith(prefix) and coefficient in (1,-1)
                edge=int(var[len(prefix):]);arcs[edge]['tail' if coefficient==1 else 'head']=node
        elif name.startswith(f'd167_weight_{i}_'):
            node=int(name.rsplit('_',1)[1]);weighted[node]=(terms,sense,rhs)
    assert set(mass)==set(weighted) and 0 in mass and 1 not in mass
    assert mass[0][1:]==('=',Q(1))
    for node,(terms,sense,rhs) in mass.items():
        expected={var.replace(prefix,qp):coef for var,coef in terms.items()}
        if node==0:expected['G']=Q(-1)
        assert weighted[node]==(expected,'=',Q(0)),(folder,i,node,'q conservation')
        if node!=0:assert (sense,rhs)==('=',Q(0))
    for edge,arc in arcs.items():
        assert 'tail' in arc
        if 'head' not in arc:arc['head']=1
    assert set(arcs)==set(range(len(arcs)))
    links={name:allrows[f'd167_link_{name}_{i}'] for name in ('Y','M','V','Z')}
    for terms,sense,rhs in links.values():assert sense=='=' and rhs==0
    def fcost(link,edge,sign):return sign*links[link][0].get(prefix+str(edge),Q(0))
    for edge,arc in arcs.items():
        arc['Y']=fcost('Y',edge,1);arc['M']=fcost('M',edge,-1);arc['V']=fcost('V',edge,-1)
        assert links['Z'][0].get(qp+str(edge),Q(0))==arc['Y'],(folder,i,edge,'Z uses another q')
    digits={};code_nz=0
    for h in range(domain['d']):
        delta,sense,rhs=allrows[f'd167_delta_{i}_{h}'];w,ws,wr=allrows[f'd167_w_{i}_{h}']
        assert (sense,rhs)==('=',Q(0)) and (ws,wr)==('=',Q(0))
        assert delta[f'bit_{i}_{h}']==-1 and w[f'prod_{i}_{h}']==-1
        expected={var.replace(prefix,qp):coefficient for var,coefficient in delta.items() if var.startswith(prefix)}
        actual={var:coefficient for var,coefficient in w.items() if var.startswith(qp)}
        assert actual==expected
        for var,coef in delta.items():
            if var.startswith(prefix):
                edge=int(var[len(prefix):]);assert coef==1 and edge not in digits;digits[edge]=h
    outgoing=defaultdict(list)
    for edge,arc in arcs.items():outgoing[arc['tail']].append(edge)
    actual=[];seen_paths=[]
    def walk(node,path,visited):
        assert node not in visited,'cycle in emitted DAG'
        if node==1:
            assert len(path)==domain['d']+2,(folder,i,'incomplete bit path')
            y=sum(arcs[e]['Y'] for e in path);movement=sum(arcs[e]['M'] for e in path);visits=sum(arcs[e]['V'] for e in path)
            assert y.denominator==1;y=int(y)
            assert movement==abs(domain['b']-y) and visits==int(y!=domain['b']),(folder,i,y,'service cost')
            assert arcs[path[0]]['Y']==arcs[path[-1]]['Y']==0
            for j,edge in enumerate(path[1:-1]):
                h=domain['d']-1-j;value=(y>>h)&1
                assert arcs[edge]['Y']==value*(1<<h)
                assert (edge in digits)==bool(value)
                if value:assert digits[edge]==h
            actual.append(y);seen_paths.append((y,path));return
        for edge in outgoing[node]:walk(arcs[edge]['head'],path+[edge],visited|{node})
    walk(0,[],set())
    expected=list(range(domain['l'],domain['u']+1))
    assert sorted(actual)==expected and len(actual)==len(set(actual)),(folder,i,'path legality/bijection')
    relevant={int(h):int(value) for h,value in mask}
    got=[y for y,path in seen_paths if all(((y>>h)&1)==v for h,v in relevant.items())]
    expect=[y for y in expected if all(((y>>h)&1)==v for h,v in relevant.items())]
    assert sorted(got)==expect
    # Envelope rows agree on every actual edge and share those same q columns.
    for edge in arcs:
        low,sense,rhs=allrows[f'd167_lo_{i}_{edge}'];high,hs,hr=allrows[f'd167_hi_{i}_{edge}']
        assert sense=='>=' and rhs==0 and hs=='<=' and hr==0
        assert low[qp+str(edge)]==high[qp+str(edge)]==1
        assert set(low)<=set([qp+str(edge),prefix+str(edge)]) and set(high)<=set([qp+str(edge),prefix+str(edge)])
        a=-low.get(prefix+str(edge),Q(0));b=-high.get(prefix+str(edge),Q(0));assert 0<=a<=b<=1
    n=2+len(mass)-1;aG=len(arcs);t=sum(arc['head']==1 for arc in arcs.values())
    assert n==domain['nodes'] and aG==domain['edges']
    assert n<=2+domain['parts']*(1+4*domain['d']) and aG<=domain['parts']*(8*domain['d']+5)
    assert len(selected)==2*(n-1)+2*aG+4+2*domain['d']
    fy=sum(bool(arc['Y']) for arc in arcs.values());fm=sum(bool(arc['M']) for arc in arcs.values());fv=sum(bool(arc['V']) for arc in arcs.values())
    common_nz=sum(not v.startswith(prefix) for v in links['M'][0])+sum(not v.startswith(prefix) for v in links['V'][0])
    expected_nz=6*aG+aG*(int(a!=0)+int(b!=0))-2*t+4*fy+fm+fv+3+common_nz+2*domain['d']
    assert expected_nz==nzs,(folder,i,expected_nz,nzs,'nonzero formula')
    return dict(station=i,states=len(actual),nodes=n,arcs=aG,rows=len(selected),nonzeros=nzs)

def main():
    manifest=read(OUT/'diagnostic_manifest.json');positions=read(OUT/'positions.json');reports=[]
    for p in positions:
        if p['representation']!='D167':continue
        folder=ROOT/p['folder'];pre=read(folder/'prepare.json')
        if 'stations' in pre:
            for d in pre['stations']:
                result=audit_network(folder,d['i'],d,pre['mask'] if d['i']==pre['selected_station'] else [])
                reports.append(dict(id=p['id'],**result))
        else:
            C,b=(8,4) if pre['id']=='L3' else (4,2)
            # Graph dimensions come directly from emitted incidence structure.
            _,rr=rows(folder/'model.lp');nn=sum(k.startswith('d167_mass_1_') for k in rr)+1;aa=sum(k.startswith('d167_lo_1_') for k in rr)
            d=dict(l=0,u=C,b=b,C=C,d=max(1,C.bit_length()),nodes=nn,edges=aa,parts=3)
            result=audit_network(folder,1,d,[[0,1],[1,0]] if pre['id']=='L3' else [[0,1]])
            reports.append(dict(id=p['id'],**result))
    # Read the prescribed strict witness against every emitted local C166 row.
    _,rr=rows(OUT/'qualification/local/L1_C166/model.lp')
    witness={'Y':Q(2),'M':Q(0),'V':Q(0),'G':Q(1,4),'Z':Q(1,2),
             'state_1_2':Q(1),'state_g_1_2':Q(1,4),'bit_1_0':Q(1),'bit_1_1':Q(1,2),
             'prod_1_0':Q(1,4),'prod_1_1':Q(1,8)}
    for name,(terms,sense,rhs) in rr.items():
        lhs=sum(coef*witness.get(var,Q(0)) for var,coef in terms.items())
        assert {'=':lhs==rhs,'<=':lhs<=rhs,'>=':lhs>=rhs}[sense],(name,lhs,sense,rhs)
    # The source code/headers and manifest must still match the inspected bytes.
    source_binding={p:sha(ROOT/p) for p in ['src/round167_research.cpp','include/Round167ConditionalState.hpp','results/unified_exact_round167/conditional_state_theory.md']}
    for path,digest in manifest['CPP_sources'].items():assert source_binding[path]==digest
    summary=dict(PASS=True,reviewer='/root/math_review',Optimize=0,independent_offline_seconds=time.perf_counter()-START,
                 canonical_and_tiny_local_networks=len(reports),paths=sum(r['states'] for r in reports),
                 exact_C166_witness_rows=len(rr),same_graph_mass_weight_incidence=True,
                 path_bijection_costs_absolute_digits=True,dimension_nonzero_formula=True,source_bindings=source_binding,
                 networks=reports)
    target=Path(__file__).with_name('math_checks.json');target.write_text(json.dumps(summary,indent=2)+'\n')
    print({k:v for k,v in summary.items() if k not in ('networks','source_bindings')})
if __name__=='__main__':main()
