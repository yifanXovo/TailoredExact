import sys
sys.path.insert(0,'scripts')
from round131_documents import *
o=read(OUT/'observations.json')
full=table(['Layer / problem','Seed / repeat','Method','Certified','T_cert','T_produce','T_verify','T_total','U','L','signed U-L'],
    [[a['layer']+' / '+a['id'],f"{a['seed']} / {a['repeat']}",a['method'],a['certificate'],fmt(a['T_cert']),fmt(a['T_produce']),fmt(a['T_verify']),fmt(a['T_total']),f"{a['U']:.6g}",f"{a['L']:.6g}",f"{a['signed_gap']:.3g}"] for a in o['arms']])
caption='**Table R131.S. All 52 formal arms and three clocks.** Layer, Seed and repeat preserve denominators. Open certification time is null. Display: clocks to 0.001 seconds, U/L to six significant digits and signed gap to three; CSV/JSON retain full precision.\n\n'
for name in ['tables/complete_results.md','tables/historical_display.md']:
    p=OUT/name;s=p.read_text(encoding='utf-8');start=s.index('**Table R131.S.')
    p.write_text(s[:start]+caption+full,encoding='utf-8')
write(OUT/'review/pdf_visual_attempt01.json',dict(status='REPAIR_REQUIRED',PDF_SHA=sha(TEMP/'pdf/attempt01/reading.pdf'),pages_actually_inspected=[42,45,91],issue='New 52-arm table at page91 has overlapping long U/L/signed-gap cells',repair='Display-only six-significant-digit U/L and three-significant-digit signed gaps; complete CSV/JSON unchanged',failed_PDF_retained=str(TEMP/'pdf/attempt01/reading.pdf'),no_new_solver_or_evidence_replay=True))
write(OUT/'review/document_tool_failures.json',dict(failures=[dict(label='pdf_locate_01',reason='GBK stdout cannot encode extracted Greek-question-mark glyph; extraction and scan completed',repair='ASCII escaped console JSON only',fee_and_stderr_retained=True)],formal_producer_changed=False))
