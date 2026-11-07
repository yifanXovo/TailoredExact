"""Bind current source/runtime and small fixed-member references, no old carrier I/O."""
import ast
from round157_common import *
from round140_common import git

def closure(entries):
    pending=list(entries);found={}
    while pending:
        path=Path(pending.pop())
        name=path.relative_to(ROOT).as_posix()
        if name in found:continue
        found[name]=sha(path)
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:modules.append(node.module)
        for module in modules:
            candidate=ROOT/'scripts'/(module.split('.')[0]+'.py')
            if candidate.is_file():pending.append(candidate)
    return found

def run():
    from round100_gurobi_runtime import binding
    native=binding();assert native['sha256']==DLL_SHA
    base_manifest='results/unified_exact_round156/public_manifest.json'
    raw=git('show',SCIENCE156+':'+base_manifest)
    assert hashlib.sha256(raw).hexdigest()==sha(PRIOR/base_manifest)
    prior=json.loads(raw);indexes={}
    for f in prior['files']:
        indexes[f['path']]=dict(commit=SCIENCE156,**f,resolution='fixed Git blob')
    for a in prior['archives']:
        path=PRIOR/a['member_index']['path'];assert sha(path)==a['member_index']['SHA256']
        for member in load_gz(path):
            indexes[member['member']]=dict(commit=SCIENCE156,path=member['member'],SHA256=member['SHA256'],
                bytes=member['bytes'],resolution='fixed archive member',archive=a['name'],archive_SHA=a['SHA256'],
                member_index=a['member_index'])
    refs=[]
    for role,s in read(OUT/'inventory_sources.json').items():
        family=read(OUT/'inventory_families.json')[role]
        paths=[s['pricing_path'],s['scope_source'],family['positive_control']['path']]
        for source in paths:
            p=Path(source);name=p.resolve().relative_to(PRIOR.resolve()).as_posix();r=indexes[name]
            assert sha(p)==r['SHA256'] and p.stat().st_size==r['bytes']
            refs.append(dict(role=role,**r))
        p=ROOT/s['panel']['input_path'];blob=git('show',BASE+':'+s['panel']['input_path'])
        assert hashlib.sha256(blob).hexdigest()==sha(p)==s['panel']['input_sha256']
        refs.append(dict(role=role,commit=BASE,path=s['panel']['input_path'],SHA256=sha(p),bytes=len(blob),
                         resolution='fixed Git input blob',original_physical_panel=s['panel']))
    write(OUT/'reuse_index.json',dict(UTC=utc(),references=refs,
        prior_manifest=dict(commit=SCIENCE156,path=base_manifest,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)),
        old_carriers_downloaded=0,old_carriers_repacked=0,old_producer_reruns=0))
    production=read(PRIOR/'results/unified_exact_round156/source_manifest.json')
    assert sha(production['PE'])==production['PE_SHA256'] and sha(PYTHON)=='2204195cec25879507d958a8b6949add67091244b8b4da9cf3672f993548fa49'
    measured=closure([ROOT/'scripts'/name for name in ('round157_fleet.py','round157_resource.py','round157_floor.py','round157_tour.py')])
    all_sources=closure(list((ROOT/'scripts').glob('round157*.py')))
    write(OUT/'source_manifest.json',dict(UTC=utc(),fixed_dependency_base=BASE,
        authoring_head_at_manifest_generation=git('rev-parse','HEAD').decode().strip(),current_algorithm_dependency_closure=measured,
        full_authoring_delivery_dependency_closure=all_sources,
        actual_executed_versions='fees and engineering/source_snapshots plus exact engineering/source_bytes; earlier versions are retained',
        Python=str(PYTHON),Python_SHA=sha(PYTHON),Native=native,
        inherited_production_source=production['production_measured_source_commit'],
        inherited_PE=production['PE'],inherited_PE_SHA=production['PE_SHA256'],
        standalone_calls_use_Gurobi_DLL_through_qualified_python=True,
        inherited_PE_executed_this_round=(OUT/'confirmation_matrix.json').exists(),
        new_Cpp_build=(WORK/'build-cache/round157').exists(),
        libraries_reused_read_only=True,original_workspace_unchanged=True,
        policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),goal_SHA=sha(OUT/'goal.md'),
        unused_prototypes='round157_time.py, round157_resource_point.py and round157_assignment_upper.py have no execution claim unless a matching fee and result exist'))
    print(json.dumps(dict(measured_dependencies=len(measured),full_dependencies=len(all_sources),references=len(refs))),flush=True)

if __name__=='__main__':run()
