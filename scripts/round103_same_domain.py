"""Check inherited finite directions on the actually declared C++ domain."""
from round103_hull import *
if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle();label=sys.argv[1];directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False);records=[]
    roles={r['id']:r for r in read(OUT/'development_inputs.json')['roles']}
    for role_id,parent in [('R98-C2','capacity_C2_01'),('F5','capacity_F5_01'),('F2','capacity_F2_01')]:
        d=directory/role_id;d.mkdir();oracle=Oracle(roles[role_id],OUT/'diagnostics'/parent/'matrix.txt',d)
        try:
            for family in ['actual-direction','fixed-charge']:
                saved=read(ROOT/'results/unified_exact_round102/compact_evidence/lp'/role_id/(family+'.json'))
                weights=saved['support_certificate']['weights'];proofs=[oracle.support(k,w) for k,w in enumerate(weights)]
                rhs=sum(r['upper'] for r in proofs)
                records.append(dict(role=role_id,family=family,inherited_rhs=saved['rhs'],same_domain_rhs=rhs,identical=exact(saved['rhs'])==rhs,proofs=proofs))
        finally:oracle.close()
    write(directory/'summary.json',dict(records=records,Optimize_calls=0,DP_calls=sum(len(r['proofs']) for r in records),all_identical=all(r['identical'] for r in records)))
    print(json.dumps(dict(all_identical=all(r['identical'] for r in records),DP_calls=sum(len(r['proofs']) for r in records))))
