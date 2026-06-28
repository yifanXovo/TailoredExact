# high_imbalance_seed3202 Reproduced Baseline

The priority V20/M3 instance was rerun in `results/v20_exact_certificate_round`
with the mip-light compact-flow relaxation and native HGA-TGBC incumbent.

Result:

- status: optimal
- objective/LB/UB: `1.74931345205`
- runtime: about `409.8s`
- unresolved intervals: `0`
- open nodes: `0`
- route-mask all-subset enumeration certifying: `false`
- certificate basis: relaxation-only full-frontier ledger

The run improved over the previous best noncertified mip-light 1200s evidence
because the current relaxation scheduling/fathoming sequence closed the final
frontier leaves directly.  No focused interval merge was needed for this
certificate.

