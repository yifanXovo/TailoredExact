# Read-only administration. Never read replace targets or active text logs.
# Committed journal numbers below are provisional observations, not audited endpoints.
$round113ObservationRoot = Split-Path -Parent $PSScriptRoot
$round113RawRoot = Join-Path $round113ObservationRoot 'results/unified_exact_round113/campaign/raw'
$round113ObservedArms = @()
if (Test-Path -LiteralPath $round113RawRoot) {
    foreach ($round113ArmDirectory in (Get-ChildItem -LiteralPath $round113RawRoot -Directory | Sort-Object Name)) {
        $round113WholePath = Join-Path $round113ArmDirectory.FullName 'whole_arm_receipt.json'
        if (Test-Path -LiteralPath $round113WholePath) {
            $round113Whole = Get-Content -Raw -LiteralPath $round113WholePath | ConvertFrom-Json
            $round113Audit = Get-Content -Raw -LiteralPath (Join-Path $round113ArmDirectory.FullName 'audit.json') | ConvertFrom-Json
            $round113ObservedArms += [PSCustomObject]@{ arm=$round113ArmDirectory.Name; state='whole_written'; seconds=$round113Whole.complete_seconds; audit=$round113Audit.passed; endpoint=$round113Audit.endpoint }
            continue
        }
        $round113JournalDirectory = Join-Path $round113ArmDirectory.FullName 'journal'
        $round113Committed = @()
        if (Test-Path -LiteralPath $round113JournalDirectory) {
            foreach ($round113CommitFile in (Get-ChildItem -LiteralPath $round113JournalDirectory -Filter '*.commit' | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 3)) {
                $round113CommitFields = (Get-Content -Raw -LiteralPath $round113CommitFile.FullName).Trim().Split(' ')
                $round113EventPath = [IO.Path]::ChangeExtension($round113CommitFile.FullName, 'json')
                if ($round113CommitFields.Length -ne 5 -or $round113CommitFields[0] -ne 'NEJ1') { throw 'Malformed committed receipt' }
                $round113EventBytes = [IO.File]::ReadAllBytes($round113EventPath)
                $round113EventHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($round113EventBytes)).ToLowerInvariant()
                if ($round113EventBytes.Length -ne [long]$round113CommitFields[3] -or $round113EventHash -ne $round113CommitFields[4]) { throw 'Committed bytes differ' }
                $round113Event = [Text.Encoding]::UTF8.GetString($round113EventBytes) | ConvertFrom-Json
                if ($round113Event.sequence -ne [int]$round113CommitFields[1]) { throw 'Committed sequence differs' }
                $round113Committed += [PSCustomObject]@{ sequence=$round113Event.sequence; available=[double]$round113CommitFields[2]; kind=$round113Event.kind; call=$round113Event.call; global_bound=$round113Event.global_bound; native_bound=$round113Event.native_bound }
            }
        }
        $round113ObservedArms += [PSCustomObject]@{ arm=$round113ArmDirectory.Name; state='awaiting_whole'; committed_provisional=$round113Committed }
    }
}
$round113NativeProcesses = @(Get-Process -Name ExactEBRP -ErrorAction SilentlyContinue | ForEach-Object {
    [PSCustomObject]@{ pid=$_.Id; elapsed_seconds=([DateTime]::Now-$_.StartTime).TotalSeconds; working_set_MiB=$_.WorkingSet64/1MB; cpu_seconds=$_.CPU }
})
[PSCustomObject]@{ observed_utc=[DateTime]::UtcNow.ToString('o'); completed_or_active=$round113ObservedArms; native_processes=$round113NativeProcesses; formal_endpoint_only_after_necessary_audit_and_whole=$true } | ConvertTo-Json -Depth 9 -Compress
