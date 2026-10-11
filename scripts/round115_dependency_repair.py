"""One 394-byte signed-authority supplement; no second carrier/export/native run."""
from round115_common import ROOT, OUT, read, write, sha
from pathlib import Path
import hashlib,json,subprocess,sys,time

REL='results/unified_exact_round115/inherited_r113/public_pack_receipt.json'

def prepare():
    authority=ROOT/REL;expected=read(OUT/'inherited_r113/dependency_manifest.json')['files']['public_pack_receipt.json']
    assert sha(authority)==expected and REL not in read(OUT/'compact_evidence/manifest.json')['files']
    write(OUT/'public_dependency_supplement.json',dict(files={REL:dict(SHA=expected,bytes=authority.stat().st_size)},
        original_scientific_payload_commit='fcf9aa4881a76bbbb26f5ec409a74ea384672886',
        reason='current pack-receipt exclusion incorrectly matched an inherited receipt basename',
        second_carrier_or_git_archive=False,admitted_helpers_or_reader_changed=False,Optimize=0))
    write(OUT/'public_dependency_incident.json',dict(step='restored_reader01',exit_code=1,seconds=15.8116806,
        failure='FileNotFoundError: inherited_r113/public_pack_receipt.json absent from public carrier',
        signed_authority_bytes=authority.stat().st_size,original_carrier_manifest_hashes_all_passed=True,
        finite_repair='commit the existing signed leaf and restore its exact Git blob; preserve first failed root/output',
        new_native_starts=0,performance_replay=False,observed_unix=time.time()))
    print(json.dumps(read(OUT/'public_dependency_supplement.json')),flush=True)

def restore(commit,destination):
    tick=time.perf_counter();destination=Path(destination).resolve()
    manifest=json.loads(subprocess.check_output(['git','show',commit+':results/unified_exact_round115/public_dependency_supplement.json'],cwd=ROOT))
    for rel,entry in manifest['files'].items():
        data=subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT)
        assert hashlib.sha256(data).hexdigest()==entry['SHA'] and len(data)==entry['bytes']
        target=destination/rel;assert not target.exists() and target.resolve().is_relative_to(destination)
        expected=read(target.parent/'dependency_manifest.json')['files'][target.name]
        assert expected==entry['SHA']
        with target.open('xb') as f:f.write(data)
        assert sha(target)==entry['SHA']
    receipt=dict(commit=commit,root=str(destination),files=manifest['files'],source='actual committed Git blobs only',
        original_root_core_fallback=False,second_carrier_or_git_archive=False,Optimize=0,native_starts=0,
        seconds=time.perf_counter()-tick,observed_unix=time.time(),future_reconstruction_not_claimed=True)
    write(OUT/'public_dependency_supplement_receipt.json',receipt)
    write(destination/'delivery_receipts/public_dependency_supplement_receipt.json',receipt)
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='restore':restore(sys.argv[2],sys.argv[3])
    else:raise ValueError(sys.argv[1])
