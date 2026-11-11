"""Predeclared two matched pairs; C pays fresh source inside its 900s clock."""
from round162_common import *
from round162_experiment import call

def freeze():
    audit=read(OUT/'reports/N-B35-S_C_LP_v1_projection_audit.json')
    assert audit['PASS'] and audit['retained_increment']>1e-7
    write(OUT/'development_plan.json',dict(UTC=utc(),positive_roles=['N-B35-S'],
        branch='at least one primary positive',roles=['R-X35-S-T2','N-B35-S'],
        order=[dict(role=r,form=f,label=r+'_'+f+'_MIP_v1') for r in ('R-X35-S-T2','N-B35-S') for f in ('S','C')],
        cap=900,NodeLimit=4096,Seed=0,Threads=1,MIPFocus=0,one_deadline=True,
        C_source='fresh C++ full Q once; remaining global deadline, no RN source; finite-box projected one row',
        source_lower_only_diagnostic=True,parent='own-H/R83 offline development source',
        completed_H_in_this_study=False,formal_GI=False,source_cost_inside_cap=True,
        PE_SHA256=read(OUT/'candidate_manifest.json')['research_PE_SHA'],
        stop_rule='After both pairs, stop before complete panel if positive source has no useful paid U/L progress or cost tradeoff; otherwise freeze one full candidate',
        directions_or_revisions=0,source_per_arm=1,automatic_additional_mechanisms=False))

def panel():
    plan=read(OUT/'development_plan.json');assert sha(pe())==plan['PE_SHA256']
    for arm in plan['order']:
        label=arm['label']
        if (OUT/'fees'/label/'receipt.json').exists():
            assert read(OUT/'fees'/label/'receipt.json')['exit_code']==0
            continue
        call(arm['role'],arm['form'],'MIP',label,cap=900,saved='paid' if arm['form']=='C' else '-',nodes=4096)

if __name__=='__main__':globals()[sys.argv[1]]()
