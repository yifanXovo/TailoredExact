"""Inherited complete lifecycle plus a narrowly qualified external proof source.

The native model/H/physical/Start/quality checks are unchanged. Only the
complete-cover proof collector learns the independently audited floor.
"""
import inspect,types
from fractions import Fraction as F
import round153_read as old
import round108_reader as core
from round154_common import *

def floor_contract(destination,enabled,launch,identity):
    proof_only=launch['R154_method']=='E'
    source=inspect.getsource(old.floor_contract)
    needle="expected=int(meta['qualified'] and meta['lower']>current['gamma_L']+1e-7)"
    assert source.count(needle)==1
    source=source.replace(needle,"expected=int(not proof_only and meta['qualified'] and meta['lower']>current['gamma_L']+1e-7)")
    ns=dict(old.floor_contract.__globals__,ROOT=ROOT,OUT=OUT,proof_only=proof_only)
    exec(compile(source,__file__+'::same_producer_contract','exec'),ns)
    value=ns['floor_contract'](destination,enabled,launch,identity)
    if not proof_only:
        assert not (destination/'external/round154_proof_ledger.json').exists()
        return value
    path=destination/'external/round154_proof_ledger.json'
    if not path.exists():
        assert value['root'] is None,'a materialized source requires a final proof ledger'
        return value
    ledger=read(path);meta=value['root']
    if meta is None:
        assert not ledger['source_qualified'] and not ledger['root_complete']
        assert all(r['proof_lower']==r['raw_search_lower'] for r in ledger['leaves'])
        assert ledger['proof_L']==ledger['raw_search_L']
        assert all('round154_own_root_floor' not in r['lower_bound_sources'] for r in core.rows(destination/'external/paper_leaf_ledger.csv'))
        value.update(proof_only=True,proof_ledger=ledger,unavailable_source_retains_B_information=True)
        write(destination/'round154_control_audit.json',value);return value
    assert ledger['root_source_SHA']==meta['source_SHA']
    assert ledger['source_qualified']==meta['qualified']
    assert ledger['root_cutoff']==meta['own_cutoff'] and ledger['floor']==meta['lower']
    assert ledger['cutoff_complement_floor']==min(meta['own_cutoff'],meta['lower'])
    assert ledger['native_floor_rows']==0 and ledger['AM_uses_search_bounds']
    # Bind "complete root" to the original decomposition and own source model,
    # not to the first artifact or c.generated alone.
    initial=core.rows(destination/'external/initial_decomposition_ledger.csv')
    roots=[v for v in ledger['leaves'] if v['id']=='L0']
    assert len(roots)==1
    root=roots[0]
    result=read(destination/'result.json')
    assert result['external_gini_tree_active_initial_intervals']
    assert root['gamma_L']==meta['gamma_L'] and root['gamma_U']==meta['gamma_U']
    assert result['external_gini_tree_initial_leaf_count']==1 and ledger['root_complete']
    assert result['external_gini_tree_root_coverage_valid']
    sources_live=ledger['source_qualified'] and ledger['root_complete'] and ledger['sources_live']
    byid={r['leaf_id']:r for r in core.rows(destination/'external/paper_leaf_ledger.csv')}
    for leaf in ledger['leaves']:
        raw=leaf['raw_search_lower'];expected=raw
        final=byid[leaf['id']]
        covered=meta['gamma_L']<=leaf['gamma_L']<=leaf['gamma_U']<=meta['gamma_U'] and leaf['cutoff']<=meta['own_cutoff']
        if sources_live and covered and final['status'] not in ('replaced','coalesced'):
            expected=max(raw,ledger['cutoff_complement_floor'])
            assert 'round154_own_root_floor' in final['lower_bound_sources'].split(';')
        assert leaf['proof_lower']==expected and float(final['lower_bound'])==expected
    relevant=[v for v in ledger['leaves'] if byid[v['id']]['status'] not in ('replaced','coalesced') and v['gamma_L']<result['upper_bound']-1e-7]
    assert ledger['proof_L']==min((v['proof_lower'] for v in relevant),default=0.)
    assert ledger['raw_search_L']==min((v['raw_search_lower'] for v in relevant),default=0.)
    assert result['lower_bound']==ledger['proof_L']
    value.update(proof_only=True,proof_ledger=ledger,proof_ledger_SHA=sha(path),initial_decomposition_rows=len(initial),
                 complete_root_checked=True,cutoff_complement_checked=True,Native_same_as_B_on_same_domain=True)
    write(destination/'round154_control_audit.json',value);return value

def verify(launch,identity):
    configure();destination=Path(launch['destination']);method=launch['R154_method']
    proof_only=method=='E'
    # Do not touch frozen reader modules on disk. This process-local adapter
    # extends only their explicit accepted proof-source list/collector.
    original=core.complete_cover
    if proof_only:
        audited=floor_contract(destination,True,launch,identity)
        meta=audited.get('root');ledger=audited.get('proof_ledger')
        def proofs(j,controller,U):
            values=core.scoped_proofs(j,controller,U)
            if meta and ledger and meta['qualified'] and ledger['root_complete'] and ledger['sources_live']:
                values.append(dict(call=None,lo=meta['gamma_L'],hi=meta['gamma_U'],L=min(meta['own_cutoff'],meta['lower']),
                    cutoff=meta['own_cutoff'],sequence=None,source='round154_own_root_floor',
                    source_SHA=meta['source_SHA'],source_audit_SHA=sha(destination/'round154_control_audit.json')))
            return values
        source=inspect.getsource(original)
        needle="valid_sources={'objective_nonnegative_penalty_G_floor',"
        assert source.count(needle)==1
        source=source.replace(needle,"valid_sources={'round154_own_root_floor','objective_nonnegative_penalty_G_floor',")
        ns=dict(vars(core),scoped_proofs=proofs)
        exec(compile(source,__file__+'::qualified_floor_cover','exec'),ns)
        core.complete_cover=ns['complete_cover']
    try:
        fn=types.FunctionType(old.verify.__code__,dict(vars(old),ROOT=ROOT,OUT=OUT,configure=configure,floor_contract=floor_contract))
        value=fn(launch,identity)
    finally:core.complete_cover=original
    value['arm'].update(R154_method=method)
    if proof_only and (destination/'round154_control_audit.json').exists():
        ledger=read(destination/'round154_control_audit.json').get('proof_ledger')
        if ledger:value['arm'].update(raw_search_L=ledger['raw_search_L'],own_floor=ledger['floor'],proof_placement=True)
    write(destination/'round154_endpoint.json',value['arm'])
    return value
