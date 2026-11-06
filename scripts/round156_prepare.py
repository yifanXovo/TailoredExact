"""Read the sealed prior own-floor sources, never execute an old producer."""
from fractions import Fraction as F
from round108_reader import lp_model
from round151_math import scope_from_model
from round152_math import h_exact, unary_dp
from round153_pricing import stock_value
from round143_math import outward
from round140_common import git
from round156_common import *

def prepare():
    tick = time.perf_counter()
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert git('remote', 'get-url', 'origin').decode().strip() == 'https://github.com/yifanXovo/TailoredExact.git'
    assert sha(DLL) == DLL_SHA
    manifest = read(PRIOR/'results/unified_exact_round155/helper_manifest.json')
    assert sha(PYTHON) == manifest['python_SHA']
    dep = []
    for name, digest in manifest['helper_dependencies'].items():
        actual = sha(ROOT/name)
        if actual != digest:
            old = (PRIOR/name).read_bytes()
            assert sha(PRIOR/name) == digest
            assert (ROOT/name).read_bytes().replace(b'\r\n', b'\n') == old.replace(b'\r\n', b'\n'), name
        dep.append(dict(path=name, actual_SHA=actual, prior_SHA=digest,
                        exact_or_LF_CRLF_only=True))
    sources = {}
    for roundno in (155, 154):
        matrix = read(PRIOR/f'results/unified_exact_round{roundno}/confirmation_matrix.json')
        for group in matrix['groups']:
            launch = group['launch']
            role = launch['id']
            if launch.get('R154_method') != 'E' or role in sources: continue
            if role not in ('R-X35-S-T2','N-B35-S','R-B35-S-T1','R-X20-S-T1'): continue
            dest = Path(launch['destination'])
            folder = dest/'external/round153_floor'
            if not folder.exists(): continue
            source, result = read(folder/'source.json'), read(folder/'pricing/result.json')
            model = Path(source['source'])
            assert sha(model) == source['source_SHA']
            scope = scope_from_model(lp_model(model), source['scope']['Bminus'], source['scope']['B'])
            assert scope == source['scope'] == result['scope']
            costs = {(s['i'],y):h_exact(s,y) for s in scope['stations'] for y in s['support']}
            assert result['beta'] == 1
            assert result['d_exact'] == {f'{i}:{y}':str(v) for (i,y),v in costs.items()}
            checked = [stock_value(scope,v['Y'],1,costs) for v in result['stocks']]
            assert all(v['feasible'] and v['price']==F(old['price_exact']) for v,old in zip(checked,result['stocks']))
            best = min(checked, key=lambda v:v['price'])
            assert result['lower'] <= float(best['price']) <= result['upper']
            assert read(folder/'result.json')['lower'] == result['lower']
            inputs = ROOT/launch['panel']['input_path']
            assert sha(inputs) == launch['panel']['input_sha256']
            sources[role] = dict(scope=scope, lower=result['lower'], upper=outward(best['price'],True),
                upper_exact=str(best['price']), warm=[v['Y'] for v in checked], best_Y=best['Y'],
                prior_round=roundno, fixed_commit=SCIENCE155 if roundno==155 else SCIENCE154,
                source=str(model), source_SHA=sha(model), pricing=str(folder/'pricing/result.json'),
                pricing_SHA=sha(folder/'pricing/result.json'), helper_result=str(folder/'result.json'),
                helper_result_SHA=sha(folder/'result.json'), input=str(inputs), input_SHA=sha(inputs),
                prior_calls=result['calls'], original_launch=launch,
                no_saved_BB_tree=True, offline_start_only=True)
    assert {'R-X35-S-T2','N-B35-S','R-B35-S-T1','R-X20-S-T1'} <= sources.keys(), sources.keys()
    write(OUT/'starting_inventory.json',sources)
    candidate = read(PRIOR/'results/unified_exact_round154/candidate_manifest.json')
    assert sha(candidate['production_PE']) == candidate['production_PE_SHA']
    write(OUT/'infra/initial_identity.json',dict(UTC=utc(),base=BASE, main='b2b940c1e517a72e226ec60fc49ff19651737632',
        PR217_open_draft_unmerged=True, remote='https://github.com/yifanXovo/TailoredExact.git',
        branch=git('branch','--show-current').decode().strip(), workspace_policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),
        goal_SHA=sha(OUT/'goal.md'), no_applicable_AGENTS_found=True, protected_snapshot_SHA=sha(OUT/'infra/protected_initial.json'),
        python=str(PYTHON), python_SHA=sha(PYTHON), DLL=str(DLL), DLL_SHA=DLL_SHA,
        PE=candidate['production_PE'], PE_SHA=candidate['production_PE_SHA'], dependencies=dep,
        old_producer_reruns=0, old_carrier_downloads=0, seconds=time.perf_counter()-tick))
    print(json.dumps({k:dict(lower=v['lower'],upper=v['upper'],calls=v['prior_calls']) for k,v in sources.items()}),flush=True)

if __name__ == '__main__': prepare()
