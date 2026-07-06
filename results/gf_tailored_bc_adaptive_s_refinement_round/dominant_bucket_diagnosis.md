# Dominant S-Bucket Diagnosis

Dominant open bucket: `2` under policy `uniform`.

S range: `[16.59546103547, 23.272821182835]`; LB `0.0455127377348`; gap-to-cutoff `0.0036398149298999954`.

Diagnosis fields in `s_bucket_child_status.csv` identify whether the bucket contains the merged-parent plateau, whether it dominates the parent merged LB, and whether bound progress comes from bucket-tight denominator rows. Exact best-bound node LP snapshots are not exposed by the current CPLEX C callback path; exported LP/model hashes, progress traces, callback row counts, and final bound trajectories are therefore used as the auditable snapshot proxy.
