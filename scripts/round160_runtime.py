"""Preserve final measured PE and recover the exact earlier development PE."""
import shutil,struct
from round160_common import *

def preserve():
    target=OUT/'runtime';target.mkdir(parents=True,exist_ok=True)
    manifest=read(OUT/'candidate_manifest.json')
    for source,name,digest in [(Path(manifest['production_PE']),'ExactEBRP.exe',manifest['production_PE_SHA']),
        (PE,'Round160Research_v4.exe',read(OUT/'build_manifest.json')['PE_SHA'])]:
        assert sha(source)==digest;shutil.copyfile(source,target/name);assert sha(target/name)==digest

def checksum(raw,offset):
    data=bytearray(raw);data[offset:offset+4]=b'\0'*4
    if len(data)%2:data+=b'\0'
    value=0
    for pos in range(0,len(data),2):
        value+=data[pos]+(data[pos+1]<<8);value=(value&65535)+(value>>16)
    value=(value&65535)+(value>>16);value=(value&65535)+(value>>16)
    return (value&65535)+len(raw)

def recover_v3():
    configure();preserve();manifest=read(OUT/'engineering/build_v3.json')
    snapshot=read(OUT/'engineering/source_snapshots/build_v3.json')
    folder=WORK/'temp/round160/recover_core_v3';folder.mkdir(parents=True,exist_ok=False)
    sources=[]
    for name in ['src/Round160PhysicalNeighborhood.cpp','src/round160_research_main.cpp']:
        digest=snapshot['files'][name];source=OUT/'engineering/source_bytes'/f'{digest}.txt'
        path=folder/Path(name).name;path.write_bytes(source.read_bytes());assert sha(path)==digest;sources.append(path)
    sources+=[ROOT/'src'/name for name in ['Parser.cpp','Evaluator.cpp','Result.cpp']]
    candidate=folder/'Round160Research.exe'
    flags=manifest['flags'];command=[manifest['compiler'],*flags,*sources,DLL,'-o',candidate]
    assert meter.metered('recover_core_v3_build','build',command,timeout=300,cwd=ROOT)==0
    raw=bytearray(candidate.read_bytes());pe=struct.unpack_from('<I',raw,60)[0];assert raw[pe:pe+4]==b'PE\0\0'
    stamp_offset=pe+8;sum_offset=pe+24+64
    receipt=read(OUT/'fees/compile_v3/receipt.json');found=None
    stamps=[0]+list(range(int(receipt['start_unix'])-2,int(receipt['end_unix'])+3))
    for stamp in stamps:
        value=bytearray(raw);struct.pack_into('<I',value,stamp_offset,stamp)
        struct.pack_into('<I',value,sum_offset,checksum(value,sum_offset))
        if hashlib.sha256(value).hexdigest()==manifest['PE_SHA']:found=(stamp,value);break
    result=dict(UTC=utc(),target_SHA=manifest['PE_SHA'],finite_rebuild=True,original_sources=snapshot,
        compilation_separately_metered=True,new_Optimize=0,tries=len(stamps),
        reason='Development build v4 replaced the common build output; retain exact measured v3 identity by finite source/PE metadata recovery',
        exact_measured_bytes_recovered=found is not None)
    if found:
        path=OUT/'runtime/Round160Research_core_v3.exe';path.write_bytes(found[1])
        assert sha(path)==manifest['PE_SHA'];result.update(carrier_PE=path.relative_to(ROOT).as_posix(),TimeDateStamp=found[0])
    write(OUT/'runtime_recovery.json',result);print(json.dumps({k:v for k,v in result.items() if k!='original_sources'}),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
