"""Protocol/reference preparation. Production PE is only copied, never compiled."""
from round116_common import *
import collections,copy,csv,inspect,shutil,subprocess,traceback
import round116_campaign as campaign
from round109_prepare import COMMON
import round108_reader as core

EXPORTER=ROOT/'build/research/round116-reference/Round116ReferenceBatch.exe'
ARCHIVE=Path('E:/codes/ExactEBRP-round112/build/research/round112-paid-v1/libexact_ebrp_core.a')

def initialize():
    check_identity();manifest=read(OUT/'input_manifest.json')
    protocol=dict(round=116,base=BASE,production_source=SOURCE,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,roles=manifest['roles'],
        pairs=[['ENS-C','P-GRB'],['M-B','P-GRB'],['P-S','P-GRB'],['ENS-C','P-S'],['M-B','P-S'],['M-B','ENS-C']],
        common=COMMON,formal_arms=24,pair_positions=36,nominal_seconds=50400,formal_group_administration=720,
        maximum_starts=56,maximum_outer_seconds=65000,qualification_maximum_starts=16,qualification_maximum_seconds=1800,
        qualification_plan=dict(reference_wrapper_and_native_child=dict(starts=2,cap=1080),finite_driver=dict(starts=1,cap=60),
            H100_wrapper_and_children=dict(starts=5,cap=540),post_driver=dict(starts=1,cap=60),admission_driver=dict(starts=1,cap=60),
            planned_starts=10,planned_outer_seconds=1800,remaining_start_slots=6),
        planned_worst_total=dict(starts=46,seconds=52920),serial=True,formal_each_arm_at_most_one_start=True,
        original_algorithms_frozen=True,cold_P_primary=True,ENS_default=True,M_B_R111_finite_candidate=True,P_S_contribution_control=True,
        own_H_Seed=20260626,own_H_seeds='original24+1/R76/R83',no_cross_arm_UB_Start_cache=True,no_performance_screening=True,
        main_clock='T_produce',secondary_clock='T_total',verification_serial_before_next_native=True,
        materiality=dict(a_U='max(.001,.01*abs(U_control))',a_gap='max(.001,.10*abs(gap_control))',a_t='max(30,.10*t_control)'),
        severity=dict(control_only_certificate=True,both_certified='t_A>=2*t_C and t_A-t_C>=120',
            both_uncertified='U_A-U_C>=max(.001,.05*abs(U_C)) and gap_A-gap_C>=max(.005,.25*abs(gap_C))'),
        closure_tolerance=1e-7,signed_negative_gap_not_clipped=True,
        proof_classes=['CLEAN_NONZERO_CERTIFICATE','OWN_ZERO_CERTIFICATE','RELIABLE_POSITIVE_LB_OPEN','SOURCE_REDUCED_OPEN','INDEPENDENT_FLOOR_OPEN','UNVERIFIABLE'],
        damaged_call_wholly_rejected=True,independent_undamaged_calls_retained=True,source_reduced_not_engine_progress=True,
        cohort_counterexamples_same_original_input_and_physical_parameters_only=True,
        phase_priority_order=['A_PROOF_RELIABILITY_PRIORITY','B_PRIMARY_BENCHMARK_GAP_IDENTIFIED','C_LIMITED_EXTERNAL_SUPPORT','D_EXTERNAL_EVIDENCE_LIMITED_OR_MIXED'],
        B='no A; M-B/P severe loss or at least2 material LOSS',C='no A/B; all6 evaluable, >=3WIN <=1LOSS, >=1V50/V100WIN and >=1M-B clean nonzero full certificate',
        no_statistical_claim=True,no_default_change=True,no_automatic_next_phase=True,
        source_recipe_SHA=sha(OUT/'source_recipe.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        inherited_claim_policy_SHA=sha(OUT/'inherited_claim_policy_r114.md'))
    write(OUT/'protocol.json',protocol)
    inherited=(OUT/'inherited_measurement_policy_v2.md').read_text(encoding='utf-8')
    policy='''# Round116 prospective measurement-v2 extension

All R115 producer/verification predicates and their implementations are inherited byte-for-byte. The appended original policy is historical authority; its Round115-only role/cap/resource statements do not specify the Round116 panel. The current explicit manifest contains six groups, four original methods each, caps900/1800/3600 and H100 qualification cap120. Every group's first arm retains that wrapper's OS creation/import time; others retain the actual pre-admission time. Each group uses local numbers1..4 plus unique global_launch_number1..24.

The original native cap-minus6 TimeLimit argument, process cap, shutdown reserve30, hard-stop cap-minus2, affinity4 and resources remain unchanged. No native remaining-window calculation is edited. T_total>that arm's cap is reported as a secondary total-cost view and is not producer failure. Required serial verification exceeding30s or the planned120s administration reserve does not cancel the next method; actual total65000s and all unstarted windows/reserves remain protected. Production overcap, necessary file/identity/model/physical/resource fault blocks. Final cohort revocation has a separate actual observation time and never rewrites a sealed receipt.

Qualification is at most16 conservative starts/1800s included in56/65000. The disclosed tree plans10 starts/1800 maximum declared seconds: reference wrapper+one zero-Optimize exporter2/1080, artificial finite records1/60, H100 wrapper+four children5/540, actual postdriver1/60, and admission driver1/60. Failed declared slots are not refunded. Pure dependency compilation/data processing/old-claim arithmetic/public recovery are separately timed engineering and never performance samples. Exactly six formal wrappers+24children reserve30 starts and50400+720 seconds; worst qualification reserve yields46/52920. No formal retries or extra performance work.

'''+inherited
    with (OUT/'measurement_policy_v2.md').open('x',encoding='utf-8',newline='\n') as f:f.write(policy)
    q=OUT/'qualification';q.mkdir(exist_ok=True)
    lines=['\t'.join(map(str,[p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],q/'reference'/p['id']])) for p in manifest['roles']]
    (q/'reference_batch.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    # Only one already signed H100 cold reference is reused; no old matrix bundle.
    original=Path('E:/codes/ExactEBRP-round115/results/unified_exact_round115/qualification/reference/H100')
    dst=q/'reference/H100';dst.mkdir(parents=True,exist_ok=False)
    for n in ['original.lp','build.json']:shutil.copyfile(original/n,dst/n)
    assert sha(dst/'original.lp')==read(dst/'build.json')['canonical_sha256']
    write(OUT/'qualification/reference_plan.json',dict(roles=manifest['roles'],TSV_SHA=sha(q/'reference_batch.tsv'),starts=2,outer_cap=1080,
        native_exporter_processes=1,Optimize=0,H100_reference_reused_SHA=sha(dst/'original.lp'),production_PE_compiled=False))
    print('protocol, formulas and reference process tree frozen before reference acquisition')

def compile_exporter():
    from round100_idle import ensure_idle
    ensure_idle();check_identity();tick=time.perf_counter();d=OUT/'engineering/reference_compile01';d.mkdir(parents=True,exist_ok=False)
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe');assert sha(compiler)==read(OUT/'production_identity.json')['compiler_SHA']
    original=read(Path('E:/codes/ExactEBRP-round112/results/unified_exact_round112/production_identity.json'))
    assert original['source_bindings']==bindings() and original['measured_source_commit']==SOURCE
    EXPORTER.parent.mkdir(parents=True,exist_ok=True)
    cmd=[str(compiler),'-std=c++17','-DEXACT_EBRP_ENABLE_GUROBI=1','-I'+str(ROOT/'include'),'-ID:/gurobi1302/win64/include',
        str(ROOT/'scripts/round116_reference_batch.cpp'),str(ARCHIVE),'-o',str(EXPORTER)]
    write(d/'launch.json',dict(command=cmd,cwd=str(ROOT),compiler_SHA=sha(compiler),frozen_core_archive_SHA=sha(ARCHIVE),
        frozen_model_source=SOURCE,production_PE_SHA_before=sha(PE),Optimize=0,native_starts=0,engineering=True))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        result=subprocess.run(cmd,cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=600)
    write(d/'receipt.json',dict(exit_code=result.returncode,seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        production_PE_SHA_after=sha(PE),exporter_SHA=sha(EXPORTER) if EXPORTER.exists() else None))
    assert result.returncode==0,(d/'stderr.log').read_text()
    check_identity();print('read-only six-input exporter compiled; production PE unchanged')

def references(label):
    fee,tick=campaign.fee_begin(label,1,1080,True);code=1;actual=0
    try:
        from round100_idle import ensure_idle
        ensure_idle();check_identity();manifest=read(OUT/'input_manifest.json')
        assert sha(EXPORTER)==read(OUT/'engineering/reference_compile01/receipt.json')['exporter_SHA']
        for p in manifest['roles']:assert not (OUT/'qualification/reference'/p['id']).exists()
        cmd=[str(EXPORTER),str(OUT/'qualification/reference_batch.tsv')]
        with (fee/'stdout.log').open('xb') as so,(fee/'stderr.log').open('xb') as se:
            child=subprocess.Popen(cmd,cwd=ROOT,env=env(),stdout=so,stderr=se);actual=1
            write(fee/'native_exporter_process.json',dict(pid=child.pid,parent_pid=os.getpid(),command=cmd,exporter_SHA=sha(EXPORTER),Optimize=0))
            try:rc=child.wait(timeout=max(1.,1080-(time.perf_counter()-tick)))
            except BaseException:child.kill();child.wait();raise
        assert rc==0,(fee/'stderr.log').read_text()
        for p in manifest['roles']:
            d=OUT/'qualification/reference'/p['id'];b=read(d/'build.json');native=read(d/'native_metadata.json')
            assert b['optimizer_calls']==native['Optimize']==0 and b['canonical_sha256']==sha(d/'original.lp')
            model=core.lp_model(d/'original.lp');assert len(model['order'])==b['columns']==native['columns'] and len(model['rows'])==b['rows']==native['rows']
            with (d/'native_columns.csv').open(newline='') as f:columns=list(csv.DictReader(f))
            counts=collections.Counter(r['type'] for r in columns);assert counts==collections.Counter(model['types'].values())
            coefficients=[abs(v) for row,_,_ in model['rows'] for _,v in row if v]
            write(d/'reference_contract.json',dict(input_parameters=p,canonical_SHA=sha(d/'original.lp'),actual_types=dict(counts),
                native_columns_SHA=sha(d/'native_columns.csv'),native_rows_SHA=sha(d/'native_rows.csv'),native_metadata=native,
                objective=model['objective'],coefficient_min=min(coefficients),coefficient_max=max(coefficients),Optimize=0,
                no_LP_or_MIP_solved=True,no_performance_sample=True))
            del model,columns,coefficients
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,actual)

if __name__=='__main__':
    if sys.argv[1]=='initialize':initialize()
    elif sys.argv[1]=='compile-exporter':compile_exporter()
    elif sys.argv[1]=='references':references(sys.argv[2])
    else:raise ValueError(sys.argv[1])
