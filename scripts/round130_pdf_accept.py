"""Record the author's actual affected-page inspection, after image viewing."""
from round130_common import *

def main():
    p=OUT/'review/pdf_render_manifest.json';current=read(p)
    previous=read(OUT/'review/pdf_render_manifest.prior01.json')
    assert current['PDF_SHA']==sha(OUT/'manuscript.pdf')=='eb88fadde90b830847f251a66195ffceef8c39280b4915c8677db79c356ca235'
    viewed_first={1,2,3,4,8,9,10,11,12,13,14,32,33,34,35,36,37,38,48,49,50,53,54,65,66,74}
    viewed_final={29,30,31,49}
    old={r['page']:r for r in previous['rendered_images']}
    assert set(old)==viewed_first
    inherited=[];new=[];duplicates=[]
    for row in current['rendered_images']:
        assert sha(row['path'])==row['SHA']
        if row['page'] in old and row['SHA']==old[row['page']]['SHA']:
            inherited.append(row['page']);duplicates.append(old[row['page']])
        else:new.append(row['page'])
    assert set(new)==viewed_final
    assert len(current['rendered_images'])==29 and len(inherited)==25
    current.update(status='PASS',UTC=utc(),inspected_all_rendered_pages=True,
        actually_viewed_initial_images=sorted(viewed_first),
        final_new_or_changed_images_actually_viewed=sorted(viewed_final),
        final_images_with_byte_identical_already_viewed_PNGs=inherited,
        byte_identical_prior_images=duplicates,
        no_visible_clipping_overlap_missing_glyphs_or_truncated_tables_in_reviewed_regions=True,
        checks=['sole S2 and pair-only policy','unrelabeled historical tables and chronology',
                'all24 clocks in six table rows','strict directions versus symmetric time-close scope',
                'contribution matrix and negative signed gap','explicit ms2/Seed command',
                'preserved mathematical and H/controller appendix entries'],
        layout_repair='One new method/version/domain phrase exceeded the text line by24.18pt; normal breakable prose fixed it. Distinct attempt01 PDF and render receipt retained.',
        remaining_warnings='Inherited tiny table alignment0.13/0.17pt and old paragraph1.50pt warnings plus duplicate hyperref option; no visible truncation in inspected pages. No full historical-page revalidation claim.',
        distinct_prior_PDF_preserved=True,
        scope='29 affected pages of81; 26 initial images actually viewed, then four new/changed final pages viewed and25 final PNG hashes matched identical viewed pixels. Old unaffected pages not all rerendered.')
    write(OUT/'review/pdf_visual_review.json',current)
    lineage=read(OUT/'manuscript_lineage.json');lineage.update(PDF_pending=False,PDF_SHA=current['PDF_SHA'],actual_visual_review='review/pdf_visual_review.json')
    write(OUT/'manuscript_lineage.json',lineage)
    export=read(OUT/'pdf_export.json');export.update(visual_review_pending=False,PDF_SHA=current['PDF_SHA'],actual_visual_review='review/pdf_visual_review.json')
    write(OUT/'pdf_export.json',export)
    print(json.dumps(dict(status='PASS',PDF_SHA=current['PDF_SHA'],affected_pages=29,total_pages=81)))

if __name__=='__main__':main()
