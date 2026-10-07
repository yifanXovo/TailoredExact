"""Eight-arm serial panel; inherited cold P, ENS command/supervisor/audit."""
from round106_common import *
import ast,csv,math,re
import round90_lp_g_g3 as r90
import round104_campaign as original
from round100_idle import ensure_idle

def csvrows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def values(p):
    v={}
    for line in Path(p).read_text().splitlines():
        if not line or line.startswith('#'):continue
        n,x=line.split();v[n]=float(x)
    return v
def helpers():
    names=['round106_campaign.py','round106_common.py','round104_campaign.py','round104_common.py','round104_audit.py',
        'round90_lp_g_g3.py','round88_a1_g3.py','round86_native_evidence.py','round94_lpg_formal_recovery_v3.py',
        'round94_lpg_contemporary.py','round83_audit_v2.py','round75_startup.py','analyze_round61.py','round70_affinity.py','round96_external.py']
    return {n:sha(ROOT/'scripts'/n) for n in names}
def audit(launch,observations,completion,identity):
    if not launch['arm'].startswith('EVENT-'):return original.adapter(launch,observations,completion,identity)
    d=Path(launch['destination']);folder=d/'external/round106';p=launch['panel']
    assert completion['stop_reason']=='normal_return' and completion['returncode']==0
    assert not (folder/'initialization_error.json').exists() and not (folder/'error.json').exists()
    result=read(d/'result.json');s=read(folder/'summary.json');strategy=launch['arm'][6:].lower()
    assert result['algorithm_preset']=='research-round106-candidate-events-'+strategy and s['strategy']==strategy
    assert result['status']!='error' and not s['status'].startswith('ERROR')
    r90.evidence.physical_module.ROOT=ROOT
    physical=r90.evidence.physical_module.physical
    seed=physical(p,r90.normalize(read(folder/'seed.json')));final=physical(p,r90.normalize(read(folder/'witness.json')))
    final_result=physical(p,r90.normalize(result))
    assert seed['original_T_feasible'] and final['original_T_feasible'] and final_result['original_T_feasible']
    assert abs(seed['F']-s['U0'])<1e-7 and abs(final['F']-s['UB'])<1e-7 and abs(final_result['F']-s['UB'])<1e-7
    assert s['LB']<=s['UB']+1e-7 and abs(result['lower_bound']-s['LB'])<1e-7
    assert result['strict_certified_original_problem']==s['certified']
    if s['certified']:assert not s['unresolved_candidate'] and abs(s['LB']-s['UB'])<=1e-7
    embedding=read(folder/'embedding.json');assert embedding['epsilon']==embedding['gamma_L']==0
    assert embedding['LazyConstraints']==1 and abs(embedding['U0']-s['U0'])<1e-7 and embedding['max_row_violation']<=1e-7
    assert sha(folder/'original.lp')==embedding['original_sha256']
    variable=csvrows(folder/'variables.csv');relaxed=[a for a in variable if a['relaxed']=='1']
    assert len(relaxed)==p['M']*((p['V']+1)*p['V']+p['V'])
    assert all(a['master_type']=='C' and a['old_type'] in ['B','I'] for a in relaxed)
    assert all(a['old_type']==a['master_type'] for a in variable if a['relaxed']=='0')
    calls=csvrows(folder/'calls.csv')+csvrows(folder/'inner/calls.csv');before=[a for a in calls if a['stage']=='before'];after=[a for a in calls if a['stage']=='after']
    counts={phase:sum(a['phase']==phase for a in after) for phase in ['master','oracle','iis','core_confirm']}
    assert len(before)==len(after) and counts==dict(master=s['master_calls'],oracle=s['oracle_calls'],iis=s['iis_calls'],core_confirm=s['core_confirmation_calls'])
    assert s['master_calls']==1,'production outer Optimize restarted or never launched'
    if strategy!='core':assert s['iis_calls']==s['core_confirmation_calls']==0
    if strategy!='struct':assert s['structural_proofs']==0 and not list(folder.glob('certificate_*.json'))
    assert not any(int(a['status'])==12 for a in after if a['phase']!='iis')
    events=[json.loads(a) for a in (folder/'events.jsonl').read_text().splitlines()]
    assert len(events)==s['events'];lazy=csvrows(folder/'lazy.csv');assert len(lazy)==s['lazy_calls']
    text=(ROOT/p['input_path']).read_text()
    def vec(name):return ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
    initial,target,weights=vec('initial'),vec('target'),vec('weights')
    if abs(max(weights[1:])-10)<1e-6:weights=[x/10 for x in weights]
    start=values(folder/'start.mst');row_pool={}
    for path in folder.glob('row_*.csv'):
        rr=csvrows(path);coeff={r['variable']:float(r['coefficient']) for r in rr};rhs=float(rr[0]['rhs'])
        activity=sum(c*start.get(n,0) for n,c in coeff.items());assert activity<=rhs+1e-7*max(1,abs(rhs),abs(activity))
        assert abs(activity-float(rr[0]['start_activity']))<1e-7
        row_pool[int(path.stem.split('_')[1])]=(coeff,rhs,rr[0]['family'])
    for e in events:
        Y=e['Y'];ratios=[Y[i-1]/target[i] for i in range(1,p['V']+1)];total=sum(ratios)
        G=sum(abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:])/(p['V']*total) if total>0 else 0
        F=G+p['lambda']*sum(weights[i]*abs(ratios[i-1]-1) for i in range(1,p['V']+1))
        assert abs(F-e['Ftrue'])<1e-7 and e['model_objective']>=F-1e-7
        v=values(folder/f'candidate_{e["event"]}.sol')
        for i in range(1,p['V']+1):
            assert abs(v.get(f'Y_{i}',0)-Y[i-1])<=1e-5 and abs(v.get(f'state_{i}_{Y[i-1]}',0)-1)<=1e-5
            served=0
            for k in range(p['M']):
                q=e['operations'][k][i-1];served+=int(q!=0)
                assert abs(v.get(f'p_{k}_{i}',0)-max(q,0))<=1e-5 and abs(v.get(f'd_{k}_{i}',0)-max(-q,0))<=1e-5
                assert abs(v.get(f'z_{k}_{i}',0)-int(q!=0))<=1e-5
                if q:assert initial[i]-Y[i-1]==q
            assert served==int(initial[i]!=Y[i-1])
        rows=[r for r in lazy if int(r['event'])==e['event']];assert [int(r['row']) for r in rows]==e['submitted_lazy_rows']
        for r in rows:
            coeff,rhs,family=row_pool[int(r['row'])];a=sum(c*v.get(n,0) for n,c in coeff.items())
            assert family==r['family'] and int(r['api_return'])==0 and abs(a-float(r['activity']))<1e-7
            assert a-rhs>max(1e-7,1e-6*max(1,abs(a),abs(rhs)))
        assert bool(rows)==(e['outcome']=='REJECTED_PROVED_LAZY')
    if s['final_native_bound_qualified']:assert s['final_native_bound']<=s['LB']+1e-7
    if s['unresolved_candidate']:assert not s['certified'] and not s['final_native_bound_qualified']
    exchange=d/'hga.csv.exchange';initial_w=r90.normalize(read(exchange/'initial.json'));neutral=r90.replay_exchange(p,exchange,initial_w)
    assert not read(exchange/'result.json')['verification_failed']
    assert r90.route_hash(r90.normalize(read(folder/'seed.json'))) in {r90.route_hash(initial_w),r90.route_hash(r90.normalize(read(exchange/'final.json')))}
    return dict(passed=True,physical_seed=seed,physical_final=final,neutral_exchange=neutral,
        native_call_counts=counts,events=len(events),lazy=len(lazy),row_pool=len(row_pool),
        parameter_readback=dict(outer=read(folder/'runtime.json'),inner=read(folder/'inner/runtime.json')),
        endpoint=dict(U=s['UB'],L=s['LB'],gap=s['UB']-s['LB'],certificate=s['certified'],status=s['status'],source='own_physical_routes_qualified_global_master'))

def prepare(name,protocol_path):
    ensure_idle();protocol=read(protocol_path);camp=OUT/name;camp.mkdir(exist_ok=False)
    original.BUILD=BUILD;common=dict(original.ext.COMMON);common['shutdown_margin_seconds']=30
    prereg=dict(common=common,candidate_binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'))
    launches=[];references={}
    for role in protocol['roles']:
        p=dict(role);assert sha(ROOT/p['input_path'])==p['input_sha256'];dest=camp/'reference'/p['id'];dest.mkdir(parents=True)
        p['reference']=references[p['id']]=original.build_reference(p,dest);p['instance_path']=p['input_path']
        for arm in p['method_order']:
            number=len(launches)+1;d=camp/'raw'/f'{number:02d}_{p["id"]}_{arm}'
            cmd=r90.audited_runner_utilities.command_for(prereg,p,arm,d) if arm=='P-GRB' else r90.command_for(prereg,p,'ENS-C',d)
            if arm.startswith('EVENT-'):cmd+=['--round106-events',arm[6:].lower()]
            launches.append(dict(number=number,id=p['id'],arm=arm,panel=p,destination=str(d),stage=name,
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
    write(camp/'identity.json',dict(prereg=prereg,prereg_sha256=sha(protocol_path),runner_sha256=sha(__file__),
        source_hashes=bindings(),helpers=helpers(),candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),DLL_sha256=sha(DLL),
        protocol_path=str(Path(protocol_path).resolve()),references=references,launches=launches,reference_children=len(references),
        measured_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        reference_PE_SHA=sha(BUILD/'Round65ReferenceBuild.exe'),prepared_unix=time.time(),Optimize_calls=0))
    print(json.dumps(dict(prepared=name,runs=len(launches),reference_children=len(references))))
def run(name,number):
    ensure_idle();camp=OUT/name;q=read(camp/'identity.json');gate=read(OUT/'review/performance_admission.json')
    assert gate['decision']=='ACCEPT' and gate['production_PE_SHA']==q['candidate_binary_sha256']
    assert q['source_hashes']==bindings() and q['helpers']==helpers() and sha(__file__)==q['runner_sha256']
    assert sha(BUILD/'ExactEBRP.exe')==q['candidate_binary_sha256'] and sha(DLL)==q['DLL_sha256']
    assert sha(q['protocol_path'])==q['prereg_sha256'] and sha(BUILD/'Round65ReferenceBuild.exe')==q['reference_PE_SHA']
    records=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()] if (camp/'summary.jsonl').exists() else []
    assert len(records)==number-1 and all(r['audit_passed'] for r in records)
    launch=q['launches'][number-1];assert not Path(launch['destination']).exists();assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    r90.CAMPAIGN=camp;r90.audit_launch=audit;r90.run_one(launch,q['prereg'],q)
def batch(name,first,last,label):
    q=read(OUT/name/'identity.json');assert 1<=first<=last<=len(q['launches']) and last-first+1<=8
    b=budget();required=sum(a['cap_seconds'] for a in q['launches'][first-1:last])
    # The enclosing research receipt has already reserved all finite children.
    assert b['remaining_starts']>=0 and b['remaining_outer_seconds']>=required
    d=OUT/name/label;d.mkdir(exist_ok=False);frozen=sha(__file__)
    write(d/'launch.json',dict(first=first,last=last,declared_children=last-first+1,identity_SHA=sha(OUT/name/'identity.json'),required_nominal_seconds=required,budget_after_reservation=b))
    for n in range(first,last+1):
        assert sha(__file__)==frozen;write(d/f'{n:02d}_before.json',dict(number=n,arm=q['launches'][n-1]['arm']))
        run(name,n);write(d/f'{n:02d}_after.json',dict(number=n,completed_and_audited=True))
    write(d/'completion.json',dict(completed=True,children=last-first+1))
if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='run':run(sys.argv[2],int(sys.argv[3]))
    elif sys.argv[1]=='batch':batch(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:raise ValueError('prepare|run|batch')
