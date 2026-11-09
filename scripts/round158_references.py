"""Fixed historical provenance index; small metadata I/O, no science calls."""
from round158_common import *

def run():
    tick=time.perf_counter();prior=read(OLD157/'reuse_index.json');manifest=read(OLD157/'public_manifest.json')
    records=list(prior['references']);old_files={r['path']:r for r in manifest['files']}
    wanted=['inventory_sources.json','inventory_families.json','mathematical_analysis.md',
        'final_report.md','source_manifest.json','reuse_index.json','finite_counterfactual_plan.md']
    for name in wanted:
        path='results/unified_exact_round157/'+name;r=old_files[path]
        records.append(dict(commit=SCIENCE157,path=path,SHA256=r['SHA256'],bytes=r['bytes'],resolution='fixed Git blob'))
    carriers={r['name']:r for r in read(OLD157/'carrier_manifest.json')['archives']}
    refs=[read(OUT/'candidates.json')['R-X35-S-T2']['source'],
          read(OUT/'infra/nb_assignment_source.json'),read(OUT/'r157_errata.json')['source']]
    for ref in refs:
        carrier=carriers[ref['archive']];assert ref['archive_SHA']==carrier['SHA256']
        records.append(dict(commit=SCIENCE157,path=ref['member'],SHA256=ref['member_SHA'],
            resolution='fixed archive member',archive=ref['archive'],archive_SHA=carrier['SHA256'],
            parts=carrier['parts'],member_index=carrier['member_index']))
    # Bind both new C++ coefficient extracts back to already public fixed members.
    for source in read(OLD157/'inventory_sources.json').values():
        package=read(OUT/'qualification/coefficient_v2'/(source['panel']['input_sha256']+'.json'))
        expected=[r for r in records if r['path']==package['source']['member'] and r['SHA256']==package['source']['SHA256']]
        assert expected and expected[0]['resolution']=='fixed archive member'
    for path in ('results/unified_exact_round92/handling_activation_physical_envelope_note.md',
                 'results/unified_exact_round92/physical_envelope_independent_static_review.md',
                 'scripts/round103_hull.py','scripts/round103_anchor_analysis.py','WORKSPACE_POLICY.md'):
        blob=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        records.append(dict(commit=BASE,path=path,SHA256=hashlib.sha256(blob).hexdigest(),bytes=len(blob),resolution='fixed Git blob'))
    unique={}
    for r in records:unique[r['commit'],r['path'],r['SHA256']]=r
    write(OUT/'reuse_index.json',dict(UTC=utc(),references=list(unique.values()),
        fixed_dependency_base=BASE,source_science=SCIENCE157,
        archive_downloads_or_repacking_in_this_metadata_step=0,old_producer_executions=0,Optimize=0,
        metadata_IO_seconds=time.perf_counter()-tick,
        source_version_note='R157 corrected report/RESUME bytes on the R158 branch are new errata; original R157 science remains pinned at its original commit and hashes.'))
    print(json.dumps(dict(references=len(unique),metadata_IO_seconds=time.perf_counter()-tick)),flush=True)

if __name__=='__main__':run()
