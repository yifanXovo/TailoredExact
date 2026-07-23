# C3 pruning failure analysis

C3 processed 4107 complete interval LPs across completed official rows
and recorded zero LP-bound prunes. Approximately 3290 LPs
(80.1%) strictly improved their
inherited leaf bound, but improvement usually remained below the verified
incumbent cutoff and therefore did not fathom the leaf.

The structural rule split every eligible improving leaf regardless of the
children's value. Of 2027 evaluable one-level splits, 723
(35.7%) had no strict post-split
controlling-bound gain. These splits increase both future LP count and the
number of exact terminal MIPs without providing immediate pruning evidence.

This is evidence for replacing unconditional refinement with a complete,
uniform child-LP benefit decision. It is not evidence that an LP bound is
invalid, and no child is pruned from this audit.
