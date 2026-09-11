"""Summarize existing evidence only; this script never starts an optimizer."""
import csv, json, math
from pathlib import Path
from round59_research import ROOT, OUT, RAW, sha, write
from analyze_round59 import csvwrite

def main():
    processes=[json.loads(s) for s in (OUT/'processes.jsonl').read_text().splitlines()]
    def arg(p,key,default=None):
        c=p['command'];return c[c.index(key)+1] if key in c else default
    scenarios={(arg(p,'--input'),arg(p,'--T')) for p in processes if p['scope']!='tiny_exact_only'}
    completed=[]
    for i,p in enumerate(processes):
        dest=Path(arg(p,'--artifact-dir')) if arg(p,'--artifact-dir') else Path(arg(p,'--out')).parent
        if not (dest/'completion.json').exists():continue
        c=json.loads((dest/'completion.json').read_text())
        next_start=processes[i+1]['started'] if i+1<len(processes) else None
        overlap=next_start is not None and p['started']+c['wall_seconds']>next_start+0.25
        assert not overlap, p
        completed.append(dict(process_number=p['process_number'],**c,next_optimizer_overlap=overlap))
    write(OUT/'process_completion_audit.json',completed)
    write(OUT/'budget_audit.json',dict(charged_processes=len(processes),limit=80,
        correctness_processes=sum(p['scope']=='tiny_exact_only' for p in processes),
        distinct_performance_scenarios_including_invalid_T=len(scenarios),
        longest_cap=max(p['cap'] for p in processes),runs_1800=0,runs_3600=0,
        optimizer_concurrency=1,build_only_identity_checks_excluded=True))
    evidence=[];trajectories=[];pairs=[];audits=[];formulation_pairs=[]
    for launch in sorted(RAW.glob('diagnostic_current_*/*/*/launch.json')):
        dest=launch.parent
        if not (dest/'completion.json').exists() or not (dest/'result.json').exists():continue
        ident=json.loads(launch.read_text());r=json.loads((dest/'result.json').read_text())
        assert not r['false_certificate'] and r['engineering_gate'], str(dest)
        if r['certificate']:
            assert r['lower_bound']>=r['verified_upper_bound']-1e-7*max(1,abs(r['verified_upper_bound']))
        identity=json.loads((dest/'state_identity.json').read_text())
        form=list(csv.DictReader((dest/'formulation_size_ledger.csv').open()))[0]
        pre=list(csv.DictReader((dest/'presolve_ledger.csv').open()))
        row=dict(id=ident['id'],arm=ident['arm'],stage=ident['stage'],model_sha256=r['model_sha256'],
            certificate_restricted_only=r['certificate'],LB=r['lower_bound'],UB=r['verified_upper_bound'],
            gap=r['gap'],process_seconds=r['process_time_seconds'],certificate_seconds=r['process_time_seconds'] if r['certificate'] else None,
            nodes=r['nodes'],iterations=r['simplex_iterations'],work=r['work'],
            root_bound=r['root_relaxation_bound'],root_cut_bound=r['final_root_cut_bound'],
            root_work=r['root_work'],root_seconds=r['root_time_seconds'],
            model_build_seconds=r['model_build_seconds'],model_read_seconds=r['model_read_seconds'],
            iterations_per_node=r['average_iterations_per_node'],
            nonroot_work_per_node=(r['work']-r['root_work'])/r['nodes'] if r['nodes'] else None,
            first_incumbent_native_seconds=r['first_incumbent_time_seconds'],
            added_rows=r['round59_added_rows_count'],added_rows_status=r['round59_added_rows_status'])
        for k in ['original_rows','original_columns','original_nonzeros','support_duration_pair_rows','support_duration_triple_rows','round51_subset_duration_rows','round51_subset_duration_big_m']:
            row[k]=form[k]
        if pre:
            row.update({'presolve_'+k:v for k,v in pre[0].items() if k not in ['state_id','policy']})
        sample=dest/'node_samples.csv.audit.json'
        if sample.exists():row.update({'monitor_'+k:v for k,v in json.loads(sample.read_text()).items()})
        progress=list(csv.DictReader((dest/'mip_progress.csv').open()))
        inc=[p for p in progress if p['incumbent_available']=='1' and float(p['incumbent'])<1e50]
        if inc:
            best=min(float(p['incumbent']) for p in inc)
            row['final_native_UB_first_reached_seconds']=next(float(p['time_seconds']) for p in inc if float(p['incumbent'])<=best+1e-9)
            row['tail_after_final_native_UB_seconds']=r['solver_time_seconds']-row['final_native_UB_first_reached_seconds']
        for t in [1,5,10,30,60,90,117]:
            eligible=[p for p in progress if float(p['time_seconds'])<=t]
            if eligible and t<=r['solver_time_seconds']:
                p=eligible[-1]
                trajectories.append(dict(id=ident['id'],arm=ident['arm'],stage=ident['stage'],
                    native_checkpoint=t,**p,time_scope='native_clock_not_end_to_end',certificate=False))
        evidence.append(row)
        audits.append(dict(id=ident['id'],arm=ident['arm'],stage=ident['stage'],
            model_sha256=r['model_sha256'],command_sha256=sha(dest/'command.json'),
            executable_sha256=ident['executable_sha256'],scope='restricted_state_only',
            certificate_contract_passed=True,state_identity=identity))
    for id in ['D3','D4']:
        arms={r['arm']:r for r in evidence if r['id']==id and r['stage'] in ['diagnostic_current_cuts','diagnostic_current_focus']}
        b=arms.get('F0')
        for arm in ['Monitor','Static','Pool','Focus1']:
            if arm not in arms or b is None:continue
            a=arms[arm];assert a['model_sha256']==b['model_sha256']
            pairs.append(dict(id=id,arm=arm,same_canonical_model=True,
                baseline_LB=b['LB'],candidate_LB=a['LB'],baseline_UB=b['UB'],candidate_UB=a['UB'],
                baseline_gap=b['gap'],candidate_gap=a['gap'],baseline_certificate=b['certificate_restricted_only'],
                candidate_certificate=a['certificate_restricted_only'],
                baseline_process=b['process_seconds'],candidate_process=a['process_seconds'],
                baseline_work=b['work'],candidate_work=a['work'],
                certified_time_ratio=a['process_seconds']/b['process_seconds'] if a['certificate_restricted_only'] and b['certificate_restricted_only'] else None))
        if 'Static' in arms and 'Pool' in arms:
            a=RAW/'diagnostic_current_cuts'/id/'Static/round59_additional_rows.csv'
            b=RAW/'diagnostic_current_cuts'/id/'Pool/round59_additional_rows.csv'
            assert a.read_bytes()==b.read_bytes()
        formulations={r['arm']:r for r in evidence if r['id']==id and r['stage']=='diagnostic_current_original'}
        if all(a in formulations for a in ['F0','OriginalCompact']):
            f0=formulations['F0'];compact=formulations['OriginalCompact']
            paths=[RAW/'diagnostic_current_original'/id/a for a in ['F0','OriginalCompact']]
            launches=[json.loads((p/'launch.json').read_text()) for p in paths]
            assert launches[0]['executable_sha256']==launches[1]['executable_sha256']
            commands=[json.loads((p/'command.json').read_text()) for p in paths]
            for key in ['gamma_lower','gamma_upper','verified_cutoff','process_cap_seconds','route_time_limit']:
                assert commands[0][key]==commands[1][key]
            origin=paths[1]/'original_compact_origin.lp'
            assert sha(origin)==arg(launches[1],'--round59-original-compact-sha256')
            formulation_pairs.append(dict(id=id,same_build=True,same_state=True,
                official_compact_origin_sha256=sha(origin),compact_LB=compact['LB'],f0_LB=f0['LB'],
                compact_UB=compact['UB'],f0_UB=f0['UB'],compact_gap=compact['gap'],f0_gap=f0['gap'],
                compact_certificate=compact['certificate_restricted_only'],f0_certificate=f0['certificate_restricted_only'],
                compact_process=compact['process_seconds'],f0_process=f0['process_seconds'],
                compact_work=compact['work'],f0_work=f0['work']))
    csvwrite(OUT/'native_mechanism_results.csv',evidence)
    csvwrite(OUT/'native_mechanism_pairs.csv',pairs)
    csvwrite(OUT/'original_compact_f0_pairs.csv',formulation_pairs)
    csvwrite(OUT/'native_trajectory_checkpoints.csv',trajectories)
    write(OUT/'diagnostic_contract_audit.json',audits)
    print('Charged',len(processes),'completed current native diagnostics',len(evidence))

if __name__=='__main__': main()
