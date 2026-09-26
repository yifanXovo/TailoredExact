# Envelope ablation

The frozen Round 44 no-adaptive/no-envelope control is the causal source. It
separates affine-envelope strengthening from the removal of recursive splits.
Both help on some rows; the major regression repair is mainly a timing effect,
while envelopes provide secondary LP strengthening. No Round 45 decision used
runtime outcomes from this ablation.
