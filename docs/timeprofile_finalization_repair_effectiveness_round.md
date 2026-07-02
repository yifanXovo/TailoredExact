# Time-Profile Finalization Repair

Wrapper-finalized rows now preserve the best valid progress checkpoint using `best_valid_lb_seen`, `best_valid_gap_seen`, and `finalization_source=wrapper_best_checkpoint`. Solver-final rows report their solver ledger as the best checkpoint.
