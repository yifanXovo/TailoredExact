"""Recover only hash-bound R140 domains; no solver loading or optimization."""
import zipfile, shutil
import round108_reader as core
from round143_common import *
from round143_math import specification,exact_fixtures

def main():
    tick=time.perf_counter(); assert sha(CARRIER)==CARRIER_SHA
    OUT.mkdir(parents=True,exist_ok=True)
    goal=Path('C:/Users/Administrator/Downloads/TailoredExact_Round143_Complete_Goal.md')
    if goal.exists():
        target=OUT/'goal.md'
        if target.exists(): assert sha(target)==sha(goal)
        else: shutil.copyfile(goal,target)
    prefix='results/unified_exact_round140/inherited/roots/'
    members=[]
    with zipfile.ZipFile(CARRIER) as z:
        for name in z.namelist():
            if not name.startswith(prefix): continue
            rel=Path(name[len(prefix):]); assert not rel.is_absolute() and '..' not in rel.parts
            data=z.read(name); target=OUT/'inherited/roots'/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists(): assert target.read_bytes()==data
            else: target.write_bytes(data)
            members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    domains={}
    for role in ['K-35-U','R-X20-S-T1','K-20-S','R-X35-S-T2']:
        folder=OUT/'inherited/roots'/role; scope=read(folder/'scope.json')
        model=folder/'inherited/original.lp'; parsed=core.lp_model(model)
        assert sha(model)==scope['saved_LP_SHA256']
        spec=specification(parsed,scope); assert spec['applicable']
        spec.update(role=role,source_SHA=sha(model),scope_SHA=sha(folder/'scope.json'))
        write(OUT/'domains'/role/'RN.json',spec); domains[role]=spec
    write(OUT/'math/fixtures.json',exact_fixtures())
    write(OUT/'inherited_dependencies.json',dict(carrier=str(CARRIER.relative_to(ROOT)),SHA256=CARRIER_SHA,
        members=members,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,
        provided_offline_zip_found=False,
        offline_zip_policy='Reconstruct from original carrier without rerunning saved-point optimization'))
    primary=[dict(position=i,role=r,variant='base',cap_seconds=120) for i,r in enumerate(['K-35-U','R-X20-S-T1'],1)]
    write(OUT/'LP_plan.json',dict(primary=primary,followup_policy='After primary signal: 1-2 matched stock/TC+stock diagnostics; no automatic grid',
        Seed=0,Threads=1,serial=True,affinity_mask=4,total_experiment_limit_seconds=28800))
    write(OUT/'start_receipt.json',dict(UTC=utc(),user_timezone='Asia/Shanghai',task_date='2026-11-01',
        base=BASE,actual_HEAD=git('rev-parse','HEAD').decode().strip(),
        branch=git('branch','--show-current').decode().strip(),main=git('rev-parse','origin/main').decode().strip(),
        temporary_PR_base='codex/round142-conditional-count-products',R142_PR=204,R142_open_Draft=True,
        tracked_dirty_before='',applicable_AGENTS=[],policy='WORKSPACE_POLICY.md',
        protected_original='E:/codes/ExactEBRP',new_assets_root=str(WORK),
        no_active_solver_at_start=True,stable_profile_SHA=sha(ROOT/'config/gi_tbc_round137.json')))
    print(json.dumps({r:{k:s[k] for k in ['S_L_exact','S_U_exact','L_t','U_t']} for r,s in domains.items()}))

if __name__=='__main__':main()
