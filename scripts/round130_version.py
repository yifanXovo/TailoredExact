"""Adopt the selected version without relabelling predecessor measurements."""
from round130_common import *
import csv,io

def run():
    seal=read(OUT/'E3_frozen.json')
    write(OUT/'paper_version_manifest.json',dict(version='Round130',sole_proposed_method='GI-TBC (uniform pair-support implementation, MS2)',
        table_short_name='S2',algorithm_identity='original E2 --round127-mode ms2',predecessor_full_MB='original E2 --round127-mode mb',
        repository_default='ENS-C (unchanged)',paper_reproduction_entry=['--method','gcap-frontier','--algorithm-preset','research-round83-vds-equal-net-exchange','--round98-state-service','m-binary','--round90-lp-g-split','false','--round127-mode','ms2'],
        E2_PE_SHA=E2_SHA,E3_PE_SHA=seal['PE_SHA'],DLL_SHA=DLL_SHA,E3_is_not_E2_binary=True,
        support='pair cover and conditional rows only; no triple support on any input',
        unchanged=['complete H','representation','support enumeration and budget','ordered supply','C_G','A/B','Gini interval controller','AM thresholds','numeric tolerances','native defaults'],
        current_main_benchmark='cold P-GRB',controls=dict(PS='own paid H -> original compact full Start',S2R='pair-only inclusive fixed root LP + MIP; outer control disabled'),
        evidence_layers=dict(R127_R128_MS2='development / known roles',R129_new_four='prospective at selection time',R129_protection='separate known protection input',R130='three already-known attribution roles; not independent new validation'),
        manuscript_performance_policy='Only qualified actual MS2 observations directly support current main-method performance. Older full-MB/ENS observations retain their names and serve predecessor/background evidence.',
        larger_roles='Historical V35/V50/V60 observations do not establish final MS2 performance at those sizes; no historical rerun authorized',
        negative_results_preserved=['R112-R115 paid-start mixed outcomes','R127 q2 P-tuned holdout 0/3 versus default P1/3','R128 timing reversal and no-split roles','R129 C15/B30 open at both Seeds and B30 endpoint reversal'],
        selection_is_settled='All five R129 conditions passed; the user adopts MS2. This round is not another candidate selection.',
        formal_results_pending=not (OUT/'arms.csv').exists()))
    rows=[]
    specs=[(122,'arms.csv','predecessor benchmark'),(123,'arms.csv','predecessor proof-limit benchmark'),
        (126,'arms.csv','predecessor small-instance confirmation'),(127,'main_arms.csv','predecessor Seed1 confirmation'),
        (127,'core_arms.csv','development / known-role component diagnostics'),(128,'arms.csv','known-role inclusive-root and MS2 development'),
        (129,'arms.csv','prospective new four / separate protection'),(130,'arms.csv','known-role attribution diagnostics')]
    for round_no,filename,layer in specs:
        path=f'results/unified_exact_round{round_no}/{filename}'
        p=ROOT/path
        if p.exists():data=p.read_text(encoding='utf-8-sig')
        elif round_no!=130:
            try:data=git('show',BASE+':'+path).decode('utf-8-sig')
            except subprocess.CalledProcessError:continue
        else:continue
        for a in csv.DictReader(io.StringIO(data)):
            method=a.get('method') or a.get('arm') or 'unknown'
            current=method in ['S2','MS2'];config='uniform pair-support MS2' if current else 'full three-station M-B' if method in ['M-B','MB','MD-R'] else 'as named in original authority'
            if method=='MD-R':config='full three-station inclusive-root MD-R control'
            if method=='S2R':config='pair-only inclusive-root s2-root control'
            if method in ['MR','MG','MD']:config='R127 three-station predecessor diagnostic '+method
            if round_no==129:role='protection' if a.get('id')=='PB-C20-B' else 'prospective at R129 selection'
            elif round_no==130:role='known-role attribution diagnostic'
            else:role=layer
            rows.append(dict(round=round_no,id=a.get('id'),seed=a.get('seed','unknown'),method=method,actual_configuration=config,
                evidence_role=role,PE_SHA=a.get('PE_SHA','unknown'),DLL_SHA=a.get('DLL_SHA',DLL_SHA),input_SHA=a.get('input_SHA','unknown'),
                numerical_policy='original source/return/coverage policy; raw signed gaps retained; no new tolerance',
                clock='T_produce; T_cert only if qualified; separate T_verify/T_total',
                certificate=a.get('certificate','unknown'),T_cert=a.get('T_cert','unknown'),source_authority=path,
                direct_current_method_performance=bool(current),predecessor_numbers_relabelled=False))
    if rows:
        with (OUT/'evidence_migration.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'method_matrix.md').write_text('''# Round130 fixed method matrix

The sole proposed method is **GI-TBC (uniform pair-support implementation, MS2)**, table ID **S2**. The selected E2 `ms2` algorithm is unchanged in E3. Historical full M-B and ENS-C measurements keep their original identity. The repository default remains ENS-C; paper reproduction explicitly selects `ms2`.

| ID | Independently paid startup | Actual mathematical backend | Role |
| --- | --- | --- | --- |
| P | no H or external Start | original cold compact, one complete native MIP, defaults | sole primary benchmark |
| PS | full same H; own fully mapped and read-back Start | same original compact as P; one native MIP; no project cutoff, strengthening or root LP | same-start control |
| S2 | full same H | unchanged pair support, R, ordered supply, C_G, A/B, Gini interval control | sole paper method |
| S2R | full same H | inclusive `[0,min(U0,(n-1)/n)]`, `F_model<=U0`, pair-only strengthened root; complete LP then MIP, own full Start | outer-control package deletion control |

PS uses the existing `--round112-ens-start-compact` entry with research mode off. S2R uses exactly one `--round127-mode s2-root`; sequential conflicting old mode flags are forbidden by the frozen argv. Only the semantic interval-no-improver proof row is suppressed in S2R. Ordinary MS2 and full MD-R retain their old behavior.

All methods use one frozen E3, original DLL, original physical/numerical settings and complete 1200-second cap. H, mapping, validation, LP/MIP, output and shutdown share the deadline. P receives no other arm's solution. PS and S2R receive no extra budget. The fixed comparison types are S2/P, PS/P, S2/PS, S2/S2R and S2R/PS.

S2/PS measures the complete backend, representation and control increment after matched own H. S2/S2R measures the entire exposed outer control package only when actual H, initial scope, settings and effective root agree. S2R/PS also changes representation, preprocessing and cutoff domain; it is not a pure-cuts experiment. Splits alone do not prove a net benefit.
''',encoding='utf-8')
    print('PAPER_VERSION_ADOPTED; predecessor evidence retains original labels')
if __name__=='__main__':run()
