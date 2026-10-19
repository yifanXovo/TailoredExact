"""Read only already-available small history manifests/selections; no recovery or solves."""
from round126_common import *
import csv

def inspect():
    current=read(OUT/'input_manifest.json')['roles'];old=[];scope=[]
    for rn,root,source in [
        (109,Path('E:/codes/ExactEBRP-round109'),'CITI'),
        (116,Path('E:/codes/ExactEBRP-round116'),'CABI'),
        (118,Path('E:/codes/ExactEBRP-round118'),'CABI'),
        (121,Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP'),None),
        (122,WORK/'worktrees/round122',None)]:
        path=root/f'results/unified_exact_round{rn}/input_manifest.json'
        if not path.is_file():scope.append(dict(round=rn,status='manifest unavailable; not recovered'));continue
        m=read(path);seen=set();used=0;skipped=0
        for key in ['new_roles','roles','development_roles','core_roles']:
            for p in m.get(key,[]):
                if p.get('selection_path') is None:continue
                token=(p.get('id'),p['selection_path'])
                if token in seen:continue
                seen.add(token);s=source or p.get('source')
                if rn==121:s='CITI' if p['id'] in ['F2','R98-C2'] else 'CABI' if p['id']=='N40-R1-S' else None
                selection=root/p['selection_path']
                if s is None or not selection.is_file():skipped+=1;continue
                old.append(dict(round=rn,id=p['id'],source=s,V=p['V'],input_SHA=p.get('input_sha256'),
                    indices=set(read(selection)['selected_source_station_row_indices']),selection_SHA=sha(selection)))
                used+=1
        scope.append(dict(round=rn,manifest_SHA=sha(path),available_selections_read=used,unavailable_or_unknown_source_skipped=skipped))
    rows=[]
    for p in current:
        chosen=set(read(ROOT/p['selection_path'])['selected_source_station_row_indices'])
        for q in old:
            if p['source']!=q['source']:continue
            rows.append(dict(id=p['id'],source=p['source'],new_V=p['V'],previous_round=q['round'],previous_id=q['id'],previous_V=q['V'],
                station_overlap=len(chosen&q['indices']),same_input_SHA=p['input_sha256']==q['input_SHA'],previous_selection_SHA=q['selection_SHA']))
    assert not any(q['same_input_SHA'] for q in rows),'DATA_BLOCKED exact existing input; no redraw'
    for v in read(OUT/'input_manifest.json')['overlaps']:
        if v['previous_round']==126:rows.append(dict(id=v['id'],source=v['source'],new_V=v['new_V'],previous_round=126,
            previous_id=v['previous_id'],previous_V=v['previous_V'],station_overlap=v['overlap'],same_input_SHA=False,previous_selection_SHA='see input manifest'))
    with (OUT/'station_overlap.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
    write(OUT/'station_overlap_scope.json',dict(scope=scope,comparisons=len(rows),no_full_history_recovery=True,no_outcome_filter=True,
        selection_overlap_is_not_same_problem=True,Optimize=0))
    print(json.dumps(dict(comparisons=len(rows),scope=scope)))

if __name__=='__main__':inspect()
