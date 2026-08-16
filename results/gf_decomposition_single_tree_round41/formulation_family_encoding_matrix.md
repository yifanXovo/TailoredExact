# Formulation-family encoding matrix

The authoritative row-by-row classification is `formulation_family_encoding_matrix.csv`. Every interval-local family returned by the existing row factory is present in all three integer formulations. Core omits only the factory's original interval-tight `G*bit` McCormick rows because the perspective block replaces them. Extended additionally replaces direct cap/floor, objective-estimator cutoff, penalty closure, and SP-product rows with the uniformly frozen selected-copy pack.

“Native indicator” means `z_k=1 -> a^T x sense rhs`; it is exact for an integer selector but does not assert external-K2 LP-hull strength. “Exact selector aggregation” means the right-hand-side/domain aggregation is mathematically valid for fractional selectors as well. “Fully perspective/disaggregated” means the formulation introduces selected variables and sums them back to the original variable/product.

No family was selected based on an instance name or witness outcome. The Extended pack was fixed as the single allowed group—`S`, `P`, `H`, and the existing SP estimator—before confirmation runs.
