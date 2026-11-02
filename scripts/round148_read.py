"""Reuse accepted complete R134/R137/R147 validation; add actual shared-S rows."""
import types
import collections
from fractions import Fraction as F
import round147_read as inherited_reader
import round108_reader as parser
from round148_math import station_data,alpha
from round148_common import *
configure()


def verify(launch,identity):
    configure();d=Path(launch['destination']);enabled=launch['R148_method']=='D_SHARED_S'
    selection_path=d/'external/round148_selection.json'
    selection=read(selection_path) if selection_path.exists() else None
    accepted=inherited_reader.accepted
    if selection and selection['ready']:
        # The normal pre-strengthening root remains in every model, Native,
        # quality, lifecycle and cost audit. Its bound was never installed in
        # the controller. Only the new formal root has an lp_status entry.
        # Filter that one old call solely for the accepted cover reconstruction.
        old=accepted.inherited;core=old.core
        def formal_scoped_proofs(j,controller,U):
            cid=selection['source_call'];call=j['calls'][cid]
            assert cid in j['returned_ids'] and not call['native_preconditions']
            assert call['model_sha256']==selection['source_model_SHA']
            discarded=[r for r in controller['controller_native'] if r['model_sha256']==selection['source_model_SHA']]
            assert len(discarded)==1 and discarded[0]['solve_kind']=='LP'
            assert Path(discarded[0]['native_log']).name=='L0_lp.gurobi.log'
            assert int(discarded[0]['integer_domain_restored'])==1
            formal=dict(j,calls={k:v for k,v in j['calls'].items() if k!=cid},
                returned_native_proofs=[p for p in j.get('returned_native_proofs',[]) if p['call']!=cid])
            control=dict(controller,controller_native=[r for r in controller['controller_native'] if r['model_sha256']!=selection['source_model_SHA']])
            return core.scoped_proofs(formal,control,U)
        cover=types.FunctionType(core.chronological_cover.__code__,dict(vars(core),scoped_proofs=formal_scoped_proofs))
        complete=types.FunctionType(core.complete_cover.__code__,dict(vars(core),scoped_proofs=formal_scoped_proofs))
        core_view=types.SimpleNamespace(**dict(vars(core),chronological_cover=cover,complete_cover=complete))
        normal=types.FunctionType(old._normal_endpoint.__code__,dict(vars(old),core=core_view))
        old_view=types.SimpleNamespace(**dict(vars(old),_normal_endpoint=normal))
        accepted=types.SimpleNamespace(**dict(vars(accepted),inherited=old_view))
    value=types.FunctionType(inherited_reader.verify.__code__,dict(vars(inherited_reader),
        ROOT=ROOT,OUT=OUT,configure=configure,accepted=accepted))(launch,identity)
    command=launch['command'];assert command.count('--round148-shared-s')==1
    assert command[command.index('--round148-shared-s')+1]==('on' if enabled else 'off')
    if enabled:
        assert read(d/'round148_parameters.json')==dict(shared_S=True,low_only=True,root_once=True,
            max_rows=1,max_added_root_LP=1,new_columns=0,source_solves=0)
    else:assert not (d/'round148_parameters.json').exists()
    audits=[read(p) for p in d.rglob('*.round148.native.json')]
    if not enabled:assert selection is None and not audits
    else:assert all(a['PASS'] for a in audits)
    row=selection['row'] if selection and selection['ready'] else None
    exact_loss=0.
    if row:
        assert selection['qualified_input'] and selection['source_call']>0
        assert selection['new_columns']==selection['source_solves']==0 and selection['max_added_root_LP']==1
        block=read(d/'round147_offline_root_rows.json');c,data=station_data(dict(block,states=selection['states']))
        assert len(selection['slopes'])==len(c)
        if selection['kind']=='affine_low':
            beta=sum(F(v) for v in selection['slopes']);loss=F(0)
            for i,states in data.items():
                b=F(selection['slopes'][i-1])
                for st in states:
                    name=f"state_{i}_{st['y']}";q=alpha(st,b)+beta*c[i]*st['y']
                    actual=-F(row['terms'].get(name,0.));assert actual<=q,(name,actual,q)
                    loss+=q-actual
            assert row['terms']['G']==1.;exact_loss=float(loss)
        else:
            from round148_qualify import check_actual
            check_actual(dict(block,states=selection['states']),selection['point'],
                dict(selection,applicable=True))
        # Source matrix identity comes from the current run's immutable models.
        sources=[p for p in (d/'external/models').glob('*.lp') if sha(p)==selection['source_model_SHA']]
        assert len(sources)==1
        source=parser.lp_model(sources[0]);point=selection['point']
        for i in c:
            assert abs(point[f'Y_{i}']-math.fsum(y*point[f'state_{i}_{y}'] for y in block['scope']['supports'][str(i)]))<1e-6
        assert row['name'] not in sources[0].read_text(encoding='utf-8')
        assert audits and any(a['affine_rows']==0 for a in audits) and any(a['affine_rows']==1 for a in audits)
    facts=[]
    for fact in read(d/'round147_control_audit.json')['models']:
        paths=[p for p in (d/'external/models').glob('*.lp') if sha(p)==fact['model_SHA']]
        assert len(paths)==1;model=parser.lp_model(paths[0]);counter=collections.Counter(model['rows'])
        has='r148_shared_S:' in paths[0].read_text(encoding='utf-8')
        if has:
            assert row is not None
            terms={k:v for k,v in row['terms'].items() if k in model['order']}
            assert counter[(tuple(sorted(terms.items())),'>=',0.)]==1
        if enabled:
            hits=[a for a in audits if a['model_SHA']==fact['model_SHA']]
            assert hits and all(a['affine_rows']==int(has) for a in hits)
        facts.append(dict(model_SHA=fact['model_SHA'],shared_S_rows=int(has),GD_rows=fact['GD_rows'],
            GD_expected_migrated_and_Native_readback=True))
    if row:
        assert any(f['shared_S_rows']==1 for f in facts)
        logs=list((d/'external/native_logs').glob('L0_lp_round148.gurobi.log'))
        assert len(logs)==1
    write(d/'round148_control_audit.json',dict(PASS=True,enabled=enabled,selection=selection,
        exact_actual_slope_RHS_loss_bound=exact_loss,models=facts,
        new_rows_max=1,new_root_reoptimization_max=1,source_solves=0,new_columns=0,
        all_accepted_H_Start_physical_scope_quality_lifecycle_R134_checks_retained=True,
        Optimize=0,Native_load=0))
    return value
