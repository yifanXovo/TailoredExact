"""Paid post-seal reference-path repair; all frozen native positions stay sealed."""
from round119_common import *
import shutil,traceback

def billed(label):
    fee,tick=fee_begin(label,0,120,False,dict(starts=12,seconds=20160));code=1
    try:
        from round100_idle import ensure_idle
        ensure_idle();identity();copied=[]
        plans=read(OUT/'argv_freeze.json')['plans']
        for plan in plans:
            i=read(OUT/plan['name']/'identity.json');role=i['launches'][0]['id']
            source=OUT/'qualification/reference'/role;target=OUT/plan['name']/'reference'/role
            for p in sorted(source.iterdir()):
                if not p.is_file():continue
                dest=target/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
                if dest.exists():assert sha(dest)==sha(p)
                else:shutil.copyfile(p,dest)
                copied.append(dict(source=p.relative_to(ROOT).as_posix(),destination=dest.relative_to(ROOT).as_posix(),SHA=sha(dest)))
            assert sha(target/'original.lp')==i['launches'][0]['panel']['reference']['canonical_sha256']
        failed=OUT/'reconstruction/group01';saved=OUT/'reconstruction/failed_group01_attempt01'
        assert failed.resolve().is_relative_to(OUT.resolve()) and saved.resolve().is_relative_to(OUT.resolve())
        assert failed.is_dir() and not saved.exists() and not (failed/'current_core.json').exists()
        failed.rename(saved)
        write(fee/'repair.json',dict(kind='missing read-only reference file path',members=copied,
            actual_old_frozen_exporter_outputs_reused=True,producer_or_native_reentry=False,
            production_bytes_changed=False,reader_bytes_changed=False,mathematical_contract_changed=False,
            preserved_failed_directory=saved.relative_to(ROOT).as_posix(),formal_slot_rerun=False))
        from read_round119 import rebuild_group
        value=rebuild_group(1,OUT/'reconstruction/group01')
        write(fee/'reconstruction_receipt.json',dict(current_core_SHA=sha(OUT/'reconstruction/group01/current_core.json'),
            all_three_arms_verified=all(a['formal_protocol_qualified'] for a in value['arms']),
            actual_postseal_seconds=time.perf_counter()-tick,Optimize=0,native_children=0))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,False,code,0)
if __name__=='__main__':billed(sys.argv[1])
