"""Thin wiring: six zero-Optimize references, explicit argv, saved-small reader admission."""
from round126_common import *
import copy, collections
from round122_prepare import command as frozen_command,COMMON as PRIOR_COMMON
from round126_run import child_creation

COMMON=dict(PRIOR_COMMON,gurobi_seed=0)
EXPORTER=Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP/build/research/round121-reference/Round121Reference.exe')

def references():
    from round100_idle import ensure_idle
    workspace();identity();ensure_idle();m=read(OUT/'input_manifest.json');q=OUT/'qualification';q.mkdir(exist_ok=True)
    frozen_sha=sha(EXPORTER);processes=[];tick=time.perf_counter()
    for batch in range(2):
        roles=m['roles'][3*batch:3*batch+3];path=q/f'reference_batch{batch+1}.tsv'
        assert not path.exists()
        path.write_text(''.join('\t'.join(map(str,[ROOT/p['input_path'],p['T_seconds'],60,60,.15,q/'reference'/p['id']]))+'\n' for p in roles),encoding='utf-8')
        cmd=[str(EXPORTER),str(path)]
        with (q/f'reference_batch{batch+1}.log').open('xb') as so:
            child=subprocess.Popen(cmd,cwd=ROOT,env=environment(),stdout=so,stderr=subprocess.STDOUT)
            record=dict(pid=child.pid,parent_pid=os.getpid(),creation_unix=child_creation(child),command=cmd,Optimize=0,exporter_SHA=frozen_sha)
            processes.append(record);write(q/f'reference_batch{batch+1}_PID.json',record)
            rc=child.wait(timeout=120)
        assert rc==0,(cmd,rc)
        for p in roles:
            d=q/'reference'/p['id'];b=read(d/'build.json');native=read(d/'native_metadata.json')
            assert b['optimizer_calls']==native['Optimize']==0
            assert sha(d/'original.lp')==b['canonical_sha256']
            assert (native['rows'],native['columns'],native['objective_constant'])==(b['rows'],b['columns'],0)
    assert sha(EXPORTER)==frozen_sha
    write(q/'reference_receipt.json',dict(UTC=utc(),native_processes=processes,Optimize=0,inputs=6,seconds=time.perf_counter()-tick,
        helper_reused_in_place=str(EXPORTER),helper_SHA=frozen_sha,helper_source_SHA=sha(ROOT/'scripts/round121_reference.cpp'),
        reason='R122 exporter was safely cleaned; two exact three-row batches reuse the existing qualified same-source R121 read-only writer.',
        production_compilations=0,no_primal_bound_basis_or_Start_export=True))

def prepare():
    workspace();identity();m=read(OUT/'input_manifest.json');groups=[];plans=[]
    for p0 in m['roles']:
        p=copy.deepcopy(p0);n=p['group_number'];camp=OUT/f'campaign/group{n:02d}';camp.mkdir(parents=True,exist_ok=False)
        ref=OUT/'qualification/reference'/p['id'];p['reference']=read(ref/'build.json')
        # The unchanged evidence reader expects a group-local reference. A hard link keeps one set of model bytes.
        target=camp/'reference'/p['id'];target.mkdir(parents=True)
        for name in ['original.lp','build.json']:(target/name).hardlink_to(ref/name)
        launches=[]
        for position,arm in enumerate(p['method_order'],1):
            d=camp/'raw'/f'{position:02d}_{p["id"]}_S0_{arm}'
            cmd=frozen_command(p,arm,d)
            assert cmd[cmd.index('--process-wall-time-limit')+1]==str(p['cap_seconds'])
            assert cmd[cmd.index('--time-limit')+1]==str(p['cap_seconds']-6)
            assert cmd[cmd.index('--process-shutdown-margin')+1]=='30'
            assert cmd[cmd.index('--gurobi-seed')+1]=='0'
            assert ('--plain-baseline' in cmd)==(arm=='P-GRB')
            assert ('--round98-state-service' in cmd)==(arm=='M-B')
            assert not any(s.startswith(('--round119','--round120','--round112','--round100')) for s in cmd)
            launches.append(dict(number=position,group_number=n,global_launch_number=2*(n-1)+position,id=p['id'],arm=arm,seed=0,
                panel=copy.deepcopy(p),panel_kind=p['panel_kind'],destination=str(d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
        group=dict(number=n,id=p['id'],campaign=f'campaign/group{n:02d}',methods=p['method_order'],cap_seconds=p['cap_seconds'],
            nominal_seconds=2*p['cap_seconds'],management_reserve=60,seed=0,source=p['source'],V=p['V'],unconditional=True)
        groups.append(group);plans.append(dict(group=group,launches=launches))
    assert sum(g['nominal_seconds'] for g in groups)==10800 and len(plans)==6
    write(OUT/'measurement_policy_v2.json',dict(main_clock='T_produce',T_cert='T_produce iff final certificate qualified; otherwise null',
        T_produce='Full own startup, admission, all model/LP/MIP/Start/online work, native exit and producer seal',
        T_verify='Only independent read-only verification and mandatory closeout after seal; no optimization',
        T_total='T_produce + T_verify; group reconciliation separately charged',native_reserve_seconds=30,
        native_cli_limit='cap minus 6, with the inherited absolute remaining-deadline rule',hard_stop='cap minus 2',
        open_return_before_cap='report actual duration and nominal cap; no cap-substituted T_cert or speedup'))
    write(OUT/'protocol.json',dict(round=126,base=BASE,source=SOURCE,sole_proposed_method='M-B',main_control='cold P-GRB',common=COMMON,
        groups=groups,formal_arms=12,formal_pairs=6,new_problems=6,formal_nominal_seconds=10800,maximum_outer_seconds=18000,
        qualification_soft_seconds=600,qualification_authorized_seconds=1200,no_formal_retries=True,
        certificate_tolerance=1e-7,clean_own_zero_tolerance=1e-12,own_H_seed=20260626,
        five_main_categories=['BOTH_CERTIFIED','MB_ONLY_CERTIFIED','P_ONLY_CERTIFIED','BOTH_OPEN','UNEVALUABLE'],
        no_open_endpoint_WIN_in_primary=True,time_materiality='max(30 seconds,0.10*T_cert(P))',speedup='T_cert(P)/T_cert(M-B) only if both certified',
        default_ENS_changed=False,no_variant_dispatch_switching_or_new_algorithm=True,no_cross_arm_warm_information=True))
    write(OUT/'argv_freeze.json',dict(groups=groups,plans=plans,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,formal_arms=12,formal_pairs=6))
    write(OUT/'paper_method_config.json',dict(name='M-B',sole_proposed_method=True,production_source=SOURCE,PE_SHA256=PE_SHA,DLL_SHA256=DLL_SHA,
        input_preset='research-round83-vds-equal-net-exchange',additional_flags=['--round98-state-service','m-binary','--round90-lp-g-split','false'],
        effective_preset='research-round99-ensc-discrete-structure-m-binary',H_seed=20260626,H_orders='24 shuffled + one constructive',
        representation='VD-P; continuous pickup/drop, binary direction; A/B; original integer loads',
        static_strengthening='R125 Appendix A.5, unchanged',controller='R125 Algorithms 1-3 and Appendix B.1-B.5, unchanged',
        native=COMMON,closed_research_variants=['D1','D0','MB-PC','LP-G','AMF/RC','contraction'],
        exact_reproduction_commands=[dict(id=p['group']['id'],command=l['command']) for p in plans for l in p['launches'] if l['arm']=='M-B'],
        baseline='cold complete original compact model; no H, route, Start, prior bound or certificate'))
    hs=helpers()
    for plan in plans:
        g=plan['group'];write(OUT/g['campaign']/'identity.json',dict(prereg=dict(common=COMMON,candidate_binary=str(PE),candidate_binary_sha256=PE_SHA),
            prereg_sha256=sha(OUT/'protocol.json'),runner_sha256=sha(ROOT/'scripts/round126_campaign.py'),helpers=hs,source_hashes=bindings(),
            candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,measured_source_commit=SOURCE,delivery_base_commit=BASE,
            references={plan['launches'][0]['id']:plan['launches'][0]['panel']['reference']},launches=plan['launches'],measurement_policy_SHA=sha(OUT/'measurement_policy_v2.json')))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=hs,input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),
        argv_SHA=sha(OUT/'argv_freeze.json'),campaign_identities={g['campaign']:sha(OUT/g['campaign']/'identity.json') for g in groups}))
    print('Six references and twelve exact command positions ready; no H/LP/MIP on new inputs')

def qualify():
    from round122_evidence import extension
    import read_round118 as reader
    import read_round116 as base_reader
    import round108_reader as core
    workspace();identity();tick=time.perf_counter();oldroot=WORK/'worktrees/round122'
    oldi=read(oldroot/'results/unified_exact_round122/campaign/group02/identity.json')
    recs=collections.defaultdict(list);core.start_reader.ROOT=oldroot
    with extension():
        items=[reader.item(oldroot,l,oldi,recs) for l in oldi['launches'] if l['arm'] in METHODS]
        assert len(items)==2 and all(v['complete'] for v in items)
        final=base_reader.reconcile([q for v in items for q in v['claims']],[q for v in items for q in v['ind']['witnesses']])
        arms=[reader.finalize(oldroot,v,final,recs) for v in items]
    core.start_reader.ROOT=ROOT
    assert not final['rejections'] and all(a['formal_protocol_qualified'] and a['certificate'] for a in arms)
    assert all(a['V']<=20 and a['PE_SHA']==PE_SHA and a['DLL_SHA']==DLL_SHA for a in arms)
    # Transitive inherited runtime source bytes are compared, not merely the old PASS label.
    hs=helpers();shared={n:h for n,h in hs.items() if n in oldi['helpers']}
    line_endings=[]
    for n,h in shared.items():
        if h==oldi['helpers'][n]:continue
        saved=oldroot/n;current=ROOT/n
        assert sha(saved)==oldi['helpers'][n]
        assert current.read_bytes().replace(b'\r\n',b'\n')==saved.read_bytes().replace(b'\r\n',b'\n'),('inherited semantic source change',n)
        line_endings.append(dict(path=n,saved_SHA=sha(saved),current_SHA=h,LF_normalized_equal=True))
    plan=read(OUT/'argv_freeze.json');assert len(plan['groups'])==6
    assert [g['cap_seconds'] for g in plan['groups']]==[600]*3+[1200]*3
    assert all(l['seed']==0 and l['arm'] in METHODS for p in plan['plans'] for l in p['launches'])
    positive=read(OUT/'shortage_positive_objective.json')['roles'];assert sum(p['positive_objective_proved'] for p in positive)==4
    assert all(p['positive_floor_decimal']>0 for p in positive if p['positive_objective_proved'])
    assert not list((OUT/'campaign').glob('*/raw/*/launch.json'))
    candidate=read(OUT/'candidate_identity.json');assert candidate['helpers']==hs
    write(OUT/'qualification/saved_small_reader.json',dict(source_root=str(oldroot),source_identity_SHA=sha(oldroot/'results/unified_exact_round122/campaign/group02/identity.json'),
        arms=arms,reconciliation=final,inherited_helper_count_compared=len(shared),line_ending_equivalences=line_endings,actual_Optimize=0,new_CLI_starts=0,
        reason_no_CLI='Same frozen PE/DLL and unchanged runtime helpers already have qualified actual V20 records; only manifest/caps/classification wiring is new.',
        seconds=time.perf_counter()-tick))
    write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',UTC=utc(),candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
        sole_proposed_method='M-B',six_inputs_sealed=True,four_shortage_positive=True,all_windows_and_commands_frozen=True,
        inherited_parameters_and_timing=True,no_formal_H_LP_MIP_preview=True,no_historical_free_solution=True,
        qualification_scope='Saved qualified V20 P/M-B reader replay, static command/cap checks, six pure references; no repeated native algorithm qualification.',
        native_reference_Optimize=0,new_CLI_Optimize=0,author_separate_admission_self_review=True,helpers=hs))
    print(json.dumps(dict(admitted=True,saved_small_arms=2,inherited_helpers=len(shared),new_Optimize=0)))

def refreeze_helpers():
    assert not list((OUT/'campaign').glob('*/raw/*/launch.json'))
    candidate=read(OUT/'candidate_identity.json');before=copy.deepcopy(candidate);hs=helpers()
    for name in candidate['campaign_identities']:
        p=OUT/name/'identity.json';i=read(p);i['helpers']=hs;write(p,i)
    candidate.update(helpers=hs,campaign_identities={name:sha(OUT/name/'identity.json') for name in candidate['campaign_identities']})
    write(OUT/'candidate_identity.json',candidate)
    write(OUT/'review/preformal_helper_serialization_repair.json',dict(UTC=utc(),reason='Saved R122 generated Python sources were LF; linked checkout files are CRLF. Require exact LF-normalized source equality, retaining both SHA values.',
        first_failure='fees/saved_reader/stderr.log',first_failure_receipt_SHA=sha(OUT/'fees/saved_reader/receipt.json'),
        before_helpers=before['helpers'],after_helpers=hs,formal_starts=0,Optimize=0,input_manifest_SHA_unchanged=candidate['input_manifest_SHA']))

if __name__=='__main__':{'references':references,'prepare':prepare,'qualify':qualify,'refreeze':refreeze_helpers}[sys.argv[1]]()
