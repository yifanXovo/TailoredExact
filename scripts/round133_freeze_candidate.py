"""Bind the executed source bytes and the separately built Round133 assets."""
from round133_common import *
import zipfile

def main():
    target=OUT/'candidate_manifest.json';assert not target.exists()
    build=read(OUT/'candidate_build.json')
    commit=git('rev-parse','HEAD').decode().strip()
    assert commit=='4507c3554c6544048d307168779c8757f53cc5ae'
    sources={**build['source_bindings'],**build['header_bindings']}
    sources={Path(n).as_posix():v for n,v in sources.items()}
    sources['scripts/Round132Expression.hpp']=build['generated_research_source']['expression_header_SHA']
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    generated=Path(build['generated_research_source']['path'])
    assert sha(generated)==build['generated_research_source']['SHA']
    archive=OUT/'artifacts/candidate_source_bytes.zip';archive.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in sorted(sources):
            z.writestr(name,(ROOT/name).read_bytes())
        z.writestr('generated/CplexBaselineResearch.cpp',generated.read_bytes())
    binaries=build['binaries']
    for row in binaries.values():assert sha(row['PE'])==row['PE_SHA'] and sha(row['DLL'])==row['DLL_SHA']
    write(target,dict(schema='round133-candidate-source-build-policy-v1',UTC=utc(),
        source_commit=commit,base=BASE,source_hashes=sources,
        production_PE=binaries['production']['PE'],production_PE_SHA=binaries['production']['PE_SHA'],
        research_PE=binaries['research']['PE'],research_PE_SHA=binaries['research']['PE_SHA'],
        DLL=str(DLL),DLL_SHA=DLL_SHA,build_manifest_SHA=sha(OUT/'candidate_build.json'),
        executed_source_bytes=dict(path=archive.relative_to(ROOT).as_posix(),SHA=sha(archive),
            bytes=archive.stat().st_size,members=len(sources)+1,reason='Preserve executed Windows bytes independently of Git text conversion'),
        generated_research_source=build['generated_research_source'],
        original_binaries_unchanged=dict(production_SHA=sha(ORIGINAL_E3),research_SHA=sha(ORIGINAL_RESEARCH)),
        source_model_change=build['model_change'],
        unchanged=build['physical_problem_H_support_leaf_policy_unchanged'],
        declared_numeric_policy=dict(Threads=1,Seed='requested integer in[0,2000000000]',Presolve='requested -1..2',
            MIPFocus='registered q0/q1 configuration',Cuts='registered q0/q1 configuration',MIPGap=0,MIPGapAbs=0,
            FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6,objective_discrepancy=1e-7,
            numerical_tolerances_are_not_objective_error_bounds=True),
        raw_values_preserved=True,unconditional_restricted_floor='min(b,c) after qualification',
        late_rejection='abandon dependent state; full original G domain OPEN; independent F>=0 and own verified U',
        fixed_qualification='14 complete exposed regression arms; normal qualified-open allowed',
        conditional_bridge='8 complete original/new S2 arms if adopted; model and online behavior changed',
        admission='PENDING independent frozen-source and matrix review',Optimize=0))
    print(json.dumps(dict(candidate=str(target),SHA=sha(target),source_commit=commit,Optimize=0)))

if __name__=='__main__':main()
