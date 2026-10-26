# Exactness and validity

Envelope rows are globally valid on their source interval and are inherited
only globally or by nested descendants. Every fathom uses a valid LP/MIP bound,
valid infeasibility, exact interval coverage, or the verified incumbent cutoff.
Incomplete consolidation propagates its valid union lower bound to each member
but never replaces member coverage. Starts require independent solution and
interval-membership verification. The full normalized CGLP pilot audited every
multiplier identity and generated no violated cut. Certificates require a
monotone global lower bound, complete root coverage, an independently verified
incumbent, exact solver gaps, and fail-closed deadline/error handling.
