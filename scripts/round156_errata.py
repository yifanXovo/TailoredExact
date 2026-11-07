"""Re-export R155 checkpoints using the actual producer outer time origin."""
import csv
from round156_common import *

def run():
    old=PRIOR/'results/unified_exact_round155';matrix=read(old/'confirmation_matrix.json')
    old_rows=read(old/'reports/common_checkpoints.json')['rows']
    rows=[];origins=[];mechanisms=[];changed=[]
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination']);arm=read(d/'round154_endpoint.json')
        audit=read(d/'audit.json');assert audit['passed'] and not audit['source_rejections']
        producer=read(d/'producer_receipt.json');marker=read(d/'process_start_marker.json')
        offset=marker['unix_seconds']-producer['t0_unix'];assert offset>=0
        origins.append(dict(role=launch['id'],method=launch['R154_method'],
            marker_unix_seconds=marker['unix_seconds'],producer_t0_unix=producer['t0_unix'],offset=offset,
            marker_SHA=sha(d/'process_start_marker.json'),producer_SHA=sha(d/'producer_receipt.json'),
            observations_SHA=sha(d/'observations.json'),endpoint_SHA=sha(d/'round154_endpoint.json')))
        obs=read(d/'observations.json');events=[]
        for record in obs:
            p=record['payload'];kind=p['kind']
            event=dict(t=record['effective_available_seconds']+offset,
                marker_relative_t=record['effective_available_seconds'],sequence=p['sequence'],kind=kind)
            if kind=='witness':event['U']=p['objective']
            elif kind=='bound' and p['global_available']:
                assert p['local_available'] and not p['retrospective'];event['L']=p['global_bound']
            elif kind=='call' and not p['full_original'] and p['cover']:
                covered=0.
                for piece in sorted(p['cover'],key=lambda q:q['lower_g']):
                    assert piece['lower_g']<=covered+1e-12;covered=max(covered,piece['upper_g'])
                assert covered+1e-12>=min(p['cutoff'],p['gmax'])
                event['L']=min([p['cutoff']]+[min(q['lower'],q['cutoff']) for q in p['cover']])
            else:continue
            events.append(event)
        root=read(d/'round153_control_audit.json')['root'];floor_time=None;floor=None
        if launch['R154_method']=='E' and root and root['qualified']:
            ledger=read(d/'round154_control_audit.json')['proof_ledger']
            assert ledger['root_complete'] and ledger['sources_live']
            first=next(r for r in obs if r['payload']['kind']=='call')
            floor_time=first['effective_available_seconds']+offset
            floor=min(root['own_cutoff'],root['lower'])
            events.append(dict(t=floor_time,marker_relative_t=first['effective_available_seconds'],
                sequence=first['sequence'],kind='own_floor_available',floor=floor))
        events.sort(key=lambda e:(e['t'],e['sequence']))
        U=None;L=0.;active_floor=None;trace=[];crossing=None;previous_below=None
        for e in events:
            if 'U' in e:U=e['U'] if U is None else min(U,e['U'])
            if 'L' in e:L=max(L,e['L'])
            if 'floor' in e:active_floor=e['floor']
            proof=max(L,active_floor) if active_floor is not None else L
            trace.append(dict(**e,verified_U=U,raw_search_L_last_committed=L,supported_proof_L=proof,
                own_floor_active=active_floor is not None and L<active_floor))
            if active_floor is not None:
                if L<active_floor:previous_below=e['t']
                elif crossing is None:crossing=dict(first_observed_at=e['t'],last_observed_below_at=previous_below)
        save_gz(OUT/'reports/r155_time_chains'/f'{launch["arm_id"]}.json.gz',trace)
        for cap in ([2400,3600,4800,7200] if launch['cap_seconds']==7200 else [1200]):
            if arm['T_produce']<=cap:
                r=dict(U=arm['U'],raw_search_L=arm.get('raw_search_L',arm['L']),proof_L=arm['L'],
                    observed_at=arm['T_produce'],state='finished_before_checkpoint',certificate=arm['certificate'],T_cert=arm['T_cert'])
            else:
                available=[e for e in trace if e['t']<=cap];last=available[-1] if available else None
                r=dict(U=last['verified_U'] if last else None,raw_search_L=last['raw_search_L_last_committed'] if last else None,
                    proof_L=last['supported_proof_L'] if last else None,observed_at=last['t'] if last else None,
                    state='last_committed_information',certificate=False,T_cert=None)
            r.update(role=launch['id'],method=launch['R154_method'],checkpoint_seconds=cap,
                time_origin='producer.t0_unix',marker_to_producer_offset=offset,
                same_long_run_checkpoint_not_independent_short_arm=True,exact_running_snapshot=False)
            r['gap']=r['U']-r['proof_L'] if r['U'] is not None else None
            previous=next(v for v in old_rows if (v['role'],v['method'],v['checkpoint_seconds'])==(r['role'],r['method'],cap))
            diffs={k:dict(old=previous[k],corrected=r[k]) for k in ('U','raw_search_L','proof_L') if previous[k]!=r[k]}
            if diffs:changed.append(dict(role=r['role'],method=r['method'],checkpoint=cap,changes=diffs))
            rows.append(r)
        mechanisms.append(dict(role=launch['id'],method=launch['R154_method'],own_floor=floor,
            floor_available_no_later_than=floor_time,raw_crossing_observation_bracket=crossing,
            time_origin='producer.t0_unix',physical_endpoint_U=arm['U'],endpoint_L=arm['L'],
            T_cert=arm['T_cert'],T_produce=arm['T_produce'],T_total=arm['T_total']))
    assert len(rows)==18 and len(changed)==1,changed
    one=changed[0];assert (one['role'],one['method'],one['checkpoint'])==('R-X35-S-T2','B',4800)
    assert one['changes']['raw_search_L']['corrected']==.21414084957658006
    write(OUT/'reports/r155_common_checkpoints.json',dict(rows=rows,mechanisms=mechanisms,origins=origins,changed_bounds=changed,
        fixed_science=SCIENCE155,old_checkpoint_SHA=sha(old/'reports/common_checkpoints.json'),old_science_untouched=True))
    with (OUT/'reports/r155_common_checkpoints.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write(OUT/'review/r155_clock_correction.json',dict(PASS=True,rows=18,changed_bounds=changed,
        origins=origins,source_SHA=sha(__file__),no_performance_rerun=True,final_U_L_Tcert_costs_unchanged=True))
    print(json.dumps(dict(PASS=True,changed=changed,mechanisms=mechanisms)),flush=True)

if __name__=='__main__':run()
