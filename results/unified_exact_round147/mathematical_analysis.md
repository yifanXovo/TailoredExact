# Standalone state-conditioned Gini deviation rows

Round147 reuses the production construction and exact-arithmetic qualifications
of Round146. It changes the experiment and wrapper, with zero new production
rows, variables, source optimizations, controller rules or parameter tuning.
The original objective is still `g + lambda P` and all physical routing and
R134 proof policies remain in force.

Let \(r_i=c_iY_i\ge0\), \(S=\sum_i r_i>0\),
\(A=\sum_{i<j}|r_i-r_j|\), and \(G=A/(nS)\). For any set \(J\),

\[
A\ge \sum_{i\in J,j\notin J}(r_j-r_i)
=|J|S-n\sum_{i\in J}r_i.
\]

Taking the components below their normalized mean and dividing by \(nS\)
proves the classical Gini–Hoover lower bound

\[
G\ge\sum_i(1/n-r_i/S)_+
=\sum_i(r_i/S-1/n)_+.
\]

The equality uses the zero sum of deviations from \(1/n\). This classical
relation is distinct from this project's safe state-conditioned construction.
For each integer selector state \(Y_i=y\), the necessary continuous inventory
box, physical total inventory and actual support give
\(0<D^-_{iy}\le S\le D^+_{iy}\). The low deviation is increasing in the
denominator, and the high deviation is decreasing in it. Therefore, whenever
the positive-denominator scope is proved, every integer physical point obeys

\[
ng\ge\sum_{i,y}(1-nc_iy/D^-_{iy})_+s_{iy},\qquad
ng\ge\sum_{i,y}(nc_iy/D^+_{iy}-1)_+s_{iy}.
\]

At an integer point exactly one selector per station is active; all its
necessary conditional bounds hold simultaneously. The sums are lower bounds
on different components of the same Hoover deviation, rather than a sum of
alternative global lower bounds. The proof uses inventory/support facts and
the original epigraph, and never assumes that the four STOCK RLT rows were
inserted into the formal LP or MIP. GD is consequently valid on stable BASE
with STOCK off. Nonminimal feasible epigraph values remain feasible.

Root coefficients are generated once with the existing directed arithmetic;
infeasible conditional states receive zero coefficients. A globally unproved
positive denominator omits the entire block. Compatible child supports inherit
the same root rows after deleting absent selectors; expanded support is rejected.
There are at most two new rows and no new columns or source solves. The old
writer already tested STOCK-off cases, including positive, fixed and zero-lower
domains. Round147's zero-Optimize reader fixture uses the saved original model
when the production block has zero rows; absence of a suffixed GD file is then
correct. H completion before model construction is a separate valid path.

On a domain with \(S>0\) proved, zero states have low coefficient one, giving
the local inequality \(ng\ge\sum_i s_{i0}\) uniformly over that domain.
It does not apply to \(S=0\), where the existing convention is \(G=0\);
the production positive-denominator scope rule omits GD on an unproved domain.
The inequality closes the R145 half/half binary example (whose \(S>0\))
at \(g\ge1/2\). This is a local integer epigraph result, with no claim about the
complete routing hull or a new general inequality theorem.

On a common fixed continuous domain, write \(P_{00}\) for BASE, \(P_{10}\)
for STOCK, \(P_{01}\) for GD alone, and \(P_{11}\) for their combination.
With the same matrix, objective, support, inventory bounds, epigraph interval
and cutoff, \(P_{11}=P_{10}\cap P_{01}\). Thus minimization gives
\(v_{11}\ge\max(v_{10},v_{01})\ge v_{00}\). No ordering of marginal gains
follows from these containments.

The four numerical K20 values already sealed by R146 are:

| STOCK | GD off | GD on |
|---|---:|---:|
| off | .19514915244120534 | .2360103023423648 |
| on | .20459043917810038 | .2510161099222611 |

The two GD increments are approximately .04086114990115946 and
.04642567074416072; the numerical fixed-domain interaction is
\(v_{11}-v_{10}-v_{01}+v_{00}\approx .00556452084300124>0\).
This is one finite LP fact, not general supermodularity and not complete-search
synergy. Joint+GD K20=.23905218467540965 and the old K35/RX20 optimized
increments and strong-joint same-value witnesses are reused without Optimize.

Full search changes preprocessing, native cuts, branching, AM choices and
incumbent discovery. LP monotonicity gives no finite-wall-clock ordering of U,
external supported L, certification or complete cost. Round147 therefore
examines B→D, S→SD, D→SD and S→D as finite same-PE mechanism contrasts.
Native returned bounds remain separate from external proof-supported L.
Open positions have no T_cert; caps are never substituted for convergence
times or used to fabricate a timing interaction. One seed on known roles
does not establish broad generalization or a unique causal internal mechanism.

Fixed inherited science:
`8ec2aebe46398485019623d9b18a3e30617d4997/results/unified_exact_round146`.
Production source `1f470aa5d6a8289347b9d4323764e6e74fa83b2b` and PE SHA256
`da8fabd315ac6228432b0f3afeba07efef3baf83300e650112d6dcdf9aca2309` remain
unchanged; wrapping and scientific-delivery commits are recorded separately.
