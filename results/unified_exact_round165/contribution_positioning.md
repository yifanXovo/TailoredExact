# Contribution and evidence map for the current manuscript

The research contribution is an integrated exact method for the inherited
inventory-equity routing problem, together with a useful distinction between
inventory representation, valid proof information and paid physical search.
The current evidence supports finite certification and endpoint advantages
over the specified compact controls. It does not identify a separate speed
gain from the outer Gini controller. This limitation was already disclosed in
the maintained manuscript; the present revision makes the complete research
account readable and current rather than claiming its discovery.

| Claim and object | Premises | Closest established work | Specific connection here | Evidence and scope |
|---|---|---|---|---|
| Shared finite inventory state for products, movement and visits | Bounded integer final stock; unique nonzero one-way service | McCormick (1976); Gupte et al. (2013), single integer-continuous products; Köppe et al. (2008), value-disjunction linking/aggregation | The same stock selector represents the objective product and the absolute inventory change and service indicator | Main §3.1; Appendix A.3–A.5; matched A/B deletion roots and complete costs. An isolated VD-P product has the McCormick rectangle projection; the linked route model is not a route convex hull. |
| Implicit integer service | Integer initial/final stock, unique vehicle assignment, binary direction and inventory balance | Standard integrality implication from a fixed integer difference; related BRP formulations use different visit/service conventions | Continuous pickup/drop quantities recover the inherited integer physical operations under these specific conventions | Lemma 1/A1 and the full physical embedding. It does not require the A/B equations and is not a theorem for arbitrary BRP. |
| Ordered supply and support/handling information | Empty departure; nonnegative prefix loads; nonzero integer service; metric travel; return unloading paid | Standard metric shortcutting, conservation, activation and conditional valid inequalities; Erdoğan, Bruck, Bulhões and Schuijbroek provide the operational context | Collected units must precede their delivery; support size implies cumulative pickup at least ceil(|W|/2), while Q still limits prefixes only | Proposition 1, A6–A8; static pair rows in the canonical writer. Triples are documented but disabled. Root and runtime increments are conditional and mixed. No new general cut-separation theory. |
| Complete true-Gini interval method | Objective-preserving true-G embedding; inclusive cutoff; applicable scoped lower bounds; full split coverage | Established spatial partitioning, mixed integer bilinear reformulation and branch-and-bound reasoning | True-G allocation, cutoff-complement floors and the full-cover minimum fit the physical inventory/service model and the implemented continuation rules | Proposition 2; A.6; complete B.0–B.11. Guards select an exact terminal continuation, or leave OPEN. Gurobi supplies native branch-and-cut; custom rows are static. Numeric qualification is distinct from rational proof. |
| Proof-only inventory versus physical realization | Matched domains, original objective and qualified independent floors; own H and all helper cost paid | Standard convex epigraph/Jensen and inventory relaxation tools; direct HGA-TGBC model/decoder antecedent | A stock value is a lower-information source; an upper requires legal routes, quantities and prefixes. Tight pricing alone cannot allocate the complete gap | Main §§3.5/6.4; mathematical analysis; R138–164 positive/mixed/adverse evidence. E+ raises one of six final lowers in R163, without an extra certificate. |
| Integrated complete-method competitiveness | Original U/L, independent cold P and own-paid-start PS; matching version/input/weight/T/cap/Seed; qualified lifecycle | Compact binary-product formulation (P); same own-H compact control (PS) | Compare the entire B package rather than native Runtime or a component proxy | R137 breadth B9/12, P7/12, PS7/12; resource B4/8 versus 0/8; separate six-input cohort B3/6 versus P1/6 at each of three Seeds. No pooled success rate, full-over-root advantage, or universal primal dominance. |

The nearest-source reading and access boundaries are recorded in
[literature_review.md](literature_review.md). The direct same-problem
HGA-TGBC manuscript retains attribution; its private text is not published.

The actual new work is the coherent one-paragraph abstract, the explicit
main algorithm, results-before-mechanisms organization, a data-bound
three-Seed endpoint figure and arrival table, current source mapping,
targeted primary-source checks, and a reproducible assembly/export/QA path.
No algorithm, formal performance observation or mathematical theorem is
introduced by these document changes.
