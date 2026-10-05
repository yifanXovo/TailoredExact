"""Reuse established R100/101 readers; no forensic overlay or native Optimize.
Run only when performance is idle. Fees are reconciled separately once.
"""
import sys,json,math
from pathlib import Path
import round101_reporting_core as core
import round101_clock_core as clock
from round102_common import *
from round100_idle import ensure_idle

def records(camp):
    return [json.loads(x) for x in (Path(camp)/'summary.jsonl').read_text().splitlines()]

def main(label,campaigns):
    ensure_idle();core.OUT=clock.OUT=OUT
    core.records_view=clock.records_view=records
    core.audit_view=clock.audit_view=lambda d:read(Path(d)/'audit.json')
    original_save=clock.save
    def save_clock(path,rows):
        if Path(path).name=='discovery_certification.csv':
            for r in rows:r['scope']=r['scope'].replace('offline independent audit separately engineering','recorded postexit offline audit additionally charged in Round102 budget')
        original_save(path,rows)
    clock.save=save_clock
    # A normal unproved exit before1800 does not cover the1800 checkpoint.
    # Add the last whole second shared by all arms of each completed role,
    # chosen from observed completion costs, never from quality or native Work.
    final_common=[]
    for name in campaigns:
        done=records(OUT/name)
        for role in {r['id'] for r in done}:
            final_common.append(math.floor(min(r['completion']['end_to_end_seconds'] for r in done if r['id']==role)))
    clock.CHECKPOINTS=sorted(set(clock.CHECKPOINTS+[1500]+final_common))
    core.extract(label,campaigns);clock.main(label+'_clocks',campaigns)
    target=OUT/label;native=[];global_rows={}
    for name in campaigns:
        for r in records(OUT/name):
            d=Path(r['destination'])
            for p in sorted((d/'external/native_logs').glob('*.round102.summary.json')):
                s=read(p);log=Path(str(p).replace('.round102.summary.json',''))
                evidence,_,_=core.native_log(log)
                cp=Path(str(p).replace('.summary.json','.certificates.jsonl'))
                rows=[json.loads(x) for x in cp.read_text().splitlines()]
                literals={(tuple((j,a) for j,a,x in row['columns']),row['rhs']) for row in rows}
                if rows:
                    binding=read(Path(str(p).replace('.summary.json','.contract.json')))
                    semantic={j:(k,i,tag) for k,stations in enumerate(binding['column_contract']['service_columns'])
                        for i,cols in enumerate(stations[1:],1) for tag,j in zip(['p','d','z'],cols)}
                    key=(r['id'],binding['input_sha256'],r['arm'])
                    group=global_rows.setdefault(key,dict(signatures=set(),saved=0,API0=0))
                    for row in rows:
                        group['signatures'].add((tuple(sorted((semantic[j],float(a).hex()) for j,a,x in row['columns'])),float(row['rhs']).hex()))
                        group['saved']+=1;group['API0']+=row['api_code']==0
                native.append(dict(campaign=name,number=r['number'],role=r['id'],arm=r['arm'],
                    path=p.relative_to(ROOT).as_posix(),sha256=sha(p),
                    native_User_count=json.loads(evidence['cuts']).get('User'),
                    literal_rows=len(literals),saved_rows=len(rows),
                    nonzeros_min=min((len(x['columns']) for x in rows),default=None),
                    nonzeros_max=max((len(x['columns']) for x in rows),default=None),**s))
    core.csv_write(target/'service_native_calls.csv',native)
    core.csv_write(target/'service_distinct_rows.csv',[dict(role=role,input_sha256=h,arm=arm,
        distinct_original_service_rows=len(g['signatures']),saved_rows=g['saved'],API0_submissions=g['API0'],
        scope='Exact literal coefficient/RHS equality after mapping to physical car/station/p,d,z names, aggregated across listed native MIPs/campaigns; API0 counts are submissions, not distinct rows or retention')
        for (role,h,arm),g in sorted(global_rows.items())])
    cp=OUT/(label+'_clocks')/'checkpoints.csv'
    groups={}
    for r in core.csv_read(cp):
        if r['covered']=='True':groups.setdefault((r['campaign'],r['role'],r['checkpoint_full_seconds']),{})[r['arm']]=r
    paired=[]
    for (camp,role,t),g in groups.items():
        for ref,cand in [('P-GRB','ENS-C'),('P-GRB','J-SUBMIT'),('ENS-C','J-SUBMIT')]:
            if ref not in g or cand not in g:continue
            a,b=g[ref],g[cand]
            def num(r,k):return float(r[k]) if r[k] else None
            au,bu,ag,bg=num(a,'U'),num(b,'U'),num(a,'gap'),num(b,'gap')
            paired.append(dict(campaign=camp,role=role,checkpoint_full_seconds=float(t),reference=ref,candidate=cand,
                reference_U=au,candidate_U=bu,reference_L=num(a,'L'),candidate_L=num(b,'L'),
                reference_gap=ag,candidate_gap=bg,U_delta=bu-au if au is not None and bu is not None else None,
                gap_delta=bg-ag if ag is not None and bg is not None else None,
                material_U_change=bool(au is not None and bu is not None and abs(bu-au)>=.001 and abs(bu-au)/max(abs(au),1e-12)>=.01),
                material_gap_change=bool(ag is not None and bg is not None and abs(bg-ag)>=.001 and abs(bg-ag)/max(abs(ag),1e-12)>=.1),
                scope='Both same-run scope-verified prefixes covered; certified endpoint may carry; no interpolation or combined certificate'))
    core.csv_write(target/'checkpoint_pairs.csv',paired)
    full=[(name,r) for name in campaigns for r in records(OUT/name)]
    isolation=[]
    for shadow_camp,b in full:
        if b['arm']!='J-SHADOW' or b['completion']['end_to_end_seconds']<300:continue
        qb=read(OUT/shadow_camp/'identity.json')
        for ref_camp,a in full:
            if a['id']!=b['id'] or a['arm'] not in ['ENS-C','J-SUBMIT']:continue
            if a['completion']['end_to_end_seconds']<300:continue
            qa=read(OUT/ref_camp/'identity.json')
            assert qa['candidate_binary_sha256']==qb['candidate_binary_sha256']
            assert qa['source_hashes']==qb['source_hashes'] and qa['helpers']==qb['helpers']
            pa=qa['launches'][a['number']-1]['panel'];pb=qb['launches'][b['number']-1]['panel']
            assert pa['input_sha256']==pb['input_sha256'] and pa['cap_seconds']==pb['cap_seconds']
            both=a['endpoint']['certificate'] and b['endpoint']['certificate']
            # Reference SHADOW; compare submission or baseline on the same PE.
            dt=a['completion']['end_to_end_seconds']-b['completion']['end_to_end_seconds'] if both else None
            ug=a['endpoint']['U']-b['endpoint']['U'];gg=a['endpoint']['gap']-b['endpoint']['gap']
            isolation.append(dict(role=a['id'],reference_campaign=shadow_camp,reference='J-SHADOW',candidate_campaign=ref_camp,candidate=a['arm'],
                both_certified=both,certified_time_delta=dt,material_time_change=bool(both and abs(dt)>=30 and abs(dt)/b['completion']['end_to_end_seconds']>=.1),
                reference_U=b['endpoint']['U'],candidate_U=a['endpoint']['U'],reference_L=b['endpoint']['L'],candidate_L=a['endpoint']['L'],
                U_delta=ug,gap_delta=gg,material_U_change=abs(ug)>=.001 and abs(ug)/max(abs(b['endpoint']['U']),1e-12)>=.01,
                material_gap_change=abs(gg)>=.001 and abs(gg)/max(abs(b['endpoint']['gap']),1e-12)>=.1,
                scope='Same frozen PE/source/helper/input/cap; separate completed runs, own endpoints; unproved eventual time unknown; no pure-cut causal or statistical stability claim'))
    core.csv_write(target/'isolation_pairs.csv',isolation)
    from round102_budget import account
    budget=account();assert budget['within_limits'] and not budget['incomplete']
    write(target/'fee_reconciliation.json',budget)
    write(target/'reporting_identity.json',dict(Optimize=0,reader_sha256=sha(core.__file__),clock_sha256=sha(clock.__file__),wrapper_sha256=sha(__file__),
        no_R101_recovery_overlay=True,additional_shared_whole_second_checkpoints=final_common,
        fee_scope='fee_reconciliation includes every Round102 billed batch; core cost table covers only listed full campaigns, not added together',
        reliable_count='Before catalog truncation; not selected/submitted/API count',API_success_is_not_retention=True))
    print(json.dumps(dict(passed=True,runs=sum(len(records(OUT/c)) for c in campaigns),Optimize=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
