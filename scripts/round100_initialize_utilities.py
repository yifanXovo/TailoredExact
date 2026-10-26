"""Copy the audited R99 utilities with narrow Round100 identities; no solver."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def create(name,text):
    with (ROOT/'scripts'/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def main():
    common=(ROOT/'scripts/round99_common.py').read_text().replace('unified_exact_round99','unified_exact_round100').replace('round99-discrete-v2','round100-quantity-v1')
    create('round100_common.py',common)
    build=(ROOT/'scripts/round99_build.py').read_text().replace('round99_common','round100_common').replace('round96_external as old','round100_idle as old').replace('Round99DiscreteTests','Round100QuantityTests').replace('Round99ModelExport','Round100ModelExport')
    create('round100_build.py',build)
    c=(ROOT/'scripts/round99_campaign.py').read_text().replace('round99_common','round100_common')
    c=c.replace('import round96_external as ext','import round96_external as ext\nfrom round100_idle import ensure_idle')
    c=c.replace('ext.ensure_idle()','ensure_idle()')
    c=c.replace("'round99_campaign.py','round99_common.py'","'round100_campaign.py','round100_common.py','round100_idle.py'")
    c=c.replace("'M-BL':'research-round99-ensc-discrete-structure-m-binary-linked'","'M-BL':'research-round99-ensc-discrete-structure-m-binary-linked',\n            'ENS-Q':'research-round100-ensc-continuous-quantities'")
    c=c.replace("['P-GRB','ENS-C','R1','R2','R3','Q-I','M-B','M-BL']","['P-GRB','ENS-C','ENS-Q','M-B']")
    c=c.replace("assert len(roles)==3 and protocol['phase'] in ['frozen independent confirmation','full linked development']","assert 1<=len(roles)<=3 and protocol['phase'] in ['minimal quantity ablation','certification extension','design-isolated confirmation']")
    c=c.replace('planned_children=3','planned_children=len(roles)').replace('actual_children=3','actual_children=len(roles)')
    needle="            launches.append(dict(number=number,id=p['id']"
    assert needle in c
    c=c.replace(needle,"            if arm=='ENS-Q':command+=['--round100-continuous-quantities']\n"+needle)
    create('round100_campaign.py',c)
    create('round100_run_batch.py',(ROOT/'scripts/round99_run_batch.py').read_text().replace('round99_campaign','round100_campaign'))
    create('round100_results.py',(ROOT/'scripts/round99_results.py').read_text().replace('round99_common','round100_common').replace('round99_results.py','round100_results.py'))
    create('round100_gurobi_runtime.py',(ROOT/'scripts/round99_gurobi_runtime.py').read_text())
    print('finite utilities created, Optimize=0')
if __name__=='__main__':main()
