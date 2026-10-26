"""Archive the completed H1/F5 evidence and reader correction while idle."""
import json
import time
import zipfile
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha
import round96_external as external

def main():
    external.ensure_idle();start=time.perf_counter();files=set()
    folders=[OUT/'external/raw/02_H1_ENS-C',OUT/'external/raw/03_H1_LP-G',
        OUT/'primal/raw',OUT/'primal/reference',OUT/'primal_v2',
        OUT/'external_report_h1',OUT/'external_trajectory_h1',OUT/'primal_report_f5',
        OUT/'cost_report_f5',ROOT/'reference/round96_primal_validation']
    for folder in folders:files.update(p for p in folder.rglob('*') if p.is_file())
    files.update(p for p in OUT.glob('*') if p.is_file() and p.suffix not in {'.zip'}
                 and not p.name.startswith('stage') and p.name!='pr_body.md')
    for identity_path in [OUT/'external/identity.json',OUT/'primal/identity.json']:
        identity=read(identity_path);files.add(identity_path)
        for key in ['bindings','source_hashes','harness_hashes']:
            for relative,expected in identity.get(key,{}).items():
                path=ROOT/relative
                if path.is_file():assert sha(path)==expected;files.add(path)
    build=read(OUT/'production_build_identity.json')
    for relative,expected in build['source_hashes'].items():
        path=ROOT/relative;assert sha(path)==expected;files.add(path)
    files.update(ROOT/'scripts'/name for name in ['round96_derived_numeric.py','round96_primal_report.py',
        'round96_cost_report.py','round96_primal_recovery_v2.py','round96_serial_queue_v2.py',
        'round96_stage3_archive.py','round96_trajectory.py'])
    records=[];archive=OUT/'stage3_evidence.zip';assert not archive.exists()
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as stream:
        for path in sorted(files):
            relative=path.relative_to(ROOT).as_posix();digest=sha(path)
            stream.write(path,relative);records.append(dict(path=relative,bytes=path.stat().st_size,sha256=digest))
    import hashlib
    with zipfile.ZipFile(archive) as stream:
        assert len(stream.infolist())==len(records)
        for row in records:assert hashlib.sha256(stream.read(row['path'])).hexdigest()==row['sha256']
    write(OUT/'stage3_archive.json',dict(files=records,archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,verified_members=len(records),wall_seconds=time.perf_counter()-start,
        production_source_ref=build['source_ref'],optimizer_calls=0,paid_starts=0,
        scope='H1 ENS/LP and F5 OFF/P/ON raw evidence, original failed audit, corrected offline audit, qualified production source capsule and preparation. H1/P and earlier diagnostics remain in stage1/2 archives. No credentials or solver license included.'))
    print(json.dumps(dict(members=len(records),bytes=archive.stat().st_size,seconds=time.perf_counter()-start)))

if __name__=='__main__':main()
