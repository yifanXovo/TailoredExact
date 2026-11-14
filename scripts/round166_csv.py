"""Separate 28-column B-control increment; never writes a user/master CSV."""
from round166_common import *
import csv,io

def csv_increment():
    summary=read(OUT/'reports/summary.json');assert summary['complete']
    base=ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
    old_bytes=base.read_bytes();old=list(csv.reader(io.StringIO(old_bytes.decode('gb18030'))));header=old[0]
    assert len(old)==104 and len(header)==28 and header[-2:]==['','']
    arms=read(OUT/'reports/complete_arms.json');groups=read(OUT/'matrix_frozen.json')['groups']
    values=[];mapping=[]
    for arm in [a for a in arms if a['method']=='B']:
        group=next(g for g in groups if g['position']==arm['position']);p=group['launch']['panel']
        scenario={'shortage':'库存短缺','balanced':'库存平衡','surplus':'库存过剩'}[p['inventory']]
        geometry={'compact':'紧凑分布','regional':'区域分布','clustered':'簇状分布'}.get(p['geometry'],p['geometry'])
        code=p['id'].split('-')[-1];url='https://github.com/yifanXovo/TailoredExact/blob/codex/round166-structure-and-paper/'
        row=[p['id'],p['V'],p['M'],scenario,code,p['source'],geometry,p['T_seconds'],p['lambda'],p['lambda']/.15,
            0,1,166,p['cap_seconds'],'已收敛' if arm['certificate'] else '未收敛',
            arm['T_cert'] if arm['certificate'] else '', '' if arm['certificate'] else 100*arm['relative_gap'],arm['L'],arm['U'],
            '无配对结果','','','','','N/A',
            '本轮同构建B控制；无同轮P-GRB，N/A-P，不计Win/Lose；run='+arm['arm_id']+'；C166独立记录；CPP='+arm['source_commit']+'；PE='+arm['PE_SHA'],
            url+'results/unified_exact_round166/reports/complete_arms.json',url+p['input_path']]
        assert len(row)==28;values.append(row)
        mapping.append(dict(increment_row=len(values),position=arm['position'],id=arm['id'],method='B',run=arm['arm_id'],
            full_key=[p['normalized_full_key'],0,166,1],source_build=arm['source_commit'],PE_SHA=arm['PE_SHA'],
            raw_endpoint=arm['endpoint'],T_produce=arm['T_produce'],T_verify=arm['T_verify'],
            new_strict_B_P_pair=False,P_fields='unpaired/empty',old_rows_overwritten=0))
    assert len(values)==6
    target=OUT/'reports/GI_TBC_R166_B_controls_increment_28col.csv'
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(values)
    with target.open(encoding='utf-8-sig',newline='') as f:check=list(csv.reader(f))
    assert check[0]==header and len(check)==7 and all(len(r)==28 for r in check)
    assert base.read_bytes()==old_bytes
    write(OUT/'reports/CSV_increment_mapping.json',mapping)
    write(OUT/'CSV_reconciliation.json',dict(UTC=utc(),requested_master=dict(rows=106,columns=28,encoding='UTF-8 BOM',bytes=60603,
        SHA256='8f39e3a23b3b6df621139cb39b4db813ca3e992da091e97251ab8337fd2b0022',found=False),
        bounded_entry_search=read(OUT/'CSV_entry.json'),local_working_copy=dict(**bind(base),rows=103,columns=28,encoding='GB18030; no BOM',unchanged=True),
        missing_from_103=['R138 R-B35-S-T2 Seed1 cap2400 N/A-P','R155 N-B35-S Seed0 cap7200 N/A-P','R156 R-X35-S-T2 Seed0 cap7200 N/A-P'],
        no_missing_rows_fabricated=True,no_master_or_user_file_written=True,
        independent_increment=dict(**bind(target),rows=6,columns=28,encoding='UTF-8 BOM',B_controls=6,new_B_P_pairs=0,new_B_P_wins=0,
            header_exactly_preserved=True,trailing_unnamed_fields='original two source-link columns',merged_into_master=False),
        C166='six variant arms only in complete_arms/pairs; never called B',
        new_independent_physical_inputs=0,new_Seed_values=0,new_complete_runs=12,new_B_C166_pairs=6,
        note='The existing N/A-P semantics serialize P status as 无配对结果 and comparison as N/A. Same-key old controls remain unchanged; round166, full run/build/SHA and mapping distinguish new repetitions.'))
    print('Six B-only unpaired rows in separate28-column increment; zero master edits, zero strict B/P pairs.')

if __name__=='__main__':csv_increment()
