"""Bind actual measured binaries/units; inverse-edit recovery must match old hashes."""
from round162_common import *

def once(raw,a,b):
    assert raw.count(a)==1,(a,raw.count(a))
    return raw.replace(a,b)

def previous_sources():
    files={n:git('show','8bbffa3c4:'+n).decode('utf8').replace('\r\n','\n') for n in ['include/Round162PhysicalCompletion.hpp',
        'src/Round162PhysicalCompletion.cpp','src/round162_research_main.cpp']}
    versions={'v6':dict(files)}
    h,c,m=[files[n] for n in files]
    h=once(h,'const std::filesystem::path& output,bool full,bool omit_endpoint_time=false);','const std::filesystem::path& output,bool full);')
    c=once(c,'const std::filesystem::path& output,bool full,bool omit_endpoint_time){','const std::filesystem::path& output,bool full){')
    begin=c.index('    std::set<int> time_rows;');end=c.index('    int scaled=0',begin);c=c[:begin]+c[end:]
    c=once(c,'for(int i:rows)if(!time_rows.count(i))for','for(int i:rows)for')
    c=once(c,r'<<",\"omitted_endpoint_time_rows\":"<<time_rows.size()*2','')
    m=once(m,'    const bool no_time=std::string(argv[8])=="F-no-time";\n','')
    m=once(m,'std::string(argv[8])=="F"||no_time,compact','std::string(argv[8])=="F",compact')
    m=once(m,'dir/"model.lp",full,no_time);','dir/"model.lp",full);')
    versions['v5']=dict(zip(files,[h,c,m]))
    h=once(h,'#include "FixedIntervalMipBackend.hpp"\n','')
    h=h[:h.index('Round162Artifact projectRound162Completion(')]+'}\n'
    c=once(c,'#include "ObjectiveResourceCompression.hpp"\n','')
    c=c[:c.index('void saveRound162LpEvidence(')]+'}\n'
    m=once(m,'const bool full=std::string(argv[8])=="F",compact=std::string(argv[8])=="C";','const bool full=std::string(argv[8])=="F";')
    m=once(m,'if(!full&&!compact&&std::string(argv[8])!="S")','if(!full&&std::string(argv[8])!="S")')
    begin=m.index('    double source_seconds=0,project_seconds=0;');end=m.index('    const double built=elapsed();',begin);m=m[:begin]+m[end:]
    m=once(m,'''    if(lp&&out.lp_primal_values_available){saveRound162LpEvidence(out,dir);
        std::map<std::string,double> values;for(const auto& e:out.lp_primal_dual_variable_evidence)values[e.name]=e.primal_value;
''','''    if(lp&&out.lp_primal_values_available){std::ofstream p(dir/"lp_values.tsv"),v(dir/"lp_variables.jsonl"),r(dir/"lp_duals.jsonl");p<<std::setprecision(17);v<<std::setprecision(17);r<<std::setprecision(17);
        std::map<std::string,double> values;for(const auto& e:out.lp_primal_dual_variable_evidence){values[e.name]=e.primal_value;p<<e.name<<'\\t'<<e.primal_value<<'\\n';v<<"{\\\"name\\\":"<<std::quoted(e.name)<<",\\\"value\\\":"<<e.primal_value<<",\\\"RC\\\":"<<e.reduced_cost<<",\\\"basis\\\":"<<e.variable_basis_status<<"}\\n";}
        for(const auto& e:out.lp_primal_dual_constraint_evidence)r<<"{\\\"name\\\":"<<std::quoted(e.name)<<",\\\"dual\\\":"<<e.dual_multiplier<<",\\\"slack\\\":"<<e.slack<<",\\\"basis\\\":"<<e.constraint_basis_status<<"}\\n";
''')
    m=once(m,'        <<",\\\"source_seconds\\\":"<<source_seconds<<",\\\"project_seconds\\\":"<<project_seconds<<",\\\"source_qualified\\\":"<<source_qualified\n','')
    versions['v4']=dict(zip(files,[h,c,m]))
    m=once(m,'''    // A fixed fractional point need not contain the physical parent. Do not
    // apply the original-domain witness/cover qualifier to this diagnostic.
    if(mode!="completion")req.native_evidence=journal;
    auto& scope=req.native_evidence_scope;scope.leaf=req.leaf_id;
''','''    req.native_evidence=journal;auto& scope=req.native_evidence_scope;scope.leaf=req.leaf_id;
''')
    versions['v3']=dict(zip(files,[h,c,m]))
    return versions

def bind():
    recovered=previous_sources();versions=[]
    for version in ('v1','v2','v3','v4','v5','v6'):
        manifest=read(OUT/f'build_{version}.json');assert sha(manifest['research_PE'])==manifest['research_PE_SHA']
        selected={}
        for name in ['include/Round162PhysicalCompletion.hpp','src/Round162PhysicalCompletion.cpp','src/round162_research_main.cpp','src/GurobiBaseline.cpp']:
            expected=manifest['source_hashes'][name];raw=(ROOT/name).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=expected:
                text=recovered.get(version,{}).get(name)
                if name=='src/GurobiBaseline.cpp':text=git('show','8bbffa3c4:'+name).decode('utf8').replace('\r\n','\n')
                if text is None:
                    selected[name]=dict(SHA256=expected,source_bytes_recovered=False,scope='failed/tiny development prototype; hash only')
                    continue
                candidates=[text.encode(),text.replace('\n','\r\n').encode()]
                candidates=[v for v in candidates if hashlib.sha256(v).hexdigest()==expected]
                assert len(candidates)==1,(version,name,expected,hashlib.sha256(text.encode()).hexdigest())
                raw=candidates[0]
            dest=OUT/'engineering/measured_source_bytes'/f'{expected}.txt';dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(raw)
            assert sha(dest)==expected
            selected[name]=dict(SHA256=expected,bytes=len(raw),source_bytes_recovered=True,path=dest.relative_to(ROOT).as_posix())
        if version in ('v3','v4','v5','v6'):assert all(v['source_bytes_recovered'] for v in selected.values()),version
        versions.append(dict(version=version,PE_SHA256=manifest['research_PE_SHA'],files=selected,
            actual_build_head=manifest['source_commit'],inverse_edits_validated_by_original_hashes=version in ('v3','v4','v5')))
    value=read(OUT/'build_v6.json');value.update(verified_CPP_commit='8bbffa3c4',versions=versions,
        performance_samples='All four paid Native arms are v6, same PE. Capacity S RX=v3, F=v4, first C=v5; actual common matrices and Starts read back exactly.',
        old_prototype_limit='v1/v2 exact edited source bytes may be hash-only; failed attempts and tiny outputs remain. Final source, primary capacity/projector source and Native measured bytes are recovered.')
    write(OUT/'measured_manifest.json',value)
    print('PASS actual measured PE/source binding',flush=True)

if __name__=='__main__':bind()
