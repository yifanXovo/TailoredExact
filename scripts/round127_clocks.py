"""Read-only complete training clock from a real parent admission boundary.

The original sealed producer/total receipts are never edited. This same rule
applies to every singleton training position, including positions run after the
first-wrapper import fix. No runtime/cap is substituted for certification.
"""
from round127_common import *
def training_clock(name,arm):
    camp=OUT/name;i=read(camp/'identity.json');assert len(i['launches'])==1
    l=i['launches'][0];d=Path(l['destination']);producer=read(d/'producer_receipt.json');total=read(d/'arm_total_receipt.json')
    label=name.replace('/','_');fee=OUT/'fees'/label
    # A read-only recovery fee may follow the original producer fee, but the
    # producer belongs to the first actual training wrapper's admission marker.
    marker=read(fee/'PID.json')['launched_unix'];launch=read(fee/'launch.json')
    assert launch['command'][-1]==name and marker<=producer['t0_unix']<=producer['t_produce_unix']
    wall_raw=producer['t_produce_unix']-producer['t0_unix']
    assert abs(wall_raw-producer['T_produce'])<.05,('wall/performance clock inconsistency',name,wall_raw,producer['T_produce'])
    full=producer['t_produce_unix']-marker
    verify=total['T_verify'];qualified=arm.get('formal_protocol_qualified') and arm.get('numbers_qualified') and arm.get('certificate_qualified') and not arm.get('source_reduced') and full<=l['cap_seconds']
    value=dict(schema='round127-complete-training-admission-clock-v1',name=name,
        actual_parent_admission_unix=marker,sealed_producer_unix=producer['t_produce_unix'],
        start_scope='parent logical admission before launch.json/Popen; includes wrapper creation/imports; not OS wrapper birth',
        raw_receipt_T_produce=producer['T_produce'],raw_receipt_T_cert=arm.get('T_cert'),
        admission_prefix_seconds=producer['t0_unix']-marker,T_produce=full,T_verify=verify,T_total=full+verify,
        cap_seconds=l['cap_seconds'],within_complete_cap=full<=l['cap_seconds'],all_gates_qualified=bool(qualified),
        T_cert=full if qualified and arm.get('certificate') else None,
        producer_receipt_SHA=sha(d/'producer_receipt.json'),total_receipt_SHA=sha(d/'arm_total_receipt.json'),
        marker_receipt_SHA=sha(fee/'PID.json'),no_Optimize=True,no_original_receipt_changed=True,no_outer_fee_prefix_added_twice=True)
    p=camp/'complete_training_clock.json'
    if p.exists():assert read(p)==value,('complete clock drift',name)
    else:write(p,value)
    return value
