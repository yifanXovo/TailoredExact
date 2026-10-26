"""Deferred document work in this active run, strictly after serial native closeout."""
from round134_common import *

def main():
    wall=time.time();waiting=time.perf_counter()
    if '--wait' in sys.argv:
        while True:
            state=read(OUT/'sequence_driver_status.json')['state']
            if state=='COMPLETE_C_D_E_NATIVE':break
            assert state!='FAILED_PRESERVE','native sequence failed: preserve and inspect; do not export partial paper'
            assert time.perf_counter()-waiting<57600
            time.sleep(30)
    assert read(OUT/'sequence_driver_status.json')['state']=='COMPLETE_C_D_E_NATIVE'
    assert not budget()['unclosed']
    resume='--resume-after-plot-runtime' in sys.argv
    prior=OUT/'delivery/document_pipeline01'
    if resume:
        state=read(prior/'status.json');oldsteps=read(prior/'steps.json')
        assert state['state']=='FAILED_PRESERVE' and state['stage']=='plots'
        assert oldsteps[0]['stage']=='scientific_closeout' and oldsteps[0]['exit_code']==0
        assert read(OUT/'scientific_closeout.json')['passed']
    folder=OUT/('delivery/document_pipeline02' if resume else 'delivery/document_pipeline01')
    folder.mkdir(parents=True,exist_ok=False)
    write(folder/'launch.json',dict(UTC=utc(),waiting_started_unix=wall,
        wait_seconds_not_compute=time.perf_counter()-waiting,native_Optimize=0,production_compile=0,
        prior_failure_SHA=sha(prior/'status.json') if resume else None,
        scientific_closeout_reused_without_repeat=resume))
    steps=[('scientific_closeout',PYTHON,'round134_closeout.py',[]),
        ('plots',DOCUMENT_PYTHON,'round134_plots.py',[]),
        ('assemble',PYTHON,'round134_documents.py',['assemble']),
        ('PDF',PYTHON,'round134_documents.py',['pdf'])]
    if resume:steps=steps[1:]
    records=[]
    for label,runtime,script,args in steps:
        assert not budget()['unclosed']
        command=[runtime,ROOT/'scripts'/script,*args];tick=time.perf_counter()
        write(folder/'status.json',dict(UTC=utc(),stage=label,state='RUNNING',no_native_compute=True))
        with (folder/(label+'.stdout.log')).open('xb') as stdout,(folder/(label+'.stderr.log')).open('xb') as stderr:
            result=subprocess.run(command,cwd=ROOT,env=environment(),stdout=stdout,stderr=stderr,timeout=1800)
        record=dict(stage=label,command=list(map(str,command)),exit_code=result.returncode,
            separate_document_delivery_seconds=time.perf_counter()-tick,native_Optimize=0,production_compile=0)
        records.append(record);write(folder/'steps.json',records)
        if result.returncode:
            write(folder/'status.json',dict(UTC=utc(),stage=label,state='FAILED_PRESERVE',no_automatic_retry=True))
            raise SystemExit(result.returncode)
    write(folder/'status.json',dict(UTC=utc(),state='DOCUMENTS_EXPORTED_REQUIRES_VISUAL_QA',
        separate_document_delivery_seconds=sum(r['separate_document_delivery_seconds'] for r in records),
        native_Optimize=0,production_compile=0,visual_QA_complete=False))
    print('Document pipeline complete; actual visual QA and final integrated review remain')

if __name__=='__main__':main()
