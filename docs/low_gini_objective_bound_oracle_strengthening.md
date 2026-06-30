# Low-Gini Objective-Bound Oracle Strengthening

The low-Gini oracle path now records explicit model semantics and allows valid
timeout lower-bound merging. The strongest implemented strengthening this round
is not an additional cut family; it is the switch from treating timeout rows as
diagnostic-only to treating finite CPLEX dual bounds as lower-bound evidence
when the oracle model is an original fixed-interval objective MIP.

Existing safe tightening remains enabled:

- Gini interval rows;
- penalty-domain tightening when a cutoff row is part of the model;
- service-operation consistency;
- vehicle symmetry breaking for identical vehicles.

The result on `moderate_seed3301` shows this is material: the full-frontier gap
fell from the previous `0.8125` frontier floor to `0.0280667552335`. The
remaining open leaves need either stronger exact compact cuts or a real BPC
leaf closure path.
