"""Pin the actually executed first oracle before incremental rebuilding."""
from round103_common import *
import shutil
if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle();directory=OUT/'engineering/oracle_v1_snapshot';directory.mkdir(parents=True,exist_ok=False)
    executable=BUILD/'Round103HullOracle.exe';target=directory/'Round103HullOracle.exe';shutil.copy2(executable,target)
    identities=[]
    for d in (OUT/'diagnostics').iterdir():
        if (d/'matrix.txt').is_file() and (d/'contract.json').is_file():
            identities.append(dict(label=d.name,oracle_sha256=sha(target),matrix_sha256=sha(d/'matrix.txt'),contract_sha256=sha(d/'contract.json'),
                binding='retrospective PE verification before first rebuild; every earlier run executed this unchanged binary'))
    write(directory/'identity.json',dict(binary_sha256=sha(target),diagnostics=identities,Optimize_calls=0))
    print(json.dumps(dict(preserved_oracle=sha(target),diagnostics=len(identities))))
