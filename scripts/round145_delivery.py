"""Bounded current-round carriers/public bytes/cleanup; no solver imports."""
import ast,fnmatch,gzip,io,re,shutil,zipfile,urllib.request
from round145_common import *
def idle():assert not budget()['unclosed'],'delivery waits for all timed producers'
def files(folder):return [p for p in folder.rglob('*') if p.is_file()] if folder.exists() else []
def local():
    idle();tick=time.perf_counter();m=read(OUT/'candidate_manifest.json');full=read(OUT/'reports/full.json')
    assert sha(m['production_PE'])==m['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for p,h in m['source_hashes'].items():assert sha(ROOT/p)==h,p
    protected=[]
    old_paths=git('ls-tree','-r','--name-only',BASE,'--','config','scripts').decode().splitlines()
    profiles=[p for p in old_paths if fnmatch.fnmatchcase(p,'config/gi_tbc*.json') or fnmatch.fnmatchcase(p,'scripts/paper_s2*.py')]
    profiles += ['results/unified_exact_round137/manuscript.md','results/unified_exact_round137/manuscript.pdf']
    for name in profiles:
        assert not git('diff',BASE,'--',name).strip(),name
        protected.append(dict(path=name,SHA256=sha(ROOT/name),unchanged_from_verified_R144=True))
    original=Path('E:/codes/ExactEBRP')
    original_status=git('status','--porcelain=v1','--untracked-files=no',cwd=original).decode()
    assert original_status==(OUT/'protected_original_tracked_status.txt').read_text(encoding='utf-8')
    assert not git('diff',BASE,'--',*[f'results/unified_exact_round{i}' for i in range(137,145)]).strip()
    assert read(OUT/'reports/LP.json')['PASS']
    assert read(OUT/'qualification_native_writer.json')['PASS'] and read(OUT/'qualification_exact_writer.json')['PASS']
    raw=[];native=0
    for a in full['new_arms']+full['qualification']:
        d=Path(a['destination']);v=read(d/'verification_closeout.json');assert v['native_proof_qualified'] and v['performance_eligible']
        assert a['declared_calls']==a['returned_calls'];native+=a['returned_calls']
        for p,h in read(d/'producer_seal.json')['required_SHA'].items():assert sha(d/p)==h,p
        raw.append(dict(arm_id=read(d/'round135_endpoint.json')['arm_id'],endpoint_SHA=sha(d/'round135_endpoint.json'),closeout_SHA=sha(d/'verification_closeout.json')))
    assert not full['pending'];assert read(OUT/'candidate_decision.json')['study_complete']
    assert read(OUT/'review/final_scientific_review.json')['PASS'] and read(OUT/'pdf_visual_review.json')['PASS']
    assert sha(OUT/'manuscript.pdf')==read(OUT/'pdf_render_manifest.json')['PDF_SHA']
    assert read(OUT/'PDF_marker.json')['successful_invocations']==1
    assert 'gurobipy' not in sys.modules and budget()['G1_seconds']<=28800
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),source_PE_binding=True,protected_entries_profiles=protected,
        qualified_native_Optimize=native,standalone_LP_Optimize=11,raw=raw,failed_qualification_count=len(full['failed_qualifications']),
        all_entered_retained=True,all_qualified_calls_returned=True,protected_original_tracked_status_unchanged=True,
        old_round_137_through_144_results_unchanged=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick))
def pack():
    idle();tick=time.perf_counter();archives=[]
    def archive(name,paths):
        target=OUT/'artifacts'/name;target.parent.mkdir(parents=True,exist_ok=True);members=[]
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(set(paths)):
                assert p.is_file() and ROOT.resolve() in p.resolve().parents
                assert p.suffix.lower() not in {'.exe','.dll','.lib','.a','.o','.obj','.lic'},p
                data=p.read_bytes();member=p.relative_to(ROOT).as_posix();z.writestr(member,data)
                members.append(dict(member=member,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        archives.append(dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,members=members))
    diagnostics=[]
    for folder in ['LP','compact','math','ordinary_steps','qualification','engineering','failures']:
        # Completed own-H qualifiers are packed below as whole groups.
        if folder=='qualification':diagnostics+=files(OUT/'qualification/project')+files(OUT/'qualification/blocks')+files(OUT/'qualification/writer')+[OUT/'qualification/K35_row.txt']
        else:diagnostics+=files(OUT/folder)
    for fee in (OUT/'fees').iterdir():
        if not fee.name.startswith(('pilot_','resource_','bridge_','extension_','confirmation_','qualification')):diagnostics+=files(fee)
    archive('diagnostics_and_failures.zip',diagnostics)
    qualifiers=[];sources=[ROOT/p for p in read(OUT/'candidate_manifest.json')['source_hashes']]
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(path)
        if 'batch' not in matrix:continue
        sources += [ROOT/p for p in matrix.get('helpers',{})]
        for g in matrix['groups']:
            p=g['launch']['panel'];sources += [ROOT/p[k] for k in ['input_path','selection_path','landscape_path'] if p.get(k)]
            complete=files(OUT/g['group'])+files(OUT/'fees'/f'{matrix["batch"]}_{g["position"]:03}')
            if matrix['batch'].startswith('qualification'):qualifiers+=complete
            elif (Path(g['launch']['destination'])/'verification_closeout.json').exists():archive(f'campaign_{matrix["batch"]}_{g["position"]:03}.zip',complete)
    for fee in (OUT/'fees').iterdir():
        if fee.name.startswith('qualification') and 'reader_recovery' in fee.name:qualifiers+=files(fee)
    archive('qualifications_and_failures.zip',qualifiers)
    # Only files actually consumed by the current diagnostic stage, not an old panel.
    deps=[]
    for role in ['K-35-U','R-X20-S-T1']:
        old=ROOT/'results/unified_exact_round144/LP'/f'{role}_base'
        deps += [old/name for name in ['base.mps','source.mps','source_scope.json','source_solution.json.gz','result.json']]
    old=ROOT/'results/unified_exact_round144/campaign_resource_k20/002/raw/R144_resource_k20_002_K-20-S_S0_RNP/external'
    deps += [old/'models/round144_RN_source.lp',old/'round144_source.json',old/'round144_projection.json']
    # The four zero-Optimize NC-PC reconstructions use production points,
    # whose degenerate optimal extensions need not equal the saved LP points.
    for batch,position in [('pilot',2),('pilot',4),('resource_k20',2),('resource',2)]:
        folder=ROOT/'results/unified_exact_round144'/('campaign_'+batch)/f'{position:03}'
        identity=read(folder/'identity.json');raw=Path(identity['launches'][0]['destination'])/'external'
        deps += [folder/'identity.json',raw/'models/round144_RN_source.lp',raw/'round144_source.json',raw/'round144_projection.json']
    for role in ['K-35-U','K-20-S','R-X20-S-T1']:
        deps += [ROOT/'results/unified_exact_round143/inherited/roots'/role/'scope.json']
    deps += [ROOT/'results/unified_exact_round143/inherited/roots/K-35-U/inherited/original.lp']
    for roundno in [137,138,139,140,141,142,143,144]:
        path=ROOT/f'results/unified_exact_round{roundno}/final_report.md'
        if path.exists():deps.append(path)
    deps += [ROOT/'results/unified_exact_round137/matrix_frozen.json',ROOT/'results/unified_exact_round144/candidate_manifest.json']
    archive('finite_inherited_inputs.zip',deps)
    sources += list((ROOT/'scripts').glob('round145_*'))+[ROOT/'scripts/paper_s2_rnjp.py',ROOT/'config/gi_tbc_rnjp_round145.json',ROOT/'CMakeLists.txt',ROOT/'WORKSPACE_POLICY.md']
    sources += [ROOT/p for p in ['config/gi_tbc_round137.json','config/gi_tbc_rn_round143.json','scripts/paper_s2.py','scripts/paper_s2_rn.py']]
    # Include local authoring/offline dependencies too, without importing any
    # module or loading a solver. Measured noncurrent versions remain separate.
    pending=[p for p in sources if p.suffix=='.py'];seen=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path);tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:modules.append(node.module)
        for module in modules:
            dependency=ROOT/'scripts'/(module.split('.')[0]+'.py')
            if dependency.is_file() and dependency not in seen:sources.append(dependency);pending.append(dependency)
    archive('source_and_helpers.zip',[p for p in sources if p.is_file()])
    excluded={'carrier_manifest.json','archive_local_check.json','publication_pin.json','public_restore_owner.json','public_attempt_history.json','public_restore_receipt.json',
        'cleanup_record.json','PR_delivery.json','PR_readback.json','PR_description.md','delivery_costs.json'}
    science=[p for p in OUT.iterdir() if p.is_file() and p.name not in excluded]+files(OUT/'reports')+files(OUT/'review')+files(OUT/'figures')+files(OUT/'qa_pages')
    archive('science_and_paper.zip',science)
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=archives,archive_count=len(archives),indexed_members=sum(len(a['members']) for a in archives),
        compressed_bytes=sum(a['bytes'] for a in archives),Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,commercial_binaries_or_licenses_published=False))
    compact()
def compact():
    """Keep the complete member index compressed; scientific archives stay intact."""
    idle();tick=time.perf_counter();path=OUT/'carrier_manifest.json';manifest=read(path)
    if 'member_index' in manifest:
        print('External compressed member index already present');return
    history=TEMP/'pack_history/initial_full_index';history.mkdir(parents=True,exist_ok=True)
    if not (history/'carrier_manifest.json').exists():shutil.copyfile(path,history/'carrier_manifest.json')
    # A delivery-format revision must also be present in its source carrier.
    source=next(a for a in manifest['archives'] if a['path'].endswith('/source_and_helpers.zip'))
    if any(sha(ROOT/m['member'])!=m['SHA256'] for m in source['members']):
        target=ROOT/source['path']
        if not (history/target.name).exists():shutil.copyfile(target,history/target.name)
        members=[]
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for old in source['members']:
                data=(ROOT/old['member']).read_bytes();z.writestr(old['member'],data)
                members.append(dict(member=old['member'],SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        source.update(SHA256=sha(target),bytes=target.stat().st_size,members=members)
    index={a['path']:a['members'] for a in manifest['archives']}
    raw=json.dumps(index,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    target=OUT/'artifacts/member_index.json.gz';target.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
    archives=[{**{k:v for k,v in a.items() if k!='members'},'member_count':len(a['members'])} for a in manifest['archives']]
    write(path,dict(manifest,schema='round145-carriers-external-member-index-v2',archives=archives,
        member_index=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,format='gzip-compressed UTF-8 JSON keyed by archive path'),
        compressed_bytes=sum(a['bytes'] for a in archives)+target.stat().st_size,
        metadata_compaction_seconds=time.perf_counter()-tick,scientific_raw_and_paper_archives_unchanged=True))
    print(json.dumps(dict(archives=len(archives),members=manifest['indexed_members'],total_bytes=sum(a['bytes'] for a in archives)+target.stat().st_size,
        member_index_bytes=target.stat().st_size,manifest_bytes=path.stat().st_size,Optimize=0,Native_load=0)))
def public(commit):
    idle();assert re.fullmatch('[0-9a-f]{40}',commit)
    history_path=OUT/'public_attempt_history.json';history=read(history_path) if history_path.exists() else []
    spent=sum(r['seconds'] for r in history);assert spent<1800;tick=time.perf_counter();records=[]
    target=WORK/'restore'/f'round145-public-{commit[:12]}-attempt{len(history)+1:02}';assert WORK.resolve() in target.resolve().parents
    target.mkdir(parents=True,exist_ok=False);manifest=read(OUT/'carrier_manifest.json');member_index=None;index_record=None
    write(OUT/'public_restore_owner.json',dict(UTC=utc(),directory=str(target),fixed_commit=commit,scope='Current-round carriers only; finite public byte/member verification'))
    manifest_url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/results/unified_exact_round145/carrier_manifest.json'
    try:
        with urllib.request.urlopen(urllib.request.Request(manifest_url,headers={'User-Agent':'Round145-finite-public-recovery'}),timeout=30) as response:remote=response.read()
        assert hashlib.sha256(remote).hexdigest()==sha(OUT/'carrier_manifest.json') and json.loads(remote)==manifest
        (target/'carrier_manifest.json').write_bytes(remote)
        if 'member_index' in manifest:
            item=manifest['member_index'];url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/{item["path"]}'
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Round145-finite-public-recovery'}),timeout=120) as response:data=response.read()
            assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['SHA256']
            member_index=json.loads(gzip.decompress(data));assert set(member_index)=={a['path'] for a in manifest['archives']}
            assert sum(len(v) for v in member_index.values())==manifest['indexed_members']
            (target/Path(item['path']).name).write_bytes(data)
            index_record=dict(url=url,SHA256=item['SHA256'],bytes=len(data),members=manifest['indexed_members'],anonymous=True)
        for a in manifest['archives']:
            assert spent+time.perf_counter()-tick<1800
            url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/{a["path"]}'
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Round145-finite-public-recovery'}),timeout=120) as response:data=response.read()
            assert len(data)==a['bytes'] and hashlib.sha256(data).hexdigest()==a['SHA256']
            members=member_index[a['path']] if member_index is not None else a['members']
            assert len(members)==a.get('member_count',len(members))
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                assert sorted(z.namelist())==sorted(m['member'] for m in members)
                for m in members:
                    value=z.read(m['member']);assert len(value)==m['bytes'] and hashlib.sha256(value).hexdigest()==m['SHA256']
            (target/Path(a['path']).name).write_bytes(data)
            records.append(dict(url=url,path=a['path'],SHA256=a['SHA256'],bytes=len(data),members_checked=len(members),anonymous=True))
        receipt=dict(PASS=True,UTC=utc(),fixed_commit=commit,archives=records,seconds=time.perf_counter()-tick,manifest_url=manifest_url,
            manifest_SHA256=sha(OUT/'carrier_manifest.json'),member_index=index_record,Optimize=0,Native_load=0,compile=0,only_public_bytes_and_members=True,credentials_used=False)
    except BaseException as error:
        receipt=dict(PASS=False,UTC=utc(),fixed_commit=commit,archives=records,seconds=time.perf_counter()-tick,error=repr(error),Optimize=0,Native_load=0,compile=0,settings_changed=False)
        history.append(receipt);write(history_path,history);write(OUT/'public_restore_receipt.json',dict(receipt,cumulative_seconds=spent+receipt['seconds']));raise
    history.append(receipt);write(history_path,history);write(OUT/'public_restore_receipt.json',dict(receipt,cumulative_seconds=spent+receipt['seconds']))
    print(json.dumps(dict(PASS=True,archives=len(records),seconds=receipt['seconds'])))
def prbody(commit):
    idle();assert re.fullmatch('[0-9a-f]{40}',commit)
    m=read(OUT/'candidate_manifest.json');c=read(OUT/'cost_report.json');f=read(OUT/'reports/full.json')
    url=f'https://github.com/yifanXovo/TailoredExact/blob/{commit}/results/unified_exact_round145'
    body=f'''Integer count chords and physical stock budgets do not automatically constrain the same reciprocal products in RN. This adds a separate default-off RN-JP research switch: pay once after the run's own H/initial root for BASE+RN+two homogenized NC rows+four reciprocal-stock TS rows, project every added source row, restore/discard the source, and rebuild formal BASE with one original-variable row and zero RN columns. TS may retain original Y coefficients. Existing proof, Start and compatible-scope policies remain in force; all source computation is charged.

The finite stage uses **11 new standalone LP optimizations**, with sealed RN baselines reused without reoptimization. On K35, joint objective .234508197894 exceeds strong RN+stock+TC+TC2 .229222197461 by .005286000433; O+joint matches joint numerically. Actual compiled/transported compact LP losses are 2.75e-14 and 1.73e-14 on K35/RX20. An all-n fixed-selector family proves strict complementarity while exhibiting a remaining integer-objective epigraph gap. Four ideal exact NC-PC saved-point separations are independently reconstructed with zero Optimize, without feeding historical cuts to fresh runs.

Complete evidence is **four same-PE Seed0 OFF/RN-JP pairs plus one K35 same-PE old RN-P bridge**, all with complete own H and mandatory verification. K35 RN-JP improves U by 1.900825% versus OFF, but supported L falls and relative gap increases by .971762 percentage points. K20 has the same U and weaker L with no certificate; RX20 certifies the same objective with no material time benefit. RB35 U worsens from .344642626 to .383702515 despite a small L increase. The old compact RN-P bridge gives K35 U/L=.660923637174/.550645816146, both better than RN-JP .679684412741/.541069698488. Every adverse endpoint remains.

Decision: **retain research and stop this once-root joint-expression trial; no stable promotion or automatic further grid**. The mathematical and representation results remain useful. The unified stage account retains earlier STOCK certificate gains and RN-P K35 gains, and the supplied R144 no-PC matching-prefix finding with its original negative endpoint. Root-value preservation is attributed to standard LP duality/R104, and NC/TS to standard count/RLT tools; no whole-tree equality or global historical dominance is claimed.

All {f['all_entered_observed_Native_Optimize']} complete/qualification Native calls returned; the 11 standalone LP calls are separate. Exact fixtures, compiled source/writer oracle checks, actual Native readback, one short complete health test, full physical/proof/lifecycle verification, independent final scientific review and actual eight-page PDF visual review pass. New experimental outer cost is **{c['charged_new_experiment_seconds']:.9f} seconds ({c['charged_new_experiment_seconds']/3600:.6f} hours)** of 28800, including source, qualification and postverification without nested double count. No route-A panel, extra Seed/floor or optional-role grid is entered.

Fixed science `{commit}`:

- [Scientific report]({url}/final_report.md), [decision]({url}/candidate_decision.json) and [stage account]({url}/stage_evidence.md)
- [Integrated paper section]({url}/manuscript.pdf) and [mathematical analysis]({url}/mathematical_analysis.md)
- [Full matched results]({url}/reports/full.json), [LP information]({url}/reports/LP.json) and [K35 compact bridge]({url}/reports/same_PE_RNP_bridges.csv)
- [Independent final review]({url}/review/final_scientific_review.json), [finite carrier manifest]({url}/carrier_manifest.json) and [source/PE lineage]({url}/candidate_manifest.json)

Measured production source remains `{m['source_commit']}`; PE SHA256 is `{m['production_PE_SHA']}`. It is distinct from science and delivery commits. Stable R137 and all earlier entries/profiles are preserved. Main has not absorbed R144, so the verified unmerged R144 branch (#206) is the temporary base. This PR remains Draft. Anonymous current-carrier public byte/member acceptance and bounded post-PR current-round cleanup are recorded in the later delivery metadata; neither triggers Optimize, compilation or commercial Native loading.
'''
    (OUT/'PR_description.md').write_text(body,encoding='utf-8',newline='\n')
    print(str(OUT/'PR_description.md'))

def cleanup():
    idle();assert read(OUT/'public_restore_receipt.json')['PASS'] and read(OUT/'PR_readback.json')['draft']
    before=shutil.disk_usage(WORK).free;roots=[WORK/'build-cache/round145',WORK/'temp/round145',OUT]
    for i,attempt in enumerate(read(OUT/'public_attempt_history.json'),1):
        assert re.fullmatch('[0-9a-f]{40}',attempt['fixed_commit'])
        roots.append(WORK/'restore'/f'round145-public-{attempt["fixed_commit"][:12]}-attempt{i:02}')
    retained=[]
    for root in roots:
        assert WORK.resolve() in root.resolve().parents
        paths=files(root);retained.append(dict(path=str(root),files=len(paths),logical_bytes=sum(p.stat().st_size for p in paths),
            reason='Current-round raw/failures, source/writer lineage, required PE/objects, rendered evidence and active tree retained'))
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),deleted_paths=[],deleted_logical_bytes=0,retained=retained,free_bytes_before=before,free_bytes_after=after,
        observed_volume_delta=after-before,volume_delta_not_attributed_to_deletion=True,bounded_current_round_only=True,old_rounds_deleted=False,
        original_user_tree_modified=False,zero_deletion_reason='Unique failures/raw and verified runtime/build lineage retained; zero deletion is explicitly allowed by the goal',
        public_acceptance_SHA=sha(OUT/'public_restore_receipt.json'),PR_readback_SHA=sha(OUT/'PR_readback.json')))
    print('Bounded current-round cleanup: zero deletion; evidence/runtime/active tree retained')
if __name__=='__main__':
    if sys.argv[1]=='public':public(sys.argv[2])
    elif sys.argv[1]=='prbody':prbody(sys.argv[2])
    else:globals()[sys.argv[1]]()
