"""Finite Round127 evidence carriers; no native software or historical carrier.

Pack only after performance work is idle. Raw remains authoritative in place.
"""
from round127_common import *
import ast,re,zipfile

BAD=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{35,}',rb'(?i)(?:cookie|authorization)\s*:\s*(?:bearer\s+)?[A-Za-z0-9+/=_-]{24,}',
     rb'(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{24,}',rb'AIza[0-9A-Za-z_-]{35}',rb'ya29\.[0-9A-Za-z_-]{24,}',
     rb'(?i)(?:WLSSecret|WLSAccessID|CloudSecretKey|CSAPISecret)\s*(?:=|:|to value)\s*[\"\x27]?[A-Za-z0-9_-]{16,}',
     rb'(?m)^KEY=[0-9a-fA-F]{20,}']
FORBIDDEN={'.exe','.dll','.lic','.key','.pem','.pfx','.p12','.ttf','.otf','.woff','.woff2','.html'}
def scan(p):
    assert p.suffix.lower() not in FORBIDDEN,('forbidden published artifact',str(p))
    assert p.resolve().is_relative_to(ROOT.resolve()) and not p.is_symlink() and not p.is_junction()
    if p.suffix=='.pdf':assert p.name=='manuscript.pdf';return p.stat().st_size
    tail=b'';size=0
    with p.open('rb') as f:
        while b:=f.read(1024*1024):
            for pattern in BAD:assert not re.search(pattern,tail+b),('credential marker',str(p))
            tail=b[-256:];size+=len(b)
    return size
def idle():
    live=subprocess.check_output(['powershell.exe','-NoProfile','-Command',"Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|MSBuild)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not live,live
def pack():
    idle();target=OUT/'artifacts';target.mkdir(exist_ok=True);temporary=TEMP/'archives';temporary.mkdir(parents=True,exist_ok=True)
    assert all((OUT/stage).is_dir() for stage in ['training','main','tiny','core'])
    assert not (OUT/'raw_archive_manifest.json').exists(),'preserve existing packed evidence; inspect before any new packing'
    stage_inputs={stage:[p for p in (OUT/stage).rglob('*') if p.is_file()]
        for stage in ['training','main','tiny','core']}
    support=[p for p in (OUT/'qualification').rglob('*') if p.is_file()]
    support.extend(p for folder in (OUT/'fees').iterdir() if folder.is_dir() and (folder/'receipt.json').exists()
        for p in folder.rglob('*') if p.is_file())
    support.extend(p for p in (OUT/'source_E0').rglob('*') if p.is_file())
    planned=set(support).union(*(set(files) for files in stage_inputs.values()))
    raw_bytes=sum(p.stat().st_size for p in planned)
    archive_upper=raw_bytes+2048*len(planned)+1024**3
    # Allow full ZIPs, public pieces, Git materialization, one downloaded and
    # joined recovery copy, the expanded raw tree and a separate loose margin.
    additional_upper=6*archive_upper+raw_bytes+2*1024**3
    free=shutil.disk_usage(WORK).free
    write(OUT/'review/packing_space_check.json',dict(status='PASS' if free>=additional_upper else 'INSUFFICIENT_SPACE',
        UTC=utc(),free_bytes_before_pack=free,planned_member_count=len(planned),
        logical_raw_member_bytes=raw_bytes,conservative_archive_bytes=archive_upper,
        conservative_additional_materialization_upper_bytes=additional_upper,
        original_preliminary_peak_allowance_bytes=read(OUT/'initialization.json')['peak_increment_allowance_bytes'],
        planning_only_not_a_measured_peak_or_volume_reclamation=True,
        scope='Current finite carriers and one recovery campaign only; all authoritative raw remains in place.'))
    assert free>=additional_upper,('insufficient prepack/recovery capacity',free,additional_upper)
    groups=[];scanned=0;index=[];tick=time.perf_counter()
    def create(name,files):
        nonlocal scanned
        complete=temporary/(name+'.zip');assert not complete.exists();raw=0;members=[]
        with zipfile.ZipFile(complete,'x',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for p in sorted(set(files)):
                scanned+=scan(p);raw+=p.stat().st_size;name_in=p.relative_to(ROOT).as_posix()
                members.append(dict(path=name_in,bytes=p.stat().st_size,SHA256=sha(p)));z.write(p,name_in)
        pieces=[];limit=48*1024**2
        with complete.open('rb') as f:
            n=1
            while data:=f.read(limit):
                name_out=complete.name if complete.stat().st_size<=limit else complete.name+f'.part{n:02d}'
                dst=target/name_out;assert not dst.exists();dst.write_bytes(data)
                pieces.append(dict(path=dst.relative_to(ROOT).as_posix(),bytes=len(data),SHA256=sha(dst)));n+=1
        return dict(name=complete.name,SHA256=sha(complete),compressed_bytes=complete.stat().st_size,uncompressed_bytes=raw,file_count=len(members),pieces=pieces,members=members,temporary_complete_archive=str(complete))
    for stage in ['training','main','tiny','core']:
        groups.append(create(stage,stage_inputs[stage]))
        for path in sorted((OUT/stage).glob('*/identity.json')):
            identity=read(path)
            for l in identity['launches']:
                d=Path(l['destination']);index.append(dict(stage=stage,id=l['id'],method=l['method'],seed=l['seed'],repeat=l['repeat'],binary_layer=l['binary_layer'],raw_root=d.relative_to(ROOT).as_posix(),identity_SHA=sha(path),producer_receipt_SHA=sha(d/'producer_receipt.json'),result_SHA=sha(d/'result.json'),model_journal_SHA=sha(d/'observations.json')))
    groups.append(create('qualification_closed_fees_original_sources',support))
    write(OUT/'raw_archive_manifest.json',dict(schema='round127-finite-carriers-v1',archives=groups,raw_remains_in_place=True,no_PE_DLL_license_or_historical_carrier=True,live_pack_fee_and_future_receipts_excluded=True,seconds=time.perf_counter()-tick))
    write(OUT/'evidence/arm_index.json',dict(arms=index,formal_arms=sum(x['stage']!='training' for x in index),training_arms=sum(x['stage']=='training' for x in index)))
    write(OUT/'review/publication_scan.json',dict(status='PASS',actual_precompression_bytes_scanned=scanned,forbidden_extensions=sorted(FORBIDDEN),archives=len(groups),no_native_software_or_credentials=True,scope='All actual finite carrier members scanned before compression; no blanket historical clearance.'))
    print(json.dumps(dict(archives=len(groups),compressed_bytes=sum(g['compressed_bytes'] for g in groups),raw_bytes=sum(g['uncompressed_bytes'] for g in groups),scanned_bytes=scanned)))
def script_closure(start):
    modules={p.stem:p for p in (ROOT/'scripts').glob('*.py')};pending=list(start);seen=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name);path=ROOT/name
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            wanted=[q.name.split('.')[0] for q in node.names] if isinstance(node,ast.Import) else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else []
            pending.extend(modules[n].relative_to(ROOT).as_posix() for n in wanted if n in modules and modules[n].relative_to(ROOT).as_posix() not in seen)
    return seen
def manifest():
    names=set();excluded={'training','main','tiny','core','qualification','fees','source_E0'}
    mutable={'export_manifest.json','resource_accounting.json','RESUME.md','runtime_status.json','public_restore_receipt.json','public_restore_receipt_failure.json','cleanup_receipt.json','delivery_receipt.json','completion_audit.json','completion_audit.md','content_A_scan.json'}
    for p in OUT.rglob('*'):
        if not p.is_file():continue
        relative=p.relative_to(OUT)
        if relative.parts[0] in excluded or p.name in mutable:continue
        names.add(p.relative_to(ROOT).as_posix())
    names.update(script_closure([p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('*round127*.py')]))
    names.update(read(OUT/'tiny_recipe.json')['dependencies'])
    names.add('scripts/round127_export.cpp')
    names.update(read(OUT/'E1_frozen.json')['source_bindings'])
    im=read(OUT/'input_manifest.json')
    names.update(p['input_path'] for p in im['main_roles']+im['training_roles']+im['core_roles'])
    names.update(['results/unified_exact_round94/preregistration.json','results/unified_exact_round108/input_manifest.json','results/unified_exact_round122/input_manifest.json',
        'results/unified_exact_round126/paper_method_config.json','results/unified_exact_round126/production_identity.json','results/unified_exact_round126/input_manifest.json',
        'results/unified_exact_round126/protocol.json','results/unified_exact_round126/measurement_policy_v2.json','results/unified_exact_round126/argv_freeze.json',
        'results/unified_exact_round126/arms.csv','results/unified_exact_round126/certification_summary.json'])
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'results/unified_exact_round126/inputs').glob('*') if p.is_file())
    names.update(['results/data_generation_citibike_round57/source_station_table.csv','results/unified_exact_round116/projection_contract.json','results/unified_exact_round116/source/snapshot.json','results/unified_exact_round116/source/source_station_table.csv','results/unified_exact_round116/source/row_decisions.json','results/unified_exact_round116/source/requests/station_information/01.response'])
    files=[];scanned=0
    for name in sorted(names):
        p=ROOT/name;assert p.is_file(),name
        if 'artifacts' not in p.parts:scanned+=scan(p)
        files.append(dict(path=name,bytes=p.stat().st_size,SHA256=sha(p),serialization='exact bytes; only exact-SHA-matching LF/CRLF materialization permitted' if p.suffix in ['.py','.cpp','.hpp','.h','.inc','.md','.json','.txt','.csv','.bib'] else 'exact bytes'))
    write(OUT/'export_manifest.json',dict(schema='round127-single-science-A-public-manifest-v1',files=files,raw_manifest_SHA=sha(OUT/'raw_archive_manifest.json'),no_historical_carrier_or_native_software=True,future_B_receipts_excluded=True,manifest_does_not_hash_itself=True,restore_checks='Every finite carrier member SHA256; all sealed endpoints/clocks/model hashes, all36 selection arithmetic and all typed comparisons/aliases/tiny thresholds; no Optimize'))
    write(OUT/'review/content_A_scan.json',dict(status='PASS',manifest_files=len(files),actual_loose_bytes_scanned=scanned,carriers_scanned_before_compression='review/publication_scan.json',future_receipts_excluded=True))
    print(json.dumps(dict(files=len(files),bytes=sum(r['bytes'] for r in files))))
if __name__=='__main__':{'pack':pack,'manifest':manifest}[sys.argv[1]]()
