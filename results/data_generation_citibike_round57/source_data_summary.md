
# Citi Bike 443 authoritative source summary

The authoritative station universe is the row-aligned pair
`E:\codes\Hybrid GA\testdata\CitiBike\coords\citibike_selected_443_capacity_list.txt` and `E:\codes\Hybrid GA\testdata\CitiBike\coords\citibike_selected_443_coords_utm18n_meters.txt`.  Each file parses
to 443 records.  The capacity file SHA-256 is `92ca9b05e66d1425bbc801be2dd9c0776b1a9707e62a60b821d941aa98625ae1`; the
coordinate file SHA-256 is `c5fd892cc82e07332d4796edb0527182d9c60883acc9b87a5410dab569f990d1`.

The source files contain no station identifiers.  Canonical provenance therefore
uses a zero-based `source_station_row_index`.  The legacy loader reads the two
lists in parallel and stores source row *i* at internal index *i+1*.  The same
443 row pairs are paired by the legacy loader.  As an independent annotation
check, 438 pairs map by
exact three-decimal coordinate and capacity to the older local companion table,
4 map by coordinate with a
different companion capacity snapshot, and
1 has no coordinate match.
The companion mapping supplies 442
station IDs/names without changing the authority or alignment of the two
requested files.

Capacities range from 0 to 75, with mean
24.795 and median 23.000.
One row has capacity zero.  It is preserved in the source table and excluded
from generated service-station subsets.  The UTM bounding box is
[586430.902, 593883.533] x [4500814.946, 4508854.182] meters.  There
are 0 duplicate coordinate
occurrences and no nonfinite coordinate values.
