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
if __name__=='__main__':billed(sys.argv[1])
