"""Disclosed post-formal support-family metadata correction; no optimizer."""
from round130_common import *
from round130_analysis import difference

def run():
    d=OUT/'review/support_count_correction'
    resume=len(sys.argv)>1 and sys.argv[1]=='resume'
    d.mkdir(parents=True,exist_ok=resume)
    names=['actual_method_differences.json','observations.json','stratified_summary.json',
           'arms.csv','pairs.csv','mechanism_costs.csv','same_H.csv','closure_sources.csv',
           'cross_arm_bound_consistency.json','scientific_decision.json','claim_decision.md']
    before={}
    for name in names:
        src=OUT/name;dst=d/'before'/name;dst.parent.mkdir(parents=True,exist_ok=True)
        if resume:assert dst.is_file() and sha(src)==sha(dst),name
        else:shutil.copyfile(src,dst)
        before[name]=sha(dst)
    for name in ['final_independent_evidence.json','final_independent_review.md']:
        src=OUT/'review'/name
        if src.exists() and not resume:shutil.copyfile(src,d/('first_failed_'+name))
    historical=OUT/'qualification/zero_qualification.json'
    frozen_sha=sha(historical)
    corrections=[]
    for fixture in ['pair_root/S12','pair_root/R98-C2','equal_cutoff/shared','equal_cutoff/fallback','pair_root_fallback/S12']:
        root=OUT/'qualification'/fixture
        from round130_qualify import difference as historical_difference
        old=historical_difference(root/'ms2/original.lp',root/'s2-root/original.lp')
        new=difference(root/'ms2/original.lp',root/'s2-root/original.lp')
        corrections.append(dict(fixture=fixture,historical_descriptive_counts=old,
            corrected_descriptive_counts=new,changed=old!=new))
    write(d/'preservation.json',dict(UTC=utc(),before_summary_SHAs=before,
        prior_correction_attempt='fees/support_count_correction_01: exclusive-create CSV writer stopped before replacing any CSV' if resume else None,
        only_derived_author_summaries_recreated=True,native_raw_untouched=True))
    # The inherited CSV writer is intentionally exclusive-create. Only remove
    # these five derived files after checking their byte-identical retained copy.
    for name in ['arms.csv','pairs.csv','mechanism_costs.csv','same_H.csv','closure_sources.csv']:
        p=OUT/name
        assert sha(p)==sha(d/'before'/name)
        p.unlink()
    for script in ['round130_analysis.py','round130_decision.py']:
        subprocess.run([PYTHON,ROOT/'scripts'/script],cwd=ROOT,env=environment(),check=True)
    assert sha(historical)==frozen_sha
    write(d/'addendum.json',dict(UTC=utc(),status='POSTPROCESS_COUNT_CORRECTED',
        discovery='Independent final review 01 failed on author support-family count metadata, not full-model identity or native evidence.',
        cause='Row-shape-only cover_2 classification aliased cross-vehicle unique-service rows when M=2.',
        correction='Use the inherited R129 single-vehicle support-family classifier in post-formal summaries.',
        before_summary_SHAs=before,historical_zero_qualification_SHA_unchanged=frozen_sha,
        qualification_descriptive_count_addendum=corrections,
        native_raw_source_algorithm_parameters_clocks_and_frozen_qualification_reports_changed=False,
        matrix_objective_order_types_bounds_and_duplicate_preserving_row_equality_unchanged=True,
        previous_failed_review_retained=True,Optimize=0,H=0,compile=0,formal_retries=0,
        scientific_tag=read(OUT/'scientific_decision.json')['tag']))
    (d/'addendum.md').write_text('''# Support-family count correction

Independent final review 01 found that the frozen qualification helper's descriptive row-shape classifier counted cross-vehicle unique-service rows as two-station cover rows when there are two vehicles. The full duplicate-preserving model, objective, column order, types and bounds comparisons were already correct. No native arm, mathematical model, source algorithm, parameter, clock or certificate changes.

The post-formal summary now uses the existing R129 classifier, which requires support variables to belong to one vehicle. The original qualification report and its hash are retained; the JSON addendum gives both original and corrected descriptive counts for its five pair-root fixtures. S12 shared/fallback pair-cover counts change from 12 to 0 (conditional counts stay 132). All formal B20/C20 pair-cover summaries lose 20 aliased unique-service rows; actual pair totals are 380. B30 totals remain 1305. The first failed review and author summaries are preserved here; a new independent review must recheck all 24 arms and 30 comparisons. The scoped/mixed scientific decision is unchanged.
''',encoding='utf-8')
    print('POSTPROCESS_SUPPORT_COUNT_CORRECTION_COMPLETE')

if __name__=='__main__':run()
