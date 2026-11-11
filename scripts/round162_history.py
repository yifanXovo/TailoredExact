"""Print bounded conclusion excerpts; never execute or restore old producers."""
from round162_common import *

GROUPS=[
 ['results/gf_k1_am_sf_inventory_route_round54/final_report.md','results/gf_cumulative_time_resource_round63/final_report.md',
  'results/gf_shared_load_time_round64/final_report.md','results/unified_exact_round66/final_report.md'],
 ['results/unified_exact_round88/ot_closure_decision.md','results/unified_exact_round103/final_report.md',
  'results/unified_exact_round104/final_report.md','results/unified_exact_round105/final_report.md',
  'results/unified_exact_round106/final_report.md','results/unified_exact_round107/final_report.md'],
 ['results/unified_exact_round138/mathematical_analysis.md','results/unified_exact_round138/final_report.md',
  'results/unified_exact_round139/final_report.md','results/unified_exact_round143/mathematical_analysis.md',
  'results/unified_exact_round144/final_report.md','results/unified_exact_round145/final_report.md'],
 ['results/unified_exact_round132/final_report.md','results/unified_exact_round133/final_report.md',
  'results/unified_exact_round153/final_report.md','results/unified_exact_round156/final_report.md']]

def excerpts(group):
    receipt=[]
    for path in GROUPS[int(group)]:
        raw=git('show',BASE+':'+path);text=raw.decode('utf-8-sig');lines=text.splitlines()
        print('\n'+path+'\n'+'\n'.join(lines[:24])+'\n'+'\n'.join(lines[-12:]),flush=True)
        receipt.append(dict(path=path,commit=BASE,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
            inspected='first 24 and last 12 lines; actual conclusion/interface readback'))
    write(OUT/'infra'/f'history_excerpt_{group}.json',receipt)

if __name__=='__main__':excerpts(sys.argv[1])
