"""Assemble one review manuscript from final evidence and the maintained appendices."""
from round134_common import *
import collections,inspect,re

def fmt(v,digits=6):return 'unresolved' if v is None else f'{v:.{digits}g}'
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n|'+ '|'.join('---' for _ in headers)+'|\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)

def assemble():
    summary=read(OUT/'reports/summary.json')
    assert summary['C_completed']==32 and not summary['C_missing'] and summary['D_completed']==4 and not summary['D_missing']
    C=read(OUT/'reports/C/arms.json');D=read(OUT/'reports/D/six_points.json');pairs=read(OUT/'reports/C/pairs.json')
    roots=read(OUT/'reports/roots.json');assert len(roots)==2 and read(OUT/'math/tiny_exact.json')['status']=='PASS'
    counts=summary['C_certificates'];denom=summary['C_denominators']
    def counter(rows,key):
        labels={'BOTH_CERTIFIED':'both certified','LEFT_ONLY_CERTIFIED':'S2 only certified',
            'RIGHT_ONLY_CERTIFIED':'control only certified','BOTH_OPEN':'both open','UNEVALUABLE':'ineligible',
            'Win':'favorable','Lose':'adverse','Tie':'tied','UNDETERMINED':'undetermined'}
        return ', '.join(f'{value} {labels.get(name,name)}' for name,value in collections.Counter(r[key] for r in rows).items())
    Ppairs=[p for p in pairs if p['right']=='P'];PSpairs=[p for p in pairs if p['right']=='PS']
    groups=collections.defaultdict(dict)
    for row in C:groups[row['role'],row['seed'],row['repeat']][row['method']]=row
    def cell(row):
        if row is None:return '-'
        if row['certificate']:return f"C {row['T_cert']:.3f}s"+(' (ind.)' if row['independent_proof'] else '')
        return f"O {fmt(row['U'],5)}/{fmt(row['L'],5)}"
    display=[]
    for (role,seed,repeat),methods in groups.items():
        matched=next((p for p in Ppairs if (p['role'],p['seed'],p['repeat'])==(role,seed,repeat)),None)
        if matched is None:outcome='unresolved'
        elif matched['class']!='BOTH_CERTIFIED':outcome={'LEFT_ONLY_CERTIFIED':'S2 only certified','RIGHT_ONLY_CERTIFIED':'P only certified','BOTH_OPEN':'both open','UNEVALUABLE':'ineligible'}[matched['class']]
        else:
            outcome={'Win':'S2 faster','Lose':'P faster','Tie':'equal'}[matched['direction']]
            outcome+=' (micro)' if matched['micro'] else ('; substantive' if matched['material'] else '; close')
        display.append([f'{role} / {seed} / {repeat}',cell(methods.get('P')),cell(methods.get('PS')),cell(methods.get('S2')),outcome])
    substantive=[p for p in pairs if p['material'] and not p['micro']]
    rejected=summary['rejected_native_independent_certificates']
    reversals=[p for p in pairs if p['direction']=='Lose']
    cert_summary=', '.join(f"{m} {counts[m]}/{denom[m]}" for m in ('S2','P','PS'))
    ctext=(f"All 32 fixed positions completed, with qualified certificates: {cert_summary}. "
        f"The fourteen S2/P comparisons comprise {counter(Ppairs,'class')}; their directions are {counter(Ppairs,'direction')}. "
        f"The four S2/PS comparisons comprise {counter(PSpairs,'class')}, with {counter(PSpairs,'direction')} directions. "
        f"There are {len(substantive)} substantive both-certified differences outside the micro panel. "
        f"There are {len(reversals)} adverse directions across both controls; these are retained individually. "
        f"{len(rejected)} observations have a rejected native source and an independent exact-zero certificate. "
        "They are eligible under the new independent-proof policy, while their native-source flag remains false. "
        "The new panel is targeted final-version evidence; it does not retroactively change historical counts.")
    if substantive:
        ctext+=' Substantive certified differences are '+', '.join(f"{p['role']} Seed{p['seed']} S2/{p['right']} {p['left_minus_right_seconds']:+.3f}s" for p in substantive)+'.'
    micro=[r for r in C if r['role']=='SM-B10-B']
    ctext+=f" Micro S2 complete times range from {min(r['T_produce'] for r in micro if r['method']=='S2'):.3f} to {max(r['T_produce'] for r in micro if r['method']=='S2'):.3f}s; P ranges from {min(r['T_produce'] for r in micro if r['method']=='P'):.3f} to {max(r['T_produce'] for r in micro if r['method']=='P'):.3f}s. Table 1 reports every repetition."
    ctable='**Table 1. All final-panel matched groups. C is a certificate with complete production seconds; O reports feasible U / qualified L and has no certificate time. Seed and repeat follow the problem name.**\n\n'+table(['Problem / Seed / repeat','P','PS','S2','S2/P result'],display)
    S2=[r for r in C if r['method']=='S2']
    ops=read(OUT/'reports/C/operations.json')
    optext=' '.join(f"{r['role']} Seed{r['seed']} has U={fmt(r['U'])}, L={fmt(r['L'])}, "+('a certificate.' if r['certificate'] else 'an unresolved original-objective gap.') for r in S2 if r['role'] in ('K-35-U','X-35-U','X-35-B'))
    optext+=' Complete vehicle quantities, target-under/equal/over counts, return loads and prefix peaks are retained for each method in the operations tables. They describe legal fleets even when optimality remains unresolved.'
    relations=read(OUT/'reports/D/tradeoff_relations.json')['adjacent_pairs']
    dop=read(OUT/'reports/D/operations.json')+[r for r in ops if r['role'] in ('K-15-S','UC-B20-B') and r['method']=='S2' and r['seed']==0]
    dtext=f"All six prescribed weight points are reported; {sum(r['certificate'] for r in D)}/6 have a qualified certificate. "
    for role in ('K-15-S','UC-B20-B'):
        rr=sorted([r for r in D if r['role']==role],key=lambda r:r['lambda_value'])
        dtext+=f"For {role}, Omega={fmt(rr[0]['Omega'])}, so rho is "+', '.join(fmt(r['rho']) for r in rr)+'. '
        same=all(abs(r['G']-rr[0]['G'])<=1e-10 and abs(r['P_avg']-rr[0]['P_avg'])<=1e-10 for r in rr)
        dtext+=('The three observed points lie on a platform. ' if same else 'The observed Gini/deviation points change with the penalty weight. ')
        if not all(r['certificate'] for r in rr):dtext+='The uncertified points are feasible incumbents, so their ordering alone cannot establish the exact optimal tradeoff. '
        work=sorted([r for r in dop if r['role']==role],key=lambda r:r['lambda_value'])
        assert len(work)==3
        dtext+='In ascending weight order, pickups are '+', '.join(str(r['pickups']) for r in work)+', returns are '+', '.join(str(r['returns']) for r in work)+', and maximum route-duration fractions are '+', '.join(fmt(r['maximum_duration']/r['T'],4) for r in work)+'. '
    dtext+='The relation table evaluates the error-aware inequalities using only accepted original-objective U/L gaps, without treating feasibility tolerance as objective error. These remain conditional on the engineering bound policy rather than new rational optimality claims.'
    dtable='**Table 2. Fixed physical instances at all three weights. Gap is signed original-objective U-L.**\n\n'+table(
        ['Problem','lambda / rho','G','P average','F','certificate','gap'],
        [[r['role'],fmt(r['lambda_value'])+' / '+fmt(r['rho']),fmt(r['G']),fmt(r['P_avg']),fmt(r['F']),
          'yes' if r['certificate'] else 'open',fmt(r['signed_gap'])] for r in D])
    reliable=[r for r in roots if r['TC_increment'] is not None and r['TC_increment']>1e-7 and all(s=='NUMERICAL_OPTIMAL_LP' for s in r['statuses'])]
    rtext='Both fixed root domains completed the three prescribed LP layers. '
    for r in roots:
        rtext+=f"{r['role']} gives L0={fmt(r['L0'],10)}, Lold={fmt(r['L_old'],10)}, Lold+TC={fmt(r['L_old_TC'],10)}, with TC increment {fmt(r['TC_increment'],10)}. "
    rtext+='These are floating-point LP observations with recorded primal/dual quality and added-row residuals; the tiny result above is an exact rational theorem. '
    if reliable:
        rtext+='A reliable numerical original-objective increase is observed on '+', '.join(r['role'] for r in reliable)+'. A next-round candidate should therefore be a single uniform root/leaf TC rule, with a fixed matched performance panel and construction costs included; it should not select instances or Seeds from these outcomes. No such production comparison is run here.'
    else:rtext+='No reliable positive TC increment is established on these real roots. The present exploration stops with the exact tiny result and this negative real-root evidence; it does not expand the root or Seed set.'
    rtable='**Table 3. Identical root domain at three relaxation layers. Times are native LP seconds; all non-comparison auxiliaries are free.**\n\n'+table(
        ['Problem','L0','Lold','Lold+TC','TC increment','U / remaining gap','LP seconds 0 / old / TC'],
        [[r['role'],fmt(r['L0'],9),fmt(r['L_old'],9),fmt(r['L_old_TC'],9),fmt(r['TC_increment'],7),
          fmt(r['U'])+' / '+fmt(r['gap_after']), ' / '.join(fmt(t,4) for t in r['solve_seconds'])] for r in roots])
    adverse_material=[p for p in substantive if p['direction']=='Lose']
    conclusion=(f"The final confirmation certifies {counts['S2']}/{denom['S2']} S2 observations, alongside "
        f"{counts['P']}/{denom['P']} P and {counts['PS']}/{denom['PS']} PS observations. "
        f"It retains {len(reversals)} adverse directions and {sum(not r['certificate'] for r in S2)} open S2 positions. "
        f"There are {len(adverse_material)} substantive adverse both-certified comparisons under the prespecified final-panel rule. "
        "The role-by-role evidence, rather than a requirement to win every Seed, determines the implementation assessment. "
        "The independent zero rule resolves a proof-source distinction while preserving normal positive proofs and rejection of insufficient native evidence.")
    replacements=dict(FINAL_ABSTRACT=f"The targeted final implementation certifies {counts['S2']}/{denom['S2']} S2, {counts['P']}/{denom['P']} cold-compact and {counts['PS']}/{denom['PS']} paid-start observations across 32 fixed positions; four additional within-instance weight runs examine Gini, deviation and vehicle work.",
        ROOT_ABSTRACT=('at least one fixed real root also shows a numerical relaxation increment.' if reliable else 'neither fixed real root shows an additional TC gain after retaining the old state-penalty control.'),
        C_RESULTS=ctext,C_MAIN_TABLE=ctable,OPERATIONAL_RESULTS=optext,D_RESULTS=dtext,D_TABLE=dtable,
        ROOT_RESULTS=rtext,ROOT_TABLE=rtable,FINAL_CONCLUSION=conclusion)
    body=(OUT/'paper_body.md').read_text(encoding='utf-8')
    for key,value in replacements.items():
        assert body.count('{{'+key+'}}')==1,key
        body=body.replace('{{'+key+'}}',value)
    assert '{{' not in body
    old=(ROOT/'results/unified_exact_round133/manuscript.md').read_text(encoding='utf-8-sig')
    appendix=old[old.index('# Appendix A.'):]
    start=appendix.index('**Frozen baseline and corrected candidate.**');end=appendix.index('This appendix is the single maintained model specification')
    appendix=appendix[:start]+('The complete physical formulation and strengthening proofs below are retained from the maintained manuscript. S2 uses uniform pair support and no triple support. The final production implementation adds the independent exact-zero proof in Proposition 1; native-source qualification and all normal positive-objective rules remain separate. Historical source pointers identify their own snapshots and are not claims that an old executable produced the final panel.\n\n')+appendix[end:]
    begin=appendix.index('### B.4.1 Frozen certificate admission and replacement qualification')
    end=appendix.index('## B.5 Teaching states and a separately sourced event')
    replacement='''### B.4.1 Final independent and native proof rules

Every own final fleet is independently checked against the original physical problem. An exact stock proof of equal ratios and zero positive-weight target penalties establishes F=0; the shared production predicate additionally repeats complete per-vehicle physical verification. It does not accept a merely near-zero positive objective. P, PS and S2 use the same predicate. P obtains no H, while PS and S2 pay their complete own startup.

An independently valid full-domain nonnegative floor may prove a zero fleet even after native-source rejection. The rejected native journal and conservative restoration of the full unresolved domain remain unchanged; this is not a successful native proof or a repaired hidden search tree. Without sufficient independent proof, source-rejected positive outcomes retain the restored open domain. Ordinary qualified positive native and outer coverage certificates retain their original policy.

The proof is finalized after the final selected own fleet is known, necessary physical checks have finished and native resources are released. Required outputs and normal process completion are included in the complete production clock. Postproduction verification has its own elapsed time and cannot backfill a proof or an earlier production timestamp. Engineering source anomalies, the finite R133 checks and historical bridge tables are collected in the supplement.

'''
    appendix=appendix[:begin]+replacement+appendix[end:]
    begin=appendix.index('## A.7 Numerical implementation boundary')
    end=appendix.index('## A.8 Writer and variable map')
    numerical=r'''## A.7 Numerical implementation boundary

Lemmas A1-A4 concern ideal exact arithmetic and valid mathematical domains. Stored matrices use binary64 arithmetic and Gurobi 13.0.2. Native FeasibilityTol and OptimalityTol are \(10^{-6}\), IntFeasTol \(10^{-5}\), requested MIPGap/MIPGapAbs zero; retained evidence closure uses \(10^{-7}\). Ordinary native/outer certificates are numerical certificates under this policy. The stock-based independent zero theorem and the rational tiny-reference proof have their separately stated exact premises.

A historical inclusive-cutoff writer could serialize an artificial contradictory row at a legal cutoff boundary. R133 removed that row while retaining valid penalty and domain rows. Its exact boundary fixture and finite qualification remain in the supplement; historical raw and performance denominators are not rewritten. The final implementation retains the corrected writer. For a native-derived bound or closure, the complete physical embedding, applicable cutoff complement and qualified source are required even when an analytic floor independently exists.

Every final selected own fleet is physically verified. Ordinary positive numerical certification additionally requires qualified source/return chains and complete coverage, normal lifecycle completion and a signed gap in \([-10^{-7},10^{-7}]\). Rejected native proof dependencies cannot close a domain. A sufficient independent original-objective zero proof can instead establish optimality while the native-source flag stays rejected. A near-zero positive objective is not exact zero. The finalizer, normal process completion and required output belong to the production clock; later postproduction checks cannot backdate a certificate.

The source-rejected zero observations in R132/R133 keep their historical unqualified certificate/performance decisions. They are distinct from the newly executed final-panel observations under the independent-proof rule. Historical numerical anomalies and readout repairs are collected in the supporting material, with unavailable hidden-tree causes left unresolved.

The total process deadline makes a run finite, rather than guaranteeing certification in every finite window. Finite physical space and ideal complete search provide no linear forecast from a remaining objective gap.

'''
    appendix=appendix[:begin]+numerical+appendix[end:]
    before='The source is public at the fixed [implementation snapshot](https://github.com/yifanXovo/TailoredExact/tree/355eefd2be3fe5651195681faf7b3a63ee4032f8). That historical source map is distinct from the current frozen byte identities in E3_binding.json and D_execution_binding.json.'
    after='The linked [implementation snapshot](https://github.com/yifanXovo/TailoredExact/tree/355eefd2be3fe5651195681faf7b3a63ee4032f8) is the historical source authority for this unchanged formulation map. The final implementation and its exact byte capsule are identified by candidate_manifest.json and source_publication.json in the current reproduction entry.'
    assert appendix.count(before)==1;appendix=appendix.replace(before,after)
    appendix=appendix.replace('## B.14 Current pair-support version and fixed attribution controls','## B.14 Historical pair-support adoption and attribution controls')
    appendix=appendix.replace('The sole paper method is original E2 `ms2`, called S2. E3 retains its source behavior and adds',
        'The sole paper method retains the historical E2 `ms2` identity, called S2. Historical E3 retains that version\'s source behavior and adds')
    fixes=[
        ('The current frozen E3 production source base is 7564a5415331b380e24d1ec06936dcfd56557e67 [@frozenImplementation]; E3_binding.json supplies its exact current source identities. The active state/service, H-use, uniform pair-only and legal inclusive-root conditions are checked against that current source, rather than inferred from historical line numbers.',
         'That historical E3 source base and its binding belong to the earlier attribution controls [@frozenImplementation]. The final production source and PE are fixed by candidate_manifest.json; source_publication.json provides the exact source-byte capsule. Current state/service, own-H, pair-only and inclusive-domain conditions are checked against these final identities, rather than inferred from historical line numbers.'),
        ('Algorithm 1 appears in Section 4;','Algorithm 1 appears in Section 3;'),
        ('The replacement qualifies the source before deriving the cutoff-complement floor and removes the invalid artificial closure row, as described in Sections 5.4 and A.7; remaining numerical limitations still apply.',
         'The final implementation retains the R133 source qualification and corrected inclusive-domain writer, as explained in A.7 and B.4.1. Its independent zero proof is separate from native-dependent coverage; the supplement retains the historical correction evidence. Remaining numerical limitations still apply.'),
        (r'the study uses \(\lambda=.15\), positive weights and \(t_p=t_d=60\).',
         r'the baseline panel uses \(\lambda=.15\), with within-instance sensitivity at \(.075,.30\), positive weights and \(t_p=t_d=60\).'),
        ('PE --input INPUT --lambda 0.15 --T T','PE --input INPUT --lambda LAMBDA --T T')]
    for before,after in fixes:
        assert appendix.count(before)==1,before
        appendix=appendix.replace(before,after)
    begin=appendix.index('The frozen paper entry is resolved by [current_method_manifest.json]')
    end=appendix.index('~~~text',begin)
    appendix=appendix[:begin]+'''The final paper entry is fixed by [candidate_manifest.json](candidate_manifest.json), [C_matrix_frozen.json](C_matrix_frozen.json) and [D_matrix_frozen.json](D_matrix_frozen.json), together with the [inherited R130 configuration](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/paper_method_config.json). The original R132 launch freezes remain historical evidence, rather than relative links to current files. The template below is one S2 token vector; complete actual launches, including P and PS, are in the current matrices. INPUT, OUT, physical T, cap B, B_MINUS_6, LAMBDA and SEED take their registered values. LAMBDA is .15 in C and .075 or .30 in the added D positions. H seed20260626 and native settings remain explicit configuration choices. The retained zero-stop flag does not assert that MS2 returns before its native lifecycle: an own zero U can produce the degenerate [0,0] root, and the shared independent proof is finalized after resource release and complete physical verification. The supervisor starts the production clock before admission and seals normal required output; native Runtime alone is not T_cert.

'''+appendix[end:]
    assert 'historical_evidence.md' in appendix
    appendix=appendix.replace('historical_evidence.md',
        '[the R130 historical account](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/manuscript.md)')
    manuscript=body+'\n\\clearpage\n\n'+appendix
    (OUT/'manuscript.md').write_text(manuscript,encoding='utf-8')
    supplement='# Supporting material: complete results, historical layers and implementation qualification\n\n'
    supplement+='The main manuscript reports the final fixed implementation. This supplement retains complete tables, historical evidence with its own versions and engineering details. No historical observation is relabelled as final-version evidence.\n\n'
    supplement+='## S1. Every final-version method position\n\n'
    supplement+=table(['Position / problem','Seed / repeat','method','proof','U','L','production / certification seconds'],
        [[f"C{r['position']:02} {r['role']}",f"{r['seed']} / {r['repeat']}",r['method'],
          'independent zero' if r['independent_proof'] else 'native/outer' if r['certificate'] else 'open',fmt(r['U'],10),fmt(r['L'],10),
          fmt(r['T_produce'],9)+' / '+fmt(r['T_cert'],9)] for r in C])
    supplement+='\n## S2. Production and postproduction clocks\n\n'
    supplement+='The C01 native producer sealed normally. Its first postreader failed on a missing launch-metadata field; a bounded read-only adapter derived the already registered settings and reused that same raw arm. The failed logs, unchanged producer clock and real verification delay remain. No healthy native arm was repeated.\n\n'
    supplement+=table(['Position','production seconds','postverification seconds','total seconds'],[[f"C{r['position']:02}",fmt(r['T_produce'],10),fmt(r['T_verify'],10),fmt(r['T_total'],10)] for r in C])
    supplement+='\nFull machine-readable arms, matched pairs, all six weight points, complete inventories/vehicle work, raw producer seals, source qualifications and construction/LP receipts are supplied through the finite reproduction entry. Open certification times are null.\n\n'
    supplement+='## S3. Source access, model inheritance and novelty boundary\n\n'+(OUT/'literature_scope.md').read_text(encoding='utf-8')
    supplement+='\n## S4. Historical reading extract, version R133\n\nThe following dated text is a historical evidence extract at base 39043b15b3cceae2cab14a3fbaec39e2b16339ce. Its terms “current” and “replacement” refer to R133 or earlier versions, never to the final panel in S1. The main manuscript states the updated scientific conclusions. Old historical_evidence.md references resolve to the [fixed R130 historical account](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/manuscript.md), including Sections6.8-6.10, rather than a missing current relative file.\n\n'
    supplement+=old[old.index('## 5. Complete-method evidence and new inputs'):old.index('# Appendix A.')]
    supplement+='\n## S5. Historical implementation/source qualification tables\n\n'
    supplement+=old[old.index('### B.4.1 Frozen certificate admission and replacement qualification'):old.index('## B.5 Teaching states and a separately sourced event')]
    supplement+='\n## S6. Relation of TC to retained historical mechanisms\n\n'+(OUT/'tc_note.md').read_text(encoding='utf-8')
    (OUT/'supplement.md').write_text(supplement,encoding='utf-8')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),supplement_SHA=sha(OUT/'supplement.md'),
        references_SHA=sha(OUT/'references.bib'),body_template_SHA=sha(OUT/'paper_body.md'),
        required_final_positions=[32,4,6],historical_original_text_preserved_in_supplement=True))
    print('Final review manuscript and complete supplement assembled from all fixed evidence')

def pdf():
    import round126_export as old
    source=inspect.getsource(old.export)
    substitutions=[("for name in ['model_appendix.md','algorithm_appendix.md','tables/historical_display.md']:","for name in []:"),
        ("Path(os.environ.get('ROUND126_PDF_DEST',str(OUT/'manuscript.pdf')))","OUT/'manuscript.pdf'"),
        ("Path(os.environ.get('ROUND126_PDF_RECEIPT',str(OUT/'pdf_export.json')))","OUT/'pdf_export.json'"),
        ('date=19 October 2026','date=26 October 2026'),
        ('text=landscape_tables(text)','text=keep_captions(landscape_tables(text))'),
        ('subprocess.run(command,cwd=TEMP','subprocess.run(command,cwd=OUT'),
        ('manuscript.md + model_appendix.md + algorithm_appendix.md + references.bib; six immutable historical tables','manuscript.md (main plus maintained model/algorithm appendices) + references.bib + current figures'),
        (r'\usepackage{etoolbox}',r'\usepackage{etoolbox}'+'\n'+r'\usepackage{needspace}'),
        (r'\setlength{\emergencystretch}{3em}',r'\setlength{\emergencystretch}{8em}'+'\n'+
         r'\widowpenalty=10000\clubpenalty=10000'+'\n'+
         r'\AtBeginEnvironment{CSLReferences}{\interlinepenalty=10000}')]
    for before,after in substitutions:
        assert source.count(before)==1,before
        source=source.replace(before,after)
    def keep_captions(value):
        value=re.sub(r'^\*\*Table[^\n]*\*\*$',lambda m:
            ('\n```{=latex}\n\\clearpage\n```\n' if m[0].startswith('**Table 1.') else '')+
            '\n```{=latex}\n\\Needspace{8\\baselineskip}\n```\n\n'+m[0],value,flags=re.M)
        value=re.sub(r'^(\*\*(?:Proposition|Lemma)[^\n]*)$',
            lambda m:'\n```{=latex}\n\\Needspace{8\\baselineskip}\n```\n\n'+m[0],value,flags=re.M)
        value=re.sub(r'(^#{2,4} [^\n]+\n\n)(?=\|)',
            lambda m:'\n```{=latex}\n\\Needspace{10\\baselineskip}\n```\n\n'+m[0],value,flags=re.M)
        for heading in ('## 7. Conclusions and implications','# References'):
            assert value.count(heading)==1
            value=value.replace(heading,'\n```{=latex}\n\\clearpage\n```\n\n'+heading)
        return value
    # All main tables fit the portrait text width; forcing the six-row and
    # two-row tables into separate landscape pages caused avoidable blank space.
    ns=dict(vars(old),OUT=OUT,TEMP_PARENT=TEMP/'pdf',keep_captions=keep_captions,
        landscape_tables=lambda value:value)
    exec(compile(source,__file__+'::maintained_export','exec'),ns);ns['export']()
    print('Final review PDF generated; visual QA remains required')

if __name__=='__main__':{'assemble':assemble,'pdf':pdf}[sys.argv[1]]()
