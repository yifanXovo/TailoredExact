"""New-only package, exact stage, one serial public recovery, zero-delete closeout."""
import inspect,shutil,zipfile
import round153_delivery as inherited
from round158_common import *

HEAVY={'resource','level','primal','physical','qualification','fees','engineering','infra'}
MUTABLE={'carrier_manifest.json','public_manifest.json','public_restore_receipt.json','public_restore_failure.json',
    'publication.json','cleanup_record.json','RESUME.md','pr_body.md','stage_paths.json','stage_verification.json',
    'final_protection_readback.json','remote_final_readback.json','final_acceptance_audit.json'}
safe=inherited.safe

def serial_idle():
    from round100_idle import ensure_idle
    configure();ensure_idle();assert not budget()['unclosed']

def protect():
    count=0
    for tree in read(OUT/'infra/protected_initial.json')['trees']:
        for name,old in tree['tracked_dirty'].items():
            assert sha(Path(tree['tree'])/name)==old['SHA256'],(tree['tree'],name);count+=1
    return count

def pack():
    serial_idle();protect();assert read(OUT/'final_decision.json')['study_complete']
    assert read(OUT/'review/final_scientific_review.json')['PASS']
    assert read(OUT/'review/paper_claim_review.json')['PASS']
    assert read(OUT/'paper_qa/visual_review.json')['PASS']
    tick=time.perf_counter();art=OUT/'artifacts';art.mkdir(exist_ok=True);groups={}
    for label in ('resource','level','primal','physical'):
        groups[label]=[p for p in (OUT/label).rglob('*') if p.is_file()]
    # The old NB start is referenced by its exact fixed-commit/member hash,
    # and retained locally. It is not repackaged as new evidence.
    groups['qualification_failures_fees']=[p for name in HEAVY-{'resource','level','primal','physical'}
        for p in (OUT/name).rglob('*') if p.is_file() and p.name!='nb_relaxed_assignment.json.gz']
    groups['necessary_point_models']=[p for p in (OUT/'review').rglob('*') if p.is_file() and p.suffix in ('.mps','.gz')]
    archives=[];seen=set()
    for label,files in groups.items():
        if not files:continue
        path=art/(label+'.zip');members=[]
        with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(set(files)):
                name=p.relative_to(ROOT).as_posix();safe(name);assert name not in seen;seen.add(name)
                data=p.read_bytes();z.writestr(name,data)
                members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        idx=art/(label+'.members.json.gz');save_gz(idx,members);parts=[]
        if path.stat().st_size>40*1024*1024:
            with path.open('rb') as stream:
                no=0
                while True:
                    content=stream.read(32*1024*1024)
                    if not content:break
                    no+=1;part=path.with_name(path.name+f'.part{no:03}');part.write_bytes(content)
                    parts.append(dict(path=part.relative_to(ROOT).as_posix(),SHA256=sha(part),bytes=len(content)))
        else:parts=[dict(path=path.relative_to(ROOT).as_posix(),SHA256=sha(path),bytes=path.stat().st_size)]
        archives.append(dict(name=path.name,SHA256=sha(path),bytes=path.stat().st_size,parts=parts,
            member_index=dict(path=idx.relative_to(ROOT).as_posix(),SHA256=sha(idx),bytes=idx.stat().st_size),
            members=len(members),uncompressed_bytes=sum(m['bytes'] for m in members)))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=archives,old_carriers_repacked=0,
        unique_evidence_and_failures_retained=True,old_NB_start_copy_repacked=False,pack_IO_seconds=time.perf_counter()-tick))
    thin=[p for p in OUT.rglob('*') if p.is_file() and p.relative_to(OUT).parts[0] not in HEAVY|{'artifacts'}
        and p.name not in MUTABLE and p.relative_to(ROOT).as_posix() not in seen]
    thin+=list((ROOT/'scripts').glob('round158*.py'))
    thin+=[ROOT/p for p in ('.gitattributes','.gitignore','docs/round158_research.md','docs/current_mainline.md',
        'docs/unified_exact_research_index.md','docs/paper_review.md',
        'results/unified_exact_round157/final_report.md','results/unified_exact_round157/RESUME.md') if (ROOT/p).is_file()]
    files=[]
    for p in sorted(set(thin)):
        name=p.relative_to(ROOT).as_posix();safe(name);files.append(dict(path=name,SHA256=sha(p),bytes=p.stat().st_size))
    write(OUT/'public_manifest.json',dict(UTC=utc(),schema='round158-new-only-fixed-commit-v1',files=files,archives=archives,
        reference_index='results/unified_exact_round158/reuse_index.json',
        inherited_member_recovery='Fixed R157/R156/R137 commit/member references; no old carrier downloaded in current-only recovery.',
        forbidden_operations=['Optimize','compile','old producer','delete','move'],pack_IO_seconds=time.perf_counter()-tick))
    paths=[r['path'] for r in files]+[(OUT/n).relative_to(ROOT).as_posix() for n in ('carrier_manifest.json','public_manifest.json','RESUME.md')]
    for a in archives:paths+=[a['member_index']['path']]+[p['path'] for p in a['parts']]
    write(OUT/'stage_paths.json',paths)
    print(json.dumps(dict(archives=len(archives),members=len(seen),compressed_bytes=sum(a['bytes'] for a in archives),thin_files=len(files))),flush=True)

def stage():
    serial_idle();paths=read(OUT/'stage_paths.json')+['results/unified_exact_round158/stage_paths.json'];facts=[]
    for no in range(0,len(paths),30):subprocess.run(['git','add','--sparse','--force','--',*paths[no:no+30]],cwd=ROOT,check=True)
    for p in paths:
        data=subprocess.check_output(['git','show',':'+p],cwd=ROOT);assert hashlib.sha256(data).hexdigest()==sha(ROOT/p),p
        facts.append(dict(path=p,SHA256=sha(p),bytes=len(data)))
    write(OUT/'stage_verification.json',dict(PASS=True,files=facts,exact_index_blobs=True));print(json.dumps(dict(staged=len(paths))),flush=True)

def restore(commit):
    serial_idle();source=inspect.getsource(inherited.restore).replace('round153','round158').replace('Round153','Round158')
    source=source.replace('max_workers=4','max_workers=1')
    ns=dict(vars(inherited),ROOT=ROOT,OUT=OUT,WORK=WORK,safe=safe)
    exec(compile(source,__file__+'::bounded_public_restore','exec'),ns);return ns['restore'](commit)

def cleanup():
    serial_idle();count=protect();assert read(OUT/'public_restore_receipt.json')['state']=='PASS'
    tick=time.perf_counter();before=shutil.disk_usage(WORK.anchor);stats=[]
    areas=[OUT,WORK/'raw/round158',WORK/'temp/round158',WORK/'build-cache/round158']+list((WORK/'restore').glob('round158-public-*'))
    for area in areas:
        if not area.exists():continue
        absolute=area.resolve();assert absolute.is_relative_to(WORK.resolve())
        files=[p for p in area.rglob('*') if p.is_file()];stats.append(dict(path=str(absolute),files=len(files),bytes=sum(p.stat().st_size for p in files),action='retained'))
    after=shutil.disk_usage(WORK.anchor)
    write(OUT/'cleanup_record.json',dict(UTC=utc(),deleted_paths=[],deleted_bytes=0,retained=stats,current_round_only=True,
        no_recursive_delete_or_move=True,reason='Retain active tree, unique science/failures, needed runtime references and accepted recovery; zero deletion is allowed.',
        volume_before=dict(total=before.total,used=before.used,free=before.free),
        volume_after=dict(total=after.total,used=after.used,free=after.free),observed_free_change=after.free-before.free,
        metadata_IO_seconds=time.perf_counter()-tick))
    write(OUT/'final_protection_readback.json',dict(UTC=utc(),PASS=True,tracked_dirty_files=count,
        initial_snapshot_SHA=sha(OUT/'infra/protected_initial.json'),checked_after_public_recovery=True))
    print(json.dumps(dict(deleted_bytes=0,protected=count)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
