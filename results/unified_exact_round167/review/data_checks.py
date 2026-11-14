"""Independent read-only checks of Round167 artifacts; never loads a solver.

The LP reader, physical checks, graph recovery and KKT calculations below
are independent of the author's C++ implementation and summary reader.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime,timezone,timedelta
import csv,hashlib,json,math,re,time,zipfile

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round167'
Q=OUT/'qualification'
REVIEW=OUT/'review'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def close(a,b,tol=1e-10):return abs(a-b)<=tol*max(1,abs(a),abs(b))
NUM=r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
TOK=re.compile(r'[+-]|'+NUM+r'|[A-Za-z_][A-Za-z_0-9.]*')
def expr(s):
    tokens=TOK.findall(s);i=0;sign=1;d=defaultdict(float)
    while i<len(tokens):
        if tokens[i] in ('+','-'):
            sign=-1 if tokens[i]=='-' else 1;i+=1
        else:sign=1
        assert i<len(tokens),s
        if re.fullmatch(NUM,tokens[i]):value=sign*float(tokens[i]);i+=1
        else:value=float(sign)
        assert i<len(tokens) and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9.]*',tokens[i]),(s,tokens,i)
        d[tokens[i]]+=value;i+=1
    return dict(d)
def parse_lp(path):
    section=None;objective=[];rowlines=[];boundlines=[];binaries=[];integers=[]
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        line=raw.strip()
        if not line or line.startswith('\\'):continue
        if line in ('Minimize','Subject To','Bounds','Binaries','Generals','End'):
            section=line;continue
        if section=='Minimize':objective.append(line)
        elif section=='Subject To':
            if ':' in line:rowlines.append(line)
            else:rowlines[-1]+=' '+line
        elif section=='Bounds':boundlines.append(line)
        elif section=='Binaries':binaries.extend(line.split())
        elif section=='Generals':integers.extend(line.split())
        else:raise AssertionError((path,section,line))
    obj=expr(' '.join(objective));vars=set(obj);rows=[]
    for line in rowlines:
        name,body=line.split(':',1)
        match=re.fullmatch(r'\s*(.*?)\s*(<=|>=|=)\s*([+-]?'+NUM+r')\s*',body)
        assert match,(path,line)
        coefficients=expr(match[1]);vars.update(coefficients)
        rows.append((name, {v:a for v,a in coefficients.items() if a!=0},match[2],float(match[3])))
    boundupdates={}
    for line in boundlines:
        tokens=line.split()
        if len(tokens)==5 and tokens[1]==tokens[3]=='<=':
            lo,v,hi=float(tokens[0]),tokens[2],float(tokens[4])
        elif len(tokens)==3 and tokens[1]=='<=':
            v=tokens[0];lo,hi=0.,float(tokens[2])
        elif len(tokens)==3 and tokens[1]=='>=':
            v=tokens[0];lo,hi=float(tokens[2]),math.inf
        elif len(tokens)==3 and tokens[1]=='=':
            v=tokens[0];lo=hi=float(tokens[2])
        elif len(tokens)==2 and tokens[1]=='free':
            v=tokens[0];lo,hi=-math.inf,math.inf
        else:raise AssertionError((path,line))
        vars.add(v);boundupdates[v]=(lo,hi)
    vars.update(binaries);vars.update(integers)
    bounds={v:(0.,1. if v in binaries else math.inf) for v in vars};bounds.update(boundupdates)
    types={v:'B' if v in binaries else 'I' if v in integers else 'C' for v in vars}
    return dict(objective={v:obj.get(v,0) for v in vars},vars=vars,rows=rows,bounds=bounds,types=types,
                binaries=set(binaries),integers=set(integers))
def read_vector(path):
    if path.suffix=='.csv':return {r['name']:float(r['value']) for r in csv.DictReader(path.open(encoding='utf-8-sig'))}
    return {line.split()[0]:float(line.split()[1]) for line in path.read_text().splitlines() if line and not line.startswith('#')}
def audit_primal(model,x,integer=False):
    assert set(x)==model['vars'],(set(x)-model['vars'],model['vars']-set(x))
    bv=iv=cv=0.;objective=0.
    for v in model['vars']:
        lo,hi=model['bounds'][v];bv=max(bv,lo-x[v],x[v]-hi)
        if integer and model['types'][v]!='C':iv=max(iv,abs(x[v]-round(x[v])))
        objective+=model['objective'][v]*x[v]
    for name,terms,sense,rhs in model['rows']:
        val=math.fsum(a*x[v] for v,a in terms.items())
        violation=abs(val-rhs) if sense=='=' else val-rhs if sense=='<=' else rhs-val
        cv=max(cv,violation)
    return dict(objective=objective,bound_violation=bv,row_violation=cv,integer_violation=iv)
def row_same(a,b):
    return a[0]==b[0] and a[1].keys()==b[1].keys() and all(close(a[1][v],b[1][v]) for v in a[1]) and a[2]==b[2] and close(a[3],b[3])
def read_rows(path):return list(csv.DictReader(path.open(encoding='utf-8-sig')))
def physical(x):
    # The inherited input has two target-2 stations, initial (3,0), Q=3,
    # zero travel, one vehicle and pickup/drop/unload time 60 seconds/unit.
    Y=[round(x['Y_1']),round(x['Y_2'])];b=[3,0]
    stops=[];at=0
    arcs={(int(k.split('_')[2]),int(k.split('_')[3])) for k,v in x.items() if k.startswith('x_0_') and v>.5}
    if arcs:
        used=set()
        while True:
            nexts=[j for i,j in arcs if i==at];assert len(nexts)==1,(at,arcs)
            nxt=nexts[0];assert (at,nxt) not in used;used.add((at,nxt));at=nxt
            if at==0:break
            stops.append(at)
        assert used==arcs
    load=0;pickup=drop=0;visits=set();prefix=[]
    for i in stops:
        assert i not in visits;visits.add(i)
        p=x[f'p_0_{i}'];d=x[f'd_0_{i}'];assert p>=-1e-8 and d>=-1e-8 and min(p,d)<=1e-8 and p+d>=1-1e-8
        assert close(Y[i-1],b[i-1]+d-p);load+=p-d;assert -1e-8<=load<=3+1e-8
        pickup+=p;drop+=d;prefix.append(load)
    for i in {1,2}-visits:
        assert Y[i-1]==b[i-1] and abs(x[f'p_0_{i}'])+abs(x[f'd_0_{i}'])<=1e-8
    assert all(0<=y<=4 for y in Y);assert close(sum(Y),3-load)
    handling=60*(pickup+drop+load);assert handling<=360+1e-8
    G=abs(Y[0]-Y[1])/(2*sum(Y)) if sum(Y) else 0
    P=sum(abs(y/2-1) for y in Y);F=G+.15*P
    assert close(x['G'],G) and close(x['zprod_1'],G*Y[0]) and close(x['zprod_2'],G*Y[1])
    return dict(Y=Y,route=[0,*stops,0],return_load=load,prefix_loads=prefix,handling_seconds=handling,G=G,P=P,F=F)
def infer_dag(model,station,lo,hi):
    i=station['i'];d=station['d'];C=station['C'];b=station['b'];lower=station['l'];upper=station['u']
    rows={r[0]:r for r in model['rows']}
    prefix=f'd167_f_{i}_';fp=sorted(v for v in model['vars'] if v.startswith(prefix));arcs={};qedges={}
    flowrows=[row for row in model['rows'] if row[0].startswith((f'd167_mass_{i}_',f'd167_weight_{i}_'))]
    for f in fp:
        e=int(f.rsplit('_',1)[1]);q=f'd167_q_{i}_{e}'
        assert q in model['vars'] and model['types'][f]==model['types'][q]=='C'
        assert model['bounds'][f]==(0.,1.) and close(model['bounds'][q][1],hi) and model['bounds'][q][0]==0
        pos=[];neg=[];qpos=[];qneg=[]
        for name,terms,sense,rhs in flowrows:
            if name.startswith(f'd167_mass_{i}_') and f in terms:
                assert sense=='=' and terms[f] in (-1,1)
                (pos if terms[f]==1 else neg).append(int(name.rsplit('_',1)[1]))
            if name.startswith(f'd167_weight_{i}_') and q in terms:
                assert sense=='=' and terms[q] in (-1,1)
                (qpos if terms[q]==1 else qneg).append(int(name.rsplit('_',1)[1]))
        assert len(pos)==1 and len(neg)<=1 and qpos==pos and qneg==neg
        arcs[e]=(pos[0],neg[0] if neg else 1)
        for suffix,sense,bound in [('lo','>=',lo),('hi','<=',hi)]:
            row=rows[f'd167_{suffix}_{i}_{e}'];assert row[2:]==(sense,0.)
            expected={q:1.};
            if bound!=0:expected[f]=-bound
            assert row[1].keys()==expected.keys() and all(close(row[1][v],expected[v]) for v in expected)
    assert len(arcs)==station['edges']
    balance_nodes={int(n.rsplit('_',1)[1]) for n in rows if n.startswith(f'd167_mass_{i}_')}
    assert len(balance_nodes)==station['nodes']-1 and 0 in balance_nodes and 1 not in balance_nodes
    for node in balance_nodes:
        mass=rows[f'd167_mass_{i}_{node}'];weight=rows[f'd167_weight_{i}_{node}'];assert mass[2]=='=' and mass[3]==(1 if node==0 else 0)
        assert weight[2:] == ('=',0.)
        if node==0:assert weight[1]['G']==-1
        else:assert 'G' not in weight[1]
    Yrow=rows[f'd167_link_Y_{i}'];Mrow=rows[f'd167_link_M_{i}'];Vrow=rows[f'd167_link_V_{i}'];Zrow=rows[f'd167_link_Z_{i}']
    assert Yrow[1][f'Y_{i}']==-1 and Zrow[1][f'zprod_{i}']==-1
    delta_edges={h:set() for h in range(d)}
    for h in range(d):
        delta=rows[f'd167_delta_{i}_{h}'];w=rows[f'd167_w_{i}_{h}'];assert delta[2:]==w[2:]==('=',0.)
        assert delta[1][f'bit_{i}_{h}']==-1 and w[1][f'prod_{i}_{h}']==-1
        delta_edges[h]={int(v.rsplit('_',1)[1]) for v,c in delta[1].items() if v.startswith(prefix) and c==1}
        w_edges={int(v.rsplit('_',1)[1]) for v,c in w[1].items() if v.startswith(f'd167_q_{i}_') and c==1}
        assert w_edges==delta_edges[h]
    outgoing=defaultdict(list)
    for e,(tail,head) in arcs.items():outgoing[tail].append(e)
    paths=[]
    def walk(node,chain):
        if node==1:paths.append(chain);return
        assert len(chain)<d+3
        for e in outgoing[node]:walk(arcs[e][1],chain+[e])
    walk(0,[]);seen=[]
    for chain in paths:
        assert len(chain)==d+2
        yc=[Yrow[1].get(f'd167_f_{i}_{e}',0) for e in chain]
        assert yc[0]==yc[-1]==0
        for p,h in enumerate(range(d-1,-1,-1),1):assert yc[p] in (0,1<<h)
        y=sum(yc);seen.append(int(y));assert lower<=y<=upper
        mm=-sum(Mrow[1].get(f'd167_f_{i}_{e}',0) for e in chain);vv=-sum(Vrow[1].get(f'd167_f_{i}_{e}',0) for e in chain)
        assert mm==abs(b-y) and vv==(y!=b)
        for h in range(d):assert sum(e in delta_edges[h] for e in chain)==((int(y)>>h)&1)
        for e in chain:assert Zrow[1].get(f'd167_q_{i}_{e}',0)==Yrow[1].get(f'd167_f_{i}_{e}',0)
    assert sorted(seen)==list(range(lower,upper+1)),(i,seen,lower,upper)
    block=[r for r in model['rows'] if r[0].startswith((f'd167_mass_{i}_',f'd167_weight_{i}_',f'd167_lo_{i}_',f'd167_hi_{i}_',f'd167_delta_{i}_',f'd167_w_{i}_')) or r[0] in (f'd167_link_Y_{i}',f'd167_link_M_{i}',f'd167_link_V_{i}',f'd167_link_Z_{i}')]
    assert len(block)==2*(station['nodes']-1)+2*len(arcs)+4+2*d
    jY=sum(v.startswith(prefix) for v in Yrow[1]);jM=sum(v.startswith(prefix) for v in Mrow[1]);jV=sum(v.startswith(prefix) for v in Vrow[1]);K=sum(v.startswith('z_') for v in Vrow[1])
    t=sum(head==1 for tail,head in arcs.values());E=len(arcs)
    nz_formula=6*E+E*(int(lo!=0)+int(hi!=0))-2*t+4*jY+jM+jV+3+3*K+2*d
    assert sum(len(r[1]) for r in block)==nz_formula,(i,nz_formula,sum(len(r[1]) for r in block))
    return dict(station=i,paths=len(paths),nodes=station['nodes'],edges=len(arcs),block_rows=len(block),block_nonzeros=nz_formula)

def main():
    start=time.perf_counter();manifest=load(OUT/'diagnostic_manifest.json');positions=load(OUT/'positions.json');ledger=load(Q/'driver_calls.json')
    assert len(manifest['positions'])==len(positions)==88
    assert Counter(p['kind'] for p in positions)==dict(canonical=72,local=12,tiny=4)
    assert len({p['id'] for p in positions})==88
    byid={p['id']:p for p in positions};optfiles=list(Q.rglob('Optimize.jsonl'));assert len(optfiles)==88
    count=0
    for file in optfiles:
        items=[json.loads(s) for s in file.read_text().splitlines()]
        assert len(items)==2 and [s['phase'] for s in items]==['begin','end'] and items[-1]['return']==0
        assert items[0]['call']==items[1]['call']==1;count+=1
    solve_entries=[r for r in ledger if r['label'].startswith('solve_')]
    assert len(solve_entries)==88 and all(r['exit_code']==0 for r in ledger)
    for index,entry in enumerate(solve_entries):
        assert entry['before_Optimize']==index and entry['after_Optimize']==index+1
        assert entry['PE_SHA256']==manifest['executable']['SHA256']
        assert entry['label']=='solve_'+manifest['positions'][index]['id']
    assert manifest['Optimize_at_freeze']==0 and manifest['frozen_before_Optimize'] and manifest['science_remaining_at_freeze_seconds']>=10800
    assert datetime.fromisoformat(manifest['UTC'])<datetime.fromisoformat(solve_entries[0]['UTC'])
    for p,h in manifest['CPP_sources'].items():assert digest(ROOT/p)==h
    assert digest(Path(manifest['executable']['path']))==manifest['executable']['SHA256']
    assert digest(Path(manifest['DLL']['path']))==manifest['DLL']['SHA256']
    # Actual input/domain/cutoff/parent identity: compare to saved R166 argv.
    oldledger=load(ROOT/'results/unified_exact_round166/qualification/driver_calls.json')
    frame_map={f['id']:f for f in manifest['frames']}
    for f in frame_map.values():
        old=next(r for r in oldledger if r['label']==f['id']+'_B')['command']
        assert f['original_command']==old and [f['T'],f['lam'],f['lo'],f['hi'],f['cutoff']]==[old[j] for j in (3,6,12,13,14)]
        assert digest(Path(f['input']))==f['input_SHA256'] and digest(Path(f['parent']))==f['parent_SHA256']
    common_sets=defaultdict(set);results=[];maximum=defaultdict(float);graphs=[];tiny=[];cache={};degenerate_common=[]
    for p in manifest['positions']:
        folder=ROOT/p['folder'];raw=load(folder/'solve.json');prep=load(folder/'prepare.json')
        assert raw==byid[p['id']]['solve'] and prep==byid[p['id']]['prepare']
        assert digest(folder/'model.lp')==p['model']['SHA256']==raw['fingerprint']==prep['model_SHA256']
        assert raw['native_status']==2 and raw['qualified_optimum'] and raw['original_types_restored'] and not raw['infeasible']
        assert raw['raw_LP']==(p['kind']!='tiny')
        params=load(folder/'parameters.json')
        assert params['Threads']==1 and params['Seed']==0 and params['MIPGap']==params['MIPGapAbs']==0 and params['NodeLimit']>=1e100
        assert params['TimeLimit']==p['Native_TimeLimit'] and params['Method']==params['Presolve']==params['Cuts']==-1 and params['MIPFocus']==0
        assert close(params['FeasibilityTol'],1e-6) and close(params['OptimalityTol'],1e-6) and close(params['IntFeasTol'],1e-5)
        m=parse_lp(folder/'model.lp');x=read_vector(folder/'solution.sol');audit=audit_primal(m,x,p['kind']=='tiny')
        audit.update(columns=len(m['vars']),rows=len(m['rows']),binaries=len(m['binaries']),nonzeros=sum(len(r[1]) for r in m['rows']))
        assert max(audit[k] for k in ('bound_violation','row_violation','integer_violation'))<=1e-7,(p['id'],audit)
        assert close(audit['objective'],raw['objective'],1e-8)
        if p['kind']!='local':
            assert len(m['vars'])==prep['columns'] and len(m['rows'])==prep['rows'] and len(m['binaries'])==prep['binaries']
            assert sum(len(r[1]) for r in m['rows'])==prep['nonzeros']
        if p['kind']=='canonical':
            common_sets[p['frame']].add(prep['common_SHA256'])
            assert digest(folder/'common_before.txt')==digest(folder/'common_after.txt')==prep['common_SHA256']
            stations=prep['stations'];selected=min(stations,key=lambda s:(-(s['u']-s['l']+1),s['i']))
            assert selected['i']==p['selected_station']
            mask={};allmasks=[[]];D=list(range(selected['l'],selected['u']+1))
            for level in range(1,3):
                for h in range(selected['d']):
                    if h in mask:continue
                    if {((y>>h)&1) for y in D}!={0,1}:continue
                    mask[h]=1-((selected['b']>>h)&1) if selected['b'] in D else 0
                    D=[y for y in D if ((y>>h)&1)==mask[h]];break
                allmasks.append([[h,a] for h,a in sorted(mask.items())])
            assert allmasks==prep['all_masks'] and p['mask']==allmasks[p['level']]
            condition=[[y for y in range(selected['l'],selected['u']+1) if all(((y>>h)&1)==a for h,a in assigned)] for assigned in allmasks]
            assert len(condition[p['level']])==p['conditional_stocks'] and not p['degenerate']
            actual_fixed=[r for r in m['rows'] if r[0].startswith('fixed_absolute_')]
            assert len(actual_fixed)==p['level']
            for row in actual_fixed:
                h=int(row[0].rsplit('_',1)[1]);assert row[1]=={f'bit_{selected["i"]}_{h}':1.} and row[2]=='=' and row[3]==dict(p['mask'])[h]
        if p['representation']=='R_abs':
            assert all(m['types'][v]=='C' for v in m['vars'] if v.startswith('state_'))
            for v in m['vars']:
                if v.startswith('bit_'):assert m['types'][v]=='B'
            assert not any(v.startswith('d167_') or v.startswith('r166_') for v in m['vars'])
            for name,terms,sense,rhs in m['rows']:
                if name.startswith(('rabs_delta_','rabs_w_')):
                    prefix,station,h=name.rsplit('_',2);i=int(station);h=int(h);weighted=prefix=='rabs_w'
                    expected={f'prod_{i}_{h}' if weighted else f'bit_{i}_{h}':1.}
                    stateprefix=f'state_g_{i}_' if weighted else f'state_{i}_'
                    for v in m['vars']:
                        if v.startswith(stateprefix) and ((int(v.rsplit('_',1)[1])>>h)&1):expected[v]=-1.
                    assert terms==expected and (sense,rhs)==('=',0.)
        if p['representation']=='D167':
            assert not any(v.startswith('state_') or v.startswith('r166_') for v in m['vars'])
            for name,terms,_,_ in m['rows']:
                if any(v.startswith('bit_') or v.startswith('prod_') for v in terms):
                    assert name.startswith(('d167_delta_','d167_w_','fixed_absolute_','fix_bit')),(p['id'],name)
            if p['kind'] in ('canonical','tiny'):
                # Recover the graph from actual emitted constraints, rather
                # than repeat the author's graph-construction algorithm.
                lo=m['bounds']['G'][0];hi=m['bounds']['G'][1]
                for s in prep['stations']:graphs.append(dict(id=p['id'],**infer_dag(m,s,lo,hi)))
        if p['kind']!='tiny':
            dual=read_rows(folder/'dual_rows.csv');primal=read_rows(folder/'primal_reduced_cost.csv');assert len(dual)==len(m['rows']) and len(primal)==len(m['vars'])
            dual_obj=0.;stationarity={v:m['objective'][v] for v in m['vars']};dual_sign=0.
            for idx,(row,dr) in enumerate(zip(m['rows'],dual)):
                name,terms,sense,rhs=row;pi=float(dr['Pi']);assert int(dr['row'])==idx and close(float(dr['RHS']),rhs)
                if sense=='<=':dual_sign=max(dual_sign,pi)
                elif sense=='>=':dual_sign=max(dual_sign,-pi)
                dual_obj+=pi*rhs
                for v,a in terms.items():stationarity[v]-=pi*a
            for r in primal:
                v=r['name'];rc=float(r['RC']);lo,hi=m['bounds'][v]
                assert close(float(r['LB']),lo) and close(float(r['UB']),hi) and close(float(r['Obj']),m['objective'][v])
                assert close(float(r['X']),x[v],1e-8)
                bound=lo if rc>=0 else hi
                assert rc==0 or math.isfinite(bound)
                if rc!=0:dual_obj+=rc*bound
                stationarity[v]-=rc
            stat=max(abs(v) for v in stationarity.values());gap=abs(dual_obj-audit['objective'])
            assert stat<=1e-7 and gap<=1e-7 and dual_sign<=1e-7,(p['id'],stat,gap,dual_sign)
            audit.update(dual_objective=dual_obj,primal_dual_gap=gap,stationarity=stat,dual_sign_violation=dual_sign)
        else:tiny.append(dict(id=p['id'],**physical(x)))
        for k,v in audit.items():
            if k not in ('objective','dual_objective','columns','rows','binaries','nonzeros') and isinstance(v,(int,float)):maximum[k]=max(maximum[k],v)
        results.append(dict(id=p['id'],**audit))
    # Raw filtering places a C166 V=0 interface row in common when its
    # legal support is only b. B's equivalent V+s_b=1 touches s_b and is
    # filtered out. Verify the exact finite exception, then normalize it.
    for frame in frame_map:
        a=Q/'canonical'/(frame+'_F0_R_abs');c=Q/'canonical'/(frame+'_F0_C166')
        aa=Counter((a/'common_after.txt').read_text().splitlines());cc=Counter((c/'common_after.txt').read_text().splitlines())
        assert not aa-cc
        extras=cc-aa
        stations=load(c/'prepare.json')['stations'];K=len([v for v in parse_lp(c/'model.lp')['vars'] if v.startswith('z_') and v.endswith('_1')])
        legal_singletons={s['i'] for s in stations if s['l']==s['u']==s['b']}
        for line,n in extras.items():
            assert n==1 and line.startswith('ROW = 0 ')
            cols=[t.rsplit(':',1) for t in line.split()[3:]]
            indices=set()
            for v,coef in cols:
                parts=v.split('_');assert parts[0]=='z' and len(parts)==3 and coef=='1';indices.add(int(parts[2]))
            assert len(indices)==1 and next(iter(indices)) in legal_singletons and len(cols)==K
        assert aa==cc-extras
        degenerate_common.append(dict(frame=frame,raw_common_equal=not extras,C166_singleton_visit_rows=list(extras),normalized_common_equal=True))
    # Every complete physical Start, including fixed and narrow positive-g
    # exports, is checked against the final serialized rows/bounds/types.
    starts=[]
    for file in sorted(Q.rglob('start.csv')):
        folder=file.parent;m=parse_lp(folder/'model.lp');x=read_vector(file);audit=audit_primal(m,x,True)
        assert max(audit[k] for k in ('bound_violation','row_violation','integer_violation'))<=1e-7,(folder,audit)
        recorded=load(folder/'start_check.json');assert close(audit['objective'],recorded['physical_objective'])
        if '/tiny/' in folder.as_posix():phys=physical(x)
        else:phys=None
        starts.append(dict(path=file.relative_to(ROOT).as_posix(),**audit,physical=phys))
    # Independent elementary inventory lower proof for tiny fixture: there
    # is no feasible perfect target (needs 4 units from 3). The only equal
    # ratio nonzero stocks are (1,1), requiring P=1, giving .15; (0,0)
    # has .30. All asymmetric feasible stocks have G>=1/6 and F>=G>.15.
    assert all(close(r['F'],.15 if r['id'].startswith('nonzero') else .3) for r in tiny)
    oracle=read_rows(Q/'tiny_oracle.csv');assert min(float(r['F']) for r in oracle)==.15
    assert all(not (float(r['Y1'])==2 and float(r['Y2'])==2) for r in oracle)
    master=load(OUT/'CSV_reconciliation.json')
    csvchecks=[]
    for f in master['found']:
        path=Path(f['path']);path=path if path.is_absolute() else ROOT/path
        assert digest(path)==f['SHA256'] and path.stat().st_size==f['bytes']
        rows=list(csv.reader(path.read_text(encoding=f['encoding']).splitlines()));assert len(rows)-1==f['records'] and len(rows[0])==28
        csvchecks.append(dict(path=f['path'],records=f['records'],columns=len(rows[0]),SHA256=f['SHA256']))
    assert not master['authoritative_112_available'] and master['new_complete_runs']==master['new_master_rows']==0
    # The measured preparation source differs from the final measurement
    # source only in retained bounded fixes/instrumentation; its own PE is
    # archived and never relabelled as the final 88-solve executable.
    v1=load(OUT/'build/preparation_v1.json');assert digest(ROOT/v1['carrier']['path'])==v1['carrier']['SHA256']
    with zipfile.ZipFile(ROOT/v1['carrier']['path']) as z:
        assert hashlib.sha256(z.read('Round167Research.exe')).hexdigest()==v1['executable']['SHA256']
        for p,h in v1['sources'].items():assert hashlib.sha256(z.read(p)).hexdigest()==h
    for r in ledger:
        assert digest(ROOT/r['log']['path'])==r['log']['SHA256']
        if not r['label'].startswith('solve_'):assert r['before_Optimize']==r['after_Optimize']==0
    summary=dict(UTC=datetime.now(timezone.utc).isoformat(),PASS=True,reviewer='/root/data_review',Optimize=0,
        actual_Optimize=count,kind_counts=dict(Counter(p['kind'] for p in positions)),source_and_PE_checked=True,
        frozen_before_Optimize=True,parameter_readbacks=len(positions),LP_KKT_checked=84,integer_physical_optima=tiny,
        Starts_checked=len(starts),common_blocks=len(common_sets),normalized_common_block_same_across_all_representations=True,
        raw_common_identity_frames=sum(row['raw_common_equal'] for row in degenerate_common),
        independently_recovered_station_graphs=len(graphs),independently_recovered_paths=sum(g['paths'] for g in graphs),
        maximum_residuals=dict(maximum),records_subprocess_outer_seconds=sum(r['seconds'] for r in ledger),
        maximum_sizes={k:max(row[k] for row in results) for k in ('columns','rows','binaries','nonzeros')},
        last_recorded_Optimize=solve_entries[-1]['after_Optimize'],CSV_actual=csvchecks,
        complete_methods_run=0,reader_repair_no_solver_rerun=True,check_seconds=time.perf_counter()-start,
        common_identity_details=degenerate_common,
        notes=['Subprocess fee sum excludes wrapper/aggregation/reader-repair overhead; label or conservatively include management cost.',
               'Native optimum/KKT evidence is numerical qualification, not a rational certificate.',
               'S0 is a fixed-inventory physical MIP; unchanged outer zero-controller evidence is inherited.'])
    REVIEW.mkdir(parents=True,exist_ok=True)
    for name,value in [('data_checks.json',summary),('data_primal_dual_checks.json',results),('data_start_checks.json',starts),('data_graph_checks.json',graphs)]:
        (REVIEW/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
