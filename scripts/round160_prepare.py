"""Minimal fixed-commit source/own-H recovery and independent corrected readback."""
import ast,zipfile,re
from fractions import Fraction as F
from round160_common import *

def data(panel,path):
    text=path.read_text(encoding='utf-8-sig')
    def vector(key):return ast.literal_eval(re.search(r'(?m)^\s*'+key+r'\s*=\s*(\[[^\n]*\])',text)[1])
    points=vector('points');initial=vector('initial');weights=vector('weights')
    if abs(max(weights[1:])-10)<=1e-6:weights=[v/10 for v in weights]
    distance=[[math.sqrt((a[0]-b[0])*(a[0]-b[0])+(a[1]-b[1])*(a[1]-b[1]))/1.5 for b in points] for a in points]
    return dict(n=len(initial)-1,Q=panel['Q_vector'],initial=initial,capacity=vector('capacities'),target=vector('target'),
        weights=weights,points=points,distance=distance,T=panel['T_seconds'],pickup=panel['pickup_seconds'],drop=panel['drop_seconds'],lam=panel['lambda'])

def prepare():
    from round157_fleet import verify
    prior=WORK/'worktrees/round156';matrix=read(prior/'results/unified_exact_round156/confirmation_matrix.json')
    refs=[]
    for pos in (9,6):
        launch=matrix['groups'][pos-1]['launch'];panel=launch['panel'];role=launch['id']
        folder=OUT/'inputs'/role;folder.mkdir(parents=True,exist_ok=False)
        content=git('show',BASE+':'+panel['input_path']);(folder/'instance.txt').write_bytes(content)
        assert sha(folder/'instance.txt')==panel['input_sha256']
        archive=prior/f'results/unified_exact_round156/artifacts/complete_arm_{pos:03}.zip'
        index=read(prior/'results/unified_exact_round156/carrier_manifest.json')
        member_prefix=f'results/unified_exact_round156/campaign_confirmation/{pos:03}/raw/'+launch['arm_id']
        selected=[member_prefix+'/external/initial_witness.json',member_prefix+'/hga.csv.exchange/final.json',
                  member_prefix+'/hga.csv.exchange/result.json',f'results/unified_exact_round156/campaign_confirmation/{pos:03}/identity.json']
        members=json.loads(gzip.open(archive.with_name(archive.stem+'.members.json.gz'),'rt').read());by={r['member']:r for r in members}
        sources=[];recovered={}
        with zipfile.ZipFile(archive) as z:
            for name in selected:
                raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==by[name]['SHA256']
                recovered[name]=json.loads(raw);sources.append(by[name])
        witness=recovered[selected[0]];exchange=recovered[selected[1]];identity=recovered[selected[3]]
        assert identity['candidate_binary_sha256']=='e5efe978f33e5c812fc9a0484caaae80696e4197ae27e289b4894d586af9d7e6'
        assert exchange['F']==witness['objective']
        assert [[o['station'],o['pickup'],o['drop']] for r in witness['routes'] for o in r['operations']]==[o for r in exchange['routes'] for o in r['operations']]
        assert [r['nodes'] for r in witness['routes']]==[r['nodes'] for r in exchange['routes']]
        d=data(panel,folder/'instance.txt');checked=verify(d,witness);assert checked['original_T_feasible']
        assert abs(checked['J']-witness['objective'])<1e-12
        lines=[str(len(witness['routes']))]
        for r in witness['routes']:
            ops={o['station']:o for o in r['operations']};lines.append(' '.join(map(str,[r['vehicle'],len(r['nodes']),*r['nodes']])))
            lines.append(' '.join(str(ops[i]['pickup']-ops[i]['drop']) for i in r['nodes'][1:-1]))
        (folder/'parent.txt').write_text('\n'.join(lines)+'\n',encoding='ascii')
        write(folder/'parent.json',witness)
        ref=dict(role=role,panel=panel,parent_J=checked['J'],parent_stage='own H / constructive + decoded descent + R83 closure; immediately before scope/RN',
            H_seed=20260626,production_source='092bad58d677cd8bef934d91e11d8abff93cba83',
            production_PE_SHA=identity['candidate_binary_sha256'],old_producer_reruns=0,
            fixed_science='751de842a0264a146701de6669b1f3dd6dc764b1',archive=str(archive),archive_SHA=sha(archive),members=sources,
            original_launch=launch['command'],data=d,original_physical_check=checked,
            source_current_production_diff=git('diff','092bad58d677cd8bef934d91e11d8abff93cba83',BASE,'--','src/Parser.cpp','src/Evaluator.cpp','src/Result.cpp','src/main.cpp','src/HgaTgbcRunner.cpp','src/Round83BlockExchange.cpp').decode(),
            duration='sqrt(dx*dx+dy*dy)/1.5; original T and general pickup/drop',scope='C++ derives capacity/eligible supports, necessary total-stock and parent-inclusive original-J scope from this parent')
        assert not ref['source_current_production_diff']
        write(folder/'source.json',ref);refs.append({k:ref[k] for k in ['role','parent_J','parent_stage','archive_SHA','fixed_science']})
    write(OUT/'input_manifest.json',dict(UTC=utc(),roles=refs,old_producer_reruns=0))

if __name__=='__main__':prepare()
