"""Pin the finite historical evidence used by the maintained manuscript."""
from round164_common import *

SOURCES={
 'earlier_seed_research':[f'results/unified_exact_round{n}/final_report.md' for n in (130,131,132,133,134)]+
    ['results/unified_exact_round137/paper_body.md','results/unified_exact_round137/mathematical_analysis.md',
     'results/unified_exact_round137/supplement.md','results/unified_exact_round137/matrix_frozen.json'],
 'seed_reversals':['results/unified_exact_round138/final_report.md','results/unified_exact_round140/final_report.md'],
 'existing_primal_objects':['results/gf_passive_threshold_conflicts_round62/final_report.md',
    'results/unified_exact_round96/final_report.md','scripts/round96_fixed_route.py',
    'results/unified_exact_round97/final_report.md','results/unified_exact_round160/final_report.md'],
 'retained_proof_inventory_and_physics':[f'results/unified_exact_round{n}/final_report.md' for n in (154,155,156,157,158,159,160,161,162)],
 'R163_cohort':['results/unified_exact_round163/final_report.md','results/unified_exact_round163/decision.json',
    'results/unified_exact_round163/input_manifest.json','results/unified_exact_round163/method_freeze.json',
    'results/unified_exact_round163/matrix_frozen.json','results/unified_exact_round163/science_identity.json',
    'results/unified_exact_round163/reports/complete_arms.json','results/unified_exact_round163/reports/comparisons.json',
    'results/unified_exact_round163/structural_synthesis.md'],
 'stable_physical_and_numerical_contract':['docs/paper_s2_release.md','config/gi_tbc_round137.json','config/paper_s2.json',
    'results/unified_exact_round135/model_and_algorithm_appendices.md']}

def run():
    groups={}
    for group,paths in SOURCES.items():
        groups[group]=[]
        for path in paths:
            raw=git('show',BASE+':'+path);assert len(raw)<10000000
            groups[group].append(dict(commit=BASE,path=path,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest(),
                url=f'https://github.com/yifanXovo/TailoredExact/blob/{BASE}/{path}'))
    write(OUT/'historical_source_map.json',dict(UTC=utc(),groups=groups,
        measured_versions_not_pooled=True,old_Optimize=0,old_full_archive_restores=0,
        source='finite fixed metadata and selected original witness members; not a full history replay'))
    print('Pinned finite historical source identities; Optimize=0.')

if __name__=='__main__':run()
