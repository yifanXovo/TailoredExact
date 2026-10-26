"""Public-table adapter for the unchanged R57 pure geographic/inventory rules."""
import csv, hashlib, math, copy
from pathlib import Path
import generate_citibike443_regional_v1 as old

VERSION='round109-geographic-mb-evaluation-v1'
SOURCE_PATH='results/data_generation_citibike_round57/source_station_table.csv'
SOURCE_SHA='9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0'
old.FAMILY=VERSION

def load(root):
    data=(Path(root)/SOURCE_PATH).read_bytes()
    assert len(data)==69678 and hashlib.sha256(data).hexdigest()==SOURCE_SHA
    with (Path(root)/SOURCE_PATH).open(encoding='utf-8',newline='') as file:rows=list(csv.DictReader(file))
    stations=[]
    for row in rows:
        # Annotation IDs/names never select/re-pair the physical source row.
        stations.append(old.SourceStation(source_row_index=int(row['source_station_row_index']),
            legacy_internal_index=int(row['legacy_internal_index']),capacity=int(row['capacity']),
            x=float(row['utm18n_easting_m']),y=float(row['utm18n_northing_m']),
            companion_full_row_index=-1,companion_capacity=None,companion_match_status='public_table_annotations_unused',
            station_id='',name='',latitude=0.,longitude=0.))
    assert len(stations)==443 and [s.source_row_index for s in stations]==list(range(443))
    assert sum(0<s.capacity<100 for s in stations)==442
    return stations

def landscape(selection,regime,stations):
    # Equivalent R57 build_landscape mathematics; only public source binding and trace are added.
    by_index={s.source_row_index:s for s in stations}
    selected=[by_index[i] for i in selection['selected_source_station_row_indices']]
    capacities=[s.capacity for s in selected];target=old.target_profile(selection,stations)
    total=sum(target);total_capacity=sum(capacities)
    delta=max(selection['V'],int(math.floor(.12*total+.5)))
    if regime=='shortage':desired=max(0,total-delta);scale=.30
    elif regime=='balanced':desired=total;scale=.18
    elif regime=='surplus':desired=min(total_capacity,total+delta);scale=.30
    else:raise ValueError(regime)
    material=f"{VERSION}|inventory|{selection['selection_id']}|{regime}"
    order=old.hash_order(range(selection['V']),material);initial=target.copy()
    signs={i:1 if rank%2==0 else -1 for rank,i in enumerate(order)}
    for i in order:
        magnitude=max(1,int(math.floor(scale*capacities[i]+.5)))
        initial[i]=max(0,min(capacities[i],target[i]+signs[i]*magnitude))
    before=initial.copy();old.adjust_total(initial,desired,[0]*len(initial),capacities,order)
    after=initial.copy();old.ensure_both_local_signs(initial,target,capacities,material)
    assert sum(initial)==desired
    max_target=max(target);weights=[round(max(.1,(d/max_target)**2),old.WEIGHT_DECIMALS) for d in target]
    max_weight=max(weights);weights=[round(w/max_weight,old.WEIGHT_DECIMALS) for w in weights]
    minimum=[round(.10+.40*(d/c),old.MIN_RATIO_DECIMALS) for d,c in zip(target,capacities)]
    deltas=[b-d for b,d in zip(initial,target)]
    result=dict(schema='citibike443-station-landscape-v1',dataset_family=VERSION,
        classification='generated_untested_paper_candidate',generator_version=old.GENERATOR_VERSION,
        landscape_id=f"{selection['selection_id']}_{regime}",selection_id=selection['selection_id'],V=selection['V'],
        geographic_regime=selection['geographic_regime'],replicate=selection['replicate'],inventory_regime=regime,
        local_imbalance_level='moderate' if regime=='balanced' else 'high',seed=old.stable_seed(material),
        seed_derivation_material=material,source_station_row_indices=selection['selected_source_station_row_indices'],
        source_hashes=dict(public_table_sha256=SOURCE_SHA),
        depot=dict(artificial=True,coordinate_utm18n_meters=selection['depot_coordinate_utm18n_meters'],
            capacity_placeholder=100000,initial_placeholder=50000,target_placeholder=0),
        capacities=capacities,initial=initial,target=target,weights=weights,min_ratio=minimum,
        points_utm18n_meters=[[s.x,s.y] for s in selected],
        statistics=dict(selection['geographic_statistics'],capacity_minimum=min(capacities),capacity_maximum=max(capacities),
            capacity_mean=old.statistics.fmean(capacities),capacity_median=old.statistics.median(capacities),
            total_capacity=total_capacity,total_initial_inventory=sum(initial),total_target_inventory=total,
            station_inventory_minus_target=sum(initial)-total,absolute_total_shortage_or_surplus=abs(sum(initial)-total),
            local_l1_imbalance=sum(abs(x) for x in deltas),maximum_local_absolute_imbalance=max(abs(x) for x in deltas),
            surplus_station_count=sum(x>0 for x in deltas),deficit_station_count=sum(x<0 for x in deltas),
            balanced_station_count=sum(x==0 for x in deltas),weight_minimum=min(weights),weight_maximum=max(weights),
            weight_mean=old.statistics.fmean(weights),min_ratio_minimum=min(minimum),min_ratio_maximum=max(minimum)))
    result['generation_trace']=dict(initial_before_total_correction=before,initial_after_total_correction=after,
        initial_after_sign_repair=initial.copy(),desired_total=desired,delta_amount=delta,local_scale=scale,
        inventory_hash_order=order,sign_repair_hash_order=old.hash_order(range(selection['V']),material+'|sign-repair'),
        anchor_material=f"{VERSION}|geographic-anchor-set|V={selection['V']}",
        selection_material=selection['seed_derivation_material'],inventory_material=material,
        target_materials=[f"{VERSION}|target-profile|{selection['selection_id']}|row={i}" for i in selection['selected_source_station_row_indices']],
        inventory_order_materials=[f'{material}|{i}' for i in range(selection['V'])],
        sign_repair_order_materials=[f'{material}|sign-repair|{i}' for i in range(selection['V'])])
    return result

def assert_equivalent(selection,regime,stations,result):
    # Zero-solve oracle: inherited function receives public identity instead of opening private source files.
    original=old.sha256_file
    old.sha256_file=lambda path:SOURCE_SHA
    try:expected=old.build_landscape(selection,regime,stations)
    finally:old.sha256_file=original
    actual=copy.deepcopy(result);actual.pop('generation_trace')
    expected['source_hashes']={'public_table_sha256':SOURCE_SHA}
    assert actual==expected,'adapter changed inherited pure mathematics'
