"""Frozen serial eight-arm campaign; original supervisor and explicit scoped audit."""
from round107_common import *
import csv,math,copy
import round90_lp_g_g3 as r90
import round104_campaign as original
import round106_campaign as inherited
import round94_lpg_formal_recovery_v3 as scope
from round100_idle import ensure_idle
def rows(p):
    with Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def journal_audit(panel,observations,PE):
    base=r90.evidence;base.physical_module.ROOT=ROOT
    calls={};witnesses=[];bounds=[];returned=[];not_started=[];identity=None
    for seq,record in enumerate(observations,1):
        e=record['payload'];assert e['sequence']==seq
        k=e['kind'];assert k!='failure',e
        if k=='identity':
            assert seq==1 and e['input_sha256']==panel['input_sha256']
            assert e['lambda']==panel['lambda'] and e['T']==panel['T_seconds']
            assert e['pickup_seconds']==panel['pickup_seconds'] and e['drop_seconds']==panel['drop_seconds'];identity=e
        elif k=='call':
            assert e['call'] not in calls and sha(e['model_path'])==e['model_sha256'];calls[e['call']]=e
            assert e['settings']==scope.SETTINGS
        elif k=='witness':
            w=base.physical_module.physical(panel,e);assert w['original_T_feasible']
            assert abs(w['G']-e['G'])<1e-7 and abs(w['P']-e['P'])<1e-7
            witnesses.append(dict(w,source=e['source'],call=e['call'],sequence=seq,available=record['effective_available_seconds']))
        elif k=='bound':
            assert not e['inconsistent']
            if e['global_available']:assert abs(base.replay_bound(calls[e['call']],e['native_bound'],witnesses)-e['global_bound'])<1e-10
            else:assert e['global_bound'] is None
            bounds.append(dict(e,available=record['effective_available_seconds']))
        elif k=='returned':assert e['call'] in calls and e['return_code']==0;returned.append(e['call'])
        elif k=='not_started':assert e['call'] in calls and e['actual_Optimize'] is False;not_started.append(e['call'])
        elif k=='witness_rejected':pass
        else:raise AssertionError(('unknown journal kind',k))
    assert identity and witnesses and not set(returned)&set(not_started)
    assert set(calls)==set(returned)|set(not_started),'missing call/intent finalization'
    U=min(w['F'] for w in witnesses);L=max([0]+[b['global_bound'] for b in bounds if b['global_available']]);assert L<=U+1e-7
    for b in bounds:
        if b['global_available']:base.replay_bound(calls[b['call']],b['native_bound'],witnesses)
    return dict(binary_sha256=PE,committed_events=len(observations),native_calls_started=len(calls)-len(not_started),
        native_calls_returned=len(returned),not_started_intents=len(not_started),physical_witnesses=len(witnesses),
        native_physical_witnesses=sum(w['source'].startswith('native_MIPSOL') for w in witnesses),
        scoped_bound_events=len(bounds),global_native_bound_events=sum(b['global_available'] for b in bounds),
        UB=U,LB=L,gap=U-L,certificate=False,witnesses=witnesses)
def frontier_audit(launch,observations,completion,identity):
    d=Path(launch['destination']);p=launch['panel'];result=read(d/'result.json')
    assert completion['stop_reason']=='normal_return' and completion['returncode']==0
    assert result['algorithm_preset']=='research-round107-ensc-frontier-struct'
    a=journal_audit(p,observations,identity['candidate_binary_sha256'])
    r90.evidence.finalize_endpoint(ROOT,p,'FRONTIER-STRUCT',a,observations,result,'normal_return',p['reference'])
    root=d/'external/round107';requests=[json.loads(x) for x in (root/'requests.jsonl').read_text().splitlines()]
    counts={};event_count=0;cross=0;remap=0
    for q in requests:
        assert sha(q['canonical_path'])==q['canonical_sha256']
        if q['kind']=='LP':assert not q['fresh_canonical_MIP'] and not q['optimal_close_by_dominance'];continue
        folder=Path(q['evidence_dir']);assert not (folder/'error.json').exists()
        if not q['native_Optimize_started']:continue
        s=read(folder/'summary.json');assert s['master_calls']==1 and s['iis_calls']==0
        assert not q['local_INF'] or not s['domain_witness_embeds']
        if q['optimal_close_by_dominance']:assert s['final_mode_verified'] and q['qualified_local_bound']+1e-7>=q['own_global_UB']
        if q['unresolved']:assert not q['target_reached'] and not s['final_native_bound_qualified']
        vv=rows(folder/'variables.csv');assert all(x['master_type']=='C' and x['old_type'] in ('B','I') for x in vv if x['relaxed']=='1')
        assert all(x['old_type']==x['master_type'] for x in vv if x['relaxed']=='0')
        ev=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()];assert len(ev)==s['events']
        audits=[json.loads(x) for x in (folder/'candidate_audit.jsonl').read_text().splitlines()]
        assert len(audits)==2*len(ev)
        for e in ev:
            r=audits[2*(e['event']-1)+1];assert r['base_rows_valid'] and r['bounds_integrality_valid'] and r['epigraph_valid']
            assert abs(r['model_objective']-r['objective_dot'])<1e-7*max(1,abs(r['model_objective'])) and e['model_objective']+1e-7>=e['Ftrue']
        for csvfile in [folder/'calls.csv',folder/'inner/calls.csv']:
            for row in rows(csvfile):
                if row['stage']=='after':counts[row['phase']]=counts.get(row['phase'],0)+1
        assert len(rows(folder/'lazy.csv'))==s['lazy_calls']
        for row in rows(folder/'lazy.csv'):assert int(row['api_return'])==0 and float(row['violation'])>max(1e-7,1e-6*max(1,abs(float(row['activity'])),abs(float(row['rhs']))))
        cross+=s['cross_request_hits'];remap+=s['remapped_rows'];event_count+=s['events']
    assert counts.get('iis',0)==0 and counts.get('core_confirm',0)==0
    LP=sum(q['kind']=='LP' and q['native_Optimize_started'] for q in requests)
    assert LP+counts.get('master',0)==result['external_gini_tree_optimize_count']==a['native_calls_started']
    assert result['external_gini_tree_fresh_restart_count']==counts.get('master',0)
    folder=d/'hga.csv.exchange';initial=r90.normalize(read(folder/'initial.json'))
    a['neutral_exchange']=r90.replay_exchange(p,folder,initial);assert not read(folder/'result.json')['verification_failed']
    a.update(passed=True,native_call_counts=dict(counts,LP=LP),request_count=len(requests),events=event_count,cross_request_hits=cross,remapped_rows=remap)
    return a
def audit(launch,observations,completion,identity):
    if launch['arm']=='GLOBAL-STRUCT':
        alias=dict(launch,arm='EVENT-STRUCT');return inherited.audit(alias,observations,completion,identity)
    if launch['arm']=='FRONTIER-STRUCT':return frontier_audit(launch,observations,completion,identity)
    return original.adapter(launch,observations,completion,identity)
def helpers():
    names=set(inherited.helpers())|{'round107_campaign.py','round107_common.py','round107_qualification.py',
        'round107_cli_qualification.py','round107_cli_development.py','round107_lp_qualification.py','round107_repair_freeze.py'}
    return {n:sha(ROOT/'scripts'/n) for n in sorted(names)}
def prepare(name,protocol_path):
    ensure_idle();protocol=read(protocol_path);camp=OUT/name;camp.mkdir(exist_ok=False)
    original.BUILD=BUILD;common=dict(original.ext.COMMON);common['shutdown_margin_seconds']=30
    prereg=dict(common=common,candidate_binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'))
    launches=[];references={}
    for role in protocol['roles']:
        p=dict(role);assert sha(ROOT/p['input_path'])==p['input_sha256'];dest=camp/'reference'/p['id'];dest.mkdir(parents=True)
        p['reference']=references[p['id']]=original.build_reference(p,dest);p['instance_path']=p['input_path']
        for arm in p['method_order']:
            n=len(launches)+1;d=camp/'raw'/f'{n:02d}_{p["id"]}_{arm}'
            cmd=r90.audited_runner_utilities.command_for(prereg,p,arm,d) if arm=='P-GRB' else r90.command_for(prereg,p,'ENS-C',d)
            if arm=='GLOBAL-STRUCT':cmd+=['--round106-events','struct']
            if arm=='FRONTIER-STRUCT':cmd+=['--round107-frontier-struct','true']
            launches.append(dict(number=n,id=p['id'],arm=arm,panel=p,destination=str(d),stage=name,cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
    write(camp/'identity.json',dict(prereg=prereg,prereg_sha256=sha(protocol_path),runner_sha256=sha(__file__),source_hashes=bindings(),helpers=helpers(),
        candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),DLL_sha256=sha(DLL),protocol_path=str(Path(protocol_path).absolute()),references=references,launches=launches,
        reference_children=len(references),measured_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),reference_PE_SHA=sha(BUILD/'Round65ReferenceBuild.exe'),
        prepared_unix=time.time(),Optimize_calls=0))
    print(json.dumps(dict(prepared=name,runs=len(launches))))
def run(name,n):
    ensure_idle();camp=OUT/name;q=read(camp/'identity.json');gate=read(OUT/'review/performance_admission.json')
    assert gate['decision']=='ACCEPT' and gate['production_PE_SHA']==q['candidate_binary_sha256']
    assert sha(OUT/'qualification/identity.json')==gate['qualification_identity_SHA']
    assert q['source_hashes']==bindings() and q['helpers']==helpers() and sha(__file__)==q['runner_sha256']
    assert sha(BUILD/'ExactEBRP.exe')==q['candidate_binary_sha256'] and sha(DLL)==q['DLL_sha256']
    assert sha(q['protocol_path'])==q['prereg_sha256'];launch=q['launches'][n-1]
    records=[json.loads(x) for x in (camp/'summary.jsonl').read_text().splitlines()] if (camp/'summary.jsonl').exists() else []
    assert len(records)==n-1 and all(r['audit_passed'] for r in records)
    r90.CAMPAIGN=camp;r90.audit_launch=audit;r90.run_one(launch,q['prereg'],q)
def batch(name,first,last,label):
    q=read(OUT/name/'identity.json');b=budget();required=sum(a['cap_seconds'] for a in q['launches'][first-1:last])
    assert b['remaining_starts']>=0 and b['remaining_outer_seconds']>=required
    d=OUT/name/label;d.mkdir(exist_ok=False);write(d/'launch.json',dict(first=first,last=last,required_nominal_seconds=required,
        actual_finite_children=last-first+2,budget_after_reservation=b,identity_SHA=sha(OUT/name/'identity.json')))
    for n in range(first,last+1):
        write(d/f'{n:02d}_before.json',dict(number=n,arm=q['launches'][n-1]['arm']));run(name,n);write(d/f'{n:02d}_after.json',dict(completed_and_audited=True))
    write(d/'completion.json',dict(completed=True));print(json.dumps(dict(completed=True,arms=last-first+1)))
def billed(name,first,last,label):
    ensure_idle();q=read(OUT/name/'identity.json');b=budget();assert not b['unclosed']
    count=last-first+2;nominal=sum(a['cap_seconds'] for a in q['launches'][first-1:last])
    assert b['remaining_starts']>=count and b['remaining_outer_seconds']>=nominal+120
    fee=OUT/'fees'/label;fee.mkdir(parents=True,exist_ok=False)
    write(fee/'launch.json',dict(command=[sys.executable,__file__,'billed',name,str(first),str(last),label],engineering=False,
        conservative_process_starts=count,declared_native_children=last-first+1,actual_wrapper_processes=1,cap_seconds=nominal+120,
        budget_before=b,source_bindings=bindings(),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),protocol_SHA=q['prereg_sha256']))
    write(fee/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));tick=time.perf_counter();code=0
    try:batch(name,first,last,label)
    except BaseException:code=1;raise
    finally:write(fee/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,engineering=False,
        conservative_process_starts=count,stop_reason='normal_return' if code==0 else 'retained_campaign_failure'))
if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare':prepare(sys.argv[2],sys.argv[3])
    elif action=='run':run(sys.argv[2],int(sys.argv[3]))
    elif action=='batch':batch(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:raise ValueError(action)
