# Transfer Subset Capacity Cuts

Date: 2026-06-28

This round adds CLI plumbing and result fields for future transfer-subset
capacity cuts:

```text
--transfer-subset-capacity-cuts true|false
```

No active transfer-subset inequality is enabled yet.  The reason is certificate
safety: a subset demand/supply transfer cut must be based on route-duration
compatible transfer caps that are valid for every original route-load plan, not
on sampled routes or heuristic station neighborhoods.

The result field `transfer_subset_capacity_cuts_added` remains zero in this
round.  The next safe implementation should derive caps from
depot-pickup-drop-depot travel lower bounds, handling time, station bounds, and
truck capacity.

