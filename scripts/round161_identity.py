"""Bind actual measured bytes to fixed source, retaining failed-build identities."""
from round161_common import *
import copy

def bind():
    versions={'v1':'696a446fb','v2':'696a446fb','v3':'1fafb6e2a'}
    units=['src/Round161NativeRN.cpp','src/round161_research_main.cpp','src/MipStartMapping.cpp','src/GurobiBaseline.cpp','include/Round161NativeRN.hpp']
    receipts=[]
    for version,commit in versions.items():
        commit=git('rev-parse',commit).decode().strip();m=read(OUT/f'build_{version}.json');sources={}
        assert sha(m['research_PE'])==m['research_PE_SHA']
        for name in units:
            raw=git('show',commit+':'+name)
            if version=='v1' and name=='src/Round161NativeRN.cpp':
                raw=raw.replace(b'round143_detail::Block block;\n        if(!out.zero_only)block=round143_detail::block(supports,c,std::max(1LL,B-Q),B);\n        if(!out.zero_only && (block.infeasible||!block.applicable)) {',
                    b'auto block=round143_detail::block(supports,c,std::max(1LL,B-Q),B);\n        if(block.infeasible||!block.applicable) {')
            expected=m['source_hashes'][name]
            if hashlib.sha256(raw).hexdigest()!=expected:
                candidate=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
                assert hashlib.sha256(candidate).hexdigest()==expected,(version,name,expected)
                raw=candidate
            dest=OUT/'engineering/measured_source_bytes'/f'{expected}.txt';dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(raw)
            assert sha(dest)==expected;sources[name]=dict(SHA256=expected,bytes=len(raw),path=dest.relative_to(ROOT).as_posix())
        receipts.append(dict(version=version,CPP_reference_commit=commit,PE_SHA=m['research_PE_SHA'],files=sources,
            reconstructed_from_fixed_commit_with_hash_verification=version=='v1',
            reconstruction='Undo only the subsequently fixed B=0 reciprocal guard; every recovered byte matches the original actual build manifest' if version=='v1' else None))
    m=copy.deepcopy(read(OUT/'build_v3.json'));m['verified_CPP_commit']=git('rev-parse','1fafb6e2a').decode().strip()
    m['actual_build_head_at_time']=m['source_commit'];m['byte_identity_proof']='verified changed C++/header bytes equal fixed commit and original actual build manifest'
    m['versions']=receipts;m['performance_samples']='eight full-native bridge calls, all v3; v1/v2 are new-interface qualification only'
    write(OUT/'measured_manifest.json',m)
    # Fixed, bounded historical references, not another carrier restoration.
    paths=['results/gf_tailored_bc_formulation_snapshot_round/alternative_formulation_final_report.md',
        'results/gf_tailored_bc_s_bucket_strengthening_round/final_report.md',
        'results/gf_tailored_bc_adaptive_s_refinement_round/full_convergence_final_report.md',
        'results/gf_tailored_bc_dominant_s_bucket_round/full_convergence_final_report.md',
        'results/gf_passive_threshold_conflicts_round62/final_report.md',
        'results/unified_exact_round96/final_report.md','results/unified_exact_round97/final_report.md',
        'results/unified_exact_round98/final_report.md','results/unified_exact_round100/final_report.md',
        'results/unified_exact_round135/final_report.md','docs/round138_research.md',
        'results/unified_exact_round143/mathematical_analysis.md','results/unified_exact_round144/final_report.md','results/unified_exact_round145/final_report.md']
    history=[]
    for path in paths:
        raw=git('show',BASE+':'+path);history.append(dict(commit=BASE,path=path,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),read_scope='bounded conclusion/interface sections only'))
    write(OUT/'history_fixed_references.json',dict(references=history,old_producers=0,old_archive_full_extractions=0))
    print('PASS actual PE/source byte binding including failed qualification builds')

if __name__=='__main__':bind()
