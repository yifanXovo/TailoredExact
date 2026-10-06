"""Frozen R105 runs; reuse original P/ENS command, supervision and audit."""
import csv, json, sys, time
from pathlib import Path
import round90_lp_g_g3 as r90
import round104_campaign as original
from round105_common import *
from round100_idle import ensure_idle

def csvrows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def helpers():
    files=['round105_campaign.py','round105_common.py','round104_campaign.py','round104_common.py',
           'round90_lp_g_g3.py','round86_native_evidence.py','round94_lpg_formal_recovery_v3.py',
           'round88_a1_g3.py','analyze_round61.py','round75_startup.py','round83_audit_v2.py','round70_affinity.py']
    return {n:sha(ROOT/'scripts'/n) for n in files}

def audit(launch,observations,completion,identity,legacy_identity=False):
    if not launch['arm'].startswith('IR-'):
        return original.adapter(launch,observations,completion,identity)
    dest=Path(launch['destination']);folder=dest/'external/round105'
    assert completion['stop_reason']=='normal_return', 'R105 interrupted external process: no invented endpoint'
    result=read(dest/'result.json');summary=read(folder/'summary.json')
    expected='research-round105-inventory-route-'+launch['arm'][3:].lower()
    if legacy_identity:
        assert launch['stage']=='diagnostic02' and launch['id']=='F2'
        assert launch['command'][-2:]==['--round105-decomposition','full']
        assert result['algorithm_preset']=='research-round83-vds-equal-net-exchange'
        assert identity['runner_sha256']=='3104b0925fd5df2b7eb5762dd4ee1f316ae4ebcdc3be48dd0f530ef42f3c71e1'
    else:assert result['algorithm_preset']==expected
    assert result['status']!='error' and not summary['status'].startswith('ERROR:')
    panel=launch['panel'];physical=r90.evidence.physical_module.physical
    r90.evidence.physical_module.ROOT=ROOT
    seed=physical(panel,r90.normalize(read(folder/'seed.json')))
    final=physical(panel,r90.normalize(read(folder/'witness.json')))
    result_check=physical(panel,r90.normalize(result))
    assert seed['original_T_feasible'] and final['original_T_feasible'] and result_check['original_T_feasible']
    assert abs(seed['F']-summary['U0'])<1e-7
    assert abs(final['F']-summary['UB'])<1e-7 and abs(result_check['F']-summary['UB'])<1e-7
    assert summary['LB']<=summary['UB']+1e-7
    assert abs(result['lower_bound']-summary['LB'])<1e-7
    assert result['strict_certified_original_problem']==summary['certified']
    if summary['certified']:assert abs(summary['LB']-summary['UB'])<1e-7
    embedding=read(folder/'embedding.json');assert embedding['epsilon']==0 and embedding['gamma_L']==0
    assert abs(embedding['U0']-summary['U0'])<1e-7 and embedding['max_row_violation']<=1e-7
    assert sha(folder/'original.lp')==embedding['original_sha256']
    calls=csvrows(folder/'calls.csv');before=[c for c in calls if c['stage']=='before'];after=[c for c in calls if c['stage']=='after']
    assert len(before)==len(after)==sum(summary[x] for x in ['master_calls','oracle_calls','iis_calls','core_confirmation_calls'])
    assert [c['call'] for c in before]==[c['call'] for c in after]
    master=[c for c in after if c['phase']=='master' and c['bound'] and int(c['status']) in [2,9,11]]
    strongest=max([0]+[float(c['bound']) for c in master]);assert abs(strongest-summary['LB'])<1e-7
    variable=csvrows(folder/'variables.csv');relaxed=[c for c in variable if c['relaxed']=='1']
    assert len(relaxed)==panel['M']*((panel['V']+1)*panel['V']+panel['V'])
    assert all(c['master_type']=='C' and c['old_type'] in ['B','I'] for c in relaxed)
    for c in variable:
        if c['relaxed']=='0':assert c['old_type']==c['master_type']
    exchange=dest/'hga.csv.exchange';assert exchange.is_dir()
    initial=r90.normalize(read(exchange/'initial.json'));replay=r90.replay_exchange(panel,exchange,initial)
    assert not read(exchange/'result.json')['verification_failed']
    assert r90.route_hash(r90.normalize(read(folder/'seed.json'))) in {
        r90.route_hash(initial),r90.route_hash(r90.normalize(read(exchange/'final.json')))}
    return dict(passed=True,certificate=summary['certified'],physical_seed=seed,physical_final=final,
        neutral_exchange=replay,native_call_counts={x:summary[x] for x in ['master_calls','oracle_calls','iis_calls','core_confirmation_calls']},
        endpoint=dict(U=summary['UB'],L=summary['LB'],gap=summary['UB']-summary['LB'],
            certificate=summary['certified'],status=summary['status'],source='valid_global_master_and_independent_physical_witness'))

def prepare(name,protocol_path):
    ensure_idle();protocol=read(protocol_path);camp=OUT/name;camp.mkdir(exist_ok=False)
    original.BUILD=BUILD
    prereg=dict(common=original.ext.COMMON,candidate_binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),
                candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'))
    launches=[];references={}
    for role in protocol['roles']:
        p=dict(role);assert sha(ROOT/p['input_path'])==p['input_sha256']
        dest=camp/'reference'/p['id'];dest.mkdir(parents=True)
        reference=original.build_reference(p,dest);references[p['id']]=reference;p['reference']=reference
        p['instance_path']=p['input_path']
        for arm in p['method_order']:
            number=len(launches)+1;dest=camp/'raw'/f'{number:02d}_{p["id"]}_{arm}'
            cmd=(r90.audited_runner_utilities.command_for(prereg,p,arm,dest) if arm=='P-GRB'
                 else r90.command_for(prereg,p,'ENS-C',dest))
            if arm.startswith('IR-'):cmd+=['--round105-decomposition',arm[3:].lower()]
            launches.append(dict(number=number,id=p['id'],arm=arm,panel=p,destination=str(dest),stage=name,
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
    write(camp/'identity.json',dict(prereg=prereg,prereg_sha256=sha(protocol_path),runner_sha256=sha(__file__),
        source_hashes=bindings(),helpers=helpers(),candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),
        dll_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),protocol_path=str(protocol_path),
        references=references,launches=launches,reference_children=len(references),optimizer_calls=0,
        prepared_unix=time.time()))
    print(json.dumps(dict(prepared=name,runs=len(launches),reference_children=len(references))))

def run(name,number):
    ensure_idle();camp=OUT/name;q=read(camp/'identity.json')
    assert sha(__file__)==q['runner_sha256'] and bindings()==q['source_hashes'] and helpers()==q['helpers']
    assert sha(BUILD/'ExactEBRP.exe')==q['candidate_binary_sha256']
    assert sha('D:/gurobi1302/win64/bin/gurobi130.dll')==q['dll_sha256']
    assert sha(q['protocol_path'])==q['prereg_sha256']
    rows=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()] if (camp/'summary.jsonl').exists() else []
    assert len(rows)==number-1 and all(c['audit_passed'] for c in rows)
    launch=q['launches'][number-1];assert not Path(launch['destination']).exists()
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    r90.CAMPAIGN=camp;r90.audit_launch=audit
    r90.run_one(launch,q['prereg'],q)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='run':run(sys.argv[2],int(sys.argv[3]))
    elif sys.argv[1]=='recover-F2-label':
        camp=OUT/'diagnostic02';q=read(camp/'identity.json');launch=q['launches'][0];dest=Path(launch['destination'])
        audited=audit(launch,read(dest/'observations.json'),read(dest/'completion.json'),q,True)
        write(dest/'audit_recovery.json',dict(audited,scope='read-only audit of original numeric evidence; no data relabel or Optimize',
            original_failed_audit_sha256=sha(dest/'audit.json'),reader_sha256=sha(__file__),
            original_source_hashes=q['source_hashes'],original_binary_sha256=q['candidate_binary_sha256']))
        print(json.dumps(audited))
    else:raise ValueError('prepare|run only')
