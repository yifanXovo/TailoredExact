"""Pair only covered, scope-verified common checkpoints; never infer speed."""
import csv,json,sys
from round101_common import *
from round101_reporting_core import csv_write
from round100_idle import ensure_idle

def main(label):
    ensure_idle();folder=OUT/label;path=folder/'checkpoints.csv'
    with path.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    groups={};paired=[]
    for r in rows:
        if r['covered']!='True':continue
        key=(r['campaign'],r['role'],r['checkpoint_full_seconds'])
        groups.setdefault(key,{})[r['arm']]=r
    def num(r,key):return float(r[key]) if r[key]!='' else None
    for (camp,role,cp),group in groups.items():
        comparisons=[(ref,arm) for arm in group if arm.startswith('FLEET-') for ref in ['P-GRB','ENS-C']]
        comparisons += [('P-GRB','ENS-C')]
        for ref,arm in comparisons:
            if ref not in group or arm not in group:continue
            a,b=group[ref],group[arm];au,bu,ag,bg=[num(r,k) for r,k in [(a,'U'),(b,'U'),(a,'gap'),(b,'gap')]]
            paired.append(dict(campaign=camp,role=role,checkpoint_full_seconds=float(cp),reference=ref,candidate=arm,
                both_covered=True,reference_certificate=a['certificate']=='True',candidate_certificate=b['certificate']=='True',
                reference_U=au,candidate_U=bu,reference_L=num(a,'L'),candidate_L=num(b,'L'),reference_gap=ag,candidate_gap=bg,
                U_delta=bu-au if au is not None and bu is not None else None,
                gap_delta=bg-ag if ag is not None and bg is not None else None,
                material_U_change=bool(au is not None and bu is not None and abs(bu-au)>=.001 and abs(bu-au)/max(abs(au),1e-12)>=.01),
                material_gap_change=bool(ag is not None and bg is not None and abs(bg-ag)>=.001 and abs(bg-ag)/max(abs(ag),1e-12)>=.1),
                certification_time_ratio=None,combined_certificate=False,
                scope='Same common covered checkpoint; same-run certified endpoints may carry; no interpolation or cross-arm certificate.'))
    csv_write(folder/'checkpoint_pairs.csv',paired)
    write(folder/'checkpoint_pairs_identity.json',dict(passed=True,optimizer_calls=0,pairs=len(paired),
        checkpoint_csv_sha256=sha(path),paired_csv_sha256=sha(folder/'checkpoint_pairs.csv'),script_sha256=sha(__file__),
        materiality=read(OUT/'protocol.json')['materiality']))
    print(json.dumps(dict(passed=True,pairs=len(paired),Optimize=0)))

if __name__=='__main__':main(sys.argv[1])
