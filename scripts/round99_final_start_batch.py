"""One registered finite 22-scope qualification; reads models, never optimizes."""
from round99_common import *
from round99_idle import ensure_idle

MODES = {'ENS-C':'off','R1':'aggregate','Q-I':'q-integer',
         'M-B':'m-binary','R2':'projected','M-BL':'m-binary-linked'}

def main():
    ensure_idle()
    plan_path=OUT/'final_start_audit_plan.json';plan=read(plan_path)
    assert plan['finite_model_scopes']==22 and plan['optimizer_calls']==0
    recovery=[json.loads(s) for s in (OUT/'confirmation_recovery01/summary.jsonl').read_text().splitlines()]
    assert len(recovery)==3 and all(r['audit_passed'] for r in recovery)
    scopes=[]
    for group in plan['scopes']:
        campaign=group['campaign'];identity=read(OUT/campaign/'identity.json')
        completed={r['number']:r for r in map(json.loads,(OUT/campaign/'summary.jsonl').read_text().splitlines())}
        for number in group['numbers']:
            launch=identity['launches'][number-1]
            assert launch['number']==number and launch['arm'] in MODES
            dest=Path(launch['destination']);assert dest.is_dir()
            if campaign=='confirmation01' and number==7:
                assert read(dest/'interrupted_audit.json')['passed']
                assert read(dest/'interruption_receipt.json')['original_completion_missing']
            else:assert completed[number]['audit_passed']
            assert list((dest/'external/native_logs').glob('*.round68.start.json'))
            assert list((dest/'external/models').glob('*.lp'))
            label=f'final_start_{campaign}_{number:02d}'
            assert not (OUT/'qualification'/(label+'.json')).exists()
            scopes.append((campaign,number,launch,label))
    assert len(scopes)==22
    # Preload the production DLL BEFORE any gurobipy-bearing reader import.
    from round99_gurobi_runtime import binding
    runtime=binding()
    assert runtime['sha256']=='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
    from round99_start_audit import run
    records=[]
    for campaign,number,launch,label in scopes:
        starts=run(launch['destination'],label,MODES[launch['arm']])
        records.append(dict(campaign=campaign,number=number,arm=launch['arm'],
                            submitted_starts=len(starts),output=label+'.json',
                            output_sha256=sha(OUT/'qualification'/(label+'.json'))))
    assert binding()==runtime
    write(OUT/'qualification/final_actual_start01/summary.json',
          dict(passed=True,finite_model_scopes=22,optimizer_calls=0,
               submitted_starts=sum(r['submitted_starts'] for r in records),
               engine=runtime,plan_sha256=sha(plan_path),scopes=records,
               qualification_scope='actual submitted Starts, all rows/types/physical p/d; no search replay',
               script_sha256=sha(__file__),reader_sha256=sha(ROOT/'scripts/round99_start_audit.py')))
    print('Finite scopes=22; actual Optimize=0; production DLL only',flush=True)

if __name__=='__main__':main()
