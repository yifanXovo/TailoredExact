"""Bounded current-round publication and byte/member recovery; no Native imports."""
import ast,fnmatch,gzip,inspect,io,re,shutil,types,zipfile
from round146_common import *
def idle():assert not budget()['unclosed'],'Delivery waits for all timed experiments'
def files(folder):return [p for p in folder.rglob('*') if p.is_file()] if folder.exists() else []
def local():
    idle();tick=time.perf_counter();m=read(OUT/'candidate_manifest.json');f=read(OUT/'reports/full.json')
    assert sha(m['production_PE'])==m['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for p,h in m['source_hashes'].items():assert sha(ROOT/p)==h,p
    old=git('ls-tree','-r','--name-only',BASE,'--','config','scripts').decode().splitlines()
    protected=[p for p in old if fnmatch.fnmatchcase(p,'config/gi_tbc*.json') or fnmatch.fnmatchcase(p,'scripts/paper_s2*.py')]
    protected+=['results/unified_exact_round137/manuscript.md','results/unified_exact_round137/manuscript.pdf']
    for p in protected:assert not git('diff',BASE,'--',p).strip(),p
    assert not git('diff',BASE,'--',*[f'results/unified_exact_round{i}' for i in range(137,145)]).strip()
    changed145=git('diff','--name-only',BASE,'--','results/unified_exact_round145').decode().splitlines()
    assert changed145==['results/unified_exact_round145/stage_evidence.md']
    assert git('status','--porcelain=v1','--untracked-files=no',cwd=Path('E:/codes/ExactEBRP')).decode()==(OUT/'protected_original_tracked_status.txt').read_text(encoding='utf-8')
    for name in ['qualification_exact_rows.json','qualification_native_writer.json','qualification_units.json','entry_check.json','reports/LP.json','review/final_scientific_review.json','pdf_visual_review.json']:
        assert read(OUT/name)['PASS'],name
    assert not f['pending'] and not budget()['unclosed'] and budget()['G1_seconds']<=28800 and read(OUT/'candidate_decision.json')['study_complete']
    raw=[]
    for arm in f['new_arms']+f['qualification']:
        d=Path(arm['destination']);v=read(d/'verification_closeout.json');assert v['native_proof_qualified'] and v['performance_eligible']
        assert arm['declared_calls']==arm['returned_calls']
        for p,h in read(d/'producer_seal.json')['required_SHA'].items():assert sha(d/p)==h,p
        raw.append(dict(arm_id=read(d/'round135_endpoint.json')['arm_id'],endpoint_SHA=sha(d/'round135_endpoint.json'),closeout_SHA=sha(d/'verification_closeout.json')))
    assert sha(OUT/'manuscript.pdf')==read(OUT/'pdf_render_manifest.json')['PDF_SHA'] and read(OUT/'PDF_marker.json')['successful_invocations']==1
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),source_PE_binding=True,protected_entries_profiles=protected,
        qualified_Native_Optimize=f['all_entered_observed_Native_Optimize'],standalone_LP_Optimize=5,raw=raw,
        all_entered_retained=True,protected_original_tracked_status_unchanged=True,old_R137_R144_results_unchanged=True,
        R145_only_requested_stage_tense_amendment=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick))
def source_publication():
    idle();m=read(OUT/'candidate_manifest.json');records=[]
    for path,digest in m['source_hashes'].items():
        data=git('show',m['source_commit']+':'+path);actual=(ROOT/path).read_bytes()
        assert hashlib.sha256(actual).hexdigest()==digest
        assert actual.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n'),path
        records.append(dict(path=path,actual_compiler_bytes_SHA256=digest,Git_bytes_SHA256=hashlib.sha256(data).hexdigest(),
            Git_blob=git('rev-parse',m['source_commit']+':'+path).decode().strip(),actual_bytes=len(actual),Git_bytes=len(data),
            equal_after_CRLF_normalization=True))
    write(OUT/'source_publication.json',dict(UTC=utc(),production_source_commit=m['source_commit'],PE_SHA256=m['production_PE_SHA'],
        compiler_SHA256=m['compiler_SHA'],compiled_units=m['compiled_units'],sources=records,
        actual_compiler_bytes_in_source_archive=True,Git_EOL_differences_explicit=True,Optimize=0,Native_load=0))
def pack():
    idle();tick=time.perf_counter();archives=[];index={};restored={};recovery=[]
    for relative in ['results/unified_exact_round132/inputs/K-20-S_landscape.json','results/unified_exact_round132/inputs/K-20-S_selection.json']:
        if not (ROOT/relative).is_file():
            value=git('show',BASE+':'+relative);restored[relative]=value
            recovery.append(dict(member=relative,commit=BASE,Git_blob=git('rev-parse',BASE+':'+relative).decode().strip(),
                SHA256=hashlib.sha256(value).hexdigest(),bytes=len(value),restored_directly_into_current_carrier=True))
    write(OUT/'inherited_metadata_recovery.json',dict(UTC=utc(),files=recovery,
        reason='Two historical selection/landscape sidecars are absent from sparse checkout; exact fixed Git blobs are packaged without altering old trees',
        model_input_changed=False,Optimize=0,Native_load=0,compile=0))
    def archive(name,paths):
        paths=sorted(set(paths));target=OUT/'artifacts'/name;target.parent.mkdir(parents=True,exist_ok=True);members=[]
        for p in paths:
            assert p.resolve().is_relative_to(ROOT.resolve()) and (p.is_file() or p.relative_to(ROOT).as_posix() in restored),p
        reuse=target.exists()
        with zipfile.ZipFile(target,'r' if reuse else 'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            if reuse:assert sorted(z.namelist())==sorted(p.relative_to(ROOT).as_posix() for p in paths),'Sealed carrier member set changed'
            for p in paths:
                assert p.suffix.lower() not in {'.exe','.dll','.lib','.a','.o','.obj','.lic','.pyc'},p
                member=p.relative_to(ROOT).as_posix();data=p.read_bytes() if p.is_file() else restored[member]
                if reuse:assert z.read(member)==data,('Sealed carrier bytes changed',member)
                else:z.writestr(member,data)
                members.append(dict(member=member,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        assert target.stat().st_size<100_000_000,'Split this carrier before publication'
        rel=target.relative_to(ROOT).as_posix();index[rel]=members
        archives.append(dict(path=rel,SHA256=sha(target),bytes=target.stat().st_size,member_count=len(members)))
    diagnostic=[]
    for folder in ['LP','engineering','failures']:diagnostic+=files(OUT/folder)
    for folder in ['rows','actual_rows','writer','units']:diagnostic+=files(OUT/'qualification'/folder)
    for fee in (OUT/'fees').iterdir():
        if not re.fullmatch(r'(?:qualification|k20|rx20|rb35|k35|base_bridge|confirmation|k15)_\d+',fee.name):diagnostic+=files(fee)
    archive('diagnostics_and_failures.zip',diagnostic)
    sources=[ROOT/p for p in read(OUT/'candidate_manifest.json')['source_hashes']];inherited=[];qual=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(path)
        if 'batch' not in matrix:continue
        sources += [ROOT/p for p in matrix.get('helpers',{})]
        for g in matrix['groups']:
            p=g['launch']['panel'];inherited += [ROOT/p[k] for k in ['input_path','selection_path','landscape_path'] if p.get(k)]
            raw=files(OUT/g['group'])+files(OUT/'fees'/f'{matrix["batch"]}_{g["position"]:03}')
            if matrix['batch'].startswith('qualification'):qual+=raw
            else:archive(f'campaign_{matrix["batch"]}_{g["position"]:03}.zip',raw)
    archive('qualification_complete.zip',qual)
    for result in (OUT/'LP').glob('*/result.json'):
        p=read(result)['baseline_reused'];inherited += [ROOT/p[k] for k in ['result','solution','matrix']]
    for role in ['K-20-S','K-35-U','R-X20-S-T1']:
        folder=ROOT/'results/unified_exact_round145/LP'/f'{role}_joint'
        inherited += [folder/name for name in ['result.json','scope.json','solution.json.gz']]
        inherited += [ROOT/'results/unified_exact_round143/inherited/roots'/role/'scope.json']
    inherited += [ROOT/'results/unified_exact_round145/compact/R-X20-S-T1'/name for name in ['result.json','solution.json.gz']]
    inherited += [ROOT/'results/unified_exact_round137/matrix_frozen.json',ROOT/'results/unified_exact_round145/candidate_manifest.json',
        ROOT/'results/unified_exact_round138/reports/pairs.csv',ROOT/'results/unified_exact_round145/reports/full.json',
        ROOT/'results/unified_exact_round145/stage_evidence.md']
    for roundno in range(137,146):
        p=ROOT/f'results/unified_exact_round{roundno}/final_report.md'
        if p.exists():inherited.append(p)
    archive('finite_inherited_inputs.zip',inherited)
    sources += list((ROOT/'scripts').glob('round146_*'))+[ROOT/'scripts/paper_s2_gd.py',ROOT/'config/gi_tbc_gd_round146.json',
        ROOT/'CMakeLists.txt',ROOT/'.gitattributes',ROOT/'WORKSPACE_POLICY.md',ROOT/'config/gi_tbc_round137.json',ROOT/'scripts/paper_s2.py']
    sources += [ROOT/name for name in ['docs/round146_research.md','docs/current_mainline.md','docs/unified_exact_research_index.md']]
    pending=[p for p in sources if p.suffix=='.py'];seen=set()
    while pending:
        p=pending.pop()
        if p in seen:continue
        seen.add(p);tree=ast.parse(p.read_text(encoding='utf-8-sig'));modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:modules.append(node.module)
        for module in modules:
            dependency=ROOT/'scripts'/(module.split('.')[0]+'.py')
            if dependency.is_file() and dependency not in seen:sources.append(dependency);pending.append(dependency)
    archive('source_and_helpers.zip',sources)
    excluded={'carrier_manifest.json','archive_local_check.json','publication_pin.json','public_restore_owner.json','public_attempt_history.json','public_restore_receipt.json',
        'cleanup_record.json','PR_delivery.json','PR_readback.json','PR_description.md','delivery_costs.json'}
    science=[p for p in OUT.iterdir() if p.is_file() and p.name not in excluded]
    for folder in ['reports','review','stages','figures','qa_pages','delivery_failures']:science+=files(OUT/folder)
    archive('science_and_paper.zip',science)
    raw=json.dumps(index,separators=(',',':'),ensure_ascii=False).encode('utf-8');target=OUT/'artifacts/member_index.json.gz';target.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),schema='round146-carriers-external-member-index-v1',archives=archives,archive_count=len(archives),
        indexed_members=sum(len(v) for v in index.values()),compressed_bytes=sum(a['bytes'] for a in archives)+target.stat().st_size,
        member_index=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,format='gzip-compressed JSON keyed by archive path'),
        Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,commercial_binaries_or_licenses_published=False))
    print(json.dumps(dict(archives=len(archives),members=sum(len(v) for v in index.values()),seconds=time.perf_counter()-tick)))
def public(commit):
    idle();import round145_delivery as old;configure()
    source=inspect.getsource(old.public).replace('round145','round146').replace('Round145','Round146')
    ns=dict(vars(old),ROOT=ROOT,WORK=WORK,OUT=OUT,TEMP=TEMP,idle=idle,budget=budget,sha=sha,read=read,write=write)
    exec(compile(source,__file__+'::bounded_public_recovery','exec'),ns);ns['public'](commit)
def cleanup():
    idle();import round145_delivery as old;configure()
    source=inspect.getsource(old.cleanup).replace('round145','round146').replace('Round145','Round146')
    ns=dict(vars(old),ROOT=ROOT,WORK=WORK,OUT=OUT,TEMP=TEMP,idle=idle,budget=budget,sha=sha,read=read,write=write,files=files)
    exec(compile(source,__file__+'::bounded_current_round_cleanup','exec'),ns);ns['cleanup']()
def prbody(commit):
    idle();assert re.fullmatch('[0-9a-f]{40}',commit)
    m=read(OUT/'candidate_manifest.json');c=read(OUT/'cost_report.json');f=read(OUT/'reports/full.json');d=read(OUT/'candidate_decision.json')
    base=read(OUT/'PR_base_selection.json')
    url=f'https://github.com/yifanXovo/TailoredExact/blob/{commit}/results/unified_exact_round146'
    body=f'''Fractional inventory selectors can retain a Gini epigraph gap even with shared stock/count/reciprocal information. This adds a separate default-off direct GD mechanism: at most two original-selector rows derived from the classical Gini-Hoover relation and exact state-conditioned inventory-box denominator bounds. Coefficients are generated once, transported downward safely and inherited only on compatible sub-supports. There are no new variables, source solves, callbacks or controller changes. The physical objective remains g + lambda P.

Five new matched LPs reuse sealed baseline optima/points. K20 BASE rises from .195149152441 to .236010302342, joint from .222808939661 to .239052184675, and STOCK from .204590439178 to .251016109922. K35/RX20 BASE also improve; their existing joint optimum witnesses satisfy GD, so those two cells are not reoptimized. The universal zero-stock inequality closes the R145 half/half binary family at g >= 1/2 without claiming the full routing hull or a new general inequality theorem.

One uniform STOCK+GD candidate is compared with same-PE STOCK, complete own H, Seed0/Threads1 and mandatory verification. {d['complete_discussion']}

Decision: **{d['decision']}**. {d['decision_discussion']}

All {f['all_entered_observed_Native_Optimize']} complete/qualification Native calls returned; five standalone LPs are separate. Exact directed-arithmetic and inventory-unit checks, actual canonical/Native coefficient transport, full/nonminimal Starts, strict sub-support inheritance, scope rejection and unchanged default-off matrices pass. Independent pre-admission/final scientific review and actual PDF visual review pass. New experimental outer cost is **{c['charged_new_experiment_seconds']:.9f} seconds ({c['charged_new_experiment_seconds']/3600:.6f} hours)** of 28800, without nested double counting. Every entered result and adverse endpoint is retained.

Fixed science `{commit}`:

- [Scientific report]({url}/final_report.md), [decision]({url}/candidate_decision.json), [LP report]({url}/LP_report.md)
- [Paper section]({url}/manuscript.pdf), [mathematics]({url}/mathematical_analysis.md), [same-PE results]({url}/reports/full.json)
- [Independent review]({url}/review/final_scientific_review.json), [cost]({url}/cost_report.json), [carriers]({url}/carrier_manifest.json), [source/PE]({url}/candidate_manifest.json)

Measured production source `{m['source_commit']}` and PE SHA256 `{m['production_PE_SHA']}` are distinct from science/delivery commits. Stable R137 and all earlier entries/profiles remain unchanged; the requested R145 stage-index tense correction does not rerun old experiments. {base['explanation']} This remains Draft; no merge or force push. Anonymous current-carrier public byte/member recovery and bounded post-PR cleanup are recorded in late delivery metadata with zero Optimize, compile or commercial Native load.
'''
    (OUT/'PR_description.md').write_text(body,encoding='utf-8',newline='\n')
if __name__=='__main__':
    if sys.argv[1] in ('public','prbody'):globals()[sys.argv[1]](sys.argv[2])
    else:globals()[sys.argv[1]]()
