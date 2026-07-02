# Memory-Safe Compact Model Generation

The time-profile round uses resource-adaptive model-size controls:

- `--compact-bc-model-size-policy resource-adaptive`;
- `--compact-bc-max-memory-mb <MB>`;
- `--compact-bc-expensive-static-families auto|on|off`;
- `--compact-bc-use-dynamic-instead-of-static true|false`.

These controls do not change certificate logic. They only disable optional
strengthening families when estimates exceed configured limits, preferring
dynamic separation for expensive support/transfer families.

V50/V100 exact diagnostics still include model-size/native-exit failures, but
they now produce final noncertified JSON rows instead of silent crashes.
