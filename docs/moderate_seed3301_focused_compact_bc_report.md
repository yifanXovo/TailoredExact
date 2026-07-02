# moderate_seed3301 Focused Compact-BC Attempt

The controlled one-thread row `moderate_seed3301_baseline_300s` used `paper-gf-compact-bc`, sealed mode, no BPC, and compact interval BC leaf solves with a 60 second per-leaf limit. It remains noncertified: LB `0.046285`, UB `0.0491525526647`, gap `0.058339852343`, with four leaves closed and two leaves timed out.

A longer 1200s/300s-per-leaf launch did not produce a final solver JSON before the outer wrapper timeout and was stopped as diagnostic only. It is not reported as paper evidence. The next useful run is a solver-finalizing focused run that either increases leaf time while adding checkpoint finalization, or targets the two remaining leaves through the same automatic full-ledger path.
