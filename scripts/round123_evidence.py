"""General read-only final/history U separation, with complete inherited scope audit."""
from round123_common import *
import ast, contextlib, copy, inspect
import round86_native_evidence as native
import round108_reader as core
import round122_evidence as inherited

def history_guard(root,panel,arm,audited,records,result,upper):
    """Do not order legal U values. Check each fleet and every scoped bound."""
    witnesses=[core.full_fleet(root,panel,r['payload']) for r in records if r['payload']['kind']=='witness']
    final=core.full_fleet(root,panel,result)
    assert abs(final['F']-upper)<1e-7
    assert len(witnesses)==audited['physical_witnesses']==len(audited['witnesses'])
    assert witnesses and abs(min(w['F'] for w in witnesses)-audited['UB'])<1e-12
    for checked,prior in zip(witnesses,audited['witnesses']): assert abs(checked['F']-prior['F'])<1e-12
    assert audited['LB']<=min(w['F'] for w in witnesses+[final])+1e-7
    scopes={r['payload']['call']:r['payload'] for r in records if r['payload']['kind']=='call'}
    checked=0
    for row in records:
        e=row['payload']
        if e['kind']=='bound':
            scope=scopes[e['call']]; bound=e['native_bound']
            assert isinstance(bound,(int,float)) and __import__('math').isfinite(bound)
            if scope['full_original']:
                assert bound<=min(w['F'] for w in witnesses+[final])+1e-7
            else:
                for witness in witnesses+[final]:
                    if scope['lower_g']-1e-7<=witness['G']<=scope['upper_g']+1e-7 and witness['F']<=scope['cutoff']+1e-7:
                        assert bound<=witness['F']+1e-7
                if e['global_available']:
                    native.replay_bound(scope,bound,audited['witnesses']+[final])
            checked+=1
    if arm=='P-GRB':
        assert result['lower_bound'] is None or result['lower_bound']<=min(w['F'] for w in witnesses+[final])+1e-7
    return True

def adapted_finalizer():
    source=inspect.getsource(native.finalize_endpoint); original=ast.parse(source).body[0]
    target=ast.parse("assert audited['UB']+1e-7 >= upper").body[0]
    replacement=ast.parse('assert _history_guard(root,panel,arm,audited,records,result,upper)').body[0]
    changed=[]
    class Replace(ast.NodeTransformer):
        def visit_Assert(self,node):
            if ast.dump(node,include_attributes=False)==ast.dump(target,include_attributes=False):
                changed.append(1); return ast.copy_location(copy.deepcopy(replacement),node)
            return self.generic_visit(node)
    modified=Replace().visit(copy.deepcopy(original)); assert changed==[1]
    class Reverse(ast.NodeTransformer):
        def visit_Assert(self,node):
            if ast.dump(node,include_attributes=False)==ast.dump(replacement,include_attributes=False):
                return ast.copy_location(copy.deepcopy(target),node)
            return self.generic_visit(node)
    assert ast.dump(Reverse().visit(copy.deepcopy(modified)),include_attributes=False)==ast.dump(original,include_attributes=False)
    namespace=dict(vars(native),_history_guard=history_guard)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[modified],type_ignores=[])),__file__+'::general_history_guard','exec'),namespace)
    return namespace['finalize_endpoint']

@contextlib.contextmanager
def history_extension():
    original=native.finalize_endpoint; native.finalize_endpoint=adapted_finalizer()
    try: yield
    finally: native.finalize_endpoint=original

@contextlib.contextmanager
def extension():
    with history_extension(),inherited.extension(): yield

def verify(l,i):
    with history_extension(): return inherited.verify(l,i)

