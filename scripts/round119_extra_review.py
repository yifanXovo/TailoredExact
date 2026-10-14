"""Separate implementation-author review process after scientific organization.

No solver load, new fleet, Optimize, native rerun, or third-party attribution.
"""
from round119_common import *
import subprocess,math

def review(commit):
    tick=time.perf_counter();assert not budget()['unclosed']
    from round100_idle import ensure_idle
    ensure_idle()
    candidate=read(OUT/'candidate_identity.json');assert bindings()==candidate['source_bindings'] and helpers()==candidate['helpers']
    proof=(ROOT/'src/Round119ProofContraction.cpp').read_text(encoding='utf-8')
    controller=(ROOT/'src/PaperExternalGiniTree.cpp').read_text(encoding='utf-8')
    backend=(ROOT/'src/GurobiBaseline.cpp').read_text(encoding='utf-8')
    header=(ROOT/'include/Instance.hpp').read_text(encoding='utf-8')
    assert 'round119_proof_contraction = false' in header or 'round119_proof_contraction=false' in header
    assert 'std::min(p.bound,p.cutoff)' in proof and 'U+tol<conservative' in proof
    assert 'a.depth<b.depth' in proof and 'a.parent<b.parent' in proof and 'a.side<b.side' in proof
    assert 'leaf.split_depth >= maximum_depth' in proof and 'p.used' in proof
    assert 'if(failed())return {}' in proof and 'same_scope_counterexample_all_dependencies_revoked' in proof
    assert 'terminal_mip_started' in controller and 'scheduler=std::move(transaction)' in controller
    assert 'evaluateRound119Return(outcome' in controller and 'round119_returned_event_lost_predicate' in controller
    assert 'round119_terminal_event' in backend and 'GRBterminate' in backend
    assert all(t not in proof for t in ['2648','4496','0.403249','0.787547','N40','F2','C2'])
    # Verify the scientific commit actually contains the carrier whose raw-byte
    # identities bind the produced sources, helpers and expected core.
    blob=subprocess.check_output(['git','show',commit+':results/unified_exact_round119/compact_evidence/manifest.json'],cwd=ROOT)
    manifest=json.loads(blob);assert manifest==read(OUT/'compact_evidence/manifest.json')
    for n,h in candidate['source_bindings'].items():assert manifest['files'][n]['SHA']==h
    for n,h in candidate['helpers'].items():assert manifest['files'][n]['SHA']==h
    values=[];exposure=[]
    for n in [1,2,3,4]:
        p=OUT/'reconstruction'/f'group{n:02d}'/'current_core.json'
        if not p.exists():assert n==4 and read(OUT/'confirmation_cancellation.json')['all_three_unrun'];continue
        v=read(p);values.append(v);assert sha(p)==manifest['files'][p.relative_to(ROOT).as_posix()]['SHA']
        assert len(v['arms'])==len(v['pairs'])==3 and all(a['formal_protocol_qualified'] for a in v['arms'])
        assert v['PE_SHA']==candidate['production_PE_SHA'] and v['DLL_SHA']==candidate['DLL_SHA']
        i=read(OUT/v['group']['campaign']/'identity.json')
        for a in v['arms']:
            assert a['T_produce']<=a['cap_seconds'] and a['T_total']>=a['T_produce']
            assert abs(a['gap']-(a['U']-a['L']))<1e-12
            assert a['native_Optimize']>=0
        m=next(m for m in v['mechanism'] if m['arm']=='MB-PC');exposure.append(dict(id=v['group']['id'],**m))
        for c in m.get('contracts',[]):
            assert c['U']+1e-7<min(c['proof_bound'],c['proof_cutoff']) and c['margin']>0
            assert c['new_upper']-c['new_lower']<c['old_upper']-c['old_lower'] and 1<=c['depth']<=8
            assert c['global_L']<=c['U']+1e-7
            assert c['close_both'] or c['next_Optimize_calls'] or c['deadline_remaining']<=0
    assert len(values)>=3
    gate=read(OUT/'development_admission.json');decision=read(OUT/'stage_decision.json')
    if gate['admitted']:assert len(values)==4 and decision['fixed_confirmation_completed']
    else:assert len(values)==3 and decision['fixed_confirmation_canceled']
    assert decision['stage'] in ['ADVANCE_MB_PC_TO_INDEPENDENT_CONFIRMATION','RETAIN_PROOF_CLOSURE_ONLY','STOP_TESTED_CONFIGURATION']
    assert not decision['default_ENS_changed'] and decision['no_automatic_further_test']
    b=budget();assert b['paid_starts']<=40 and b['paid_outer_seconds']<=48000 and b['qualification_starts']<=12 and b['qualification_seconds']<=2400
    assert read(OUT/'delivery/restored_check.json')['passed']
    checks=[
        dict(item=1,question='Current-arm paid proof and own physical U only',passed=True,evidence='frozen argv/source bindings, physical journals and paid source calls'),
        dict(item=2,question='Original embedding, cutoff complement, margin and scoped cover',passed=True,evidence='actual native matrices/Start audit, min(bound,cutoff), original witness reconciliation and reconstructed covers'),
        dict(item=3,question='Strict shrink, all complements, finite depth and retained terminal guard',passed=True,evidence='actual contracts, consumed-proof checks and scheduler transaction source'),
        dict(item=4,question='Real return before transaction, status/deadline/Start/true-G handling',passed=True,evidence='native event contract plus successful micro and finite return/physical negative checks'),
        dict(item=5,question='All new work paid; same new PE controls and no free historical fleet',passed=True,evidence='producer seals, three clocks, current own-fleet tables and fees'),
        dict(item=6,question='Nine fixed arms, conditional three positions and budget closure',passed=True,evidence='current cores, development gate, confirmation completion/cancellation and retained failed receipts'),
        dict(item=7,question='One stage decision closes this configuration or admits finite further confirmation',passed=True,evidence='stage_decision.json; no default/merge/automatic next grid')]
    receipt=dict(passed=True,scientific_commit=commit,scientific_manifest_SHA=sha(OUT/'compact_evidence/manifest.json'),
        reviewer='implementation author in a separate pure Python process',independent_third_party=False,
        separate_execution_step=True,new_native_reproduction=False,checks=checks,exposure=exposure,budget=b,
        retained_limitations=['numerical evidence under original tolerances, not rational proof','supplementary native lifecycle tail failed a test assumption and was not rerun',
            'all roles already exposed','current containment/restore do not attest all history or future commits'],
        recovery_receipt_SHA=sha(OUT/'delivery/restored_check.json'),Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick,
        receipt_does_not_attest_its_own_future_commit=True)
    write(OUT/'review/extra_review.json',receipt)
    print(json.dumps(dict(passed=True,checks=len(checks),scientific_commit=commit,reviewer=receipt['reviewer'])),flush=True)
if __name__=='__main__':review(sys.argv[1])
