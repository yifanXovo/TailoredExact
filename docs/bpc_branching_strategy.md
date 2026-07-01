# BPC Branching Strategy

The BPC repair round records branching behavior even when no branch closes:

- branch candidates considered;
- selected branch type;
- predicted child bound information when available;
- child node feasibility;
- pricing closure status per child.

Certificate rule: a BPC subtree can close a frontier interval only when every
node used for lower-bound evidence has exact pricing closure.  Branching
heuristics can guide the tree, but they cannot replace exact pricing.

Current implemented branch families remain:

- Ryan-Foster style route co-membership branching where available;
- final-inventory branching;
- operation-mode branching;
- strong/reliability branching controls from the paper-core preset.

This round evaluates whether branching is reached at all.  If pricing cannot
close the root RMP of a target leaf, the bottleneck is pricing/RMP strength
before tree strategy.
