"""Finite paper/data/visual-identity readback; no Optimize or compiler."""
import csv
from fractions import Fraction as F
from round158_common import *

LABEL='paper_claim_review'
TARGET=OUT/'review/paper_claim_review.json'

def run():
    from round100_idle import ensure_idle
    ensure_idle();assert os.environ.get('ROUND140_METERED_PARENT_LABEL')==LABEL
    assert all(r['label']==LABEL for r in budget()['unclosed'])
    science=read(OUT/'review/final_scientific_review.json');assert science['PASS']
    decision=read(OUT/'final_decision.json');assert decision['study_complete'] and not decision['scientific_question_resolved']
    assert decision['science_question_open'] and decision['EplusR_candidate'] is None and not decision['conditional_panel_entered']
    main=read(OUT/'level/rx35_raw_quarter_deep_v3/result.json')
    assert main['classification']=='UNKNOWN' and main['SolCount']==0 and not main['level_excluded']
    assert main['NodeCount']==258972 and main['IterCount']==160559495 and main['Runtime']>=129600
    assert main['U_R'] is None and main['physical_U'] is None
    lp=read(OUT/'qualification/lp_fractional_ownership_v2/result.json')
    assert lp['PASS'] and lp['exact_rational_feasible_in_both_models']
    assert lp['integer_resource_upper'] is None and lp['physical_U'] is None and not lp['whole_level_exclusion']
    assert lp['total_pickups']==lp['total_drops']==56 and lp['owner_fraction_exact']=='1/3'
    assert all(r['exact_rational_feasible'] and r['maximum_row_violation_exact']==r['maximum_bound_violation_exact']=='0' for r in lp['facts'])
    assert all(r['nonintegral_columns']==102 for r in science['lp_saved_point_exact_checks'])
    initial=read(OUT/'initial_intervals.json');final=read(OUT/'final_intervals.json');candidates=read(OUT/'candidates.json')
    for role,r in initial.items():
        for key in ('L_I','U_I','U_R','U_P','tau'):assert final[role][key]==r[key],(role,key)
        assert final[role]['new_resource_assignment_upper'] is None and final[role]['new_physical_U'] is None
        assert final[role]['F_R_lower']==r['L_I'] and final[role]['F_R_upper']==r['U_R']==r['U_P']
        if role.startswith('R-'):assert F(final[role]['F_F_upper'])>=F(candidates[role]['J_exact'])
        else:assert final[role]['D_F_definition']=='D_F=D_I'
    prior=read(OUT/'qualification/level_v1/result.json');actual=read(OUT/'qualification/level_v2/result.json')
    assert prior['PASS'] and actual['PASS'] and prior['hard_level_full_coverage']
    assert prior['R92_counterexample_retained'] and prior['physical_comparison_boundary_retained']
    for r in prior['facts']:
        if r['role'].startswith('R-'):assert (r['kept_subsets'],r['negative'],r['minimal_forbidden'],r['time_acceptance_threshold_changes'])==(4087,264,81,2)
        else:assert (r['kept_subsets'],r['minimal_forbidden'],r['time_acceptance_threshold_changes'])==(4755,4,5)
    tau=F(main['tau']);UI=F(initial['R-X35-S-T2']['U_I'])
    assert abs(float(tau-UI)-.015834716)<1e-9
    render=read(OUT/'paper_qa/render_receipt.json');visual=read(OUT/'paper_qa/visual_review.json')
    assert render['render_PASS'] and render['pages']==5 and visual['PASS'] and visual['inspected_pages']==[1,2,3,4,5]
    assert not render['overfull_boxes'] and not visual['visual_defects']
    assert sha(OUT/'manuscript.pdf')==render['PDF_SHA']==visual['PDF_SHA']
    for name,digest in render['source_SHA'].items():assert sha(OUT/name)==digest==visual['source_SHA'][name]
    for r in render['page_images']:assert sha(ROOT/r['path'])==r['SHA256']
    assert all(r['returncode']==0 for r in render['calls']) and render['not_G1']
    tex=(OUT/'manuscript.tex').read_text(encoding='utf-8');emp=(OUT/'empirical_results.tex').read_text(encoding='utf-8')
    extracted=(OUT/'paper_qa/extracted_text.txt').read_text(encoding='utf-8')
    for token in ('258972','160559495','318526.526959','129600.004','129601.832','37.1','UNKNOWN','102'):
        assert token in emp and token in extracted,token
    assert 'D_F=D_I' in tex and 'Later family exclusions do not silently redefine' in tex
    assert 'not an integer resource' in tex and 'cannot upper-bound' in tex
    assert 'Whether $F_R-F_I$ is worthwhile remains open.' in emp
    assert 'No new original-objective lower or true route benefit' in emp
    assert not any(x in tex+emp+extracted for x in ('TODO','TBD','??'))
    with (OUT/'reports/fees.csv').open(encoding='utf-8',newline='') as stream:fees=list(csv.DictReader(stream))
    assert abs(sum(float(r['outer_seconds']) for r in fees)-budget()['G1_seconds'])<1e-8
    assert round(budget()['G1_seconds']/3600,1)==37.1
    for r in fees:
        assert sha(OUT/r['receipt'])==r['receipt_SHA']
        receipt=read(OUT/r['receipt']);assert receipt['exit_observed'] and not receipt['timeout']
    docs=['docs/round158_research.md','docs/current_mainline.md','docs/paper_review.md','docs/unified_exact_research_index.md']
    for path in docs:
        text=(ROOT/path).read_text(encoding='utf-8');assert 'round158' in text
    write(TARGET,dict(UTC=utc(),PASS=False,paper_claims_PASS=True,own_receipt_pending_seal=True,Optimize=0,
        review_method='Same agent separate saved-data/source/PDF identity checks and manual argument review; no independent reviewer identity',
        source_SHA=render['source_SHA'],PDF_SHA=render['PDF_SHA'],pages=5,visual_review_SHA=sha(OUT/'paper_qa/visual_review.json'),
        scientific_review_SHA=sha(OUT/'review/final_scientific_review.json'),render_receipt_SHA=sha(OUT/'paper_qa/render_receipt.json'),
        manual_argument_review=[
            'Domain containment orders minima; a true integer original-T resource witness caps only cut domains containing that D_R.',
            'The hard cutoff covers integer low-J stocks through q=G, one-hot per-station positive-excess correction and upward RHS.',
            'Rounded endpoint budgets and delta monotonicity imply the old rows; actual emitted RHS checks and R92 cases are reused.',
            'Uniform ownership obeys eligibility, assignment and return balance. Singleton/large-subset and forbidden-set inequalities follow from the stated M/P/U conditions.',
            'The exact saved fractional point is not an integer U_R and implies neither a global strict optimum gap nor a ceiling on extra integer-valid cuts.',
            'TIME_LIMIT/UNKNOWN, finite family scopes, coefficient-transfer qualification and absence of E+R/physical improvement are stated without extrapolation.'],
        other_fee_count=len(fees),other_G1_seconds=budget()['G1_seconds'],
        exact_report_fee_totals='Refresh pure report assembly after this receipt closes; paper total is rounded to one decimal hour.',
        own_receipt='fees/'+LABEL+'/receipt.json',complete_goal_delivery='Publication/recovery/final acceptance still pending'))
    print(json.dumps(dict(paper_claims_PASS=True,own_receipt_pending_seal=True,Optimize=0,pages=5)),flush=True)

def seal():
    r=read(TARGET);assert r['paper_claims_PASS'] and r['own_receipt_pending_seal']
    receipt=read(OUT/r['own_receipt']);b=budget()
    assert receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout'] and not b['unclosed']
    assert abs(r['other_G1_seconds']+receipt['G1_seconds']-b['G1_seconds'])<1e-8
    assert round(b['G1_seconds']/3600,1)==37.1
    for name,digest in r['source_SHA'].items():assert sha(OUT/name)==digest
    assert sha(OUT/'manuscript.pdf')==r['PDF_SHA']
    r.update(PASS=True,own_receipt_pending_seal=False,own_receipt_SHA=sha(OUT/r['own_receipt']),
        all_fees_closed_at_seal=True,closed_G1_seconds=b['G1_seconds'],seal_UTC=utc())
    write(TARGET,r);print(json.dumps(dict(PASS=True,G1_seconds=b['G1_seconds'],fees=r['other_fee_count']+1)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
