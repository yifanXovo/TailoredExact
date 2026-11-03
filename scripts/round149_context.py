"""Select root context by the actual first Native call SHA, including zero GD."""
import round147_read as inherited
from round143_qualify import actual_spec
from round146_math import compiled
from round149_common import *


def unique_model(models,digest):
    paths=[p for p in models.glob('*.lp') if sha(p)==digest]
    assert len(paths)==1,('missing_or_duplicate_model_SHA',digest)
    return paths[0]


def first_call(models):
    path=models.parent.parent/'observations.json'
    observations=read(path) if path.exists() else []
    calls=[row['payload'] for row in observations if row['payload']['kind']=='call']
    if not calls:return None
    return min(calls,key=lambda r:r['call'])


def root_context(models,panel,gd,target,audits,fixture_model=None):
    metadata=models/'round146_root.json'
    if not gd:
        assert not metadata.exists() and not audits
        return None,None,None
    if not metadata.exists():
        assert not audits and first_call(models) is None
        return None,None,None
    meta=read(metadata);call=first_call(models)
    assert call is not None or fixture_model is not None
    source=unique_model(models,call['model_sha256']) if call else fixture_model
    model=inherited.parser.lp_model(source);total=panel['total_initial']
    spec=actual_spec(model,max(0,total-sum(panel['Q_vector'])),total)
    block=compiled(spec,target)
    assert len(block['rows'])==meta['rows'] and block['applicable']==meta['applicable']
    assert meta['Bminus']==spec['Bminus'] and meta['B']==spec['B']
    assert meta['source_solves']==meta['new_columns']==0
    assert all(a['PASS'] and a['GD_rows']==len(block['rows']) and
        a['source_solves']==a['Optimize_extra']==a['new_columns']==0 for a in audits)
    return block,{int(i):set(v) for i,v in spec['supports'].items()},meta
