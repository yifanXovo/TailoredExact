# C0 V12 overhead diagnosis

The retained V12 audit contains 0 C0/C1-equivalent leaf events.
Repeated same-leaf processing accounts for
0 events, with median
per-event Work 0.  The Round 26 controlled
forensics remain authoritative: V12_M1's small wall regression was timing
noise, whereas V12_M2 used six reads/fresh restarts, eight optimize calls and
five observed root relaxations at the median.  Its hard parent received the
30/60-second sequence before splitting, and a child repeated it.

The transferable lesson is to harvest a validity-gated native bound and define
the next state by a mathematical bound milestone.  Repeating because a time
quantum expired or because the attempt ordinal equals two is forbidden.
