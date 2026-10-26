# Representative Round 39 trajectories

One case per stratum is selected by proximity to that stratum's frozen median
difficulty score, never by solver outcome. `representative_trajectories.csv`
contains both official arms with process-entry time, monotone valid lower
bound, observed incumbent, proof gap to the final verified optimum, event, and
source. Values are observed left-continuously; there is no interpolation or
extension beyond the last event, and the strict serialized endpoint is added
only when the native trace ends earlier.
