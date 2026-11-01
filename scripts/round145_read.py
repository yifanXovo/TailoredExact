"""Complete physical/proof contract inherited from R144; explicit RN-JP identity and full source list."""
import types,collections
import round137_read as accepted
from round143_qualify import actual_spec,check_matrix as rn_check
from round145_qualify import production_joint_rows,exact_check
from round145_common import *
configure()

def joint_check(model,spec):
    rows=rn_check(model,spec)
    if not spec['applicable']:return rows
    extra=production_joint_rows(spec);counter=collections.Counter(model['rows'])
    for r in extra:
        wanted=(tuple(sorted(r['terms'].items())),{'>':'>=','<':'<=','=':'='}[r['sense']],r['rhs'])
        assert counter[wanted]==1,r['name']
    return rows+extra

def verify_inherited_contract(launch,identity):
    d=Path(launch['destination']);method=launch['R144_method'];enabled=method=='RNP';rn=method=='RN';facts=[]
    audits=[read(p) for p in d.rglob('*.round144.native.json')]
    sources=[read(p) for p in d.rglob('*.round143.native.json')]
    source_path=d/'external/round144_source.json';source_not_reached=enabled and not source_path.exists()
    source=(read(source_path) if not source_not_reached else dict(source_solves=0,formal_RN_columns=0,PC_emitted=False,
        not_reached=True,derived_postverification_disposition=True)) if enabled else None
    applicable=enabled and not source_not_reached and source.get('applicable',True)
    evidence=read(d/'external/round144_projection.json') if enabled and source.get('qualified') else None
    exact=None
    if enabled:
        if launch['R145_method']=='RNJP':
            assert not (d/'round144_parameters.json').exists()
        else:
            assert read(d/'round144_parameters.json')==dict(RN_P=True,Seed=launch['seed'],H_seed=20260626,stock=False,counts='off',AP=False,source_policy='once_initial_root',persistent_RN=False)
        if source_not_reached:
            assert not audits and not sources
            assert not any(r['payload']['kind']=='call' for r in read(d/'observations.json'))
        else:assert audits
        if applicable:
            assert source['qualified'] and source['source_solves']==1 and not source['formal_control_from_source']
            assert evidence['source_SHA']==source['source_SHA'] and sources
            assert all(a['PASS'] and a['model_SHA']==source['source_SHA'] for a in sources)
        else:
            assert source['source_solves']==0 and source['formal_RN_columns']==0 and evidence is None and not sources
        assert all(a['PASS'] and a['RN_columns']==0 and a['PC_rows']==int(source.get('PC_emitted',False)) and a['Optimize_extra']==0 for a in audits)
    elif rn:
        assert not audits and not (d/'round144_parameters.json').exists() and sources
        assert read(d/'round143_parameters.json')==dict(RN=True,Seed=launch['seed'],H_seed=20260626,stock=False,counts='off',AP=False)
    else:assert not audits and not sources and not (d/'round144_parameters.json').exists()
    class Models(accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            nonlocal exact
            fact,m=super().model_contract(root,p,path,arm);B=p['total_initial'];bm=max(0,B-sum(p['Q_vector']))
            if rn or enabled and fact['SHA']==source.get('source_SHA'):
                spec=actual_spec(m,bm,B);wanted=(joint_check(m,spec) if launch['R145_method']=='RNJP' else rn_check(m,spec))
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
                    if applicable:assert source['source_lower']<=m['bounds']['G'][0]<=m['bounds']['G'][1]<=source['source_upper']
                    row=evidence['row'] if evidence else dict(terms={},rhs=0.)
                    terms={k:v for k,v in row['terms'].items() if k in m['order']}
                    if source.get('PC_emitted',False):
                        counter=collections.Counter(m['rows']);wanted=(tuple(sorted(terms.items())),'<=',row['rhs']);assert counter[wanted]==1
                    else:assert not terms and row['rhs']>=0
                    assert any(a['model_SHA']==fact['SHA'] for a in audits)
                    facts.append(dict(model_SHA=fact['SHA'],kind='formal_compact',RN_columns=0,PC_rows=int(source.get('PC_emitted',False)),PC_nonzeros=len(terms)))
            return fact,m
    # All source calls remain in the complete Native/quality/lifecycle/cost
    # audit. Only formal LPs enter the controller-bound reconstruction: the
    # source deliberately has no formal lp_status row or installed control.
    old=accepted.inherited;core=old.core
    def formal_scoped_proofs(j,controller,U):
        if not applicable:return core.scoped_proofs(j,controller,U)
        cid=source['source_call'];call=j['calls'][cid]
        assert cid in j['returned_ids'] and not call['native_preconditions'] and call['model_sha256']==source['source_SHA']
        assert Path(call['model_path']).name=='round144_RN_source.lp'
        discarded=[r for r in controller['controller_native'] if r['model_sha256']==source['source_SHA']]
        assert len(discarded)==1 and discarded[0]['solve_kind']=='LP' and int(discarded[0]['integer_domain_restored'])==1
        formal=dict(j,calls={k:v for k,v in j['calls'].items() if k!=cid},
            returned_native_proofs=[p for p in j.get('returned_native_proofs',[]) if p['call']!=cid])
        control=dict(controller,controller_native=[r for r in controller['controller_native'] if r['model_sha256']!=source['source_SHA']])
        return core.scoped_proofs(formal,control,U)
    cover=types.FunctionType(core.chronological_cover.__code__,dict(vars(core),scoped_proofs=formal_scoped_proofs))
    complete=types.FunctionType(core.complete_cover.__code__,dict(vars(core),scoped_proofs=formal_scoped_proofs))
    core_view=types.SimpleNamespace(**dict(vars(core),chronological_cover=cover,complete_cover=complete))
    normal=types.FunctionType(old._normal_endpoint.__code__,dict(vars(old),core=core_view))
    inherited=types.SimpleNamespace(**dict(vars(old),_normal_endpoint=normal))
    ns=dict(vars(accepted),ROOT=ROOT,OUT=OUT,ArmModels=Models,inherited=inherited)
    value=types.FunctionType(accepted.verify.__code__,ns)(launch,identity)
    if enabled:
        assert any(f['kind']=='formal_compact' for f in facts) or source_not_reached and value['arm']['declared_calls']==0
        if applicable:assert exact and exact['PASS']
    write(d/'round144_control_audit.json',dict(PASS=True,method=method,models=facts,source=source,exact_compiled_online_PC_check=exact,
        native_compact_audits=audits,native_RN_audits=sources,all_H_Start_physical_scope_quality_lifecycle_inherited=True,Optimize=0,Native_load=0))
    return value

def verify(launch,identity):
    joint=launch['R145_method']=='RNJP';d=Path(launch['destination'])
    if joint:
        assert read(d/'round145_parameters.json')==dict(RN_JP=True,NC_rows=2,TS_rows=4,source_policy='once_initial_root',formal_RN_columns=0)
        source_path=d/'external/round144_source.json'
        if source_path.exists():
            src=read(source_path)
            if src.get('qualified'):
                ev=read(d/'external/round144_projection.json');assert len(ev['source_rows'])==len(set(ev['source_rows']))
                assert all(f'r145_NC{k}' in ev['source_rows'] for k in (1,2))
                assert all(f'r145_TS{k}' in ev['source_rows'] for k in (1,2,3,4))
                audits=[read(p) for p in d.rglob('*.round143.native.json')]
                assert audits and all(a['joint_NC_TS_rows_checked']==6 and a['added_rows_checked']==len(ev['source_rows']) for a in audits)
                assert ev['row']['name']=='r145_PC'
    else:assert not (d/'round145_parameters.json').exists()
    value=verify_inherited_contract(launch,identity)
    write(d/'round145_control_audit.json',dict(PASS=True,method=launch['R145_method'],
        complete_source_list_includes_RN_NC_TS=joint,all_H_Start_scope_quality_lifecycle_source_discard_inherited=True,
        actual_source_native_all_six_rows_checked=joint,formal_RN_columns=0,Optimize=0,Native_load=0))
    return value
