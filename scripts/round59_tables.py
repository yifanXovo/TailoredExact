"""Render small, reviewable Markdown tables from audited CSV data."""
import csv,json
from round59_research import OUT

def read(name):
    p=OUT/name
    return list(csv.DictReader(p.open(encoding='utf-8'))) if p.exists() else []
def f(x,n=5):
    return f'{float(x):.{n}f}' if x not in [None,''] else '—'
def table(head,rows):
    return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)+'\n'

def main():
    full=read('full_instance_results.csv');native=read('native_mechanism_results.csv');fixed=read('fixed_state_results.csv')
    text='# Audited result tables\n\nAll performance caps are 120 seconds end to end. ✓ means an original-problem engineering certificate; its number is process time in seconds. Other entries are the terminal relative gap, **not solve time**. Bounds and absolute gaps are in the linked CSV. Diagnostic ✓ is explicitly restricted-state only.\n\n'
    rows=[]
    panel=json.loads((OUT/'panel.json').read_text())['panel']
    for p in panel:
        line=[p['id'],p['role']]
        for arm in ['P-GRB','K1-H','K1-S','F0-Single-S']:
            r=next((x for x in full if x['id']==p['id'] and x['arm']==arm),None)
            line.append('pending' if not r else ('✓ '+f(r['process_seconds'],2) if r['certificate']=='True' else f(float(r['relative_gap'])*100,2)+'% gap'))
        rows.append(line)
    text+=table(['ID','Frozen role','P-GRB','K1-H','K1-S','Single-S'],rows)
    text+='[Full-instance bounds, absolute gaps and work](full_instance_results.csv); [matched pairs](paired_results.csv).\n\n## Current-model root LP pack-removal ablation\n\nThe removed-pack arm retains connectivity flow and cutoff-derived bounds; it is not original compact.\n\n'
    text+=table(['ID','Model','LP bound','Work','Seconds','Presolved rows','Columns'],[
        [r['id'],r.get('display_arm',r['arm']),f(r['objective']),f(r['work'],4),f(r['process_time_seconds'],3),r['presolved_rows'],r['presolved_columns']]
        for r in fixed if r['stage']=='diagnostic_current_roots'])
    text+='## Native execution and search (restricted states)\n\n'
    text+=table(['ID','Arm','LB','Verified UB','Gap %','Certificate seconds','Work','Nodes','Iterations/node'],[
        [r['id'],r['arm'],f(r['LB']),f(r['UB']),f(float(r['gap'])*100,2),f(r['certificate_seconds'],2),f(r['work'],2),r['nodes'],f(r['iterations_per_node'],1)]
        for r in native if r['stage'] in ['diagnostic_current_cuts','diagnostic_current_focus']])
    text+='## Literal original compact/F0 (restricted states, separate same-build pairs)\n\n'
    text+=table(['ID','Model','LB','Verified UB','Gap %','Certificate seconds','Work'],[
        [r['id'],r['arm'],f(r['LB']),f(r['UB']),f(float(r['gap'])*100,2),f(r['certificate_seconds'],2),f(r['work'],2)]
        for r in native if r['stage']=='diagnostic_current_original'])
    text+='## Frozen incumbent startup-exhaustion diagnostics (restricted states)\n\n'
    text+=table(['ID','State','Model','LB','Verified UB','Gap %','Certificate seconds','Work'],[
        [r['id'],r['stage'].removeprefix('diagnostic_current_'),'F0-minus-pack_connectivity_retained' if r['arm']=='Compact' else r['arm'],f(r['LB']),f(r['UB']),f(float(r['gap'])*100,2),f(r['certificate_seconds'],2),f(r['work'],2)]
        for r in native if r['stage'] in ['diagnostic_current_hga_state','diagnostic_current_startup_state']])
    text+='## Observation cost\n\n'
    text+=table(['ID','Samples','Sampling seconds','Eligible callback checks','Read failures'],[
        [r['id'],r.get('monitor_successful_samples',''),f(r.get('monitor_sampling_seconds'),6),r.get('monitor_eligible_callback_checks',''),r.get('monitor_sampling_failures','')]
        for r in native if r['arm']=='Monitor'])
    text+='The unmonitored arm retains existing native progress telemetry. The added monitor never submits cuts, starts or hints. One timing pair does not estimate a statistically stable overhead distribution.\n'
    (OUT/'result_tables.md').write_text(text,encoding='utf-8')

if __name__=='__main__': main()
