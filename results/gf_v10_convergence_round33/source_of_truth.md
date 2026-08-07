# Round 33 source of truth

- Branch: `codex/round33-v10-convergence-benchmark`
- Starting HEAD: `2db8fe5b5c33145e1a8cd6dca86f8459885fa2bf`
- Observed live main at preparation: `e352055138c4ea00f308bed94523ee161dad1a6d`
- C6 source: unchanged Round 31/32 `round31-nonblocking-native-bound`
- Primary benchmark: P-GRB versus C6-FROZEN
- New matrix: 18 deterministic V10 instances, M in {1,2,3}, Q in
  {20,30}, and three scenarios
- Safety cap and primary timing: 3,600 process-entry seconds
- Round 32 raw evidence is read-only and never copied into Round 33 raw rows.
- Official source commit and executable hash are bound later by
  `round33_frozen_manifest.json` after clean build and certificate preflight.
- Frozen source commit: `1a79322dd9c2f2345de1e02909727c49c58cb2dd`
- Frozen executable SHA-256: `bdc5145c9c1f6c2fad6a851db08dd96849355cda903bd000363a60e764d35385`
- Protocol SHA-256: `8e5ec84e1dfcf7ad332e54cecee0bef5b4660e9dba755fe1426a217e57354b69`
