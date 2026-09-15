"""Lossless startup evidence, per-prefix physical replay and revision costs."""
import csv
import gzip
import json
import time
import round73_startup_diagnostic as diag
from round73_qualify import ROOT, OUT, sha, write


def main():
    started=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    identity=diag.read(OUT/'diagnostic_identity.json')
    assert sha(diag.__file__)==identity['driver_sha256']
    assert sha(OUT/'plan.md')==identity['plan_sha256']
    for name,digest in identity['source'].items():assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'build/round73/v3/ExactEBRP.exe')==identity['binary_sha256']
    entries=[json.loads(line) for line in (OUT/'diagnostic_processes.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(entries)==10
    manifest=[];checks=[];diag.physical_module.ROOT=ROOT
    def archive(source,target):
        target.parent.mkdir(parents=True,exist_ok=True)
        raw=source.read_bytes();encoded=gzip.compress(raw,mtime=0)
        if target.exists():assert gzip.decompress(target.read_bytes())==raw
        else:target.write_bytes(encoded)
        assert gzip.decompress(target.read_bytes())==raw
        manifest.append(dict(source=str(source.relative_to(ROOT)),artifact=str(target.relative_to(OUT)),
            source_sha256=sha(source),sha256=sha(target),original_bytes=len(raw),compact_bytes=target.stat().st_size))
    for entry in entries:
        folder=ROOT/entry['destination'];p=entry['input'];r=diag.read(folder/'result.json')
        c=diag.read(folder/'completion.json');assert c['returncode']==0 and c['within_cap'] and not c['watchdog']
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        assert r['certificate_scope']=='primal_heuristic_ub_only' and not r['strict_certified_original_problem']
        checked=diag.physical_module.physical(p,dict(r,inventory=r['verification']['final_inventories']))
        assert checked['original_T_feasible']
        if entry['arm']=='JI':detail=diag.replay_joint(p,folder,r)
        else:
            trace=list(csv.DictReader((folder/'hga.csv.descent.csv').open(encoding='utf-8')))
            assert [int(row['seed']) for row in trace if row['exhausted']=='1']==list(range(1,25))
            for row in trace:
                assert row['interrupted']=='0'
                if row['exhausted']=='1':assert row['decoded_checks']==row['neighbors'] and row['cross_route_checks']==row['cross_route_neighbors']
            detail=dict(terminal_seeds=24,passes=len(trace),terminal_neighborhoods_complete=True)
        checks.append(dict(number=entry['number'],id=p['id'],arm=entry['arm'],physical=checked,
            route_sha256=diag.route_hash(r),detail=detail))
        for source in sorted(folder.rglob('*')):
            if source.is_file():archive(source,OUT/'startup_evidence'/str(entry['number'])/(str(source.relative_to(folder))+'.gz'))
    build=ROOT/'build/round73/v3'
    for name in ['configure.log','build.log','tests.log']:
        archive(build/name,OUT/'qualification_evidence/v3'/(name+'.gz'))
    cli=list(build.glob('round73_cli*'));assert len(cli)==1
    for source in sorted(cli[0].rglob('*')):
        if source.is_file():archive(source,OUT/'qualification_evidence/v3/native_ji'/(str(source.relative_to(cli[0]))+'.gz'))
    rows=diag.read(OUT/'diagnostic_results.json');pairs=[]
    for role in ['D3','C2','D4','D6','D7']:
        a,b=[next(r for r in rows if r['id']==role and r['arm']==arm) for arm in ['DS-X','JI']]
        pairs.append(dict(id=role,DSX_UB=a['UB'],JI_UB=b['UB'],UB_delta=b['UB']-a['UB'],
            DSX_wall=a['wall'],JI_wall=b['wall'],DSX_stations=a['physical']['stations'],JI_stations=b['physical']['stations'],
            scope='UB-only component attribution, not full-proof performance'))
    write(OUT/'startup_pairs.json',pairs);write(OUT/'startup_checks.json',checks);write(OUT/'startup_manifest.json',manifest)
    q=[diag.read(OUT/f'qualification_v{i}.json') for i in [1,2,3]]
    qualification_wall=sum(a['wall_seconds'] for item in q for a in item['attempts'])
    write(OUT/'resource_summary.json',dict(startup_launches=10,startup_wall_seconds=sum(r['wall'] for r in rows),
        startup_optimize_calls=0,qualification_batches=3,failed_qualification_batches=2,
        latest_passed_tests=51,qualification_native_calls=135,qualification_wall_seconds=qualification_wall,
        standalone_native_persistence_diagnostics=0,formal_performance_launches=0,
        maximum_new_experiment_reserve='Six native persistence diagnoses <=30s each; no formal panel or second startup tranche opened',
        scope='Every executed revision and diagnosis counted; no inherited tests counted as fresh'))
    audit=dict(completed_startup_diagnoses=10,physical_and_trace_checks_passed=True,
        artifacts=len(manifest),original_bytes=sum(e['original_bytes'] for e in manifest),
        compact_bytes=sum(e['compact_bytes'] for e in manifest),all_lossless_content_hashes_passed=True,
        all_source_and_input_bindings_passed=True,optimizer_calls=0,wall_seconds=time.perf_counter()-started,
        script_sha256=sha(__file__),scope='Initial tranche audit; no full-proof performance or stage-completion claim')
    write(OUT/'startup_audit.json',audit);print(json.dumps(dict(pairs=pairs,audit=audit),indent=2))

if __name__=='__main__':main()
