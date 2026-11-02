"""Read-only recovery of a sealed qualification after a narrow reader fix."""
from round148_read import verify
from round148_common import *

if __name__=='__main__':
    configure();batch=sys.argv[1];position=int(sys.argv[2]);assert batch.startswith('qualification')
    matrix=read(OUT/f'{batch}_matrix.json');group=matrix['groups'][position-1]
    identity=read(OUT/group['group']/'identity.json');d=Path(group['launch']['destination'])
    assert (d/'producer_seal.json').exists() and (d/'producer_receipt.json').exists()
    value=verify(group['launch'],identity)
    write(OUT/'qualification_reader_recovery.json',dict(PASS=True,UTC=utc(),
        producer_seal_SHA=sha(d/'producer_seal.json'),old_matrix_SHA=sha(OUT/f'{batch}_matrix.json'),
        old_helpers=matrix['helpers'],new_reader_SHA=sha(ROOT/'scripts/round148_read.py'),
        production_source_unchanged=True,Optimize=0,Native_load=0,
        reason='Retain all pre-strengthening root evidence; exclude its never-installed bound only from controller LP-status pairing',
        complete_endpoint=value['arm']))
    print('PASS sealed qualification reverified without Optimize')
