"""Independent complement-budget lower counts and integer row validity, no solver."""
from round140_common import *
from fractions import Fraction as F
import bisect,itertools

def main():
    cases=[]
    for folder in sorted((OUT/'roots').iterdir()):
        a=read(folder/'additions.json');supports={int(i):ys for i,ys in a['supports'].items()}
        ratios={int(i):F(c) for i,c in a['ratios'].items()};budget=F(a['Bminus'])
        max_stock=sum(max(ys) for ys in supports.values());loss_budget=max_stock-budget;checked=[]
        for row in a['thresholds']:
            t=F(row['t']);forced=0;cost=[]
            for i,ys in supports.items():
                k=bisect.bisect_left([ratios[i]*y for y in ys],t)
                if k==0:forced+=1
                elif k<len(ys):cost.append(ys[-1]-ys[k-1])
            used=0;low=0
            for v in sorted(cost):
                if used+v>loss_budget:break
                used+=v;low+=1
            ell=forced+len(cost)-low
            assert ell==row['ell'],(folder.name,row['t'],ell,row['ell'])
            checked.append(dict(t=row['t'],ell=ell,optional_low_at_most=low))
        cases.append(dict(role=folder.name,thresholds_checked=len(checked),checks=checked))
    # Full integer inventories from the actual already sealed qualifications
    # and completed formal K20 run; evaluate each physically valid Gini numerator.
    integers=[]
    for path in [OUT/'qualification_matrix.json',OUT/'primary_matrix.json']:
        for g in read(path)['groups']:
            l=g['launch'];e=Path(l['destination'])/'round135_endpoint.json'
            if not e.exists():continue
            inventory=read(e)['H_final_inventory'];a=read(OUT/'roots'/l['id']/'additions.json') if (OUT/'roots'/l['id']/'additions.json').exists() else None
            if a is None:continue
            ratios={int(i):F(c) for i,c in a['ratios'].items()};supported=all(inventory[int(i)] in ys for i,ys in a['supports'].items())
            if not supported:continue
            r=[ratios[i]*inventory[i] for i in sorted(ratios)]
            H=sum(abs(x-y) for j,x in enumerate(r) for y in r[j+1:])
            old=sum(F(a['TC_exact'].get(f'state_{i}_{inventory[i]}','0')) for i in ratios)
            new=F(a['constant_exact'])+sum(F(a['TC2_exact'].get(f'state_{i}_{inventory[i]}','0')) for i in ratios)
            assert old<=H and new<=H
            integers.append(dict(role=l['id'],source_endpoint=str(e),TC_rhs=str(old),TC2_rhs=str(new),true_H=str(H),exact_valid=True))
    write(OUT/'math/complement_count_crosscheck.json',dict(PASS=True,Optimize=0,solver_imports=0,cases=cases,
        independent_method='Maximize number of optional low stations within sum(M)-Bminus by buying ascending minimum inventory losses',integer_inventories=integers))
    print(json.dumps(dict(thresholds=sum(c['thresholds_checked'] for c in cases),integer_inventories=len(integers),Optimize=0)))

if __name__=='__main__':main()
