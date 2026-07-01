# Core BPC Scheduling

The `paper-gf-bpc-core` preset is adjusted to avoid delaying BPC indefinitely behind adaptive splitting:

- compact interval-oracle certificates remain disabled;
- complete route-mask enumeration remains disabled as certificate evidence;
- `frontier_split_before_tree=false` in paper-core so unresolved intervals can enter BPC;
- the BPC reserve minimum is reduced from 60s to 20s for controlled diagnostic runs.

This is a scheduling change, not a certificate shortcut. A leaf still closes only when exact BPC pricing closes.

Short full-row runs showed that BPC can become very expensive once it is entered. The focused leaf validations therefore remain the primary evidence for the pricing bottleneck.

