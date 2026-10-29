"""Offline return-product projection screen; no model or optimizer is loaded."""
from round140_common import *
from fractions import Fraction as F
import gzip

def main():
    facts=[]
    for role in ['K-20-S','K-35-U','R-X20-S-T1','R-X35-S-T2']:
        scope=read(OUT/'roots'/role/'scope.json');p=scope['panel'];alpha=F(scope['alpha']);beta=F(scope['beta']);B=scope['B']
        for variant in ['stock','tc_stock']:
            path=OUT/'inherited/roots'/role/variant/'solution.json.gz'
            assert sha(path)==read(path.parent/'result.json')['solution_SHA']
            with gzip.open(path,'rt') as f:point=json.load(f)
            g=F(point['G']);J=sum(F(point[f'zprod_{i}']) for i in range(1,p['V']+1));returns=[];lower=[];upper=[]
            for k,Q in enumerate(p['Q_vector']):
                value=sum(F(point[f'p_{k}_{i}'])-F(point[f'd_{k}_{i}']) for i in range(1,p['V']+1));returns.append(value)
                lower.append(max(alpha*value,beta*value+Q*(g-beta)))
                upper.append(min(beta*value,alpha*value+Q*(g-alpha)))
            target=B*g-J
            facts.append(dict(role=role,variant=variant,B=B,tau=sum(point[f'Y_{i}'] for i in range(1,p['V']+1)),
                R=[float(v) for v in returns],Q=p['Q_vector'],return_upper_violations=[max(0.,float(v)-Q) for v,Q in zip(returns,p['Q_vector'])],
                sum_lower=float(sum(lower)),target=float(target),sum_upper=float(sum(upper)),
                product_projection_feasible=float(sum(lower)-target)<=1e-7 and float(target-sum(upper))<=1e-7,
                return_bounds_feasible=all(-1e-7<=float(v)<=Q+1e-7 for v,Q in zip(returns,p['Q_vector']))))
    write(OUT/'math/return_product_offline.json',dict(Optimize=0,cases=facts,comparison_tolerance=1e-7,
        stored_float_evaluation='Exact Fraction evaluation, with stated numerical residual tolerance for LP saved-point feasibility',
        scope='Related alternative offline screening only; a linear R<=Q violation is not product gain',source_SHA=sha(__file__)))
    print('Eight old saved-point return screens; zero new LP/MIP, numerical residual tolerance explicit')

if __name__=='__main__':main()
