"""Write the decision-complete research report from qualified frozen facts."""
from round143_common import *
from round143_analyze import require_idle

SHORT={'K-35-U':'K35','R-X20-S-T1':'RX20-T1','K-20-S':'K20','R-B35-S-T2':'RB35-T2','K-15-S':'K15','R-X35-S-T2':'RX35-T2'}
def fmt(v):
    if v is None:return 'open'
    if isinstance(v,float):return format(v,'.3g' if 0<abs(v)<1e-6 else '.9g')
    return str(v)
def table(head,rows):
    return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+''.join('| '+' | '.join(fmt(x) for x in r)+' |\n' for r in rows)+'\n'

def main():
    require_idle();decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    lp=read(OUT/'reports/LP.json')['positions'];full=read(OUT/'reports/full.json');cost=read(OUT/'cost_report.json');m=read(OUT/'candidate_manifest.json')
    text='# Round143: reciprocal-normalized Gini on stable GI-TBC\n\n'
    text+=decision['summary']+'\n\n'
    text+='RN supplements the old shared-g products with a common reciprocal t, normalized inventory and normalized pair differences. It keeps the original integer route/inventory structure and original penalty. Its integer extension and continuous inclusion are exact on a proved positive-denominator scope. The separate research switch defaults off. Stable R137 remains available.\n\n'
    text+='## Matched continuous objectives\n\n'
    text+='All four new LPs are numerical optima under unchanged 1e-6 feasibility/optimality qualification, explicit Gurobi Seed 0, Threads 1 and affinity mask 4, run serially. The original complete objective, cutoff, support, g interval and old matrix are retained. BASE gains include physical inventory information used for t bounds; TC+stock controls still show information beyond that older resource/count combination.\n\n'
    text+=table(['Role','Old expression','Old L','RN L','Gain'],[[SHORT[r['role']],r['variant'],r['old_L'],r['L'],r['difference']] for r in lp])
    text+=table(['Role / expression','Old g','RN g','Old weighted P','RN weighted P'],[[SHORT[r['role']]+'/'+r['variant'],r['old_g'],r['g'],r['old_weighted_penalty'],r['weighted_penalty']] for r in lp])
    text+=table(['Role / expression','Added rows','Added columns','Added nonzeros','Build / solve s'],[[SHORT[r['role']]+'/'+r['variant'],r['added_rows'],r['added_columns'],r['added_nonzeros'],fmt(r['build_seconds'])+' / '+fmt(r['optimize_wall_seconds'])] for r in lp])
    text+='Actual denominator bounds, reciprocal endpoints, complete row/column/nonzero counts, Runtime/Work, all quality measures and actual source/solution hashes are in reports/LP.json and LP.csv. These reoptimized full-objective gains are separate from saved-point exclusions. Four diagnostic Optimize calls were sufficient; no RN x TC2 x CP grid was opened.\n\n'
    text+='## Complete same-PE methods\n\n'
    text+='Each method pays for its own H (separate fixed seed 20260626), root/lookahead, online validation and complete Native proof search. The stable carrier is M-B/VD-P, pair-only, AM=.08, depth 8, minimum width 1e-4, AP off; stock, TC/TC2, count disjunction and CP are off. Each entered role receives its original full cap. Diagnostic/historical solutions or bounds are never injected.\n\n'
    arms=full['new_arms']
    text+=table(['Role','Method','U','Supported L','Relative gap','T cert s'],[[SHORT[r['role']],r['method'],r['U'],r['L'],r['relative_gap'],r['T_cert']] for r in arms])
    text+=table(['Role / method','Produce s','Verify s','Total s','Splits'],[[SHORT[r['role']]+'/'+r['method'],r['T_produce'],r['T_verify'],r['T_total'],r['actual_split_count']] for r in arms])
    text+=table(['Same-PE role','RN - off U','RN - off L','Produce delta s','Total delta s'],[[SHORT[r['role']],r['delta_U'],r['delta_L'],r['delta_T_produce'],r['delta_T_total']] for r in full['pairs']])
    text+=decision['complete_discussion']+'\n\n'
    text+='Open T_cert is null, never the cap. Native returned ObjVal/ObjBoundC and externally merged supported L are separately retained. Root LP, AM decisions, outer splits, terminal nodes/Work and full Native logs explain observed outcomes without equating LP strength with search speed. One Seed does not identify a runtime distribution or attribute every difference directly to a new row.\n\n'
    text+=decision['attribution_discussion']+'\n\n'
    text+='## Qualifications, boundaries and cost\n\n'
    text+='The three-station exact subblock separates 1/3 from 5/12; the four-station fixed-denominator example allows RN g=0 while retained TC+stock requires 1/4. RN is complementary and is not claimed to dominate the old count information or provide the complete integer objective hull. The original R140 carrier supplied twelve fixed-point checks with zero Optimize: six exclusions and six same-old-point extensions. The separately named offline ZIP was absent; reconstructed rank/eta certificates have their own identities and sometimes stronger bounds. They are not retroactively labeled as the missing old certificate bytes.\n\n'
    text+='Production qualification includes exact dyadic full-scope bounds with directed conversion before reciprocal, actual c_i, zero-lower-bound omission, fixed-S and positive-S fixtures, nonminimal epigraph extensions, complete old/new Start values, preservation of the physical-G Start-domain rule, and actual Native reads of all new rows/coefficients/column types/bounds. K35 RN-off equals the inherited complete BASE matrix. All four affected units were recompiled; hybrid object/archive lineage and actual PE/DLL hashes are saved. Two new diagnostic failures occurred before Optimize, were repaired under new labels, and remain charged. Small offline constructor/search failures are separately recorded.\n\n'
    seconds=cost['charged_new_experiment_seconds']
    text+=f'The conservative new experimental charge is **{seconds:.6f} seconds ({seconds/3600:.6f} hours)** of the 28800-second ceiling. This is the complete outer including qualification, failures and mandatory postverification, charged once. Nested H/LP/MIP/Work are nonadditive details. Build time is separately {cost["build_seconds_separate"]:.6f} seconds; exact offline reconstruction, writing, independent review, PDF and public I/O are separate. Interactive editing/review does not receive invented timing precision.\n\n'
    text+=decision['decision_paragraph']+'\n\n'+decision['conditional_work_discussion']+'\n\n'
    text+='## Reproduction and delivery identity\n\n'
    text+=f'Actual production source is `{m["source_commit"]}`; PE SHA256 is `{m["production_PE_SHA"]}`. DLL SHA256 is `{m["DLL_SHA"]}`. The carrier is stable R137 plus uniform RN, not R138-R142 mechanism stacking. Source/PE/helper/input/parameter matrices and actual returned calls are bound separately from later report metadata. The research entry is `scripts/paper_s2_rn.py`, profile `config/gi_tbc_rn_round143.json`, with `--rn on|off`; it expands only unless `--run` is explicit. `RESUME.md` describes safe continuation and the no-repeat rule.\n\n'
    text+='The mathematical/history/literature note and independent reviews separate four evidence levels: standard construction and integer equivalence, strict subblock/saved-point relations, reoptimized LP gains, and complete algorithm performance. Existing R88/R133/R138/R140 results and Charnes-Cooper, Yue et al. and Chen-Hooker antecedents retain their identities. No new general fractional-programming principle or higher-journal claim follows.\n\n'
    text+='The formal stable GI-TBC manuscript is retained. The increment and full reports retain all entered favorable/adverse positions; missing configurations are not inferred. Fixed-science carriers, anonymous public byte/member recovery and bounded current-round cleanup have separate receipts. All new assets stay under ExactEBRP-work, protecting the original user tree and old rounds. No merge or force push is authorized.\n'
    (OUT/'final_report.md').write_text(text,encoding='utf-8',newline='\n')
    (OUT/'LP_report.md').write_text(('# Round143 matched LP evidence\n\n'+text.split('## Matched continuous objectives\n\n',1)[1].split('## Complete same-PE methods',1)[0]).rstrip()+'\n',encoding='utf-8',newline='\n')
    print('Decision-complete Round143 report assembled')

if __name__=='__main__':main()
