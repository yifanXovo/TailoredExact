"""Independent R125 bounded arithmetic and source-contract review.

No optimizer, production import/compile, route generation or H search.
Decision adapters are transparent specifications, not execution of C++.
Source assertions pin important control-flow properties separately.
"""
from fractions import Fraction as Q
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / 'src'
EPS = 1e-7
facts = []

def fact(name, condition, detail):
    assert condition, name
    facts.append(dict(name=name, passed=True, detail=detail))

def relevant(leaf, cutoff=1.):
    return (not leaf.get('replaced', False) and leaf['status'] in ('Open', 'Invalid')
            and leaf['lo'] < cutoff-EPS and leaf['bound'] < cutoff-EPS)

def next_rule(bound, others, reached=False):
    if not all(math.isfinite(v) for v in [bound]+others):
        return 'ERROR', None
    if any(v+EPS < bound for v in others):
        return 'REQUEUE', None
    if reached:
        return 'LOOKAHEAD', None
    higher = [v for v in others if v > bound+EPS]
    return ('NEXT', min(higher)) if higher else ('LOOKAHEAD', None)

closed = dict(status='Closed', lo=0.2, bound=0.4)
fact('closed floor is not a NEXT competitor',
     not relevant(closed) and next_rule(.2, []) == ('LOOKAHEAD', None)
     and next_rule(.2, [.4]) == ('NEXT', .4),
     'Including a proof-cover Closed leaf as a scheduling competitor changes the action.')
fact('NEXT requeue precedes reached milestone',
     next_rule(.35, [.2, .6], True) == ('REQUEUE', None),
     'Already-reached milestone does not override a lower relevant open competitor.')
fact('NEXT milestone permits later lookahead',
     next_rule(.35, [.4, .6], True) == ('LOOKAHEAD', None),
     'No timed quantum and no fresh NEXT target after the retained milestone.')

def am(bound, upper, children):
    gap=max(upper-bound,EPS)
    v=[min(1.,max(0.,(x-bound)/gap)) for x in children]
    score=min(v)*sum(v)/2
    scale=max(1.,abs(bound),abs(upper),*(abs(x) for x in children))
    tol=min(1.,max(EPS,32*2**-52*scale)/gap+32*2**-52)
    return ('TERMINAL' if min(children)<=bound+EPS else
            'SPLIT' if score+tol>=.08 else 'CHILD', score, tol)

fact('three AM actions',
     [am(.2,1.,x)[0] for x in [( .21,.3),(.2,.9),(.5,.6)]]
     == ['CHILD','TERMINAL','SPLIT'],
     'Fixed teaching states; no LP solve. AM uses raw child bounds.')

snapshot_path=HERE/'independent_source_excerpts.json'
snapshot=json.loads(snapshot_path.read_text(encoding='utf-8')) if snapshot_path.exists() else {}
if (SRC/'PaperExternalGiniTree.cpp').exists():
    cpp=(SRC/'PaperExternalGiniTree.cpp').read_text(encoding='utf-8')
    epoch=cpp.split('if (state.artifact_ready &&\n            state.artifact_incumbent_epoch != incumbent_epoch)',1)[1].split('if (state.artifact_ready)',1)[0]
    source_mode='current frozen source read'
else:
    epoch=snapshot['epoch_invalidation_excerpt']
    source_mode='compact saved source excerpts; no source revalidation'
fact('epoch invalidation source leaves milestone intact',
     'state.c6_children_ready = false' in epoch
     and 'state.lp_complete = false' in epoch
     and 'c6_frontier_milestone_reached' not in epoch,
     'Direct source text assertion within active ensureArtifact invalidation block.')
if (SRC/'Round83BlockExchange.cpp').exists():
    neutral_full=(SRC/'Round83BlockExchange.cpp').read_text(encoding='utf-8')
    neutral=neutral_full.split('if(!checked.feasible',1)[1].split('result.routes=std::move(next)',1)[0]
else:
    neutral=snapshot['neutral_admission_excerpt']
fact('neutral source uses exact equality and full potential',
     'checked.objective!=result.verification.objective' in neutral
     and 'checked.final_inventory!=result.verification.final_inventory' in neutral
     and 'round78DurationPotential(checked)!=move.duration_potential' in neutral
     and '!(move.duration_potential<round78DurationPotential(result.verification))' in neutral,
     'Direct source assertions; not a rerun of the physical neighborhood.')
fact('neutral tolerance substitution would alter acceptance',
     Q(1,10)+Q(1,10**12)!=Q(1,10)
     and not ([101,1] < [100,99]) and sum([101,1])<sum([100,99]),
     'A tiny objective increase and an earlier duration increase are rejected despite small residual or lower sum.')

count=0
for ratios in product([Q(0),Q(1,2),Q(1),Q(3,2)],repeat=3):
    S=sum(ratios); A=sum(abs(a-b) for a,b in combinations(ratios,2))
    G=A/(3*S) if S else Q(0)
    P=sum(w*abs(r-1) for w,r in zip([Q(1),Q(2,3),Q(1,3)],ratios))
    lam=Q(3,20);cutoff=G+lam*P+Q(1,10); Sbar=Q(9,2)
    assert all(A>=2*abs(a-b) for a,b in combinations(ratios,2))
    assert A+3*lam*S*P<=3*cutoff*S
    assert A+3*lam*Sbar*P<=3*Sbar*cutoff
    W=S*P;Pl=Q(0);Pu=Q(2);Sl=Q(0)
    assert W>=Sl*P+Pl*S-Sl*Pl
    assert W>=Sbar*P+Pu*S-Sbar*Pu
    assert W<=Sbar*P+Pl*S-Sbar*Pl
    assert W<=Sl*P+Pu*S-Sl*Pu
    count+=1
fact('tight physical Gini scalar SP inequalities',True,
     dict(fixed_ratio_vectors=count, exact_fraction_arithmetic=True, includes_S_zero=True))

# Complete tiny physical point illustrating the already-disclosed closure guard.
# n=2, C=D=(1,1), initial (1,0), Q=1; coincident coordinates, h=2,T=2.
# Empty fleet has U; the declared route 0,1,2,0 with +1,-1 has F<U.
# Interval [1/2,1/2], tiny strictly positive weights retain both inventory states.
weights=[Q(1,10**10),Q(5,10**10)]
upper=Q(1,2)+weights[1]
improver=Q(1,2)+weights[0]
alpha=Q(1,2);Pfloor=Q(0)
fact('nonstrict numerical closure is not exact infeasibility',
     improver<upper and alpha+Pfloor>=upper-Q(1,10**9),
     dict(n=2,C=[1,1],D=[1,1],initial=[1,0],Q=1,h=2,T=2,
          coordinates='all zero',lambda_value=1,weights=[str(x) for x in weights],
          interval=['1/2','1/2'],own_empty_U=str(upper),declared_route=[0,1,2,0],
          declared_operations=[1,-1],physical_F=str(improver),
          interpretation='Known numerical guard limitation within 1e-7; not a counterexample to ideal rows or a new native campaign.'))

U=1.;L=1.+2e-7
fact('native and post-seal signed-gap predicates differ',
     L+EPS>=U and not L<=U+EPS,
     'With all other gates true, native one-sided gap predicate accepts; clean published post-seal audit rejects L>U+1e-7.')
fact('ideal complement and raw numeric floor differ',
     min(Q(10000002,10000000),Q(1))==1,
     'Raw scheduler merge retains 1.0000002, while source-cutoff-completed ideal floor is 1.')

source_names=['PaperExternalGiniTree.cpp','ControllingLeafScheduler.cpp','ExternalGiniTree.cpp',
              'IntervalRowFactory.cpp','CplexBaseline.cpp','HgaTgbcRunner.cpp',
              'Round83BlockExchange.cpp','hga_tgbc/HgaTgbcGreedy.cpp']
sources={name:hashlib.sha256((SRC/name).read_bytes()).hexdigest() if (SRC/name).exists()
         else snapshot['source_sha256'][name] for name in source_names}
if source_mode=='current frozen source read':
    snapshot=dict(source_sha256=sources,epoch_invalidation_excerpt=epoch,
                  neutral_admission_excerpt=neutral,
                  scope='Only two compact reviewed source excerpts; complete source identity recorded separately.')
    snapshot_path.write_text(json.dumps(snapshot,indent=2)+'\n',encoding='utf-8')
result=dict(scope='independent bounded arithmetic/source assertions; no native execution',
            facts=facts,sources=sources,source_mode=source_mode,optimizer_calls=0,production_compilations=0,H_searches=0)
(HERE/'independent_finite_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=len(facts),optimizer_calls=0,production_compilations=0,H_searches=0)))
