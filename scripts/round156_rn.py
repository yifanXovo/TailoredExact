"""The original RN model/stops with observation-only pricing callbacks."""
import inspect, textwrap, hashlib
from round153_pricing import Oracle

def instrument():
    source = textwrap.dedent(inspect.getsource(Oracle.price))
    needle = 'built=time.perf_counter();m.optimize();done=time.perf_counter()'
    assert source.count(needle) == 1
    original = next(line for line in source.splitlines() if needle in line)
    indent = original[:len(original)-len(original.lstrip())]
    block = '''callback_errors=[]; last_observation=[-1.,None]
def observe(model,where):
    try:
        if where==gp.GRB.Callback.MIPSOL:
            xx=model.cbGetSolution(self.x)
            Y=[max(s['support'],key=lambda y:xx[s['i'],y]) for s in ss]
            value=stock_value(scope,Y,beta,d)
            if value['feasible']:
                consider(Y)
                self.record_event(dict(kind='stock',Y=value['Y'],price_exact=str(value['price']),
                    price=outward(value['price'],True),nodes=model.cbGet(gp.GRB.Callback.MIPSOL_NODCNT)))
        elif where==gp.GRB.Callback.MIP:
            bound=model.cbGet(gp.GRB.Callback.MIP_OBJBND)
            now=time.perf_counter()
            if math.isfinite(bound) and abs(bound)<1e90 and (bound!=last_observation[1] or now-last_observation[0]>=5.):
                positive=max(fallback,F(scale)*(F(bound)-F(guard)-correction)+sum(anchors.values(),F(0)))
                lower_now=min(positive,zero) if zero is not None else positive
                self.record_event(dict(kind='bound',native_bound=bound,lower=outward(lower_now,False),
                    nodes=model.cbGet(gp.GRB.Callback.MIP_NODCNT),work=model.cbGet(gp.GRB.Callback.WORK)))
                last_observation[:]=[now,bound]
    except BaseException as error:
        callback_errors.append(repr(error));model.terminate()
built=time.perf_counter();m.optimize(observe);done=time.perf_counter()
if callback_errors: raise RuntimeError('RN_observation_failed:'+str(callback_errors))'''
    source = source.replace(original, '\n'.join(indent+line if line else '' for line in block.splitlines()))
    ns = dict(Oracle.price.__globals__)
    exec(compile(source,__file__+'::observed','exec'),ns)
    return ns['price'],source,hashlib.sha256(source.encode()).hexdigest()

class ObservedRN(Oracle): pass
ObservedRN.price, GENERATED_SOURCE, GENERATED_SHA = instrument()
