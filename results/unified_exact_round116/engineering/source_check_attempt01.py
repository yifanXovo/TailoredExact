"""Recheck source lineage and six deterministic inputs without writes/native.

The forward projection was exercised in the original data preparation. This
portable check verifies the saved contract, raw row mappings, projected decimal
serialization and inverse checks; it does not independently rerun PROJ.
"""
import argparse, json, math, statistics, time
from pathlib import Path
import round108_reader as core
import round116_data as data
from read_round116 import ROUND

def check(root):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND
    manifest=core.read(out/'input_manifest.json');snapshot=core.read(out/'source/snapshot.json')
    assert core.sha(root/snapshot['station_response_path'])==manifest['raw_station_response_SHA']==snapshot['station_response_SHA']
    assert core.sha(out/'source/source_station_table.csv')==manifest['source_table_SHA']
    raw=core.read(root/snapshot['station_response_path'])['data']['stations']
    rows=core.rows(out/'source/source_station_table.csv');decisions=core.read(out/'source/row_decisions.json')
    assert len(raw)==len(rows)==len(decisions)==865
    for n,d in enumerate(decisions):
        assert d['original_row_index']==n and d['original_row']==raw[n] and d['qualified_physical_row'] and not d['exclusion_reasons']
    ids=[r['station_id'] for r in rows]
    assert ids==sorted(ids,key=lambda x:x.encode('utf-8')) and len(set(ids))==len(ids)
    contract=core.read(out/'projection_contract.json');area=contract['area_of_use'];stations=[]
    for n,r in enumerate(rows):
        assert int(r['source_row_index'])==n
        indices=json.loads(r['original_row_indices']);c=int(r['capacity']);lat=float(r['latitude']);lon=float(r['longitude'])
        assert 0<c<100 and area['west']<=lon<=area['east'] and area['south']<=lat<=area['north']
        assert abs(float(r['inverse_longitude'])-lon)<1e-10 and abs(float(r['inverse_latitude'])-lat)<1e-10
        x=float(r['utm18n_easting_unrounded_m']);y=float(r['utm18n_northing_unrounded_m'])
        assert math.isfinite(x) and math.isfinite(y) and 100000<x<900000 and 0<=y<9500000
        assert r['utm18n_easting_m']==f'{round(x,3):.3f}' and r['utm18n_northing_m']==f'{round(y,3):.3f}'
        for i in indices:
            q=raw[i];assert q['station_id']==r['station_id'] and q['capacity']==c and q['lat']==lat and q['lon']==lon and q.get('is_virtual_station') is not True
        stations.append(data.SourceStation(n,r['station_id'],c,round(x,3),round(y,3),lat,lon,tuple(indices)))
    data.configure(snapshot['station_response_SHA']);checked=[]
    for p in manifest['roles']:
        selection=data.select(stations,p['V'],p['geometry'],p['replicate']);selection['schema']='cabi-geographic-selection-v1'
        landscape=data.landscape(selection,p['inventory'],stations)
        assert selection==core.read(root/p['selection_path']) and landscape==core.read(root/p['landscape_path'])
        lines=data.old.instance_text(landscape,p['M'],p['Q_vector'][0]).splitlines()
        lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        expected=('\n'.join(lines).rstrip()+'\n').encode('utf-8')
        assert (root/p['input_path']).read_bytes()==expected and core.sha(root/p['input_path'])==p['input_sha256']
        parsed=data.old.parse_instance_mirror(root/p['input_path']);assert parsed==core.read(root/'reference/round116_external'/f"{p['id']}_parsed.json")
        assert landscape['depot']['coordinate_utm18n_meters']==[round(statistics.fmean(q[0] for q in parsed['points'][1:]),3),round(statistics.fmean(q[1] for q in parsed['points'][1:]),3)]
        checked.append(dict(id=p['id'],input_SHA=p['input_sha256'],bytes=len(expected),pure_generation_byte_equal=True))
    return dict(source_rows=865,roles=checked,raw_station_SHA=snapshot['station_response_SHA'],
        saved_projection_contract_SHA=core.sha(out/'projection_contract.json'),saved_inverse_and_serialization_checks=True,
        forward_PROJ_rerun=False,no_network=True,no_native=True,Optimize=0,seconds=time.perf_counter()-tick)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    a=parser.parse_args();value=check(a.root);core.write(Path(a.out),value);print(json.dumps(value),flush=True)
