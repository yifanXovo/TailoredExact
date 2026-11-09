"""Post-publication A--H acceptance audit: metadata and saved identities only.

No Optimize, model construction, compiler, old producer or deletion. The
fixed science recovery is not repeated. This late audit source is delivery
metadata and is published in a normal follow-up, outside the frozen manifest.
"""
import csv,hashlib,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
SCIENCE='163b1b3d0dbcc7be3a84d94108ef4a26ae9baba3'
BASE='7f9f0d31ee6963e58c620b029469c90c2d92a6cc'
META='1285dbe39e99a1b0690dd7e4f3c304113f611268'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def run():
    tick=time.perf_counter();requirements=[]
    def accept(item,condition,scope,*paths,status='PASS'):
        assert condition,item
        evidence=[]
        for path in paths:
            p=OUT/path;assert p.is_file(),p
            evidence.append(dict(path=path,SHA256=sha(p)))
        requirements.append(dict(item=item,status=status,scope=scope,evidence=evidence))
    goal=(OUT/'goal.md').read_text(encoding='utf-8')
    assert sha(OUT/'goal.md')==sha(Path('C:/Users/Administrator/Downloads/TailoredExact_Round158_Complete_Goal.md'))
    assert '充分深入后的UNKNOWN可以验收' in goal and '计算负面' in goal
    assert git('merge-base','--is-ancestor',BASE,'HEAD')==b''
    changed=git('diff','--name-only',BASE,'HEAD').decode().splitlines()
    allowed={'.gitattributes','.gitignore','docs/round158_research.md','docs/current_mainline.md','docs/paper_review.md',
        'docs/unified_exact_research_index.md','results/unified_exact_round157/RESUME.md','results/unified_exact_round157/final_report.md'}
    assert all(n in allowed or n.startswith('scripts/round158') or n.startswith('results/unified_exact_round158/') for n in changed)
    assert git('diff','--name-only',BASE,'HEAD','--','src','include','config','results/unified_exact_round137')==b''
    remote=read(OUT/'remote_final_readback.json');assert remote['PASS']
    assert remote['published_metadata_head']==META==remote['ls_remote_head']==remote['local_head_at_readback']
    assert remote['base_sha']==BASE and remote['base']=='codex/round157-physical-inventory-realizability'
    assert remote['draft'] and remote['state']=='open' and not remote['merged']
    assert remote['body'].strip()==(OUT/'pr_body.md').read_text(encoding='utf-8').strip()
    initial=read(OUT/'infra/protected_initial.json');protected=0
    for tree in initial['trees']:
        for name,fact in tree['tracked_dirty'].items():
            assert sha(Path(tree['tree'])/name)==fact['SHA256'];protected+=1
    assert protected==3
    err=read(OUT/'r157_errata.json')
    accept('A.entry_base_and_workspace',True,'Verified R157 temporary base; actual remote absorption checked; isolated E-work tree and protected original dirty bytes.',
        'research_plan.json','infra/prepublication_remote_readback.json','infra/protected_initial.json','final_protection_readback.json')
    accept('A.774_erratum',err['displayed_nodes_at_least']==774 and not err['call_completed'] and err['final_NodeCount'] is None and err['final_Work'] is None,
        'At least774 displayed nodes; no final historical NodeCount/Work and no unsaved incumbent upper.','r157_errata.json')
    q1=read(OUT/'qualification/level_v1/result.json');q2=read(OUT/'qualification/level_v2/result.json')
    coef=read(OUT/'qualification/coefficient_v2/result.json');imp=read(OUT/'qualification/level_v2/actual_raw_implication.json')
    assert all(r['PASS'] for r in (q1,q2,coef,imp))
    accept('A.normal_return_and_durable_point_interface',q1['callback_Optimize_calls']==2,
        'Actual tiny Native callbacks test saved complete points and normal terminate; failed/control originals and launch bytes retained.',
        'qualification/level_v1/result.json','supervisor_interface_correction.json')
    decision=read(OUT/'final_decision.json');intervals=read(OUT/'final_intervals.json')
    accept('B.domains_minima_and_upper_identities',decision['science_question_open'] and decision['new_resource_assignment_upper'] is None,
        'RX35 D_F keeps only original26 deletion set; NB35 D_F=D_I; inventory, resource, physical and bare-LP identities remain distinct.',
        'mathematical_analysis.md','final_intervals.json','final_decision.json')
    accept('B.same_resource_value_ceiling',True,
        'Conditional on a true integer original-T U_R; no low-price novel U_R or ceiling on integer cuts is inferred from LP price.',
        'manuscript.tex','review/paper_claim_review.json')
    science=read(OUT/'review/final_scientific_review.json');paper=read(OUT/'review/paper_claim_review.json')
    assert science['PASS'] and paper['PASS'] and not science['own_receipt_pending_seal'] and not paper['own_receipt_pending_seal']
    families=science['finite_family_scope_checks']
    accept('C1.preselected_free_assignment_queries',[(r['members'],r['classification']) for r in families]==[(10,'FAMILY_RESOURCE_INFEAS'),(1,'FAMILY_RESOURCE_INFEAS')],
        'Entire preselected RX35 Y3 family and one NB singleton query; no point-by-point grid, no relaxed-time upper consumed.',
        'reports/finite_queries.csv','review/final_scientific_review.json')
    accept('C1.actual_CPP_exclusion_scope',coef['existing_finite_family_exclusions_preserved_by_guard_and_identical_integer_budgets'] and all(r['nominal_budget_changes']==r['guarded_budget_changes']==0 for r in coef['facts']),
        'Numeric v1/hypot time lower retained as queried; actual-C++ original/guarded-T exclusion transfers through identical integer budgets.',
        'coefficient_binding_correction.json','qualification/coefficient_v2/result.json')
    main=read(OUT/'level/rx35_raw_quarter_deep_v3/result.json');call=read(OUT/'level/rx35_raw_quarter_deep_v3/call.json')
    assert sha(OUT/'level/rx35_raw_quarter_deep_v3/result.json')==science['main_result_SHA']
    assert sha(OUT/'level/rx35_raw_quarter_deep_v3/model.mps')==call['model_SHA']==main['model_SHA']
    assert sha(OUT/call['admission_relative'])==call['admission_SHA']
    assert sha(OUT/call['actual_row_gate_relative'])==call['actual_row_gate_SHA']
    accept('C2.full_hard_J_level_and_result_qualification',main['classification']=='UNKNOWN' and not main['level_excluded'] and main['U_R'] is None and call['assignment_free'] and call['all_inventory_decisions_free'],
        'Conservative actual hard quarter-gap cutoff; complete original RN/free assignment; UNKNOWN retains old lower and no physical U.',
        'level/rx35_raw_quarter_deep_v3/call.json','review/rx35_raw_quarter_deep_v3_level.json','review/final_scientific_review.json')
    accept('C3.one_qualified_integer_expression',q1['rounded_same_integer_domain_and_LP_implication'] and all(r['all_rounded_rows_imply_actual_raw_rows'] and r['actual_rows']==21525 for r in imp['facts']),
        'Common raw/emitted physical envelope and guarded horizon, total pickups rather than Q, integer budgets and subset dominance; no grid or measured speedup claim.',
        'qualification/level_v1/result.json','qualification/level_v2/actual_raw_implication.json','diagnostic_decision.md')
    accept('D1.targeted_qualification_and_reuse',q1['R92_counterexample_retained'] and q1['physical_comparison_boundary_retained'] and coef['old_producer_executions']==coef['new_build']==0,
        'R92/R103 and historical controls reused; only actual new interface/coefficient qualification, no universal FP repair or performance rerun.',
        'history_dedup.md','qualification/coefficient_v2/result.json','qualification/level_v1/result.json')
    accept('D2.resource_opportunity_decision',True,
        'Finite primal-oriented free assignment first; no low novel U_R so the principal branch is a complete hard level, not another no-good/core cycle.',
        'research_plan.json','deepening_decision.json','reports/finite_queries.csv')
    accept('D3.full_substantive_capacity',main['status']==9 and main['SolCount']==0 and main['normal_Optimize_return'] and main['Runtime']>=129600 and main['NodeCount']==258972,
        'Full36-hour Native capacity completed after repair; not a short flat-bound stop. Meaningful computational negative accepted under explicit goal D3/F; value question stays open.',
        'level/rx35_raw_quarter_deep_v3/result.json','fees/level_rx35_raw_quarter_deep_v3/receipt.json','final_decision.json','goal.md')
    lp=read(OUT/'qualification/lp_fractional_ownership_v2/result.json')
    assert sha(OUT/'qualification/lp_fractional_ownership_v2/point_exact.json.gz')==lp['point_SHA']
    accept('D3.exact_bare_LP_explanation',lp['exact_rational_feasible_in_both_models'] and all(r['nonintegral_columns']==102 for r in science['lp_saved_point_exact_checks']),
        'Exact point in both complete matrices after main closure; only bare-LP scope, no integer U_R/global strict gap/Native-cut closure claim.',
        'qualification/lp_fractional_ownership_v2/result.json','review/final_scientific_review.json')
    accept('D3.conditional_physical_branch',not (OUT/'physical').exists() or not list((OUT/'physical').glob('*/result.json')),
        'No low integer resource upper arose; the conditional unqualified physical prototype was not executed. Only the required principal branch was followed.',
        'final_decision.json',status='CONDITIONAL_NOT_ENTERED')
    accept('E.uniform_candidate_and_complete_arms',decision['EplusR_candidate'] is None and not decision['conditional_panel_entered'] and decision['new_original_J_lower'] is None and decision['new_physical_U'] is None,
        'No qualifying lower or true route benefit; no E+R or empty eight-arm panel, no free offline hints in claimed fresh arms. Four-pair costs/seeds are conditional requirements and no such results are fabricated.',
        'final_decision.json','final_report.md',status='CONDITIONAL_NOT_ENTERED')
    receipts=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        r=read(p);assert r['exit_observed'] and not r['timeout'] and r['G1_seconds']==r['outer_seconds'];receipts.append((p.parent.name,r))
    total=sum(r['outer_seconds'] for _,r in receipts);cost=read(OUT/'cost_report.json')
    assert len(receipts)==22 and abs(total-cost['G1_seconds'])<1e-8 and total<259200
    assert {label for label,r in receipts if r['exit_code']}=={'prepare','lp_fractional_witness'}
    assert paper['closed_G1_seconds']==cost['G1_seconds'] and paper['all_fees_closed_at_seal']
    with (OUT/'reports/fees.csv').open(encoding='utf-8',newline='') as stream:fee_rows=list(csv.DictReader(stream))
    assert len(fee_rows)==22 and abs(sum(float(r['outer_seconds']) for r in fee_rows)-total)<1e-8
    for r in fee_rows:assert sha(OUT/r['receipt'])==r['receipt_SHA']
    accept('F.outer_costs_and_failures',True,'All22 outer scientific calls once, including failures/controls/readers; no nested Runtime/Work addition, within72h. Pure writing and measured compile/public I/O separate.',
        'cost_report.json','reports/fees.csv','reproducibility.md')
    render=read(OUT/'paper_qa/render_receipt.json');visual=read(OUT/'paper_qa/visual_review.json')
    assert sha(OUT/'manuscript.pdf')==paper['PDF_SHA']==render['PDF_SHA']==visual['PDF_SHA']
    for n,digest in paper['source_SHA'].items():assert sha(OUT/n)==digest
    assert visual['PASS'] and visual['inspected_pages']==[1,2,3,4,5] and not visual['visual_defects'] and not render['overfull_boxes']
    accept('F.thematic_paper_and_stable_formal_lineage',paper['PASS'] and render['pages']==5,
        'Five actual pages inspected; thematic integer proof/domain/value/level/computability discussion with existing attribution. Stable Round137 paper unchanged, stable B default and E+ reference.',
        'manuscript.tex','empirical_results.tex','manuscript.pdf','paper_qa/visual_review.json','review/paper_claim_review.json')
    source=read(OUT/'source_manifest.json')
    accept('G.saved_original_math_physical_cost_scope_review',science['PASS'] and paper['PASS'],
        'Same-agent separate readers; no invented independent identity; all actual new claims covered by preserved qualified originals.',
        'review/final_scientific_review.json','review/paper_claim_review.json')
    accept('G.source_runtime_and_production_identity',not source['production_CPP_or_configuration_changes'] and source['production_PE']['executions']==source['production_PE']['new_builds']==0,
        'Actual launcher/base interpreter/DLL and launched source snapshots distinguish late authoring code; no production build or execution.',
        'source_manifest.json','reproducibility.md')
    manifest=read(OUT/'public_manifest.json');carrier=read(OUT/'carrier_manifest.json');restore=read(OUT/'public_restore_receipt.json')
    assert sha(OUT/'public_manifest.json')==restore['manifest_SHA']==hashlib.sha256(git('show',SCIENCE+':results/unified_exact_round158/public_manifest.json')).hexdigest()
    for r in manifest['files']:assert sha(ROOT/r['path'])==r['SHA256'],r['path']
    for a in manifest['archives']:
        for r in a['parts']+[a['member_index']]:assert sha(ROOT/r['path'])==r['SHA256'],r['path']
    assert len(manifest['files'])==70 and len(manifest['archives'])==4
    assert sum(a['members'] for a in manifest['archives'])==restore['members']==282
    assert sum(a['uncompressed_bytes'] for a in manifest['archives'])==restore['member_bytes']==169068422
    assert sum(a['bytes'] for a in manifest['archives'])==20118495
    assert carrier['old_carriers_repacked']==0
    stage=read(OUT/'stage_verification.json');assert stage['PASS'] and stage['exact_index_blobs'] and len(stage['files'])==82 and stage['fixed_science_commit']==SCIENCE
    accept('G.new_only_fixed_science_and_exact_stage',True,
        '70 thin files,4 archives/282 members; actual82-path stage verification. Core manifest and current immutable bytes remain fixed at science commit; only explicit delivery metadata follows.',
        'public_manifest.json','carrier_manifest.json','stage_verification.json')
    dest=Path(restore['destination']).resolve();assert dest.is_relative_to((WORK/'restore').resolve())
    assert restore['state']=='PASS' and restore['commit']==SCIENCE and restore['initially_empty'] and restore['files']==78
    assert restore['no_Optimize_compiler_Native_or_old_producer'] and restore['old_carriers_downloaded']==0
    assert read(dest/'restore_state.json')['state']=='PASS' and not (OUT/'public_restore_failure.json').exists()
    accept('G.single_anonymous_current_only_recovery',True,
        'One actual new empty attempt01; every declared file/archive/member byte checked; no second recovery or old carrier/producer/native execution.',
        'public_restore_receipt.json','publication.json')
    cleanup=read(OUT/'cleanup_record.json');protect=read(OUT/'final_protection_readback.json')
    assert cleanup['deleted_bytes']==0 and cleanup['deleted_paths']==[] and cleanup['current_round_only']
    assert protect['PASS'] and protect['tracked_dirty_files']==3 and protect['checked_after_public_recovery']
    assert all(Path(r['path']).resolve().is_relative_to(WORK.resolve()) and r['action']=='retained' for r in cleanup['retained'])
    accept('G.post_PR_workspace_screen_and_cleanup',True,
        'Current-round metadata screening and literal E-work scope; zero deletion allowed, unique evidence/active trees/runtime references retained and all3 protected dirty hashes reread.',
        'cleanup_record.json','final_protection_readback.json')
    accept('G.English_Draft_PR_base_head_and_normal_push',True,
        'PR220 open Draft, verified temporary base and S2 remote/local head equal. Normal push only; no merge/force push/branch deletion.',
        'remote_final_readback.json','pr_body.md','publication.json')
    refs=read(OUT/'reuse_index.json');assert len(refs['references'])==23
    accept('H.historical_deduplication_and_attribution',True,
        '23 fixed references; no old carriers repackaged/downloaded, old loops/producers/tolerance or benchmark grids reopened; existing rounding/oracle attribution retained.',
        'reuse_index.json','history_dedup.md','mathematical_analysis.md')
    metadata_names=['RESUME.md','pr_body.md','publication.json','public_restore_receipt.json','cleanup_record.json','final_protection_readback.json','stage_verification.json']
    metadata=[]
    for name in metadata_names:
        digest=hashlib.sha256(git('show',META+':results/unified_exact_round158/'+name)).hexdigest()
        assert digest==sha(OUT/name),name
        metadata.append(dict(path=name,SHA256=digest,published_commit=META))
    accept('G.delivery_metadata_committed_and_read_back',True,
        'All seven delivered metadata paths match the actually published S2 Git blobs and remote head; the present audit/readback source follow-up is checked after its own normal push.',
        'remote_final_readback.json')
    output=dict(recorded_UTC=datetime.now(timezone.utc).isoformat(),PASS=True,requirements=requirements,
        accepted_outcome='Substantive complete-capacity computational UNKNOWN under the explicit D3/F acceptance path; scientific value question remains open.',
        scientific_question_resolved=False,science_commit=SCIENCE,published_metadata_commit=META,PR_url=remote['PR_url'],
        G1_seconds=total,fee_count=22,conditional_candidate_panel='Not entered under its explicit gate',protected_dirty_files=protected,
        metadata_blob_readback=metadata,public_manifest_immutable_checks=True,second_public_recovery=False,
        audit_kind='Post-publication delivery/metadata acceptance; no new scientific computation or experiment',
        Optimize=0,compiler_calls=0,old_producer_calls=0,deleted_paths=[],metadata_audit_IO_seconds=time.perf_counter()-tick,
        final_followup='This audit source/result and remote readback record are delivery metadata. Their final normally pushed Git blobs and actual Draft/base/head must be checked once more before /goal completion.')
    (OUT/'final_acceptance_audit.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(PASS=True,requirements=len(requirements),scientific_question_resolved=False,G1_seconds=total,metadata_audit_IO_seconds=output['metadata_audit_IO_seconds'])))

if __name__=='__main__':run()
