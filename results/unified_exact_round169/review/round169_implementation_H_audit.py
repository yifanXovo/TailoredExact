"""Independent read-only 35-fleet/RNG/data audit; no optimizer imports."""
from pathlib import Path
import ast,hashlib,itertools,json,math,re,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round169'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    tick=time.perf_counter();cfg=read(OUT/'h_panel_frozen.json');rows=[];mx=0;native_named=[]
    for p in cfg['roles']:
        inp=ROOT/p['input_path'];text=inp.read_text(encoding='utf-8-sig')
        first=text.splitlines()[0];n,m=map(int,first.split('[')[0].split());q=ast.literal_eval(first[first.index('['):])
        def vec(k):return ast.literal_eval(re.search(r'^'+k+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
        a={k:vec(k) for k in ['initial','target','capacities','weights','points']}
        if abs(max(a['weights'][1:])-10)<1e-6:a['weights']=[x/10 for x in a['weights']]
        paths=[]
        for name,seed,mult in zip(cfg['path_order'],cfg['seeds']+cfg['seeds'][1:],[1,1,1,.5,2]):
            d=OUT/'h_raw'/p['id']/'primal'/name;data=read(d/'path.json');fleet=read(d/'fleet.json')['routes']
            y=a['initial'].copy();seen=set();cars=set();returns=[]
            assert data['effective_seed']==seed and data['search_lambda']==p['lambda']*mult and data['evaluation_lambda']==p['lambda']
            assert data['input_SHA256']==sha(inp)==p['input_sha256']
            assert data['fleet_SHA256']==sha(d/'fleet.json')
            raw=(d/'initial_random_orders.txt').read_bytes();semantic=raw.replace(b'\r\n',b'\n')
            assert data['initial_random_orders_SHA256']==hashlib.sha256(semantic).hexdigest()
            lines=semantic.decode().splitlines();assert len(lines)==24
            for z,line in enumerate(lines):
                idx,part=line.split(':');xs=[int(t) for t in part.split(',') if t]
                assert int(idx)==z and sorted(t for t in xs if t>0)==list(range(1,n+1)) and sum(t<=0 for t in xs)==m-1
            for rt in fleet:
                k=rt['vehicle'];assert k not in cars and 0<=k<m;cars.add(k);nodes=rt['nodes'];assert nodes[0]==nodes[-1]==0
                ops={z['station']:z for z in rt['operations']}
                assert len(ops)==len(rt['operations'])==len(nodes)-2 and set(nodes[1:-1])==set(ops)
                load=pick=drop=0
                for i in nodes[1:-1]:
                    assert i not in seen and 1<=i<=n;seen.add(i);op=ops[i];x,b=op['pickup'],op['drop']
                    assert isinstance(x,int) and isinstance(b,int) and x>=0 and b>=0 and bool(x)!=bool(b)
                    load+=x-b;pick+=x;drop+=b;assert 0<=load<=q[k]
                    y[i]+=b-x;assert 0<=y[i]<=a['capacities'][i]
                travel=math.fsum(math.hypot(a['points'][i][0]-a['points'][j][0],a['points'][i][1]-a['points'][j][1])/1.5 for i,j in zip(nodes,nodes[1:]))
                handling=60*(pick+drop+load);assert travel+handling<=p['T_seconds']+1e-7;returns.append(load)
            ratios=[y[i]/a['target'][i] for i in range(1,n+1)]
            S=math.fsum(ratios);G=math.fsum(abs(x-y) for x,y in itertools.combinations(ratios,2))/(n*S) if S>0 else 0
            P=math.fsum(w*abs(r-1) for w,r in zip(a['weights'][1:],ratios));F=G+p['lambda']*P
            err=max(abs(G-data['G']),abs(P-data['P']),abs(F-data['F']),abs(G+p['lambda']*mult*P-data['search_F']))
            mx=max(mx,err);assert err<2e-14
            assert data['complete'] and data['joint_complete'] and data['descent_complete'] and data['closure_complete'] and data['descent_seeds_completed']==25
            paths.append(dict(path=name,F=F,G=G,P=P,effective_seed=seed,decoded_checks=data['decoded_checks'],H_seconds=data['H_seconds'],
                return_loads=returns,orders_LF_semantic_SHA256=data['initial_random_orders_SHA256'],orders_file_byte_SHA256=sha(d/'initial_random_orders.txt')))
        for j in [1,2]:
            assert paths[j]['orders_file_byte_SHA256']==paths[j+2]['orders_file_byte_SHA256']
            assert (OUT/'h_raw'/p['id']/'primal'/f'M_s{j}'/'initial_random_orders.txt').read_bytes()==(OUT/'h_raw'/p['id']/'primal'/f'C_s{j}'/'initial_random_orders.txt').read_bytes()
        selection=read(OUT/'h_raw'/p['id']/'primal/selection.json')
        B=paths[0]['F'];M=min(t['F'] for t in paths[:3]);C=min(t['F'] for t in [paths[0],paths[3],paths[4]])
        assert abs(B-selection['B'])<2e-14 and abs(M-selection['M'])<2e-14 and abs(C-selection['C'])<2e-14
        rows.append(dict(role=p['id'],valid_fleets=len(paths),B=B,M=M,C=C,paths=paths))
        native_named.extend(str(f.relative_to(OUT)) for f in (OUT/'h_raw'/p['id']).rglob('*') if f.is_file() and ('journal' in f.parts or 'native' in f.name.lower()))
    value=dict(PASS=True,fleets=sum(x['valid_fleets'] for x in rows),maximum_absolute_numeric_difference=mx,
        Optimize_run_by_reviewer=0,H_calls=35,seconds=time.perf_counter()-tick,rows=rows,observed_native_named_files=native_named,
        native_initial_orders_hash_semantics='LF normalized in-memory order stream; actual CRLF file-byte hashes separately checked')
    (OUT/'review/implementation_independent_H_readback.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in value.items() if k not in ['rows','native_initial_orders_hash_semantics']},indent=2))
if __name__=='__main__':main()
