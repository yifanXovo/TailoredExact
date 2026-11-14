"""Bounded current-source edits and diagnostic tables; never calls a solver."""
from round167_common import *
import re
PAPER=ROOT/'results/unified_exact_round137'
def save(p,s):Path(p).write_bytes((s.rstrip()+'\n').encode('utf-8'))
def mdtable(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(map(str,r))+' |' for r in rows]])+'\n\n'
def apply():
    # Normalize CRLF inherited through git-show before editing; do not insert
    # extra blank lines into the algorithm listings or formulas.
    for name in ['paper_body.md','supplement.md']:
        p=PAPER/name;p.write_bytes(p.read_bytes().replace(b'\r\r\n',b'\r\n').replace(b'\r\n',b'\n'))
    body=(PAPER/'paper_body.md').read_text(encoding='utf-8-sig')
    def replace_paragraph(start,replacement):
        nonlocal body
        a=body.index(start);b=body.find('\n\n',a)
        body=body[:a]+replacement.strip()+body[b:]
    replace_paragraph('The proof\'s source-dependency requirement',r'''The scheduler accumulates same-unit bounds monotonically. Its final qualification rejects affected Native proof dependencies and restores the unresolved physical domain; Appendix B.4 distinguishes that conservative fallback from ideal source-revocation accounting. Numerical qualification and lifecycle evidence are required in addition to the ideal coverage proof.''')
    replace_paragraph('The C++ complete-method implementation and the historical Python',r'''The supplement identifies the C++ complete method and historical Python helper separately. E+ is uniform, independently paid and evaluated only in its registered runs; B/P Seed repetitions do not retest it.''')
    replace_paragraph('E+ evidence is confined',r'''The validity of an inventory lower source and its net complete-method value are separate questions.''')
    replace_paragraph('Tables report each registered panel',r'''Each panel retains its own denominator. Matching AM/mechanism/resource/weight baselines refer to one historical record, counted once. Additional Seeds and representation tests on the later six configurations are exposed-input repetitions. Resource pairs change only T; each weight family retains one physical feasible set.''')
    replace_paragraph('The six later source configurations',r'''The later six configurations are exposed for the Seed follow-up; its command set was frozen before execution.''') if 'The six later source configurations' in body else None
    replace_paragraph('The preselected Seed 1',r'''The preselected Seed1 checks retain their own matched baselines.''') if 'The preselected Seed 1' in body else None
    replace_paragraph('The additional 24 commands',r'''The 24 additional Seed commands use the exposed six-input cohort.''') if 'The additional 24 commands' in body else None
    replace_paragraph('The separately named C166',r'''C166 changes only the representation in Section 2.3. Its six exposed-input Seed0 comparison uses fresh same-build B controls, with independently paid complete H and the original 1200/2400 s caps under §3.4. Offline fleets and bounds enter neither method.''')
    replace_paragraph('Eight same-scope qualification LP pairs',r'''Eight qualification LP pairs, six roots and two fixed children, differ by at most 3.33e-16. C166 reduces columns in every pair but can increase rows/nonzeros. These checks support the common physical LP projection; they give no root-bound gain or search-time guarantee.''')
    replace_paragraph('B certifies 3/6 and C166 certifies 2/6.',r'''B certifies 3/6 and C166 2/6. Their joint-CERT denominator is 2/6. C166/B certificate-time ratios are 1.1108 on B20 (nonmaterial) and 4.3488 on X20 (substantive), under §3.4. The comparison adds no B/P pair or independent Seed evidence.''')
    replace_paragraph('The complete panel supports retaining B',r'''Retain B uniformly. C166 loses C20's certificate; its C35/B35 U improve by .00852312/.01500068 while L weakens, and X35 worsens on both endpoints. These mixed results remain part of the evidence, without a per-input portfolio or single-Seed generalization.''')
    replace_paragraph('The three n20 pairs have the same recorded AM',r'''The three n20 pairs have matching recorded AM action sequences and equal initial raw LP values. On X20, Native Runtime is 122.891/542.289 s, Work 220.964/992.214 and nodes 8842/66425 for B/C166; writer time is .721/.724 s. Extra cost lies mainly inside Native optimization. Presolve, cuts and branching may all differ; no particular cause is established.''')
    replace_paragraph('The independently priced inventory problem gives',r'''For a common inventory necessary problem, \(L_I\le f_I^*\le U_I\) and \(f_I^*\le f_P^*\le U_P\). Thus''')
    replace_paragraph('Only the final term is bounded',r'''Only the last term is controlled by the price width \(U_I-L_I\); precise inventory pricing does not settle physical realization or incumbent quality. The supplement retains each structural object's positive, mixed and adverse results.''')
    body=body.replace('preparation plus diagnostic execution takes 126.262 s, including the solver-free checks.',
        'recorded C++ subprocess wall time is 126.262 s; the supplement gives conservative enclosing-window accounting.')
    # Remove repeated table display cautions after the single protocol; all data remain.
    body=body.replace('Values within the frozen 1e-7 equivalence scale\nare displayed as 0. Full individual U/L, raw search bounds, paid costs,\nmedians/ranges and binary64 values remain in the supplement.',
                      'Values within 1e-7 are displayed as 0; individual endpoints and costs remain in the supplement.')
    body=body.replace('The final column is\nT_produce for B / C166, in seconds, including startup and close. It is a\ncertificate time only for a CERT entry; OPEN has null T_cert. Individual\npost-verification costs and full-precision endpoints are in the supplement.',
                      'The last column is paid production seconds; T_cert exists only for CERT. Full precision and separate verification costs are in the supplement.')
    save(PAPER/'paper_body.md',body)
    # Preserve the exact removed bibliographic-reading notes internally.
    bib=(PAPER/'references.bib').read_text(encoding='utf-8-sig')
    removed=re.findall(r'^\s*note=\{(.*?)\}\s*$',bib,re.M)
    save(OUT/'bibliography_reading_notes.md','# Inherited reading notes moved out of the public bibliography\n\nThese describe historical reading scopes, not new full-text review.\n\n'+'\n\n'.join(removed))
    bib=re.sub(r'^\s*note=\{.*?\}\s*\n','',bib,flags=re.M)
    bib=re.sub(r'howpublished=\{Frozen E3 production source base [^}]+\}', 'howpublished={Archived implementation and reproducibility record}',bib)
    bib=re.sub(r'howpublished=\{Round12[23] scientific commit [^}]+\}', 'howpublished={Archived finite benchmark and proof study}',bib)
    bib+=r'''
@phdthesis{behle2007,
 author={Behle, Markus}, title={Binary Decision Diagrams and Integer Programming},
 school={Universitaet des Saarlandes}, year={2007},
 url={https://people.mpi-inf.mpg.de/alumni/d1/2019/behle/publications/behle_thesis.pdf}
}
@article{balas2005,
 author={Balas, Egon}, title={Projection, Lifting and Extended Formulation in Integer and Combinatorial Optimization},
 journal={Annals of Operations Research}, volume={140}, pages={125--161}, year={2005},
 url={https://www3.diism.unisi.it/~agnetis/projlift.pdf}
}
@article{muldoon2013,
 author={Muldoon, Frank M. and Adams, Warren P. and Sherali, Hanif D.},
 title={Ideal Representations of Lexicographic Orderings and Base-2 Expansions of Integer Variables},
 journal={Operations Research Letters}, volume={41}, number={1}, pages={32--39}, year={2013},
 doi={10.1016/j.orl.2012.10.005}
}
@incollection{vanhoeve2024,
 author={van Hoeve, Willem-Jan}, title={An Introduction to Decision Diagrams for Optimization},
 booktitle={Tutorials in Operations Research}, publisher={INFORMS}, year={2024},
 url={https://www.andrew.cmu.edu/user/vanhoeve/papers/DD_TutORial.pdf}
}
'''
    save(PAPER/'references.bib',bib)
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    app=app.replace('difference interval in Table 5','difference interval in Table 8')
    a11=r'''
## A.11 Conditional joint stock, service, product and code hull

Write \(D=[l,u]\cap\mathbb Z\), \(m(y)=|b-y|\), \(v(y)=\mathbf1[y\ne b]\), and let \(c(y)\) be the absolute d-bit stock code, \(d=\max\{1,\operatorname{bit\_width}(C)\}\). The enhanced hull is

\[
E(D)=\operatorname{conv}\{(y,m(y),v(y),g,gy,c(y),gc(y)):y\in D,\ g\in[\alpha,\beta]\}.
\]

The continuous enumerated reference R_abs uses the state/perspective equations (A15)-(A16), movement/visit links, and \(\delta_h=\sum_yc_h(y)s_y\), \(w_h=\sum_yc_h(y)q_y\). Its selectors remain continuous even when delta is declared binary. This is a common absolute code; the historical LOG offset code \(y-l\) is different.

Partition D into nonempty donor, initial singleton and receiver intervals. Each has a separate source entry and MSB-first bit DAG. At each layer at most four prefix states record tightness to that part's lower and upper bounds. A 0/1 edge is permitted exactly when consistent with its tight bounds; the next flags record equality. Every path reads all d bits and reaches the common sink. Prefix induction proves a bijection between paths and legal stocks. No graph nodes are shared between service parts before the sink. Bounds on nodes and arcs are \(n_G\le2+r(1+4d)\), \(a_G\le r(8d+5)\), \(r\le3\).

Let \(A\) use tail +1 and head -1 and let \(e\) be source +1, sink -1. On this single graph use

\[
Af=e,\quad Aq=ge,\quad f\ge0,\quad \alpha f\le q\le\beta f.
\tag{AD1}
\]

Every bit-one edge h has Y cost \(2^h\). On donor entries the M cost is b and donor digit-edge M cost is minus its Y cost; on receiver entries it is -b and receiver digit-edge cost is its Y cost. Initial-piece M costs are zero. Donor/receiver entries have V cost one; all others zero. Thus path totals are y, m(y), v(y). Denoting these costs by \(a_Y,a_M,a_V\), reconstruct

\[
Y=a_Y^\top f,\ M=a_M^\top f,\ V=a_V^\top f,\ Z=a_Y^\top q,
\quad \delta_h=\sum_{e\in A_h^1}f_e,\quad w_h=\sum_{e\in A_h^1}q_e.
\tag{AD2}
\]

Entry/terminal edges do not contribute to code coordinates. Both flows conserve at every internal node. Omitting each sink equation is equivalent because the incidence-column sums are zero. D167 adds no independent bit-product block.

**Proposition A11 (enhanced projection and partial digits).** Equations (AD1)-(AD2) project exactly to E(D). After fixing any subset of absolute digits, the projection is \(E(D(F))\); its physical projection is \(H(D(F))\). Empty conditional domains are infeasible. Integer delta recovers the exact local stock/service/product object.

**Proof.** For \(\alpha<\beta\), define nonnegative conserved endpoint flows

\[
f^\alpha=\frac{\beta f-q}{\beta-\alpha},\qquad
f^\beta=\frac{q-\alpha f}{\beta-\alpha}.
\]

Their source masses are \((\beta-g)/(\beta-\alpha)\) and \((g-\alpha)/(\beta-\alpha)\), summing to one. Decompose each acyclic flow into nonnegative source-sink path flows by repeatedly subtracting the minimum positive flow along a complete path. No residual cycle or disconnected positive component can remain. Equations (AD2) give a convex combination of legal stock/code points at the two Gini endpoints. Conversely a legal stock/g uses f=1,q=g on its unique path, zero elsewhere; convex combinations extend all E(D) points. For \(\alpha=\beta=a\), the bounds imply q=af and g=a; decompose only f. The implementation uses the direct path map and never divides by the Gini width.

Each unit path crosses each bit layer once. If \(\delta_h=0\), nonnegative one-edge flow vanishes; if \(\delta_h=1\), zero-edge flow vanishes because total layer mass is one. The q bounds eliminate the same inconsistent edges. Only compatible paths remain in the endpoint decomposition, exactly the stocks in D(F). Conversely all compatible paths extend. With all digits integer, the injective absolute code leaves one legal stock/path; conservation gives q=gf, and the desired M,V,Z,w follow. The empty, singleton and C=0 cases are included. The physical bidirectional mapping then uses the unchanged one-way service, unique assignment and integer balance premises of Lemmas A1-A2. \(\square\)

Every E(D) point extends to C166: compress its physical graph terms to legal affine-piece endpoints at the same g, but retain the original full-mixture delta/w for the separate bit layer. Those coordinates satisfy its global and interval product inequalities by convexity. Thus D167 and R_abs have identical enhanced projections contained in C166's; partial fixed-bit physical inclusion follows. With no bit fixes all physical projections equal H(D). In D=0..4,b=2,g in [0,1/2], the C166 point t2=1,q2=1/4, delta=(1,1/2,0), w=(1/4,1/8,0) has M=V=0 while delta0=1 leaves legal stocks {1,3} and requires M=V=1 in the conditional hull. This proves local strictness, not a claim about a visited Native node.

For any conditional domain, the minimum/maximum legal donor stocks, legal initial singleton, and minimum/maximum receiver stocks generate H with at most five supports: same-g affine interpolation preserves Y,M,V,Z on each side. Holes do not invalidate this physical-hull argument, but integer membership and E still need the compatible code/path set. Five supports do not generally represent E.

The complete-model conclusion requires all outside rows to use the replaced state only through the declared interface. Actual B's e epigraph, H/S, original objective, physical route/service/time, cutoff and enabled valid rows meet that condition; AP/count/RN/CDF/theta/linked-direction/VD-J extensions are unsupported by the offline entry. The network's auxiliary counts are \(2a_G+2d\) columns, d binaries and \(2(n_G-1)+2a_G+4+2d\) rows, excluding unchanged physical rows. Nonzero counts scale likewise; coefficients have O(d) bits, so total coefficient description length includes that factor. The research note gives exact nonzero counts and actual full-model dimensions.

Path-flow projection and endpoint disjunction are established methods [@behle2007; @balas2005; @vanhoeve2024]; bounded ideal base-2 encodings are established as well [@muldoon2013]. This local guarantee concerns the specified partial digits. Adding an arbitrary stock inequality or a narrower g bound to an old model does not rebuild the hull for the new domain; actual new bounds must be used in (AD1) and path legality. Local ideality does not imply the full BRP hull or effective branching [@huchetteVielma2023]. The default-off C++ entry verifies the frozen representation and physical interface, without integrating a complete controller or claiming a speedup.

'''
    assert '## A.11' not in app
    app=app.replace('# Appendix B. Executable method specification',a11+'\\clearpage\n\n# Appendix B. Executable method specification')
    save(PAPER/'model_and_algorithm_appendices.md',app)
    companion=(PAPER/'mathematical_analysis.md').read_text(encoding='utf-8-sig')
    companion+=r'''
## Conditional absolute-code information

Appendix A.11 augments the shared physical hull with absolute digits and their Gini products. The f/q formulation on one MSB-first interval graph is exactly the enumerated enhanced hull E(D), and fixing any subset of its digits yields E(D(F)). Its proof uses two conserved endpoint flows, with a direct fixed-g case. R_abs and D167 therefore preserve service/code mixture information that C166's independent bit layer can lose; their unconditioned physical hulls still agree. Legal donor/receiver extrema and the initial singleton generate H(D(F)) with at most five supports, even when the condition creates holes, but they do not generally generate E(D(F)).

This is a local conditional statement with the full-model interface premise, not ideality of the routing problem or all possible Native child domains. The fixed diagnostic matrix has three strict original-objective conditioned LP increments, many zero increments and larger D167 matrices; no complete-method performance is inferred. The [full conditional proof](../unified_exact_round167/conditional_state_theory.md) states costs, coefficient encoding and sharp scope limits, and the [complete positions](../unified_exact_round167/positions.csv) retains every local, canonical and tiny observation.
'''
    save(PAPER/'mathematical_analysis.md',companion)
    supp=(PAPER/'supplement.md').read_text(encoding='utf-8-sig').replace('../unified_exact_round166/source_manifest.json','../unified_exact_round167/source_manifest.json').replace('../unified_exact_round166/document_build.json','../unified_exact_round167/document_build.json')
    q=read(OUT/'qualification.json');positions=read(OUT/'positions.json')
    supp+='''\n## S167.3 Conditional representation diagnostics\n\nThe network is a separately named offline representation prototype. B and C166 production source/defaults are frozen; no new complete GI-TBC/P/PS/E+ run or Seed comparison is made. All eight frames use the exact R166 inputs, domain, cutoff and original objective from the recorded argv. All stations use the selected representation, while one station receives a deterministic partial absolute-code assignment. The largest legal domain is selected, ties by lowest station index. F1/F2 choose the first available mixed low bit, opposing initial stock when still legal, otherwise zero. No LP values or times select the masks. These scopes are not claimed to be visited Native nodes.\n\nThe [frozen diagnostic manifest](../unified_exact_round167/diagnostic_manifest.json), [all 88 positions](../unified_exact_round167/positions.csv) and [raw qualification](../unified_exact_round167/qualification.json) bind exact models, masks, physical block identities, full dimensions and costs. The 72 canonical positions form the following 24 triples; each value is a qualified raw LP optimum of the original objective. All 72 are OPTIMAL, with no infeasible, failed, reused or unexecuted position. All three levels are nondegenerate.\n\n'''
    rows=[]
    for t in q['triples']:
        p=next(p for p in positions if p['id']==t['frame']+'_F'+str(t['level'])+'_D167')
        rows.append([t['frame'],t['level'],str(p['mask']).replace(' ',''),p['conditional_stocks'],*[format(t['values'][r],'.12g') for r in ['R_abs','C166','D167']],format(t['delta_D167_C166'],'.7g')])
    supp+=mdtable(['Frame','F','Fixed [h,a]','Legal stocks','R_abs L','C166 L','D167 L','D167-C166'],rows)
    supp+='''D167/R_abs maximum absolute difference is 2.22e-16. Their unconditioned physical LP objectives match C166; among sixteen partial conditions, only X20 root F2 and B35 root F1/F2 have increments above 1e-7. The other thirteen conditions show no increment at that scale. This is stronger conditional information, without a full-domain certificate or full-algorithm runtime implication.\n\n'''
    rows=[]
    for frame in ['R163-C20-S_root','R163-B20-B_root','R163-X20-S_root','R163-C35-U_root','R163-B35-S_root','R163-X35-S_root','R163-C20-S_child','R163-B20-B_child']:
        trio=[next(p for p in positions if p['id']==frame+'_F0_'+r) for r in ['R_abs','C166','D167']]
        rows.append([frame,*[' / '.join(str(p['prepare'][k]) for p in trio) for k in ['columns','binaries','rows','nonzeros']]])
    supp+=mdtable(['Frame','Columns R/C/D','Binaries R/C/D','Rows R/C/D','Nonzeros R/C/D'],rows)
    supp+='''The fixed graph has logarithmic asymptotic size, but its constants make every tested D167 matrix larger than R_abs in columns and rows. Nonzero counts also increase here. F1/F2 add one/two fixed-bit equality rows. The per-station graph sizes, exact model file bytes, build time and every Native Runtime/Work counter are in the complete positions and raw models. Tiny LP times are diagnostics; no full-method speed ratio is reported.\n\n'''
    supp+=mdtable(['Local position','Objective','R_abs','C166','D167'],[[i,'min V' if i=='L2' else 'min M',q['local'][i+'_R_abs'],q['local'][i+'_C166'],q['local'][i+'_D167']] for i in ['L1','L2','L3','L4']])
    supp+='''L1 is D=0..4,b=2,g in [0,1/2],bit0=1; L2 adds g=1/4 and minimizes visits. L3 is D=0..8,b=4,g in [1/8,1/2],bit0=1,bit1=0. L4 uses the L1 domain with fixed g=1/4. All twelve solve positions qualify. In addition, C++ solver-free checks cover nine selected domains, 489 partial conditions, empty/all-fixed codes, fixed and narrow g, path mappings and int-capacity bit boundaries. Complete actual-row/bound/type/objective Start checks include fixed positive and narrow positive g with a loaded return, without more Optimize calls.\n\nThe four tiny physical MIPs use R_abs/D167 on the inherited nonzero internal-stock instance and its S=0 fixed-inventory path. R_abs state weights are continuous and its delta bits integer; D167 uses its same conserved path/code block. Original physical integer types remain. The independent C++ oracle enumerates inventories and route orders under empty departure, capacity three, sixty-second pickup/drop and T=360s. It gives optimum .15 at stock (1,1), with one unit returned and 240s handling. The S=0 path fixes stock (0,0), gives objective .3 and returns three units. All four native optima agree with those physical results, and LP-to-MIP type restoration is checked without auxiliary solves. The old independent-zero controller proof is reused as unchanged evidence rather than rerun.\n\nThere are exactly 88 actual serial Optimize calls: 72 canonical LP, 12 local LP and four tiny MIP, leaving all eight reserved repair slots unused. The sole summary-reader error requested a canonical mask field on local rows; it was repaired read-only after healthy producers, with zero solver reruns. The pre-Optimize source boundary repair and prepared-source/PE identity are retained separately from the final measured driver. Recorded C++ subprocess outer fees sum to 126.261657s and Native Runtime sums to 31.346999s, nested inside those fees. Conservative management-inclusive window and independent offline-check costs are recorded in the final cost report. No 96-call or 3600s cap is reported as consumed work.\n\nThe decision retains uniform B and keeps C166/D167 default off. D167 proves and implements the conditional object, but the three modest gains and larger matrices give limited immediate motivation for complete integration. A future comparison would need an acceptable faithful implementation and independently paid complete-method evidence; local ideality and log scale alone do not supply that case.\n'''
    save(PAPER/'supplement.md',supp)
    counts=read(OUT/'manuscript_word_counts.json');counts.update(after_whitespace_words=len(body.split()),
        sections=[dict(heading=s.splitlines()[0],words=len(s.split())) for s in re.split(r'(?=^## )',body,flags=re.M)])
    write(OUT/'manuscript_word_counts.json',counts)
    print('Final current-body whitespace words',len(body.split()))
if __name__=='__main__':apply()
