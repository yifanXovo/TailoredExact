# Logarithmic encoding of the inventory disjunction

For a station with proved integer domain {L,...,U}, set N=U-L+1. Keep the VD-P
selectors s_y>=0 and perspective variables q_y, and its equations

    sum_y s_y=1; Y=sum_y y s_y;
    gamma_L s_y <= q_y <= gamma_U s_y;
    sum_y q_y=G; Z=sum_y y q_y.

Remove only selector binary declarations. With B=ceil(log2 N), introduce
binary code_j for j=0,...,B-1 and impose

    code_j = sum_y bit_j(y-L) s_y.

Use the natural binary encoding of the domain offset uniformly. N=1 needs no
code variable. Keep original Y integrality, penalty epigraph, route/operation
constraints and all interval/cutoff rows. No VD-J penalty equality is added.

If code_j is zero, every positive selector must have that bit zero; if it is
one, every positive selector must have it one, because the selector weights
sum to one. The code is injective on allowed states, so integral codes force a
unique selected y. Unused binary patterns have no feasible selector vector.
The remaining VD-P equations then give q_y=G and Z=GY at that state. Conversely
every allowed original integer inventory has its unique code and one-hot
extension. This proves original decision/optimal-objective correspondence
conditional on valid propagated domains and each valid interval/cutoff. Empty
departure, loaded return, recycled capacity and zero handling remain unchanged.

The encoding itself imposes no travel assumption. The retained controller's
direct route-derived domains require metric travel lower bounds, however. The
new research presets explicitly reject nonmetric/asymmetric matrices before
HGA/optimization; the supplied Euclidean development family meets this scope.
General nonmetric qualification of inherited cuts remains open. Zero handling
also exposed an inherited domain bug, repaired before performance; see
preflight_issue_1.md. Do not confuse component equivalence with validity of
every retained strengthening on a broader input class.

When codes are relaxed, any VD-P LP selector vector defines code values in
[0,1]. Conversely dropping the code equalities/variables gives the VD-P LP.
Thus the projection onto all common original/VD-P coordinates is identical.
This does not assert an integer hull for the route-coupled problem, numerical
identity of native LP solutions, or better runtime. Original Y integrality alone
would not suffice: mixtures of different integer states may have integral mean
Y while failing Z=GY. The code variables are essential for exactness.

Compared with VD-P, add sum_i B_i continuous-relaxation rows and variables, turn
sum_i N_i selectors continuous, and add sum_i B_i binary declarations. The
encoding may alter branching, presolve and outer decisions in either direction.
Full paid solver evidence, not binary count or root value, decides its value.

Primary literature bounds the novelty claim: Vielma and Nemhauser,
[Mathematical Programming128 (2011),49-72](https://link.springer.com/article/10.1007/s10107-009-0295-4),
and Vielma, [Embedding Formulations and Complexity for Unions of Polyhedra](https://arxiv.org/abs/1506.01417).
Publisher/author abstracts were checked; no full-paper review is claimed. The
special-case proof above is explicit. No new general disjunctive theorem,
speed theorem, or strict rational certificate is claimed.
