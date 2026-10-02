"""Keep physical witnesses, call boundaries, final bounds and useful bound steps."""
import csv
from round99_common import *

def main():
    folder=OUT/'complete_results_final';source=folder/'trajectories.csv'
    with source.open(newline='',encoding='utf-8') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    retained=set();last_kept={};last_row={}
    for i,row in enumerate(rows):
        if row['source']!='committed_bound':retained.add(i);continue
        key=(row['campaign'],row['number'],row['call']);last_row[key]=i
        old=last_kept.get(key);keep=old is None
        seconds=float(row['available_seconds']);flag=row['global_available']
        bound_name='global_bound' if flag in ['1','True','true'] and row['global_bound'] else 'native_bound'
        value=float(row[bound_name]) if row[bound_name] else None
        if old is not None:
            before=rows[old];old_value=float(before[bound_name]) if before[bound_name] else None
            keep=flag!=before['global_available'] or seconds-float(before['available_seconds'])>=60
            keep=keep or (value is not None and old_value is not None and abs(value-old_value)>=1e-4)
        if keep:retained.add(i);last_kept[key]=i
    retained.update(last_row.values())
    output=folder/'trajectories_key.csv'
    with output.open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows[i] for i in sorted(retained))
    write(folder/'trajectory_scope.json',dict(full_local_path=source.relative_to(ROOT).as_posix(),full_sha256=sha(source),
        full_rows=len(rows),retained_rows=len(retained),retained_sha256=sha(output),
        rules='all physical/rounded incumbent events, first/last per call, availability toggles, bound change>=1e-4 or60s; no interpolation',
        full_trace_retained_locally=True,optimizer_calls=0,script_sha256=sha(__file__)))
    path=OUT/'local_artifact_index.json';index=read(path)
    index['files'].append(dict(path=source.relative_to(ROOT).as_posix(),sha256=sha(source),bytes=source.stat().st_size,
        scope='full committed/native trajectory; compact key trace committed without interpolation'))
    path.write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(full_rows=len(rows),retained_rows=len(retained),optimizer_calls=0)))

if __name__=='__main__':main()
