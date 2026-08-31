# Round 50 symmetry audit

All 23 frozen fixed-interval states have identical capacities across vehicles within an instance. The v0 formulation already exploits this exact label symmetry with nonincreasing route-use cardinality rows. Pickup and drop operation modes remain directionally distinct; neither candidate changes or identifies those modes.

Iteration 3 tested two alternative exact representatives. S1 orders depot start indices while assigning an unused route rank of zero. Its single allowed revision, S1-R1, orders used routes first and assigns unused routes the terminal rank. For each D state, the model-delta validator independently parsed the LP files and confirmed that exactly `M-1` v0 cardinality rows were removed, exactly `M-1` candidate route-start rows were added, every other row signature was unchanged, and the replacement rows matched the declared formula.

Both candidates produced real gains on several states, but each lost D13's v0 optimality certificate within the frozen 300-second qualification limit. That is a severe regression under the frozen gate. No symmetry change is accepted; vNext retains the v0 cardinality ordering.
