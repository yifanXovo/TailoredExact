import sys
sys.path.insert(0,'scripts')
from round131_benchmark import *
p=OUT/'manuscript.md';s=p.read_text(encoding='utf-8')
replacements={
'The current direct statements concern the actual MS2 R129 observations and the complete fixed R130 attribution panel, with conditional both-certified time ratios.':'The principal final-version statement concerns the complete fixed Round131 A panel; B and C separately delimit tiny overhead and V35 scope. The earlier MS2 R129 selection observations and fixed R130 attribution panel retain their own roles. Time ratios condition on each explicitly both-certified intersection.',
'Supplement S retains all 32 arms and 48 pairs, all three clocks, the three long endpoints and checkpoint unknowns.':'Supplement S retains the historical R122 32 arms and 48 pairs, all three clocks, the three long endpoints and checkpoint unknowns, and adds the separately labelled 52 Round131 arms. The 26 current comparisons are shown in Tables R131.A-C.',
'The final-version evidence gap is closed within this finite design. Deliver the limited paper statement for substantive review and end this round; no extra ablation or selection cycle follows.':'The resulting certification statement is finite and case-dependent on these known inputs; it does not establish population-wide dominance.'}
for old,new in replacements.items():assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
v=read(OUT/'manuscript_lineage.json');v['current_SHA']=sha(p);v['local_changes']+=['introduction and discussion evidence entry points','explicit historical/current supplement denominators','declarative finite conclusion'];write(OUT/'manuscript_lineage.json',v)
write(OUT/'review/pdf_visual_attempt02.json',dict(status='PROSE_REFERENCE_REPAIR',PDF_SHA=sha(TEMP/'pdf/attempt02/reading.pdf'),pages_actually_inspected=[1,2,3,4,14,41,42,43,44,45,46,47,57,58,59,90,91,92,93],layout='New 52-arm table fixed and all inspected pages legible',issue='Inherited discussion opener still points only to R129/R130; supplement denominator needs explicit historical/current labels; conclusion contains task-direction prose',repair='Local prose/reference corrections only; no numeric, raw, appendix or solver change',failed_PDF_retained=str(TEMP/'pdf/attempt02/reading.pdf')))
