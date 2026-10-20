"""The three frozen formal stages, serially, after committed P selection."""
from round127_common import *
from round127_pipeline import formal
if __name__=='__main__':
    commit=git('rev-parse','HEAD').decode().strip()
    assert git('show',commit+':results/unified_exact_round127/tuning_selection.json')==(OUT/'tuning_selection.json').read_bytes()
    assert read(OUT/'tuning_selection.json')['status']=='SELECTED'
    for stage in ['main','tiny','core']:
        print(json.dumps(dict(stage=stage,status='START_OR_READONLY_RESUME',budget=budget())),flush=True)
        formal(stage)
        (OUT/'RESUME.md').write_text(f'Round127 v3 {stage} stage sealed.\n\nAll original positions retained; existing sealed arms are never rerun.\nCheck native processes and fees before the next stage or analysis.\n',encoding='utf-8')
        print(json.dumps(dict(stage=stage,status='SEALED',budget=budget())),flush=True)
    print('ALL_UNBLOCKED_FORMAL_STAGES_SEALED; MD remains blocked; analysis/review/documentation pending',flush=True)
