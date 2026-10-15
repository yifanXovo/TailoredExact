"""One qualification parent, one zero-Optimize batch and four real Seed1 CLI."""
from round121_common import *
from round121_prepare import EXPORTER,resolve
from round121_campaign import execute
from round121_evidence import extension
from round121_fixtures import run as finite
from qualify_round120 import child_creation
from read_round121 import complete_H
from round121_reaudit import replay,saved_view,producer_identity
from round100_idle import ensure_idle
import traceback,collections,csv
def billed(label):
    fee,tick=fee_begin(label,5,1200,True,dict(starts=21,seconds=37800));actual=0;code=1
    try:
        ensure_idle();identity();f=read(OUT/'prospective_helper_freeze.json');assert f['helpers']==helpers() and f['source_bindings']==bindings()
        gate=read(OUT/'review/pre_contract.json');assert gate['decision']=='ACCEPT' and gate['helpers']==helpers() and gate['source_bindings']==bindings()
        finite()
        assert sha(EXPORTER)==read(OUT/'engineering/reference_compile02/receipt.json')['exporter_SHA']
        cmd=[str(EXPORTER),str(OUT/'qualification/reference_batch.tsv')]
        write(fee/'01_reference_before.json',dict(command=cmd,outer_cap=300,Optimize=0,exporter_SHA=sha(EXPORTER)))
        actual+=1;start=time.perf_counter()
        with (fee/'01_reference_stdout.txt').open('xb') as out:
            child=subprocess.Popen(cmd,cwd=ROOT,env=environment(),stdout=out,stderr=subprocess.STDOUT)
            write(fee/'01_reference_PID.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=child_creation(child),command=cmd))
            try:rc=child.wait(timeout=300)
            except BaseException:child.kill();child.wait();raise
        write(fee/'01_reference_return.json',dict(exit_code=rc,outer_seconds=time.perf_counter()-start,actual_exit_observed=True))
        assert rc==0
        m=read(OUT/'input_manifest.json')
        for p in m['new_roles']:
            d=OUT/'qualification/reference'/p['id'];b=read(d/'build.json');native=read(d/'native_metadata.json')
            assert b['optimizer_calls']==native['Optimize']==0 and sha(d/'original.lp')==b['canonical_sha256']
            assert b['columns']==native['columns'] and b['rows']==native['rows'] and native['objective_constant']==0
        resolve();h=read(OUT/'qualification/h100/identity.json')
        for l in h['launches']:
            actual+=1;execute(l,h)
            write(fee/f'{actual:02d}_H100_after.json',dict(arm=l['arm'],seed=l['seed'],producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json')))
        H=complete_H(h['launches'][0]['panel'],{l['arm']:Path(l['destination']) for l in h['launches'] if l['arm']!='P-GRB'})
        assert all(x['qualified'] for x in H['comparisons']);write(OUT/'qualification/full_H_comparison.json',H)
        assert actual==5 and time.perf_counter()-tick<=1200
        write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            final_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=helpers(),source_bindings=bindings(),pre_contract_SHA=sha(OUT/'review/pre_contract.json'),
            finite_fixtures_SHA=sha(OUT/'qualification/finite_fixtures.json'),H100_four_Seed1_actual_CLI=True,full_H_equal=True,
            no_extra_H_weak_start_LP_or_MIP_diagnostic=True,native_children=actual,wrapper=1,fee_close_required_before_formal=True,
            scope='reuse R120 native matrix qualification; actual new Seed1 wiring/reference/complete audit',not_performance_superiority=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)
def continue_sealed_P(label):
    """One final parent plus only three never-started CLI positions.

    The first P producer seal/clock and original qualification identity remain
    immutable. Final read-only helpers requalify its existing returned data.
    No reference exporter or P solver is run again.
    """
    fee,tick=fee_begin(label,3,900,True,dict(starts=21,seconds=37800));actual=0;code=1
    try:
        ensure_idle();identity();gate=read(OUT/'review/pre_contract.json')
        assert gate['decision']=='ACCEPT' and gate['helpers']==helpers() and gate['source_bindings']==bindings()
        patch=read(OUT/'qualification/read_only_patch_identity.json');assert patch['final_helpers']==helpers()
        h=read(OUT/'qualification/h100/identity.json');first=h['launches'][0];d=Path(first['destination'])
        assert sha(OUT/'qualification/h100/identity.json')==patch['original_H100_identity_SHA']
        assert sha(d/'producer_seal.json')==patch['preserved_P_producer_seal_SHA']
        assert sha(d/'producer_receipt.json')==patch['preserved_P_producer_receipt_SHA']
        assert read(OUT/'fees/qualification02/01_reference_return.json')['exit_code']==0
        from round121_evidence import verify
        verify(first,h)
        write(fee/'existing_P_readonly_requalification.json',dict(actual_new_native_children=0,Optimize=0,
            original_producer_receipt_SHA=sha(d/'producer_receipt.json'),original_producer_seal_SHA=sha(d/'producer_seal.json'),
            final_total_receipt_SHA=sha(d/'arm_total_receipt.json'),original_T_produce_unchanged=True,
            verification_clock_includes_elapsed_gap_since_original_seal=True,raw_never_replaced=True,helpers=helpers()))
        for l in h['launches'][1:]:
            assert not Path(l['destination']).exists()
            actual+=1;execute(l,h)
            write(fee/f'{actual:02d}_H100_after.json',dict(arm=l['arm'],seed=l['seed'],producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json')))
        H=complete_H(h['launches'][0]['panel'],{l['arm']:Path(l['destination']) for l in h['launches'] if l['arm']!='P-GRB'})
        assert all(x['qualified'] for x in H['comparisons']);write(OUT/'qualification/full_H_comparison.json',H)
        assert actual==3 and time.perf_counter()-tick<=900
        write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            final_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=helpers(),source_bindings=bindings(),pre_contract_SHA=sha(OUT/'review/pre_contract.json'),
            finite_fixtures_SHA=sha(OUT/'qualification/finite_fixtures.json'),H100_four_Seed1_actual_CLI=True,full_H_equal=True,
            original_reference_exporter_and_P_run_once=True,remaining_three_CLI_once=True,readonly_requalification_of_existing_P=True,
            original_H100_identity_SHA=sha(OUT/'qualification/h100/identity.json'),read_only_patch_identity_SHA=sha(OUT/'qualification/read_only_patch_identity.json'),
            actual_new_native_children=actual,wrapper=1,fee_close_required_before_formal=True,
            scope='R120 production unchanged; R121 final read-only Seed1 bool/int handling qualified on original sealed P plus three actual CLI',not_performance_superiority=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)
def minimal_final(label):
    """Finite composed admission: recheck saved MB, one last real D1 CLI.

    Four H100 CLI were a suggested qualification design in the user contract.
    Failed read-only wiring consumed its spare parents. D0's complete unchanged
    R120 native qualification is reused explicitly; H100 D0 Seed1 is unrun.
    Every one of the 16 fixed formal positions remains mandatory and unchanged.
    """
    fee,tick=fee_begin(label,1,600,True,dict(starts=21,seconds=37800));actual=0;code=1
    try:
        ensure_idle();identity();gate=read(OUT/'review/pre_contract.json')
        assert gate['decision']=='ACCEPT' and gate['helpers']==helpers() and gate['source_bindings']==bindings()
        minimum=read(OUT/'qualification/minimum_admission_plan.json')
        assert minimum['final_helpers']==helpers() and minimum['formal_positions_unchanged']==16 and minimum['formal_pairs_unchanged']==18
        assert gate['minimum_admission']['decision']=='ACCEPT_COMPOSED_MINIMUM_PENDING_ACTUAL_D1'
        h=read(OUT/'qualification/h100/identity.json');p,mb,d0,d1=h['launches']
        assert sha(OUT/'qualification/h100/identity.json')==minimum['original_H100_identity_SHA']
        for l in [p,mb]:
            d=Path(l['destination']);saved=minimum['preserved_producers'][l['arm']]
            assert sha(d/'producer_receipt.json')==saved['receipt_SHA'] and sha(d/'producer_seal.json')==saved['seal_SHA']
        assert (Path(p['destination'])/'arm_total_receipt.json').exists() and read(Path(p['destination'])/'audit.json')['passed']
        assert not Path(d0['destination']).exists() and not Path(d1['destination']).exists()
        from round121_evidence import verify
        verify(mb,h)
        write(fee/'existing_MB_readonly_requalification.json',dict(Optimize=0,new_native_children=0,
            producer_receipt_SHA=sha(Path(mb['destination'])/'producer_receipt.json'),total_receipt_SHA=sha(Path(mb['destination'])/'arm_total_receipt.json'),
            original_T_produce_unchanged=True,raw_never_replaced=True,helpers=helpers()))
        actual+=1;execute(d1,h)
        H=complete_H(p['panel'],{l['arm']:Path(l['destination']) for l in [mb,d1]})
        assert all(x['qualified'] for x in H['comparisons']);write(OUT/'qualification/full_H_comparison.json',H)
        status=[dict(arm=l['arm'],seed=1,state='NOT_STARTED_REUSED_R120_D0_NATIVE_QUALIFICATION' if l['arm']=='MB-D0' else 'ACTUAL_CLI_COMPLETE_QUALIFIED',
            actual_CLI=(Path(l['destination'])/'launch.json').exists(),producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json') if l['arm']!='MB-D0' else None) for l in h['launches']]
        write(OUT/'qualification/actual_CLI_status.json',dict(positions=status,actual_CLI=3,H100_D0_Seed1_not_started=True,
            original_suggested_plan_retained=True,complete_R120_D0_native_contract_reused=True,no_missing_formal_position_substituted=True))
        assert actual==1 and time.perf_counter()-tick<=600
        write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            final_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=helpers(),source_bindings=bindings(),pre_contract_SHA=sha(OUT/'review/pre_contract.json'),
            finite_fixtures_SHA=sha(OUT/'qualification/finite_fixtures.json'),H100_four_Seed1_actual_CLI=False,
            H100_actual_Seed1_CLI=['P-GRB','M-B','MB-D1'],H100_D0_Seed1='NOT_STARTED; unchanged R120 full native matrix/type/Start qualification reused',
            minimum_admission_plan_SHA=sha(OUT/'qualification/minimum_admission_plan.json'),full_H_equal_for_actual_warm_CLI=True,
            original_exporter_P_MB_run_once=True,last_D1_run_once=True,all_failed_fees_retained=True,formal_arms_unchanged=16,formal_pairs_unchanged=18,
            actual_new_native_children=actual,wrapper=1,fee_close_required_before_formal=True,
            scope='explicit composed minimum under user section6 suggested four-CLI plan; no production/physical/parameter/certificate/Start criterion relaxed',not_performance_superiority=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)
def resume_four_cli(label):
    """Same R121: retain both producers, re-audit, then only D0 and D1."""
    fee,tick=fee_begin(label,2,900,True,dict(starts=21,seconds=37800));actual=0;code=1
    resume=OUT/'qualification/resume01'
    try:
        ensure_idle();identity();gate=read(OUT/'review/resume_precontract.json')
        assert gate['decision']=='ACCEPT' and gate['helpers']==helpers() and gate['source_bindings']==bindings()
        assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
        authorization=read(OUT/'resumption/authorization01.json')
        assert authorization['new_qualification_starts']==QUALIFICATION_MAXIMUM_STARTS==12
        h=read(resume/'identity.json');old=read(OUT/'qualification/h100/identity.json')
        assert h['launches']==old['launches'] and h['helpers']==helpers() and h['source_hashes']==bindings()
        assert sha(OUT/'qualification/h100/identity.json')==authorization['original_H100_identity_SHA']
        assert not Path(h['launches'][2]['destination']).exists() and not Path(h['launches'][3]['destination']).exists()
        finite(resume/'finite_fixtures.json');recovered={}
        for l in h['launches'][:2]:
            recovered[l['arm']]=replay(l,h,resume/'recovery'/l['arm'])
        write(resume/'recovery_index.json',dict(recovered=recovered,helpers=helpers(),source_bindings=bindings(),no_native_reexecution=True))
        for position,l in enumerate(h['launches'][2:]):
            remaining=(2-position)*120+120
            elapsed=time.perf_counter()-tick;b=budget()
            assert elapsed+remaining<=900 and b['qualification_seconds']+elapsed+remaining<=1800
            assert b['paid_outer_seconds']+elapsed+remaining+37800<=48000
            write(fee/f'{position+1:02d}_before.json',dict(arm=l['arm'],seed=l['seed'],command=l['command'],remaining_budget=b))
            actual+=1;execute(l,h)
            write(fee/f'{position+1:02d}_after.json',dict(arm=l['arm'],producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json')))
        import read_round118 as reader
        import read_round116 as inherited
        items=[];records=collections.defaultdict(list)
        with extension():
            for l in h['launches']:
                if l['arm'] in recovered:
                    with saved_view(l['destination'],resume/'recovery'/l['arm']):items.append(reader.item(ROOT,l,producer_identity(l,h),records))
                else:items.append(reader.item(ROOT,l,h,records))
            assert all(v['complete'] for v in items)
            final=inherited.reconcile([q for v in items for q in v['claims']],[q for v in items for q in v['ind']['witnesses']])
            assert not final['rejections'],'PROOF_RELIABILITY_PRIORITY: qualification same-domain proof contradiction'
            arms=[]
            for v in items:
                l=v['l']
                if l['arm'] in recovered:
                    with saved_view(l['destination'],resume/'recovery'/l['arm']):arms.append(reader.finalize(ROOT,v,final,records))
                else:arms.append(reader.finalize(ROOT,v,final,records))
        assert all(a['formal_protocol_qualified'] and a['numbers_qualified'] for a in arms)
        H=complete_H(h['launches'][0]['panel'],{l['arm']:Path(l['destination']) for l in h['launches'] if l['arm']!='P-GRB'})
        assert all(x['qualified'] for x in H['comparisons'])
        write(resume/'full_H_comparison.json',H)
        write(resume/'current_core.json',dict(arms=arms,adjudication=final,full_H=H,not_formal_performance=True,
            final_helpers=helpers(),source_bindings=bindings(),old_failed_raw_unchanged=True,recovery_index_SHA=sha(resume/'recovery_index.json')))
        write(OUT/'qualification/actual_CLI_status.json',dict(actual_CLI=4,H100_four_Seed1_actual_CLI=True,
            positions=[dict(arm=a['arm'],seed=1,state='ACTUAL_CLI_COMPLETE_QUALIFIED',reused_producer=a['arm'] in recovered,
                recovery_receipt_SHA=sha(resume/'recovery'/a['arm']/'traceable_receipt.json') if a['arm'] in recovered else None) for a in arms],
            all_failures_retained=True,all_original_P_MB_bytes_unchanged=True))
        assert actual==2 and time.perf_counter()-tick<=900
        write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            final_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=helpers(),source_bindings=bindings(),
            pre_contract_SHA=sha(OUT/'review/resume_precontract.json'),H100_four_Seed1_actual_CLI=True,full_H_equal=True,
            original_P_MB_producers_reused_after_complete_final_file_reaudit=True,D0_D1_each_actual_once=True,
            four_arm_qualification_core_SHA=sha(resume/'current_core.json'),new_recovery_receipts_preserve_old_failures=True,
            actual_new_native_children=2,new_wrapper=1,all_old_fees_charged=True,qualification_maximum_starts=12,
            qualification_maximum_seconds=1800,total_maximum_starts=40,total_maximum_seconds=48000,
            formal_arms=16,formal_pairs=18,not_performance_superiority=True,fee_close_required_before_formal=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)

if __name__=='__main__':
    if '--resume-four-cli' in sys.argv[2:]:resume_four_cli(sys.argv[1])
    elif '--minimum-final-D1' in sys.argv[2:]:minimal_final(sys.argv[1])
    elif '--continue-sealed-P' in sys.argv[2:]:continue_sealed_P(sys.argv[1])
    else:billed(sys.argv[1])
