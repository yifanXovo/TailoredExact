"""Compute admissibility for the inherited Seed0-only NEJ metadata guard.

Raw journals are immutable. This is an offline normal-return proof, not a
new callback/global observation, and never promotes global_available/null.
"""
import copy, collections, re
from pathlib import Path
import round108_reader as core

read=core.read;sha=core.sha;portable=core.portable
SETTINGS=dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,
    FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)

def expected(seed):
    assert type(seed) is int and seed in [0,1]
    return dict(SETTINGS,Seed=seed)

def qualify(root,launch,observations,completion,identity):
    root=Path(root).resolve();d=portable(root,launch['destination']);seed=launch['seed'];arm=launch['arm'];p=launch['panel']
    assert p['gurobi_seed']==seed
    assert launch['command'][launch['command'].index('--gurobi-seed')+1]==str(seed)
    calls=[r['payload'] for r in observations if r['payload']['kind']=='call']
    for c in calls:assert c['settings']==expected(seed),'actual nine-setting readback differs'
    if seed==0:
        return dict(schema='round109-computed-seed-scope-v1',actual_seed=seed,recovered_calls=[],raw_flags_preserved=True)
    # A partial/interrupted process cannot use a later normal-return gate.
    assert completion['stop_reason']=='normal_return' and completion['returncode']==0
    assert observations==read(d/'observations.json') and completion==read(d/'completion.json')
    assert len({c['call'] for c in calls})==len(calls),'duplicate native call id'
    result=read(d/'result.json')
    saved=read(d/'launch.json');assert saved['command']==launch['command'] and saved['panel']==p
    assert sha(root/p['input_path'])==p['input_sha256']
    for source,digest in identity['source_hashes'].items():assert sha(root/source)==digest,source
    # The frozen full-production entry excludes the optional request mutations.
    forbidden=['--round60','--round63','--round65-projection','--round65-budget','--round65-controller','--round89','--round96','--round97','--round101','--round102','--round103','--round104','--round105','--round106','--round107','--round100-continuous-quantities']
    assert not any(any(arg.startswith(prefix) for prefix in forbidden) for arg in launch['command'])
    return_events=[r['payload'] for r in observations if r['payload']['kind']=='returned']
    skip_events=[r['payload'] for r in observations if r['payload']['kind']=='not_started']
    assert all(e['return_code']==0 for e in return_events),'nonzero native return cannot recover'
    assert all(type(e['actual_Optimize']) in [int,bool] and e['actual_Optimize']==0 for e in skip_events)
    returned={e['call'] for e in return_events};not_started={e['call'] for e in skip_events}
    assert len(returned)==len(return_events) and len(not_started)==len(skip_events),'duplicate native disposition'
    assert returned|not_started=={c['call'] for c in calls} and not returned&not_started
    ledger=[] if arm=='P-GRB' else core.rows(d/'external/paper_optimize_ledger.csv')
    actual=[c for c in calls if c['call'] not in not_started]
    assert arm=='P-GRB' or len(ledger)==len(actual)
    models={};proofs=[]
    if arm=='P-GRB':
        assert len(actual)==1 and result['gurobi_optimize_count']==1 and result['gurobi_optimize_return_code']==0
        assert result['gurobi_native_domain_audit_passed'] is True and result['gurobi_lifecycle_valid'] is True
        assert result['native_mip_strict_gap_parameters_valid'] is True and result['gurobi_hga_start_requested'] is False
        for key,field in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:assert result[field]==p['reference'][key]
    elif actual:
        assert arm=='M-B' and result['algorithm_preset']=='research-round99-ensc-discrete-structure-m-binary'
        for field in ['backend_parameter_roundtrip_valid','feasibility_consistency_gate','lifecycle_complete','root_coverage_valid','parent_child_coverage_valid']:
            assert result['external_gini_tree_'+field] is True,field
        assert result['external_gini_tree_failure_reason'] in ['none','overall_global_deadline']
    else:
        assert arm=='M-B'
        physical=core.full_fleet(root,p,result);a=core.evidence.instance(root,p)
        assert p['lambda']>=0 and all(w>=0 for w in a['w'][1:])
        assert physical['F']<=1e-12,'zero-call closure requires independently physical zero objective'
    for position,c in enumerate(actual):
        assert type(c['native_preconditions']) in [int,bool] and c['native_preconditions'] in [0,1]
        assert not c['native_preconditions'],'inherited Seed1 guard should be false; unexplained flag needs review'
        row=ledger[position] if ledger else None
        if row:
            assert row['leaf_id']==c['leaf'] and row['model_sha256']==c['model_sha256']
            assert int(row['optimize_return_code'])==0
            assert portable(root,row['native_log'])==portable(root,c['native_log_path'])
            if row['solve_kind']=='LP':
                assert not c['full_original'] and int(row['integer_domain_restored'])==1
                continue # Never project an LP call to an integer prerequisite.
            assert row['solve_kind'] in {'MIP','CHILD_BOUND_TARGET_MIP','NEXT_LEAF_TARGET_MIP','PARTIAL_MIP_TARGET','MIP_CONSOLIDATION_TARGET','MIP_BLOCK'}
        assert c['call'] in returned
        path=portable(root,c['model_path']);assert sha(path)==c['model_sha256']
        if c['model_sha256'] not in models:
            facts,m=core.model_contract(root,p,path,arm);models[c['model_sha256']]=(facts,m)
        facts,m=models[c['model_sha256']];scope=core.model_scope_contract(c,m,p)
        log=portable(root,c['native_log_path']);text=log.read_text(encoding='utf-8')
        size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text)
        types=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',text)
        assert size and types
        assert (int(size[1]),int(size[2]))==(facts['rows'],facts['columns'])
        counts=collections.Counter(m['types'].values())
        assert dict(C=int(types[1]),I=int(types[2])-int(types[3]),B=int(types[3]))=={k:counts.get(k,0) for k in ['C','I','B']}
        if arm=='P-GRB':
            assert c['full_original'] and c['model_scope']=='complete_original_compact_milp'
            assert c['model_sha256']==p['reference']['canonical_sha256']==sha(d/'compact.lp')
            assert 'Loaded user MIP start' not in text
        else:
            assert not c['full_original'] and c['model_scope']=='complete_original_compact_milp_intersected_with_static_gini_interval'
        assert not any(r['payload']['kind']=='bound' and r['payload']['call']==c['call'] and
            (r['payload']['global_available'] or r['payload']['global_bound'] is not None) for r in observations)
        proofs.append(dict(call=c['call'],raw_native_preconditions=c['native_preconditions'],computed_native_prerequisites=True,
            model=facts,scope=scope,native_log_SHA=sha(log),successful_return=True,actual_settings=c['settings'],
            other_conjuncts_basis='unchanged full-production request defaults + actual canonical matrix/types + linked native return + backend postcondition gate',
            qualification_role='offline mathematical scope proof; no raw callback/global flag promotion'))
    return dict(schema='round109-computed-seed-scope-v1',actual_seed=seed,recovered_calls=proofs,
        observations_SHA=sha(d/'observations.json'),completion_SHA=sha(d/'completion.json'),result_SHA=sha(d/'result.json'),
        producer_source_SHA=identity['source_hashes']['src/GurobiBaseline.cpp'],raw_flags_preserved=True,
        raw_global_available_and_global_bound_unchanged=True,production_or_search_changed=False)

def projected_records(observations,proof,legacy_seed=False):
    projected=copy.deepcopy(observations);allowed={p['call'] for p in proof['recovered_calls']}
    for r in projected:
        c=r['payload']
        if c['kind']=='call':
            if c['call'] in allowed:
                c['raw_native_preconditions']=c['native_preconditions'];c['native_preconditions']=True
                c['computed_native_prerequisites']=True
            if legacy_seed:c['settings']['Seed']=0
    return projected

def projected_journal(journal,proof):
    j=copy.deepcopy(journal);allowed={p['call'] for p in proof['recovered_calls']}
    for i,c in j['calls'].items():
        if i in allowed:
            c['raw_native_preconditions']=c['native_preconditions'];c['native_preconditions']=True;c['computed_native_prerequisites']=True
    return j
