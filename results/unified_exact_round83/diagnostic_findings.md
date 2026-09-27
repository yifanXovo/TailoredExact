# Frozen prototype result

All eight structural/oracle fixtures and all five fixed-witness processes pass
at prototype source13bf7a5317220ea60a283e814aefbf77245de1fd. No failed run,
recompile, retry or Optimize. Driver wall7.489758s includes compile5.603660s,
processes0.328s and independent offline replays1.479569s (rounding applies).
Full identities and all selected transitions are in diagnostic/v1. Preserve
these before source integration; do not rerun the prototype against later core.

|Role|Initial F|Final F|Exchanges|Relocations|Insertion/quantity|
|---|---:|---:|---:|---:|---:|
|U6|.214430471758|.178390957548|24|1|1/42|
|D6|.157849712515|.157083131103|13|0|0/2|
|D7|.300543518294|.271177227019|3|0|0/12|
|E8|.022295597484|.022295597484|0|0|0/0|
|N12|.879835617333|.879835617333|0|0|0/0|

U6 G .093736757064 -> .053364780104 while unscaled penalty .804624764624 ->
.833507849628. Pickup/drop176 ->189; maximum route duration13872.148 ->11088.156.
Thus improved objective is predominantly Gini with a penalty tradeoff. D6's
small improvement and both small nulls stay visible. All five declare local
exhaustion without deadline/verification failure. The results support testing
actual integration, not a claim of full exact performance or U6 repair.
