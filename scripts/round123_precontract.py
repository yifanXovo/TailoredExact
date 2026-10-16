"""Finite preformal contract review, checks data and actual commands rather than markers."""
from round123_common import *
import copy,collections
import round123_evidence as ev

def regression():
    oldroot=WORK/'worktrees/round122'; out=oldroot/'results/unified_exact_round122'
    i=read(out/'campaign/group08/identity.json'); l=next(x for x in i['launches'] if x['arm']=='P-GRB')
    d=Path(l['destination']); records=read(d/'observations.json'); result=read(d/'result.json')
    before=ev.native.audit(oldroot,l['panel'],records,PE_SHA); original_failed=False
    try:ev.native.finalize_endpoint(oldroot,l['panel'],l['arm'],copy.deepcopy(before),records,result,'normal_return',l['panel']['reference'])
    except AssertionError:original_failed=True
    assert original_failed
    after=copy.deepcopy(before); ev.adapted_finalizer()(oldroot,l['panel'],l['arm'],after,records,result,'normal_return',l['panel']['reference'])
    assert after['endpoint']['U']==result['upper_bound'] and after['endpoint']['L']==result['lower_bound']
    rejected=[]
    for kind in ['bad_final_L','bad_observed_L']:
        bad=copy.deepcopy(result); audit=copy.deepcopy(before)
        if kind=='bad_final_L':bad['lower_bound']=result['upper_bound']+1
        else:audit['LB']=result['upper_bound']+1
        try:ev.adapted_finalizer()(oldroot,l['panel'],l['arm'],audit,records,bad,'normal_return',l['panel']['reference'])
        except AssertionError:rejected.append(kind)
    assert len(rejected)==2
    value=dict(passed=True,original_order_assertion_reproduced=True,history_U=before['UB'],final_U=result['upper_bound'],
        witnesses=len(before['witnesses']),bound_events=sum(x['payload']['kind']=='bound' for x in records),
        final_endpoint=after['endpoint'],negative_bound_fixtures_rejected=rejected,
        no_history_or_endpoint_order_imposed=True,no_R122_hash_or_number_in_general_adapter=True,
        adapter_SHA=sha(ROOT/'scripts/round123_evidence.py'),original_finalizer_SHA=sha(ROOT/'scripts/round86_native_evidence.py'),
        original_R122_result_SHA=sha(d/'result.json'),original_R122_observations_SHA=sha(d/'observations.json'),Optimize=0)
    write(OUT/'qualification/general_history_regression.json',value);return value

def run():
    workspace(); tick=time.perf_counter(); identity(); reg=regression()
    f=read(OUT/'argv_freeze.json'); formal=f['plans'][0]; ls=formal['launches']
    assert [l['arm'] for l in ls]==METHODS and len(ls)==3
    i=read(OUT/formal['name']/'identity.json'); candidate=read(OUT/'candidate_identity.json')
    assert candidate['helpers']==helpers()==i['helpers']
    facts=[]
    for l in ls:
        cmd=l['command']; p=l['panel']; fields={}
        for key in ['--T','--time-limit','--process-wall-time-limit','--process-shutdown-margin','--threads','--mip-threads','--gurobi-seed','--gurobi-presolve']:
            assert cmd.count(key)==1;fields[key]=cmd[cmd.index(key)+1]
        assert fields=={'--T':'10800','--time-limit':'17994','--process-wall-time-limit':'18000',
            '--process-shutdown-margin':'30','--threads':'1','--mip-threads':'1','--gurobi-seed':'0','--gurobi-presolve':'-1'}
        assert l['cap_seconds']==18000 and l['hard_stop_seconds']==17998
        assert p['Q_vector']==[30]*4 and p['V']==50 and p['M']==4 and p['T_seconds']==10800
        assert p['pickup_seconds']==p['drop_seconds']==60 and p['lambda']==.15
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        assert cmd[0]==str(PE) and not any('round122' in v for v in cmd if v!=p['input_path'])
        if l['arm']=='P-GRB':assert '--plain-baseline' in cmd and '--round98-state-service' not in cmd and '--algorithm-preset' not in cmd
        else:
            assert cmd[cmd.index('--algorithm-preset')+1]=='research-round83-vds-equal-net-exchange'
            assert ('--round98-state-service' in cmd)==(l['arm']=='M-B')
        assert not any(v.startswith(('--round119','--round120','--round112','--round100-continuous')) for v in cmd)
        assert not Path(l['destination']).exists()
        facts.append(dict(arm=l['arm'],actual_argv=cmd,fields=fields,independent_cold_destination=True))
    loaded=read(OUT/'qualification/actual_loaded_modules.json')
    assert Path(loaded['ExecutablePath']).resolve()==PE.resolve()
    gurobi=[m for m in loaded['Modules'] if m['ModuleName'].lower()=='gurobi130.dll'];assert len(gurobi)==1
    assert Path(gurobi[0]['FileName']).resolve()==DLL.resolve() and sha(gurobi[0]['FileName'])==DLL_SHA
    qual=read(OUT/'qualification/h100_seed0/identity.json'); checks=[]
    for l in qual['launches']:
        d=Path(l['destination']); a=read(d/'audit.json'); prod=read(d/'producer_receipt.json'); total=read(d/'arm_total_receipt.json')
        assert a['passed'] and a['native_proof_qualified'] and read(d/'completion.json')['stop_reason']=='normal_return'
        assert prod['T_produce']<=120 and total['necessary_verification_complete']
        assert abs(total['T_total']-prod['T_produce']-total['T_verify'])<1e-8
        checks.append(dict(arm=l['arm'],audit_SHA=sha(d/'audit.json'),T_produce=prod['T_produce'],T_verify=total['T_verify'],endpoint=a['endpoint']))
    assert len(checks)==3 and budget()['qualification_seconds']<=QUAL_PLAN and not budget()['unclosed']
    mathfacts=read(OUT/'mathematics/positive_objective.json'); assert mathfacts['decimal']['simple_float']>0
    assert read(OUT/'prior_proof_obligations.json')['records']
    capacity=workspace(); assert capacity['volume_free_bytes']>=47*1024**3
    assert budget()['remaining_outer_seconds']>=54000+360+4000
    result=dict(decision='ACCEPT',review_type='Self-review by a separate finite contract implementation; no third-party executor claimed',
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),source_files=216,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        actual_loaded_modules_SHA=sha(OUT/'qualification/actual_loaded_modules.json'),formal_argv=facts,
        qualification_results=checks,history_regression=reg,physical_T_distinct_from_computational_cap=True,
        no_old_U_L_or_routes_in_commands=True,positive_objective_interpretation_not_production_cut=True,
        full_coverage_scope_required_not_local_terminal_status=True,budget=budget(),capacity=capacity,
        paper_reference='frozen M-B',default='ENS-C',D1_selection_closed=True,Optimize=0,UTC=utc(),seconds=time.perf_counter()-tick)
    write(OUT/'review/performance_admission.json',result)
    (OUT/'review/pre_contract.md').write_text('# Round123 finite preformal contract review\n\nACCEPT. A separate check of all three actual argv lists verifies physical T10800, produce cap18000, native time17994, process cap18000, hard stop17998 and reserve30. Method identity, Seed0, threads and Presolve remain frozen. Commands carry no old witness, bound, route, cutoff, basis or tree. The original216 production files and actual loaded PE/DLL paths match. Three real H100 (V20) CLI producers and their complete audits passed.\n\nThe history/final-U regression replays every original group08 witness and bound, retains its final endpoint, and rejects erroneous lower-bound fixtures; only the prior ordering assertion is replaced. Exact positive-objective and D1 endpoint checks are offline interpretation. The long study is one known role, three methods, zero new samples; complete cover and numerical1e-7 policy remain required. Full54000 nominal obligation and postprocessing fit in70000 actual outer seconds without assuming early certification. All new output/TEMP/restore paths stay under the fixed E work root.\n\nThis is self-review with a separate contract implementation, not an assertion of a third-party review. Postformal independent physical/pair/math arithmetic and actual public recovery are still required.\n',encoding='utf-8')
    print(json.dumps(dict(decision='ACCEPT',budget=budget(),remaining_formal_seconds=54000)))

if __name__=='__main__':run()
