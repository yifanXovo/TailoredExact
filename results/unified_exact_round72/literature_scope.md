# Focused positioning check during the frozen long campaign

This check concerns constituent techniques and theorem scope. It changes no
algorithm, experiment cap, input or admission criterion. Checked2026-09-15.

Li, Szeto, Long and Shui (2016), *A multiple type bike repositioning problem*,
Transportation Research Part B90,263–278, already combine hybrid genetic route
search with a greedy procedure for loading/unloading decisions. Their model
has multiple bike types and substitution/occupancy decisions. This supports
treating hybrid route search plus greedy decoding as established ingredients;
it does not establish implementation provenance or equivalence to this repo.
The publisher abstract and author-affiliated bibliographic record were inspected.
[Publisher](https://www.sciencedirect.com/science/article/pii/S0191261516302867),
[author-affiliated record](https://scholar.nycu.edu.tw/en/publications/a-multiple-type-bike-repositioning-problem/).

Szeto and Shui (2018), *Exact loading and unloading strategies for the static
multi-vehicle bike repositioning problem*, Transportation Research Part B109,
176–211, derive fixed-route loading strategies for a lexicographic objective:
excess demand dissatisfaction first, then service time. Their Section2.1 assumes
the depot stores no bikes and each station is visited exactly once. The
abstract, introduction and model setting were inspected in the open author
repository PDF. These are objective/domain-specific results.
[Paper](https://hub.hku.hk/bitstream/10722/259227/1/content.pdf),
[repository record and DOI](https://hub.hku.hk/handle/10722/259227).

For this project, the objective couples all final ratios through normalized
Gini plus weighted target deviations; optional visits and loaded returns also
matter. Consequently, the2018 fixed-route optimality result cannot simply be
imported as a proof that the current greedy decoder is optimal. That is an
inference from the different stated objectives/domains, not a counterexample
to the paper. Any future exact operation subproblem would need its own proof
under the current contract. Present DS-X uses decoder output only as physically
verified UB and retains complete Gurobi proof obligations.

The current contribution is therefore the scoped implementation, cost/coverage
discipline and measured exact-solver behavior, not an invention of genetic
search, greedy loading, relocation, one-hot encoding or native MIP Starts.
The broader sustained performance claim still depends on D7 and confirmation.

A2023 target-based service-efficiency/equity PDF at NUS appeared in search,
but subsequent content retrieval timed out. Its technical results are not used
in this positioning conclusion. This focused two-paper check is not a claim
that all related algorithms or novelty questions have been exhaustively settled.
