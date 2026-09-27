# Base-landscape reproduction

Run `D:/msys64/ucrt64/bin/python.exe scripts/prepare_round56_stage0.py` from the
repository root at the exact Round 55 base commit on the declared Round 56
branch. Seeds are derived from the frozen SHA-256 material in the manifest.
The generator uses one moderate landscape per V, writes LF newlines, and writes
the parser-effective metric distances (Euclidean coordinate distance divided by
the frozen factor 1.5). M, Q, and T never enter random generation.
