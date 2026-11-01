"""Bound the one pre-health identity clarification; no algorithm change."""
from round145_build import COMPILER,BUILD,SYSTEM
from round145_common import *
def main():
    configure();old=read(OUT/'candidate_manifest.json');write(OUT/'engineering/pre_identity_candidate_manifest.json',old)
    changed=[p for p,h in old['source_hashes'].items() if sha(ROOT/p)!=h];assert changed==['src/main.cpp'],changed
    obj=BUILD/'identity-main.o';pe=BUILD/'ExactEBRP-jp.exe'
    assert metered('compile_identity_main','build',[COMPILER,*old['flags'],'-c',ROOT/'src/main.cpp','-o',obj],timeout=180)==0
    command=[COMPILER,obj,*old['objects'],old['archive']['path'],*SYSTEM,'-o',pe]
    assert metered('link_identity','build',command,timeout=120)==0
    old.update(source_commit=git('rev-parse','HEAD').decode().strip(),production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        main_object=dict(path=str(obj),SHA=sha(obj)),link_command=list(map(str,command)),identity_clarification='RN-JP has only its own method parameter file; R144 lifecycle engine reused internally')
    old['source_hashes']['src/main.cpp']=sha(ROOT/'src/main.cpp');write(OUT/'candidate_manifest.json',old)
    p=read(ROOT/'config/gi_tbc_rnp_round144.json');p.update(schema='round145-joint-projection-frozen-argv-v1',algorithm='GI-TBC + once-root RN/NC/TS joint original-variable projection',
        source_commit=old['source_commit'],research_head=old['source_commit'],default_executable=str(pe),verified_PE_SHA256=sha(pe),
        round=145,source_manifest='results/unified_exact_round145/candidate_manifest.json',RN_JP=True)
    p.pop('RN_P');p['argv'][-2]='--round145-projection';write(ROOT/'config/gi_tbc_rnjp_round145.json',p)
    print('Identity-only main rebuild and separate research profile complete')
if __name__=='__main__':main()
