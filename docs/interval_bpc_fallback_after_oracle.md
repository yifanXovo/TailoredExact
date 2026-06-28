# Interval BPC Fallback After Oracle

BPC fallback was not run in this round because the priority V20/M3 instance
closed through the full-frontier relaxation ledger before interval fallback was
required.  The result file `interval_bpc_fallback_results.csv` records this
explicitly.

BPC interval evidence remains certificate-valid only if exact pricing closes for
every node used as lower-bound evidence.  Incomplete pricing remains diagnostic.

