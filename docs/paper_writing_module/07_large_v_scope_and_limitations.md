# 07 Large-V Scope And Limitations

V50/V100 diagnostics in this round are stability checks, not certificate claims.

They verify that `paper-gf-bpc-core`:

- runs sealed;
- does not use route-mask all-subset enumeration;
- does not use interval-oracle certificate evidence by default;
- produces final auditable JSON.

The current large-V bottleneck is still lower-bound strength and BPC exact
pricing closure, so broad large-V benchmarking should wait for another targeted
BPC/pricing round.
