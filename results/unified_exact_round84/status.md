# Round84 status

Latest: six runs complete and independently valid. D6 P is open after
3597.187s (gap.006425693916377456), ENS certifies in3171.157s, and K1-R
reaches the whole-run guard at3598.078s with valid committed evidence:
U.15708313110317407,L.1483180363170433,gap.008765094786130773, no certificate.
K1 returns code1 due to the external whole-run stop; it is not a normal return.
D7 P also reaches the whole-run guard at3598.0469999997877s: valid committed
U.2372849915487284,L.19858649317712468,gap.03869849837160372, no certificate.
It returns code1 with1 Optimize start/0 returns;235 physical witnesses,
68 global-bound events and305 commits pass replay in.24535810016095638s.
D7 ENS-C returns normally in3597.186999999918s: U.22515085005563812,
L.20473785631837987,gap.020412993737258245, no certificate. Relative gap is
.09066363165945805 versus P.1630886897608805. Both bounds improve;
absolute gap decreases.018285504634345473 (47.25119941026719%).
Four Optimize starts/returns (3 LP plus parent-domain MIP),52 physical
witnesses,93 global-bound events and154 commits pass replay in.643729000352323s.
Actual startup executes3 exchanges,3 relocations,2 insertions,38 quantity moves
and7519 equal-net pairs; its outer witness matches the final route.
D7 K1-R returns normally in3597.25s: U.21564407531579505,
L.19850842028251278,gap.017135655033282265, no certificate. Six Optimize
starts/returns,1 physical witness,47 global-bound events and61 commits pass
replay in.07675880007445812s. ENS has worse U and stronger L than K1;
its gap is.0032773387039759794 (19.125844314737108%) larger. It retains
84.80099005240418% of K1's absolute-gap advantage over current P. This is
a material K1 gap tradeoff under the frozen rule, alongside the47.2512% P gain.
K1 HGA completes2739 generations at595.0508286s; its first witness is available
at595.2660000002943s. At300s U is unavailable; at600s U is available but L=0.
These are original observed checkpoints, not backdated generation-log values.
There are now4 normal returns and2 valid hard stops,25 Optimize starts/23 returns,
and21158.90599999996s paid in the completed prefix. See d7_completed_comparison.json.
Run7 U6 P-GRB started at1789652202.0036876 in the same original queue.
Its active cost is additional. Final nine-run/Start/replication audits remain
pending; no R84 PR yet and no overall-goal claim. Never restart the producer.
Exact remote preparation/prefix heade1ee5c143 was independently verified.
The syntax-checked binary publisher v3 is prepared but unexecuted; it refuses
use while the campaign lock exists. v2 remains the tested text-prefix transport.
Latest resource read: ordinary usage allowed,80% weekly remaining, no reset call.

Earlier two-run snapshot:

Original nine-arm queue is running, exec session19331 / driver PID48520.
Runs1/2 are complete, normal and independently valid. D6 ENS-C certifies the
original problem in3171.157000000123s:U.15708313110317415,
L.15708313110316996,gap4.191091917959966e-15. D6 P remains open at3600.
This is a current matched certificate gain, subject to final campaign/Start
audits. ENS uses6 returned Optimize calls;4 physical witnesses,3452 global
bound events and3469 committed events pass replay. Current startup has4
exchanges,4 quantity moves,0 relocations/insertions and1161 equal-net pairs;
the outer handoff matches its final route. Per-run replay.12716879975050688s.
Run3 D6 K1-R started at1789637812.5953043. Completed process cost6768.344s,
7 Optimize starts/returns. Keep the original queue running; do not relaunch.

Run1 D6 P-GRB is complete, normal and independently valid:3597.186999999918s,
U.1572411758522922,L.15081548193591474,gap.006425693916377456,not certified.
One Optimize starts/returns,62 physical witnesses,3480 global bound events;
per-run replay.05177119979634881s. Run2 D6 ENS-C started at1789634641.2657506.
The original queue proceeds; whole nine-run campaign/mechanism/replication
audits remain pending. No run is repeated.

Preparation was preserved remotely at5ad3564c2f338737bcb2e65ca31b512c1da14507.
Local later commit871e3b812 retains all transport failures and exact-hash
API recovery. Read publication_recovery.md; no R84 draft PR exists yet.
First arm D6 P-GRB started at Unix1789631043.9638808. The plan/driver/protocol
were committed together at3dae75c03 before launch. Never restart this producer.
Use campaign/active_experiment.json, summary.json and the owned process handle
to recover current progress; an absent summary before run1 closes is expected.

Plan and original input identities prepared before any R84 solve. New branch
codex/round84-ensc-long-protection-replication, base R83 final131d09280a1563243d0201e68367b26baf5079c3 / draft PR144.
Fresh resource read: ordinary allowed,100% weekly remaining. No reset call by
this agent; the external account change is not attributed.

Exactly nine serial arms admitted: D6 P/ENS/K1, D7 P/ENS/K1, U6 P/ENS/K1,
all whole caps3600s, maximum32400s; three zero-Optimize compact exports<=30s.
No new build/qualification/parameter/source/input change. Qualified R83 source
4496078f25c0cdad1cf7a5c39835fd23121e8978 and binary25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e.
Read plan.md and protocol.json. Formal driver refuses an existing campaign.

Fresh preflight1.0566500998102129s includes three compact exports totaling
0.7969999997876585s and zero Optimize. All274 source hashes and both executable
identities revalidate. Keep R83 and earlier producers closed. This
stage is exposed protection/repetition, not new unadapted confirmation. Overall
goal unmet; no main/default merge. Owned E:/codes/ExactEBRP-round66.
