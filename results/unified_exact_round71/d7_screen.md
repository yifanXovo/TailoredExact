# D7 screen: cross-route benefit, insufficient K1 protection

All four arms were predeclared at a common 1200s cap before implementation
and have completed. Full physical/model/Start/coverage/trajectory and delivery
audits pass. No run is replaced or extended. These are exposed development
roles, without independent confirmation or new long-window evidence.

|Arm|Paid seconds|Verified UB|Global LB|Signed gap|Certificate|
|---|---:|---:|---:|---:|---|
|P-GRB|1197.078|0.27732086593398886|0.1972864787145512|0.08003438721943765|No|
|DS|1197.109|0.31895879908690944|0.20407715858329653|0.11488164050361291|No|
|DS-X|1197.109|0.2783352667791633|0.20414629462573686|0.07418897215342646|No|
|K1-R|1197.125|0.21564407531579505|0.1973574792283258|0.018286596087469242|No|

DS-X reduces the DS gap by about 35.4%, materially under the frozen criteria.
It reduces P's gap by about 7.3%, below the required 10% relative threshold.
The P comparison is mixed: DS-X UB is worse by0.001014401 and LB is better
by0.006859816. Thus the material DS regression has narrowed to a small net
P gap advantage in this window, without establishing substantial P superiority.
K1 protection is not preserved adequately in this window. DS-X gap is about
305.7% larger than K1-R: UB worsens0.062691191 while LB improves0.006788815.
K1-R improves on P by0.061747791 absolute gap; DS-X preserves only about9.5%
of that advantage. This is a serious loss of a meaningful K1 benefit alongside
a below-threshold P advantage, not a veto for missing a historical fastest time.

DS-X startup costs9.3804927s, compared with DS about2.83s. Its independently
verified initial route has F0.5445105902163795, G0.2273990839816184 and penalty
sum2.1140767082317407;39 stations,166 pickups,157 drops and legal return load9.
DS initial F0.6945633798694341 serves33 stations,144 pickups,127 drops and
returns17. The new startup completes24 seeds,371 passes,2355 decoded checks
(2243 uncached decoder calls), generating2142 cross-route candidates and
actually checking298/accepting178. Full terminal/strict trace audit passes.

The retained initial route hash998b45d335de86ee9093d6ad1d9392bfaeabd531950d0d0110d8a6e25306a569
matches a verified published event. A separate light comparison confirms DS's
164-pass logical startup trace matches Round70, excluding timing and newly
added cross-route counters. This does not equate complete solver searches or
permit pooling historical times with this fresh matched screen.

DS-X's final witness serves48 stations, picks215/drops212 and legally returns3;
maximum duration17952.562761289235 is within the original T18000. Final
G0.08309292884690324 and penalty sum1.3016155862150662 differ from P's
G0.09989121031469565 and penalty1.1828643707952866. Original inventory and
loaded-return semantics are preserved. The last improved solution occurs
within this same full run; intermediate reports do not backdate that route.

K1-R spends612.4211812s in a completed2739-generation/41479-uncached-decode
HGA search. Its verified route serves all50 stations with228 pickups/drops,
empty return and F0.21564407531579505. The full route hash356124388ee9c761491b4bf926abb98c21b41fdeff8f76b6e388b33af2287170
matches the earlier retained HGA route, but actual time is not corrected or
pooled with history. K1-R makes6 native Optimize calls and retains a5-row
coverage tree with2 replaced nodes; DS and DS-X each make4 calls and retain
one root. Their stronger lower bounds cannot offset K1's stronger upper bound.

The audited stage prefix contains13 performance+6 micro runs,82 actual
experiment Optimize calls and4808.951s paid process wall, with no validity
failure, startup-only deadline or supervisor exception. Qualification remains
separate:49 CTests/39 native calls and95.131s configure/build/test, ten no-opt
exports costing0.797s. The full audit now checks65 witness/model combinations
(26 incompatible Gini intervals),10 eligible/accepted/full-vector-observed
Starts and7 controls. All300 compact artifacts (862130 bytes),199 source files
and10 input settings pass delivery integrity. Twelve conservative300/600/1200
checkpoints retain the documented intermediate-witness/clock limitations.

Screen decision: continue the remaining predeclared panel, beginning with D6.
The new neighborhood executes substantially and materially improves the DS
endpoint while retaining small-instance repairs, satisfying the plan's screen
criterion. The remaining question is whether it preserves D6 and C2/D4 gains
and improves D3; this is not an acceptance of the overall candidate. The large
K1 protection loss remains a required future repair. No extra repeat, parameter
revision, new confirmation or extended run is opened by this decision.
