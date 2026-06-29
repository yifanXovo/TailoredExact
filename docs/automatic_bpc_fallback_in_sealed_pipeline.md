# Automatic BPC Fallback in the Sealed Pipeline

BPC fallback remains a final diagnostic stage. It is not a default lower-bound
shortcut.

## Trigger

The sealed command accepts:

- `--auto-interval-bpc-fallback true|false`;
- `--auto-interval-bpc-time-limit <seconds>`;
- `--auto-interval-bpc-max-leaves <N>`.

Fallback is eligible only after an unresolved leaf survives relaxation and
oracle attempts. It is intended for a small number of leaves.

## Certificate Rule

A BPC interval can close only if every node used for a lower-bound certificate
has exact pricing closure. If pricing times out, if negative reduced cost
remains, or if the BPC tree does not close, the leaf remains unresolved.

Generated columns may feed UB-only recombination, but they never contribute
lower-bound evidence unless the exact BPC certificate conditions hold.

## Current Round

No sealed completion row obtained a certificate from automatic BPC fallback.
The successful rows closed before BPC fallback. The interrupted rows were
finalized with checkpoint/oracle diagnostics and remain noncertified.
