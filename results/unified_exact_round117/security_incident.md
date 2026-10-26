# Round117 source-publication incident

This report records the observed GitHub alert and separates current publication containment from history cleanup, issuer remediation, and alert closure. No discovered credential has been used to call an API or execute a downloaded script. Current incident disposition is `CONTAINED_PENDING_OWNER_ACTION`, scoped to the new safe Round117 publication; original refs/history remain reachable.

## Verified facts

- Existing GitHub CLI authorization can read alert 1 and all its location pages. The repository is public; the API reports existing administrator permission. No permissions or security settings were changed.
- Observation: 2026-10-13 02:11 Asia/Shanghai (2026-10-12T18:11:25 UTC). Type: Google API Key; state: `open`; validity: `unknown`; created/updated: 2026-10-12T16:01:50Z; resolution: null. The API also reports `publicly_leaked=true` and `push_protection_bypassed=false`.
- Both returned locations first refer to commit `9f3a7f58a4af9059cb5f70fafe1aae139f8015af`: `results/unified_exact_round116/source/requests/system_data/01.response`, line 289, and `results/unified_exact_round116/source/requests/license/01.response`, line 272. Both values have the same SHA256 fingerprint: `cef6ada8ca76d2848cb108115c699be78aa68f4baa03ac532bd6d273d21f5901`. No reusable prefix/suffix is published.
- Original system-data response: 128348 bytes, SHA256 `e90dbc4aab4ceff963cba44e7997875533528175a32a1b718a339463592b282e`. Original license response: 123565 bytes, SHA256 `89e7c6dcfd383aeb68422de288eaf8c61e86dd317c8f162de49c31cdc6ada181`.
- The key occurs in each page's embedded client runtime configuration under `confidantCredentials.CREDENTIALS_FRONTEND_GOOGLE_MAPS_KEY`. Other client credential fields are present and are within the same removal scope. None is needed for station selection, mathematics, license text, or discovery provenance.
- The inspected collector constructs ordinary unauthenticated HTTPS GETs with only an explicit User-Agent and Accept header. It installs no cookie jar, supplies no Authorization, reads no local credentials, and does not run web scripts. It saves the complete response body and response headers; these receipts are also nested in `source/snapshot.json`.
- Alert management and repository settings are separate: secret scanning and push protection are enabled; validity checks are reported disabled. This run neither enables checks nor requests on-demand verification.

## Attribution and unknowns

The downloaded official web runtime is the supported source attribution. Third-party operator ownership is an inference from that origin and configuration context; the underlying Google project owner, restrictions, enabled APIs, billing access, current activity, and validity remain unknown. Appearance in public HTML does not establish harmlessness or false-positive status. No author credential leak has been established. Response cookies are sensitive publication candidates, not proof of an author login session.

No key rotation, revocation, alert resolution, operator notification, history rewrite, force push, branch/PR deletion, repository visibility change, protection bypass, or solver execution has occurred. The alert stays open pending issuer/owner review; `revoked` and `false_positive` are unsupported by current evidence.

## Current work and local protection

Affected publication bytes and their necessary local backup are processed outside version control in an ACL-restricted task directory accessible to Administrator and SYSTEM. Public scan records contain category, location, and one-way fingerprints only. The incident scope includes both HTML pages, all five request receipts, nested snapshot receipts, current R116 archive members, reports/logs and actual later inherited copies.

The two pages are now visible-text extracts with all scripts/runtime/client fields removed. Five receipts use the explicit safe header whitelist, and all nested snapshot receipts use the same safe values. Historical response identities and safe response identities have different explicit fields. The original station-information bytes remain unchanged. `redaction_manifest.json` records eight source changes and two engineering-entry changes, with old/new SHA256s and a preserved original-code authority for the historical admitted data helper.

All four polluted R116 parts are removed from the current branch; `compact_evidence/SUPERSEDED.json` points to the new safe carrier. Of119649 original members,119639 remain byte equal; the ten exceptions are only source publication material and engineering entry points. The completed safe data stream was finalized without recompression after the gate rejected two NONREAL URL literals in test source. Only that fixture source was corrected and remains in the Git delivery outside the scientific carrier.

`safe_restore_receipt.json` verifies all119671 new payload hashes from a fresh directory without old-carrier/network/original-root fallback. `restored_validation/validation.json` rebuilds the four in-scope inputs and16 observed arms/24 pairs with all original scientific fields equal. `restored_security_scan.json` reports zero findings/errors. The full actual staged-file/carrier gate and actual draft/head/alert observation are recorded separately at publication; later receipts do not claim to be contained in the earlier scientific payload.

`affected_refs.json`, `carrier_replacement.json`, `source_identity_exceptions.json`, `history_preview_mapping.json` and `history_and_owner_actions.md` provide the exposure boundaries, actual safe identities, isolated four-commit proposal and minimum issuer/owner action. The private operator notice is drafted and unsent. Initial context inspection briefly showed another client configuration value; context printing was stopped, and no original value is included in any new version-controlled report, test or safe carrier. This limitation is disclosed in the additional review.

R116 PR178 remains a historical BLOCKED evaluation. R117 begins at verified head `d0647f3a29fa079919a5eb9430450d032a14deb6` on `codex/round117-security-v60-scope`. Scientific results and measured identities are independent of this security publication repair.

## Official semantics checked for this run

A regular cleanup commit does not purge reachable Git history; a history rewrite can affect commit identities, stacked PRs, clones and cached references. [GitHub sensitive-data removal](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Removing a token from the tree does not automatically close a secret-scanning alert; its resolution is a separate authorized, evidence-based action. [GitHub alert resolution](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-secret-scanning-alerts/resolving-alerts).

Application and API restrictions and service continuity require the issuer's assessment; a third-party website key cannot be rotated by this researcher. [Google Maps API security guidance](https://developers.google.com/maps/api-security-best-practices).
