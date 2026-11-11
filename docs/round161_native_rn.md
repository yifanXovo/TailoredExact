# Full physical reciprocal normalization on the existing carrier

Round161 asks whether replacing the shared-G objective products by reciprocal
normalization is useful when inventory, complete routes, service, loads and
time remain in one Native MIP. The opt-in `Round161Research` target is a
separate default-off entry. Stable GI-TBC/B (S2/ms2), the bare CLI compatibility
default and the E+ reference retain their definitions. R160 neighborhoods are
not used. No instance-name, size, machine or elapsed-time dispatch is introduced.

## Original problem and the common carrier

For n stations, let c_i be the actual binary64 coefficient 1/D_i in the
canonical ratio row, and let x_iy be the existing binary one-hot inventory
selectors over their actual supported values. Write

\[
 Y_i=\sum_y yx_{iy},\quad S=\sum_i c_iY_i,\quad
 A=\sum_{i<j}|c_iY_i-c_jY_j|.
\]

The objective for S>0 is

\[
 J=\frac{A}{nS}+\sum_i\alpha_i|c_iY_i-1|,
 \qquad\alpha_i=\lambda\,\mathrm{weights}_i.
\]

The model objective remains G+sum_i alpha_i e_i. Original r/e links,
absolute-deviation inequalities, e upper bounds and original cutoff/penalty
floor rows remain. There is no state-unary penalty replacement. The actual
matrix registry checks all retained e rows and objective coefficients.

Both formulations are built from the same canonical M-B/VD-P writer with
pair-only physical support. All original route/operation, inventory, service,
direction, load, connectivity and order variables keep their original types.
Original T, empty departure and loaded return/unloading semantics are unchanged.
The only model transformation is the declared old objective module's removal
and RN's insertion. Every unremoved original row and column, including r-only
centering/band information, is compared by its complete named coefficients,
sense, RHS, bounds, type and objective coefficient.

The adapter registers actual inventory selectors, constructs the old
`state_g`, `zprod` and unscaled pair `h` column set, and also registers `W_SP`
when present. Every row consuming those columns is removed, with all its
consumer names saved. Thus h-dependent cap/floor/spread and objective-product
estimators leave with the old module. No unscaled h is renamed as a normalized
one. This is an objective-block comparison, including those old strengthenings;
it is not a one-coefficient intervention or a claim of identical objective
relaxation information. Complete original/actual registries and the exact
removed consumer closure accompany every model.

## Full-scope denominator bounds

Let B=sum_i initial_i, excluding the depot, and Q=sum_k Q_k. Empty departures,
inventory conservation and loaded returns imply

\[
 \max(0,B-Q)\le\sum_iY_i\le B.
\]

This is a bound on final station inventory. Cumulative pickups P can exceed
fleet capacity; total handling includes (tp+td)P. For actual support endpoints
m_i,M_i, the sum-inventory bounds are intersected with sum m_i and sum M_i.
Minimizing S over that box fills remaining units in increasing c_i order;
maximizing it fills in decreasing c_i order. The positive branch additionally
has sum Y>=1. Support holes are relaxed only for this bound computation;
the model retains the original selectors and their holes.

R143/R140's checked common-dyadic arithmetic computes the sums of the actual
binary64 coefficients. It rounds S_L down and S_U up, then the reciprocals
outward, giving t_L<=1/S_U and t_U>=1/S_L. These are mathematical-domain bounds,
not an incumbent's observed denominator. Arithmetic overflow or a missing
positive domain fails closed. No infeasible reciprocal is evaluated at B=0.

## Integer and objective equivalence

In a structurally positive domain add continuous t,w,Yhat,a with

\[
 t_L\le t\le t_U,\quad t_Lx_{iy}\le w_{iy}\le t_Ux_{iy},
 \quad\sum_yw_{iy}=t,
\]
\[
 \widehat Y_i=\sum_y yw_{iy},\quad\rho_i=c_i\widehat Y_i,
 \quad\sum_i\rho_i=1,
\]
\[
 a_{ij}\ge\rho_i-\rho_j,\quad a_{ij}\ge\rho_j-\rho_i,
 \quad\sum_{i<j}a_{ij}\le nG.
\]

At binary one-hot x, all unselected w vanish and the selected w equals t.
Consequently Yhat=tY; normalization gives tS=1. Every feasible RN integer
solution therefore has G>=A/(nS). Conversely any original feasible physical
fleet with positive S lifts with t=1/S, w=tx, Yhat=tY, a=t times the original
absolute differences, G equal to its true Gini and e at its original minimum.
That lift attains exactly the original J. The epigraph permits larger G/e;
auxiliaries need not be unique. This proves integer-domain correspondence and
preservation of minimum original objective, independently of Native OPTIMAL.
Physical integers and binaries are never scaled and then relabeled integral.

The finite caps Yhat_i<=M_i t_U and a_ij<=1 retain every physical lift and do
not change the projected epigraph: rho>=0, sum rho=1 permits the minimum
necessary a<=1. The original selector/G and RN mass constraints imply the
omitted two complementary binary-product facets in the positive domain.

If zero stock is possible, S=0 iff Y=0 because c_i>0. Its Gini is 0 and its
objective is J0=sum alpha_i; route feasibility still belongs to the original
physical constraints. A binary z0 introduces the finite union:

\[
 1-z_0\le\sum_iY_i\le B(1-z_0),\quad
 t_L(1-z_0)\le t\le t_U(1-z_0),
\]
\[
 0\le w_{iy}\le t_Ux_{iy},\quad
 w_{iy}\ge t_L(x_{iy}-z_0),\quad\sum_yw_{iy}=t,
\]
\[
 \sum_i c_i\widehat Y_i=1-z_0,\quad 0\le G\le G_U(1-z_0).
\]

At z0=0 this is the positive construction. At z0=1 the stock link forces
Y=0 and the reciprocal links force t=w=Yhat=0, while G=0. Conversely either
physical branch has the corresponding lift. If the positive relaxation is
empty, the adapter uses the original physical carrier with the single
objective row G=0, computing no reciprocal. Original objective-common rows
are retained only under the same inclusive scope; their completion remains
valid for the true G of both branches. The tiny tests cover a positive-only
domain, an actual zero/positive union and the structurally all-zero case.

## The basic LPs are incomparable

For two stations with c=(1,1), support {0,1}, and 1<=sum Y<=2, fix the
inventory-one masses to (1/2,3/4). RN permits t=3/4, w_i0=1/4,w_i1=1/2,
rho=(1/2,1/2) and G=0. OLD's unscaled absolute difference is at least 1/4.
Its two zprod values are each at most G, so 1/4<=2(zprod_1+zprod_2)<=4G.
The bound G>=1/16 is attained by zprod_1=zprod_2=G=1/16 and the corresponding
zero-state G masses equal to zero. All old product/mass bounds hold.

For the already stored R143 three-station example, c=(1,1,1), support {0,1},
1<=sum Y<=2 and one-state masses (1,1/2,0), OLD permits G=1/3 and products
(1/3,1/3,0), with pair-difference sum 2. RN has t in [1/2,1],
rho=(t,1-t,0). The middle zero-state w=2t-1>=1/4 implies t>=5/8;
pair sum=2t implies G>=5/12. Equality is attained by w rows
(0,5/8), (1/4,3/8), (5/8,0). Exact Fraction checks verify the witnesses.

These are selector/G projection witnesses for specified objective/stock
subblocks, not strict separation theorems for every complete routing LP.
The common penalty can use the same e at each fixed selector point. The
stronger old+RN intersection in R143 is a different comparison. Normalizing
does not imply a smaller formulation: with K states and p pairs, K old
state_g, n zprod and p h are replaced by K w, n Yhat, p a and t (and a
zero indicator when needed). Actual sizes and coefficients must be measured.

### Fixed-denominator limit and reciprocal slack

There is a useful elementary limit to this non-dominance. On a positive
domain with S fixed, t_L=t_U=1/S makes w=tx even at fractional selectors.
RN then gives the exact convex fractional-inventory epigraph
G>=A(Y)/(nS). Every such point lifts to the old *basic* objective block with
state_g=Gx, zprod=GY and h=|c_iY_i-c_jY_j|. Thus RN dominates that basic block
in this limit; this statement excludes the old optional strengthenings.

On the positive block z0=0, for a nondegenerate envelope let delta_i=rho_i-t*c_iY_i and
p_i=c_iY_i/S. Normalization gives 1-tS=sum delta_i, hence
||p-rho||_1<=2 sum |delta_i|. The unit-sum Gini functional has L1 Lipschitz
constant (n-1)/n, so

\[
 G\ge \frac{A(Y)}{nS}
       -\frac{2(n-1)}{n}\sum_i|\delta_i|.
\]

At each station the pairs (x_iy,w_iy) describe a distribution of inventory
values and conditional reciprocal values in [t_L,t_U], with reciprocal mean
t. Therefore delta_i is c_i times their covariance. Cauchy–Schwarz and the
range variance bound give

\[
 |\delta_i|\le\frac{c_i(M_i-m_i)(t_U-t_L)}4.
\]

This bound vanishes at a fixed denominator and the actual covariance vanishes
at integer selectors. It can be loose for a broad envelope. It explains a
specific structural question: can the *existing* stock/penalty/physical scope
bound reciprocal distortion tightly enough to matter, without introducing
a denominator-partition controller? It predicts neither Native performance
nor dominance for a general full model. The offline saved-point diagnostic
tests one original-penalty implication without Optimize; it is not an
automatic rescue direction or a new cut-combination experiment. These are
elementary relaxation observations, not a separate originality claim.

## A complete Native domain and proof transport

The original GI intervals directly restrict the common factor G in the old
products. RN's factor is t, so copying that controller would introduce another
research question. This study instead solves one complete Native MIP over
the original inclusive improvement domain supplied by its own initial U0:
0<=true G<=min(U0,(n-1)/n), J<=U0, with outward bounds and epsilon=0.
OLD and RN receive the same cutoff, support and G bounds. There is no AM,
bound target, split, restart or dynamically rebuilt external model.

The existing PaperTerminalMip backend supplies parameter readback, original
route decoding and validation, source/model identity and witness consistency.
Native parameters retain Seed0, Threads1, MIPFocus0 and the inherited zero-gap
and numerical policies. Development alone has the explicit 4096-node limit.
Every complete candidate would remove that development limit.

A qualified restricted lower ell on the complete J<=c region transports as
min(ell,c), using the cutoff complement. If represented as disjoint physical
branches their regional floors must first be combined by minimum. A separate
same-domain proof-only floor may then be combined by maximum. The single
zero-indicator MIP already covers the complete union. Any source/witness
contradiction revokes that source; an unclosed gap remains OPEN.

## One uniform revision from the existing penalty budget

The core bridge is followed by one evidence-backed RN-P revision. The exact
saved-point diagnostic raises the full-scope S lower bounds from 8.6111111
to 11.0011452 on RX35 and from 14.8444444 to 21.3915926 on NB35. The resulting
w envelopes exclude both saved core RN optima, by about .00497 and .00625.
This is evidence for testing a narrower envelope, not proof of a new optimum
or faster integer search.

The original common rows imply sum alpha_i e_i<=c and e_i>=|r_i-1|.
For ratio-box endpoints l_i=c_i m_i and u_i=c_i M_i, put
b_i=clip(1,[l_i,u_i]) and P0=sum alpha_i |b_i-1|. Starting at b, minimizing
sum r spends the remaining penalty budget c-P0 on decreases b_i-l_i,
in increasing alpha order. Maximizing sum r spends it on increases u_i-b_i
in the same order. A zero alpha permits a free full change. This continuous
fractional knapsack is exact for that penalty-only box; support holes,
stock and routes are relaxed in this calculation. Intersecting its S bounds
with the independently valid stock-box bounds remains valid for the original
complete scope. It need not solve their joint relaxation exactly.

The C++ revision reads alpha directly from each original e objective
coefficient, already including lambda. Checked common-dyadic arithmetic
represents ratio endpoints, alpha, complete-item costs and remaining budget.
For the final partial item, the available budget, division and endpoint
conversion are rounded outward. The revised t/w/Yhat bounds and w envelope
coefficients are changed; no original penalty, physical row, support, cutoff
or Native parameter changes. The initial scope remains fixed after new
incumbents. This is a single declared expression revision, applied uniformly
from input coefficients and the same initial cutoff.

The two affected LP/MIP pairs use RN-P. The unchanged OLD controls were paid
in the core phase and are explicitly reused. Their new export is identical
in full model/Start bytes and both Native-backend/mapper object files are
byte-identical. The executable differs because of the adapter revision;
this is not labeled a fresh same-PE OLD/RN-P panel. Both core and revised
results and their complete costs remain in the report. No second recipe
revision is selected.

## Experiment and interpretation

The finite bridge uses two fixed, identity-complete own-H parents immediately
after H/R83 and before scope/RN. They are offline development inputs, not
complete performance samples. The matched OLD/RN LPs each allow at most 300s;
four whole-Native MIPs each allow 4096 nodes and at most 900s outer time.
All construction, model conversion/read, validation and output are paid.
Work, Runtime, nodes and wall time are separate observations. Continuous LP
values provide product residual diagnostics without another Optimize.

Results and the evidence-based continuation/stop decision are recorded in
[the R161 report](../results/unified_exact_round161/final_report.md). A complete
E+/N-RN panel is conditional on useful physical U, qualified proof progress or
an explainable search/cost tradeoff. A full-method comparison would additionally
change the outer controller, so its result could not be attributed solely to
the objective expression. The finite bridge has the narrower attribution.

## Attribution

The normalization and bounded binary/continuous products are established
tools. Glover (1975), *Improved Linear Integer Programming Formulations of
Nonlinear Integer Problems*, Management Science 22(4), 455–460,
[doi:10.1287/mnsc.22.4.455](https://doi.org/10.1287/mnsc.22.4.455), is classical
linearization background. Charnes and Cooper (1962), *Programming with linear fractional
functionals*, NRLQ 9, 181–186,
[doi:10.1002/nav.3800090303](https://doi.org/10.1002/nav.3800090303), supplies the
classical linear-fractional normalization background. Yue, Guillén-Gosálbez
and You (2013), *Global optimization of large-scale mixed-integer linear
fractional programming problems: A reformulation-linearization method and
process scheduling applications*, AIChE J. 59, 4255–4272,
[doi:10.1002/aic.14185](https://doi.org/10.1002/aic.14185), describes combining
Charnes–Cooper and Glover linearization in its public abstract; this study
does not claim to have checked that paper's full theorems. Chen and Hooker
(2023), *A guide to formulating fairness in an optimization model*,
[doi:10.1007/s10479-023-05264-y](https://doi.org/10.1007/s10479-023-05264-y),
[author manuscript](https://johnhooker.tepper.cmu.edu/equityGuideAOR3post.pdf),
discusses Gini criteria and mathematical-programming formulations.

The project-specific contribution here is the explicit full physical
integer/zero-domain contract, the precise replacement registry and the
measured complete-carrier comparison. Neither the elementary counterexamples
nor a single formulation benchmark is claimed as a stand-alone OR-level
original result. No main-manuscript TeX was changed.
