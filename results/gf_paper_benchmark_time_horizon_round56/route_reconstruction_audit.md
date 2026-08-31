# Native route reconstruction audit

The corrected K1-AM-SF controller owns one `best_routes` plan initialized from
the verified seed. Each accepted native partial, exact, block, sibling-union,
or terminal incumbent is independently verified before it replaces that plan,
and the incumbent epoch is advanced with the route assignment. Finalization
copies exactly that plan to `SolveResult::routes` and reruns the original
solution verifier. JSON serialization writes native vehicle indices, node
sequences, and station operations directly. Round 56 archive generation only
materializes and independently rereads these values; it never invokes a solver,
repairs a route, compacts it, or searches for an objective-equivalent witness.
