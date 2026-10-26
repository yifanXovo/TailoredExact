"""Actually restore and reconstruct in new roots using public-only stdlib children."""
from round107_common import *

def verify(public,restored,reconstructed):
    from round100_idle import ensure_idle
    ensure_idle();public=Path(public).resolve();restored=Path(restored).resolve();reconstructed=Path(reconstructed).resolve()
    assert public.is_dir() and not restored.exists() and not reconstructed.exists()
    folder=OUT/'restoration';folder.mkdir(exist_ok=True);executions=[]
    def execute(name,command,cwd):
        tick=time.perf_counter();start=time.time();before=dict(command=list(map(str,command)),cwd=str(cwd),started_unix=start)
        write(folder/(name+'_before.json'),before)
        with (folder/(name+'_stdout.log')).open('x') as so,(folder/(name+'_stderr.log')).open('x') as se:
            process=subprocess.Popen(list(map(str,command)),cwd=cwd,stdout=so,stderr=se)
            code=process.wait(timeout=600)
        result=dict(before,pid=process.pid,returncode=code,engineering_seconds=time.perf_counter()-tick,Optimize_calls=0,IIS_calls=0)
        write(folder/(name+'_after.json'),result);executions.append(result);assert code==0,(name,code)
    execute('restore01',[PYTHON,'-B',public/'scripts/round107_restore.py','--public-root',public,'--out',restored],public)
    execute('reader01',[PYTHON,'-B',restored/'scripts/round107_reader.py','--root',restored,'--out',reconstructed,'--compare',restored/'results/unified_exact_round107/reports05'],restored)
    restoration=read(restored/'restore_receipt.json');replay=read(reconstructed/'reader_receipt.json')
    assert restoration['public_parts_only'] and not restoration['original_workspace_reads'] and replay['compared_fields']>0
    expected=read(OUT/'reports05/summary.json');assert replay['summary']==expected
    write(folder/'isolated_verification.json',dict(public_root=str(public),restored_root=str(restored),reconstructed_root=str(reconstructed),
        executions=executions,restore_receipt=restoration,reader_receipt=replay,
        all_published_CSV_fields_reconstructed_and_compared=True,summary_and_frozen_gate_exact_match=True,
        original_workspace_used_by_stdlib_children=False,solver_performance_rerun=False,Optimize_calls=0,IIS_calls=0))
    print(json.dumps(dict(restored=str(restored),compared_fields=replay['compared_fields'],Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':verify(*sys.argv[1:4])
