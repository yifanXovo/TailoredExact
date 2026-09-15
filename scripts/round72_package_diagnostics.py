"""Archive and audit the completed UB-only diagnostic prefix."""
import csv,gzip,json
import round72_startup_diagnostic as diag
base=diag.base;OUT=diag.OUT;ROOT=diag.ROOT

def main():
    base.bind();base.run.assert_frozen();assert not (OUT/'active_run.lock').exists()
    identity=diag.read(OUT/'diagnostic_identity.json')
    assert base.run.sha(diag.__file__)==identity['driver_sha256']
    assert base.run.sha(OUT/'plan.md')==identity['plan_sha256']
    entries=[json.loads(line) for line in (OUT/'diagnostic_processes.jsonl').read_text().splitlines()]
    assert len(entries)==6
    manifest=[];checks=[];pairs=[]
    for entry in entries:
        folder=ROOT/entry['destination'];r=diag.read(folder/'result.json');n=entry['number']
        assert r['certificate_scope']=='primal_heuristic_ub_only' and r['method']=='primal-heuristic'
        assert not r['strict_certified_original_problem'] and not (folder/'external').exists()
        physical=base.audit.physical_module.physical(entry['input'],r)
        assert physical['original_T_feasible'] and abs(physical['F']-r['upper_bound'])<=1e-7
        trace=base.audit.rows(folder/'hga.csv.descent.csv');exhausted=[];previous_time=0
        assert len(trace)==r['decoded_descent_passes']
        for index,row in enumerate(trace,1):
            assert int(row['pass'])==index and 1<=int(row['seed'])<=24
            count=int(row['decoded_checks']);neighbors=int(row['neighbors'])
            cross=int(row['cross_route_checks']);generated=int(row['cross_route_neighbors'])
            assert 0<=cross<=generated<=neighbors and cross<=count<=neighbors
            before=float(row['fitness_before']);after=float(row['fitness_after'])
            accepted=row['accepted']=='1';terminal=row['exhausted']=='1'
            assert row['interrupted']=='0'
            if accepted:assert after>before+1e-12 and not terminal
            else:assert after==before
            if row['accepted_cross_route']=='1':assert accepted and cross>0
            if terminal:
                assert count==neighbors and cross==generated;exhausted.append(int(row['seed']))
            assert float(row['elapsed_seconds'])>=previous_time;previous_time=float(row['elapsed_seconds'])
        assert exhausted==list(range(1,25)) and r['decoded_descent_complete']
        for field,column in [('checks','decoded_checks'),('cross_route_neighbors','cross_route_neighbors'),('cross_route_checks','cross_route_checks'),('cross_route_moves','accepted_cross_route')]:
            assert sum(int(row[column]) for row in trace)==r['decoded_descent_'+field]
        if entry['arm']=='DS':assert r['decoded_descent_cross_route_checks']==r['decoded_descent_cross_route_moves']==r['decoded_descent_cross_route_neighbors']==0
        digest=base.route_hash(r)
        events=base.audit.rows(folder/'hga_events.csv')
        linked=any(e['published']=='1' and e['verifier_passed']=='1' and e['content_sha256']==digest for e in events)
        assert linked and digest==r['hga_retained_candidate_sha256']
        witness={k:r[k] for k in ['routes','objective','upper_bound','G','P']}
        witness['final_inventories']=r['verification']['final_inventories']
        target=OUT/'witnesses'/f'{n}.json';diag.write(target,witness)
        checks.append(dict(number=n,id=entry['id'],arm=entry['arm'],physical=physical,
            full_route_sha256=digest,linked_verified_event=True,strict_terminal_trace_passed=True,
            witness_sha256=base.run.sha(target),passes=len(trace)))
        for name in ['launch.json','completion.json','affinity.json','phases.csv','heuristic.csv','hga_events.csv','hga.csv.descent.csv']:
            source=folder/name
            if not source.exists():continue
            dest=OUT/'evidence'/str(n)/(name+'.gz' if name.endswith('.csv') else name)
            dest.parent.mkdir(parents=True,exist_ok=True)
            raw=source.read_bytes();data=gzip.compress(raw,mtime=0) if dest.suffix=='.gz' else raw
            dest.write_bytes(data)
            assert (gzip.decompress(data) if dest.suffix=='.gz' else data)==raw
            manifest.append(dict(number=n,source=str(source.relative_to(ROOT)),artifact=str(dest.relative_to(OUT)),
                source_sha256=base.run.sha(source),sha256=base.run.sha(dest),bytes=len(data),lossless=True))
        keys=['method','status','certificate_scope','strict_certified_original_problem','objective','upper_bound']
        selected={k:v for k,v in r.items() if k in keys or k.startswith(('decoded_descent_','hga_'))}
        dest=OUT/'evidence'/str(n)/'result_summary.json';diag.write(dest,selected)
        assert all(value==r[key] for key,value in diag.read(dest).items())
        manifest.append(dict(number=n,source=str((folder/'result.json').relative_to(ROOT)),artifact=str(dest.relative_to(OUT)),
            source_sha256=base.run.sha(folder/'result.json'),sha256=base.run.sha(dest),bytes=dest.stat().st_size,lossless=False))
    data=diag.read(OUT/'diagnostic_results.json')
    for name in ['D3','C2','D4']:
        arms={row['arm']:row for row in data if row['id']==name};a,b=arms['DS'],arms['DS-X']
        pairs.append(dict(id=name,DS_initial_UB=a['UB'],DSX_initial_UB=b['UB'],UB_delta=b['UB']-a['UB'],
            DS_stations=a['physical']['stations'],DSX_stations=b['physical']['stations'],
            same_full_routes=a['initial_route_sha256']==b['initial_route_sha256'],
            cross_checks=b['cross_route_checks'],cross_moves=b['cross_route_moves'],
            scope='Startup objective attribution only; no inference about full exact performance'))
    diag.write(OUT/'diagnostic_checks.json',checks);diag.write(OUT/'diagnostic_pairs.json',pairs)
    diag.write(OUT/'diagnostic_evidence_manifest.json',manifest)
    diag.write(OUT/'diagnostic_audit.json',dict(completed=6,physical_and_trace_checks_passed=True,
        artifacts=len(manifest),compact_bytes=sum(e['bytes'] for e in manifest),optimizer_calls=0,
        script_sha256=base.run.sha(__file__),scope='Component-only checks; inherited C++ qualification, no new exact certification'))
    print(json.dumps(pairs,indent=2));print('Archived',len(manifest),'diagnostic artifacts')

if __name__=='__main__':main()
