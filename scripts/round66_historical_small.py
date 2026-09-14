"""Attribute existing R58 small-instance losses; launches no optimizer."""
import csv,json
from pathlib import Path
import round66_research as run

def main():
    source=run.ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/screen_results_3600.csv'
    records=list(csv.DictReader(source.open()))
    panel=list(csv.DictReader((run.ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/round58_complete_panel.csv').open()))
    result=[]
    for a in records:
        if a['method']!='k1_am_sf' or int(a['V'])>12:continue
        b=next(x for x in records if x['scenario_id']==a['scenario_id'] and x['method']=='pgrb')
        ta,tb=map(float,[a['actual_wall_time_seconds'],b['actual_wall_time_seconds']])
        if ta<=tb+2:continue
        p=Path('E:/codes/ExactEBRP')/a['result_path']
        if not p.exists():raise RuntimeError(f'historical raw result unavailable: {p}')
        s=json.loads(p.read_text());h=s['hga_wall_time_seconds']
        identity=next(x for x in panel if x['scenario_id']==a['scenario_id'])
        result.append(dict(scenario=a['scenario_id'],V=a['V'],M=a['M'],Q=a['Q'],T=a['T'],
            input_sha256=identity['instance_file_sha256'],common_cap=3600,
            K1_certificate=a['strict_certificate'],P_certificate=b['strict_certificate'],
            K1_wall=ta,P_wall=tb,K1_HGA=h,K1_post_HGA=ta-h,post_HGA_minus_P=ta-h-tb,
            K1_UB=a['verified_upper_bound'],K1_LB=a['valid_lower_bound'],
            P_UB=b['verified_upper_bound'],P_LB=b['valid_lower_bound'],
            zero_objective=float(a['objective'])==0,source_result=str(p),source_result_sha256=run.sha(p),
            comparison_scope='historical same-stage pair; post-HGA is attribution only, not official time'))
    with (run.OUT/'historical_small_attribution.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    print(len(result),'historical small losses attributed; no optimizer launched')
if __name__=='__main__':main()
