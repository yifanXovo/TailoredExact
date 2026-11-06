"""Inherited qualified pricing with lossless incremental matrix evidence.

The only generated-source changes concern evidence storage. All objective,
guard, zero-branch, bound conversion and target-stop operations are inherited.
"""
import hashlib, inspect, textwrap
from round154_residual import ResidualOracle
from round154_strengthened import StrengthenedResidualOracle
from round154_goal_oracle import TargetResidualCore
from round143_lp import semantics
from round155_common import *

DYNAMIC_ROWS=('hard_cost_','tight_DP_cost_product_','floor_residual','G_residual')

def dynamic(name): return name.startswith(DYNAMIC_ROWS)

def semantic_hash(value):
    # Free native bounds are legitimate infinities, not finite replacements.
    # Give them explicit hash tokens while rejecting NaN. Signed zero has the
    # same model meaning and can be normalized by an MPS round-trip.
    def encode(item):
        if isinstance(item,float):
            assert not math.isnan(item),'NaN is not an admissible model coefficient or bound'
            if math.isinf(item):return {'binary64_bound':'positive_infinity' if item>0 else 'negative_infinity'}
            return 0. if item==0 else item
        if isinstance(item,dict):return {key:encode(child) for key,child in item.items()}
        if isinstance(item,(list,tuple)):return [encode(child) for child in item]
        return item
    return hashlib.sha256(json.dumps(encode(value),separators=(',',':'),allow_nan=False).encode()).hexdigest()

def capture(oracle,model,target):
    structure=semantics(model); root=oracle.evidence_root
    root.mkdir(parents=True,exist_ok=True)
    base=root/'base.mps'; first=not base.exists()
    if first:
        model.write(str(base))
        with oracle.gp.read(str(base),env=oracle.env) as back: assert semantics(back)==structure
        oracle.evidence_base=structure; oracle.evidence_base_SHA=sha(base)
        write(root/'base_identity.json',dict(SHA256=oracle.evidence_base_SHA,semantics_SHA=semantic_hash(structure),
            semantics_encoding='ordered-binary64-json-explicit-infinite-bounds-normalized-zero',
            original_order_retained=True,full_MPS_readback=True))
    original=oracle.evidence_base
    fixed=lambda s:[r for r in s['rows'] if not dynamic(r[0])]
    assert fixed(structure)==fixed(original)
    assert [v[0] for v in structure['columns']]==[v[0] for v in original['columns']]
    updates=[]
    for before,after in zip(original['columns'],structure['columns']):
        if before!=after:
            assert after[0] in ('hard_cost_D','hard_cost_W') and before[3:]==after[3:]
            updates.append(dict(name=after[0],LB=after[1],UB=after[2]))
    assert structure['ObjCon']==original['ObjCon'] and structure['ModelSense']==original['ModelSense']
    delta=dict(schema='round155-full-price-matrix-delta-v1',base=str(base),base_SHA=oracle.evidence_base_SHA,
        semantics_encoding='ordered-binary64-json-explicit-infinite-bounds-normalized-zero',
        column_updates=updates,rows=[r for r in structure['rows'] if dynamic(r[0])],
        row_order=[r[0] for r in structure['rows']],semantics_SHA=semantic_hash(structure),
        new_model_semantics_complete=True,full_model_first_readback=first)
    save_gz(target/'matrix_delta.json.gz',delta)
    return dict(model_SHA=oracle.evidence_base_SHA if first else None,full_readback=first,
        matrix_evidence=str(target/'matrix_delta.json.gz'),matrix_evidence_SHA=sha(target/'matrix_delta.json.gz'),
        semantics_SHA=delta['semantics_SHA'])

def reconstruct(delta_path,gp,env):
    delta=load_gz(delta_path); assert sha(delta['base'])==delta['base_SHA']
    m=gp.read(delta['base'],env=env)
    m.remove([c for c in m.getConstrs() if dynamic(c.ConstrName)]);m.update()
    vs={v.VarName:v for v in m.getVars()}
    for row in delta['column_updates']:
        vs[row['name']].LB=row['LB'];vs[row['name']].UB=row['UB']
    for name,sense,rhs,terms in delta['rows']:
        e=gp.quicksum(a*vs[k] for k,a in terms)
        m.addConstr(e>=rhs if sense=='>' else e<=rhs if sense=='<' else e==rhs,name=name)
    m.update()
    assert [c.ConstrName for c in m.getConstrs()]==delta['row_order']
    assert semantic_hash(semantics(m))==delta['semantics_SHA']
    return m

def compact_method(first):
    if first:
        original=TargetResidualCore.price
        source=original.__globals__['_generated_source']
    else:
        original=ResidualOracle.price;source=textwrap.dedent(inspect.getsource(original))
    lines=source.splitlines()
    matches=[j for j,line in enumerate(lines) if line.strip()=="m.update(); structure=semantics(m); m.write(str(target/'model.mps'))"]
    assert len(matches)==1
    index=matches[0];indent=lines[index][:len(lines[index])-len(lines[index].lstrip())]
    assert lines[index+1].strip()=="with gp.read(str(target/'model.mps'),env=self.env) as back: assert semantics(back)==structure"
    lines[index:index+2]=[indent+'m.update(); matrix_record=_capture(self,m,target)']
    source='\n'.join(lines)+'\n'
    source=source.replace("sha(target/'model.mps')","matrix_record['model_SHA']")
    source=source.replace('matrix_readback=True,','matrix_readback=matrix_record["full_readback"],matrix_evidence=matrix_record,')
    # One immutable generated source per oracle is sufficient for every call.
    source=source.replace("(target/'target_stop_source.txt').write_bytes(_generated_source.encode('utf-8'))",
                          "(self.evidence_root/'target_stop_source.txt').write_bytes(_generated_source.encode('utf-8')) if not (self.evidence_root/'target_stop_source.txt').exists() else None")
    digest=hashlib.sha256(source.encode()).hexdigest()
    ns=dict(original.__globals__,_capture=capture,_generated_source=source,
            _generated_source_SHA=digest,_wrapper_SHA=sha(__file__))
    exec(compile(source,__file__+('::first' if first else '::bounded'),'exec'),ns)
    return ns['price'],digest,source

class CompactFirstCore(ResidualOracle): pass
CompactFirstCore.price,FIRST_SHA,FIRST_SOURCE=compact_method(True)
class CompactBoundedCore(ResidualOracle): pass
CompactBoundedCore.price,BOUNDED_SHA,BOUNDED_SOURCE=compact_method(False)
class ActualStateTransport:
    def price(self,beta,d,tau,target,**kwargs):
        result=super().price(beta,d,tau,target,**kwargs)
        if self.model is None:return result
        from round155_price_certificate import recover_actual,corrected_result
        tick=time.perf_counter();target=Path(target)
        raw=target/'nominal_coordinate_result.json';assert not raw.exists();write(raw,result)
        correction=recover_actual(target/'result.json',result)
        assert correction['actual_cost_bounds_cover_complete_domain'],'actual Native state-cost bounds must retain the full price domain'
        ext=read(target/'strengthening.json')
        assert [self.Dcost.LB,self.Dcost.UB]==ext['tight_cost_bounds']
        result=corrected_result(result,correction)
        result.update(nominal_coordinate_result_SHA=sha(raw),
            numerical_guard_not_reused_for_omission_error=True)
        result['seconds']+=time.perf_counter()-tick
        write(target/'result.json',result)
        return result

class FirstOracle(ActualStateTransport,StrengthenedResidualOracle,CompactFirstCore): pass
class BoundedOracle(ActualStateTransport,StrengthenedResidualOracle,CompactBoundedCore): pass

def make_oracle(scope,env,rule,root):
    assert rule in ('first','bounded')
    oracle=(FirstOracle if rule=='first' else BoundedOracle)(scope,env)
    oracle.evidence_root=Path(root)
    oracle.evidence_root.mkdir(parents=True,exist_ok=True)
    (oracle.evidence_root/'generated_price.py.txt').write_bytes((FIRST_SOURCE if rule=='first' else BOUNDED_SOURCE).encode('utf-8'))
    return oracle
