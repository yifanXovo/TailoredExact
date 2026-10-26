"""Cheap signed-byte runtime eligibility for the independently audited P26.

Every matrix row is checked by the unchanged offline cold reader and reviewer.
This runtime gate only rehashes their complete signed current evidence.
"""
from round110_evidence import *


def verify_signed_cold_binding(root,launch,d):
    root=Path(root).resolve();d=Path(d);p=launch['panel'];s=core.read(root/side_path(launch))
    assert s['schema']=='round110-current-cold-call-rejection-v1'
    assert s['key']==[launch['number'],launch['id'],launch['seed'],launch['arm']]==[26,'G100-C1',0,'P-GRB']
    ident=core.read(root/ROUND/'campaign/identity.json')
    assert s['production_PE_SHA']==ident['candidate_binary_sha256'] and s['DLL_SHA']==ident['dll_sha256']
    assert s['campaign_identity_SHA']==core.sha(root/ROUND/'campaign/identity.json')
    assert s['command']==launch['command'] and s['input_SHA']==core.sha(root/p['input_path'])==p['input_sha256']
    for relative,digest in s['raw_bindings'].items():assert core.sha(located(root,relative))==digest
    audit=located(root,s['independent_audit_path']);a=core.read(audit)
    assert core.sha(audit)==s['independent_audit_SHA'] and a['decision']=='ACCEPT_CURRENT_CALL_REJECTION'
    assert a['current_key']==s['key'] and a['Optimize']==a['native_environment']==0
    for field in ['campaign_identity_SHA','production_PE_SHA','DLL_SHA','model_SHA','raw_bindings','time','exact_vector_path','exact_vector_SHA']:
        assert a[field]==s[field],('signed cold current binding differs',field)
    assert s['reject_all_call_native_lower_claims'] and s['withdraw_necessary_dependent_closures']
    assert s['own_U']>0. and s['qualified_L']==0. and not s['certificate_from_own_exact_zero']
    assert s['qualified_L_source']=='independently_proved_own_original_full_domain_nonnegative_floor'
    required=[d/'launch.json',d/'result.json',d/'observations.json',d/'completion.json',d/'audit.json',
        d/'native_end_receipt.json',d/'postexit_audit_receipt.json',d/'compact.lp',d/'native.log',d/'phases.csv',
        located(root,s['exact_vector_path'])]
    assert all(q.relative_to(root).as_posix() in s['raw_bindings'] for q in required)
    assert core.sha(located(root,s['exact_vector_path']))==s['exact_vector_SHA']
    assert s['model_SHA']==p['reference']['canonical_sha256']
    return s
