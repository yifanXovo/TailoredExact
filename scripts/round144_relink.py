"""Targeted lifecycle fix: rebuild only the changed tree unit, preserve lineage."""
from round144_build import COMPILER,SYSTEM
from round144_common import *
configure()
def main():
    old=read(OUT/'candidate_manifest.json');changed=[p for p,h in old['source_hashes'].items() if sha(ROOT/p)!=h]
    assert changed==['src/PaperExternalGiniTree.cpp'],changed
    assert not budget()['unclosed'];b=WORK/'build-cache/round144-v5';b.mkdir(parents=True,exist_ok=False)
    for p,h in old['objects'].items():assert sha(p)==h
    assert sha(old['main_object']['path'])==old['main_object']['SHA']
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    assert metered('compile_lifecycle_tree_v5','build',[COMPILER,*old['flags'],'-c',ROOT/'src/PaperExternalGiniTree.cpp','-o',b/'PaperExternalGiniTree.o'],timeout=600)==0
    objects=[b/'PaperExternalGiniTree.o' if Path(p).stem=='PaperExternalGiniTree' else Path(p) for p in old['objects']]
    command=[COMPILER,old['main_object']['path'],*objects,old['archive']['path'],*SYSTEM,'-o',b/'ExactEBRP.exe']
    assert metered('link_lifecycle_v5','build',command,timeout=120)==0
    write(OUT/'engineering/build_history/before-v5.json',old)
    m=dict(old,source_commit=git('rev-parse','HEAD').decode().strip(),compiled_units=['PaperExternalGiniTree'],round_affected_units=['ObjectiveResourceCompression','GurobiBaseline','PaperExternalGiniTree','main'],
        inherited_candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),objects={str(p):sha(p) for p in objects},link_command=list(map(str,command)))
    m['source_hashes']=dict(old['source_hashes']);m['source_hashes'][changed[0]]=sha(ROOT/changed[0])
    for key in ['production','research']:m[key+'_PE']=str(b/'ExactEBRP.exe');m[key+'_PE_SHA']=sha(b/'ExactEBRP.exe')
    write(OUT/'candidate_build.json',m);write(OUT/'candidate_manifest.json',m)
if __name__=='__main__':main()
