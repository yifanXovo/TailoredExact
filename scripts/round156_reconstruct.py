"""Read exact residual deltas after relocating a verified evidence tree.

This reader never edits the original base/delta and never calls Optimize.
Obtain inherited modules from the fixed Git source before using this reader;
the bounded public recovery itself only checks and restores bytes.
"""
from pathlib import PureWindowsPath
from round155_oracle import dynamic,semantic_hash
from round143_lp import semantics
from round156_common import *

def mapped_path(recorded,original_workspace,restored_workspace):
    original=PureWindowsPath(original_workspace);source=PureWindowsPath(recorded)
    rel=source.relative_to(original)
    assert '..' not in rel.parts and not rel.is_absolute()
    root=Path(restored_workspace).resolve();target=root.joinpath(*rel.parts).resolve()
    assert target.is_relative_to(root)
    return target

def reconstruct(delta_path,gp,env,restored_workspace=ROOT,original_workspace=ROOT):
    delta=load_gz(delta_path)
    base=mapped_path(delta['base'],original_workspace,restored_workspace)
    assert sha(base)==delta['base_SHA']
    model=gp.read(str(base),env=env)
    model.remove([c for c in model.getConstrs() if dynamic(c.ConstrName)]);model.update()
    variables={v.VarName:v for v in model.getVars()}
    for row in delta['column_updates']:
        variables[row['name']].LB=row['LB'];variables[row['name']].UB=row['UB']
    for name,sense,rhs,terms in delta['rows']:
        expression=gp.quicksum(a*variables[k] for k,a in terms)
        model.addConstr(expression>=rhs if sense=='>' else expression<=rhs if sense=='<' else expression==rhs,name=name)
    model.update()
    assert [c.ConstrName for c in model.getConstrs()]==delta['row_order']
    assert semantic_hash(semantics(model))==delta['semantics_SHA']
    return model

def check(label):
    from round100_gurobi_runtime import gp,binding
    from round100_idle import ensure_idle
    configure();ensure_idle();assert binding()['sha256']==DLL_SHA
    target=OUT/'review'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for path in sorted((OUT/'oracle').glob('*/*/price_*/matrix_delta.json.gz')):
            delta=load_gz(path)
            with reconstruct(path,gp,env) as model:
                assert semantic_hash(semantics(model))==delta['semantics_SHA']
                facts.append(dict(delta=path.relative_to(ROOT).as_posix(),SHA256=sha(path),
                    base_SHA=delta['base_SHA'],semantics_SHA=delta['semantics_SHA']))
            # Mapping is also checked at a different root without copying data.
            rel=PureWindowsPath(delta['base']).relative_to(PureWindowsPath(ROOT))
            alternative=WORK/'restore/round156-relocation-contract-only'
            assert mapped_path(delta['base'],ROOT,alternative)==alternative.joinpath(*rel.parts).resolve()
    assert len(facts)==3
    write(target/'result.json',dict(PASS=True,facts=facts,Optimize=0,original_deltas_unchanged=True,
        actual_current_base_reconstruction=True,alternative_root_path_mapping_checked=True,
        alternative_root_data_copy_performed=False,source_SHA=sha(__file__)))
    print(json.dumps(dict(PASS=True,matrices=len(facts),Optimize=0)),flush=True)

if __name__=='__main__':check(sys.argv[1])
