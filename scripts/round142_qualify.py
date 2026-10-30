"""Finite source-writer qualification, actual Native readback, zero Optimize."""
from round142_common import *
from round142_math import product_rows, range_rows, ranges, F
from round140_math import model_counts, serializable
from round142_lp import audit_row
import round108_reader as core
import collections
configure()

def build():
    from round142_build import COMPILER,SYSTEM
    manifest=read(OUT/'candidate_manifest.json')
    flags=read(ROOT/'results/unified_exact_round140/candidate_build.json')['flags']
    target=Path(manifest['production_PE']).parent/'Round142Qualify.exe'
    command=[COMPILER,*flags,ROOT/'scripts/round142_qualify.cpp',*manifest['objects'],manifest['archive']['path'],*SYSTEM,'-o',target]
    assert metered('compile_qualification','build',command,timeout=180)==0
    write(OUT/'qualification_build.json',dict(PE=str(target),PE_SHA=sha(target),source_SHA=sha(ROOT/'scripts/round142_qualify.cpp')))

def tiny():
    q=read(OUT/'qualification_build.json');assert sha(q['PE'])==q['PE_SHA']
    assert metered('tiny_cpp','diagnostic',[q['PE'],OUT/'qualification/writer'],30,60)==0

def native():
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    root=OUT/'qualification/writer';facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for tag in ['positive','fixed','tiny']:
            parent=core.lp_model(root/tag/'parent.lp')
            add=json.loads(json.dumps(serializable(model_counts(parent,2,4))))
            for mode in ['off','selected','all']:
                for side in [0,1]:
                    path=root/tag/f'{mode}_{side}.lp';expected=read(str(path)+'.expected.json')
                    parsed=core.lp_model(path)
                    assert collections.Counter(parent['rows'])<=collections.Counter(parsed['rows'])
                    assert parent['order']==parsed['order'] and parent['types']==parsed['types']
                    assert not any(k.startswith('r142_') for k in parent['order'])
                    if mode!='off':
                        spec=dict(threshold='1',pivot=expected['pivot'],side='low' if side==0 else 'high')
                        intervals=ranges(add,spec,mode)
                        wanted=range_rows(add,intervals,spec)+product_rows(add,intervals,expected['alpha'],expected['beta'])
                        actual=[r for r in expected['rows'] if r['name'].startswith('r142_')]
                        assert len(actual)==len(wanted)
                        by_name={r['name']:r for r in actual}
                        for r in wanted:
                            actual=by_name[r['name']]
                            assert actual['terms']==r['terms'] and actual['sense']==r['sense'] and actual['rhs']==r['rhs'],(tag,mode,side,r['name'])
                    else:assert len(expected['rows'])==2 and 'r142_' not in path.read_text()
                    with gp.read(str(path),env=env) as model:
                        assert sha(path)==expected['model_SHA']
                        for r in expected['rows']:audit_row(model,r)
                        assert {v.VarName:v.VType for v in model.getVars()}==parsed['types']
                        facts.append(dict(tag=tag,mode=mode,side=side,model_SHA=sha(path),
                            checked_rows=len(expected['rows']),columns=model.NumVars,rows=model.NumConstrs,
                            actual_Native_coefficients_senses_RHS_exact=True))
    write(OUT/'qualification_native_writer.json',dict(PASS=True,Optimize=0,native_identity=binding(),
        fixtures=facts,positive_alpha=True,fixed_g_linear_ranges_retained=True,tiny_coefficients_preserved=True,
        all_added_rows_under_one_expected_SHA=True,source_columns_unchanged=True))
    print(json.dumps(dict(PASS=True,fixtures=len(facts),Optimize=0)))

if __name__=='__main__':globals()[sys.argv[1]]()
