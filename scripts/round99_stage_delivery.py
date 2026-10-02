"""Explicit Round99-only staging manifest; never stages unrelated paths."""
from round99_common import *

def main():
    names=['candidate_freeze.json','confirmation_generation_recipe.json','confirmation_protocol01.json',
        'development_inputs.json','environment.json','failures.md','final_report.md','final_start_audit_plan.json',
        'history_increment.md','inner_protocol01.json','known_unknown.md','linked_plan.md','linked_protocol01.json',
        'linked_qualification_result.json','local_artifact_index.json','long_protocol01.json','mathematical_algorithm.md',
        'model_change_table.md','repeat_plan.md','repeat_protocol01.json','research_plan.md','reproduce.md','RESUME.md','root_final_review.md',
        'stage1_result.md','user_edit_preservation.json']
    files=set((ROOT/'scripts').glob('round99*.py'))|set((ROOT/'reference/round99_confirmation').glob('*.txt'))
    files.update(OUT/name for name in names)
    files.add(OUT/'frozen/v1/index.json')
    for directory in ['complete_results_final','evidence','pure_qualification']:
        files.update(p for p in (OUT/directory).rglob('*') if p.is_file() and p.name!='trajectories.csv')
    files.update((OUT/'qualification').glob('factorial_start_*.json'))
    files.update(p for p in (OUT/'inner_results02').rglob('*') if p.is_file() and p.name!='native.log')
    assert all(p.is_file() and p.resolve().is_relative_to(ROOT) for p in files)
    assert all(sha(ROOT/p)==h for p,h in read(OUT/'user_edit_preservation.json').items())
    relative=sorted(p.relative_to(ROOT).as_posix() for p in files)
    assert not any(p in read(OUT/'user_edit_preservation.json') for p in relative)
    import sys
    path=OUT/(sys.argv[1] if len(sys.argv)>1 else 'delivery_paths.txt')
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(relative)+'\n')
    print(json.dumps(dict(explicit_paths=len(relative),bytes=sum(p.stat().st_size for p in files),
        manifest=path.relative_to(ROOT).as_posix(),unrelated_user_files_excluded=True)))

if __name__=='__main__':main()
