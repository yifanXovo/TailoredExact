"""Restore measured qualification source bytes from the recorded inverse edits.
Writes a separate archive only; never changes production source or executables.
The missing measured PE remains missing. A rebuilt PE is not its replacement.
"""
import json
from round101_common import *

def main():
    paths=['src/FleetEventCuts.cpp','src/GurobiBaseline.cpp','src/round101_fleet_diagnostic.cpp']
    before=read(OUT/'native01/identity.json')['source_hashes']
    after=read(OUT/'isolation01/identity.json')['source_hashes']
    restored={p:(ROOT/p).read_bytes().decode('utf-8') for p in paths}
    assert all(sha(ROOT/p)==after[p] for p in paths)
    for edit in read(OUT/'builds/native01_source_inverse_edits.json'):
        path,old,new=(edit[k] for k in ['path','old','new'])
        assert path in restored
        if not new:
            # The one removed helper had no hunk context in the recorded edit.
            assert old=='int bits(unsigned int b) { int n=0;for(;b;b&=b-1)++n;return n; }\n'
            anchor='std::vector<double> tours('
            assert restored[path].count(anchor)==1
            restored[path]=restored[path].replace(anchor,old+anchor,1)
        else:
            assert restored[path].count(new)==1,(path,new[:100])
            restored[path]=restored[path].replace(new,old,1)
    output=OUT/'builds/native01_source_recovery'
    for p,data in restored.items():
        import hashlib
        actual=hashlib.sha256(data.encode('utf-8')).hexdigest()
        assert actual==before[p],(p,actual,before[p])
    if output.exists():
        assert all(sha(output/p)==before[p] for p in paths)
        print(json.dumps(dict(passed=True,verified_recovered_sources=3,measured_binary_preserved=False)))
        return
    output.mkdir(exist_ok=False)
    for p,data in restored.items():
        q=output/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data.encode('utf-8'))
    write(output/'manifest.json',dict(source_sha256={p:before[p] for p in paths},
        unchanged_sources='native01/identity.json; current bytes match those hashes',
        recovery='inverse of recorded cost and warning edits; every restored byte hash matches the prospectively recorded native01 identity',
        measured_binary_preserved=False,measured_binary_sha256=read(OUT/'native01/identity.json')['candidate_binary_sha256'],
        limitation='The measured v1 PE was overwritten. Recovered source is not a recovered measured binary. All later build05 binaries are archived separately.'))
    print(json.dumps(dict(passed=True,recovered_sources=3,measured_binary_preserved=False)))

if __name__=='__main__':main()
