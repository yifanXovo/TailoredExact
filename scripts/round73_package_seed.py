"""Audit the second startup tranche without changing the first checkpoint."""
import csv
import gzip
import json
import time
import round73_seed_diagnostic as diag
from round73_qualify import ROOT, OUT as STAGE, sha, write
OUT=diag.OUT

def rows(path):
    return list(csv.DictReader(path.open(encoding='utf-8')))

def main():
    started=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    identity=diag.read(OUT/'diagnostic_identity.json')
    assert sha(diag.__file__)==identity['driver_sha256']
    assert sha(OUT/'plan.md')==identity['plan_sha256']==sha(STAGE/'seed_extension.md')
    for name,digest in identity['source'].items():assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'build/round73/v4/ExactEBRP.exe')==identity['binary_sha256']
    entries=[json.loads(line) for line in (OUT/'diagnostic_processes.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(entries)==10;manifest=[];checks=[];diag.physical_module.ROOT=ROOT
    def archive(source,target):
        target.parent.mkdir(parents=True,exist_ok=True);raw=source.read_bytes()
        if target.exists():assert gzip.decompress(target.read_bytes())==raw
        else:target.write_bytes(gzip.compress(raw,mtime=0))
        assert gzip.decompress(target.read_bytes())==raw
        manifest.append(dict(source=str(source.relative_to(ROOT)),artifact=str(target.relative_to(OUT)),
            source_sha256=sha(source),sha256=sha(target),original_bytes=len(raw),compact_bytes=target.stat().st_size))
    for entry in entries:
        folder=ROOT/entry['destination'];p=entry['input'];r=diag.read(folder/'result.json')
        done=diag.read(folder/'completion.json');assert done['returncode']==0 and done['within_cap'] and not done['watchdog']
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        checked=diag.physical_module.physical(p,dict(r,inventory=r['verification']['final_inventories']))
        assert checked['original_T_feasible'] and r['certificate_scope']=='primal_heuristic_ub_only'
        assert not r['strict_certified_original_problem'] and r['hga_total_generations']==0
        trace=rows(folder/'hga.csv.descent.csv');count=24 if entry['arm']=='DS-X' else 25
        assert [int(row['seed']) for row in trace if row['exhausted']=='1']==list(range(1,count+1))
        assert r['decoded_descent_complete'] and r['decoded_descent_seeds_completed']==count
        for row in trace:
            assert row['interrupted']=='0'
            if row['exhausted']=='1':assert row['decoded_checks']==row['neighbors'] and row['cross_route_checks']==row['cross_route_neighbors']
        detail=dict(completed_seeds=count,all_terminal_neighborhoods_checked=True)
        if count==25:
            witness=diag.read(folder/'replayed_constructive_witness.json')
            detail.update(diag.replay_joint(p,folder,witness))
            baseline=rows(OUT/'local_raw'/p['id']/'DS-X/hga.csv.descent.csv')
            logical=lambda row:{k:v for k,v in row.items() if k!='elapsed_seconds'}
            assert list(map(logical,baseline))==[logical(row) for row in trace if int(row['seed'])<=24]
            old=diag.read(STAGE/'local_raw'/p['id']/'JI/result.json')
            assert diag.route_hash(witness)==diag.route_hash(old)
            detail.update(first24_logical_paths_equal=True,constructive_route_matches_initial_tranche=True,
                extra_seed_checks=sum(int(row['decoded_checks']) for row in trace if row['seed']=='25'),
                extra_seed_moves=sum(int(row['accepted']) for row in trace if row['seed']=='25'))
        checks.append(dict(number=entry['number'],id=p['id'],arm=entry['arm'],physical=checked,
            route_sha256=diag.route_hash(r),detail=detail))
        for source in sorted(folder.rglob('*')):
            if source.is_file():archive(source,OUT/'evidence'/str(entry['number'])/(str(source.relative_to(folder))+'.gz'))
    build=ROOT/'build/round73/v4'
    for name in ['configure.log','build.log','tests.log']:archive(build/name,OUT/'qualification_evidence'/(name+'.gz'))
    cli=list(build.glob('round73_seed_cli*'));assert len(cli)==1
    for source in sorted(cli[0].rglob('*')):
        if source.is_file():archive(source,OUT/'qualification_evidence/native_seeded'/(str(source.relative_to(cli[0]))+'.gz'))
    data=diag.read(OUT/'diagnostic_results.json');pairs=[]
    for role in ['D3','C2','D4','D6','D7']:
        a,b=[next(r for r in data if r['id']==role and r['arm']==arm) for arm in ['DS-X','JDS-X']]
        pairs.append(dict(id=role,DSX_UB=a['UB'],JDSX_UB=b['UB'],UB_delta=b['UB']-a['UB'],
            DSX_wall=a['wall'],JDSX_wall=b['wall'],wall_delta=b['wall']-a['wall'],
            extra_seed_checks=b['detail']['extra_seed_checks'],extra_seed_moves=b['detail']['extra_seed_moves'],
            scope='Paid startup attribution only; not a full-proof comparison'))
    write(OUT/'pairs.json',pairs);write(OUT/'checks.json',checks);write(OUT/'evidence_manifest.json',manifest)
    audit=dict(completed=10,all_source_input_and_artifact_checks_passed=True,
        all_prefix_physical_and_terminal_trace_checks_passed=True,first24_paths_preserved_on_all5_roles=True,
        artifacts=len(manifest),compact_bytes=sum(e['compact_bytes'] for e in manifest),
        original_bytes=sum(e['original_bytes'] for e in manifest),optimizer_calls=0,
        wall_seconds=time.perf_counter()-started,script_sha256=sha(__file__))
    write(OUT/'audit.json',audit)
    before=diag.read(STAGE/'resource_summary.json')
    qualification=diag.read(STAGE/'qualification_v4.json')
    resource=dict(initial_tranche=before,seed_tranche_launches=10,seed_tranche_wall_seconds=sum(r['wall'] for r in data),
        total_startup_launches=20,total_startup_wall_seconds=before['startup_wall_seconds']+sum(r['wall'] for r in data),
        total_startup_optimize_calls=0,total_qualification_batches=4,failed_qualification_batches=2,
        latest_passed_tests=53,total_qualification_native_calls=210,
        total_qualification_wall_seconds=before['qualification_wall_seconds']+sum(a['wall_seconds'] for a in qualification['attempts']),
        standalone_native_persistence_diagnostics=0,formal_performance_launches=0,
        stage_complete=False,scope='Both startup tranches and all qualification attempts counted; no formal or long panel opened')
    write(STAGE/'combined_resource_summary.json',resource)
    print(json.dumps(dict(pairs=pairs,audit=audit,resources=resource),indent=2))

if __name__=='__main__':main()
