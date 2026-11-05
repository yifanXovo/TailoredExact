"""Mathematical target stops, preserving the actual frozen pricing models.

The current long run showed negative residual incumbents long before return.
This interface stops only for an exactly reevaluated legal counterexample
or the corresponding guarded Native bound threshold. It adds no model row,
time-based component switch, potential box or production-helper change.
"""
import hashlib,inspect,textwrap
from fractions import Fraction as F
import round153_pricing as normalized
import round154_residual as residual
from round154_strengthened import StrengthenedResidualOracle
from round154_common import sha

def method(original,kind):
    source=textwrap.dedent(inspect.getsource(original))
    if kind=='RN':
        assert source.count('global_deadline=None):')==1
        source=source.replace('global_deadline=None):','global_deadline=None,tau=None):')
        assert source.count('dp=unary_dp(scope,d)')==1
        source=source.replace('dp=unary_dp(scope,d)','tau=F(tau);dp=unary_dp(scope,d)')
        needle='built=time.perf_counter();m.optimize();done=time.perf_counter()'
        threshold="(tau-sum(anchors.values(),F(0)))/F(scale)+F(guard)+correction"
        qualification='qualified=m.Status in accepted and'
        replacement='qualified=(m.Status in accepted or m.Status==gp.GRB.USER_OBJ_LIMIT or (m.Status==gp.GRB.INTERRUPTED and stopped_counterexample)) and'
    else:
        assert kind=='residual'
        needle='built=time.perf_counter(); m.optimize(); done=time.perf_counter()'
        threshold='F(guard)'
        qualification='qualified=m.Status in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.NODE_LIMIT) and'
        replacement='qualified=(m.Status in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.NODE_LIMIT,gp.GRB.USER_OBJ_LIMIT) or (m.Status==gp.GRB.INTERRUPTED and stopped_counterexample)) and'
    assert source.count(needle)==source.count(qualification)==1
    original_line=next(line for line in source.splitlines() if needle in line)
    indentation=original_line[:len(original_line)-len(original_line.lstrip())]
    block=f'''stopped_counterexample=False;callback_errors=[]
native_stop=outward({threshold},True)
m.Params.BestBdStop=native_stop;m.Params.BestObjStop=-gp.GRB.INFINITY
assert m.Params.BestBdStop==native_stop
write(target/'target_stop_plan.json',dict(kind='{kind}',tau_exact=str(tau),Native_BestBdStop=native_stop,
      bound_stop_exact=str({threshold}),guard_already_paid=True,no_model_changes=True,
      generated_source_SHA=_generated_source_SHA,wrapper_SHA=_wrapper_SHA,
      model_SHA=sha(target/'model.mps'),counterexample_requires_original_price_and_scope=True,
      accepted_new_return_statuses=[gp.GRB.USER_OBJ_LIMIT,gp.GRB.INTERRUPTED],
      interrupted_bound_requires_own_verified_counterexample=True))
(target/'target_stop_source.txt').write_bytes(_generated_source.encode('utf-8'))
def target_callback(model,where):
    nonlocal stopped_counterexample
    if where!=gp.GRB.Callback.MIPSOL:return
    try:
        xx=model.cbGetSolution(self.x)
        Y=[max(s['support'],key=lambda y:xx[s['i'],y]) for s in ss]
        value=stock_value(scope,Y,beta,d)
        if value['feasible'] and value['price']<tau:
            consider(Y);stopped_counterexample=True
            write(target/'counterexample_stop.json',dict(stock=serial_stock(value),tau_exact=str(tau),
                original_price_exact=str(value['price']),scope=scope,UTC=utc(),
                Native_callback='MIPSOL',mathematical_target_rejected=True,
                auxiliary_completion_not_used_as_price=True))
            model.terminate()
    except BaseException as error:
        callback_errors.append(repr(error));model.terminate()
built=time.perf_counter();m.optimize(target_callback);done=time.perf_counter()
if callback_errors:
    write(target/'callback_failure.json',dict(errors=callback_errors,no_new_bound=True))
    raise RuntimeError('target_callback_failure:'+str(callback_errors))'''
    source=source.replace(original_line,'\n'.join(indentation+line if line else '' for line in block.splitlines()))
    source=source.replace(qualification,replacement)
    digest=hashlib.sha256(source.encode()).hexdigest()
    ns=dict(original.__globals__,_generated_source=source,_generated_source_SHA=digest,_wrapper_SHA=sha(__file__))
    exec(compile(source,__file__+'::'+kind,'exec'),ns)
    return ns['price'],dict(kind=kind,generated_SHA=digest,original_module=original.__module__)

class TargetResidualCore(residual.ResidualOracle):pass
TargetResidualCore.price,RESIDUAL_SOURCE=method(residual.ResidualOracle.price,'residual')

class TargetResidualOracle(StrengthenedResidualOracle,TargetResidualCore):pass

class TargetRNOracle(normalized.Oracle):pass
TargetRNOracle.price,RN_SOURCE=method(normalized.Oracle.price,'RN')
