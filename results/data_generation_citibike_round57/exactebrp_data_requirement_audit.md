
# Current ExactEBRP data-requirement audit

The frozen parser is `src/Parser.cpp` (SHA-256
`9402d2744b4b2a7a83c3152d90d6d6438ca9c3e417d1a57da14dd8101c3b2911`).  `Parser.cpp:126-199` accepts the
Hybrid-GA-compatible text format.  The first line must contain integer `V`,
integer `M`, and a bracketed vehicle-capacity vector of exactly M values.
Named arrays `capacities`, `initial`, and `target` must each have V+1 values.
`weights` and `min_ratio` also resolve to V+1 values; absent values receive
legacy defaults, but this family writes them explicitly.  Service-station
targets must be positive and weights finite/nonnegative.

Index zero is the depot.  This family uses the repository's established
placeholders `capacity=100000`, `initial=50000`, `target=0`, `weight=0`, and
`min_ratio=0`.  Service stations occupy indices 1..V.

When exactly V+1 points are present, `Parser.cpp:91-103,177-180` ignores any
serialized matrix and rebuilds the effective symmetric matrix as Euclidean UTM
distance divided by 1.5.  The new files therefore serialize only points, at
three decimals, and make those values authoritative.  This avoids two
competing matrices and the Round 56 pre-freeze rounding defect.

Operational horizon T is not an input-file field.  `main.cpp:631-635` receives
it through `--T`, then `main.cpp:19085-19092` passes it to the parser.  Pickup
and drop service times are current `SolveOptions` defaults of 60 seconds each
(`Instance.hpp:23-25,40-43`); no current CLI override exists.  Scenario rows
therefore bind an input-file hash to T, pickup/drop defaults, and lambda.

No parser or algorithm modification is needed.  Parser compatibility is
verified with a standalone probe compiled only from the current `Parser.cpp`;
the ExactEBRP optimizer executable is never launched.
