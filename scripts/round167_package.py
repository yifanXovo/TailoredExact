"""Publish only the current round's own new raw/PE; never copies vendor DLLs."""
from round167_common import *
import csv,gzip,io,zipfile
def package():
    dest=OUT/'artifacts';dest.mkdir(exist_ok=True)
    archive=dest/'round167_new_raw_and_runtime.zip'
    assert not archive.exists(),'one-time carrier; never overwrite a published archive'
    entries=[]
    for directory in [OUT/'qualification']:
        entries.extend((p,p.relative_to(OUT).as_posix()) for p in sorted(directory.rglob('*')) if p.is_file())
    entries.extend((p,'review/'+p.name) for p in sorted((OUT/'review').glob('manuscript_*.png')))
    exe=WORK/'build-cache/round167/Round167Research.exe';entries.append((exe,'runtime/Round167Research.exe'))
    for name in ['src/round167_research.cpp','include/Round167ConditionalState.hpp']:
        entries.append((ROOT/name,'measured_source/'+name))
    entries.append((OUT/'build/preparation_v1.zip','preparation/preparation_v1.zip'))
    rows=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,member in entries:
            assert p.suffix.lower() not in ['.dll','.lic'],p
            assert 'license' not in p.name.lower() and 'credential' not in p.name.lower(),p
            z.write(p,member);rows.append(dict(member=member,bytes=p.stat().st_size,SHA256=sha(p),local_source=str(p)))
    sio=io.StringIO(newline='');writer=csv.DictWriter(sio,fieldnames=['member','bytes','SHA256','local_source']);writer.writeheader();writer.writerows(rows)
    membermap=dest/'round167_new_raw_members.csv.gz';membermap.write_bytes(gzip.compress(sio.getvalue().encode('utf-8')))
    # One actual bounded local readback, before public recovery.
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(rows)
        for row in rows:assert hashlib.sha256(z.read(row['member'])).hexdigest()==row['SHA256']
    write(OUT/'evidence_archives.json',dict(UTC=utc(),new_only=True,carrier=bind(archive),membermap=bind(membermap),members=len(rows),
        raw_uncompressed_bytes=sum(r['bytes'] for r in rows),local_member_readback=True,
        own_project_PE_included=True,commercial_DLL_license_credentials_private_antecedent_included=False,
        historical_carriers_repacked=False,recovery='unzip members qualification/ under results/unified_exact_round167/; runtime/ is the new diagnostic PE only'))
    print('New-only carrier',len(rows),'members,',archive.stat().st_size,'bytes.')
if __name__=='__main__':package()
