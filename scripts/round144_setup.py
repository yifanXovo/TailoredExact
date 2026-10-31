"""Finite startup inventory; no optimizer or commercial engine import."""
from round144_common import *
def main():
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('rev-parse','origin/main').decode().strip()=='b2b940c1e517a72e226ec60fc49ff19651737632'
    write(OUT/'start_receipt.json',dict(UTC=utc(),task_date='2026-11-01',timezone='Asia/Shanghai',
        actual_start_HEAD=BASE,branch='codex/round144-rn-projection',temporary_PR_base='codex/round143-reciprocal-normalization',
        R143_PR=205,R143_open_Draft=True,actual_main=git('rev-parse','origin/main').decode().strip(),
        tracked_dirty_before='',applicable_AGENTS=[],policy='WORKSPACE_POLICY.md',
        protected_original='E:/codes/ExactEBRP',new_assets_root=str(WORK),no_active_solver_at_start=True,
        stable_profile_SHA=sha(ROOT/'config/gi_tbc_round137.json'),stable_entry_SHA=sha(ROOT/'scripts/paper_s2.py'),
        inherited_RN_profile_SHA=sha(ROOT/'config/gi_tbc_rn_round143.json'),inherited_RN_entry_SHA=sha(ROOT/'scripts/paper_s2_rn.py'),
        offline_attachment_found=False,missing_attachment_policy='Finite reconstruction from R143 saved data; no old Optimize',
        experiment_limit_seconds=28800,Seed=0,Threads=1,H_seed=20260626,serial=True,Optimize=0,Native_load=0))
    write(OUT/'LP_plan.json',dict(primary=['K-35-U','R-X20-S-T1'],LP_Optimize_per_role=2,
        source='Matched BASE + actual production RN rows and finite caps',compact='Same BASE + one full-block projected PC; zero RN columns',
        followup='At most 1-2 useful domains after observed primary results; no automatic grid',
        qualification='Fraction oracle, directed C++ writer, actual Native readback, physical Start and scope, one short complete qualifier',
        full_admission='Independent non-implementer review and useful matched-LP retention first'))
    print('Round144 startup inventory frozen; no Optimize')
if __name__=='__main__':main()
