"""Round141-only evidence packing and bounded additive pure checks."""
from round141_common import *
from round141_analyze import require_idle
import ast,types,zipfile
import round138_delivery as previous

INDEX='__round141_member_index__.json'
BANNED=previous.BANNED
make_zip=types.FunctionType(previous.make_zip.__code__,dict(vars(previous),ROOT=ROOT,OUT=OUT,INDEX=INDEX,sha=sha))

def groups():
    return [g for m in sorted(OUT.glob('*_matrix.json')) for g in read(m).get('groups',[])]

def local_check():
    require_idle()
    import round108_reader as core
    from round135_read import validate_event_lifecycle
    tick=time.perf_counter();facts=[]
    for g in groups():
        launch=g['launch'];d=Path(launch['destination'])
        if not (d/'verification_closeout.json').exists():continue
        p=launch['panel'];assert sha(ROOT/p['input_path'])==p['input_sha256']
        close=read(d/'verification_closeout.json');audit=read(d/'audit.json')
        endpoint=read(d/'round135_endpoint.json');controls=read(d/'round141_control_audit.json')
        chain=read(d/'round141_chain_audit.json')
        assert close['necessary_verification_complete'] and close['evidence_complete'] and audit['passed']
        assert close['audit_SHA']==sha(d/'audit.json') and controls['PASS'] and chain['PASS']
        assert endpoint['performance_eligible'] and endpoint['native_proof_qualified']
        assert endpoint['T_cert'] is None if not endpoint['certificate'] else endpoint['T_cert']==endpoint['T_produce']
        receipt=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json')
        assert receipt['native_stopped_no_reentry'] and receipt['producer_seal_SHA']==sha(d/'producer_seal.json')
        for path,digest in seal['required_SHA'].items():assert sha(d/path)==digest,(d,path)
        payloads=[r['payload'] for r in read(d/'observations.json')]
        lifecycle=validate_event_lifecycle(payloads,True)
        model_facts=[]
        for call in (r for r in payloads if r['kind']=='call'):
            model=core.portable(ROOT,call['model_path']);assert sha(model)==call['model_sha256']
            model_facts.append(dict(call=call['call'],model_SHA=call['model_sha256']))
        physical=core.full_fleet(ROOT,p,read(d/'result.json'))
        assert abs(physical['F']-endpoint['U'])<=1e-7
        facts.append(dict(arm_id=launch['arm_id'],qualification=launch['stage'].startswith('qualification'),
            method=launch['method'],seed=launch['seed'],U=endpoint['U'],L=endpoint['L'],certificate=endpoint['certificate'],
            audit_SHA=sha(d/'audit.json'),closeout_SHA=sha(d/'verification_closeout.json'),
            controls_SHA=sha(d/'round141_control_audit.json'),chain_SHA=sha(d/'round141_chain_audit.json'),
            calls=model_facts,lifecycle=lifecycle))
    assert facts and 'gurobipy' not in sys.modules
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),positions=facts,seconds=time.perf_counter()-tick,
        Optimize=0,commercial_native_loads=0,
        scope='Additive seal/physical/lifecycle/model-hash replay. Original full H/Start/quality/count-scope/actual-row audits and independent floor-to-call chain checks are retained, not relabelled as a new full replay.'))
    print(f'{len(facts)} sealed qualified positions pass additive local checks')

def accounting():
    require_idle();b=budget()
    ordinary_paths=sorted((OUT/'ordinary_steps').glob('*/receipt.json'))
    ordinary=[read(p) for p in ordinary_paths]
    fees=[(p.parent.name,read(p)) for p in sorted((OUT/'fees').glob('*/receipt.json'))]
    experimental=[(name,r) for name,r in fees if r['budget_category'] in ['native','diagnostic']]
    outer=sum(r['outer_seconds'] for _,r in experimental)
    assert b['G1_seconds']<=36000 and outer<=36000
    additional=sum(r['seconds'] for r in ordinary)
    write(OUT/'cost_report.json',dict(UTC=utc(),experiment=b,
        experimental_outer_including_pure_postverification_seconds=outer,
        conservative_outer_within_36000=True,fee_ordinary_seconds=b['separately_reported_seconds'],
        additional_disjoint_ordinary_seconds=additional,
        recorded_disjoint_process_wall_total_seconds=b['G1_seconds']+b['separately_reported_seconds']+additional,
        experimental_fee_receipts=[dict(label=name,receipt=r) for name,r in experimental],
        ordinary_steps=[dict(label=p.parent.name,SHA=sha(p),receipt=r) for p,r in zip(ordinary_paths,ordinary)],
        failed_measured_steps=[name for name,r in fees if r['exit_code']!=0]+[p.parent.name for p,r in zip(ordinary_paths,ordinary) if r['exit_code']!=0],
        qualifiers_and_failed_experimental_attempts_included=True,old_references_new_Optimize=0,
        nested_H_LP_MIP_Work_not_added_twice=True,
        precision_scope='Measured child processes only; interactive editing, review and Git have no invented wall-time precision. Late publication/cleanup receipts are additive and are not recursively packed into their own science carrier.'))
    print(json.dumps(dict(charged=b['G1_seconds'],hours=b['G1_seconds']/3600,conservative_experimental_outer=outer)))

def software_bindings():
    require_idle();manifest=read(OUT/'candidate_manifest.json')
    paths=dict(production=Path(manifest['production_PE']),Native_DLL=DLL,
        compiler=Path('D:/msys64/ucrt64/bin/g++.exe'),process_python=PYTHON,
        LP_python=LP_PYTHON,document_python=DOCUMENT_PYTHON,
        document_node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'))
    assets={name:dict(path=str(path),SHA256=sha(path),bytes=path.stat().st_size) for name,path in paths.items()}
    assert assets['production']['SHA256']==manifest['production_PE_SHA']
    assert assets['Native_DLL']['SHA256']==manifest['DLL_SHA']==DLL_SHA
    write(OUT/'software_bindings.json',dict(UTC=utc(),assets=assets,Optimize=0,commercial_native_loads=0,
        scope='Closeout byte hashes of installed assets. Production source/PE were checked before full calls and the actual single loaded DLL was bound in LP processes. Interpreter hashes are closeout observations, not retroactively claimed in-process assertions.',
        global_settings_changed=False))

def dependencies():
    require_idle()
    fixed={name:dict(commit=SCIENCE140,SHA=sha(ROOT/name)) for name in [
        'results/unified_exact_round140/reports/full.json',
        'results/unified_exact_round140/carrier_manifest.json',
        'results/unified_exact_round140/baseline_reuse.json',
        'results/unified_exact_round140/inherited_dependencies.json']}
    for name,record in fixed.items():
        assert hashlib.sha256(git('show',SCIENCE140+':'+name)).hexdigest()==record['SHA']
    full=read(OUT/'reports/full.json');roles={r['role'] for r in full['new_arms']}
    old=read(ROOT/'results/unified_exact_round140/inherited_dependencies.json')
    references=[r for r in old['accepted_full_reference_members'] if r['role'] in roles]
    old_manifest=read(ROOT/'results/unified_exact_round140/carrier_manifest.json')
    carriers={r['path']:r for r in old_manifest['carriers']};new140=[]
    for r in full['reused_arms']:
        if r['role'] not in roles or r['method'] not in ['TC_STOCK','TC2_STOCK']:continue
        path=f'results/unified_exact_round140/artifacts/campaign_{r["batch"]}_{r["position"]:03}.zip'
        carrier=carriers[path];assert sha(ROOT/path)==carrier['SHA256']
        with zipfile.ZipFile(ROOT/path) as z:
            raw=z.read(carrier['member_index'])
            assert hashlib.sha256(raw).hexdigest()==carrier['member_index_SHA']
            index=json.loads(raw)
        suffixes=['/identity.json','/round135_endpoint.json','/audit.json','/verification_closeout.json',
            '/round140_control_audit.json','/result.json','/observations.json','/external/paper_optimize_ledger.csv']
        selected={n:f for n,f in index.items() if any(n.endswith(s) for s in suffixes)}
        assert selected and any(n.endswith('/round135_endpoint.json') for n in selected)
        new140.append(dict(role=r['role'],method=r['method'],seed=r.get('seed',0),
            source_commit=r['source_commit'],PE_SHA=r['PE_SHA'],commit=SCIENCE140,
            carrier=carrier,selected_members=selected,metadata='results/unified_exact_round140/reports/full.json'))
    write(OUT/'full_reference_dependencies.json',dict(UTC=utc(),fixed_metadata=fixed,
        accepted_BASE_STOCK_dependencies=references,
        new_R140_references=new140,
        selected_continuous_members=read(OUT/'inherited_dependencies.json'),Optimize=0,
        scope='Accepted fixed references and necessary member identities; no old full-raw recovery or public acceptance repeated.'))

def source_closure(seeds):
    names=set(seeds);todo=[n for n in names if n.endswith('.py')]
    while todo:
        name=todo.pop();path=ROOT/name
        if not path.is_file():continue
        tree=ast.parse(path.read_text(encoding='utf-8-sig'),filename=name)
        for node in ast.walk(tree):
            modules=[]
            if isinstance(node,ast.Import):modules=[alias.name for alias in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module:modules=[node.module]
            for module in modules:
                candidate='scripts/'+module.split('.')[0]+'.py'
                if candidate not in names and (ROOT/candidate).is_file():
                    names.add(candidate);todo.append(candidate)
    return names

def archive():
    require_idle();assert read(OUT/'candidate_decision.json')['study_complete']
    assert read(OUT/'local_semantic_check.json')['PASS'];tick=time.perf_counter();records=[];packed=set()
    for g in groups():
        folder=OUT/g['group'];d=Path(g['launch']['destination'])
        if not d.is_dir():continue
        files=[p for p in folder.rglob('*') if p.is_file()]
        if not files:continue
        records.append(make_zip(folder.relative_to(OUT).as_posix().replace('/','_'),files));packed.add(folder)
    diagnostics=[]
    for name in ['domains','LP','qualification','math','fees','cost_segments']:
        diagnostics.extend(p for p in (OUT/name).rglob('*') if p.is_file())
    # Matrices/identities of superseded positions stay visible, even if no
    # producer entered. Previously packed actual arms are not duplicated.
    for g in groups():
        folder=OUT/g['group']
        if folder not in packed:diagnostics.extend(p for p in folder.rglob('*') if p.is_file())
    for receipt in (OUT/'ordinary_steps').glob('*/receipt.json'):
        diagnostics.extend(p for p in receipt.parent.rglob('*') if p.is_file())
    records.append(make_zip('diagnostics_and_failures',diagnostics))
    manifest=read(OUT/'candidate_manifest.json');helpers={};bindings={}
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(path);bindings[path.name]=matrix.get('helpers',{})
        if matrix.get('batch','').startswith('qualification'):continue
        for name,digest in matrix.get('helpers',{}).items():
            assert sha(ROOT/name)==digest,name
            if name in helpers:assert helpers[name]==digest
            helpers[name]=digest
    seeds=set(manifest['source_hashes'])|set(helpers)|{
        '.gitattributes','CMakeLists.txt','WORKSPACE_POLICY.md',
        'scripts/paper_s2.py','scripts/paper_s2_stock_rlt.py','scripts/paper_s2_stock_placement.py',
        'scripts/paper_s2_tc2.py','scripts/paper_s2_count_disjunction.py',
        'scripts/round126_export.py','scripts/round138_public_read.py',
        'scripts/round138_pdf_qa.py','results/unified_exact_round94/preregistration.json'}
    seeds.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round141*') if p.is_file())
    sources=source_closure(seeds)
    for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest,name
    source=make_zip('source_and_helpers',[ROOT/name for name in sources]);records.append(source)
    inputs={g['launch']['panel']['input_path'] for g in groups()}
    for path in (OUT/'domains').glob('*/scope.json'):
        panel=read(path)['panel'];inputs.add(panel['input_path'])
    configs=['config/gi_tbc_round137.json','config/gi_tbc_stock_rlt_round138.json',
        'config/gi_tbc_stock_placement_round139.json','config/gi_tbc_tc2_round140.json',
        'config/gi_tbc_count_disjunction_round141.json']
    write(OUT/'source_publication.json',dict(UTC=utc(),production_source_commit=manifest['source_commit'],
        production_PE_SHA=manifest['production_PE_SHA'],production_DLL_SHA=manifest['DLL_SHA'],
        actual_source_hashes=manifest['source_hashes'],source_bundle=source,frozen_formal_helpers=helpers,
        all_original_batch_helper_bindings=bindings,current_source_files={name:sha(ROOT/name) for name in sources},
        inputs={name:sha(ROOT/name) for name in inputs},configuration_files={name:sha(ROOT/name) for name in configs},
        historical_references='full_reference_dependencies.json',commercial_assets_published=False,Optimize=0))
    excluded={'carrier_manifest.json','publication_pin.json','public_restore_receipt.json','cleanup_record.json'}
    meta=[p for p in OUT.iterdir() if p.is_file() and p.suffix.lower() in {'.json','.md','.bib','.pdf'} and p.name not in excluded]
    meta.extend(p for name in ['reports','review','figures'] for p in (OUT/name).rglob('*') if p.is_file())
    meta.extend(ROOT/name for name in inputs|set(configs))
    meta.extend(ROOT/name for name in ['docs/round141_research.md','docs/current_mainline.md','docs/unified_exact_research_index.md'])
    records.append(make_zip('science_and_paper',meta))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),carriers=records,source_bundle=source,
        seconds=time.perf_counter()-tick,new_round_only=True,all_entered_adverse_open_and_failures_retained=True,
        Optimize=0,public_scope='Finite anonymous fixed-commit archive/member byte readability; distinct from local science/semantics.'))

if __name__=='__main__':globals()[sys.argv[1]]()
