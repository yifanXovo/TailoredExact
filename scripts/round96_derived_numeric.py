"""Offline coefficient replay of saved canonical leaf models; never Optimize.

Replays endpoint/state, centering, cutoff and SP expressions from declared
leaf bounds and input. This checks serialization, not domain validity or an
exact-rational certificate. Previous overwritten model versions are excluded.
"""
import argparse
import collections
import json
import math
import re
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha,citi
from round96_numeric_inputs import expression

def signature(expr,sense,rhs):
    return (tuple(sorted((k,v) for k,v in expr.items() if v)),sense,rhs)

def inspect(path,panel):
    data=citi.parse_instance_mirror(ROOT/panel['input_path']);n=data['V']
    lines=path.read_text().splitlines();bounds={};rows=set();objective=None
    for line in lines:
        if line.startswith(' obj:'):objective=expression(line.split(':',1)[1])
        elif line.startswith(' c'):
            expr,sense,rhs=re.split(r'\s+(<=|>=|=)\s+',line.split(':',1)[1])
            rows.add(signature(expression(expr),sense,float(rhs)))
        elif '<=' in line and ':' not in line:
            parts=line.split()
            if len(parts)==5 and parts[1]==parts[3]=='<=':
                bounds[parts[2]]=(float(parts[0]),float(parts[4]))
    a,b=bounds['G'];assert any(k.startswith('state_g_') for k in bounds)
    # The model's own cutoff, not a later incumbent or cross-arm objective.
    cutoffs=[rhs for expr,sense,rhs in rows if expr==signature(objective,'',0)[0] and sense=='<=']
    assert len(cutoffs)==1,(path,cutoffs)
    cutoff=cutoffs[0];families=collections.Counter();changes=[];largest=0.
    def check(family,terms,sense,rhs,shared=True):
        nonlocal largest
        ideal={};factory={}
        for var,value in terms:
            ideal[var]=ideal.get(var,0.)+value
            if shared and abs(value)<=1e-14:continue
            factory[var]=factory.get(var,0.)+value
            if shared and abs(factory[var])<=1e-14:del factory[var]
        printed={}
        for var,value in factory.items():
            if abs(value)<=1e-12:continue
            printed[var]=math.copysign(1.,value) if abs(abs(value)-1)<=1e-12 else value
        assert signature(printed,sense,rhs) in rows,(path,family,rhs,printed)
        families[family]+=1
        delta={v:printed.get(v,0.)-x for v,x in ideal.items() if printed.get(v,0.)!=x}
        if delta:
            # Whole declared column range, not just one returned witness.
            residual=sum(abs(d)*max(abs(t) for t in bounds[v]) for v,d in delta.items())
            largest=max(largest,residual)
            changes.append(dict(family=family,delta=delta,max_absolute_lhs_change=residual))
    h=[(f'h_{i}_{j}',1.) for i in range(1,n+1) for j in range(i+1,n+1)]
    r=lambda c:[(f'r_{i}',c) for i in range(1,n+1)]
    e=lambda c:[(f'e_{i}',c*data['weights'][i]) for i in range(1,n+1)]
    check('direct_gini_cap',h+r(-n*b),'<=',0.)
    check('direct_gini_floor',h+r(-n*a),'>=',0.)
    sl=su=pl=pu=0.
    for i in range(1,n+1):
        lo,hi=bounds[f'Y_{i}'];d=data['target'][i]
        rl=lo/d;ru=hi/d;sl+=rl;su+=ru
        el=max(0.,1-ru,rl-1);eu=max(abs(rl-1),abs(ru-1))
        pl+=data['weights'][i]*el;pu+=data['weights'][i]*eu
        for y in range(int(lo),int(hi)+1):
            s=f'state_{i}_{y}';q=f'state_g_{i}_{y}'
            check('VDP_lower',[(q,1.),(s,-a)],'>=',0.,False)
            check('VDP_upper',[(q,1.),(s,-b)],'<=',0.,False)
    pu=max(pl,pu)
    for i in range(1,n+1):
        for j in range(i+1,n+1):
            check('pair_spread',[(f'h_{i}_{j}',float(n-1))]+r(-n*b),'<=',0.)
            for positive,negative in [(i,j),(j,i)]:
                check('centering',[(f'r_{positive}',1.),(f'r_{negative}',-1.)],
                      '<=',max(0.,n*b*su/(n-1)))
                check('variable_s_centering',[(f'r_{positive}',float(n-1)),
                      (f'r_{negative}',-float(n-1))]+r(-n*b),'<=',0.)
    lam=panel['lambda']
    check('objective_cutoff',[('G',1.)]+e(lam),'<=',cutoff)
    check('objective_estimator',h+[(f'e_{i}',n*su*lam*data['weights'][i]) for i in range(1,n+1)],'<=',n*su*cutoff)
    check('penalty_lower',e(1.),'>=',pl)
    for sc,pc,sense,rhs in [(-sl,-pl,'>=',-sl*pl),(-su,-pu,'>=',-su*pu),
                           (-su,-pl,'<=',-su*pl),(-sl,-pu,'<=',-sl*pu)]:
        check('SP_McCormick',[('W_SP',1.)]+e(sc)+r(pc),sense,rhs)
    check('SP_estimator',h+r(-n*cutoff)+[('W_SP',n*lam)],'<=',0.)
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),gamma=[a,b],cutoff=cutoff,
        families=dict(families),changed_rows=len(changes),changes=changes,
        maximum_changed_lhs_bound=largest,
        scope='Saved current canonical model only; declared Y bounds are inputs to coefficient replay, their validity is checked by the separate scope/coverage audit.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('campaign',choices=['external','external_v2','primal','primal_v2']);parser.add_argument('label')
    args=parser.parse_args();assert args.label.replace('_','').replace('-','').isalnum()
    campaign=OUT/args.campaign;identity=read(campaign/'identity.json')
    summaries=[json.loads(line) for line in (campaign/'summary.jsonl').read_text().splitlines()]
    records=[]
    for row in summaries:
        assert row['audit_passed']
        if row['arm']=='P-GRB':continue
        launch=identity['launches'][row['number']-1]
        for path in sorted((Path(row['destination'])/'external/models').glob('*.lp')):
            records.append(dict(number=row['number'],role=row['id'],arm=row['arm'],**inspect(path,launch['panel'])))
    assert records
    write(OUT/f'derived_numeric_{args.campaign}_{args.label}.json',dict(passed=True,records=records,
        source_sha256=sha(__file__),summary_sha256=sha(campaign/'summary.jsonl'),optimizer_calls=0,
        limitation='Selected active derived families reconstructed before serialization. No claim that every historical overwritten model, every static family, or arbitrary real input is exact. No change to existing numerical tolerances.'))

if __name__=='__main__':main()
