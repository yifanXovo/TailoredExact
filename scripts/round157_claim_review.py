"""Record actual five-page visual inspection and check the final claim boundary."""
from round157_common import *

def run():
    render=read(OUT/'paper_qa/render_receipt.json')
    assert render['render_PASS'] and render['pages']==5 and not render['overfull_boxes']
    assert render['source_SHA']==sha(OUT/'manuscript.tex') and render['PDF_SHA']==sha(OUT/'manuscript.pdf')
    for p in render['page_images']:assert sha(ROOT/p['path'])==p['SHA256']
    paper=(OUT/'paper_qa/extracted_text.txt').read_text(encoding='utf-8')
    for number in ('6300.56543','6300.38986','6993.96882','0.2360521029074557','0.23648786033514127'):
        assert number in paper,number
    assert 'remains unresolved' in paper and 'not established a strict gap' in paper
    assert 'conditional eight-arm panel' in paper and 'not run' in paper
    review=read(OUT/'review/final_scientific_review.json');assert review['PASS'] and not review['scientific_blockers']
    decision=read(OUT/'final_decision.json');assert not decision['complete_candidate_frozen'] and not decision['complete_panel_started']
    result=read(OUT/'family_floor/rx35_two_families_v1/result.json')
    assert result['original_lower']==.2360521029074557 and not result['level_excluded']
    assert read(OUT/'source_manifest.json')['inherited_PE_executed_this_round'] is False
    report=(OUT/'final_report.md').read_text(encoding='utf-8')
    assert 'does not exclude its selected level' in report and 'no global lower gain' in report
    visuals=dict(UTC=utc(),PASS=True,pages_actually_viewed=[1,2,3,4,5],
        method='All five rendered PNG pages were emitted by view_image and visually inspected by the authoring agent before this receipt.',
        observations={'1':'Title, definitions, proposition and proof fit cleanly.',
            '2':'Invariance and fleet-load equations are legible; bottom continuation is not clipped.',
            '3':'Resource inequalities and objective-gap identity fit; section break is clean.',
            '4':'Evidence table, long numeric bounds and paragraph continuations fit without overlap.',
            '5':'Final bounded conclusion and references fit cleanly; expected white space on final page.'},
        PDF_SHA=sha(OUT/'manuscript.pdf'),source_SHA=sha(OUT/'manuscript.tex'),
        clipping_or_overlap=False,missing_glyphs=False,not_a_separate_person_review=True)
    write(OUT/'paper_qa/visual_review.json',visuals)
    write(OUT/'review/paper_claim_review.json',dict(UTC=utc(),PASS=True,scientific_blockers=[],Optimize=0,
        source_SHA=sha(__file__),paper_source_SHA=sha(OUT/'manuscript.tex'),PDF_SHA=sha(OUT/'manuscript.pdf'),
        actual_saved_scientific_review_SHA=sha(OUT/'review/final_scientific_review.json'),
        full_level_not_excluded=True,global_physical_bounds_unchanged=True,complete_algorithm_not_claimed=True,
        true_time_uppers_distinguished_from_relaxed_assignment_uppers=True,
        costs_authoritative_in_final_closed_fee_ledger=True,visual_review_SHA=sha(OUT/'paper_qa/visual_review.json'),
        review_kind='same-agent manual claim reading plus saved-evidence assertions; no independent-agent claim'))
    print(json.dumps(dict(PASS=True,pages=5,global_bound_gain=0.)),flush=True)

if __name__=='__main__':run()
