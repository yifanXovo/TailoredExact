# Interpreting native route witnesses

Round 56 retains exactly one final native witness per scenario when the official solver produced an independently verified incumbent. Certified rows retain the exact optimal witness associated with the strict certificate. Capped rows retain the final verified incumbent and label it noncertified.

No witness is post-optimized. In particular, Round 56 does not fix final inventory and solve another routing model, minimize maximum or total duration, minimize travel, minimize vehicles used, search for an objective-equivalent shorter route, or replace native vehicle order with a presentation-oriented route.

Consequently, route travel time, operation time, duration, slack, utilization, vehicles used, stations visited, and bicycles handled are descriptive properties of the one returned witness. They are not minimum-route-duration, shortest-route, necessary-horizon, or minimum-vehicle claims. A large-T witness may use little of T because the objective does not reward route duration, because another objective-equivalent route exists, or because the native incumbent happened to have that shape.

Exact cross-T, cross-M, and cross-Q objective claims use only pairs whose endpoints both strictly certified. Native routes from capped rows remain useful feasibility descriptions but do not enter exact monotonicity conclusions. Different repeatability witnesses are permitted when their certified objective, certificate class, and independent verifier outcome agree; multiple optima can have different route or final-inventory representations.
