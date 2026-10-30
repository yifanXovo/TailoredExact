"""Bounded current-round carriers, reuse checks and disjoint cost reporting."""
from round142_common import *
from round142_analyze import require_idle
import round138_delivery as previous
import types,zipfile
configure()

INDEX='__round142_member_index__.json'
BANNED=previous.BANNED
make_zip=types.FunctionType(previous.make_zip.__code__,dict(vars(previous),ROOT=ROOT,OUT=OUT,INDEX=INDEX,sha=sha))

def groups():
    return [g for p in sorted(OUT.glob('*_matrix.json')) for g in read(p).get('groups',[])]

def accounting():
    require_idle();b=budget()
    ordinary=[(p,read(p)) for p in sorted((OUT/'ordinary_steps').glob('*/receipt.json'))]
    fees=[(p.parent.name,read(p)) for p in sorted((OUT/'fees').glob('*/receipt.json'))]
    experiment=[(n,r) for n,r in fees if r['budget_category'] in ['native','diagnostic']]
    outer=sum(r['outer_seconds'] for _,r in experiment)
    assert b['G1_seconds']<=28800 and outer<=28800
    write(OUT/'cost_report.json',dict(UTC=utc(),experiment=b,
        charged_new_experiment_seconds=outer,charged_new_experiment_hours=outer/3600.,
        experimental_outer_including_pure_postverification_seconds=outer,
        conservative_outer_within_28800=True,fee_ordinary_seconds=b['separately_reported_seconds'],
        additional_disjoint_ordinary_seconds=sum(r['seconds'] for _,r in ordinary),
        experimental_fee_receipts=[dict(label=n,receipt=r) for n,r in experiment],
        ordinary_steps=[dict(label=p.parent.name,SHA=sha(p),receipt=r) for p,r in ordinary],
        failed_steps=[n for n,r in fees if r['exit_code']!=0]+[p.parent.name for p,r in ordinary if r['exit_code']!=0],
        qualifiers_and_failures_charged=True,nested_H_LP_MIP_Work_not_added_twice=True,
        old_references_new_Optimize=0,
        charge_scope='Conservative primary round charge is every experimental outer, including mandatory pure postverification. The inherited G1 submeter separately excludes those explicit disjoint verification segments; neither value is added to the other.',
        precision_scope='Measured processes only; offline prepare elapsed is in offline_screen.json. Interactive editing/review/Git has no invented precise process clock. Late delivery I/O/cleanup receipts are additive, outside fixed science carriers.'))
    print(json.dumps(dict(conservative_experiment_seconds=outer,hours=outer/3600.,online_G1_seconds=b['G1_seconds'])))

def local_check():
    require_idle()
    from round135_read import validate_event_lifecycle
    import round108_reader as core
    tick=time.perf_counter();facts=[]
    for g in groups():
        launch=g['launch'];d=Path(launch['destination'])
        if not (d/'verification_closeout.json').exists():continue
        p=launch['panel'];assert sha(ROOT/p['input_path'])==p['input_sha256']
        close=read(d/'verification_closeout.json');audit=read(d/'audit.json')
        endpoint=read(d/'round135_endpoint.json');control=read(d/'round142_control_audit.json')
        assert close['necessary_verification_complete'] and close['evidence_complete'] and audit['passed']
        assert close['audit_SHA']==sha(d/'audit.json') and control['PASS'] and control['chain']['PASS']
        assert endpoint['performance_eligible'] and endpoint['native_proof_qualified']
        assert endpoint['T_cert'] is None if not endpoint['certificate'] else endpoint['T_cert']==endpoint['T_produce']
        receipt=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json')
        assert receipt['native_stopped_no_reentry'] and receipt['producer_seal_SHA']==sha(d/'producer_seal.json')
        for path,digest in seal['required_SHA'].items():assert sha(d/path)==digest
        payloads=[r['payload'] for r in read(d/'observations.json')]
        lifecycle=validate_event_lifecycle(payloads,True)
        models=[]
        for call in (r for r in payloads if r['kind']=='call'):
            path=core.portable(ROOT,call['model_path']);assert sha(path)==call['model_sha256']
            models.append(dict(call=call['call'],SHA=call['model_sha256']))
        physical=core.full_fleet(ROOT,p,read(d/'result.json'))
        assert abs(physical['F']-endpoint['U'])<=1e-7
        facts.append(dict(arm_id=launch['arm_id'],qualification=launch['stage'].startswith('qualification'),
            method=launch['method'],seed=launch['seed'],U=endpoint['U'],L=endpoint['L'],certificate=endpoint['certificate'],
            control_SHA=sha(d/'round142_control_audit.json'),closeout_SHA=sha(d/'verification_closeout.json'),
            models=models,lifecycle=lifecycle))
    assert facts and 'gurobipy' not in sys.modules
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),positions=facts,seconds=time.perf_counter()-tick,
        Optimize=0,Native_load=0,
        scope='Additive seal/physical/lifecycle/hash replay; original complete physical/H/Start/quality/scope/source-floor/Native-row audits are retained separately.'))

def helper_versions():
    """Preserve exact older LP helper bytes rather than retagging old runs."""
    records=[]
    for path in sorted((OUT/'LP').glob('*/result.json')):
        r=read(path)
        for name,key in [('scripts/round142_math.py','math_SHA'),('scripts/round142_lp.py','writer_SHA')]:
            digest=r[key];current=ROOT/name
            if sha(current)==digest:continue
            raw=git('show',r['source_rev']+':'+name)
            transform='identity'
            if hashlib.sha256(raw).hexdigest()!=digest:
                candidate=raw.replace(b'\n',b'\r\n')
                assert b'\r' not in raw and hashlib.sha256(candidate).hexdigest()==digest
                raw=candidate;transform='exact_git_LF_to_registered_local_CRLF'
            target=OUT/'replay_helpers'/digest/Path(name).name
            if target.exists():assert target.read_bytes()==raw
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            records.append(dict(result=path.relative_to(ROOT).as_posix(),source_rev=r['source_rev'],
                original_path=name,saved_path=target.relative_to(ROOT).as_posix(),SHA=digest,transform=transform,
                scope='Exact measured helper; initial tiny-fixture constructor fix did not change product generation'))
    write(OUT/'measured_helper_versions.json',dict(versions=records,Optimize=0))

def software_bindings():
    require_idle()
    import platform
    manifest=read(OUT/'candidate_manifest.json')
    paths=dict(production=Path(manifest['production_PE']),Native_DLL=DLL,
        compiler=Path('D:/msys64/ucrt64/bin/g++.exe'),process_python=PYTHON,
        LP_python=LP_PYTHON,document_python=DOCUMENT_PYTHON,
        document_node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'))
    assets={name:dict(path=str(path),SHA256=sha(path),bytes=path.stat().st_size) for name,path in paths.items()}
    assert assets['production']['SHA256']==manifest['production_PE_SHA'] and assets['Native_DLL']['SHA256']==DLL_SHA
    write(OUT/'software_bindings.json',dict(UTC=utc(),assets=assets,platform=platform.platform(),
        machine=platform.machine(),process_python_version=platform.python_version(),
        user_clock_timezone='Asia/Shanghai',task_date='2026-10-30',closeout_date='2026-10-31',
        affinity_mask=4,Threads=1,Gurobi_Seed=0,H_seed=20260626,Optimize=0,Native_load=0,
        scope='Closeout installed-asset/environment observation. Actual source/PE/DLL, input and complete parameters were separately checked before admitted producers; LP records bind the actual loaded engine. Interpreter hashes are not retroactively claimed in-process assertions.',
        global_settings_changed=False))

def references():
    require_idle();facts=[]
    science140='15e401f794bb53e31c5848e0edabf0b4153ca678'
    for commit,names in [(SCIENCE141,['reports/full.json','carrier_manifest.json','candidate_manifest.json']),
                         (science140,['reports/full.json','baseline_reuse.json'])]:
        number=141 if commit==SCIENCE141 else 140
        for suffix in names:
            name=f'results/unified_exact_round{number}/{suffix}'
            raw=git('show',commit+':'+name);local=ROOT/name
            assert json.loads(raw)==read(local),(commit,name)
            facts.append(dict(commit=commit,path=name,Git_SHA256=hashlib.sha256(raw).hexdigest(),
                local_SHA256=sha(local),complete_JSON_semantics_equal=True,new_Optimize=0))
    full=read(OUT/'reports/full.json');roles={r['role'] for r in full['new_arms']}
    inherited=[r for r in full['reused_arms'] if r['role'] in roles]
    write(OUT/'reference_dependencies.json',dict(UTC=utc(),fixed_metadata=facts,
        selected_accepted_references=inherited,original_source_PE_and_complete_costs_preserved=True,
        old_raw_recovery='No broad replay or restoration. Accepted R141/R140 reference metadata and carrier pins remain authorities; only six actual LP source members are newly carried.',
        Optimize=0,Native_load=0))

def archive():
    require_idle();assert read(OUT/'candidate_decision.json')['study_complete']
    assert read(OUT/'local_semantic_check.json')['PASS']
    tick=time.perf_counter();helper_versions();records=[]
    for g in groups():
        folder=OUT/g['group'];label=folder.relative_to(OUT).as_posix().replace('/','_')
        records.append(make_zip(label,[p for p in folder.rglob('*') if p.is_file()]))
    diagnostics=[p for name in ['LP','qualification/writer','fees','math','cost_segments','replay_helpers','layout_history']
                 for p in (OUT/name).rglob('*') if p.is_file()]
    diagnostics += [p for receipt in (OUT/'ordinary_steps').glob('*/receipt.json') for p in receipt.parent.rglob('*') if p.is_file()]
    records.append(make_zip('diagnostics_and_failures',diagnostics))
    inherited=[]
    for p in read(OUT/'inherited_dependencies.json')['members']:
        path=ROOT/p['path'];assert sha(path)==p['SHA256'];inherited.append(path)
    records.append(make_zip('inherited_selected_sources',inherited))
    manifest=read(OUT/'candidate_manifest.json');sources=set(manifest['source_hashes'])
    for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest
    frozen={}
    for matrix in OUT.glob('*_matrix.json'):
        for name,digest in read(matrix).get('helpers',{}).items():
            assert sha(ROOT/name)==digest,(matrix,name)
            frozen[name]=digest
    sources.update(frozen)
    sources.update(p.relative_to(ROOT).as_posix() for pattern in ['round142*','paper_s2*'] for p in (ROOT/'scripts').glob(pattern) if p.is_file())
    sources.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'config').glob('*.json'))
    sources.update(['CMakeLists.txt','WORKSPACE_POLICY.md','docs/round142_research.md',
        'docs/current_mainline.md','docs/unified_exact_research_index.md',
        'results/unified_exact_round141/candidate_manifest.json','results/unified_exact_round140/candidate_build.json'])
    source=make_zip('source_and_helpers',[ROOT/p for p in sources]);records.append(source)
    write(OUT/'source_publication.json',dict(UTC=utc(),actual_production_source_commit=manifest['source_commit'],
        actual_PE_SHA=manifest['production_PE_SHA'],actual_DLL_SHA=manifest['DLL_SHA'],source_bundle=source,
        actual_source_hashes=manifest['source_hashes'],frozen_helpers=frozen,
        standalone_helpers_and_metadata={n:sha(ROOT/n) for n in sources if n not in frozen and n not in manifest['source_hashes']},
        commercial_assets_published=False,measured_helper_versions=read(OUT/'measured_helper_versions.json'),
        publication_parent=git('rev-parse','HEAD').decode().strip(),Optimize=0))
    meta=[p for p in OUT.iterdir() if p.is_file() and p.suffix in ['.json','.md','.bib','.pdf'] and
          p.name not in ['carrier_manifest.json','public_restore_receipt.json','publication_pin.json','PR_delivery.json','PR_description.md']]
    meta += [p for name in ['reports','review','figures'] for p in (OUT/name).rglob('*') if p.is_file()]
    meta += [ROOT/g['launch']['panel']['input_path'] for g in groups()]
    records.append(make_zip('science_and_paper',meta))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),round=142,carriers=records,source_bundle=source,
        new_round_only=True,inherited_recovery_limited_to_selected_sources=True,
        unique_science_and_failures_retained=True,Optimize=0,seconds=time.perf_counter()-tick,
        public_scope='Finite fixed-commit anonymous archive/member bytes, without Native, build or Optimize'))
    print(json.dumps(dict(archives=len(records),members=sum(r['members'] for r in records),bytes=sum(r['bytes'] for r in records))))

if __name__=='__main__':globals()[sys.argv[1]]()
