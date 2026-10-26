# Targeted primal-design literature check

Read during the frozen R74 D7 campaign on2026-09-15. This is a targeted
primary-source check, not a systematic review. Reading coverage is explicit;
no claim of full-paper verification or new algorithm admission is made.

* Li, Szeto, Long and Shui(2016), A multiple type bike repositioning problem,
  Transportation Research B. The retrieved author-repository publisher PDF
  separates route evolution from greedy loading. Its loading section assumes
  empty vehicle returns and penalizes insufficient final-station unloading
  capacity. This differs from our allowed loaded return with paid depot
  unloading, as well as our normalized-Gini objective. Read section3 lead and
  section3.2, especially PDF text lines512-617; the full16-page paper was not
  read here. [Primary PDF](https://hub.hku.hk/bitstream/10722/229157/1/Content.pdf),
  [DOI](https://doi.org/10.1016/j.trb.2016.05.010).

* Ho and Szeto(2017), A hybrid large neighborhood search for the static
  multi-vehicle bike-repositioning problem, Transportation Research B. The objective uses
  separable convex inventory penalties plus weighted travel. Regret insertion
  considers best versus later travel insertion positions, followed by loading
  readjustment. Section3.6 redistributes quantities between same-type nodes on
  a route; its depot adjustments permit loading at departure, and its model
  permits split service across vehicles. Those features cannot be imported
  into our empty-departure, single-service BRP. Generic insertion, relocation
  and quantity adjustment are therefore established ideas. Read the model
  definition, excerpts from sections3.4-3.6 (including section3.6's explanatory
  prose) and selected Algorithm6 lines, not all neighborhood pseudocode or
  experimental tables. Its CitiBike data also use different station sets,
  road travel and penalties; shared city branding does not imply matched data.
  [Primary PDF](https://hub.hku.hk/bitstream/10722/246055/1/Content.pdf),
  [Repository record](https://hub.hku.hk/handle/10722/246055),
  [DOI](https://doi.org/10.1016/j.trb.2016.11.003).

* Schuijbroek, Hampshire and van Hoeve(2017), Inventory rebalancing and vehicle
  routing in bike sharing systems, EJOR. Inventory service requirements and
  approximate routing jointly inform vehicle clusters, followed by routing
  within each cluster. This supports considering fleet assignment together
  with inventories, but does not supply an exact global bound for our objective
  or justify permanently restricting it to fixed clusters. Read abstract,
  introductory method description and conclusion only.
  [Author manuscript](https://www.contrib.andrew.cmu.edu/~vanhoeve/papers/bike_sharing_final_draft_EJOR.pdf),
  [DOI](https://doi.org/10.1016/j.ejor.2016.08.029).

* Haddad et al.(2018), Large Neighborhood-Based Metaheuristic and Branch-and-
  Price for the Pickup and Delivery Problem with Split Loads. The abstract
  describes joint pair insertion using resource-constrained shortest-path and
  knapsack subproblems. Its one-to-one requests, split loads and multiple
  visits differ from our semantics. It precludes claiming generic joint pair
  insertion as new; no transfer of its algorithm or proof is inferred.
  Abstract only read. [Primary abstract](https://arxiv.org/abs/1802.06318).

Our prospective question is narrower: can a finite, physically verified
neighborhood revise served quantities and fleet allocation efficiently under
the original coupled objective? The archived unused vehicle motivates that
question but proves no improving move exists. No such neighborhood is part
of the currently frozen JDS-X implementation, and literature precedent is
neither a correctness proof for a new adaptation nor performance evidence.
