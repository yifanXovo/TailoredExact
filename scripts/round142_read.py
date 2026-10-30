"""Reuse R141 lifecycle/physical/floor checks and verify only the new rows."""
from round142_common import *
import round141_read as legacy
from round142_math import ranges, range_rows, product_rows, F
from round141_chain import check as legacy_chain
from round140_math import model_counts,serializable
import collections,types,re
configure()

def verify(launch,identity):
    d=Path(launch['destination']);mode=launch['count_products']
    if mode!='off':
        assert read(d/'round142_parameters.json')==dict(count_products=mode,placement='count_sources_only',
            Seed=launch['seed'],H_seed=20260626)
    else:assert not (d/'round142_parameters.json').exists()
    facts=[]
    class ProductsModels(legacy.accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            fact,model=super().model_contract(root,p,path,arm)
            model['_r142_names']=re.findall(r'^\s*(r142_[^: ]+)\s*:',Path(path).read_text(),re.M)
            return fact,model
        def model_scope_contract(self,scope,model,p):
            fact=super().model_scope_contract(scope,model,p)
            count=legacy.count_scope(scope)
            if count and mode!='off':
                B=p['total_initial'];add=json.loads(json.dumps(serializable(model_counts(model,max(0,B-sum(p['Q_vector'])),B))))
                spec=dict(threshold=str(count['threshold']),pivot=count['pivot'],side='low' if count['side']==0 else 'high')
                intervals=ranges(add,spec,mode)
                wanted=range_rows(add,intervals,spec)+product_rows(add,intervals,scope['lower_g'],scope['upper_g'])
                assert set(model['_r142_names'])=={r['name'] for r in wanted}
                counter=collections.Counter(model['rows'])
                for r in wanted:assert counter[(tuple(sorted(r['terms'].items())),'>=',r['rhs'])]>=1,r['name']
                assert 'r141_b' not in model['order'] and not any(k.startswith('r142_') for k in model['order'])
                facts.append(dict(SHA=scope['model_sha256'],side=count['side'],mode=mode,
                    alpha=scope['lower_g'],beta=scope['upper_g'],CP_rows=4*len(intervals),range_rows=len(wanted)-4*len(intervals),
                    no_added_columns=True,complete_expected_row_set=True))
            else:assert not model['_r142_names'],'conditional range/CP leaked into parent, MIP or disabled source'
            return fact
    accepted=types.SimpleNamespace(**dict(vars(legacy.accepted),ArmModels=ProductsModels))
    ns=dict(vars(legacy),ROOT=ROOT,OUT=OUT,accepted=accepted)
    function=types.FunctionType(legacy.verify.__code__,ns,'verify',legacy.verify.__defaults__,legacy.verify.__closure__)
    value=function(launch,identity)
    chain=legacy_chain(d)
    if mode!='off' and chain['pair_ready']:
        assert {r['side'] for r in facts}=={0,1}
        for source in chain['sides']:assert any(f['SHA']==source['model_SHA'] and f['side']==source['side'] for f in facts)
    write(d/'round142_control_audit.json',dict(PASS=True,mode=mode,source_models=facts,
        actual_source_floors_bound_to_calls_and_SHA=True,chain=chain,Optimize=0,Native_load=0,
        conditional_rows_absent_from_parent_and_MIP=True,legacy_physical_H_Start_quality_scope_and_VType_checks_reused=True))
    return value

def postverify(batch,position):
    matrix=read(OUT/f'{batch}_matrix.json');group=matrix['groups'][position-1]
    identity=read(OUT/group['group']/'identity.json');launch=identity['launches'][0]
    d=Path(launch['destination']);assert (d/'producer_seal.json').exists()
    print(json.dumps(verify(launch,identity)['arm']),flush=True)

if __name__=='__main__':postverify(sys.argv[1],int(sys.argv[2]))
