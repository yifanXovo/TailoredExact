"""Small read-only arithmetic and selection evidence; no H, solver or redraw."""
from round129_common import *
from fractions import Fraction
import csv

def inspect():
    roles=read(OUT/'input_manifest.json')['new_roles'];arithmetic=[]
    for p in roles:
        v=read(ROOT/p['input_path'].replace('.txt','_parsed.json'))
        b,D,w=v['initial'][1:],v['target'][1:],v['weights'][1:]
        assert len(b)==len(D)==len(w)==p['V']
        assert all(d>0 for d in D) and all(x>0 for x in w)
        shortage=sum(D)-sum(b)
        decimal_delta=min(Fraction('0.15')*Fraction(str(x))/d for x,d in zip(w,D))
        parsed_delta=min(Fraction.from_float(.15)*Fraction.from_float(float(x))/d for x,d in zip(w,D))
        if p['inventory']=='shortage':assert shortage>0 and decimal_delta*shortage>0 and parsed_delta*shortage>0
        arithmetic.append(dict(id=p['id'],service_indices=f'1..{p["V"]}; depot excluded',sum_b=sum(b),sum_D=sum(D),shortage=shortage,
            decimal_lambda='0.15',parsed_binary64_lambda_hex=float(.15).hex(),
            decimal_weights=[str(x) for x in w],parsed_binary64_weights_hex=[float(x).hex() for x in w],
            decimal_delta_rational=str(decimal_delta),parsed_binary64_delta_rational=str(parsed_delta),
            decimal_necessary_floor_rational=str(decimal_delta*shortage),parsed_binary64_necessary_floor_rational=str(parsed_delta*shortage),
            decimal_necessary_floor=float(decimal_delta*shortage),parsed_binary64_necessary_floor=float(parsed_delta*shortage),
            positive_shortage_floor=p['inventory']=='shortage',no_model_Start_or_reported_native_L_injection=True))
    snapshots=[];history={}
    for rn in [122,126,127,128]:
        root=WORK/f'worktrees/round{rn}';mp=root/f'results/unified_exact_round{rn}/input_manifest.json';m=read(mp);seen=set()
        for key in ['roles','new_roles','tiny_roles','main_roles','core_roles','training_roles']:
            for p in m.get(key,[]):
                token=(p.get('id'),p.get('input_sha256'))
                if token in seen:continue
                seen.add(token);sp=p.get('selection_path')
                if not sp and key=='tiny_roles':sp=f'results/unified_exact_round127/inputs/{p["id"]}_selection.json'
                if not sp:continue
                path=root/sp
                if not path.is_file():path=ROOT/sp
                if not path.is_file():continue
                raw=path.read_bytes();s=read(path);indices=s['selected_source_station_row_indices']
                assert len(set(indices))==p['V']
                record=dict(round=rn,id=p['id'],source=p['source'],V=p['V'],input_SHA=p['input_sha256'],
                    manifest_SHA=sha(mp),selection_path=sp,selection_SHA=sha(path),selection_bytes=len(raw),
                    original_utf8_text=raw.decode('utf-8'),selected_source_station_row_indices=indices)
                snapshots.append(record);history[rn,p['id']]=record
    current={p['id']:p for p in roles};rows=[]
    for name in ['station_overlap.csv','station_overlap_tiny_addendum.csv']:
        with (OUT/name).open(encoding='utf-8-sig',newline='') as f:rows.extend(csv.DictReader(f))
    for row in rows:
        p=current[row['id']];a=set(read(ROOT/p['selection_path'])['selected_source_station_row_indices'])
        rn=int(row['previous_round'])
        if rn==129:
            q=current[row['previous_id']];b=set(read(ROOT/q['selection_path'])['selected_source_station_row_indices']);digest=sha(ROOT/q['selection_path'])
        else:
            q=history[rn,row['previous_id']];b=set(q['selected_source_station_row_indices']);digest=q['selection_SHA']
        assert len(a&b)==int(row['station_overlap']) and digest==row['previous_selection_SHA']
    write(OUT/'evidence/historical_selection_snapshots.json',dict(schema='round129-small-selection-snapshots-v1',snapshots=snapshots,
        purpose='Recompute only the reported station overlaps without any old checkout or large historical carrier',
        full_historical_campaign_recovered=False,original_small_selection_bytes_preserved=True))
    write(OUT/'parsed_binary64_shortage_audit.json',dict(UTC=utc(),roles=arithmetic,overlap_rows_recomputed=len(rows),
        historical_small_selection_snapshots=len(snapshots),Optimize=0,H_calls=0,LP_calls=0,MIP_calls=0,
        input_recipe_hashes_changed=False,no_redraw_or_role_replacement=True,
        scope='Distinguish exact serialized decimal data from exact rational values of parsed binary64 data; no claim of a global floating-point error bound'))
    print(json.dumps(dict(arithmetic_roles=len(arithmetic),overlaps=len(rows),selection_snapshots=len(snapshots),Optimize=0)))

if __name__=='__main__':inspect()
