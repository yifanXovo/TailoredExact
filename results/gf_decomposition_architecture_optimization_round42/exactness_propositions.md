# Round 42 exactness propositions

1. **Gap-free segmented union.** If ordered segments start at the union lower
   endpoint, end at its upper endpoint, and adjacent endpoints agree within the
   certificate tolerance, their disjunction is exactly the union. Rejected
   geometry never reaches a backend.

2. **One-hot selector equivalence.** Exactly one feasible selector is one, and
   infeasible selectors are fixed to zero. Thus every integer model point
   belongs to exactly one valid segment and every valid segment point has an
   embedding in the block.

3. **Core perspective exactness.** At integral selectors and inventory bits,
   the selector-bit activation and selected G-bit product blocks equal their
   intended products. Sum-back rows recover the original G, bits, and products.

4. **Exact common-row factoring.** A coefficient-identical row present once in
   every segment is unconditional when RHS values agree. With a shared LHS and
   sense but varying RHS, a selector-weighted RHS row evaluates to exactly the
   active segment row. All nonqualifying rows remain conditional.

5. **Hierarchical selector equivalence.** Lower/upper half binaries linked to
   sums of the four leaf selectors introduce no new leaf assignment and remove
   none; they only provide a redundant exact search hierarchy.

6. **Paired cover certificate.** Native-exact closures for the two adjacent
   quarter-pair models provide valid component bounds for their gap-free K4
   cover. The union lower bound is their minimum. The union is strict only if
   that minimum equals an independently verified original-space objective;
   an individual higher-G component is not mislabeled as an original-problem
   certificate when its retained decoded route belongs to another component.

7. **Atomic sibling replacement.** Replacing two exact live terminal-ready
   siblings by a union leaf initialized at their minimum valid lower bound
   preserves both coverage and the scheduler global lower bound.

8. **Unresolved union semantics.** A native bound for a segmented union is a
   bound on the union minimum. Storing it only on the union object is valid;
   assigning it to either original child is not required and is forbidden.

9. **Fail-closed fallback.** Until model and native-result validation succeeds,
   original sibling objects are not replaced. Any failure reopens them, so no
   region or bound is lost.

10. **Strict original-space certificate.** A block or external tree is strict
    only after complete coverage, exact required native closures, valid and
    monotone bounds, parameter/lifecycle gates, original-space route decoding,
    and independent recomputation of the original objective and feasibility.

The C++ test suite exercises arbitrary covers, K2/K4/hierarchical selectors,
perspective truth tables, infeasible fixing, both factoring cases, sibling
identity, atomic replacement, fail-closed rejection, and union-only bound
updates. The pre/post default audit checks that default C6 trajectories remain
byte-stable at the deterministic evidence level.
