"""New-only carriers and one bounded anonymous fixed-commit recovery.

No Optimize, compiler, old producer, delete or move. Existing R153 input/
source/carrier dependencies are references, never a repack of old archives.
"""
from pathlib import PurePosixPath
import concurrent.futures,inspect,re,shutil,types,zipfile
from urllib.parse import quote
import round153_delivery as previous
from round154_common import *

HEAVY={'coupled','support_LP','qualification','fees','engineering','infra','campaign_confirmation','directions','fixed_prices'}
EXCLUDED={'carrier_manifest.json','public_manifest.json','public_restore_receipt.json','publication.json','cleanup_record.json',
          'RESUME.md','pr_body.md','stage_paths.json'}
FORBIDDEN={'.exe','.dll','.lib','.o','.obj','.a','.lic','.pyc','.ttf','.otf'}
safe=previous.safe

def pack():
    assert not budget()['unclosed'],'no packing while experiments/builds run'
    tick=time.perf_counter();art=OUT/'artifacts';art.mkdir(exist_ok=True);groups={};assigned=set()
    for role in ['N-B35-S','K-35-U','N-C20-U']:
        members=[]
        for name in ['coupled','support_LP']:
            for folder in (OUT/name).glob(role+'*'):
                members.extend(p for p in folder.rglob('*') if p.is_file())
        for direction in (OUT/'directions').glob('*/direction.json'):
            if read(direction)['role']!=role:continue
            members.extend(p for p in direction.parent.rglob('*') if p.is_file())
            members.extend(p for p in (OUT/'fixed_prices'/direction.parent.name).rglob('*') if p.is_file())
        if members:groups['research_'+role]=members;assigned.update(members)
    groups['qualification_failures_and_fees']=[p for name in HEAVY-{'campaign_confirmation'} for p in (OUT/name).rglob('*')
        if p.is_file() and p not in assigned]
    for camp in sorted((OUT/'campaign_confirmation').glob('*')):
        if camp.is_dir():groups['complete_arm_'+camp.name]=[p for p in camp.rglob('*') if p.is_file()]
    archives=[];seen=set()
    for label,files in groups.items():
        if not files:continue
        dest=art/(label+'.zip');assert not dest.exists();members=[]
        with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(set(files)):
                name=p.relative_to(ROOT).as_posix();safe(name);assert name not in seen;seen.add(name)
                assert p.suffix.lower() not in FORBIDDEN,p
                data=p.read_bytes();z.writestr(name,data)
                members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        idx=art/(label+'.members.json.gz');save_gz(idx,members);parts=[]
        if dest.stat().st_size>40*1024*1024:
            with dest.open('rb') as f:
                k=0
                while True:
                    data=f.read(32*1024*1024)
                    if not data:break
                    k+=1;p=dest.with_name(dest.name+f'.part{k:03}');assert not p.exists();p.write_bytes(data)
                    parts.append(dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=len(data)))
        else:parts=[dict(path=dest.relative_to(ROOT).as_posix(),SHA256=sha(dest),bytes=dest.stat().st_size)]
        archives.append(dict(name=dest.name,SHA256=sha(dest),bytes=dest.stat().st_size,parts=parts,
            member_index=dict(path=idx.relative_to(ROOT).as_posix(),SHA256=sha(idx),bytes=idx.stat().st_size),
            members=len(members),uncompressed_bytes=sum(m['bytes'] for m in members)))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=archives,old_carriers_repacked=0,
        unique_raw_retained=True,all_failures_preserved=True,pack_IO_seconds=time.perf_counter()-tick))
    thin=[p for p in OUT.rglob('*') if p.is_file() and p.relative_to(OUT).parts[0] not in HEAVY|{'artifacts'} and p.name not in EXCLUDED]
    thin+=list((ROOT/'scripts').glob('round154*'))
    for name in ['scripts/paper_s2_proof_floor.py','include/Round154Research.hpp','include/Round153Research.hpp',
        'config/gi_tbc_proof_floor_round154.json','src/main.cpp','src/PaperExternalGiniTree.cpp','.gitattributes','.gitignore',
        'docs/round154_research.md','docs/current_mainline.md','docs/unified_exact_research_index.md','docs/paper_review.md']:
        if (ROOT/name).is_file():thin.append(ROOT/name)
    files=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size) for p in sorted(set(thin))]
    write(OUT/'public_manifest.json',dict(UTC=utc(),schema='round154-new-only-fixed-commit-v1',files=files,archives=archives,
        reference_index='results/unified_exact_round154/reuse_index.json',
        inherited_member_recovery='Resolve old Q/pools/inputs/source through fixed R153 science and member hashes; no old carrier is repacked or downloaded by this new-only recovery.',
        forbidden_operations=['Optimize','compile','old producer','delete','move'],pack_IO_seconds=time.perf_counter()-tick))
    paths=[x['path'] for x in files]+[(OUT/n).relative_to(ROOT).as_posix() for n in ['carrier_manifest.json','public_manifest.json','RESUME.md']]
    for a in archives:paths+=[a['member_index']['path']]+[p['path'] for p in a['parts']]
    write(OUT/'stage_paths.json',paths)
    print(json.dumps(dict(archives=len(archives),members=len(seen),compressed_bytes=sum(a['bytes'] for a in archives),thin_files=len(files),IO_seconds=time.perf_counter()-tick)),flush=True)

def inherited_function(name,*args):
    # These routines already implement path/birth safety and a hash-by-hash
    # current-only recovery. Rebind only this round's identity and root.
    source=inspect.getsource(getattr(previous,name)).replace('round153','round154').replace('Round153','Round154')
    ns=dict(vars(previous),ROOT=ROOT,WORK=WORK,OUT=OUT)
    exec(compile(source,__file__+'::'+name,'exec'),ns)
    return ns[name](*args)

def restore(commit):return inherited_function('restore',commit)
def stage():return inherited_function('stage')
def cleanup():return inherited_function('cleanup')

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
