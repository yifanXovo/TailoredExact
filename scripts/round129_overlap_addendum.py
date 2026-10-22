"""Read only the two saved R127 tiny selections omitted by its pathless manifest."""
from round129_common import *
import csv

def inspect():
    prior_root=WORK/'worktrees/round127';mp=prior_root/'results/unified_exact_round127/input_manifest.json'
    old=read(mp)['tiny_roles'];current=read(OUT/'input_manifest.json')['new_roles'];rows=[];bindings=[]
    for q in old:
        sp=prior_root/'results/unified_exact_round127/inputs'/(q['id']+'_selection.json')
        s=read(sp);indices=set(s['selected_source_station_row_indices'])
        assert len(indices)==q['V']
        bindings.append(dict(id=q['id'],path=sp.relative_to(prior_root).as_posix(),SHA=sha(sp),
            input_SHA=q['input_sha256'],path_inferred_from_original_R127_serialization=True))
        for p in current:
            assert p['input_sha256']!=q['input_sha256'],'DATA_BLOCKED complete input duplicate'
            if p['source']!=q['source']:continue
            chosen=set(read(ROOT/p['selection_path'])['selected_source_station_row_indices'])
            rows.append(dict(id=p['id'],source=p['source'],new_V=p['V'],previous_round=127,previous_id=q['id'],previous_V=q['V'],
                station_overlap=len(chosen&indices),complete_input_duplicate=False,previous_selection_SHA=sha(sp)))
    with (OUT/'station_overlap_tiny_addendum.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
    write(OUT/'station_overlap_tiny_addendum.json',dict(UTC=utc(),reason='R127 tiny manifest has no selection_path; original small selection files exist',
        manifest_SHA=sha(mp),saved_selections=bindings,comparisons=len(rows),no_large_carrier_recovered=True,Optimize=0,
        no_input_or_recipe_changed=True,no_screening_or_redraw=True))
    print(json.dumps(dict(additional_comparisons=len(rows),overlaps=rows)))

if __name__=='__main__':inspect()
