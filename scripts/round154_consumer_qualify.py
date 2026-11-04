"""Finite real-header consumer checks; no optimizer or new production PE."""
from round154_common import *
from round153_build import COMPILER

def build():
    configure();manifest=read(OUT/'candidate_manifest.json');build=WORK/'build-cache/round154/consumer_control'
    build.mkdir(parents=True,exist_ok=False)
    scheduler=next(p for p in manifest['objects'] if Path(p).stem=='ControllingLeafScheduler')
    assert sha(scheduler)==manifest['objects'][scheduler]
    pe=build/'Round154ProofControl.exe'
    command=[COMPILER,*manifest['flags'],ROOT/'scripts/round154_proof_control.cpp',scheduler,'-o',pe]
    assert meter.metered('compile_consumer_control','build',command,timeout=180)==0
    write(OUT/'consumer_control_manifest.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round154_proof_control.cpp'),
        header_SHA=sha(ROOT/'include/Round154Research.hpp'),scheduler_SHA=sha(scheduler),candidate_manifest_SHA=sha(OUT/'candidate_manifest.json')))

def check(label='consumer_control_v1'):
    tick=time.perf_counter();manifest=read(OUT/'consumer_control_manifest.json');assert sha(manifest['PE'])==manifest['PE_SHA']
    p=subprocess.run([manifest['PE']],capture_output=True,text=True,check=True);value=json.loads(p.stdout)
    assert value['PASS'];value.update(manifest_SHA=sha(OUT/'consumer_control_manifest.json'),seconds=time.perf_counter()-tick,Optimize=0)
    write(OUT/'qualification'/label/'result.json',value);print(p.stdout,flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
