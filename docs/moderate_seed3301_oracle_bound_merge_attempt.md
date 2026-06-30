# moderate_seed3301 Oracle Bound Merge Attempt

`moderate_seed3301` was the primary target for this round. It did not certify,
but the new objective-bound oracle merge produced a large valid lower-bound
improvement.

Result:

- status: noncertified;
- UB: `0.0491525526647`;
- LB after oracle-bound merge: `0.047773`;
- gap: `0.0280667552335`;
- oracle leaves attempted: `13`;
- root leaves closed or bound-fathomed: `7`;
- remaining open leaves: `2`.

The two remaining leaves are:

- `[0.0122881381662, 0.0245762763324]`, merged LB `0.047773`;
- `[0.0245762763324, 0.0368644144986]`, merged LB `0.048467`.

Both remaining leaves have valid original compact objective-bound evidence but
do not reach the incumbent cutoff. Therefore the row remains honestly
noncertified. This still meets the round's minimum target: the audited
full-frontier gap is below `0.05`.

BPC fallback was called after the oracle stage but closed zero leaves, so the
active blocker remains exact interval objective-bound closure, not incumbent UB.
