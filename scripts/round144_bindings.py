"""Finite source/helper byte binding. Run only after timed producers stop."""
from round144_common import *
def main():
    assert not budget()['unclosed'];m=read(OUT/'candidate_manifest.json');used={};sets=[];versions=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        v=read(path)
        if 'helpers' not in v:continue
        sets.append(dict(matrix=path.relative_to(ROOT).as_posix(),matrix_SHA=sha(path),helpers=v['helpers']))
        for p,h in v['helpers'].items():used.setdefault(p,set()).add(h)
    for p,digests in sorted(used.items()):
        current=(ROOT/p).read_bytes();current_h=hashlib.sha256(current).hexdigest()
        for h in sorted(digests):
            if h==current_h:
                versions.append(dict(path=p,SHA256=h,current=True,carrier_member=p));continue
            candidates=git('log','--format=%H','-20','--',p).decode().splitlines();found=None
            for commit in candidates:
                blob=git('show',commit+':'+p)
                for transform,value in [('identity',blob),('Git_LF_to_local_CRLF',blob.replace(b'\n',b'\r\n') if b'\r' not in blob else blob)]:
                    if hashlib.sha256(value).hexdigest()==h:found=(commit,transform,value);break
                if found:break
            assert found,('unbound frozen helper; preserve actual failed/working version explicitly',p,h)
            commit,transform,value=found;target=OUT/'engineering/helper_versions'/h/Path(p).name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(value)
            versions.append(dict(path=p,SHA256=h,current=False,Git_commit=commit,transport=transform,carrier_member=target.relative_to(ROOT).as_posix()))
    write(OUT/'measured_helper_versions.json',dict(actual_frozen_sets=sets,versions=versions,all_actual_versions_bound=True,
        changed_reader_versions_do_not_rewrite_producer_raw=True,Optimize=0,Native_load=0))
    sources=[]
    for p,h in m['source_hashes'].items():
        actual=(ROOT/p).read_bytes();assert hashlib.sha256(actual).hexdigest()==h
        blob=git('show',m['source_commit']+':'+p)
        assert blob.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),p
        sources.append(dict(path=p,SHA256=h,bytes=len(actual),measured_commit=m['source_commit'],Git_blob_SHA256=hashlib.sha256(blob).hexdigest(),
            actual_compiler_bytes_in_source_carrier=True,Git_semantics_equal_modulo_registered_EOL=True))
    write(OUT/'source_publication.json',dict(measured_production_commit=m['source_commit'],PE_SHA256=m['production_PE_SHA'],sources=sources,
        measured_command=m['link_command'],object_and_archive_lineage_manifest_SHA=sha(OUT/'candidate_manifest.json'),
        CMake_recipe_SHA=sha(ROOT/'CMakeLists.txt'),CMake_link_correction_changes_no_measured_PE=True,Optimize=0,Native_load=0))
    assets={}
    for name,p in [('production',Path(m['production_PE'])),('Native_DLL',DLL),('LP_python',LP_PYTHON),('process_python',PYTHON),
        ('figure_python',Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')),
        ('compiler',Path('D:/msys64/ucrt64/bin/g++.exe'))]:
        assets[name]=dict(path=str(p),SHA256=sha(p),bytes=p.stat().st_size)
    write(OUT/'software_bindings.json',dict(UTC=utc(),task_date='2026-11-01',timezone='Asia/Shanghai',assets=assets,
        Seed=0,H_seed=20260626,Threads=1,affinity_mask=4,global_settings_changed=False,Optimize=0,Native_load=0))
    print('Finite source/compiler bytes and actual frozen helper versions bound; no Native/Optimize')
if __name__=='__main__':main()
