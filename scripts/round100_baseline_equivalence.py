"""Read-only original P matrix binding against the actual R99 campaign."""
from round100_common import *
if __name__=='__main__':
    old=read(ROOT/'results/unified_exact_round99/factorial01/identity.json')['references']
    now=read(OUT/'development01/identity.json')['references']
    assert old==now,('original P matrix drift',old,now)
    write(OUT/'P_baseline_equivalence.json',dict(passed=True,optimizer_calls=0,
        source='actual R99 factorial01 identity, not delivery-head inference',reference=now,
        compared=['ordered original LP SHA','native fingerprint','rows','columns','Optimize=0'],
        new_reference_production_source=read(OUT/'development01/identity.json')['source_hashes'],
        new_reference_binary_sha256=read(OUT/'development01/identity.json')['reference_binary_sha256']))
    print('all three original P matrices exactly match R99; Optimize=0')
