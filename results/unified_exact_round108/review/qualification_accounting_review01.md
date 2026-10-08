# Independent qualification driver accounting correction

Decision: **ACCEPT** supplemental +1 conservative start for each qualification_prepare01 and qualification_cli01. Preserve original launch/receipt bytes and use explicit correction records before future confirmation groups.

round108_common.receipt is an outer Python process that starts round108_qualification.py as a second Python driver. Preparation declares ten native children: quantity guard, exporter and eight reference builders. Actual conservative structure is 1 outer + 1 inner + 10 children = 12, versus original 11. CLI retains its maximum five native children (three primary and two fallback, although fallback was unused); 1 outer + 1 inner + 5 = 7, versus original 6.

Corrected qualification is 19; bridge reserves 7, giving 26; five possible confirmation groups add 4 each, giving 46 within the 48 limit. My earlier independent admission arithmetic used the declared 17 / full-plan 44 and missed the two inner drivers. Those factual counts are explicitly superseded here. Admission remains valid because the corrected full plan still fits the limit.

Original outer qualification seconds remain 269.17639509995934: the inner driver is already inside the outer fee, so no nested duration is added. Frozen common.budget ignores supplemental corrections. Before each future confirmation group require every fee closed, corrected paid/reserved starts +4 <=48, enough remaining outer seconds and the original stage/identity/bridge gates. round107_reader.fees already reads fee_corrections by label; final tables must use corrected counts.

This review checks small source and metadata only. It does not rewrite frozen helpers, retry a solver, release unused fallback reservation or claim the bridge is idle.
