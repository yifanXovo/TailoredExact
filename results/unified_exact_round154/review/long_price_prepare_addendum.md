# K35 long-price admission: prepare-only source addendum

The original long_price_admission.json and its frozen plan/direction are
preserved unchanged. This is a source-difference record, not a new
performance sample or an extension of that admitted window.

The reviewer `/root/review_round154` read the actual Git diff and current
round154_targets.py. Since the admitted comparison source
e14d09042e62a0f4b3082228f18eb3d69c2af0c4d75bbe9074c446e5697196e8,
the changes are confined to prepare(): explicit prior_override, the
already qualified process-local exact-text enable(), inheritance of
the current pool interval, and reuse of its full qualified RMP solve
to save refreshed_pool.json and consume a possibly better upper.

The entire compare() body, its module-level imports and frozen K35
direction are unchanged. The exact-text import is local to prepare()
and is not executed by compare(). No K35 beta/d/tau/initial stocks,
formulation, numerical guard, Native parameters, cost rule or stopping
condition changes. The running process's actual source snapshot and
call/model records remain its version authority; a later delivery
file hash is not relabelled as its executed source.

The subsequent matching RN long process still executes the identical
reviewed compare body and reads the same direction SHA
a4411f4cf6d094b092a9fbaee400702a437aa7866c2187b3c5ac5cfb6e4999cd.
The deepening plan SHA remains
39640d4d3f81ea03c68a9a35c471176da21322b22511b55b2e9707299ea3b981.
This addendum grants no extra price window, no changed initial information
and no automatic grid. The conditional skip rule remains unchanged.

The current full targets.py source SHA at this review is
7bbaa94b8d6e5dea7ef94bcf2e9a64b65df8efa64fac364d3fbe87b7d0613de0.
The additional prepare/coupling logic is reviewed separately in
coupling_interface.md. The complete B/E/J producer/reader/helper chain
does not import this offline direction module and remains frozen at
its original confirmation-matrix identity.

No Optimize, Native model read, compile, large I/O or experimental
process was performed by the reviewer.

