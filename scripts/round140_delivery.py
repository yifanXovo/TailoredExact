"""Bounded new-round carriers and additive semantic checks; never Optimize."""
from round140_common import *
import types,zipfile,collections
import round138_delivery as old

INDEX='__round140_member_index__.json'
BANNED=old.BANNED
make_zip=types.FunctionType(old.make_zip.__code__,dict(vars(old),ROOT=ROOT,OUT=OUT,INDEX=INDEX,sha=sha))

def groups():
    return [g for path in sorted(OUT.glob('*_matrix.json')) for g in read(path)['groups']]

def dependencies():
    assert not budget()['unclosed']
    inherited=ROOT/'results/unified_exact_round139/inherited_dependencies.json'
    old=read(inherited);roles={g['launch']['id'] for g in groups()}
    selections=[r for r in old['archives'] if r['role'] in roles and r['method'] in ['base','both']]
    write(OUT/'inherited_dependencies.json',dict(UTC=utc(),Optimize=0,
        R139_dependency_pin='94a275b7545eba4464a25945bbadc8b4bc896962',
        R139_dependency_path=inherited.relative_to(ROOT).as_posix(),R139_dependency_SHA=sha(inherited),
        accepted_full_reference_members=selections,old_metadata_files=old['metadata_files'],
        continuous_LP_dependencies=read(OUT/'historical_points.json')['dependencies'],
        limited_Seed1_reference_reuse=(dict(path='results/unified_exact_round140/seed1_reference_reuse.json',
            SHA=sha(OUT/'seed1_reference_reuse.json'),metadata=read(OUT/'seed1_reference_reuse.json'))
            if (OUT/'seed1_reference_reuse.json').exists() else None),
        scope='Fixed old commits and already accepted selected member identities. Only finite R138 diagnostic/root members were recovered locally. No old public acceptance or full history replay reopened.'))

def local_check():
    assert not budget()['unclosed']
    from round140_qualify import exact_matrix
    from round140_math import model_counts
    from fractions import Fraction as F
    from round135_read import validate_event_lifecycle,expected_settings
    import round108_reader as core
    tick=time.perf_counter();facts=[]
    for g in groups():
        l=g['launch'];d=Path(l['destination']);p=l['panel']
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        close=read(d/'verification_closeout.json');audit=read(d/'audit.json');e=read(d/'round135_endpoint.json')
        assert close['necessary_verification_complete'] and close['evidence_complete'] and audit['passed']
        assert close['audit_SHA']==sha(d/'audit.json') and e['performance_eligible'] and e['native_proof_qualified']
        producer=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json')
        assert producer['producer_seal_SHA']==sha(d/'producer_seal.json') and producer['native_stopped_no_reentry']
        for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,(d,name)
        physical=core.full_fleet(ROOT,p,read(d/'result.json'));assert abs(physical['F']-e['U'])<=1e-7
        payloads=[r['payload'] for r in read(d/'observations.json')];life=validate_event_lifecycle(payloads,True)
        assert read(d/'round140_control_audit.json')['PASS'];checked=[];root_model=None
        for c in (r for r in payloads if r['kind']=='call'):
            for name,value in expected_settings(l).items():assert c['settings'][name]==value
            path=core.portable(ROOT,c['model_path']);assert sha(path)==c['model_sha256']
            fact,model=exact_matrix(path,p,l['counts'],l['stock'],False);checked.append(fact)
            if c['leaf']=='L0' and root_model is None:root_model=model
        assert root_model is not None
        data=core.evidence.instance(ROOT,p);B=sum(data['b'][1:]);Bm=max(0,B-sum(p['Q_vector']))
        counts=model_counts(root_model,Bm,B);assert not counts['inventory_domain_infeasible']
        def integer_check(value,label):
            y=value['Y'];assert all(F(y[i]).denominator==1 and int(y[i]) in counts['supports'][i] for i in counts['supports'])
            ratios=[counts['ratios'][i]*int(y[i]) for i in sorted(counts['supports'])]
            H=sum(abs(a-b) for j,a in enumerate(ratios) for b in ratios[j+1:])
            old=sum(counts['TC'][i,int(y[i])] for i in counts['supports'])
            new=counts['constant']+sum(counts['TC2'][i,int(y[i])] for i in counts['supports'])
            assert old<=H and new<=H,(l['id'],label,old,new,H)
            return dict(label=label,exact_H=str(H),TC_rhs=str(old),TC2_rhs=str(new),valid=True)
        integer_points=[integer_check(physical,'own validated final incumbent')]
        if l['id']=='K-35-U' and l['counts']=='tc2':
            reuse=next(a for a in read(OUT/'baseline_reuse.json')['positions'] if a['role']==l['id'])
            for method in ['base','both']:
                old_result=read(Path(reuse[method]['destination'])/'result.json')
                old_physical=core.full_fleet(ROOT,p,old_result)
                integer_points.append(integer_check(old_physical,'retained '+method+' incumbent'))
        facts.append(dict(arm_id=l['arm_id'],counts=l['counts'],Seed=l['seed'],certificate=e['certificate'],U=e['U'],L=e['L'],
            audit_SHA=sha(d/'audit.json'),closeout_SHA=sha(d/'verification_closeout.json'),
            physical_return_loads=physical['return_loads'],lifecycle=life,models=checked,integer_count_checks=integer_points))
    assert 'gurobipy' not in sys.modules
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),positions=facts,seconds=time.perf_counter()-tick,
        Optimize=0,vendor_DLL_loads=0,scope='Additive pure physical/seal/lifecycle/parameter/actual-count-row replay; original complete H/Start/proof readers retained'))
    print(f'{len(facts)} entered positions pass local additive semantic checks')

def accounting():
    assert not budget()['unclosed'];b=budget();paths=sorted((OUT/'ordinary_steps').glob('*/receipt.json'));records=[read(p) for p in paths]
    fee_receipts=[read(p) for p in (OUT/'fees').glob('*/receipt.json')]
    experiment_outer=sum(r['outer_seconds'] for r in fee_receipts if r['budget_category'] in ['native','diagnostic'])
    additional_ordinary=sum(r['seconds'] for r in records)
    write(OUT/'cost_report.json',dict(UTC=utc(),experiment=b,fee_ordinary_seconds=b['separately_reported_seconds'],
        experimental_outer_including_pure_postverification_seconds=experiment_outer,
        experimental_outer_including_pure_postverification_within_43200=experiment_outer<=43200,
        additional_disjoint_ordinary_seconds=additional_ordinary,
        recorded_disjoint_process_wall_total_seconds=b['G1_seconds']+b['separately_reported_seconds']+additional_ordinary,
        ordinary_steps=[dict(label=p.parent.name,SHA=sha(p),receipt=r) for p,r in zip(paths,records)],
        reused_reference_original_clocks_retained_without_new_charge=True,all_experiment_qualification_and_failed_attempts_charged=True,
        ordinary_failed_steps=[p.parent.name for p,r in zip(paths,records) if r['exit_code']!=0],
        complete_outer_cost_without_nested_H_LP_MIP_Work_double_count=True,
        precision_scope='Measured processes only; interactive reading/editing/review/Git are not assigned invented precision'))
    print(json.dumps(dict(charged_seconds=b['G1_seconds'],hours=b['G1_seconds']/3600,remaining=b['remaining_G1_seconds'])))

def software_bindings():
    assert not budget()['unclosed']
    from round140_lp import LP_PYTHON
    assets={name:dict(path=str(path),SHA256=sha(path),bytes=Path(path).stat().st_size)
        for name,path in dict(production=E3,Native_DLL=DLL,compiler=COMPILER,
            process_python=PYTHON,LP_python=LP_PYTHON,document_python=DOCUMENT_PYTHON).items()}
    assert assets['production']['SHA256']==read(OUT/'candidate_manifest.json')['production_PE_SHA']
    assert assets['Native_DLL']['SHA256']==DLL_SHA
    historical='2204195cec25879507d958a8b6949add67091244b8b4da9cf3672f993548fa49'
    write(OUT/'software_bindings.json',dict(UTC=utc(),assets=assets,
        LP_python_matches_R138_verified_asset=assets['LP_python']['SHA256']==historical,
        observation_scope='Closeout byte hashes of installed runtimes. CPP PE/source were checked before full runs; the actual single loaded Gurobi DLL was checked in every LP process. Interpreter hashes are closeout observations, not retroactively claimed in-process assertions.',
        Optimize=0,vendor_DLL_loads=0,global_settings_changed=False))

def archive():
    assert not budget()['unclosed'] and read(OUT/'candidate_decision.json')['study_complete']
    assert read(OUT/'local_semantic_check.json')['PASS'];tick=time.perf_counter();records=[]
    for g in groups():
        folder=OUT/g['group'];records.append(make_zip(folder.relative_to(OUT).as_posix().replace('/','_'),[p for p in folder.rglob('*') if p.is_file()]))
    diagnostics=[]
    for name in ['inherited','roots','LP','LP_precision','qualification','fees','infra','cost_segments','ordinary_steps','math']:
        if name=='ordinary_steps':
            for step in (OUT/name).iterdir():
                if step.is_dir() and (step/'receipt.json').is_file():
                    diagnostics.extend(p for p in step.rglob('*') if p.is_file())
            continue
        for p in (OUT/name).rglob('*'):
            if p.is_file() and not p.is_relative_to(OUT/'qualification/runs'):diagnostics.append(p)
    records.append(make_zip('diagnostics_and_failures',diagnostics))
    manifest=read(OUT/'candidate_manifest.json');helpers={}
    for path in OUT.glob('*_matrix.json'):
        for name,digest in read(path)['helpers'].items():
            assert sha(ROOT/name)==digest,name
            if name in helpers:assert helpers[name]==digest,name
            helpers[name]=digest
    source_names=set(manifest['source_hashes'])|set(helpers)|{'.gitattributes','CMakeLists.txt','WORKSPACE_POLICY.md',
        'scripts/round126_export.py','scripts/round138_documents.py','scripts/round138_pdf_qa.py',
        'scripts/round139_documents.py','scripts/round139_common.py','scripts/round138_analyze.py',
        'scripts/round100_gurobi_runtime.py',
        'scripts/round138_public_read.py','scripts/round138_delivery.py','scripts/paper_s2.py','scripts/paper_s2_tc2.py',
        'results/unified_exact_round94/preregistration.json'}
    # Finite transitive local imports of the retained analysis/document helpers.
    # Sources only: this does not restore or revalidate old experiment raw.
    source_names.update({
        'scripts/read_round120.py','scripts/read_round121.py','scripts/round122_data.py',
        'scripts/round126_data.py','scripts/round127_analysis.py','scripts/round127_campaign.py',
        'scripts/round127_clocks.py','scripts/round127_data.py','scripts/round127_pipeline.py',
        'scripts/round127_qualify.py','scripts/round133_joint_check.py','scripts/round134_analyze.py',
        'scripts/round137_analyze.py','scripts/round138_math.py','scripts/round138_offline_products.py',
        'scripts/round138_read.py','scripts/round138_scaled_read.py','scripts/round138_tiny_read.py',
        'scripts/round69_research.py','scripts/round69_topology.py','scripts/round88_ot_closure.py',
        'scripts/round88_ot_diagnostic.py','scripts/round88_ot_epigraph.py','scripts/round88_ot_math.py'})
    source_names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round140*') if p.is_file())
    for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest,name
    source=make_zip('source_and_helpers',[ROOT/n for n in source_names]);records.append(source)
    inputs={g['launch']['panel']['input_path'] for g in groups()}
    for scope_path in (OUT/'roots').glob('*/scope.json'):
        p=read(scope_path)['panel'];assert sha(ROOT/p['input_path'])==p['input_sha256']
        inputs.add(p['input_path'])
    configs=['config/gi_tbc_round137.json','config/gi_tbc_stock_rlt_round138.json','config/gi_tbc_stock_placement_round139.json','config/gi_tbc_tc2_round140.json']
    write(OUT/'source_publication.json',dict(UTC=utc(),production_source_commit=manifest['source_commit'],
        production_PE_SHA=manifest['production_PE_SHA'],production_DLL_SHA=manifest['DLL_SHA'],source_bundle=source,
        actual_source_hashes=manifest['source_hashes'],frozen_helpers=helpers,
        additional_source_files={n:sha(ROOT/n) for n in source_names if n not in helpers and n not in manifest['source_hashes']},
        inputs={n:sha(ROOT/n) for n in inputs},configuration_files={n:sha(ROOT/n) for n in configs},
        inherited_science=dict(R137='e735c3447eb1443713c700942d873de1783a4a26',R138='1b19897ab5819ab3b7485ddc978954b45225f361',R139='94a275b7545eba4464a25945bbadc8b4bc896962'),
        commercial_assets_published=False,Optimize=0))
    meta=[p for p in OUT.iterdir() if p.is_file() and p.suffix.lower() in {'.json','.md','.bib','.pdf'} and p.name not in {'carrier_manifest.json','publication_pin.json','public_restore_receipt.json'}]
    meta += [p for name in ['reports','review','paper','figures'] for p in (OUT/name).rglob('*') if p.is_file()]
    meta += [ROOT/n for n in inputs|set(configs)]
    meta += [ROOT/n for n in ['docs/round140_research.md','docs/current_mainline.md','docs/unified_exact_research_index.md']]
    records.append(make_zip('science_and_paper',meta))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),carriers=records,source_bundle=source,new_round_only=True,
        all_entered_adverse_open_and_failures_retained=True,unique_science_retained=True,seconds=time.perf_counter()-tick,
        Optimize=0,public_check='Finite anonymous fixed-commit archive/member byte check only; no Optimize, compile or commercial Native load'))

if __name__=='__main__':globals()[sys.argv[1]]()
