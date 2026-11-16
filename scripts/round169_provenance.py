"""Bounded old-member recovery, C++ reevaluation, and read-only time attribution."""
from round169_common import *
from round169_run import launch, result
import collections, re
def main():
    records=read(ROOT/'results/unified_exact_round166/review/data_physical_archive.json')['records']
    groups=read(ROOT/'results/unified_exact_round137/matrix_frozen.json')['groups']
    original_lambda=.0754049775127276;rows=[];members=[];first_hit={}
    def revalue(fleet,folder,input_path,T,lam):
        cmd=[str(PE),'--input',str(input_path),'--lambda',format(lam,'.17g'),'--T',str(T),
            '--pickup-time','60','--drop-time','60','--method','incumbent-import-test',
            '--external-incumbent',str(fleet),'--external-incumbent-format','route_json',
            '--out',str(folder/'result.json'),'--time-limit','10','--process-wall-time-limit','10','--process-shutdown-margin','1']
        if not (folder/'completion.json').exists():launch(cmd,folder,12)
        r=result(folder/'result.json');assert r['incumbent_import_verified'],r.get('incumbent_import_errors')
        return {k:r[k] for k in ['objective','G','P','routes']}
    for rid in ['R137:B3:68','R137:B2:59','R137:B3:71']:
        r=next(x for x in records if x['record_id']==rid);s=r['source'];archive=ROOT/s['archive'];assert sha(archive)==s['archive_SHA']
        group=next(x for x in groups if x['position']==r['position']);assert group['arm_id']==r['original']['arm_id']
        z=zipfile.ZipFile(archive);pre=s['member_prefix']+'/'
        def member(leaf):
            raw=z.read(pre+leaf);members.append(dict(archive=s['archive'],archive_SHA256=s['archive_SHA'],member=pre+leaf,
                bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()));return raw
        h=json.loads(member('external/initial_witness.json'));audit=json.loads(member('audit.json'))
        assert audit['passed'] and audit['full_H'];dest=OUT/'provenance_old_members'/f"{r['position']:03}"
        dest.mkdir(parents=True,exist_ok=True);write(dest/'fleet.json',dict(routes=h['routes']))
        v=revalue(dest/'fleet.json',OUT/'provenance_revalue'/str(r['position']),ROOT/s['input_path'],6300,original_lambda)
        rows.append(dict(record_id=rid,rho=r['original']['rho'],arm=group['arm_id'],search_lambda=r['original']['lambda_value'],
            evaluation_lambda=original_lambda,H_search_reported_F=h['objective'],H_original_reverified={k:v[k] for k in ['objective','G','P']},
            full_H_audit=audit['full_H'],source=s,no_new_run_Start=True))
        if rid.endswith(':71'):
            final=json.loads(member('result.json'))
            events=[]
            for n in z.namelist():
                if n.startswith(pre+'journal/event_') and n.endswith('.json'):
                    d=json.loads(z.read(n));events.append((n,d))
            events.sort(key=lambda nd:nd[1]['sequence'])
            witnesses=[(n,d) for n,d in events if d['kind']=='witness' and abs(d['objective']-final['objective'])<1e-10]
            assert witnesses;name,event=witnesses[0];member(name[len(pre):])
            assert event['routes']==final['routes']
            commit_leaf=name[len(pre):].removesuffix('.json')+'.commit'
            fields=member(commit_leaf).decode('ascii').split()
            assert fields[:2]==['NEJ1',str(event['sequence'])]
            assert int(fields[3])==len(z.read(name)) and fields[4]==hashlib.sha256(z.read(name)).hexdigest()
            observed=next(x for x in json.loads(member('observations.json')) if x['sequence']==event['sequence'])
            assert observed['sha256']==fields[4] and observed['data_close_seconds']==float(fields[2])
            callname,call=next((n,d) for n,d in events if d['kind']=='call' and d['call']==event['call']);member(callname[len(pre):])
            logleaf=call['native_log_path'].replace('\\','/').split('/raw/'+r['original']['arm_id']+'/')[1]
            log=member(logleaf).decode();matches=[line.strip() for line in log.splitlines() if re.search(r'0\.5245528',line)]
            trace=list(csv.DictReader(io.StringIO(member('external/global_bound_trace.csv').decode())))
            accepted=next(x for x in trace if abs(float(x['verified_global_upper_bound'])-final['objective'])<1e-9)
            first_hit=dict(final_F_search=final['objective'],first_exact_final_fleet_witness_member=name,sequence=event['sequence'],
                call=event['call'],source=event['source'],call_native_log=logleaf,call_is_terminal_mip='terminal_mip' in logleaf,
                witness_JSON_has_timestamp=False,commit_sidecar_has_process_timestamp=True,
                first_verified_witness_producer_publication_marker_seconds=float(fields[2]),
                first_external_observation_process_seconds=observed['first_observed_seconds'],
                first_recorded_effective_availability_seconds=observed['effective_available_seconds'],
                commit_member=pre+commit_leaf,precise_internal_solver_discovery_seconds=None,
                rounded_native_incumbent_log_lines=matches,rounded_native_solve_seconds=2298,
                first_outer_acceptance_ledger=accepted,
                timing_scope='The validated C++ NEJ1 sidecar records a producer publication/close marker sampled after JSON close/hash and before commit-sidecar writing. External observation records actual external availability. Neither is the unrecorded internal solver discovery instant; outer-store acceptance is after return.',
                producer_endpoint_not_used_as_first_hit=True)
    fixture=ROOT/'tests/data/round59_tiny.txt'
    for name,routes in [('loaded_return',[dict(vehicle=0,nodes=[0,1,0],operations=[dict(station=1,pickup=1,drop=0)])]),('empty',[])]:
        d=OUT/'qualification'/name;d.mkdir(parents=True,exist_ok=True);write(d/'fleet.json',dict(routes=routes))
        v=revalue(d/'fleet.json',d/'cpp_check',fixture,3600,.15)
        write(d/'expected_readback.json',dict(CPP=v,expected_G=2/15 if name=='loaded_return' else 2/9,
            loaded_return_unloading_seconds=60 if name=='loaded_return' else 0,Optimize=0))
        if name=='loaded_return':assert abs(v['G']-2/15)<1e-13 and abs(v['P']-.5)<1e-13
    write(OUT/'weight_provenance.json',dict(UTC=utc(),rows=rows,members=members,final_first_hit=first_hit,
        original_input_SHA256=rows[0]['source']['input_SHA'],old_fleets_analysis_only=True,Optimize=0,
        no_download_required=True,provenance_member_copies_excluded_from_new_raw_carrier=True))
    print(json.dumps(dict(H=[(r['record_id'],r['H_original_reverified']) for r in rows],first_hit=first_hit),indent=2),flush=True)
if __name__=='__main__':main()
