# Direct Gini deviation rows on discrete inventory states

Round146 research section, 2 November 2026. This section extends the stable
Round137 GI-TBC manuscript with a finite study of a default-off mechanism.
The complete routing model, physical objective and original proof policy
remain unchanged. All roles are known research configurations, not an
independent validation set.

## 1. From shared resource information to direct deviation rows

The earlier studies distinguish relaxation information from complete search
value. STOCK retained real certificate benefits: K15 improved from about
112.77 to 33.82 seconds, and K20 certified in about 101.64 and 90.23 seconds
on the two tested seeds while the matched BASE runs stayed open at cap1200.
The second seed has the disclosed V2 coefficient-transport identity; it is
not a pure seed-only intervention. Later count and reciprocal-normalization
studies established complementary information without uniform full-method
promotion. Those positive results remain part of the evidence.

In Round145, K35's joint NC/TS/RN LP value .234508197894 exceeded the strong
RN+STOCK+TC+TC2 value .229222197461; adding the old carrier to joint did not
raise it further. Compiled compact projections lost only about
\(2.75\times10^{-14}\) and \(1.73\times10^{-14}\) on the two tested domains.
However, four same-PE pairs and a K35 RN-P bridge did not justify adoption.
RN-JP improved K35 U against OFF but weakened its supported L/gap; old RN-P
was better at both endpoints. K20 weakened L, RX20 gave no material time
gain, and RB35 had an important U/gap regression. These complete negative
results coexist with the structural theorems and root-value preservation.

The present question is whether a classical normalized-deviation principle
can supply useful integer-objective information directly on the existing
selectors, without an RN source solve, dual projection, callback, extra
variable or new controller. Gini and Hoover/Pietra are established indices
[@ChenHooker2023, section 4.2]. No new general inequality theorem is claimed.

## 2. Validity and the state-conditioned construction

Let \(r_i=c_iY_i\ge0\), \(S=\sum_i r_i>0\), and
\(A=\sum_{i<j}|r_i-r_j|\). The project Gini is \(G=A/(nS)\), and the
original epigraph variable satisfies \(g\ge G\). For any station set J,

\[
A\ge\sum_{i\in J,j\notin J}(r_j-r_i)
=|J|S-n\sum_{i\in J}r_i.
\]

Choose the components below their normalized mean and use
\(\sum_i r_i/S=1\). This proves the classical bound

\[
G\ge\sum_i(1/n-r_i/S)_+
=\sum_i(r_i/S-1/n)_+.
\]

With global bounds \(0<S^-\le S\le S^+\), this gives the integer-valid
original-selector rows

\[
ng\ge\sum_{i,y}(1-nc_iy/S^-)_+s_{iy},
\qquad ng\ge\sum_{i,y}(nc_iy/S^+-1)_+s_{iy}.
\]

The conditional construction below strengthens the denominator bounds
without adding rows or variables beyond these two.

At a supported state \(Y_i=y\), take valid conditional bounds
\(0<D^-_{iy}\le S\le D^+_{iy}\). The physical stock interval is
\(B^-=\max(0,B-\sum_kQ_k)\le\sum_jY_j\le B\). Fix \(Y_i=y\),
start the remaining inventories at their support minima, and fill to the
smallest admissible total in increasing \(c_j\) order for the minimum.
Fill to the largest total in decreasing order for the maximum. Nonnegative
costs justify these choices. Replacing holey supports by their interval
boxes enlarges the domain, so the extrema remain safe bounds; they are not
claimed as exact discrete-support extrema.

The two direct state-conditioned deviation rows (GD-state) are

\[
ng\ge\sum_{i,y}\left(1-\frac{nc_iy}{D^-_{iy}}\right)_+s_{iy},
\qquad
ng\ge\sum_{i,y}\left(\frac{nc_iy}{D^+_{iy}}-1\right)_+s_{iy}.
\]

The low deviation increases with its denominator; the high deviation
decreases with it. At an integer point each selected state's conditional
bound applies at the same point. The coefficients lower-bound individual
Hoover deviation terms, which can be summed. This does not sum independent
full-Gini lower bounds. Conditional domains are subsets of the global
domain, so ideal conditional coefficients dominate the corresponding
global-bound coefficients termwise. An infeasible necessary state box
receives zero coefficients; this study adds no state-removal mechanism.

If the whole root domain lacks a proved positive denominator lower bound,
both rows are omitted, preserving the existing all-zero convention.
Otherwise a zero ratio is allowed and contributes one to the low deviation
at its supported states. The objective remains the original
\(g+\lambda P\), including the old penalty and constant.

## 3. Numerical transport, scope and a simple local hull closure

The production implementation uses existing checked exact dyadic arithmetic
for the actual loaded binary64 ratios, inventory units, water-fill sums and
\(nc_iy\). Lower denominators are converted downward and upper denominators
upward. The low coefficient uses an upward enclosed ratio followed by a
downward subtraction; the high coefficient uses a downward enclosed ratio
and subtraction. Tiny positive coefficients below 1e-12 are omitted, which
only relaxes the row because selectors are nonnegative. The coefficient n
on g and each feasible zero-state low coefficient one are exact.

There are at most two rows and no new variables. Root coefficients are
computed once and inherited only with identical input SHA, actual ratios
and physical stock interval and with a subset of the original selectors.
Removed selectors are identically zero, so their terms are deleted.
Expanded support or changed input/ratios/stock is rejected. No root LP,
dual or stored solution is used to generate these coefficients. The
generation timer measures the coefficient routine; complete outer clocks
also pay support parsing, file transport, Native audit and verification.

If z stations have zero inventory, zero-positive pairs give \(A\ge zS\),
and therefore \(ng\ge z=\sum_i s_{i0}\). The low GD row contains this
simple inequality. In the Round145 equal-cost binary-support family,
stock in [1,n-1] and fixed half/half selectors imply \(g\ge1/2\), which
attains that local integer Gini epigraph hull. It closes the joint value
\((3n-4)/(2n(n-1))\). The earlier strict complementarity result remains
valid, but its remaining gap does not establish a need to reconstruct a
more elaborate joint integer hull. This is not the full routing hull.

Eight exact-oracle fixtures cover heterogeneous and zero ratios, support
holes, fixed states, infeasible states/domains and all-zero domains. Actual
canonical/Native checks cover both rows, unchanged default-off matrices,
strict sub-support inheritance, changed-scope rejection, and complete
physical Starts with minimal and nonminimal g. Three affected production
translation units were rebuilt. One short complete health run and the
inherited physical/proof/lifecycle verifier qualified the production path.
Independent review corrected only an offline reader's root-file ordering;
the original helper is preserved and no solver run was repeated.

## 4. Saved-point evidence and matched optimization

The supplied preliminary attachment was unavailable locally. Existing
fixed carriers permit an exact reconstruction of the four decision-relevant
saved points, with no Optimize and no point normalization. K20 joint has
positive low/high violations .0258580381333/.0495572135569 despite zero
zero-state selector mass. K35 and RX20 joint optima satisfy both rows,
so they witness unchanged numerical optimal values on those particular
strong models; these two cells were not reoptimized. RX20's transported
compact point has violations .235260517665/.0186545799038.

A saved extension violation, exclusion of the same original point,
optimized objective increment, and complete algorithm improvement are four
different claims. Five new matched LPs retain the full original objective,
matrix, support, g bounds and cutoff, while reusing sealed baseline optima
and solutions. All use Seed0 and one thread. The table gives numerical
continuous optima, not rational certificates or Native root-after-cuts bounds.

| Role | Carrier | Old L | With GD | Increment |
|---|---|---|---|---|
| K20 | base | 0.195149152 | 0.236010302 | 0.040861150 |
| K20 | joint | 0.222808940 | 0.239052185 | 0.016243245 |
| K20 | stock | 0.204590439 | 0.251016110 | 0.046425671 |
| K35 | base | 0.200177662 | 0.204187028 | 0.004009366 |
| RX20-T1 | base | 0.331594316 | 0.365004646 | 0.033410329 |

The K20 STOCK combination reaches .251016109922, above standalone GD .236010302342 and STOCK .204590439178. This motivates one uniform STOCK+GD candidate with STOCK as the complete reference. The direct rows also add optimized information beyond K20 joint and on all three BASE domains. Coefficient generation takes approximately 0.38-1.95 ms in these tests, with 97-405 added nonzeros and no paid source solve. The optional state-level Hoover extension and global/state parameter grids are unnecessary for this decision and are not opened.

## 5. Complete same-PE experiments and the adoption decision

Every entered method pays its own complete H (seed20260626), ordinary root/lookahead, formal search and required verification. Gurobi Seed0, Threads1, affinity4, M-B/VD-P, pair-only support, AM=.08, depth8, minimum width1e-4, AP off and the R134 proof policy remain fixed. Physical route horizons and original lambda values are distinct from experimental caps. Rows apply in formal initial LP, target and terminal models, with complete Starts and the unchanged proof reconstruction.

| Role | Stations/vehicles | Physical T | Lambda | Cap |
|---|---|---|---|---|
| RB35-T2 | 35/3 | 7200 | 0.05512527522 | 2400 |
| K20 | 20/2 | 5400 | 0.15 | 1200 |
| RX20-T1 | 20/2 | 4800 | 0.1267606098 | 1200 |

Three complete same-PE STOCK/STOCK+GD pairs retain the uniform candidate. K20 certifies the same U=.7168065462777502 in 94.261389 versus 74.916420s (20.5227% earlier); total times are 96.931591/77.553682s. RX20 retains U=.6453250303858205 and certification, with a small absolute certificate-clock gain of 2.702614s and total gain of 2.233928s; its extra 0.468686s verification is included. RB35 improves U from 0.401200217839 to 0.377816983545 (5.8283%), L from 0.229181599664 to 0.233498944436, and gap by 4.6781 percentage points. Both RB35 arms remain open after full cap2400 windows; GD verification costs 5.005234s more. The necessary same-PE stable BASE bridge returns U/L=0.344642625592/0.218985949603. The combination raises L by 0.014512994833 but worsens U by 9.6257% and gap by 1.7379 percentage points versus BASE.

| Role | Method | Verified U | Supported L | Gap % | T cert |
|---|---|---|---|---|---|
| K20 | STOCK | 0.716806546 | 0.716806546 | 0.000 | 94.26 |
| K20 | STOCK+GD | 0.716806546 | 0.716806546 | 0.000 | 74.92 |
| RX20-T1 | STOCK | 0.645325030 | 0.645325030 | 0.000 | 14.76 |
| RX20-T1 | STOCK+GD | 0.645325030 | 0.645325027 | 0.000 | 12.05 |
| RB35-T2 | BASE | 0.344642626 | 0.218985950 | 36.460 | open |
| RB35-T2 | STOCK | 0.401200218 | 0.229181600 | 42.876 | open |
| RB35-T2 | STOCK+GD | 0.377816984 | 0.233498944 | 38.198 | open |

Open certificate times stay null in the data and are displayed as open. Native returned bounds and the external supported L are separate fields. Tiny certified endpoint differences remain under the inherited proof policy; no solver tolerance is changed.

| Role | Method | T produce | T verify | T total |
|---|---|---|---|---|
| K20 | STOCK | 94.26 | 2.67 | 96.93 |
| K20 | STOCK+GD | 74.92 | 2.64 | 77.55 |
| RX20-T1 | STOCK | 14.76 | 1.14 | 15.89 |
| RX20-T1 | STOCK+GD | 12.05 | 1.61 | 13.66 |
| RB35-T2 | BASE | 2371.35 | 3.80 | 2375.14 |
| RB35-T2 | STOCK | 2371.07 | 3.83 | 2374.90 |
| RB35-T2 | STOCK+GD | 2371.09 | 8.83 | 2379.92 |

| Role | Method | Initial LP | Root after cuts | GD NZ |
|---|---|---|---|---|
| K20 | STOCK | 0.204590 | 0.58526 | 0 |
| K20 | STOCK+GD | 0.251016 | 0.58619 | 330 |
| RX20-T1 | STOCK | 0.377558 | 0.53642 | 0 |
| RX20-T1 | STOCK+GD | 0.398702 | 0.54633 | 97 |
| RB35-T2 | BASE | 0.128911 | 0.17634 | 0 |
| RB35-T2 | STOCK | 0.129151 | 0.18287 | 0 |
| RB35-T2 | STOCK+GD | 0.136191 | 0.18634 | 407 |

Printed root-after-cuts values have log precision. They do not equal the initial standalone LP values. Full CSV authorities retain simplex iterations, Work, nodes, splits, Native returned bounds, row sizes and verified physical-witness trajectories. The observed changes are not attributed solely to row density or initial LP strength.

The stable BASE pressure comparison above is newly measured on the same PE; its matching historical R145 endpoints are not reused as a free new experiment. BASE already has U=0.362136826572 at producer time 850.641s, better than the combination's final U. BASE improves again to its final U at 2366.781s; the combination reaches its final U at 2217.750s. Both early and late observations are retained; a near-cap explanation does not erase the observed regression. K20/RX20 have strong same-PE STOCK references but no new same-PE BASE arms. Earlier STOCK certificate gains and the old RN-P K35 gains remain useful historical results with their original identities. K35 is tested here only in the finite LP stage; no complete STOCK+GD K35 or new RN-P bridge was run, so this study makes no claim to replace or improve RN-P's complete K35 performance.

## 6. Cost, identity and reproducibility

New experimental outer cost is 7412.786360 seconds out of 28800; 21387.213640 seconds remain unused. Own H, all solves, qualifications, failures if any and necessary postverification are counted once. Nested LP/MIP runtime and Work are not added again. The five standalone LPs and one short health qualification have separate identities from the complete positions. Build cost is 44.650598 seconds separately; pure arithmetic, authoring, PDF export and public I/O are also separate. Timed runs are serial and do not overlap compilation, PDF export or heavy I/O.

Measured production source is `1f470aa5d6a8289347b9d4323764e6e74fa83b2b`; PE SHA256 is `da8fabd315ac6228432b0f3afeba07efef3baf83300e650112d6dcdf9aca2309`. Actual source/compiler/object/DLL bytes and Git EOL distinctions remain in the source and carrier manifests. The separate research entry is `scripts/paper_s2_gd.py` with `config/gi_tbc_gd_round146.json`; its default research profile selects STOCK+GD, while `--gd off` selects STOCK. The executable research switch itself defaults off. Stable R137 and all prior launchers/profiles and formal manuscript remain unchanged.

Retain STOCK+GD as a research candidate and retain stable R137 GI-TBC as the default. Direct GD provides real original-variable optimized information and useful incremental complete-search benefits over STOCK on all three measured roles. The combination alleviates, but does not eliminate, the important RB35 incumbent/gap regression versus stable BASE. That is a limitation of the selected combination; it is not evidence that adding GD caused the older STOCK regression or that GD alone is useless. The material same-PE pressure regression, rather than tiny certified-bound differences or a small mixed endpoint, prevents stable promotion. Stop this finite full-method expansion after the BASE bridge. No K35 rescue panel, RN-P bridge, extra seed, K15/RX35 boundary run, BASE+GD second full candidate, state-Hoover branch or tuning grid is opened. These additional runs are unnecessary for this adoption decision; unused budget is not an invitation to extend the panel. The evidence is from known configurations and Seed0, so no general dominance, out-of-sample performance or multi-seed robustness is claimed.

This section is suitable for integration into the stable GI-TBC paper and does not add invented authorship, affiliations, funding or global fractional-integer-programming claims. Source/raw publication, public byte/member recovery and the Draft PR are separate delivery checks; public recovery performs no Optimize, compilation or commercial Native loading.
