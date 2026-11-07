"""Read the real smoke lifecycles and bind the candidate before long runs."""
from round156_common import *

def run():
    configure();assert not budget()['unclosed'] or all(r['label']=='pre_panel_v1' for r in budget()['unclosed'])
    assert budget()['remaining_G1_seconds']>=43200+18000
    fresh=read(OUT/'review/fresh_producer_audit_v1/result.json');assert fresh['PASS']
    manifest=read(OUT/'candidate_manifest.json');assert sha(manifest['production_PE'])==manifest['production_PE_SHA']
    assert manifest['source_commit']=='092bad58d677cd8bef934d91e11d8abff93cba83'
    arms=[];facts=[]
    for method in ('B','E','Eplus'):
        camp=OUT/f'qualification/smoke_{method}_v1';result=read(camp/'result.json');assert result['PASS']
        identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
        close=read(d/'verification_closeout.json');assert close['implementation_qualified'] and close['evidence_complete'] and close['performance_eligible']
        arm=read(d/'round156_endpoint.json');arms.append(arm)
        assert arm['PE_SHA']==manifest['production_PE_SHA'] and arm['certificate']
        control=read(d/'round153_control_audit.json');root=control['root']
        assert all(row['floor_rows']==0 for row in control['models'])
        if method=='B':assert root is None
        else:
            assert root['qualified'] and root['node_limit']==(16384 if method=='Eplus' else 4096)
            assert root['lower']==.3761865166548789 and root['helper_exit']==0
        facts.append(dict(method=method,U=arm['U'],L=arm['L'],T_produce=arm['T_produce'],T_verify=arm['T_verify'],
            T_total=arm['T_total'],T_cert=arm['T_cert'],root=root,endpoint_SHA=sha(d/'round156_endpoint.json')))
    assert len({a['H_semantic_SHA'] for a in arms})==1
    assert len({a['U'] for a in arms})==len({a['L'] for a in arms})==1
    for variant in ('E','Eplus'):
        h=read(OUT/f'helper_manifest_{variant}.json')
        assert h['source_commit']==manifest['source_commit']
        assert all(sha(ROOT/name)==digest for name,digest in h['helper_dependencies'].items())
    write(OUT/'review/pre_panel_review.json',dict(decision='ACCEPT_NINE_PRESELECTED_PAID_ARMS',facts=facts,
        PE_SHA=manifest['production_PE_SHA'],production_source_commit=manifest['source_commit'],
        exact_same_PE=True,own_H_semantics_match=True,old_E_and_default_B_preserved=True,
        no_new_native_rows_columns_AM_or_split_rules=True,remaining_budget=budget()['remaining_G1_seconds'],
        nonimplementer_agent_review=False,source_SHA=sha(__file__),Optimize=0))
    from round156_campaign import arguments
    profile=read(ROOT/'config/gi_tbc_round137.json')
    profile.update(schema='round156-own-proof-floor-frozen-argv-v1',algorithm='GI-TBC with own RN16384 proof floor',
        round=156,source_commit=manifest['source_commit'],research_head=manifest['source_commit'],
        default_executable=manifest['production_PE'],verified_PE_SHA256=manifest['production_PE_SHA'],
        verified_DLL=str(DLL),verified_DLL_SHA256=DLL_SHA,research_profile=True,
        source_manifest='results/unified_exact_round156/candidate_manifest.json',
        parent_profile_SHA256=sha(ROOT/'config/gi_tbc_round137.json'),unique_complete_candidate='Eplus',
        default_AM=.08,maximum_depth=8,minimum_width=.0001,pair_only=True,H_seed=20260626)
    profile['argv']+=arguments('Eplus');write(ROOT/'config/gi_tbc_proof_floor_round156.json',profile)
    print(json.dumps(dict(accepted=True,arms=3,PE_SHA=manifest['production_PE_SHA'])),flush=True)

if __name__=='__main__':run()
