"""Offline actual startup/neighborhood/Start audit of the frozen E8/D6 runs."""
import csv
import json
import re
import time
from pathlib import Path
from round78_qualify import ROOT,sha,write
import round73_native_evidence as evidence
from round68_start_audit import actual_vector_check,mapping
from round80_analyze import campaign_summary

OUT=ROOT/'results/unified_exact_round80/campaign'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def main():
    started=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    assert not (OUT/'mechanism_audit.json').exists(),'Do not replace a completed mechanism audit'
    assert read(OUT/'audit.json')['all_checks_passed']
    frozen=read(OUT/'identity.json');summary=campaign_summary()
    mapping.run.ROOT=ROOT;mapping.audit.physical_module.ROOT=ROOT
    evidence.physical_module.ROOT=ROOT
    arms=[];starts=[];traces={};controls=0
    for launch,done in zip(frozen['launches'],summary['records']):
        identity=launch['panel']['id'];arm=launch['arm'];folder=ROOT/launch['destination'];p=launch['panel']
        events=read(folder/'observations.json')
        calls=[r['payload'] for r in events if r['payload']['kind']=='call']
        initial=[r for r in events if r['payload']['kind']=='witness' and r['payload']['call']==0]
        phase=rows(folder/'phases.csv')
        row=dict(id=identity,arm=arm,wall_seconds=done['wall_seconds'],endpoint=done['audit']['endpoint'],
            phase_events=[r for r in phase if r['event'] in ['hga_start','decoded_descent_complete',
                'exact_phase_start','hga_complete','hga_generation_loop_complete','hga_global_deadline']],
            call_scopes=[dict(call=c['call'],leaf=c['leaf'],lower_g=c['lower_g'],upper_g=c['upper_g'],
                cutoff=c['cutoff'],model_sha256=c['model_sha256'],native_preconditions=c['native_preconditions']) for c in calls])
        if done['stop_reason']=='normal_return':
            row['endpoint_physical']=evidence.physical_module.physical(p,read(folder/'result.json'))
        else:
            physical_events=[r for r in events if r['payload']['kind']=='witness']
            best=min(physical_events,key=lambda r:r['payload']['objective'])
            row['endpoint_physical']=evidence.physical_module.physical(p,best['payload'])
        if initial:
            r=initial[0];row['startup']=dict(evidence.physical_module.physical(p,r['payload']),
                available_seconds=r['effective_available_seconds'],sequence=r['sequence'])
        metas=list(folder.glob('external/**/*.round68.start.json'))
        if arm!='BDS-C':
            assert not metas;controls+=1
            if arm=='P-GRB':
                assert 'Loaded user MIP start' not in (folder/'native.log').read_text(encoding='utf-8')
        else:
            mip_calls=[c for c in calls if c['native_preconditions']]
            assert len(metas)==len(mip_calls),'Missing or extra actual Start decision'
            for c in mip_calls:
                log=Path(c['native_log_path']);meta=Path(str(log)+'.round68.start.json');data=read(meta)
                model=Path(c['model_path']);assert sha(model)==data['model_sha256']==c['model_sha256']
                assert data['leaf']==c['leaf']
                witness_path=folder/'external'/(data['source']+'_witness.json');witness=read(witness_path)
                check=mapping.check_model(p,witness,model)
                eligible=check['compatible_interval'] and check.get('compatible_cutoff',False)
                assert data['submitted']==eligible
                accepted=bool(re.search(r'Loaded user MIP start with objective',log.read_text(encoding='utf-8')))
                vector=Path(str(log)+'.round68.start.values.csv');actual={}
                if eligible:
                    assert check['all_bounds_types_rows_valid']
                    assert all(data[k] for k in ['mapping_complete','rows_valid','objective_valid','readback_valid'])
                    actual=actual_vector_check(p,witness,model,vector)
                    assert actual['actual_rows']==data['checked_rows']
                    assert abs(data['objective']-evidence.physical_module.physical(p,witness)['F'])<1e-7
                    if done['stop_reason']=='normal_return':
                        assert (data['status']=='accepted_by_native_log')==accepted
                else:
                    assert data['status'].startswith('ineligible:') and not vector.exists()
                starts.append(dict(id=identity,arm=arm,call=c['call'],eligible=eligible,native_log_accepted=accepted,
                    metadata=str(meta.relative_to(ROOT)),metadata_sha256=sha(meta),
                    witness_sha256=sha(witness_path),independent_actual_vector=actual,**data))
            row['balanced_physical_audit']=done['audit']['balanced']
            row['outer_handoff']=done['audit']['outer_handoff']
            trace=rows(folder/'hga.csv.descent.csv');traces[identity]=trace
            count=25
            assert [int(r['seed']) for r in trace if r['exhausted']=='1']==list(range(1,count+1))
            for r in trace:
                assert r['interrupted']=='0'
                if r['exhausted']=='1':
                    assert r['decoded_checks']==r['neighbors'] and r['cross_route_checks']==r['cross_route_neighbors']
            row['descent']=dict(completed_seeds=count,passes=len(trace),
                decoded_checks=sum(int(r['decoded_checks']) for r in trace),
                cross_route_checks=sum(int(r['cross_route_checks']) for r in trace),
                accepted_cross_route=sum(int(r['accepted_cross_route']) for r in trace),
                extra_seed_checks=sum(int(r['decoded_checks']) for r in trace if r['seed']=='25'),
                extra_seed_moves=sum(int(r['accepted']) for r in trace if r['seed']=='25'),
                extra_seed_cross_route_neighbors=sum(int(r['cross_route_neighbors']) for r in trace if r['seed']=='25'),
                extra_seed_cross_route_checks=sum(int(r['cross_route_checks']) for r in trace if r['seed']=='25'),
                extra_seed_cross_route_moves=sum(int(r['accepted_cross_route']) for r in trace if r['seed']=='25'))
        native_costs=[]
        for c in calls:
            text=Path(c['native_log_path']).read_text(encoding='utf-8',errors='replace')
            size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',text)
            assert size,'Native model dimension line missing'
            record=dict(call=c['call'],rows=int(size[1]),columns=int(size[2]),nonzeros=int(size[3]),
                gamma=[c['lower_g'],c['upper_g']],cutoff=c['cutoff'],
                root_relaxation_lines=[line for line in text.splitlines() if line.startswith('Root relaxation:')],
                scope='Rounded per-call native-log attribution; not a replacement for complete physical/global endpoint or whole-process cost')
            explored=re.search(r'Explored (\d+) nodes \((\d+) simplex iterations\) in ([0-9.]+) seconds \(([0-9.]+) work units\)',text)
            if explored:record.update(nodes=int(explored[1]),simplex_iterations=int(explored[2]),native_seconds=float(explored[3]),native_work=float(explored[4]))
            lp=re.search(r'Solved in (\d+) iterations and ([0-9.]+) seconds',text)
            if lp and not explored:record.update(lp_iterations=int(lp[1]),native_seconds=float(lp[2]))
            native_costs.append(record)
        row['native_cost_attribution']=native_costs
        arms.append(row)
    logical=lambda r:{k:v for k,v in r.items() if k!='elapsed_seconds'}
    prior_checks=0
    for identity in ['D6']:
        previous=rows(ROOT/'results/unified_exact_round78/startup/local_raw'/identity/'BDS-C/hga.csv.descent.csv')
        assert list(map(logical,traces[identity]))==list(map(logical,previous))
        prior_checks+=1
    assert len(traces)==2 and controls==4
    output=dict(all_checks_passed=True,arms=arms,start_decisions=starts,controls_checked=controls,
        all25_paths_match_available_prior_startup_screen=True,prior_startup_pairs_checked=prior_checks,actual_Start_decisions=len(starts),
        eligible_Starts=sum(r['eligible'] for r in starts),native_accepted_Starts=sum(r['native_log_accepted'] for r in starts),
        optimizer_calls=0,wall_seconds=time.perf_counter()-started,script_sha256=sha(__file__),
        mapping_sha256=sha(mapping.__file__),
        scope='Independent retained submitted/readback vectors and native acceptance logs. No causal speed attribution from acceptance alone; pending interrupted observer flags are not finalized.')
    write(OUT/'mechanism_audit.json',output)
    print(json.dumps({k:v for k,v in output.items() if k not in ['arms','start_decisions']},indent=2))


if __name__=='__main__':main()
