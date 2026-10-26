"""Read closed R105 records; no Optimize/IIS/DP or endpoint repair."""
from round105_common import *
import csv
import json
from pathlib import Path

def table(path,rows):
    with Path(path).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def build(label):
    dest=OUT/label;dest.mkdir(exist_ok=False);arms=[]
    for camp in sorted(OUT.iterdir()):
        if not (camp/'identity.json').exists():continue
        identity=read(camp/'identity.json')
        for a in identity['launches']:
            d=Path(a['destination'])
            if not (d/'completion.json').exists():continue
            completion=read(d/'completion.json');audit=read(d/'audit.json')
            recovered=d/'audit_recovery.json'
            if recovered.exists():audit=read(recovered)
            summary=read(d/'external/round105/summary.json') if (d/'external/round105/summary.json').exists() else {}
            endpoint=audit.get('endpoint') or {}
            row=dict(campaign=camp.name,id=a['id'],arm=a['arm'],cap_seconds=a['cap_seconds'],
                reserve_seconds=identity['prereg']['common']['shutdown_margin_seconds'],
                observed_end_to_end_seconds=completion['fully_observed_end_to_end_seconds'],
                audit_passed=audit['passed'],audit_recovery=recovered.exists(),
                status=endpoint.get('status','FAILED_NO_QUALIFIED_ENDPOINT'),
                certificate=endpoint.get('certificate',False),U=endpoint.get('U'),L=endpoint.get('L'),gap=endpoint.get('gap'),
                U0=summary.get('U0'),iterations=summary.get('iterations'),conflicts=summary.get('conflicts'),
                cache_hits=summary.get('cache_hits'),master_calls=summary.get('master_calls'),oracle_calls=summary.get('oracle_calls'),
                iis_calls=summary.get('iis_calls'),core_confirmation_calls=summary.get('core_confirmation_calls'),
                master_seconds=summary.get('master_seconds'),oracle_seconds=summary.get('oracle_seconds'),
                iis_seconds=summary.get('iis_seconds'),core_confirmation_seconds=summary.get('core_confirmation_seconds'),
                control_native_calls=audit.get('native_scope_adapter',{}).get('native_calls'),
                PE_sha256=identity['candidate_binary_sha256'],input_sha256=a['panel']['input_sha256'],
                destination=str(d.relative_to(ROOT)))
            arms.append(row)
    table(dest/'arm_results.csv',arms)
    pairs=[]
    for role in ['F2','R98-C2']:
        group=[a for a in arms if a['campaign']=='control01' and a['id']==role]
        for candidate in [a for a in group if a['arm'].startswith('IR-')]:
            for control in [a for a in group if a['arm'] in ['P-GRB','ENS-C']]:
                assert candidate['audit_passed'] and control['audit_passed']
                classification=('both_certified' if candidate['certificate'] and control['certificate'] else
                  'candidate_certified_control_censored' if candidate['certificate'] else
                  'control_certified_candidate_censored' if control['certificate'] else 'both_censored')
                pairs.append(dict(id=role,candidate=candidate['arm'],control=control['arm'],classification=classification,
                    candidate_seconds=candidate['observed_end_to_end_seconds'],control_seconds=control['observed_end_to_end_seconds'],
                    candidate_U=candidate['U'],candidate_L=candidate['L'],control_U=control['U'],control_L=control['L'],
                    certified_time_ratio=(candidate['observed_end_to_end_seconds']/control['observed_end_to_end_seconds']
                                          if classification=='both_certified' else None)))
    table(dest/'paired_results.csv',pairs)
    fees=[]
    for folder in sorted((OUT/'fees').iterdir()):
        launch=read(folder/'launch.json');receipt=read(folder/'receipt.json');cmd=launch['command'];children=0
        script=Path(cmd[1]).name if len(cmd)>1 else ''
        if script=='round105_campaign.py' and cmd[2]=='prepare':
            children=read(OUT/cmd[3]/'identity.json')['reference_children']
        elif script=='round105_campaign.py' and cmd[2]=='run':
            a=read(OUT/cmd[3]/'identity.json')['launches'][int(cmd[4])-1]
            children=int((Path(a['destination'])/'process_start_marker.json').exists())
        elif script=='round105_batch.py':
            q=read(OUT/cmd[2]/'identity.json')
            children=sum((Path(a['destination'])/'process_start_marker.json').exists()
                         for a in q['launches'][int(cmd[3])-1:int(cmd[4])])
        elif script=='round105_modes.py' and cmd[2]=='batch':
            plan=read(cmd[3]);children=sum((ROOT/read(OUT/'modes'/j['label']/'manifest.json')['modes'][j['number']-1]['path']/'native_launch.json').exists() for j in plan['jobs'])
        elif 'review' in str(cmd[1]):
            # The independent review runner must declare any real subprocesses.
            child_record=OUT/'review/native_execution.json'
            if child_record.exists():children=read(child_record).get('subprocess_starts',0)
        fees.append(dict(label=folder.name,outer_seconds=receipt['outer_seconds'],exit_code=receipt['exit_code'],
            stop_reason=receipt['stop_reason'],outer_process_starts=1,nested_process_starts=children,
            conservative_process_starts=1+children))
    table(dest/'fees.csv',fees)
    native=[]
    for p in sorted(OUT.rglob('calls.csv')):
        with p.open(newline='') as f:rows=list(csv.DictReader(f))
        for phase in ['master','oracle','iis','core_confirm']:
            before=[r for r in rows if r['stage']=='before' and r['phase']==phase]
            after=[r for r in rows if r['stage']=='after' and r['phase']==phase]
            if before:native.append(dict(path=p.relative_to(ROOT).as_posix(),phase=phase,
                started=len(before),returned=len(after),missing_after=len(before)-len(after),
                native_seconds=sum(float(r['seconds']) for r in after)))
    table(dest/'native_calls.csv',native)
    starts=sum(f['conservative_process_starts'] for f in fees);seconds=sum(f['outer_seconds'] for f in fees)
    assert starts<=72 and seconds<=80000
    controls=sum(a['control_native_calls'] or 0 for a in arms)
    is_started=sum(r['started'] for r in native if r['phase']=='iis')
    independent_path=OUT/'review/native_execution.json'
    independent=read(independent_path) if independent_path.exists() else {}
    independent_opt=int(independent.get('Optimize_starts',0))
    independent_iis=int(independent.get('IIS_starts',0))
    write(dest/'summary.json',dict(paid_process_starts=starts,paid_outer_seconds=seconds,
        native_started=sum(r['started'] for r in native),native_returned=sum(r['returned'] for r in native),
        iis_started=is_started,P_ENS_native_Optimize_calls=controls,
        independent_review_Optimize_starts=independent_opt,
        independent_review_IIS_starts=independent_iis,
        all_IIS_starts=is_started+independent_iis,
        all_Optimize_starts=sum(r['started'] for r in native)-is_started+controls+independent_opt,
        missing_after=sum(r['missing_after'] for r in native),
        nested_native_seconds_are_not_added_to_outer_fees=True,
        P_ENS_calls_scope='Original journals/Optimize ledgers and audit native_scope_adapter; separate from R105 calls.csv',
        failed_fees=[f['label'] for f in fees if f['exit_code']!=0],
        source_sha256=sha(__file__),Optimize_calls=0))
    print(json.dumps(dict(report=label,paid_starts=starts,paid_seconds=seconds)))

if __name__=='__main__':build(sys.argv[1])
