"""Checked thin R109 loop adaptation; authoring only, never a solver launch."""
from round110_common import *

def main():
    source=ROOT/'scripts/round109_reader.py';text=source.read_text(encoding='utf-8')
    replacements={
        'Round109 stdlib':'Round110 stdlib',
        'import round109_decisions as decision':'import round110_decisions as decision',
        'import round109_main06_recovery as numerical':'import round110_evidence as numerical',
        "ROUND='results/unified_exact_round109'":"ROUND='results/unified_exact_round110'",
        "root/'scripts/round109_campaign.py'":"root/'scripts/round110_campaign.py'",
        "root/'scripts/round109_decisions.py'":"root/'scripts/round110_decisions.py'",
        "proof=None if formal and numerical.prior.key(launch)==numerical.KEY else computed.qualify(root,launch,observations,completion,ident)":
            "proof=numerical.qualify_seed(root,launch,observations,completion,ident)",
        "if launch['seed']==1:":"if launch['seed']==1 and proof is not None:",
        'recovery_sidecar=numerical.SIDE.as_posix(),recovery_sidecar_SHA=sha(root/numerical.SIDE)':
            'recovery_sidecar=numerical.side_path(launch).as_posix(),recovery_sidecar_SHA=sha(root/numerical.side_path(launch))',
        "<=72 and sum(r['outer_seconds'] for r in fee_rows)<=100000":"<=96 and sum(r['outer_seconds'] for r in fee_rows)<=110000",
    }
    counts={}
    for before,after in replacements.items():
        counts[before]=text.count(before);assert counts[before]>=1,before;text=text.replace(before,after)
    target=ROOT/'scripts/round110_reader.py';assert not target.exists();target.write_text(text,encoding='utf-8',newline='\n')
    write(OUT/'engineering/reader_adaptation01.json',dict(inherited_source_SHA=sha(source),new_source_SHA=sha(target),replacements=counts,
        core_math_unchanged=True,old_tuple_sidecars_have_no_R110_authority=True,Optimize=0))

if __name__=='__main__':main()
