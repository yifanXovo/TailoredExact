"""Stable full physical/proof reader plus RN-source/compact projection contract."""
import types,collections
import round137_read as accepted
from round143_qualify import actual_spec,check_matrix
from round144_qualify import exact_check
from round144_common import *
configure()
def verify(launch,identity):
    d=Path(launch['destination']);method=launch['R144_method'];enabled=method=='RNP';rn=method=='RN';facts=[]
    audits=[read(p) for p in d.rglob('*.round144.native.json')]
    sources=[read(p) for p in d.rglob('*.round143.native.json')]
    source=read(d/'external/round144_source.json') if enabled else None
    evidence=read(d/'external/round144_projection.json') if enabled and source.get('qualified') else None
    exact=None
    if enabled:
        assert read(d/'round144_parameters.json')==dict(RN_P=True,Seed=launch['seed'],H_seed=20260626,stock=False,counts='off',AP=False,source_policy='once_initial_root',persistent_RN=False)
        assert source['qualified'] and source['source_solves']==1 and not source['formal_control_from_source']
        assert evidence['source_SHA']==source['source_SHA'] and audits and sources
        assert all(a['PASS'] and a['RN_columns']==0 and a['PC_rows']==1 and a['Optimize_extra']==0 for a in audits)
        assert all(a['PASS'] and a['model_SHA']==source['source_SHA'] for a in sources)
    elif rn:
        assert not audits and not (d/'round144_parameters.json').exists() and sources
        assert read(d/'round143_parameters.json')==dict(RN=True,Seed=launch['seed'],H_seed=20260626,stock=False,counts='off',AP=False)
    else:assert not audits and not sources and not (d/'round144_parameters.json').exists()
    class Models(accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            nonlocal exact
            fact,m=super().model_contract(root,p,path,arm);B=p['total_initial'];bm=max(0,B-sum(p['Q_vector']))
            if rn or enabled and fact['SHA']==source['source_SHA']:
                spec=actual_spec(m,bm,B);wanted=check_matrix(m,spec)
                matches=[a for a in sources if a['model_SHA']==fact['SHA']];assert matches
                if enabled:
                    assert path.name=='round144_RN_source.lp' and 'r144_PC' not in path.read_text()
                    pi={r['name']:r['Pi'] for r in evidence['constraints']};rows=[dict(r,Pi=pi[r['name']]) for r in wanted]
                    bounds={v['name']:v for v in evidence['variables']}
                    assert set(bounds)==set(m['order'])
                    for k,v in bounds.items():assert (v['LB'],v['UB'])==m['bounds'][k]
                    exact=exact_check(bounds,rows,dict(rhs=evidence['row']['rhs'],terms=evidence['row']['terms']))
                facts.append(dict(model_SHA=fact['SHA'],kind='RN_source' if enabled else 'RN_bridge',RN_columns=len([k for k in m['order'] if k.startswith('rn_')]),RN_rows=len(wanted)))
            else:
                assert not any(k.startswith('rn_') for k in m['order'])
                if enabled:
                    assert source['source_lower']<=m['bounds']['G'][0]<=m['bounds']['G'][1]<=source['source_upper']
                    row=evidence['row'];terms={k:v for k,v in row['terms'].items() if k in m['order']}
                    counter=collections.Counter(m['rows']);wanted=(tuple(sorted(terms.items())),'<=',row['rhs']);assert counter[wanted]==1
                    assert any(a['model_SHA']==fact['SHA'] for a in audits)
                    facts.append(dict(model_SHA=fact['SHA'],kind='formal_compact',RN_columns=0,PC_rows=1,PC_nonzeros=len(terms)))
            return fact,m
    ns=dict(vars(accepted),ROOT=ROOT,OUT=OUT,ArmModels=Models)
    value=types.FunctionType(accepted.verify.__code__,ns)(launch,identity)
    if enabled:assert exact and exact['PASS'] and any(f['kind']=='formal_compact' for f in facts)
    write(d/'round144_control_audit.json',dict(PASS=True,method=method,models=facts,source=source,exact_compiled_online_PC_check=exact,
        native_compact_audits=audits,native_RN_audits=sources,all_H_Start_physical_scope_quality_lifecycle_inherited=True,Optimize=0,Native_load=0))
    return value
