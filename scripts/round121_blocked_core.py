"""Rebuild the finite current evidence of an unadmitted R121 batch, no solver.

This does not construct formal endpoints or replace the failed M-B closeout.
It rechecks sealed qualification data, physical fleets, actual Seed/scope/model
facts, fixed unrun positions, and the non-refundable accounting.
"""
from round121_common import ROOT,OUT,read,write,sha,helpers,bindings,budget
from round121_decision import decide
from pathlib import Path
import json

BLOCKER = ('Qualification minimum not completed: H100 MB-D1 Seed1 requires '
           'one supervisor parent and one actual child (2 starts); only 1 of '
           '8 qualification starts remains after four failed parents. '
           'H100 M-B original closeout is also incomplete; its full temporary '
           'read-only review passed without replacing that failed closeout.')
F2_PAIRS=[('MB-D1','M-B'),('MB-D1','P-GRB'),('MB-D1','MB-D0'),
          ('MB-D0','M-B'),('MB-D0','P-GRB'),('M-B','P-GRB')]
TRIPLE_PAIRS=[('MB-D1','M-B'),('MB-D1','P-GRB'),('M-B','P-GRB')]

def reconstruct():
    import round121_evidence as evidence
    import round108_reader as physical
    import round121_precontract_review as independent
    manifest=read(OUT/'input_manifest.json');candidate=read(OUT/'candidate_identity.json')
    assert bindings()==candidate['source_bindings'] and helpers()==candidate['helpers']
    assert sha(OUT/'input_manifest.json')==candidate['input_manifest_SHA']
    for key,file in [('argv_freeze_SHA','argv_freeze.json'),('protocol_SHA','protocol.json')]:
        assert sha(OUT/file)==candidate[key]
    inputs=[]
    for p in manifest['roles']:
        path=ROOT/p['input_path'];assert sha(path)==p['input_sha256']
        v,m,qs,a=independent.parse_input(path);assert (v,m,qs)==(p['V'],p['M'],p['Q_vector'])
        inputs.append(dict(id=p['id'],input_SHA=sha(path),V=v,M=m,Q=qs,
            total_initial=sum(a['initial'][1:]),total_target=sum(a['target'][1:]),
            sum_weights=sum(a['weights'][1:]),performance_measured=False))
    slots=[];pairs=[]
    for g in read(OUT/'argv_freeze.json')['groups']:
        identity=read(OUT/g['campaign']/'identity.json')
        assert identity['helpers']==candidate['helpers'] and identity['source_hashes']==candidate['source_bindings']
        for l in identity['launches']:
            d=physical.portable(ROOT,l['destination']);assert not d.exists()
            assert l['seed']==g['seed'] and l['command'][l['command'].index('--gurobi-seed')+1]==str(l['seed'])
            slots.append(dict(group=g['number'],id=l['id'],arm=l['arm'],seed=l['seed'],cap_seconds=l['cap_seconds'],
                state='NOT_STARTED_QUALIFICATION_BLOCKED',actually_executed=False,
                formal_protocol_qualified=False,U=None,L=None,gap=None,certificate=None,
                T_produce=None,T_verify=None,T_total=None))
        for c,p in F2_PAIRS if g['number']==1 else TRIPLE_PAIRS:
            pairs.append(dict(group=g['number'],id=g['id'],seed=g['seed'],candidate=c,control=p,
                classification='UNEVALUABLE',evaluable=False,severe_regression=None,
                basis='neither fixed formal position was started; no endpoint or certificate comparison'))
    assert len(slots)==16 and len(pairs)==18
    h=read(OUT/'qualification/h100/identity.json');qualification=[]
    for l in h['launches']:
        d=physical.portable(ROOT,l['destination'])
        if not d.exists():
            qualification.append(dict(arm=l['arm'],seed=l['seed'],state='NOT_STARTED',native_calls=0))
            continue
        seal=read(d/'producer_seal.json');producer=read(d/'producer_receipt.json')
        assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
        assert all(sha(d/n)==digest for n,digest in seal['required_SHA'].items())
        observations=read(d/'observations.json');completion=read(d/'completion.json');result=read(d/'result.json')
        proof=evidence.qualify_seed(ROOT,l,observations,completion,h)
        fleet=physical.full_fleet(ROOT,l['panel'],result)
        assert abs(fleet['F']-result['upper_bound'])<=1e-7
        journal=evidence.journal(ROOT,l,d,observations);contracts=[];context=evidence.ArmModels()
        try:
            for call,c in journal['calls'].items():
                if call in journal['not_started_ids']:continue
                path=physical.portable(ROOT,c['model_path'])
                if c['full_original']:
                    m=physical.lp_model(path);fact=dict(full_original=True,SHA=sha(path),rows=len(m['rows']),columns=len(m['order']))
                else:fact,m=context.model_contract(ROOT,l['panel'],path,l['arm'])
                contracts.append(dict(call=call,model=fact,scope=context.model_scope_contract(c,m,l['panel'])))
        finally:context.clear()
        audit=read(d/'audit.json');closeout=(d/'arm_total_receipt.json').exists()
        qualification.append(dict(arm=l['arm'],seed=l['seed'],state='ACTUAL_CLI_SEALED',
            producer_receipt_SHA=sha(d/'producer_receipt.json'),producer_seal_SHA=sha(d/'producer_seal.json'),
            all_sealed_required_bytes_unchanged=True,T_produce=producer['T_produce'],
            native_calls=len(contracts),computed_seed_scope=proof,actual_models=contracts,own_physical=fleet,
            canonical_audit_passed=audit.get('passed') is True,canonical_closeout_complete=closeout,
            failed_canonical_audit=audit if audit.get('passed') is not True else None,
            separate_temporary_review_passed=True,temporary_review_is_not_original_closeout=True,
            formal_performance_evidence=False))
    b=budget();assert not b['unclosed'] and b['qualification_starts']==7 and b['qualification_seconds']<=1800
    assert len(list((OUT/'fees').glob('*/launch.json')))==4
    fee_records=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        l=read(p.parent/'launch.json');r=read(p)
        assert r['actual_exit_observed'] and r['nested_native_seconds_added'] is False
        fee_records.append(dict(name=p.parent.name,receipt_SHA=sha(p),starts=r['conservative_process_starts'],
            native_children=r['actual_native_children'],outer_seconds=r['outer_seconds_upper'],exit_code=r['exit_code'],
            parent_pid=l['wrapper_pid'],parent_creation_unix=l['wrapper_creation_unix']))
    stage=decide([],True,blockers=[BLOCKER])
    stage.update(performance_gate_evaluated=False,formal_positions_planned=16,pair_positions_planned=18,
        all_support_and_veto_counts_unobserved=True,observed_zero_certificate_counts_are_not_a_performance_tie=True,
        proof_contradiction_observed=False,blocker_is_qualification_resource_and_closeout=True)
    return dict(schema='round121-blocked-current-evidence-v1',stage=stage,formal_slots=slots,pair_slots=pairs,
        actual_formal_arms=[],actual_formal_pairs=[],inputs=inputs,qualification=qualification,
        resource=b,fees=fee_records,h_reselection=[independent.old_h_review(role) for role in ['F2','R98-C2']],
        production_source_bindings_equal=True,source_files=len(bindings()),helpers_equal=True,helper_files=len(helpers()),
        production_PE_DLL_only_historical_hashes_in_public_replay=True,no_native_reentry=True,Optimize=0,
        new_D1_physical_endpoint_and_three_row_check='UNAVAILABLE: no new D1 native execution',
        default_ENS_changed=False,no_automatic_further_batch=True)

if __name__=='__main__':
    value=reconstruct();write(OUT/'blocked_current_core.json',value)
    print(json.dumps(dict(stage=value['stage']['stage'],formal_arms=0,formal_pairs=0,slots=16,pair_slots=18,
        budget=value['resource'],Optimize=0)))
