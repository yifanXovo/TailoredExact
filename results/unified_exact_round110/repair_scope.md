# Round110 authorized entry repair

The original measured PE has a 2 MiB stack, a fixed main frame of 1414288
bytes, and arm25 failed 0xC00000FD before parsing_complete. Independent Windows
events and disassembly locate its fault in the regex matcher. The multiline
payload expression uses recursively matched [\\s\\S]*?. No dump establishes
the particular field or complete recursion depth; this is not an OOM finding.
The known old formal-main crash is not deliberately reproduced.

First repair only src/Parser.cpp::namedBracketPayload: retain the exact regex
prefix name/whitespace/equals/whitespace/left bracket and replace matching the
payload with iterative search for the first right bracket. Prefix search has
the original unanchored, embedded-name and first-match grammar. For the first
matching prefix, any right bracket makes that prefix the earliest complete
match; if none exists, no later prefix can complete. The prefix regex no longer
recurses once per payload character. Its whitespace matching remains the
original grammar. All numerical tokenization, stod, llround, defaults, legacy
weights, points/matrix priority and sqrt(dx*dx+dy*dy)/1.5 are unchanged.

The minimal Parser repair was sufficient for the actual frozen input domain.
No main/object/build/stack repair was made. Toolchain, standard library, Gurobi version,
optimization and link stack settings remain inherited. Every actual change,
build command and actual PE header is bound before formal performance.

Qualification disproves equivalence if any integer or binary64 mathematical
field changes, any finite extraction boundary changes, any original cold
matrix differs, or the final PE cannot parse all 12 through common main and
return without Optimize/heuristic/oracle. The old and repaired C++ Parsers
are compared in small standalone batch executables on the same toolchain.
Metadata paths are reported separately. Five original H100 CLI paths verify
Seed0 P/ENS/M-B and Seed1 P/M-B, LP/MIP/types/Start/normal return, cap <=120.

Qualification does not inject empty fleets, Starts, UBs or caches into formal
arms. The final new PE, rather than an alternate harness, must pass three
physical-T directory groups through option-consistency-test. Formal production
algorithms, writer, A/B, parameters, startup and deadlines remain unchanged.

Final result: all12 mathematical C++ dumps and inherited cold matrices match;
The16 finite parser-format comparisons and58 bounded historical-evidence
regression cases pass. The actual final PE passed all12 common-main
zero-Optimize entries plus the five fixed H100 functional CLI qualifications.
Qualification consumed16 conservative starts/437.9070925555425 outer seconds.
All42 formal native processes returned normally; the actual old parser stack
failure did not recur. These facts establish finite-domain entry recovery,
not universal arbitrary-input stack safety: the unchanged prefix whitespace
regex still has its original behavior. The final whole-arm audit clock breach
is separate from parser equivalence and is preserved as a formal blocker.

Wrapper/evidence changes preserve original raw flags and journal omissions,
write durable launch/end clocks before post-exit review, and reuse strict
provenance and mathematical checks. Only independently verified current-call
known-fault predicates permit evidence recovery. Unknown correctness defects
pause the campaign; a production-PE change requires a full new 42-arm panel.
