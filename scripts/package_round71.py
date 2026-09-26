"""Reuse qualified audits, adding DS structure, affinity, traces and paired rows.

Every mutable legacy module binding is redirected to this stage. No optimizer
is launched, no old evidence is written, and generation clocks are not used.
"""
import gzip,hashlib,json,re
import package_round68 as shared
import round71_research as run
import round71_start_audit as starts
import analyze_round71 as audit
import round71_startup_deadline as startup_deadline

shared.analyze_round68=audit
mapping=shared.round67_witness_model_audit

def bind():
    shared.run=run;shared.round68_start_audit=starts
    audit.run=run;starts.run=run;starts.audit=audit
    mapping.run=run;mapping.audit.run=run
    audit.physical_module.ROOT=run.ROOT
    run.runner.ROOT=run.ROOT;run.runner.OUT=run.OUT;run.runner.RAW=run.RAW
    run.runner.BUILD=run.BUILD;run.runner.LEDGER=run.OUT/'processes.jsonl'

def route_hash(witness):
    parts=[]
    for route in sorted(witness['routes'],key=lambda r:r['vehicle']):
        operations=[(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else tuple(op) for op in route['operations']]
        parts.append('v='+str(route['vehicle'])+';nodes='+''.join(str(i)+',' for i in route['nodes'])+
            ';ops='+''.join(':'.join(map(str,op))+',' for op in sorted(operations))+'|')
    return hashlib.sha256(''.join(parts).encode('ascii')).hexdigest()

def extra_checks():
    checks=[];descent=[];provenance=[];versions=[];deadlines=[]
    for e in run.runner.entries():
        folder=run.ROOT/e['destination']
        if not (folder/'completion.json').exists():continue
        done=run.read(folder/'completion.json');aff=run.read(folder/'affinity.json')
        assert aff['child_readback']['process_mask']==aff['binding']['effective']['process_mask']==4
        assert done['restored_launcher']==aff['binding']['before']
        checks.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],child_mask=4,
            restored=True,affinity_sha256=run.sha(folder/'affinity.json')))
        if not e['charged']:continue
        assert done['returncode']==0 and not done['watchdog'] and done['within_budget']
        result=run.read(folder/'result.json')
        if startup_deadline.matches(result):
            deadlines.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],
                **startup_deadline.check(folder,run.panel()[e['id']],result,run,audit,route_hash)))
        native_logs=[folder/'native.log'] if e['arm']=='P-GRB' else [run.ROOT/c['native_log'] for c in audit.rows(folder/'external/paper_optimize_ledger.csv')]
        if e['arm']=='P-GRB':
            assert result['gurobi_version']==result['gurobi_header_version']=='13.0.2'
        for native_log in native_logs:
            with native_log.open(encoding='utf-8',errors='replace') as stream:header=stream.read(4096)
            match=re.search(r'Gurobi Optimizer version (\d+\.\d+\.\d+)\b',header)
            assert match and match.group(1)=='13.0.2',(native_log,match)
        versions.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],version='13.0.2',
            actual_native_logs_checked=len(native_logs),scope='Actual Optimize log headers; no claim of a frozen DLL hash'))
        witness=folder/'external/initial_witness.json'
        if e['arm']!='P-GRB' and witness.exists():
            physical=run.read(witness);digest=route_hash(physical)
            events=[r for r in audit.rows(folder/'hga_events.csv') if r['published']=='1' and r['verifier_passed']=='1' and r['content_sha256']==digest]
            linked=bool(events) and digest==result.get('hga_retained_candidate_sha256') and result.get('hga_retained_verified_event_candidate',False)
            if linked:assert abs(float(events[0]['objective'])-audit.physical_module.physical(run.panel()[e['id']],physical)['F'])<=1e-7
            provenance.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],linked=linked,
                full_route_sha256=digest,scope='Full-content initial witness publication only; no early-time inference from generation0'))
        if e['arm'] not in ['DS','DS-X']:continue
        expected_mode='decoded-descent-interroute' if e['arm']=='DS-X' else 'decoded-descent'
        assert result['hga_stop_mode']==expected_mode and result['hga_total_generations']==0
        assert result['decoded_descent_cross_route_enabled']==(e['arm']=='DS-X')
        assert not (folder/'hga.csv').exists(),'DS must not impersonate a generation trace'
        path=run.ROOT/result['decoded_descent_log_path']
        assert path==folder/'hga.csv.descent.csv'
        trace=audit.rows(path)
        assert len(trace)==result['decoded_descent_passes']
        assert sum(int(r['decoded_checks']) for r in trace)==result['decoded_descent_checks']
        assert sum(int(r['cross_route_neighbors']) for r in trace)==result['decoded_descent_cross_route_neighbors']
        assert sum(int(r['cross_route_checks']) for r in trace)==result['decoded_descent_cross_route_checks']
        assert sum(r['accepted_cross_route']=='1' for r in trace)==result['decoded_descent_cross_route_moves']
        if e['arm']=='DS':
            assert all(result[k]==0 for k in ['decoded_descent_cross_route_neighbors','decoded_descent_cross_route_checks','decoded_descent_cross_route_moves'])
        exhausted=[];last_time=0
        for number,r in enumerate(trace,1):
            assert int(r['pass'])==number and 1<=int(r['seed'])<=24
            assert 0<=int(r['decoded_checks'])<=int(r['neighbors'])
            assert 0<=int(r['cross_route_checks'])<=int(r['cross_route_neighbors'])<=int(r['neighbors'])
            assert int(r['cross_route_checks'])<=int(r['decoded_checks'])
            accepted=r['accepted']=='1';terminal=r['exhausted']=='1';interrupted=r['interrupted']=='1'
            before=float(r['fitness_before']);after=float(r['fitness_after'])
            assert float(r['elapsed_seconds'])>=last_time;last_time=float(r['elapsed_seconds'])
            if accepted:assert after>before+1e-12 and not terminal and not interrupted
            else:assert after==before
            if r['accepted_cross_route']=='1':assert accepted and int(r['cross_route_checks'])>0
            if terminal:
                assert r['decoded_checks']==r['neighbors'] and not interrupted
                assert r['cross_route_checks']==r['cross_route_neighbors']
                exhausted.append(int(r['seed']))
            if interrupted:assert number==len(trace)
        completed=int(result['decoded_descent_seeds_completed'])
        # A deadline can arrive just after a terminal pass was recorded and
        # before the completed-seed counter is incremented. Never infer more.
        assert completed<=len(exhausted)<=completed+1
        if result['decoded_descent_complete']:
            assert completed==24 and exhausted==list(range(1,25))
        for model in folder.glob('external/**/*.lp'):
            text=model.read_text();general=text.partition('Generals\n')[2].partition('Binaries\n')[0]
            binary=text.partition('Binaries\n')[2].partition('End')[0]
            assert 'state_g_' in text and 'bit_' not in text and 'state_code_' not in text
            assert 'r64_q_balance_' not in text and 'r63f_' not in text
            assert re.search(r'(?m)^\s*load_\d+_\d+\s*$',general)
            assert re.search(r'(?m)^\s*state_\d+_\d+\s*$',binary)
        descent.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],complete=result['decoded_descent_complete'],
            completed_seeds=completed,passes=len(trace),decoded_checks=result['decoded_descent_checks'],
            cross_route_neighbors=result['decoded_descent_cross_route_neighbors'],
            cross_route_checks=result['decoded_descent_cross_route_checks'],cross_route_moves=result['decoded_descent_cross_route_moves'],
            trace_sha256=run.sha(path),strict_descent_and_terminal_checks=True))
    run.write(run.OUT/'affinity_checks.json',checks)
    run.write(run.OUT/'descent_checks.json',descent)
    run.write(run.OUT/'witness_event_provenance.json',provenance)
    run.write(run.OUT/'native_version_checks.json',versions)
    run.write(run.OUT/'startup_deadline_checks.json',deadlines)

def primary_pairs():
    records=audit.rows(run.OUT/'runs.csv');pairs=[]
    for r in records:
        for name in ['wall','UB','LB','signed_absolute_gap']:r[name]=float(r[name])
        r['certificate']=r['certificate']=='True'
    for c in records:
        if c['arm'] not in ['DS-X','DS'] or c['kind']!='performance':continue
        for b in records:
            references=['P-GRB','DS','K1-R'] if c['arm']=='DS-X' else ['P-GRB','K1-R']
            if b['id']!=c['id'] or b['cap']!=c['cap'] or b['stage']!=c['stage'] or b['arm'] not in references:continue
            pairs.append(dict(id=c['id'],cap=c['cap'],candidate_arm=c['arm'],candidate_number=c['number'],
                reference_number=b['number'],reference=b['arm'],candidate_certificate=c['certificate'],reference_certificate=b['certificate'],
                wall_delta=c['wall']-b['wall'],UB_delta=c['UB']-b['UB'],LB_delta=c['LB']-b['LB'],
                signed_gap_delta=c['signed_absolute_gap']-b['signed_absolute_gap'],
                paired_build=c['executable_sha256']==b['executable_sha256'],uniform_affinity_mask=4,
                same_paid_initial_routes=c['initial_route_signature']==b['initial_route_signature'] if b['arm']!='P-GRB' else None,
                practical_classification=audit.practical_classification(c,b),
                bound_tradeoff='mixed' if (c['UB']-b['UB'])*(c['LB']-b['LB'])>1e-14 else 'aligned_or_unchanged'))
    # Micros remain correctness evidence, never performance pairs.
    if pairs:audit.table('pairs.csv',pairs)
    else:(run.OUT/'pairs.csv').write_text('id,candidate_arm,reference,practical_classification\n',encoding='utf-8')

def main():
    bind();run.assert_frozen();shared.main();extra_checks();primary_pairs()
    manifest=run.read(run.OUT/'evidence_manifest.json')
    for e in run.runner.entries():
        source=run.ROOT/e['destination']
        if not e['charged'] or not (source/'completion.json').exists():continue
        destination=run.OUT/'evidence'/str(e['charged_number'])
        for name in ['affinity.json','hga.csv','hga.csv.descent.csv']:
            original=source/name
            if not original.exists():continue
            dest=destination/(name+'.gz' if name.endswith('.csv') else name)
            dest.write_bytes(gzip.compress(original.read_bytes(),mtime=0) if name.endswith('.csv') else original.read_bytes())
            assert (gzip.decompress(dest.read_bytes()) if name.endswith('.csv') else dest.read_bytes())==original.read_bytes()
            manifest.append(dict(number=e['charged_number'],artifact=str(dest.relative_to(run.OUT)),source=str(original.relative_to(run.ROOT)),
                source_sha256=run.sha(original),sha256=run.sha(dest),bytes=dest.stat().st_size))
        summary=destination/'result_summary.json';data=run.read(summary);raw=run.read(source/'result.json')
        data.update({k:v for k,v in raw.items() if k.startswith('decoded_descent_')});run.write(summary,data)
        next(m for m in manifest if m['artifact']==str(summary.relative_to(run.OUT)))['sha256']=run.sha(summary)
    run.write(run.OUT/'evidence_manifest.json',manifest)
    identity=run.read(run.OUT/'analysis_identity.json')
    qualification=run.read(run.OUT/'qualification.json')
    identity.update(round71_binding_and_extra_audits=run.sha(__file__),actual_start_audit=run.sha(starts.__file__),
        inherited_packaging=identity['packaging'],reproduction=run.sha(run.ROOT/'scripts/round71_reproduce.py'),
        reproduction_scope='Fresh bounded same-byte helper; not invoked as an extra campaign run',
        light_endpoint=run.sha(run.ROOT/'scripts/round71_endpoint.py'),
        startup_deadline_audit=run.sha(startup_deadline.__file__),
        inherited_analysis_reference=run.sha(run.ROOT/'scripts/analyze_round68.py'),
        startup_attribution=run.sha(run.ROOT/'scripts/round71_startup_analysis.py'),
        qualification_scope='49 inherited tests; no new execution' if qualification.get('inherited_ctest_tests') else '49 newly executed tests; prior affinity API qualification is inherited')
    run.write(run.OUT/'analysis_identity.json',identity)
    run.write(run.OUT/'source_snapshot.json',run.read(run.OUT/'build_v1.json')['source'])
    resource=run.read(run.OUT/'resource_status.json')
    incidents=run.OUT/'supervisor_postcondition_failures.json'
    resource.update(valid_startup_deadline_runs=len(run.read(run.OUT/'startup_deadline_checks.json')),
        supervisor_postcondition_failures=len(run.read(incidents)) if incidents.exists() else 0)
    run.write(run.OUT/'resource_status.json',resource)
    print('Round71 compact artifacts',len(manifest),'including uniform affinity and separate DS traces')

if __name__=='__main__':main()
