"""R148-local zero-GD reader context selected by the current source SHA.

Installed only after the initial frozen K35 pair; it never changes production.
The normal accepted call/model audit still validates the source-call binding.
"""
import round147_read as old_reader
from round143_qualify import actual_spec
from round146_math import compiled
from round148_common import *
configure()


def source_call_check(selection, observations, native_ledger):
    calls=[r['payload'] for r in observations
           if r['payload']['kind']=='call' and r['payload']['call']==selection['source_call']]
    assert len(calls)==1,'missing_or_duplicate_current_source_call'
    call=calls[0]
    assert call['model_sha256']==selection['source_model_SHA'],'current_source_call_SHA_mismatch'
    assert call['leaf']=='L0'
    # Raw Native preconditions describe the integer model before relaxation.
    # The accepted controller ledger, not that raw flag, identifies an LP.
    linked=[r for r in native_ledger if r['leaf_id']==call['leaf'] and
        r['model_sha256']==call['model_sha256'] and
        Path(r['native_log']).resolve()==Path(call['native_log_path']).resolve()]
    assert len(linked)==1 and linked[0]['solve_kind']=='LP','current_source_not_unique_controller_LP'
    assert int(linked[0]['optimize_return_code'])==0
    return dict(call=call,controller_LP=linked[0])


def root_context(models,panel,gd,target,audits,fixture_model=None):
    metadata=models/'round146_root.json';selection_path=models.parent/'round148_selection.json'
    if not (gd and metadata.exists() and selection_path.exists()):
        return old_reader.root_context(models,panel,gd,target,audits,fixture_model)
    meta=read(metadata)
    if meta['rows']!=0:
        return old_reader.root_context(models,panel,gd,target,audits,fixture_model)
    selection=read(selection_path)
    assert selection['source_call']>0 and len(selection['source_model_SHA'])==64
    # Do not sort wildcard filenames: the affine model and an earlier unrelated
    # generation can coexist. The current immutable source call chooses one.
    sources=[p for p in models.glob('*.lp') if sha(p)==selection['source_model_SHA']]
    assert len(sources)==1,'missing_or_duplicate_current_source_model_SHA'
    first=sources[0];model=old_reader.parser.lp_model(first)
    total=panel['total_initial'];spec=actual_spec(model,max(0,total-sum(panel['Q_vector'])),total)
    block=compiled(spec,target)
    assert len(block['rows'])==meta['rows']==0 and block['applicable']==meta['applicable']
    assert meta['Bminus']==spec['Bminus'] and meta['B']==spec['B']
    assert meta['source_solves']==meta['new_columns']==0
    assert all(a['PASS'] and a['GD_rows']==0 and a['source_solves']==a['Optimize_extra']==a['new_columns']==0 for a in audits)
    support={int(i):set(ys) for i,ys in spec['supports'].items()}
    return block,support,meta
