"""One qualification parent, one zero-Optimize batch and four real Seed1 CLI."""
from round121_common import *
from round121_prepare import EXPORTER,resolve
from round121_campaign import execute
from round121_evidence import extension
from round121_fixtures import run as finite
from qualify_round120 import child_creation
from read_round121 import complete_H
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
if __name__=='__main__':continue_sealed_P(sys.argv[1]) if '--continue-sealed-P' in sys.argv[2:] else billed(sys.argv[1])
