"""One billed finite native batch; injected failures are labeled explicitly."""
from round112_common import *
from round112_campaign import fee_begin,fee_pending
from round100_idle import ensure_idle

label='start_fault01';d,tick=fee_begin(label,1,180,True);code=1
try:
    ensure_idle();production=check_identity()
    exe=BUILD/'Round112StartFaultBatch.exe'
    cases=OUT/'qualification/start_fault01'
    cmd=[str(exe),str(ROOT/'reference/round100_confirmation/H100.txt'),
        str(OUT/'qualification/reference/H100/original.lp'),str(cases)]
    write(d/'native_launch.json',dict(command=cmd,PE_SHA=sha(exe),production_PE_SHA=production['production_PE_SHA'],
        helper_SHA=sha(__file__),test_source_SHA=sha(OUT/'qualification/start_fault_batch.cpp'),
        production_source_bindings=bindings(),Optimize=0,real_native_read_only_model=True,explicit_fault_injection=True))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        child=subprocess.run(cmd,cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=175)
    assert child.returncode==0,(d/'stderr.log').read_text()
    rows=[json.loads(s) for s in (cases/'cases.jsonl').read_text().splitlines()]
    assert len(rows)==13 and all(r['passed'] and r['native_Optimize_calls']==0 for r in rows)
    write(cases/'necessary_audit.json',dict(passed=True,case_count=13,actual_production_function=True,
        Optimize=0,native_model_read_and_Start_APIs=True,injected_errors_not_claimed_real_Gurobi_failures=True,
        source_bindings=bindings(),case_file_SHA=sha(cases/'cases.jsonl'),inside_outer_clock=True))
    code=0
finally:
    fee_pending(d,tick,True,code,1)
