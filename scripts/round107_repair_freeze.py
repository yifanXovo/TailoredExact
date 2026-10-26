"""Zero-Optimize refreeze after actual CLI guard/LP-metadata correctness repairs."""
from round107_common import *
import csv,shutil

def run():
    from round100_idle import ensure_idle
    ensure_idle()
    old=read(OUT/'qualification/identity.json');current=bindings()
    changed={p for p in set(old['source_bindings'])|set(current) if old['source_bindings'].get(p)!=current.get(p)}
    assert changed=={'src/main.cpp','src/Round107GurobiFrontier.inc','include/Round107Scope.hpp','include/Round107LpMetadata.hpp'},changed
    for p in ['src/GurobiBaseline.cpp','src/Round105GurobiDecomposition.inc','include/Round105Decomposition.hpp',
              'include/Round107Research.hpp','src/PaperExternalGiniTree.cpp','src/PaperK1AmSf.cpp','src/Round106Events.cpp']:
        assert old['source_bindings'][p]==current[p],p
    assert sha(DLL)==old['DLL_SHA']
    cli=read(OUT/'qualification/cli02/qualification.json');plan=read(OUT/'qualification/cli02/plan.json')
    assert cli['passed'] and cli['actual_scoped_MIP']>=1 and cli['actual_original_LP']>=1 and cli['IIS']==0
    assert plan['source_bindings']==current and cli['production_PE_SHA']==sha(BUILD/'ExactEBRP.exe')
    regression=read(OUT/'qualification/lp_metadata02/result.json');assert regression['passed'] and regression['Optimize']==0
    history=OUT/'protocol_history/repair_cli01';history.mkdir(parents=True,exist_ok=False)
    copies={}
    def replace(name,value):
        p=OUT/name;h=history/name;h.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,h);assert sha(p)==sha(h);copies[name]=sha(h);p.unlink();write(p,value)
    calls={}
    for p in (OUT/'qualification/cli02').rglob('calls.csv'):
        for r in csv.DictReader(p.open(newline='')):
            if r['stage']=='after':calls[r['phase']]=calls.get(r['phase'],0)+1
    calls['LP']=cli['actual_original_LP'];assert not calls.get('iis',0) and not calls.get('core_confirm',0)
    combined=old['native_call_totals'].copy()
    for phase,n in calls.items():combined[phase]=combined.get(phase,0)+n
    identity=dict(old,source_bindings=current,production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),fixture_PE_SHA=sha(BUILD/'Round107Tests.exe'),
        native_call_totals=combined,fee_snapshot=budget(),qualification_refreeze='repair_cli01',
        actual_production_CLI=dict(path='qualification/cli02',plan_SHA=sha(OUT/'qualification/cli02/plan.json'),
            qualification_SHA=sha(OUT/'qualification/cli02/qualification.json'),counts=calls,original_R68_startup_entered=True),
        semantic_LP_metadata_regression=dict(path='qualification/lp_metadata02',result_SHA=sha(OUT/'qualification/lp_metadata02/result.json'),
            actual_canonical_files=13,Optimize=0),
        selected_prior_fixture_production_PE_SHA=old['production_PE_SHA'],selected_prior_fixture_PE_SHA=old['fixture_PE_SHA'],
        affected_requalification='Actual production CLI now exercises original R83/R68 startup, delegated original LP plus semantic metadata, scoped MIP, physical handling and deadline with the repaired PE. Thirteen actual canonical files and malformed/order/wrapping/sign/zero cases passed zero-Optimize parser regression.',
        retained_native_scope_target_reuse='The entire R107State and MIP branch, ScopeFacts/decideRound107Scope bodies, original controller, original LP backend, R105Session/inner oracle and DLL are unchanged. Only the CLI preset guard and post-LP metadata evidence parser changed. Historical native scope/target/inner/outer evidence keeps its original PE/source bytes and is reused by these unchanged function bodies; whole Frontier.inc/header byte equality is not claimed.',
        inner_qualification_reuse='Original GurobiBaseline/R105Session/inner qualification header/DLL bytes are unchanged. The new LP metadata helper is not on the inner path.')
    replace('qualification/identity.json',identity)
    dev=read(OUT/'development_protocol.json');dev.update(production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),source_bindings=current,
        qualification_identity_SHA=sha(OUT/'qualification/identity.json'),production_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        correctness_refreeze='repair_cli01: original inherited R68 startup guard and semantic post-LP cutoff metadata; complete same-PE eight-arm rerun required.',
        superseded_partial_campaign='development02: three completed old-PE controls plus failed CLI arm4; all raw outputs and charges retained, none used for final paired conclusions.',
        orchestration='One paid wrapper contains actual finite CLI qualification plus all8 formal children, with an independently reviewed pause between phases. All child/outer times and fees retained. Conditional confirmation reserves a separate wrapper+9 children.',
        unaffected_frozen_contract='Role order, physical inputs, cap/reserve, original numerical/startup/AM/controller contracts, A/B/FULL and confirmation gates are identical to the initial pre-performance freeze.')
    replace('development_protocol.json',dev)
    manifest=read(OUT/'source_runtime_manifest.json');manifest.update(source_bindings=current,production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),
        fixture_PE_SHA=sha(BUILD/'Round107Tests.exe'),production_source_commit=dev['production_source_commit'],
        qualifications='Repaired PE has actual production CLI evidence. Selected earlier native scope/target/inner/outer fixtures retain exact original PE identities; reuse is by independently reviewed unchanged function bodies, separately from new parser regressions.')
    replace('source_runtime_manifest.json',manifest)
    write(history/'copies.json',dict(exact_previous_bytes=copies,confirmation_protocol_SHA=sha(OUT/'confirmation_protocol.json'),
        confirmation_gates_and_sealed_inputs_unchanged=True,production_changes=sorted(changed),Optimize=0,IIS=0))
    print(json.dumps(dict(refrozen=True,production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),qualification_identity_SHA=sha(OUT/'qualification/identity.json'),native_calls=combined,budget=budget())))

if __name__=='__main__':run()
