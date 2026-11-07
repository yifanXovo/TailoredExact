"""Finite from-zero helper checks; no complete-arm data injection."""
from round108_reader import lp_model
from round151_math import scope_from_model
from round149_context import first_call,unique_model
from round156_common import *

def run(role,label,variant='Eplus'):
    target=OUT/'producer_checks'/label;target.mkdir(parents=True,exist_ok=False)
    if role=='K-20-S':
        matrix=read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
        launch=next(g['launch'] for g in matrix['groups'] if g['launch']['id']==role and g['launch']['method']=='S2' and g['launch']['seed']==0)
        panel=launch['panel'];assert panel['T_seconds']==5400 and panel['lambda']==.15 and panel['Q_vector']==[30,30]
        assert sha(ROOT/panel['input_path'])==panel['input_sha256']=='d1a65be4b87dead2ae351068ece3c3ce486a51c93652d778e055f2684606ea42'
        models=Path(launch['destination'])/'external/models';call=first_call(models);assert call
        source=unique_model(models,call['model_sha256']);bm=148;b=208
        scope=scope_from_model(lp_model(source),bm,b)
        provenance=dict(original_launch=launch,first_call=call,source=str(source),source_SHA=sha(source),scope=scope,
            fixed_commit='e735c3447eb1443713c700942d873de1783a4a26',preselected=True,previously_exposed=True)
    else:
        prior=read(OUT/'starting_inventory.json')[role]
        source=Path(prior['source']);assert sha(source)==prior['source_SHA']
        scope=prior['scope'];bm=scope['Bminus'];b=scope['B'];provenance=dict(source=str(source),source_SHA=sha(source),scope=scope,
            fixed_commit=prior['fixed_commit'],no_prior_price_or_stock_passed=True)
    write(target/'source_identity.json',provenance)
    entry='round156_online.py' if variant=='Eplus' else 'round153_online.py'
    args=[PYTHON,'-B',ROOT/'scripts'/entry,'--source',source,'--out',target/'helper',
        '--Bminus',bm,'--B',b,'--manifest',OUT/f'helper_manifest_{variant}.json','--remaining-global-seconds',3600]
    tick=time.perf_counter();p=subprocess.run(list(map(str,args)),cwd=ROOT,env=meter.environment())
    assert p.returncode==0,p.returncode
    r=read(target/'helper/result.json');price=read(target/'helper/pricing/result.json')
    assert r['qualified'] and r['scope']==scope and r['no_historical_inventory_or_price_loaded']
    write(target/'result.json',dict(role=role,variant=variant,lower=r['lower'],upper=r['upper'],gap=r['upper']-r['lower'],
        helper_outer_seconds=time.perf_counter()-tick,helper_seconds=r['seconds'],calls=price['calls'],
        own_DP_and_RN_only=True,no_historical_warm_or_lower=True,source_identity_SHA=sha(target/'source_identity.json')))
    print(json.dumps(read(target/'result.json')),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
