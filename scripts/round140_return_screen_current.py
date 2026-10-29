"""Offline projection of the five new TC2+stock LP optima; never Optimize."""
from round140_common import *
from fractions import Fraction as F
import gzip


def main():
    assert not budget()['unclosed'], 'Defer offline point I/O until timed runs are idle'
    tick=time.perf_counter();facts=[];tol=1e-7
    for a in read(OUT/'LP_plan.json')['positions']:
        if a['variant']!='tc2_stock':continue
        role=a['role'];folder=OUT/'LP'/f"{a['position']:02}_{role}_tc2_stock"
        result=read(folder/'result.json');path=folder/'solution.json.gz'
        assert result['status']=='NUMERICAL_OPTIMAL_CONTINUOUS_LP'
        assert sha(path)==result['solution_SHA']
        scope=read(OUT/'roots'/role/'scope.json');p=scope['panel']
        assert result['source_SHA']==scope['stock_SHA']
        with gzip.open(path,'rt') as stream:point=json.load(stream)
        alpha,beta=F(scope['alpha']),F(scope['beta']);g=F(point['G']);B=scope['B']
        assert float(alpha)-tol<=float(g)<=float(beta)+tol
        J=sum(F(point[f'zprod_{i}']) for i in range(1,p['V']+1))
        tau=sum(F(point[f'Y_{i}']) for i in range(1,p['V']+1))
        returns=[];lower=[];upper=[]
        for k,Q in enumerate(p['Q_vector']):
            r=sum(F(point[f'p_{k}_{i}'])-F(point[f'd_{k}_{i}']) for i in range(1,p['V']+1))
            returns.append(r)
            lower.append(max(alpha*r,beta*r+Q*(g-beta)))
            upper.append(min(beta*r,alpha*r+Q*(g-alpha)))
        assert abs(float(B-tau-sum(returns)))<=tol
        target=B*g-J
        bounds_ok=all(-tol<=float(r)<=Q+tol for r,Q in zip(returns,p['Q_vector']))
        intervals_ok=all(float(lo-hi)<=tol for lo,hi in zip(lower,upper))
        projection_ok=intervals_ok and float(sum(lower)-target)<=tol and float(target-sum(upper))<=tol
        facts.append(dict(role=role,variant='tc2_stock',B=B,tau=float(tau),G=float(g),J=float(J),
            R=[float(r) for r in returns],Q=p['Q_vector'],return_bounds_feasible=bounds_ok,
            return_upper_violations=[max(0.,float(r)-Q) for r,Q in zip(returns,p['Q_vector'])],
            sum_lower=float(sum(lower)),target=float(target),sum_upper=float(sum(upper)),
            product_projection_feasible_ignoring_return_bound_check=projection_ok,
            product_signal_beyond_linear_bounds=bounds_ok and not projection_ok,
            solution_SHA=sha(path),result_SHA=sha(folder/'result.json'),source_model_SHA=result['source_SHA']))
    assert len(facts)==5 and 'gurobipy' not in sys.modules
    # Supplement the existing exact block witness, not a full cutoff witness.
    g=F(1,6);J=F(1,2);B=5;tau=3;r=2;Q=2;alpha=F(0);beta=F(1,2);w=g*r
    lo=max(alpha*r,beta*r+Q*(g-beta));hi=min(beta*r,alpha*r+Q*(g-alpha))
    assert lo==w==hi==F(1,3) and J+w==B*g and B-tau==r
    tiny=dict(scope='Exact return-product extension of the existing strict relaxation-block witness; not full BRP/cutoff feasibility',
        B=B,tau=tau,R=r,Q=Q,g=str(g),J=str(J),W=str(w),lower=str(lo),upper=str(hi),conservation=True)
    write(OUT/'math/return_product_current_points.json',dict(UTC=utc(),Optimize=0,vendor_DLL_loads=0,
        scope='Existing new continuous LP optimal vectors only, not complete Native incumbents or a new solve. R<=Q obstruction is classified before product projection.',
        comparison_tolerance=tol,evaluation='Exact Fraction of saved binary64 values, with explicit numerical residual tolerance',
        cases=facts,product_signal_roles=[f['role'] for f in facts if f['product_signal_beyond_linear_bounds']],
        exact_strict_block_return_extension=tiny,
        source_SHA=sha(__file__),seconds=time.perf_counter()-tick))
    print(json.dumps(dict(points=len(facts),product_signal_roles=[f['role'] for f in facts if f['product_signal_beyond_linear_bounds']],Optimize=0)))


if __name__=='__main__':main()
