# Round 36 source of truth

The existing repository is authoritative. Round 36 begins on branch
`codex/round36-incumbent-decomposition-causal-study` at the tree represented by
the fetched `origin/main` merge of the completed Round 35 branch. That merge
and the Round 35 head had identical trees when this branch was created.

The validated C6 implementation and default options are the executable source
of truth. Round 35's committed classification and instance manifest are the
only inputs to causal-panel selection. Historical solver results remain
read-only. New HH/SS/BW-P/BW-A artifacts must be stored under this Round 36
directory and must never be substituted for or written into historical result
packages.

Pre-existing modified and untracked files recorded by the initial Git audit
are user work. They are excluded from Round 36 staging and commits.
