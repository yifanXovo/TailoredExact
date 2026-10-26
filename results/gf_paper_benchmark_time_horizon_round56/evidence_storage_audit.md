# Round 56 evidence storage audit

Compact manifests, tables, reports, route packages, verification files, reproduction commands, and hashes are committed. Native solver logs, generated LPs, and transient progress ledgers remain under `results/gf_paper_benchmark_time_horizon_round56/local_raw/` and are not committed.

The local-raw inventory records 1944 files totaling 1684208281 bytes, each with an exact path, byte count, and SHA-256. `compact_evidence_inventory.csv` inventories the compact committed evidence; `final_evidence_inventory.csv` joins that evidence with the committed local-raw index. The inventory files exclude their own recursive hashes.
