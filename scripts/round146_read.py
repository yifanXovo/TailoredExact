"""Reuse complete R137 physical/proof/Start verification; audit GD and STOCK."""
import types,collections,re
import round137_read as accepted
from round138_repair import scaled_rows
from round143_qualify import actual_spec
from round146_math import compiled
from round146_common import *
configure()
def verify(launch,identity):
    configure();d=Path(launch['destination']);gd=launch['R146_method']=='STOCK_GD';stock=launch['panel']['round138_stock_rlt'];facts=[]
    assert stock==(launch['R146_method'] in ('STOCK','STOCK_GD'))
    if stock:assert read(d/'round138_parameters.json')==dict(stock_rlt=True,gurobi_seed=launch['seed'],H_seed=20260626,loaded_after_presets=True)
    else:assert not (d/'round138_parameters.json').exists()
    if gd:assert read(d/'round146_parameters.json')==dict(GD=True,conditional=True,root_once=True,new_columns=0,source_solves=0,stock=stock,Seed=launch['seed'],H_seed=20260626)
    else:assert not (d/'round146_parameters.json').exists()
    audits=[read(p) for p in d.rglob('*.round146.native.json')];root_block=None;root_support=None
    if gd:
        paths=sorted((d/'external/models').glob('*_round146_GD.lp'),
            key=lambda path:int(re.search(r'_generation_(\d+)_round146_GD\.lp$',path.name).group(1)))
        assert paths and (d/'external/models/round146_root.json').exists()
        import round108_reader as parser
        root=parser.lp_model(paths[0]);p=launch['panel'];B=p['total_initial'];spec=actual_spec(root,max(0,B-sum(p['Q_vector'])),B)
        root_block=compiled(spec,d/'round146_offline_root_rows.json');root_support={int(i):set(v) for i,v in spec['supports'].items()}
        assert audits and all(a['PASS'] and a['source_solves']==a['Optimize_extra']==a['new_columns']==0 for a in audits)
        meta=read(d/'external/models/round146_root.json');assert meta['source_solves']==meta['new_columns']==0 and meta['rows']==len(root_block['rows'])
    else:assert not audits
    class Models(accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            fact,m=super().model_contract(root,p,path,arm);B=p['total_initial'];bm=max(0,B-sum(p['Q_vector']));counter=collections.Counter(m['rows'])
            expected_stock=collections.Counter(scaled_rows(p['V'],*m['bounds']['G'],bm,B))
            if stock:assert not expected_stock-counter,('missing stock rows',path)
            else:assert not expected_stock&counter,('unexpected stock rows',path)
            assert not any(k.startswith('rn_') for k in m['order'])
            if gd:
                spec=actual_spec(m,bm,B)
                assert all(set(v)<=root_support[int(i)] for i,v in spec['supports'].items())
                rows=[dict(r,terms={k:v for k,v in r['terms'].items() if k in m['order']}) for r in root_block['rows']]
                for r in rows:assert counter[(tuple(sorted(r['terms'].items())),'>=',0.)]==1,('missing GD row',path,r['name'])
                matched=[a for a in audits if a['model_SHA']==fact['SHA']];assert matched
                assert all(a['GD_rows']==len(rows) and a['GD_nonzeros']==sum(len(r['terms']) for r in rows) for a in matched)
            else:rows=[];assert 'r146_GD_' not in path.read_text(encoding='utf-8')
            facts.append(dict(model_SHA=fact['SHA'],GD_rows=len(rows),GD_nonzeros=sum(len(r['terms']) for r in rows),stock_rows=4 if stock else 0,new_columns=0,actual_scope_and_rows=True))
            return fact,m
    value=types.FunctionType(accepted.verify.__code__,dict(vars(accepted),ROOT=ROOT,OUT=OUT,ArmModels=Models))(launch,identity)
    write(d/'round146_control_audit.json',dict(PASS=True,method=launch['R146_method'],models=facts,Native_audits=audits,
        root_generation=read(d/'external/models/round146_root.json') if gd else None,
        all_H_Start_physical_scope_quality_lifecycle_inherited=True,independent_exact_root_coefficients=gd,Optimize=0,Native_load=0))
    return value
