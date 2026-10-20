"""Returned-model evidence extension; immutable raw flags and actual columns.

The established complete model/Start/physical/coverage reader is retained.
Only its historical Seed0/1 administrative range and source-tree location are
extended. Native MIPFocus/Cuts are independently checked before this adapter.
"""
from round127_common import *
import contextlib,inspect,types,copy
import round122_evidence as inherited
import round114_audit as audit
import round108_reader as core
import round109_seed_scope as computed
import round109_seed_audit as seed_audit

E0_SOURCE=WORK/'worktrees/round126'
def expected(seed):
    assert type(seed) is int and seed in [0,1,2,3]
    return dict(computed.SETTINGS,Seed=seed)
_qualify_source=inspect.getsource(inherited.qualify_seed).replace(
    "for n,h in identity['source_hashes'].items():assert sha(root/n)==h",
    "for n,h in identity['source_hashes'].items():assert sha((E0_SOURCE if l['binary_layer']=='E0' else root)/n)==h")
_qualify_namespace=dict(vars(inherited),E0_SOURCE=E0_SOURCE)
exec(compile(_qualify_source,__file__+'::actual_Seed_source_tree','exec'),_qualify_namespace)
qualify_seed=_qualify_namespace['qualify_seed']
def journal(root,l,d,observations):
    j=inherited._raw_journal(root,l,d,observations)
    if l['seed']!=0:
        proof=qualify_seed(root,l,observations,read(d/'completion.json'),read(d.parents[1]/'identity.json'))
        j=computed.projected_journal(j,proof)
    return j
def legacy_journal(root,p,d):
    value=inherited._OLD_JOURNAL(root,p,d)
    if p.get('gurobi_seed',0)!=0:
        i=read(d.parents[1]/'identity.json');l=next(l for l in i['launches'] if core.portable(root,l['destination'])==d)
        proof=qualify_seed(root,l,read(d/'observations.json'),read(d/'completion.json'),i)
        value=computed.projected_journal(value,proof)
    return value
@contextlib.contextmanager
def extension():
    with inherited.extension():
        old=(audit.journal,computed.qualify,core.evidence.journal,computed.expected,seed_audit.expected)
        audit.journal=journal;computed.qualify=qualify_seed;core.evidence.journal=legacy_journal
        computed.expected=expected;seed_audit.expected=expected
        try:yield
        finally:audit.journal,computed.qualify,core.evidence.journal,computed.expected,seed_audit.expected=old
def verify(l,i):
    if l['binary_layer']=='E1' and l['arm']=='P-GRB':
        p=read(Path(l['destination'])/'round127_parameters.json');wanted=l.get('configuration',dict(MIPFocus=0,Cuts=-1))
        assert p['MIPFocus']==wanted['MIPFocus'] and p['Cuts']==wanted['Cuts'] and p['NumStart_before_optimize']==0
        assert p['loaded_after_presets'] and p['authoritative_model_environment']
    fn=types.FunctionType(inherited.verify.__code__,dict(vars(inherited),extension=extension),'round127_full_verify')
    return fn(l,i)
