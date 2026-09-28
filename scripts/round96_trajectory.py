"""Known-optimum publication intervals from audited journals, no Optimize.

Never treats a best-known feasible witness as an optimum or backfills a final
solution into an earlier checkpoint. Timing is verified-publication timing;
the precise internal discovery instant is not identifiable from these logs.
"""
import argparse
import csv
import json
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha,evidence

def main():
    parser=argparse.ArgumentParser();parser.add_argument('campaign',choices=['external','primal']);parser.add_argument('label')
    args=parser.parse_args();assert args.label.replace('_','').replace('-','').isalnum()
    camp=OUT/args.campaign;path=camp/'summary.jsonl'
    records=[json.loads(line) for line in path.read_text().splitlines()];assert all(r['audit_passed'] for r in records)
    certified={}
    for row in sorted(records,key=lambda r:r['number']):
        if row['endpoint']['certificate'] and row['id'] not in certified:certified[row['id']]=row
    result=[]
    for row in records:
        audit=read(Path(row['destination'])/'audit.json');assert audit['passed']
        endpoint=row['endpoint'];cost=row['completion']['process_wall_seconds'];ref=certified.get(row['id'])
        item=dict(role=row['id'],arm=row['arm'],certificate=endpoint['certificate'],process_seconds=cost,
            F_star_reference=None,F_star_source_arm=None,F_star_source_number=None,
            first_optimum_band_sequence=None,publication_interval_low=None,publication_interval_high=None,
            certified_tail_low=None,certified_tail_high=None,censored_tail_lower_bound=None,
            state='no_reliable_optimum_in_this_campaign')
        if ref:
            value=ref['endpoint']['U'];lower=ref['endpoint']['L']
            item.update(F_star_reference=value,F_star_source_arm=ref['arm'],F_star_source_number=ref['number'],
                state='known_optimum_band_not_observed')
            assert all(w['F']>=lower-1e-7 for w in audit['witnesses'])
            hits=[w for w in audit['witnesses'] if abs(w['F']-value)<=1e-7]
            if hits:
                witness=min(hits,key=lambda w:w['sequence']);seq=witness['sequence']
                raw=evidence.receipt(Path(row['destination'])/'journal'/f'event_{seq}.commit',
                    witness['available'],row['completion']['process_cap_seconds'])
                assert raw['payload']['kind']=='witness' and abs(raw['payload']['objective']-witness['F'])<1e-7
                lo=raw['data_close_seconds'];hi=witness['available'];assert 0<=lo<=hi<=cost+1
                item.update(state='known_optimum_band_published',first_optimum_band_sequence=seq,
                    publication_interval_low=lo,publication_interval_high=hi)
                if endpoint['certificate']:
                    item.update(certified_tail_low=max(0,cost-hi),certified_tail_high=max(0,cost-lo))
                else:item['censored_tail_lower_bound']=max(0,cost-hi)
            elif endpoint['certificate']:
                assert abs(endpoint['U']-value)<=1e-7
                item['state']='only_finalized_optimum_band_no_earlier_find_time_assigned'
        result.append(item)
    dest=OUT/(args.campaign+'_trajectory_'+args.label);dest.mkdir(exist_ok=False)
    write(dest/'timing.json',dict(rows=result,summary_sha256=sha(path),optimizer_calls=0,
        optimum_definition='First certified arm by frozen order on the identical role, using its own numerical certificate; no cross-arm merged certificate.',
        timing_definition='Interval from C++ data-close time to outer first-observed availability for the first independently verified witness within 1e-7 of the certified reference. Internal solver/heuristic discovery may be earlier and is not reconstructed.',
        tail_definition='Whole-process certified cost minus the verified-publication interval; includes remaining proof, physical verification and finalization. Censored tails are lower bounds only.'))
    with (dest/'timing.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(result[0]));writer.writeheader();writer.writerows(result)

if __name__=='__main__':main()
