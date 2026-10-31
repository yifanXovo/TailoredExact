"""Close scientific metadata without adding experiments or retagging the PE."""
import io,zipfile
from round143_common import *
from round143_analyze import require_idle

def main():
    require_idle();review=read(OUT/'review/stage_decision.json');assert not review['additional_experiments_admitted']
    manifest=read(OUT/'candidate_manifest.json');full=read(OUT/'reports/full.json')
    decision=dict(UTC=utc(),study_complete=True,decision=review['decision'],stable_promotion=False,
        source_correctness_qualified=True,uniform_default_off_RN_retained=True,additional_experiments_admitted=False,
        independent_stage_review_SHA=sha(OUT/'review/stage_decision.json'),
        summary='RN supplies real complementary LP information, but the two priority same-PE Seed0 pairs do not show a sufficient complete-method benefit. Retain the uniform lift as research-only and stop full expansion this round; stable R137 GI-TBC remains the paper mainline.',
        complete_discussion='K35 is a real tradeoff: RN lowers verified U by 0.0115958602505 but also lowers supported L by 0.0142269916815. Its signed gap grows from 0.135695592698 to 0.138326724129, and relative gap grows from 0.195850096067 to 0.203045869458. Both remain qualified-open after the full 2400-second caps. Producer time is essentially unchanged; RN adds 1.91078480007 seconds of verification and 1.87683260511 seconds to complete total. RX20-T1 certifies the same verified physical objective 0.645325030386 with both methods; RN raises producer/certificate time from 22.2066890239 to 23.4901347759 seconds and total from 23.3987336238 to 24.9265588757 seconds. The 7.97e-10 returned-L difference is within the inherited numerical policy and is not a substantive mathematical loss or gain.',
        attribution_discussion='All four formal positions have zero outer splits. Actual complete root bounds repeat the matched diagnostic improvements, but final Native cut/search behavior is different. K35 terminal nodes decrease from 16825 to 10779 while Work increases from 4691.00560053 to 4999.12908278. RX20-T1 nodes decrease from 2621 to 1620 while Work increases from 29.5418051573 to 34.9746070207. These are descriptive full-method effects, not a proof that fewer nodes mean less computation or that a specific added row caused every difference. Same-PE methods have matching complete own-H semantics and fleets; their full Native/H/Start/quality/lifecycle evidence is qualified.',
        decision_paragraph='The decision is RESEARCH_ONLY_STOP_FULL_EXPANSION_THIS_ROUND. Qualification and integer equivalence pass; nonpromotion follows the observed complete-method tradeoff and lack of proof-clock benefit, not a correctness failure. The code remains a separate uniform default-off research option. The tested result is not that RN is mathematically redundant, generally slower, or incapable of benefiting an untested instance.',
        conditional_work_discussion='No formal K20/RB35-T2 pair, optional K15/RX35-T2 pair or Seed1 is entered. K20 cap90 remains health-only; its saved-root extension is not a complete performance prediction. Other roles could characterize additional behavior, but there is no specific pending adoption/stop decision that their measurement would change after the priority hard-role support-bound regression and the second role\'s proof-clock result. Seed1 would not erase the retained adverse Seed0 result or establish a runtime distribution. Reopening requires a concrete new mechanism or decision-changing evidence, rather than a missing table. Stopping occurs with substantial budget remaining.')
    write(OUT/'candidate_decision.json',decision)
    write(OUT/'candidate_freeze.json',dict(UTC=utc(),uniform_candidate='stable R137 GI-TBC + compact RN',default_off=True,
        stock=False,TC_TC2=False,count_disjunction=False,CP=False,AP=False,AM=.08,depth=8,minimum_width=1e-4,
        pair_only=True,Seed=0,H_seed=20260626,source_commit=manifest['source_commit'],PE_SHA=manifest['production_PE_SHA'],
        no_instance_or_size_patch=True,no_timed_algorithm_switch=True,original_penalty_and_integer_path_retained=True))
    # Restore the first replay's actual gzip bytes from the already committed
    # science version. The second replay adds bindings, without invalidating
    # the preserved first report's compressed-column identities.
    history=[];old=read(OUT/'math/history/offline_point_checks_v1.json')
    for r in old['results']:
        if r['status']!='SAME_OLD_POINT_EXTENSION':continue
        rel='results/unified_exact_round143/'+Path(r['new_columns_path']).as_posix()
        data=git('show','0ced8a89d:'+rel);assert hashlib.sha256(data).hexdigest()==r['new_columns_SHA']
        target=OUT/'math/history/initial_extensions'/Path(r['new_columns_path']).name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        history.append(dict(original_path=r['new_columns_path'],preserved_path=target.relative_to(OUT).as_posix(),SHA256=r['new_columns_SHA']))
    write(OUT/'math/history/identity_map.json',dict(source_commit='0ced8a89d',initial_report_SHA=sha(OUT/'math/history/offline_point_checks_v1.json'),
        initial_gzip_bytes_restored_from_git=True,files=history,Optimize=0,Native_load=0))
    # Compare actual compiled bytes with their source commit, explicitly
    # recording only identity or the repository's LF/CRLF transport.
    data=git('archive','--format=zip',manifest['source_commit'],'src','include');sources=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name,digest in manifest['source_hashes'].items():
            actual=(ROOT/name).read_bytes();assert hashlib.sha256(actual).hexdigest()==digest
            original=z.read(name)
            if original==actual:transport='identity'
            else:
                assert b'\r' not in original and original.replace(b'\n',b'\r\n')==actual,name
                transport='Git_LF_to_compiled_CRLF'
            sources.append(dict(path=name,compiled_SHA256=digest,Git_SHA256=hashlib.sha256(original).hexdigest(),transport=transport))
    write(OUT/'source_publication.json',dict(UTC=utc(),source_commit=manifest['source_commit'],sources=sources,
        actual_compiled_bytes_in_source_carrier=True,source_semantics_unchanged=True,Optimize=0,Native_load=0))
    helper_sets={}
    for matrix_path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(matrix_path)
        if 'helpers' not in matrix:continue
        for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
        helper_sets[matrix_path.name]=matrix['helpers']
    write(OUT/'measured_helper_versions.json',dict(actual_frozen_helper_sets=helper_sets,current_bytes_match=True,
        LP_versions=[dict(path=p.relative_to(ROOT).as_posix(),writer_SHA=read(p)['writer_SHA'],math_SHA=read(p)['math_SHA'],source_commit=read(p)['source_commit']) for p in (OUT/'LP').glob('*/result.json')],
        before_Optimize_failures_bound_to_git_versions='failures/attempt_history.json',Optimize=0,Native_load=0))
    reference_paths=['results/gf_tailored_bc_formulation_snapshot_round/alternative_formulation_rejection_notes.csv',
        'results/unified_exact_round88/ot_mathematics.md','results/unified_exact_round133/joint_objective_gap_note.md',
        'results/unified_exact_round138/mathematical_analysis.md','results/unified_exact_round140/mathematical_analysis.md',
        'results/unified_exact_round137/final_report.md','results/unified_exact_round126/historical_attribution.md']
    references=[]
    for name in reference_paths:
        raw=git('show',BASE+':'+name);references.append(dict(commit=BASE,path=name,Git_SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
            URL=f'https://github.com/yifanXovo/TailoredExact/blob/{BASE}/{name}'))
    write(OUT/'reference_dependencies.json',dict(scope='Finite directed historical readings only; no old experiment regenerated',references=references,Optimize=0,Native_load=0))
    write(OUT/'LP_execution_index.json',dict(retrospective_execution_index=True,initial_plan_SHA=sha(OUT/'LP_plan.json'),
        TC_stock_followups_authorized_by_initial_signal_policy=True,
        actual_positions=[dict(role=read(p)['role'],variant=read(p)['variant'],result=p.relative_to(ROOT).as_posix(),result_SHA=sha(p),
            canonical_SHA=read(p)['canonical_SHA']) for p in (OUT/'LP').glob('*/result.json')],
        LP_Optimize=4,additional_Optimize_for_offline_points=0,Seed1=0))
    assets={}
    for name,p in [('production',Path(manifest['production_PE'])),('Native_DLL',DLL),('LP_python',LP_PYTHON),('process_python',PYTHON),
        ('compiler',Path('D:/msys64/ucrt64/bin/g++.exe'))]:assets[name]=dict(path=str(p),SHA256=sha(p),bytes=p.stat().st_size)
    write(OUT/'software_bindings.json',dict(UTC=utc(),task_date='2026-11-01',timezone='Asia/Shanghai',assets=assets,
        Seed=0,H_seed=20260626,Threads=1,affinity_mask=4,global_settings_changed=False,Optimize=0,Native_load=0))
    docs=ROOT/'docs/round143_research.md'
    docs.write_text('''# Round143 reciprocal-normalization study

The default-off [RN research entry](../scripts/paper_s2_rn.py) adds a compact
reciprocal-normalized Gini block to stable R137 GI-TBC, retaining integer
routes/inventory and the original penalty. Four matched continuous LPs show
real gains, including gains over TC+stock. Two same-PE Seed0 role pairs show
K35 incumbent/support-bound tradeoffs and no RX20-T1 proof-clock benefit.

The independently reviewed decision is **research-only; stop full expansion
this round**. Stable GI-TBC and previous entries/profiles remain available.
See the [report](../results/unified_exact_round143/final_report.md),
[mathematics](../results/unified_exact_round143/mathematical_analysis.md),
[decision](../results/unified_exact_round143/candidate_decision.json),
[research appendix](../results/unified_exact_round143/manuscript.pdf) and
[continuation/delivery record](../results/unified_exact_round143/RESUME.md).
The profile is `config/gi_tbc_rn_round143.json`; `--rn on|off` selects the
same-PE research/control mode. The launcher only expands unless `--run` is explicit.

All new build/raw/temp/restore assets stay under ExactEBRP-work. Post-PR
cleanup is bounded to this round after public recovery acceptance, retaining
unique raw/failures and necessary runtime dependencies. Old rounds and the
original user tree remain protected.
''',encoding='utf-8',newline='\n')
    for filename in ['docs/current_mainline.md','docs/unified_exact_research_index.md']:
        p=ROOT/filename;text=p.read_text(encoding='utf-8-sig')
        if 'round143_research.md' not in text:
            p.write_text(text+'\nThe [Round143 reciprocal-normalization study](round143_research.md) records real\nmatched LP gains but mixed complete same-PE results. It remains default-off\nresearch-only, with no full expansion or stable promotion; stable R137 above\ncontinues as the paper mainline.\n',encoding='utf-8',newline='\n')
    print('Scientific decision, byte/lineage bindings and research documentation closed; no new experiments')

if __name__=='__main__':main()
