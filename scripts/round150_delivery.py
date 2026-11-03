"""Bounded current-round carriers, public byte recovery and zero-deletion closeout."""
import gzip
import io
import re
import shutil
import zipfile
from round150_common import *


def files(root):
    return [p for p in root.rglob('*') if p.is_file()] if root.exists() else []


def idle(allow_current=False):
    configure()
    current = os.environ.get('ROUND140_METERED_PARENT_LABEL') if allow_current else None
    assert all(v['label']==current for v in budget()['unclosed'])


def local():
    idle(True)
    full = read(OUT/'reports/full.json')
    assert not full['pending'] and len(full['formal_arms'])==4
    assert full['complete_Native_Optimize']==full['complete_Native_returned']
    assert full['diagnostic_LP_Optimize']==full['diagnostic_LP_returned']==3
    manifest = read(OUT/'candidate_manifest.json')
    assert sha(manifest['production_PE'])==manifest['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for p,h in manifest['source_hashes'].items():
        assert sha(ROOT/p)==h,p
    start = read(OUT/'start_receipt.json')
    for p,h in start['protected_entry_bytes'].items():
        assert sha(ROOT/p)==h,p
    assert not git('diff',BASE,'--','src','include','config','scripts/paper_s2.py','scripts/paper_s2_gd_only.py').strip()
    assert not git('diff',BASE,'--',*[f'results/unified_exact_round{i}' for i in range(137,150)]).strip()
    original = Path('E:/codes/ExactEBRP')
    assert git('status','--porcelain=v1','--untracked-files=no',cwd=original).decode()==start['protected_original_status']
    for p,h in start['protected_modified_file_hashes'].items():
        assert sha(original/p)==h,p
    for r in full['formal_arms']:
        d = Path(r['destination'])
        assert read(d/'round147_control_audit.json')['PASS']
        assert read(d/'round149_control_audit.json')['PASS']
        assert read(d/'round149_control_audit.json')['enabled'] is False
        for p,h in read(d/'producer_seal.json')['required_SHA'].items():
            assert sha(d/p)==h,p
    for r in read(OUT/'reports/LP.json')['domains']:
        d = OUT/'LP'/f'{r["role"]}_CPF'
        assert sha(d/'model.mps')==r['model_SHA'] and sha(d/'solution.json.gz')==r['solution_SHA']
        assert sha(d/'dual.json.gz')==r['dual_SHA'] and (d/'return.json').exists()
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),all_entered_preserved=True,
        complete_calls_all_returned=True,source_PE_DLL_identity=True,all_producer_seals=True,
        old_source_profiles_entries_and_results_unchanged=True,original_user_bytes_unchanged=True,
        Optimize=0,Native_load=0,compile=0))
    print('PASS: identities, old/user bytes, actual calls and producer seals')


def pack():
    idle()
    assert read(OUT/'local_semantic_check.json')['PASS']
    assert read(OUT/'review/final_scientific_review.json')['PASS']
    tick = time.perf_counter()
    archives, index = [], {}
    def archive(name, paths):
        target = OUT/'artifacts'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.exists()
        members = []
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
            for p in sorted(set(paths)):
                assert p.resolve().is_relative_to(ROOT.resolve())
                assert p.suffix.lower() not in {'.exe','.dll','.lic','.o','.obj','.a','.lib','.pyc'}
                name = p.relative_to(ROOT).as_posix()
                data = p.read_bytes()
                zipped.writestr(name,data)
                members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        assert target.stat().st_size<100_000_000, 'Use a deterministic split; do not discard evidence'
        relative = target.relative_to(ROOT).as_posix()
        index[relative] = members
        archives.append(dict(path=relative,SHA256=sha(target),bytes=target.stat().st_size,member_count=len(members)))
    labels = set()
    for g in read(OUT/'confirmation_matrix.json')['groups']:
        label = f'confirmation_{g["position"]:03}'
        labels.add(label)
        archive('campaign_'+label+'.zip',files(OUT/g['group'])+files(OUT/'fees'/label))
    diagnostic = files(OUT/'LP')+files(OUT/'infra')
    diagnostic += [p for folder in (OUT/'fees').iterdir() if folder.name not in labels for p in files(folder)]
    archive('CPF_diagnostics_and_fees.zip',diagnostic)
    source = list((ROOT/'scripts').glob('round150*.py'))+[ROOT/'.gitattributes',ROOT/'docs/round150_research.md',
        ROOT/'docs/current_mainline.md',ROOT/'docs/unified_exact_research_index.md']
    archive('new_helpers.zip',source)
    excluded = {'carrier_manifest.json','publication_pin.json','PR_delivery.json','PR_readback.json','PR_description.md',
        'public_restore_receipt.json','public_attempt_history.json','cleanup_record.json','public_restore_owner.json',
        'delivery_costs.json','delivery_snapshot.json'}
    science = [p for p in OUT.iterdir() if p.is_file() and p.name not in excluded]
    science += files(OUT/'reports')+files(OUT/'review')
    archive('science_and_paper.zip',science)
    target = OUT/'artifacts/member_index.json.gz'
    target.write_bytes(gzip.compress(json.dumps(index,separators=(',',':'),ensure_ascii=False).encode(),compresslevel=6,mtime=0))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),schema='round150-incremental-carriers-v1',
        archives=archives,archive_count=len(archives),indexed_members=sum(len(v) for v in index.values()),
        compressed_bytes=sum(a['bytes'] for a in archives)+target.stat().st_size,
        member_index=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size),
        inherited_fixed_science=SCIENCE149,inherited_members='reuse_index.json',
        old_large_history_duplicated=False,commercial_binaries_or_licenses_published=False,
        Optimize=0,Native_load=0,compile=0,seconds=time.perf_counter()-tick))
    print(json.dumps(dict(archives=len(archives),members=sum(len(v) for v in index.values()),seconds=time.perf_counter()-tick)))


def public(commit):
    idle()
    assert re.fullmatch('[0-9a-f]{40}',commit)
    history_path = OUT/'public_attempt_history.json'
    history = read(history_path) if history_path.exists() else []
    spent = sum(r['seconds'] for r in history)
    assert spent<1800
    tick = time.perf_counter()
    target = WORK/'restore'/f'round150-public-{commit[:12]}-attempt{len(history)+1:02}'
    assert target.resolve().is_relative_to((WORK/'restore').resolve())
    target.mkdir(parents=True,exist_ok=False)
    write(OUT/'public_restore_owner.json',dict(directory=str(target),fixed_commit=commit,UTC=utc()))
    def fetch(relative,ref=commit):
        assert spent+time.perf_counter()-tick<1800
        relative = relative.replace('\\','/')
        url = f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{ref}/{relative}'
        destination = target/(ref[:12]+'_'+Path(relative).name)
        run = subprocess.run(['C:/Windows/System32/curl.exe','--disable','--fail','--silent','--show-error',
            '--location','--max-time','90','--proto','=https','--proto-redir','=https','--output',str(destination),
            '--url',url],capture_output=True,timeout=100)
        assert run.returncode==0,run.stderr.decode(errors='replace')
        return destination.read_bytes(),url
    records = []
    try:
        raw,_ = fetch('results/unified_exact_round150/carrier_manifest.json')
        assert hashlib.sha256(raw).hexdigest()==sha(OUT/'carrier_manifest.json')
        manifest = json.loads(raw)
        raw,_ = fetch(manifest['member_index']['path'])
        assert hashlib.sha256(raw).hexdigest()==manifest['member_index']['SHA256']
        index = json.loads(gzip.decompress(raw))
        assert set(index)=={a['path'] for a in manifest['archives']}
        for a in manifest['archives']:
            raw,url = fetch(a['path'])
            assert len(raw)==a['bytes'] and hashlib.sha256(raw).hexdigest()==a['SHA256']
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                members = index[a['path']]
                assert sorted(z.namelist())==sorted(x['member'] for x in members)
                for item in members:
                    data = z.read(item['member'])
                    assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['SHA256']
            records.append(dict(path=a['path'],url=url,SHA256=a['SHA256'],members_checked=len(members)))
        reuse = read(OUT/'reuse_index.json')
        raw,oldurl = fetch(reuse['archive'],SCIENCE149)
        assert hashlib.sha256(raw).hexdigest()==reuse['archive_SHA']
        oldmembers = {x['path']:x['SHA256'] for d in reuse['domains'] for x in d['files']}
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for member,digest in oldmembers.items():
                assert hashlib.sha256(z.read(member)).hexdigest()==digest
        for item in reuse['inputs']:
            raw,_ = fetch(item['path'],SCIENCE137)
            assert hashlib.sha256(raw).hexdigest()==item['SHA256']
        receipt = dict(PASS=True,UTC=utc(),fixed_commit=commit,archives=records,
            new_members_checked=sum(r['members_checked'] for r in records),
            inherited_archive_url=oldurl,inherited_members_checked=len(oldmembers),old_inputs_checked=2,
            seconds=time.perf_counter()-tick,credentials_used=False,TLS_verification_enabled=True,
            transport='Windows curl/Schannel; curlrc disabled; HTTPS only; default certificate verification',
            Optimize=0,Native_load=0,compile=0,only_public_bytes_and_members=True)
    except BaseException as error:
        receipt = dict(PASS=False,UTC=utc(),fixed_commit=commit,archives=records,
            seconds=time.perf_counter()-tick,error=repr(error),Optimize=0,Native_load=0,compile=0)
        history.append(receipt)
        write(history_path,history)
        write(OUT/'public_restore_receipt.json',receipt)
        raise
    history.append(receipt)
    write(history_path,history)
    write(OUT/'public_restore_receipt.json',dict(receipt,cumulative_seconds=spent+receipt['seconds']))
    print(json.dumps(dict(PASS=True,archives=len(records),members=receipt['new_members_checked'],seconds=receipt['seconds'])))


def cleanup():
    idle()
    assert read(OUT/'public_restore_receipt.json')['PASS'] and read(OUT/'PR_readback.json')['draft']
    tick = time.perf_counter()
    before = shutil.disk_usage(WORK).free
    roots = [OUT,TEMP,WORK/'temp/round150-review',Path(read(OUT/'public_restore_owner.json')['directory'])]
    retained = []
    for root in roots:
        assert root.resolve().is_relative_to(WORK.resolve())
        paths = files(root)
        retained.append(dict(path=str(root),files=len(paths),logical_bytes=sum(p.stat().st_size for p in paths),
            reason='Unique raw/failures, active science, independent review or bounded verified public restore'))
    manifest = read(OUT/'candidate_manifest.json')
    runtime = [Path(manifest['production_PE']),DLL,
        Path(read(ROOT/'results/unified_exact_round146/rows_driver.json')['PE'])]
    after = shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),deleted_paths=[],deleted_logical_bytes=0,
        retained=retained,retained_runtime_files=[dict(path=str(p),bytes=p.stat().st_size,SHA256=sha(p)) for p in runtime],
        free_bytes_before=before,free_bytes_after=after,observed_volume_delta=after-before,
        volume_delta_not_attributed_to_deletion=True,bounded_current_round_only=True,
        old_rounds_deleted=False,original_user_tree_modified=False,
        zero_deletion_reason='Goal I permits zero deletion; retain unique evidence, required runtimes and active tree',
        public_acceptance_SHA=sha(OUT/'public_restore_receipt.json'),PR_readback_SHA=sha(OUT/'PR_readback.json'),
        seconds=time.perf_counter()-tick))
    print('Bounded closeout complete: zero deletion')


def pr_body(commit):
    idle()
    assert re.fullmatch('[0-9a-f]{40}',commit)
    full = read(OUT/'reports/full.json')
    cost = read(OUT/'cost_report.json')
    main_sha = git('rev-parse','origin/main').decode().strip()
    absorbed = subprocess.run(['git','merge-base','--is-ancestor',BASE,'origin/main'],cwd=ROOT).returncode==0
    base = 'main' if absorbed else 'codex/round149-penalty-product-feedback'
    science = f'https://github.com/yifanXovo/TailoredExact/blob/{commit}/results/unified_exact_round150/'
    lines = ['This confirms standalone GD on two known/exposed R137 configurations outside GD selection '
        'and screens fixed-dual conditional penalty feedback (CPF) after uniform PF. '
        'The original physical inputs, lambda=.15, horizons and paired windows are frozen before '
        'new D results. All four complete arms pay independent own H and use the same reused '
        'R149 executable, Seed0/Threads1 and H seed20260626. Production C++, PE, stable entries '
        'and profiles are unchanged.','',
        '| Role | Arm | Physical U | Supported L | Gap % | T_cert (s) | T_total (s) |',
        '|---|---|---:|---:|---:|---:|---:|']
    for r in full['formal_arms']:
        cert = 'open' if r['T_cert'] is None else f"{r['T_cert']:.3f}"
        lines.append(f"| {r['role']} | {r['method']} | {r['U']:.12f} | {r['L']:.12f} | "
            f"{100*r['relative_gap']:.6f} | {cert} | {r['T_total']:.3f} |")
    lines += ['', 'D retains the N-C20-U positive-objective certificate and final U, but T_cert is '
        '43.73383% longer. On N-B35-S it improves L 0.16464%, loses U 2.24371%, and enlarges '
        'signed gap 15.46345%; both remain open. The severe double-open reference is not '
        'triggered and is not the adoption rule. Decision: retain a **limited uniform paper '
        'candidate with restricted claims**, preserving the selected R147 hard-role gains '
        'without broadening a replacement/robustness claim. Stable GI-TBC remains primary. '
        'No role-based dispatch or open-cap speedup is introduced.','',
        'Three complete saved PF models gain after appending CPF: K20 +0.000783001403129, '
        'K35 +0.000498396263243 and RX20 +0.001120777978353. Every old semantic item is '
        'retained and every variable is free. Exact Fraction leave-one-out arithmetic reuses '
        'the actual saved binary64 dual; penalty is rounded down and beta up. Independent '
        'MPS parsing and Native readback agree on 451/902, 539/1078 and 143/286 rows/NZ. '
        'New numerical primal-dual gaps are below 1.2e-15. The old K35 PF gap of about '
        '0.000619046 remains disclosed; the new numerical dual exceeds the old saved primal. '
        'These are floating LP qualifications, not exact rational optima. CPF earns future '
        'complete-cost evaluation only; no production CPF or full CPF run follows.','',
        f"All {full['complete_Native_Optimize']} actual complete-arm Native calls returned, plus three "
        'separate CPF LP calls. There is no repeated baseline, fourth domain, extra quality '
        'Optimize, clarification pair, seed grid or new build. '
        f"Charged experimental outer cost is **{cost['charged_new_experiment_seconds']:.9f}s / 14400s**, "
        'including own H, construction and necessary qualification/validation once. Nested '
        'Runtime/Work and old fees are not added. Pure authoring/public I/O are separate.','',
        f"Fixed science: `{commit}`.",'',
        f"- [Complete report]({science}final_report.md), [decisions]({science}candidate_decision.json), "
        f"[endpoints and trajectories]({science}reports/full.json)",
        f"- [Mathematics]({science}mathematical_analysis.md), [matched LPs]({science}LP_report.md), "
        f"[paper section and evidence table]({science}manuscript.tex)",
        f"- [Independent final review]({science}review/final_scientific_review.json), "
        f"[costs]({science}cost_report.json), [carriers]({science}carrier_manifest.json)",
        '- [Actual delivery record](https://github.com/yifanXovo/TailoredExact/blob/'
        'codex/round150-gd-confirmation-conditional-feedback/results/unified_exact_round150/RESUME.md)','',
        'Production source380a85f866bffb914036190f8ee2700ce8b55978 and PE SHA256 '
        '373efa9a596aaf02fb332685515fcfe88df1b169cbe53b295ab6027140620295 are distinct '
        'from the R150 wrapper, fixed design, science and delivery identities. Historical '
        'strong/negative results and the R149 incumbent gains remain visible. '
        f'The verified PR base is `{base}`. This is an English Draft PR with no automatic '
        'merge or default replacement. New assets stay in ExactEBRP-work; original user '
        'changes and old evidence are protected. Finite public byte/member recovery and '
        'bounded current-round cleanup are recorded in the delivery record.','']
    (OUT/'PR_description.md').write_text('\n'.join(lines),encoding='utf-8')
    write(OUT/'publication_pin.json',dict(UTC=utc(),fixed_science_commit=commit,
        original_delivery_base=BASE,actual_PR_base=base,actual_main=main_sha,main_contains_R149=absorbed,
        production_source=SOURCE,PE_SHA=read(OUT/'candidate_manifest.json')['production_PE_SHA'],
        executed_wrapper=read(OUT/'execution_identity.json')['executed_wrapper_commit'],
        frozen_design=read(OUT/'execution_identity.json')['frozen_design_commit'],
        delivery_head='Actual subsequent PR readback; not production source',all_identities_separate=True))
    print(json.dumps(dict(fixed_science=commit,PR_base=base,main=main_sha)))


if __name__=='__main__':
    if sys.argv[1]=='public': public(sys.argv[2])
    elif sys.argv[1]=='pr_body': pr_body(sys.argv[2])
    elif sys.argv[1]=='meter_local':
        configure()
        assert metered('local_semantic_check','diagnostic',[PYTHON,'-B',__file__,'local'],180,300)==0
    else: globals()[sys.argv[1]]()
