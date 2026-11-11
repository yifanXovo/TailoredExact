"""Close current-only identities/accounting and write bounded reproduction notes."""
from round161_common import *
import copy,collections

def close():
    pending=budget()['unclosed'];assert all(p['label']==os.environ.get('ROUND140_METERED_PARENT_LABEL') for p in pending)
    # Every old actual build remains immutable. Annotate the final measured
    # identity copies so the legacy production_PE alias cannot imply a panel.
    for filename in ('measured_manifest.json','measured_manifest_RNP.json'):
        m=read(OUT/filename);m.update(standalone_research=True,complete_method_performance=False,
            production_PE_field='legacy alias for the standalone research executable; not a full H/helper algorithm entry')
        for name in ('src/Round161NativeRN.cpp','src/round161_research_main.cpp','src/MipStartMapping.cpp','src/GurobiBaseline.cpp','include/Round161NativeRN.hpp'):
            digest=m['source_hashes'][name];dest=OUT/'engineering/measured_source_bytes'/f'{digest}.txt'
            if not dest.exists():
                raw=git('show',m['verified_CPP_commit']+':'+name)
                if hashlib.sha256(raw).hexdigest()!=digest:raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
                assert hashlib.sha256(raw).hexdigest()==digest;dest.write_bytes(raw)
            assert sha(dest)==digest
        write(OUT/filename,m)
    # Capture the scientific preparation outside individual child intervals.
    # Each panel's OS birth -> final receipt span is disjoint from its paid
    # child outer intervals after subtraction, so no nested Runtime is added.
    groups=collections.defaultdict(list)
    for p in (OUT/'fees').glob('*/receipt.json'):
        launch=read(p.parent/'launch.json')
        if launch['kind']=='native':groups[launch['parent_pid']].append((launch,read(p)))
    extra=[]
    for pid,values in groups.items():
        birth=min(x['parent_birth']['creation_unix'] for x,r in values)
        end=max(r['end_unix'] for x,r in values);paid=sum(r['outer_seconds'] for x,r in values)
        overhead=end-birth-paid;assert overhead>=0,(pid,overhead)
        extra.append(dict(kind='verification',outer_seconds=overhead,parent_PID=pid,
            start_unix=birth,end_unix=end,paid_child_outer_seconds=paid,
            rule='Observed parent birth through last closed receipt minus disjoint paid native child outer intervals; final administrative tail excluded',
            new_Optimize=0))
    write(OUT/'infra/external_costs.json',dict(processes=extra,not_nested_Runtime=True))
    raw_goal=Path('C:/Users/Administrator/Downloads/TailoredExact_Round161_Complete_Goal.md').read_bytes()
    intake=OUT/'engineering/intake_goal_original.txt';intake.write_bytes(raw_goal)
    write(OUT/'source_build_runtime_input.json',dict(base=BASE,branch=git('branch','--show-current').decode().strip(),
        original_goal_SHA256=hashlib.sha256(raw_goal).hexdigest(),original_goal_archive_member=intake.relative_to(ROOT).as_posix(),
        core_manifest='measured_manifest.json',revised_manifest='measured_manifest_RNP.json',
        measured_core_CPP=read(OUT/'measured_manifest.json')['verified_CPP_commit'],
        measured_revised_CPP=read(OUT/'measured_manifest_RNP.json')['verified_CPP_commit'],
        actual_runtime_bindings=[p.relative_to(ROOT).as_posix() for p in (OUT/'infra').glob('runtime_binding_*.json')],
        input_manifest='input_manifest.json',actual_models='reports/model_identities.json',
        full_method_panel='conditional_complete_results.json',commercial_runtime_published=False))
    earlier=OUT/'qualification/revision/reader_probe_correction.json'
    if earlier.exists():
        value=read(earlier);value.update(superseded=True,correct_rule='Integer targets are parsed with llround, then required >0; the guessed 1e-9 threshold was incorrect.',
            corrected_record='reader_probe_correction_final.json');write(earlier,value)
    write(OUT/'engineering/hardening_resolution.json',dict(PASS=True,measured_sources_preserved=True,
        actual_ratio_coefficients_checked=True,semantic_old_product_registry=True,physical_consumers_rejected=True,
        physical_common_rows_checked='reports/matrix_audits.json',zero_row_units='qualification/revision/scaled_zero_kernel.json',
        zero_scaling_unit_is_not_route_input=True,ordinary_positive_zero_physical_optima=True,
        Native_backend_and_mapper_byte_identical=True,CPP_delivery_clean_build='engineering/cmake_delivery.json',
        new_complete_method=False,major_revision_count=1))
    with (OUT/'engineering/open_engineering_items.md').open('a',encoding='utf8') as f:
        f.write('\n## Final resolution\n\nAll numbered items are resolved by measured_manifest*, qualification/revision.json, reports/model_identities.json and engineering/cmake_delivery.json. Scaled rows are tested in an explicitly algebraic kernel; the existing reader has integer targets and was unchanged. Both rejected noninteger-demand probe inputs/logs remain, with the corrected diagnosis. The sole RN-P revision completed both affected LP/MIP pairs and did not earn the conditional complete panel. See decision.json.\n')
    (OUT/'reproducibility.md').write_text('''# Bounded Round161 reproduction

The dependency is verified R160 delivery 53e5c62fbcf6bc24898b7d5d3ecb755e4331ab0b;
the branch is codex/round161-full-physical-rn. Work only under
E:/codes/ExactEBRP-work. WORKSPACE_POLICY.md applies. Stable GI-TBC/B and
historical main comparison data were not replaced.

The actual measured core C++ is pinned by measured_manifest.json (v3);
the RN-P C++/PE is separately pinned by measured_manifest_RNP.json (v6).
Qualification v1/v2/v5 and a failed v4 compile are separate, never promoted
to full-bridge or complete-method performance. Raw changed-source bytes are
inside the new evidence carrier, indexed by their actual SHA256. The later
clean CMake executable is an engineering build, not a measured sample.

Use the installed GNU C++17 toolchain and Gurobi 13.0.2 listed in the manifests.
A source build enables EXACT_EBRP_ENABLE_GUROBI=ON and the default-OFF option
EXACT_EBRP_BUILD_ROUND161_RESEARCH=ON, with GUROBI_ROOT pointing at the local
win64 installation. Build target Round161Research. The exact single-job
clean configure/build commands are in engineering/cmake_delivery.json.
No optimization, fast-math or tolerance override was introduced.

The standalone CLI is:

    Round161Research input T tp td lambda parent.txt output OLD|RN|RN-P LP|MIP seconds nodes

Use a new output directory. The finite bridge uses 300s/-1 for LP and
900s/4096 for MIP, Seed0/Threads1/MIPFocus0. A complete Native call would
pass -1 (unlimited nodes); no complete H/helper candidate was entered here.
The explicit export mode writes models/registries/Start without Optimize.

Restore only the new carrier using public_manifest.json and its archive/member
hashes. The two original input blobs use fixed commit/path/SHA references.
The offline old parent source has fixed R160 archive/member hashes in
input_manifest.json; no old archive download is required for a bounded readback.
Each NEW journal's call-0 witness already contains the same complete parent
routes/operations. To reconstruct parent.txt, write route count, then each
vehicle and complete node list (with its length), then pickup-drop for the
interior nodes. This is the unchanged C++ route input format.

scripts/round161_analyze.py, round161_envelope_diagnostic.py and the separate
round161_review.py read saved current-round evidence only. The final verifier
extracts only the existing R157 physical verify function's AST; no old imports,
producer, solver or old budget controller execute. The plot uses an isolated
Matplotlib target under the work-root temp directory and a task-local config
cache. Plot dependency installation and public I/O are separate costs.

The commercial DLL/license/credentials are excluded. The actual measured PEs,
objects and old verified archive remain available locally at their manifest
paths; public byte-identical PE reconstruction is not claimed. Source/model/
route/parameter/evidence recovery requires no Optimize and no old producer.
The finite anonymous public recovery and post-PR bounded cleanup receipts
are written by the delivery metadata commit.
''',encoding='utf8')
    print('Closed identities, actual controller overhead and bounded reproduction notes')

if __name__=='__main__':close()
