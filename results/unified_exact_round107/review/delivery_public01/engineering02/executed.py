"""Independent R107 public-only delivery review. Python stdlib; no project imports.

Critical physical, domain, cut, fee, native and gate facts are recomputed here.
Original embedded C: paths are data identifiers remapped to this fresh root.
"""
import ast
import collections
import csv
import datetime
from decimal import Decimal, getcontext, ROUND_FLOOR
import gzip
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import re
import sys
import tarfile
import time
import traceback

getcontext().prec = 55
D = Decimal
PUBLIC = Path('E:/r107_public107_01').resolve()
ROOT = Path('E:/r107_restore107_01').resolve()
READER = Path('E:/r107_reader107_01').resolve()
OUT = Path('E:/r107_delivery107_01').resolve()
RUNTIME = Path(sys.base_prefix).resolve()
BASE = ROOT / 'results/unified_exact_round107'
READS = {}
MANIFEST_PATHS = []
PATH_CACHE = {}


def path(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    elif not any(p.is_relative_to(x) for x in (ROOT, PUBLIC, READER, OUT)):
        s = str(p).replace('\\', '/')
        if '/ExactEBRP/' not in s:
            raise RuntimeError('Refuse external data path: ' + s)
        p = ROOT / s.split('/ExactEBRP/', 1)[1]
    key=str(p.absolute())
    if key in PATH_CACHE:return PATH_CACHE[key]
    p = p.resolve()
    assert any(p.is_relative_to(x) for x in (ROOT, PUBLIC, READER, OUT)), p
    PATH_CACHE[key]=p;PATH_CACHE[str(p)]=p
    return p


def raw(p):
    p = path(p)
    b = p.read_bytes()
    READS[str(p)] = dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    return b


def sha(p):
    p = path(p)
    h = hashlib.sha256()
    size = 0
    with p.open('rb') as f:
        while b := f.read(1024 * 1024):
            h.update(b); size += len(b)
    READS[str(p)] = dict(bytes=size, sha256=h.hexdigest())
    return h.hexdigest()


def text(p): return raw(p).decode('utf-8-sig').replace('\r\n', '\n')
def obj(p): return json.loads(text(p))
def table(p): return list(csv.DictReader(io.StringIO(text(p))))
def lines(p): return [json.loads(s) for s in text(p).splitlines() if s.strip()]
def near(a, b, tol='1e-9'): assert abs(D(str(a)) - D(str(b))) <= D(tol), (a, b, tol)


def write(p, value):
    with Path(p).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, default=str); f.write('\n')


def announce(s): print(s, flush=True)


def verify_package(package, archive, destination):
    manifest, parts = obj(package / 'manifest.json'), obj(package / 'parts_manifest.json')
    assert sha(package / 'manifest.json') == parts['original_manifest_SHA']
    combo, size = hashlib.sha256(), 0
    for n, r in enumerate(parts['archive_parts'], 1):
        assert r['path'] == f'evidence.tar.gz.part{n:03d}'
        source, h, length = package / r['path'], hashlib.sha256(), 0
        with path(source).open('rb') as f:
            while b := f.read(1024 * 1024):
                h.update(b); combo.update(b); length += len(b); size += len(b)
        assert length == r['bytes'] and h.hexdigest() == r['sha256']
        READS[str(path(source))] = dict(bytes=length, sha256=h.hexdigest())
    assert size == parts['archive_bytes'] == manifest['archive_bytes']
    assert combo.hexdigest() == parts['archive_sha256'] == manifest['archive_sha256'] == sha(archive)
    result = verify_members(archive, manifest, destination)
    result.update(archive_SHA=combo.hexdigest(), bytes=size, manifest_SHA=sha(package / 'manifest.json'), parts=len(parts['archive_parts']))
    return manifest, result


def verify_members(archive, manifest, destination):
    expected = {r['path']: r for r in manifest['files']}
    assert len(expected) == len(manifest['files'])
    seen, digest, total = set(), hashlib.sha256(), 0
    with tarfile.open(path(archive), 'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in expected and member.name not in seen
            r = expected[member.name]
            assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            b = tar.extractfile(member).read()
            value = hashlib.sha256(b).hexdigest()
            assert len(b) == r['bytes'] and value == r['sha256']
            restored = (destination / member.name).absolute()
            assert restored.is_relative_to(destination)
            assert sha(restored) == value and READS[str(restored)]['bytes'] == len(b)
            digest.update((member.name + '\0' + value + '\n').encode()); total += len(b); seen.add(member.name)
    assert seen == set(expected)
    return dict(files=len(seen), uncompressed_bytes=total, exact_member_and_fresh_file_hashes=True, verification_digest=digest.hexdigest())


def public_integrity():
    export = obj(PUBLIC / 'public_export_manifest.json')
    for r in export['files']:
        source = PUBLIC / r['path']
        assert sha(source) == r['sha256'] and READS[str(source)]['bytes'] == r['bytes']
    announce('Public exports exact; independently stream checking R107 archive members and fresh bytes')
    m, current = verify_package(PUBLIC / 'results/unified_exact_round107/compact_evidence', ROOT / 'round107_carrier/evidence.tar.gz', ROOT)
    MANIFEST_PATHS.extend(r['path'] for r in m['files'])
    announce('R107 archive/fresh bytes exact; checking pinned R106/R105 dependency members')
    old, inherited = verify_package(PUBLIC / 'results/unified_exact_round106/compact_evidence', ROOT / 'round106_carrier/evidence.tar.gz', ROOT / 'inherited_r106')
    d106, d105 = m['public_dependencies']
    assert inherited['archive_SHA'] == d106['archive_SHA'] and inherited['manifest_SHA'] == d106['manifest_SHA']
    assert sha(PUBLIC / 'results/unified_exact_round106/compact_evidence/parts_manifest.json') == d106['parts_manifest_SHA']
    legacy_manifest = obj(PUBLIC / d105['exact_manifest_public_path'])
    assert sha(PUBLIC / d105['exact_manifest_public_path']) == d105['exact_manifest_SHA']
    assert sha(PUBLIC / d105['path']) == d105['archive_SHA'] == legacy_manifest['archive_sha256']
    legacy_root = ROOT / 'inherited_r106/inherited_r105'
    legacy = verify_members(PUBLIC / d105['path'], legacy_manifest, legacy_root)
    supplement = obj(ROOT / 'inherited_r106/results/unified_exact_round106/r105_supplement/manifest.json')
    for r in supplement['files']:
        assert sha(ROOT / 'inherited_r106' / r['recovered_path']) == sha(legacy_root / r['original_path']) == r['sha256']
    receipt = obj(ROOT / 'restore_receipt.json')
    assert (current['files'], inherited['files'], legacy['files'], len(supplement['files'])) == (72553,45827,1556,66)
    assert receipt['round107_archive_SHA'] == current['archive_SHA'] == export['round107_archive_SHA']
    assert receipt['reader_SHA'] == sha(ROOT / 'scripts/round107_reader.py') == '3b04fe6757ae097ec721c13937b4ff9f463af73bc07ec699572d034bc46b788e'
    assert not receipt['original_workspace_reads'] and receipt['Optimize_calls'] == receipt['IIS_calls'] == 0
    return dict(public_export_files=len(export['files']), R107=current, R106=inherited, R105=legacy,
                legacy_supplement_files=len(supplement['files']), restore_receipt=receipt)


def instance(panel):
    a = {}
    for line in text(panel['input_path']).splitlines()[1:]:
        if '=' in line:
            key, value = line.split('=', 1); a[key.strip()] = ast.literal_eval(value)
    assert sha(panel['input_path']) == panel['input_sha256']
    a.update(panel)
    points = [[D(str(x)) for x in p] for p in a['points']]
    a['dist'] = [[sum((x[k]-y[k])**2 for k in (0,1)).sqrt()/D('1.5') for y in points] for x in points]
    a['Q'] = a['Q_vector']; a['capacity'] = a['capacities']; a['T'] = a['T_seconds']
    return a


def objective(a, Y):
    ratios = [D(Y[i])/D(a['target'][i]) for i in range(1,a['V']+1)]
    denom = sum(ratios, D(0)) * a['V']
    g = sum((abs(x-y) for x,y in itertools.combinations(ratios,2)), D(0))/denom if denom else D(0)
    weights = [D(str(v)) for v in a['weights'][1:]]
    if abs(max(weights)-10) < D('1e-6'): weights = [v/10 for v in weights]
    p = sum((w*abs(r-1) for w,r in zip(weights,ratios)), D(0))
    return g,p,g+D(str(a['lambda']))*p


def physical(a, w):
    Y, owned, result = list(a['initial']), set(), []
    assert sorted(r['vehicle'] for r in w['routes']) == list(range(a['M']))
    for r in w['routes']:
        k,nodes = r['vehicle'],r['nodes']
        operations = {x['station']:x for x in r['operations']}
        assert nodes[0] == nodes[-1] == 0 and set(nodes[1:-1]) == set(operations)
        assert len(operations) == len(r['operations']) == len(nodes)-2 == len(set(nodes[1:-1]))
        load=pickup=delivery=0; prefix=[]
        for i in nodes[1:-1]:
            p,d = operations[i]['pickup'],operations[i]['drop']
            assert type(p) is int and type(d) is int and p>=0 and d>=0 and bool(p)!=bool(d)
            assert 1<=i<=a['V'] and i not in owned; owned.add(i)
            load += p-d; pickup += p; delivery += d; prefix.append(load)
            assert 0<=load<=a['Q'][k]; Y[i]+=d-p
        travel=sum((D(str(a['dist'][i][j])) for i,j in zip(nodes,nodes[1:])),D(0))
        handling=D(str(a['pickup_seconds']))*pickup+D(str(a['drop_seconds']))*(delivery+load)
        assert travel+handling<=D(str(a['T']))+D('1e-7')
        result.append(dict(vehicle=k,nodes=nodes,pickup=pickup,delivery=delivery,return_load=load,
                           prefix_loads=prefix,travel=str(travel),handling=str(handling),duration=str(travel+handling)))
    assert all(0<=Y[i]<=a['capacity'][i] for i in range(1,a['V']+1))
    G,P,F=objective(a,Y); near(F,w['objective'],'1e-12')
    return dict(Y=Y,G=str(G),P=str(P),F=str(F),routes=result)


def small_exact(a):
    patterns={}; best=D('Infinity'); bestY=None; legal_count=0
    def legal(k, op):
        key=k,tuple(op)
        if key in patterns:return patterns[key]
        active=[i for i in range(1,a['V']+1) if op[i]]
        pickup=sum(max(0,q) for q in op); delivery=sum(max(0,-q) for q in op); found=False
        for order in itertools.permutations(active):
            load=0
            for i in order:
                load+=op[i]
                if not 0<=load<=a['Q'][k]:break
            else:
                ns=(0,)+order+(0,)
                duration=sum((D(str(a['dist'][i][j])) for i,j in zip(ns,ns[1:])),D(0))
                duration+=D(str(a['pickup_seconds']))*pickup+D(str(a['drop_seconds']))*(delivery+load)
                if duration<=D(str(a['T']))+D('1e-7'):found=True;break
        patterns[key]=found; return found
    inventories=0
    for ys in itertools.product(*(range(a['capacity'][i]+1) for i in range(1,a['V']+1))):
        Y=[a['initial'][0]]+list(ys); inventories+=1
        changed=[i for i in range(1,a['V']+1) if Y[i]!=a['initial'][i]]
        for owners in itertools.product(range(a['M']),repeat=len(changed)):
            ops=[[0]*(a['V']+1) for _ in range(a['M'])]
            for i,k in zip(changed,owners):ops[k][i]=a['initial'][i]-Y[i]
            if all(legal(k,op) for k,op in enumerate(ops)):
                legal_count+=1; F=objective(a,Y)[2]
                if F<best:best,bestY=F,Y
                break
    return dict(inventories=inventories,physical_inventories=legal_count,route_patterns=len(patterns),F=str(best),Y=bestY)


def vector(p):
    x={}
    for line in text(p).splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            n,v=line.split(); assert n not in x;x[n]=D(v)
    return x


def terms(expr):
    token = re.compile(r'([+-]?)\s*(?:(\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)\s*)?([A-Za-z_][A-Za-z0-9_.]*)')
    values={}; cursor=0
    for m in token.finditer(expr):
        assert not expr[cursor:m.start()].strip(), expr
        c=D(m[2] or 1)*(-1 if m[1]=='-' else 1); values[m[3]]=values.get(m[3],D(0))+c;cursor=m.end()
    assert not expr[cursor:].strip(),expr
    return {k:v for k,v in values.items() if v}


def lp_rows(p):
    chunks=[]; current=''; inside=False
    for line in text(p).splitlines():
        if line.lstrip().startswith('\\'):continue
        if line.strip()=='Subject To':inside=True;continue
        if line.strip()=='Bounds':break
        if not inside:continue
        if re.match(r'^\s*[^\s:]+\s*:',line):
            if current:chunks.append(current)
            current=line.strip()
        else:current+=' '+line.strip()
    if current:chunks.append(current)
    rows=[]
    for chunk in chunks:
        name,expr=chunk.split(':',1); m=re.search(r'(<=|>=|=)\s*([-+0-9.eE]+)\s*$',expr);assert m,chunk
        rows.append((name,terms(expr[:m.start()].strip()),m[1],D(m[2])))
    return rows


def domain(p):
    txt=text(p/'original.lp'); cols=table(p/'variables.csv'); index={x['name']:int(x['index']) for x in cols}
    bounds={int(i):(int(D(lo)),int(D(hi))) for lo,i,hi in re.findall(r'^\s*([+\-0-9.eE]+) <= Y_(\d+) <= ([+\-0-9.eE]+)\s*$',txt,re.M)}
    for i,(lo,hi) in bounds.items():
        states={int(m[2]) for n in index if (m:=re.fullmatch(r'state_(\d+)_(\d+)',n)) and int(m[1])==i}
        assert states==set(range(lo,hi+1))
    assert all(z['master_type']==('C' if z['name'].startswith(('x_','load_')) else z['old_type']) for z in cols)
    return bounds,index


def activity(row, e):
    value=D(0)
    for z in row:
        name=z['variable']; c=D(z['coefficient'])
        if name.startswith('state_'):
            _,i,y=name.split('_');v=int(e['Y'][int(i)-1]==int(y))
        else:
            kind,k,i=name.split('_');q=e['operations'][int(k)][int(i)-1]
            v=int(bool(q)) if kind=='z' else max(0,q) if kind=='p' else max(0,-q) if kind=='d' else None
            assert v is not None,name
        value+=c*v
    return value


def metric(a):
    n=a['V']+1;m=[[0]*n for _ in range(n)]
    for i,j in itertools.combinations(range(n),2):
        v=D(str(a['dist'][i][j]))*1000;k=int(v.to_integral_value(rounding=ROUND_FLOOR));k-=int(k>0 and v==k)
        m[i][j]=m[j][i]=k
    for k in range(n):
        for i in range(n):
            for j in range(n):m[i][j]=min(m[i][j],m[i][k]+m[k][j])
    return m


def journal(d,a):
    observed=obj(d/'observations.json'); calls={}; returned=set(); skipped=set(); witnesses=[]; bounds=[]
    for n,r in enumerate(observed,1):
        p=d/'journal'/f'event_{n}.json'; b=raw(p);e=json.loads(b);commit=text(p.with_suffix('.commit')).split()
        assert commit[0]=='NEJ1' and int(commit[1])==n and int(commit[3])==len(b)
        assert commit[4]==hashlib.sha256(b).hexdigest()==r['sha256'] and e==r['payload']
        assert D(str(r['effective_available_seconds']))+D('1e-9')>=D(commit[2])
        if e['kind']=='call':
            assert e['call'] not in calls and sha(e['model_path'])==e['model_sha256'];calls[e['call']]=e
            assert e['settings']['read_return_code']==0
            for key,value in dict(Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6).items():
                near(e['settings'][key],value,'1e-12')
        elif e['kind']=='returned':
            assert e['call'] in calls and e['return_code']==0;returned.add(e['call'])
        elif e['kind']=='not_started':skipped.add(e['call'])
        elif e['kind']=='witness':witnesses.append(physical(a,e))
        elif e['kind']=='bound':
            assert not e['inconsistent']
            if e['global_available']:
                c=calls[e['call']]
                if c['full_original']:L=D(str(e['native_bound']))
                else:
                    assert len(c['cover'])==1 and c['cover'][0]['id']=='L0' and D(str(c['cover'][0]['lower_g']))==0
                    L=min(min(D(w['F']) for w in witnesses),max(D(str(c['cover'][0]['lower'])),D(str(e['native_bound']))))
                near(L,e['global_bound']);bounds.append(L)
        elif e['kind']=='failure':raise AssertionError(e)
    assert set(calls)==returned|skipped and witnesses
    U=min(D(w['F']) for w in witnesses)
    final_returns=[]
    for id,c in calls.items():
        if id not in returned or not(c['full_original'] or c['native_preconditions']):continue
        matches=re.findall(r'Best objective [^,\n]+, best bound ([^,\n]+), gap',text(c['native_log_path']))
        assert matches,c
        native=D(matches[-1].strip())
        L=native if c['full_original'] else min(U,max(D(str(c['cover'][0]['lower'])),native))
        bounds.append(L);final_returns.append(dict(call=id,native_bound=str(native),qualified_bound=str(L)))
    return dict(actual_Optimize=len(calls)-len(skipped),committed_events=len(observed),U=str(U),L=str(max([D(0)]+bounds)),
                physical_witnesses=len(witnesses),last_physical=witnesses[-1],final_native_return_bounds=final_returns)


def cover(d,a,result):
    am=table(d/'adaptive_mass_decision_ledger.csv'); audited=[]
    for r in am:
        parent,left,right,U=(D(r[k]) for k in ('B_p','B_L','B_R','U')); gap=U-parent
        if gap<=D('1e-7'):continue
        gains=[max(D(0),min(D(1),(v-parent)/gap)) for v in (left,right)]
        score=min(gains)*sum(gains)/2;near(score,r['S_AM'])
        audited.append(dict(score=str(score),action=r['selected_action']))
    target=table(d/'native_target_ledger.csv'); assert len(target)==1
    assert target[0]['requeued']=='1' and target[0]['exact_closure']=='0' and target[0]['target_reached']=='1'
    assert D(target[0]['native_bound'])+D('1e-7')>=D(target[0]['target_bound'])
    seed=physical(a,obj(d/'initial_witness.json'))
    initial=table(d/'initial_decomposition_ledger.csv');assert len(initial)==1 and D(initial[0]['active_lower'])==0
    near(initial[0]['active_upper'],seed['F'])
    leaves=table(d/'paper_leaf_ledger.csv'); assert len(leaves)==1 and leaves[0]['leaf_id']=='L0'
    near(leaves[0]['lower_bound'],result['lower_bound'])
    events=table(d/'paper_tree_events.csv');names=[r['event'] for r in events]
    assert 'native_bound_target_reached' in names and 'child_lp_reuse' in names
    assert names.index('native_bound_target_reached')<names.index('child_lp_reuse')
    optimized=table(d/'paper_optimize_ledger.csv')
    partial=[r for r in optimized if r['solve_kind']=='CHILD_BOUND_TARGET_MIP']
    terminal=[r for r in optimized if r['solve_kind']=='MIP']
    assert len(partial)==len(terminal)==1 and partial[0]['native_status']=='INTERRUPTED'
    assert partial[0]['optimize_return_code']==terminal[0]['optimize_return_code']=='0'
    assert optimized.index(partial[0])<optimized.index(terminal[0]) and partial[0]['model_sha256']==terminal[0]['model_sha256']
    child=table(d/'parent_child_bound_ledger.csv');assert len(child)>=2
    expected_target=min(D(child[0]['left_lp_bound']),D(child[0]['right_lp_bound']))
    near(expected_target,target[0]['target_bound'])
    assert (child[0]['left_lp_bound'],child[0]['right_lp_bound'])==(child[1]['left_lp_bound'],child[1]['right_lp_bound'])
    if result['strict_certified_original_problem']:
        assert leaves[0]['status']=='closed' and leaves[0]['closure_source']=='native_terminal_mip_optimal'
        assert D(leaves[0]['lower_bound'])+D('1e-7')>=D(str(result['objective']))
        assert terminal[0]['native_status']=='OPTIMAL' and 'terminal_mip_complete' in names
    else:
        assert leaves[0]['status']=='open' and terminal[0]['native_status'] in ('INTERRUPTED','TIME_LIMIT')
        assert 'terminal_mip_complete' not in names
    return dict(AM=audited,target=target,leaves=leaves,original_root_cover=initial,seed_physical=seed,
                real_target_requeue_child_cache_then_terminal=True,terminal_native_return=terminal[0],parent_child_bounds=child,
                terminal_completion_event_exposed='terminal_mip_complete' in names)


def scoped(d,a):
    base=d/'external/round107'; qs=lines(base/'requests.jsonl'); chains=[]; checked=[]; summaries=[];new=[]
    assert [q['kind'] for q in qs]==['LP','LP','LP','PARTIAL_TARGET','TERMINAL']
    assert qs[3]['target_reached'] and not qs[3]['unresolved'] and not qs[3]['optimal_close_by_dominance']
    assert qs[4]['reason']=='open_local_obligation:global_deadline_in_master' and qs[4]['stop_whole_run']
    semantic=lines(base/'semantic_rows.jsonl'); assert all(s['scope']=='global_physical' for s in semantic)
    family_count=collections.Counter()
    for q in qs:
        assert q['failure']=='none' and sha(q['canonical_path'])==q['canonical_sha256'] and not q['native_continuation_claimed']
        if q['kind']=='LP':continue
        folder=path(q['evidence_dir']); bounds,index=domain(folder);s=obj(folder/'summary.json'); summaries.append(s)
        assert s['master_calls']==1 and s['iis_calls']==0 and not s['unresolved'] and s['unknown_candidates']==0
        events=lines(folder/'events.jsonl'); assert len(events)==s['events']
        selected={1,len(events)}
        for n,e in enumerate(events,1):
            assert e['event']==n and e['request']==q['request']; F=objective(a,[0]+e['Y'])[2];near(F,e['Ftrue'],'1e-12')
            assert D(str(e['model_objective']))+D('1e-7')>=F
            for i,y in enumerate(e['Y'],1):
                assert bounds[i][0]<=y<=bounds[i][1]
                assert y==a['initial'][i]-sum(op[i-1] for op in e['operations'])
                assert sum(bool(op[i-1]) for op in e['operations'])==int(y!=a['initial'][i])
            if e['physical_ub_events']:selected.add(n)
        lazy=table(folder/'lazy.csv'); assert len(lazy)==s['lazy_calls'];by_event=collections.defaultdict(list)
        for z in lazy:
            n,r=int(z['event']),int(z['row']); row=table(folder/f'row_{r}.csv');e=events[n-1]
            lhs=activity(row,e);rhs=D(row[0]['rhs']);near(lhs,z['activity'],'1e-7');near(rhs,z['rhs'])
            assert lhs-rhs>max(D('1e-7'),D('1e-6')*max(D(1),abs(lhs),abs(rhs))) and z['api_return']=='0'
            assert D(str(e['entered_seconds']))<=D(z['process_seconds'])<=D(str(e['published_seconds']))+D('1e-7')
            by_event[n].append(r);family_count[z['family']]+=1
            if not any(c['family']==z['family'] and c['role']==a['id'] for c in chains):
                chains.append(dict(role=a['id'],family=z['family'],request=q['request'],event=n,row=r,vehicle=int(z['vehicle']),folder=str(folder)))
                selected.add(n)
        for e in events:assert by_event[e['event']]==e['submitted_lazy_rows']
        for r in table(folder/'remap.csv'):
            srow=semantic[int(r['row'])];n=r['semantic_variable'];assert D(str(srow['coefficients'][n]))==D(r['coefficient'])
            if r['omitted_fixed_zero']=='1':
                match=re.fullmatch(r'state_(\d+)_(\d+)',n);assert match
                i,y=map(int,match.groups()); assert not bounds[i][0]<=y<=bounds[i][1]
                assert int(r['current_column'])==-1 and 'outside_audited_current' in r['omission_proof']
            else:assert int(r['current_column'])==index[n]
        rows=lp_rows(folder/'master.lp')
        for n in sorted(selected):
            e=events[n-1];x=vector(folder/f'candidate_{n}.sol'); maxv=D(0)
            for name,c,sense,rhs in rows:
                value=sum((v*x.get(k,D(0)) for k,v in c.items()),D(0))
                vio=max(D(0),value-rhs) if sense=='<=' else max(D(0),rhs-value) if sense=='>=' else abs(value-rhs)
                maxv=max(maxv,vio)
            assert maxv<=D('1e-6'),(folder,n,maxv)
            for i,y in enumerate(e['Y'],1):near(x.get(f'Y_{i}',0),y,'1e-5');near(x.get(f'state_{i}_{y}',0),1,'1e-5')
            checked.append(dict(role=a['id'],request=q['request'],event=n,vector_SHA=sha(folder/f'candidate_{n}.sol'),base_rows=len(rows),maximum_violation=str(maxv)))
        for witness in sorted(p for p in MANIFEST_PATHS if p.startswith(str(folder.relative_to(ROOT)).replace('\\','/')+'/physical_ub_') and p.endswith('.json')):
            new.append(dict(path=str(path(witness)),physical=physical(a,obj(witness))))
    final=physical(a,obj(base/'witness.json'));near(final['F'],qs[-1]['own_global_UB'])
    return dict(requests=qs,summaries=summaries,all_candidate_true_objectives_and_ownership_recomputed=True,
                all_lazy_activities_and_timing_recomputed=True,lazy_families=dict(family_count),selected_raw_base_audits=checked,
                new_complete_physical_fleets=new,final_physical=final,chains=chains)


def cut_proof(item,a):
    folder=path(item['folder']);n,k=item['event'],item['vehicle'];e=lines(folder/'events.jsonl')[n-1]
    row=table(folder/f'row_{item["row"]}.csv');x=vector(folder/f'candidate_{n}.sol')
    lhs=sum((D(z['coefficient'])*x.get(z['variable'],D(0)) for z in row),D(0));rhs=D(row[0]['rhs']);assert lhs>rhs+D('1e-7')
    m=metric(a);family=item['family']
    cert_path=folder/f'certificate_{n}_{2 if family=="B_THRESHOLD" else 1}.json'
    if family=='A_MST':
        cert=obj(cert_path);support=cert['support']; nodes=[0]+support;parent={i:i for i in nodes}
        def find(i):
            while parent[i]!=i:i=parent[i]
            return i
        mst=0
        for v,i,j in sorted((m[i][j],i,j) for i,j in itertools.combinations(nodes,2)):
            left,right=find(i),find(j)
            if left!=right:parent[left]=right;mst+=v
        amount=sum(e['operations'][k][i-1] for i in support)
        assert all(e['operations'][k][i-1]>0 for i in support)
        lower=D(mst)/1000+D(str(a['pickup_seconds']+a['drop_seconds']))*amount
        near(D(mst)/1000,cert['travel_lower'],'1e-9');assert lower>D(str(a['T']))+D('.01')
        proof=dict(support=support,MST_milliseconds=mst,pickup=amount,duration_lower=str(lower))
    else:
        support=[i+1 for i,q in enumerate(e['operations'][k]) if q] if family=='FULL' else obj(cert_path)['support']
        assert len(support)==3
        orders=[];minimum=None;P=sum(max(0,e['operations'][k][i-1]) for i in support)
        for order in itertools.permutations(support):
            load=0;prefix=[]
            for i in order:load+=e['operations'][k][i-1];prefix.append(load)
            route=(0,)+order+(0,); ms=sum(m[i][j] for i,j in zip(route,route[1:]));minimum=ms if minimum is None else min(minimum,ms)
            lower=D(ms)/1000+D(str(a['pickup_seconds']+a['drop_seconds']))*P
            legal=all(0<=v<=a['Q'][k] for v in prefix);assert not legal or lower>D(str(a['T']))+D('.01')
            orders.append(dict(order=order,prefix=prefix,prefix_feasible=legal,duration_lower=str(lower)))
        proof=dict(support=support,six_orders=orders,pickup=P)
        if family.startswith('B'):
            assert sum(e['operations'][k][i-1] for i in support)==0
            strict=D(minimum)/1000+D(str(a['pickup_seconds']+a['drop_seconds']))*(P+1)
            assert strict>D(str(a['T']))+D('.01');proof['strict_extra_pickup_duration_lower']=str(strict)
            cert=obj(cert_path);expected={f'z_{k}_{i}':1 for i in support}
            for i in support:
                q=e['operations'][k][i-1];threshold=a['initial'][i]-q
                values=[threshold] if family=='B_EXACT' else [y for y in range(a['capacity'][i]+1) if (q>0 and y<=threshold) or (q<0 and y>=threshold)]
                expected.update({f'state_{i}_{y}':1 for y in values})
            assert expected==cert['coefficients'];proof['complete_global_semantic_coefficients_reconstructed']=True
        else:
            full=folder/f'event_{n}_k{k}/full.lp';fullrows={name:(c,s,r) for name,c,s,r in lp_rows(full)}
            for i in range(1,a['V']+1):assert fullrows[f'a_{i}_z']==({f'z_{i}':D(1)},'=',D(bool(e['operations'][k][i-1])))
            called=[z for z in table(folder/'inner/calls.csv') if z['stage']=='after' and z['model_sha256']==sha(full)]
            assert len(called)==1 and called[0]['status']=='3' and called[0]['solutions']=='0'
            proof['actual_FULL_INF_complete_all_station_assumptions']=True
    calls=table(folder/'calls.csv');assert len([z for z in calls if z['stage']=='before'])==len([z for z in calls if z['stage']=='after'])==1
    events=lines(folder/'events.jsonl');assert len(events)>n and events[n]['event']==n+1
    return dict(**item,lhs=str(lhs),rhs=str(rhs),proof=proof,same_Optimize_continues_to_event=n+1)


def qualification():
    folder=BASE/'qualification/final03/scope/terminal/round107';qs=lines(folder/'requests.jsonl')
    a=dict(V=4,M=1,Q=[3],capacity=[0,5,5,5,5],initial=[0,3,3,0,1],target=[0,1,1,3,1],weights=[0,1,1,1,1],
           T=100,pickup_seconds=1,drop_seconds=1,**{'lambda':.15},dist=[[0 if i==j else 2 if i and j else 1 for j in range(5)] for i in range(5)])
    testsrc=text(ROOT/'tests/round107_tests.cpp')
    assert 'a.initial={0,3,3,0,1}' in testsrc and 'a.target={0,1,1,3,1}' in testsrc
    exact=small_exact(a);near(exact['F'],qs[0]['own_global_UB'],'1e-12')
    assert qs[1]['local_INF'] and not qs[1]['domain_start'] and D(exact['F'])>D(str(qs[1]['effective_cutoff']))
    assert not qs[2]['domain_start'] and qs[2]['qualified_local_bound']>qs[2]['own_global_UB'] and qs[2]['optimal_close_by_dominance']
    witness=physical(a,obj(folder/'request_3/entry_witness.json'))
    assert D(witness['G'])<D(str(qs[2]['gamma_L'])) and not (folder/'request_3/start.mst').exists()
    feedback=lines(folder/'request_3/feedback.jsonl');assert feedback and all(not r['submitted'] and r['global_physical_UB_retained'] for r in feedback)
    summary=obj(folder/'request_3/summary.json'); assert summary['cross_request_hits']==2 and summary['remapped_rows']==1
    cache=table(folder/'request_3/cache.csv');assert {r['cache_status'] for r in cache}=={'INF','FEAS'}
    first=lines(folder/'request_1/events.jsonl');last=lines(folder/'request_3/events.jsonl')
    for r in cache:
        e=last[int(r['event'])-1];assert any(x['operations']==e['operations'] for x in first)
        assert r['origin_request']=='1' and r['current_request']=='3' and r['key'].startswith('R105-physical-v1/')
    semantic=lines(folder/'semantic_rows.jsonl');assert len(semantic)==1 and semantic[0]['family']=='FULL' and semantic[0]['scope']=='global_physical'
    domains={n:domain(folder/f'request_{n}') for n in (1,2,3)}
    for n in (1,2,3):
        for r in table(folder/f'request_{n}/remap.csv'):
            assert r['omitted_fixed_zero']=='0' and int(r['current_column'])==domains[n][1][r['semantic_variable']]
            assert D(r['coefficient'])==D(str(semantic[0]['coefficients'][r['semantic_variable']]))
    coeff={f'z_0_{i}':1 for i in (1,2,3)}; op={1:2,2:1,3:-3}; initial=a['initial']
    for i,q in op.items():
        coeff.update({f'state_{i}_{y}':1 for y in range(6) if (q>0 and y<=initial[i]-q) or (q<0 and y>=initial[i]-q)})
    old={n:c for n,c in coeff.items() if n in domains[2][1]};new={n:c for n,c in coeff.items() if n in domains[3][1]}
    newly=sorted(set(new)-set(old));assert newly==['state_1_0','state_2_0','state_2_2']
    values={'z_0_1':1,'z_0_2':1,'z_0_3':1,'state_1_1':1,'state_2_2':1,'state_3_3':1}
    oldact=sum(c*values.get(n,0) for n,c in old.items());newact=sum(c*values.get(n,0) for n,c in new.items())
    assert (oldact,newact)==(5,6)
    # Independent global B physics fixture for the operator replay, not the T100 native instance.
    square={0:(0,0),1:(3,0),2:(0,3),3:(3,3)};six=[]
    for order in itertools.permutations((1,2,3)):
        load=0;prefix=[]
        for i in order:load+=op[i];prefix.append(load)
        ns=(0,)+order+(0,);travel=sum(math.dist(square[i],square[j]) for i,j in zip(ns,ns[1:]));duration=travel+6
        legal=all(0<=x<=3 for x in prefix);assert not legal or duration>19.9
        six.append(dict(order=order,prefix=prefix,travel=travel,duration=duration))
    assert abs(min(x['travel'] for x in six)+2*4-19.9-.1)<1e-12
    # A high local bound cannot close the independent low-cover obligation.
    high=D(str(qs[2]['qualified_local_bound']));low=D(exact['F'])/2; global_cover=min(low,high)
    assert global_cover<D(exact['F'])<high
    targetbase=BASE/'qualification/final03/target/case_1'
    targetinstance=obj(targetbase/'instance.json');targetexact=small_exact(targetinstance)
    targetqs=lines(targetbase/'controller/round107/requests.jsonl');targetresult=obj(targetbase/'controller_result.json')
    near(targetexact['F'],targetresult['UB'],'1e-12')
    partial,terminal=targetqs[-2:]
    assert partial['kind']=='PARTIAL_TARGET' and partial['target_reached'] and partial['qualified_local_bound']>=partial['target']
    assert terminal['native_status']==2 and terminal['optimal_close_by_dominance'] and not terminal['unresolved']
    ledger=table(targetbase/'controller/native_target_ledger.csv');leaf=table(targetbase/'controller/paper_leaf_ledger.csv')
    assert ledger[0]['requeued']=='1' and ledger[0]['exact_closure']=='0' and leaf[0]['status']=='closed'
    tree=table(targetbase/'controller/paper_tree_events.csv');events=[r['event'] for r in tree]
    assert events.index('native_bound_target_reached')<events.index('child_lp_reuse')<events.index('terminal_mip_complete')
    assert targetresult['certified'] and targetresult['target_reached']==targetresult['requeues']==targetresult['terminal_calls']==1
    outerbase=BASE/'qualification/final03/outer_deadline';outer=obj(outerbase/'deadline_outcome.json')
    outerq=lines(outerbase/'round107/requests.jsonl')[0];outercalls=table(outerbase/'round107/request_1/calls.csv')
    assert len([r for r in outercalls if r['stage']=='before'])==len([r for r in outercalls if r['stage']=='after'])==1
    after=[r for r in outercalls if r['stage']=='after'][0];assert after['status']=='11' and D(after['remaining'])<0
    assert outerq['stop_whole_run'] and not outerq['target_reached'] and not outer['certified'] and outerq['reason'].endswith('global_deadline_in_master')
    innerbase=BASE/'qualification/final02/inner_deadline/inner';inner=obj(innerbase/'deadline.json');innercalls=table(innerbase/'calls.csv')
    assert inner['actual_oracle_Optimize']==1 and inner['cancelled'] and inner['IIS']==0
    ia=[r for r in innercalls if r['stage']=='after'];assert len(ia)==1 and ia[0]['status']=='11' and ia[0]['solutions']=='0'
    assert D(ia[0]['remaining'])<0
    scope=text(ROOT/'include/Round107Scope.hpp')
    assert scope.index('if (f.unresolved)')<scope.index('if (f.native_infeasible)')<scope.index('d.target_reached =')
    return dict(independent_small_scope_exact=exact,strict_empty_INF_no_Start=qs[1],outside_high_local_bound=qs[2],
                outside_global_physical_UB_and_no_Start=dict(physical=witness,feedback=feedback,global_UB_retained=True),
                other_cover_obligation=dict(layer='PURE_ARITHMETIC_COVER_COUNTEREXAMPLE',low=str(low),high=str(high),global_lower=str(global_cover),UB=exact['F'],not_globally_closed=True),
                native_FULL_cache_reuse=dict(cross_request_hits=2,remapped_rows=1,cache_statuses=['INF','FEAS'],native_threshold_transition='NOT_EXPOSED'),
                independent_threshold_replay=dict(layer='INDEPENDENT_ACTUAL_DOMAIN_OPERATOR_REPLAY_WITH_SEPARATE_BOUNDED_B_PHYSICS',newly_present=newly,old_activity=oldact,new_activity=newact,rhs=5,six_orders=six,T=19.9,strict_extra_pickup_margin=.1),
                native_target_original_controller_terminal_cert=dict(exact=targetexact,result=targetresult,target=partial,terminal=terminal,ledger=ledger,leaf=leaf),
                real_outer_deadline=dict(outcome=outer,request=outerq,after=after,UNKNOWN_candidate='NOT_EXPOSED'),
                real_inner_deadline=dict(outcome=inner,after=ia[0],interpretation='UNKNOWN: interrupted without solution; no infeasibility proof'),
                unresolved_priority_source_checked=True,formal_unknown_not_exposed=True)


def native_census():
    roots=[p for p in MANIFEST_PATHS if re.match(r'results/unified_exact_round107/(qualification/|development0[23]/raw/)',p)]
    counts=collections.Counter();entries=[]
    for p in sorted(z for z in roots if z.endswith('/calls.csv')):
        rr=table(p);before=collections.Counter((r['phase'],r['call']) for r in rr if r['stage']=='before')
        after=collections.Counter((r['phase'],r['call']) for r in rr if r['stage']=='after')
        skipped=collections.Counter((r['phase'],r['call']) for r in rr if r['stage']=='not_started_deadline')
        assert before==after+skipped,(p,before-after-skipped)
        counts.update(r['phase'] for r in rr if r['stage']=='after')
        entries.append(dict(path=p,phase_counts=dict(collections.Counter(r['phase'] for r in rr if r['stage']=='after')),started=sum(before.values())-sum(skipped.values()),returned=sum(after.values()),missing_after=0))
    for p in sorted(z for z in roots if z.endswith('/requests.jsonl')):
        qs=[q for q in lines(p) if q['kind']=='LP' and q.get('native_Optimize_started',True)]
        if not qs:continue
        folder=path(p).parent.parent;ledger=folder/'paper_optimize_ledger.csv'
        for q in qs:assert sha(q['canonical_path'])==q['canonical_sha256']
        if ledger.exists():
            status={'OPTIMAL':2,'INFEASIBLE':3,'TIME_LIMIT':9,'INTERRUPTED':11}
            rr=[r for r in table(ledger) if r['solve_kind']=='LP' and r['optimize_return_code']=='0']
            assert collections.Counter((q['canonical_sha256'],q['native_status']) for q in qs)==collections.Counter((r['model_sha256'],status[r['native_status']]) for r in rr)
        else:
            log=text(folder/'native.log');assert len(re.findall(r'^Solved in ',log,re.M))==len(qs)
            assert len(re.findall(r'^Optimal objective ',log,re.M))==len(qs)
        counts['LP']+=len(qs);entries.append(dict(path=p,LP=len(qs),native_field_missing_legacy=sum('native_Optimize_started' not in q for q in qs)))
    journals=collections.defaultdict(list)
    for p in roots:
        if re.search(r'/journal/event_\d+\.json$',p):journals[p.rsplit('/',1)[0]].append(p)
    for folder,files in sorted(journals.items()):
        calls={};returns=set();ns=set()
        for p in sorted(files,key=lambda p:int(re.search(r'event_(\d+)\.json$',p)[1])):
            e=obj(p)
            if e['kind']=='call':assert e['call'] not in calls;calls[e['call']]=e
            elif e['kind']=='returned':assert e['return_code']==0;returns.add(e['call'])
            elif e['kind']=='not_started':ns.add(e['call'])
        assert set(calls)==returns|ns,(folder,set(calls)-returns-ns)
        parent=path(folder).parent;tracked=collections.Counter()
        for id,e in calls.items():
            if id in ns:continue
            if parent.name=='cli01':
                assert not e['native_preconditions'] and 'Solved in ' in text(e['native_log_path'])
                assert sha(e['model_path'])==e['model_sha256'];tracked['failed_CLI_LP_recovered']+=1;counts['LP']+=1
            elif parent.parent.name=='raw' and ('P-GRB' in parent.name or 'ENS-C' in parent.name):
                kind='P_ENS_MIP' if e['full_original'] or e['native_preconditions'] else 'P_ENS_LP'
                tracked[kind]+=1;counts['LP' if kind=='P_ENS_LP' else 'original_MIP']+=1
        if tracked:entries.append(dict(path=folder,counts=dict(tracked),actual_Optimize=sum(tracked.values()),missing_after=0))
    total=counts['LP']+counts['master']+counts['original_MIP']+counts['oracle']+counts['core_confirm']+counts['iis']
    assert total==5946 and counts['iis']==counts['core_confirm']==0,(total,counts)
    return dict(total_Optimize=total,LP=counts['LP'],MIP_master=counts['master']+counts['original_MIP'],oracle=counts['oracle'],IIS=counts['iis'],core=counts['core_confirm'],missing_after=0,details=entries)


def fee_census():
    fees=[];starts=0;seconds=D(0)
    for p in sorted(z for z in MANIFEST_PATHS if re.fullmatch(r'results/unified_exact_round107/fees/[^/]+/launch.json',z)):
        launch=obj(p);receipt=obj(Path(p).parent/'receipt.json')
        assert not launch['engineering'] and not receipt['engineering']
        assert launch['conservative_process_starts']==receipt['conservative_process_starts']
        starts+=launch['conservative_process_starts'];seconds+=D(str(receipt['outer_seconds']))
        fees.append(dict(label=Path(p).parent.name,starts=launch['conservative_process_starts'],outer_seconds=str(receipt['outer_seconds']),exit_code=receipt['exit_code']))
    corrections=[]
    for p in sorted(z for z in MANIFEST_PATHS if z.startswith('results/unified_exact_round107/fee_corrections/') and z.endswith('.json')):
        c=obj(p);starts+=c['additional_conservative_starts'];corrections.append(c)
    assert starts==62;near(seconds,'15157.511650200002','1e-8')
    return dict(conservative_starts=starts,outer_seconds=str(seconds),retained_failures=[x['label'] for x in fees if x['exit_code']!=0],unclosed=0,
                remaining_starts=72-starts,remaining_seconds=str(D(80000)-seconds),nested_native_time_added=False,fees=fees,corrections=corrections)


def fresh_reader_check():
    receipt=obj(READER/'reader_receipt.json');assert path(receipt['source_root'])==ROOT
    assert receipt['reader_SHA']==sha(ROOT/'scripts/round107_reader.py') and receipt['Optimize_calls']==receipt['IIS_calls']==0
    fields=0;tables=[]
    for p in sorted(z for z in MANIFEST_PATHS if z.startswith('results/unified_exact_round107/reports05/') and z.endswith('.csv')):
        original=list(csv.reader(io.StringIO(text(p))));fresh=list(csv.reader(io.StringIO(text(READER/Path(p).name))))
        assert original[0]==fresh[0] and len(original)==len(fresh)
        for n,(row,new) in enumerate(zip(original[1:],fresh[1:]),1):
            assert len(row)==len(new)==len(original[0])
            for a,b in zip(row,new):
                if a!=b:
                    try:near(a,b,'1e-9')
                    except Exception:raise AssertionError((p,n,a,b))
                fields+=1
        tables.append(dict(name=Path(p).name,rows=len(original)-1,fields=(len(original)-1)*len(original[0]),original_SHA=sha(p),fresh_SHA=sha(READER/Path(p).name)))
    summary=obj(READER/'summary.json');assert summary==obj(BASE/'reports05/summary.json')==receipt['summary']
    assert obj(READER/'confirmation_gate.json')==obj(BASE/'reports05/confirmation_gate.json')
    assert len(tables)==31 and fields==2388525==receipt['compared_fields'],(len(tables),fields)
    assert summary['paid_process_starts']==62 and summary['all_Optimize_starts']==5946 and summary['all_IIS_starts']==summary['native_missing_after']==0
    near(summary['paid_outer_seconds'],'15157.511650200002','1e-8')
    return dict(tables=len(tables),compared_fields=fields,receipt=receipt,summary=summary,field_comparison_independently_repeated=True,table_hashes=tables)


def run():
    public=public_integrity()
    announce('Archive/public identity checks complete; independently reconstructing eight formal endpoints')
    campaign=obj(BASE/'development03/identity.json');dev=obj(BASE/'development_protocol.json');qual=obj(BASE/'qualification/identity.json')
    admission=obj(BASE/'review/performance_admission.json');final=obj(BASE/'admission_decision.json')
    assert campaign['source_hashes']==qual['source_bindings']==dev['source_bindings']
    for p,pin in campaign['source_hashes'].items():assert sha(p)==pin
    for p,pin in campaign['helpers'].items():assert sha(ROOT/'scripts'/p)==pin
    for p,key in [('development_protocol.json','development_protocol_SHA'),('confirmation_protocol.json','confirmation_protocol_SHA'),
                  ('qualification/identity.json','qualification_identity_SHA'),('development03/identity.json','campaign_identity_SHA')]:
        assert sha(BASE/p)==admission[key]
    assert admission['decision']=='ACCEPT' and campaign['measured_source_commit']==admission['production_source_commit']==final['measured_source_commit']
    assert campaign['candidate_binary_sha256']==dev['production_PE_SHA']==admission['production_PE_SHA']==qual['production_PE_SHA']==final['production_PE_SHA']
    assert campaign['DLL_sha256']==admission['DLL_SHA']==qual['DLL_SHA']==final['DLL_SHA']
    snapshot=BASE/'review/source_final17'
    reuse={}
    for name in ('src/PaperExternalGiniTree.cpp','src/PaperK1AmSf.cpp','src/Round105GurobiDecomposition.inc','src/Round106Events.cpp','src/GurobiBaseline.cpp'):
        assert text(ROOT/name)==text(snapshot/name)
        reuse[name]=dict(current_SHA=sha(ROOT/name),prior_qualified_SHA=sha(snapshot/name),whole_source_identical=True)
    boundary='        FixedIntervalMipOutcome out;out.round107_scoped=true;out.available=capabilities().available;'
    prior=text(snapshot/'src/Round107GurobiFrontier.inc');current=text(ROOT/'src/Round107GurobiFrontier.inc')
    assert prior.split(boundary,1)[1]==current.split(boundary,1)[1]
    scope_boundary='struct Round107ScopeFacts {'
    assert text(ROOT/'include/Round107Scope.hpp').split(scope_boundary,1)[1]==text(snapshot/'include/Round107Scope.hpp').split(scope_boundary,1)[1]
    reuse['R107_MIP_and_scope']=dict(qualified_MIP_suffix_identical=True,scope_facts_decision_body_identical=True,
                                    whole_wrapper_header_byte_identity_claimed=False)
    roles={p['id']:instance(p) for p in dev['roles']};summary=lines(BASE/'development03/summary.jsonl');assert len(summary)==8
    arms=[];chains=[]
    reports=table(BASE/'reports05/arm_results.csv');assert len(reports)==8
    for n,z in enumerate(summary,1):
        assert z['number']==n and z['audit_passed'] and z['audit_error'] is None
        d=path(z['destination']);a=roles[z['id']];result=obj(d/'result.json');completion=obj(d/'completion.json');launch=obj(d/'launch.json')
        assert completion==z['completion'] and completion['returncode']==0 and completion['within_cap'] and completion['stop_reason']=='normal_return'
        assert launch['number']==n and launch['arm']==z['arm'] and launch['prereg_sha256']==sha(BASE/'development_protocol.json')
        assert launch['runner_sha256']==admission['campaign_runner_SHA']
        assert D(str(completion['fully_observed_end_to_end_seconds']))<=D(launch['cap_seconds'])
        endpoint=z['endpoint'];near(endpoint['gap'],D(str(endpoint['U']))-D(str(endpoint['L'])))
        report=next(r for r in reports if r['id']==z['id'] and r['arm']==z['arm'])
        assert report['PE_sha256']==campaign['candidate_binary_sha256'] and report['DLL_sha256']==campaign['DLL_sha256']
        near(endpoint['U'],report['U'],'1e-12');near(endpoint['L'],report['L'],'1e-12')
        if z['arm']=='GLOBAL-STRUCT':
            folder=d/'external/round106';s=obj(folder/'summary.json');evidence=dict(final_physical=physical(a,obj(folder/'witness.json')),mechanism=s)
            near(evidence['final_physical']['F'],endpoint['U']);near(s['LB'],endpoint['L'])
            assert s['final_native_bound_qualified'] and not s['certified'] and not s['unresolved_candidate'] and s['iis_calls']==s['core_confirmation_calls']==0
            runtime=obj(folder/'runtime.json')
        else:
            evidence=journal(d,a);near(evidence['U'],endpoint['U']);near(evidence['L'],endpoint['L'])
            near(result['objective'],endpoint['U']);near(result['lower_bound'],endpoint['L'])
            assert result['strict_certified_original_problem']==endpoint['certificate']
            if z['arm']!='P-GRB':
                assert result['decoded_descent_seeds_completed']==25
                evidence['controller']=cover(d/'external',a,result)
            if z['arm']=='FRONTIER-STRUCT':
                evidence['scoped']=scoped(d,a);chains+=evidence['scoped']['chains']
                runtime=obj(d/'external/round107/request_5/runtime.json')
            else:runtime=None
        if runtime:
            assert runtime['dll_sha256']==campaign['DLL_sha256'] and runtime['runtime']=='13.0.2'
            assert runtime['parameters']['read_return_code']==0
            for key,value in dev['parameters'].items():near(runtime['parameters'][key],value,'1e-12')
        arms.append(dict(number=n,id=z['id'],arm=z['arm'],U=str(endpoint['U']),L=str(endpoint['L']),
                         gap=str(D(str(endpoint['U']))-D(str(endpoint['L']))),certificate=endpoint['certificate'],
                         fully_observed_seconds=str(completion['fully_observed_end_to_end_seconds']),evidence=evidence))
        announce(f'Raw endpoint/physical/cover PASS: {n} {z["id"]} {z["arm"]}')
    selected=[next(c for c in chains if c['family']==f and c['role']==r) for f,r in [('A_MST','R98-C2'),('B_EXACT','F2'),('B_THRESHOLD','F2'),('FULL','F2')]]
    proof=[cut_proof(c,roles[c['role']]) for c in selected]
    announce('Actual A/B/FULL proof→violated lazy→same Optimize continuation PASS; checking native qualifications')
    qualification_result=qualification()
    source=text(ROOT/'src/Round107GurobiFrontier.inc')
    assert 'rows.push_back({cut,family,proof,k,request})' in source and 'const auto inherited=evidence.rows;' in source
    assert 'add(row.cut,row.family,row.vehicle,true,row.proof)' in source and 'round107_missing_state_inside_current_Y_domain:' in source
    assert 'global_physical' in source
    native=native_census();fees=fee_census()
    announce('Fee/native census PASS; independently comparing all public-reader table fields')
    reader=fresh_reader_check()
    endpoints={(r['id'],r['arm']):r for r in arms};ratios={};strong=[];guard=[]
    for role in roles:
        p,c=endpoints[role,'P-GRB'],endpoints[role,'FRONTIER-STRUCT']
        U=D(c['U'])/D(p['U']);gap=D(c['gap'])/D(p['gap'])
        first=c['certificate'] and (not p['certificate'] or D(c['fully_observed_seconds'])<=D('.9')*D(p['fully_observed_seconds']))
        other=c['certificate'] or (not p['certificate'] and not c['certificate'] and U<=D('1.01') and gap<=D('1.25'))
        strong.append(first);guard.append(other);ratios[role]=dict(U_ratio=str(U),absolute_gap_ratio=str(gap),A_strong=first,A_other_guard=other)
    A=any(strong) and all(guard)
    B_F2=D(ratios['F2']['U_ratio'])<=D('1.01') and D(ratios['F2']['absolute_gap_ratio'])<=D('1.05')
    B_C2=D(ratios['R98-C2']['U_ratio'])<=D('.99') and D(ratios['R98-C2']['absolute_gap_ratio'])<=D('.8')
    B=B_F2 and B_C2
    assert not A and not B and final['confirmation_gate']['A']==A and final['confirmation_gate']['B']==B
    cancellation=obj(BASE/'confirmation_cancellation.json')
    assert len(cancellation['groups'])==3 and sum(len(g['methods']) for g in cancellation['groups'])==9
    assert all(g['actual_native_processes']==g['actual_Optimize_calls']==0 and g['status']=='NOT_STARTED_CANCELLED' for g in cancellation['groups'])
    assert final['stage']=='STOP_TESTED_CONFIGURATION' and not final['substantive_revision']['used'] and not final['ADVANCE_CANDIDATE']
    assert final['confirmation_arms_cancelled']==9 and final['confirmation_arms_started']==0
    all_roots=collections.Counter()
    for p in READS:
        actual=Path(p).resolve(); assert any(actual.is_relative_to(x) for x in (ROOT,PUBLIC,READER,OUT))
        key=next(str(x) for x in (ROOT,PUBLIC,READER,OUT) if actual.is_relative_to(x));all_roots[key]+=1
    return dict(status='PASS_INDEPENDENT_PUBLIC_ONLY_FINAL_DELIVERY_REVIEW',final_stage='STOP_TESTED_CONFIGURATION',
                archive_public_integrity=public,source_runtime_identity=dict(source_commit=campaign['measured_source_commit'],source_files=len(campaign['source_hashes']),
                  production_PE_SHA=campaign['candidate_binary_sha256'],DLL_SHA=campaign['DLL_sha256'],reader_SHA=sha(ROOT/'scripts/round107_reader.py'),
                  source_and_helper_pins_rehashed=True,all_formal_launch_protocol_pins_checked=True,
                  selected_historical_native_qualification_protected_body_reuse=reuse,
                  published_runtime_readbacks_checked=True,PE_DLL_binary_rehash_performed=False,
                  binary_scope='Public carrier intentionally excludes EXE/DLL. This review verifies archived source/protocol/launch/native-runtime identity bindings, not fresh binary execution.'),
                eight_formal_endpoints=arms,actual_cut_lazy_same_Optimize_chains=proof,scoped_native_and_arithmetic_qualification=qualification_result,
                all_native_calls=native,all_fees=fees,fresh_reader_independent_comparison=reader,
                frozen_gate=dict(A=A,B=B,F2_B_guard=B_F2,C2_B_gate=B_C2,ratios=ratios,confirmation_cancelled=9),
                substantive_revision=dict(supported=False,used=False,reason='No raw correctness/cover/interface failure found; event activity and censored weak endpoints do not support an allowed substantive revision.'),
                public_only_read_provenance=dict(actual_roots=dict(all_roots),original_workspace_reads=False,old_restore_roots_read=False,
                  allowlist_enforced=True,total_unique_source_files=len(READS)),
                limits=['No fresh solver replay or compiler execution.','Native threshold absent→present remains NOT_EXPOSED; actual-domain zero-solver operator replay is separately labeled.',
                        'Formal UNKNOWN/post-cancel candidate exposure is NOT_EXPOSED; actual isolated inner UNKNOWN and actual outer deadline are checked.',
                        'All thin FRONTIER objectives/ownership and lazy activities are recomputed; selected complete raw vectors/base rows and physical fleets are checked, not every C2 full vector.'],
                correctness_blockers=[],Optimize_calls=0,IIS_calls=0,compiler_calls=0,paid_solver_starts=0,production_math_imports=0,production_reader_imports=0)


def audit_open(event,args):
    if event!='open' or not args or not isinstance(args[0],(str,bytes,os.PathLike)):return
    p=Path(os.fsdecode(args[0])).absolute()
    if p.is_relative_to(RUNTIME):return
    if str(p) in PATH_CACHE:p=PATH_CACHE[str(p)]
    else:
        resolved=p.resolve();PATH_CACHE[str(p)]=resolved;p=resolved
    if not any(p.is_relative_to(x) for x in (ROOT,PUBLIC,READER,OUT)):
        raise RuntimeError('Python audit guard rejected external filesystem read/write: '+str(p))
    mode=args[1] if len(args)>1 else None
    if isinstance(mode,str) and any(c in mode for c in 'wax+') and not p.is_relative_to(OUT):
        raise RuntimeError('Python audit guard rejected write outside exclusive review directory: '+str(p))


if __name__=='__main__':
    assert Path.cwd().resolve()==ROOT
    for n in itertools.count(1):
        execution=OUT/f'engineering{n:02d}'
        try:execution.mkdir();break
        except FileExistsError:continue
    code=1;tick=time.perf_counter()
    (execution/'executed.py').write_bytes(Path(__file__).read_bytes())
    write(execution/'launch.json',dict(command=[sys.executable,str(Path(__file__).resolve())],cwd=str(Path.cwd().resolve()),
        source_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        allowed_roots=[str(x) for x in (PUBLIC,ROOT,READER,OUT)],Optimize_calls=0,IIS_calls=0,compiler_calls=0,paid_solver_starts=0))
    write(execution/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()))
    sys.addaudithook(audit_open)
    try:
        result=run()
        with gzip.open(OUT/'actual_source_reads.json.gz','xt',encoding='utf-8') as f:json.dump(READS,f,ensure_ascii=False,sort_keys=True)
        result['actual_source_reads_SHA']=sha(OUT/'actual_source_reads.json.gz')
        result['executed_source_SHA']=sha(execution/'executed.py')
        write(OUT/'delivery_review.json',result)
        report=(
            '# 独立公开交付审查\n\n'
            '结论：PASS，最终阶段保持 STOP_TESTED_CONFIGURATION；A/B 均为 false，没有证据支持允许范围内的实质修订，九个确认臂保持取消。\n\n'
            '本检查器只使用 Python 标准库，从 E:/r107_public107_01、E:/r107_restore107_01、E:/r107_reader107_01 读取本次公开导出、全新恢复和实际重建结果。'
            '所有数据打开均受路径白名单约束，没有访问原工作区或旧恢复目录。独立逐 part、archive member 和恢复文件核对 SHA：R107 72553、R106 45827、R105 1556、补充账本 66。\n\n'
            '独立重算了实际 A 的保守 MST/handling、B 的完整六序及严格额外 pickup 预算，以及 FULL 的全站假设和三站完整 route-order 不可行性；'
            '实际违反行的 lazy API 返回 0，随后仍有同一次 master Optimize 的候选。检查全部 FRONTIER thin candidate 真目标/归属与 lazy 活动值，选取实际原始向量重算基础行，'
            '复核新的完整物理 fleet，包含返库余载卸车 handling。\n\n'
            '本轮资格的小域 target 实际返回原控制器、requeue、复用 child LP，再到 terminal/cert；正式 F2/C2 FRONTIER 也暴露该前序，但终端因 deadline 保留 open cover，未伪称获证。'
            '独立穷举小域核实 strict-empty INF/no Start、区间外物理 UB/no Start 和高局部 LB；另以覆盖算术反例保留其他叶义务。实际 inner 中断无解为 UNKNOWN，实际 outer deadline 未闭合。'
            '原生 FULL 跨 request 缓存/重映射合格；B 阈值缺列→可用仍未原生暴露，实际域/列上的零求解反例作为独立层报告。\n\n'
            '八臂原始终态、完整物理 UB、native return LB、初始 cover、AM/target/requeue/terminal 账本与同身份冻结参数得到复核。F2 ENS-C 获证而两个 STRUCT 臂仍删失；'
            'C2 FRONTIER 的 U 比同期 P 大约 1.891 倍、绝对 gap 约 15.940 倍，两个冻结确认门均未满足。无默认算法变更。\n\n'
            '从所有失败和成功原始 fee/native 账本独立得出 62 个保守 starts、15157.511650200002 秒 outer fee、5946 次 Optimize、0 IIS、0 missing-after；没有累加嵌套 native 时间。'
            '实际公开 reader 的 31 CSV、2388525 字段及 summary/gate 再次独立逐字段比较通过。\n\n'
            '审查没有启动 Optimize/IIS、编译或计费进程。公开载体不含 EXE/DLL；本审查重新核对源码/helper/script、原始 launch/协议和 runtime readback 身份绑定，未在公开恢复中重哈希不存在的二进制。'
            '详见 delivery_review.json、actual_source_reads.json.gz 及 engineering 执行回执；失败尝试若有均保留。\n')
        with (OUT/'delivery_review.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
        code=0
        print(json.dumps(dict(status=result['status'],result_SHA=sha(OUT/'delivery_review.json'),source_SHA=result['executed_source_SHA'],
                              all_Optimize=result['all_native_calls']['total_Optimize'],A=result['frozen_gate']['A'],B=result['frozen_gate']['B'])),flush=True)
    except Exception as exc:
        write(execution/'failure.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),source_reads_completed=len(READS)))
        raise
    finally:
        write(execution/'receipt.json',dict(exit_code=code,outer_engineering_seconds=time.perf_counter()-tick,
            executed_source_SHA=sha(execution/'executed.py'),actual_python_processes=1,Optimize_calls=0,IIS_calls=0,compiler_calls=0,paid_solver_starts=0,
            finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
