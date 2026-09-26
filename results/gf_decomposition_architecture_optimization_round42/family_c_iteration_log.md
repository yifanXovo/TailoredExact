# Family C iteration log

## Base: C6 sibling Core

All 10 development rows exercised the unchanged C6 scheduler before terminal
closure. Coverage and lifecycle audits pass with zero false certificates. On
the major witness, two sibling pairs are coalesced, four terminal leaves are
replaced, and counted integer proof jobs fall from 8 to 4. One union remains
unresolved at the shared cap; Work is 1.031932x C6 and the candidate correctly
refuses a strict certificate, creating one certificate regression. The
strongest control remains certified but regresses to 1.489296 Work and 1.468462
shifted time.

## Required refinement: C6 sibling Core factored

The same structural trigger with uniform exact factoring reduces major Work to
0.962999x but still reaches the cap (1.000028 shifted time) with the same honest
certificate regression. The strongest control remains certified but uses
1.421817x Work and 1.508178x shifted time. Family C is rejected. The unresolved
union retains a union-only lower bound; no bound is copied to either child and
no coverage is discarded.
