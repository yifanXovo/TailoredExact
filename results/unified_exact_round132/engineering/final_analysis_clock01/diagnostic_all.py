from pathlib import Path
import json,hashlib
root=Path.cwd();out=root/'results/unified_exact_round132';target=out/'engineering/final_analysis_clock01'
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
checked=0;issues=[]
for line,groups in [('D',rd(out/'experiment_plan.json')['D']),('C',rd(out/'C_experiment_plan.json')['groups'])]:
    for g in groups:
        p=out/g['name']/'reconstructed.json';aall=rd(p)['arms'];launches=rd(out/g['name']/'identity.json')['launches']
        for a,l in zip(aall,launches):
            checked+=1;q=all(a.get(k) for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified']) and not a.get('source_reduced')
            expected=a['T_produce'] if q and a['certificate'] else None
            if a['T_cert']!=expected:
                dest=Path(l['destination']);producer=rd(dest/'producer_receipt.json')
                issues.append(dict(line=line,group=g['name'],id=a['id'],seed=a['seed'],method=l.get('comparison_method',l['method']),
                    expected=expected,fields={k:v for k,v in a.items() if k in ['T_cert','T_produce','T_verify','T_total','certificate','formal_protocol_qualified','numbers_qualified','certificate_qualified','source_reduced']},
                    producer=producer,reconstruction_SHA=hashlib.sha256(p.read_bytes()).hexdigest()))
                # Preserve the first and any later mismatch.
        # Continue the finite registered plan to enumerate every mismatch.
    # Continue the finite registered plan to enumerate every mismatch.
r=dict(checked_complete_frozen_plan=checked,issues=issues,no_Optimize=True,raw_unchanged=True)
(target/'diagnostic_all.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps(r))
