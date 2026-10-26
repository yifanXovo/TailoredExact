# Private operator security notice draft — not sent

Subject: Client credential configuration copied from public Capital Bikeshare pages into a research snapshot

Hello Capital Bikeshare website/security team,

During a non-commercial reproducibility study, we saved unauthenticated HTTP200 responses from https://capitalbikeshare.com/system-data and https://capitalbikeshare.com/data-license-agreement on 2026-10-12. A public research repository's secret scanner subsequently identified a Google API Key in the pages' embedded client runtime configuration. Both occurrences refer to the `confidantCredentials.CREDENTIALS_FRONTEND_GOOGLE_MAPS_KEY` field. Additional client credential configuration was present in the same runtime block.

The Google value's SHA256 fingerprint is `cef6ada8ca76d2848cb108115c699be78aa68f4baa03ac532bd6d273d21f5901`. We provide no complete key or reusable key fragment. We have not used the value against Google services, executed the downloaded scripts, or checked any underlying account. Current validity and application/API restrictions are unknown to us; the fact that it was served in public HTML does not establish whether its configuration is safe.

We are removing the runtime configuration and response cookies from the current research publication and its archive, preserving only scientific static data, source/permission text and historical response fingerprints. Repository history/cached copies require separate owner handling. Please assess the issuing project's ownership, restrictions, intended client use and any required credential remediation through your own authorized tools. If a secure contact channel is available, the researcher can provide the two original response hashes and exact source timestamps without sending full credentials.

This draft has not been emailed, posted as an issue, or otherwise transmitted. Sending it requires explicit author authorization and selection of the operator's appropriate private security channel.
