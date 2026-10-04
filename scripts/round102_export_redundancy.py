"""Zero-Optimize exact exported-duration proof of the specific F5 S relation."""
from round102_common import *
from pathlib import Path
from fractions import Fraction as F
def main():
    source=ROOT/'results/unified_exact_round101/diagnostics/lp01/F5/matrix.txt'
    with source.open() as f:
        n,R=map(int,f.readline().split());names=[f.readline().split()[0] for _ in range(n)];rows=[]
        for r in range(R):
            line=f.readline().split();sense,rhs,count=line[:3];terms={names[int(line[t])]:F(line[t+1]) for t in range(3,len(line),2)}
            rows.append((r,sense,F(rhs),terms))
    proofs=[]
    for k in range(4):
        prefix=f'p_{k}_';need={name for name in names if name.startswith(prefix)}
        found=[row for row in rows if row[1]=='<' and row[2]==7200 and need<=row[3].keys() and all(a>=0 for a in row[3].values())
            and all(row[3][name]>=120 for name in need)]
        assert len(found)==1
        r,s,rhs,terms=found[0];proofs.append(dict(vehicle=k,row_index=r,RHS=str(rhs),handling_min=str(min(terms[name] for name in need)),
            quantity_support=len(need),all_remaining_coefficients_nonnegative=True,complete_terms=[[name,str(a)] for name,a in terms.items()]))
    old=read(ROOT/'results/unified_exact_round101/compact_evidence/lp/F5/implication_0.json')['row']['proof']
    c=read(ROOT/'results/unified_exact_round101/compact_evidence/lp/F5/raw.separation.json')['contract']
    caps=sorted(min(c['initial'][i],30) for i,s,q in old['events']);assert sum(caps[:16])==240 and len(caps)==38
    write(OUT/'diagnostics/F5_actual_export_redundancy.json',dict(matrix_sha256=sha(source),proofs=proofs,caps=caps,
        exact_total_pickup_upper='240',exact_knapsack_upper='16',rank=old['rank'],
        proof='Sum four actual nonnegative duration rows, discard travel, divide120. h<=u/U. Fill smallest caps first;16 full caps exhaust240.',
        scope='Specific38-event positive-part S relation on this entire old exported LP, mathematical exact coefficients; no tolerance-feasible enlarged polyhedron or other event family claim',Optimize_calls=0))
    print('F5 specific entire S relation implied by exact actual exported duration rows; Optimize=0')
if __name__=='__main__':main()
