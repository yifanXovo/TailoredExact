"""Offline falsifiable check of one possible S-bound bottleneck; no Optimize.

The penalty budget is the ORIGINAL e budget. Its box relaxation is a fractional
knapsack in ratio deviations around clipped one. This diagnostic never changes
the model and does not select a candidate automatically.
"""
from round161_common import *
from round161_qualify import cols
from round161_analyze import instance
from fractions import Fraction as F
import re

def main():
    results=[]
    for role in ('R-X35-S-T2','N-B35-S'):
        folder=OUT/'runs'/f'{role}_RN_LP_v1';c=cols(folder,'actual');d=instance(role)
        point=read(folder/'lp_values.json');block=read(folder/'block.json');ad=read(folder/'admission.json')
        supports={i:[] for i in range(1,d['n']+1)}
        for name,v in c.items():
            m=re.fullmatch(r'state_(\d+)_(\d+)',name)
            if m and v['ub']>0:supports[int(m[1])].append(int(m[2]))
        rlo={i:F(1./d['target'][i])*min(ys) for i,ys in supports.items()}
        rhi={i:F(1./d['target'][i])*max(ys) for i,ys in supports.items()}
        base={i:min(max(F(1),rlo[i]),rhi[i]) for i in supports}
        alpha={i:F(c[f'e_{i}']['obj']) for i in supports}
        initial_cost=sum((alpha[i]*abs(base[i]-1) for i in supports),F(0));budget=F(ad['cutoff'])-initial_cost
        assert budget>=0
        def extreme(upper):
            value=sum(base.values(),F(0));remaining=budget
            for i in sorted(supports,key=lambda i:(alpha[i],i)):
                room=(rhi[i]-base[i]) if upper else (base[i]-rlo[i])
                take=room if not alpha[i] else min(room,remaining/alpha[i]);remaining-=alpha[i]*take
                value+=take if upper else -take
            return value
        sl=max(F(block['S_lower']),extreme(False));su=min(F(block['S_upper']),extreme(True))
        assert sl>0 and su>=sl
        tl,tu=1/su,1/sl;violations=[]
        for i,ys in supports.items():
            for y in ys:
                x=F(point[f'state_{i}_{y}']);w=F(point[f'rn_w_{i}_{y}'])
                violations.append(max(tl*x-w,w-tu*x,F(0)))
        violation=max(violations)
        results.append(dict(role=role,old_S=[block['S_lower'],block['S_upper']],penalty_box_S=[float(extreme(False)),float(extreme(True))],
            combined_S=[float(sl),float(su)],old_t=[block['t_lower'],block['t_upper']],implied_t=[float(tl),float(tu)],
            saved_RN_LP_t=point['rn_t'],max_new_envelope_violation=float(violation),saved_point_excluded=violation>F(1e-7),
            scope='valid bound from existing shared original e penalty/cutoff; only offline saved point, not a reoptimized gain',
            exact_sl=str(sl),exact_su=str(su)))
    write(OUT/'reports/envelope_diagnostic.json',dict(Optimize=0,automatic_revision=False,results=results))
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
