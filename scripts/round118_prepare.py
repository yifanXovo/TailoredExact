"""Finite setup and one read-only reference wrapper; no main-PE compilation."""
from round118_common import *
from round118_campaign import COMMON
import collections,csv,shutil,subprocess,traceback
import round108_reader as core
from round100_idle import ensure_idle
EXPORTER=ROOT/'build/research/round118-reference/Round118Reference.exe'
ARCHIVE=Path('E:/codes/ExactEBRP-round112/build/research/round112-paid-v1/libexact_ebrp_core.a')

def initialize():
    check_identity();role=read(OUT/'input_manifest.json')['roles'][0]
    write(OUT/'protocol.json',dict(round=118,actual_base=BASE,production_source=SOURCE,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        roles=[role],pairs=[['ENS-C','P-GRB'],['M-B','P-GRB'],['P-S','P-GRB'],['ENS-C','P-S'],['M-B','P-S'],['M-B','ENS-C']],
        common=COMMON,formal_arms=4,each_formal_cap=5400,nominal_seconds=21600,maximum_starts=20,maximum_outer_seconds=28000,
        qualification_maximum_starts=8,qualification_maximum_seconds=1200,
        qualification_plan={'finite_replay':{'starts':1,'cap':180},'reference':{'starts':2,'cap':360},
            'H100_PS_MB':{'starts':3,'cap':600},'post_admission':{'starts':1,'cap':60}},
        qualification_planned_starts=7,qualification_planned_declared_seconds=1200,
        formal_wrapper_children=5,formal_group_reserve=120,main_clock='T_produce',secondary_clock='T_total',
        own_H_seed=20260626,own_H_seeds='24+1 / R76 / R83',gurobi_seed=0,no_cross_arm_transfer=True,
        original_native_window_unchanged=True,default='ENS-C',candidate='M-B finite R111',primary='cold P-GRB',control='P-S',
        materiality={'a_U':'max(.001,.01*abs(U_C))','a_gap':'max(.001,.10*abs(gap_C))','a_t':'max(30,.10*t_C)'},
        closure_tolerance=1e-7,signed_gap_not_clipped=True,positive_analysis_offline_only=True,
        stage_priority=['PROOF_RELIABILITY_PRIORITY','PRIMARY_BENCHMARK_RISK_ON_THIS_ROLE','NONZERO_PROOF_INCREMENT_ON_THIS_ROLE','LIMITED_OR_MIXED_ROLE_EVIDENCE'],
        no_algorithm_change=True,no_performance_retry=True,no_additional_input_or_seed=True))
    policy='''# Round118 prospective measurement-v2

The four fixed arms, in order cold P-GRB, M-B, P-S, ENS-C, each receive a 5400-second producer cap. First-arm origin is the wrapper OS creation; later origins precede each admission. H, all online model/physical checks, Start, journal, deadline/resource supervision, native cleanup, serialization and producer sealing are included. The original cap-minus6 CLI TimeLimit, absolute work deadline, 30-second reserve and cap-minus2 hard stop are retained. No timer restarts after H or Optimize.

After native exit and a closed producer seal, serial independent verification reads existing models, fleets, calls, Starts and coverage. It may confirm or revoke claims, and cannot reenter a solver, create a better fleet, add a bound or backfill certification. T_verify includes receipt management and complete closeout; T_total has the identical origin and equals T_produce+T_verify. A verify interval over 30 seconds or a T_total over the producer cap does not itself disqualify a valid within-cap producer. Final cohort checks are group cost, not assigned to a later method.

Call-scoped immutable-model/log-byte views repair the inherited read-only evidence readers. This is a new qualified helper identity, not unchanged old-helper admission or solver performance. UNRESOLVED model/return/log matching stops before formal execution. Proven same-domain contradictions revoke the affected call and dependent closure; a verified independent own fleet and inherited floor0 may remain SOURCE_REDUCED_OPEN. The new positive-objective arithmetic is never an online or formal lower bound.

Budgets are 20 conservative starts / 28000 observed outer seconds; qualification and reference subbudget is 8 / 1200. A failed declared slot is permanently paid. The qualification plan is replay1/180, reference wrapper+exporter2/360, H100 wrapper+two children3/600, post/admission1/60. The formal wrapper+four children consumes5 slots and reserves21600+120 seconds; actual necessary verification is additionally paid within the total envelope. Nested times are not added again. Pure static/data/dependency/compilation/export/restore engineering is itemized separately; unknown human time is unknown.

Cold-reference fingerprint is a deterministic numeric readback slot in the pre-export argv contract; all algorithm/input/deadline arguments are already literal. It is resolved once from the frozen zero-Optimize exporter, before any H100 or formal Optimize. The final resolved argv is bound at admission. No reference result is used to choose the input, horizon, cap, method or order.
'''
    (OUT/'measurement_policy_v2.md').write_text(policy,encoding='utf-8',newline='\n')
    dependency='''# Small Round118 dependency table

| Dependency | Current use | Boundary |
|---|---|---|
| R117 safe tree / safe manifest and selected members | Static table/response, H100 cold reference, finite V20 call fixtures | No polluted R116 carrier, HTML recovery or network |
| R57 pure functions + R109 pure landscape | New thin offline adapter; new FAMILY throughout | R116 acquisition/generation main remains disabled |
| R115 producer extraction and v2 seal/closeout | Original PE, supervisor, physical check and clock | New root and manifest; no old one-group/cap assertion |
| R114 claim/return policies + R108 model/cover reader | Healthy and rejected call checks | Explicit byte segment, immutable model and serial ledger binding; unresolved rejects |
| R94 preregistration common fields | Legacy import-only static dependency | Current safe Git blob only; no old campaign launch |
| Frozen R112 core archive and compiler | Read-only single-input cold exporter | 0 Optimize; main PE not compiled |
| New finite and post/admission drivers | One batch, H100 P-S then M-B | 8 starts/1200 maximum; no V40 H pilot |

Historical helper SHA values remain historical code identities. Current repaired readers and the new adapter receive new identities. R117 alert1 remains open/validity unknown absent a later issuer/owner receipt. R116 positions19–24 stay canceled and position18 historical BLOCKED.
'''
    (OUT/'dependency_table.md').write_text(dependency,encoding='utf-8',newline='\n')
    p=role;row='\t'.join(map(str,[p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],OUT/'qualification/reference'/p['id']]))
    (OUT/'qualification/reference_batch.tsv').write_text(row+'\n',encoding='utf-8',newline='\n')
    print('current protocol, v2 measurement and bounded dependency table saved')

def compile_exporter():
    ensure_idle();check_identity();tick=time.perf_counter();d=OUT/'engineering/reference_compile01';d.mkdir(parents=True,exist_ok=False)
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe');assert sha(compiler)==read(OUT/'production_identity.json')['compiler_SHA']
    original=read(ROOT/'results/unified_exact_round112/production_identity.json');assert original['source_bindings']==bindings()
    EXPORTER.parent.mkdir(parents=True,exist_ok=True)
    cmd=[str(compiler),'-std=c++17','-DEXACT_EBRP_ENABLE_GUROBI=1','-I'+str(ROOT/'include'),'-ID:/gurobi1302/win64/include',
        str(ROOT/'scripts/round118_reference.cpp'),str(ARCHIVE),'-o',str(EXPORTER)]
    write(d/'launch.json',dict(command=cmd,compiler_SHA=sha(compiler),frozen_core_archive_SHA=sha(ARCHIVE),frozen_model_source=SOURCE,
        production_PE_SHA_before=sha(PE),Optimize=0,native_starts=0,engineering=True))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        result=subprocess.run(cmd,cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=600)
    write(d/'receipt.json',dict(exit_code=result.returncode,seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        production_PE_SHA_after=sha(PE),exporter_SHA=sha(EXPORTER) if EXPORTER.exists() else None))
    assert result.returncode==0,'auxiliary compilation failed; see local engineering stderr'
    check_identity();print('read-only exporter built; frozen production PE unchanged')

def reference(label):
    from round118_campaign import helpers
    fee,tick=fee_begin(label,1,360,True);code=1;actual=0
    try:
        ensure_idle();check_identity();assert sha(EXPORTER)==read(OUT/'engineering/reference_compile01/receipt.json')['exporter_SHA']
        p=read(OUT/'input_manifest.json')['roles'][0];d=OUT/'qualification/reference'/p['id'];assert not d.exists()
        with (fee/'stdout.log').open('xb') as so,(fee/'stderr.log').open('xb') as se:
            child=subprocess.Popen([str(EXPORTER),str(OUT/'qualification/reference_batch.tsv')],cwd=ROOT,env=env(),stdout=so,stderr=se);actual=1
            write(fee/'child.json',dict(pid=child.pid,exporter_SHA=sha(EXPORTER),Optimize=0))
            try:rc=child.wait(timeout=max(1.,360-(time.perf_counter()-tick)))
            except BaseException:child.kill();child.wait();raise
        assert rc==0,'read-only exporter failed'
        b=read(d/'build.json');native=read(d/'native_metadata.json')
        assert b['optimizer_calls']==native['Optimize']==0 and sha(d/'original.lp')==b['canonical_sha256']
        m=core.lp_model(d/'original.lp');assert len(m['order'])==b['columns']==native['columns'] and len(m['rows'])==b['rows']==native['rows']
        with (d/'native_columns.csv').open(newline='') as f:cols=list(csv.DictReader(f))
        assert len(cols)==len(m['order'])
        obj=dict(m['objective'][0])
        # The native LP loader can reorder columns; reference retains both actual order and canonical grammar.
        assert collections.Counter(q['type'] for q in cols)==collections.Counter(m['types'].values())
        coefficients=[abs(v) for row,_,_ in m['rows'] for _,v in row if v]
        write(d/'reference_contract.json',dict(input_parameters=p,canonical_SHA=sha(d/'original.lp'),actual_types=dict(collections.Counter(q['type'] for q in cols)),
            native_columns_SHA=sha(d/'native_columns.csv'),native_rows_SHA=sha(d/'native_rows.csv'),native_metadata=native,
            objective=m['objective'],coefficient_min=min(coefficients),coefficient_max=max(coefficients),Optimize=0,no_LP_or_MIP_solved=True))
        assert time.perf_counter()-tick<360;code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)

if __name__=='__main__':
    if sys.argv[1]=='initialize':initialize()
    elif sys.argv[1]=='compile':compile_exporter()
    elif sys.argv[1]=='reference':reference(sys.argv[2])
    else:raise ValueError(sys.argv[1])
