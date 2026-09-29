"""Nonoverlapping outer-cost and native-call ledger from saved receipts."""
import argparse
import csv
import json
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha

def main():
    parser=argparse.ArgumentParser();parser.add_argument('label');args=parser.parse_args()
    assert args.label.replace('_','').replace('-','').isalnum()
    rows=[]
    def add(path,group,calls,micro=False):
        record=read(path)
        rows.append(dict(group=group,path=path.relative_to(ROOT).as_posix(),sha256=sha(path),
            seconds=record['wall_seconds'],native_calls=calls,native_micro=int(micro),
            conservative_starts=1))
    add(OUT/'qualification_outer.json','quantity_qualification',1,True)
    for path in sorted(OUT.glob('fixed_route_*.receipt.json')):add(path,'fixed_route',1)
    add(OUT/'multi_tests_001.json','multi_quantity_micro',0)
    for path in sorted((OUT/'multi_quantity').glob('*.completion.json')):add(path,'multi_quantity_real',0)
    add(OUT/'reorder_qualification.receipt.json','free_order_qualification',1,True)
    add(OUT/'reorder_F5_final.receipt.json','free_order_real',1)
    add(OUT/'route_order_micro.receipt.json','order_micro',0)
    for path in sorted((OUT/'route_order').glob('*.completion.json')):add(path,'order_real',0)
    for path in sorted((OUT/'route_order_cli').glob('*.receipt.json')):add(path,'CLI_identity',0)
    for campaign in ['external','primal']:
        for path in sorted((OUT/campaign/'reference').glob('*/completion.json')):add(path,'reference_export',0)
        summary=OUT/campaign/'summary.jsonl'
        if campaign=='external' and (OUT/'external_v2/admission.json').exists():summary=OUT/'external_v2/summary.jsonl'
        if campaign=='primal' and (OUT/'primal_v2/admission.json').exists():summary=OUT/'primal_v2/summary.jsonl'
        for record in [json.loads(line) for line in summary.read_text().splitlines()] if summary.exists() else []:
            path=Path(record['destination']);audit=read(ROOT/record['audit_path'] if 'audit_path' in record else path/'audit.json');assert record['audit_passed'] and audit['passed']
            ledger=path/'external/paper_optimize_ledger.csv'
            if record['arm']=='P-GRB':calls=1
            elif audit.get('administrative_hard_stop'):
                observations=read(path/'observations.json')
                calls=sum(r['payload']['kind']=='call' for r in observations)
                assert calls==audit['native_scope_adapter']['native_calls']
            else:
                with ledger.open(newline='',encoding='utf-8') as stream:calls=sum(1 for _ in csv.DictReader(stream))
                assert calls==audit['native_scope_adapter']['native_calls']
            completion=path/'completion.json'
            rows.append(dict(group=campaign,role=record['id'],arm=record['arm'],
                path=completion.relative_to(ROOT).as_posix(),sha256=sha(completion),
                seconds=record['completion']['process_wall_seconds'],native_calls=calls,native_micro=0,
                conservative_starts=1))
    offline=[]
    patterns=['*build*.receipt.json','*configure*.receipt.json','multi_build_001.json','multi_configure_001.json',
              'route_order_oracle.receipt.json','primal_auditor_fixture.receipt.json']
    for path in sorted(set(p for pattern in patterns for p in OUT.glob(pattern))):
        value=read(path)
        offline.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),seconds=value['wall_seconds']))
    dest=OUT/f'cost_report_{args.label}';dest.mkdir(exist_ok=False)
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with (dest/'costs.csv').open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(rows)
    write(dest/'summary.json',dict(completed_conservative_starts=len(rows),planned_total=67,authorized_about=72,
        native_micro=sum(r['native_micro'] for r in rows),native_calls=sum(r['native_calls'] for r in rows),
        outer_seconds=sum(r['seconds'] for r in rows),rows=rows,recorded_offline=offline,
        recorded_offline_seconds=sum(r['seconds'] for r in offline),source_sha256=sha(__file__),
        accounting='One outer receipt per diagnostic/test/export; formal process launch through exit includes all nested solver/init/validation cost. Batch wrappers, native runtime and serial-queue elapsed time are NOT added again. Completed launches only; an active or failed launch must be separately reconciled before final use.',
        offline_limit='Only recorded build/configure and timed audit costs are summed. Untimed reading, mathematical reasoning, report editing and archives are not inferred; no claim of complete wall-clock labor accounting.'))

if __name__=='__main__':main()
