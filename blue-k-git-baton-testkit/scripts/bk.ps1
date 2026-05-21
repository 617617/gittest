param(
    [Parameter(Position = 0)]
    [ValidateSet("sync", "work", "status", "help")]
    [string]$Command = "sync",

    [string]$Scenario = "ready_codex_main",
    [ValidateSet("auto", "test", "real")]
    [string]$Mode = "auto",
    [switch]$Coverage,
    [switch]$All,
    [switch]$List,
    [switch]$NoFastForward
)

$ErrorActionPreference = "Stop"
$ScenarioSpecified = $PSBoundParameters.ContainsKey("Scenario")

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$Simulator = Join-Path $ScriptDir "bk_sync_sim.py"

function Invoke-GitText {
    param([string[]]$GitArgs)
    $output = & git -C $RepoRoot @GitArgs 2>&1
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "git $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return ($output -join "`n").Trim()
}

function Test-GitSuccess {
    param([string[]]$GitArgs)
    & git -C $RepoRoot @GitArgs *> $null
    return ($LASTEXITCODE -eq 0)
}

function Write-Blocked {
    param(
        [string]$Code,
        [string]$Why,
        [string]$Next = "NEXT: Do not run /bk work",
        [string]$LocalDirty = "unknown"
    )
    Write-Output $Next
    Write-Output "Task: -"
    Write-Output "Holder: -"
    Write-Output "Last: -"
    Write-Output "ChatTarget: -"
    Write-Output "ChatCommand: -"
    Write-Output "FailureCode: $Code"
    Write-Output "Lane: -"
    Write-Output "ProgressFile: -"
    Write-Output "ProgressIndex: -"
    Write-Output "ProgressStatus: -"
    Write-Output "BatonState: unknown"
    Write-Output "LeaseToken: -"
    Write-Output "RemoteHead: -"
    Write-Output "LastPushedCommit: -"
    Write-Output "LastLocalCommit: -"
    Write-Output "UnpushedCommits: unknown"
    Write-Output "LocalDirty: $LocalDirty"
    Write-Output "RemoteTakeoverAllowed: no"
    Write-Output "TakeoverBasis: not evaluated"
    Write-Output "Next command: -"
    Write-Output "WHY: $Why"
    Write-Output "RepoRoot: $RepoRoot"
    Write-Output "Log path: blue-k-git-baton-testkit/logs/live-sync.log"
}

function Copy-NextChatCommand {
    param([object[]]$OutputLines)

    $commandLine = $OutputLines |
        ForEach-Object { [string]$_ } |
        Where-Object { $_ -match "^ChatCommand:\s*/bk " } |
        Select-Object -First 1

    if (-not $commandLine) {
        return
    }

    $command = ($commandLine -replace "^ChatCommand:\s*", "").Trim()
    if (-not $command -or $command -eq "-") {
        Write-Output "Clipboard: skipped (no chat command is safe now)"
        return
    }

    if (-not (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
        Write-Output "Clipboard: unavailable; copy manually: $command"
        return
    }

    try {
        Set-Clipboard -Value $command
        Write-Output "Clipboard: copied $command"
    } catch {
        Write-Output "Clipboard: unavailable; copy manually: $command"
    }
}

function Invoke-SimulatorCommand {
    param(
        [string[]]$SimulatorArgs,
        [switch]$CopyCommand
    )

    $output = & python $Simulator @SimulatorArgs 2>&1
    $code = $LASTEXITCODE
    if ($output) {
        $output | ForEach-Object { Write-Output $_ }
    }
    if ($CopyCommand) {
        Copy-NextChatCommand $output
    }
    exit $code
}

function Sync-GitState {
    Write-Output "BK: sync"
    Write-Output "RepoRoot: $RepoRoot"

    & git -C $RepoRoot fetch --prune origin
    if ($LASTEXITCODE -ne 0) {
        Write-Blocked "FETCH_FAILED" "could not fetch origin; remote state is unknown"
        exit 2
    }

    $branch = Invoke-GitText @("rev-parse", "--abbrev-ref", "HEAD")
    if ($branch -eq "HEAD") {
        Write-Blocked "DETACHED_HEAD" "bk sync requires a checked-out branch"
        exit 2
    }

    $upstreamOutput = & git -C $RepoRoot rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Blocked "NO_UPSTREAM" "current branch has no upstream; wrapper cannot infer remote head"
        exit 2
    }
    $upstream = ($upstreamOutput -join "`n").Trim()

    $dirty = (Invoke-GitText @("status", "--porcelain=v1", "--untracked-files=normal"))
    $localHead = Invoke-GitText @("rev-parse", "HEAD")
    $remoteHead = Invoke-GitText @("rev-parse", $upstream)

    Write-Output "Branch: $branch"
    Write-Output "Upstream: $upstream"
    Write-Output "LocalHead: $localHead"
    Write-Output "RemoteHead: $remoteHead"

    if ($dirty) {
        Write-Blocked "LOCAL_DIRTY_BEFORE_SYNC_DECISION" "working tree has tracked or untracked changes; commit/stash/clean before /bk work" -LocalDirty "true"
        exit 2
    }

    if ($localHead -eq $remoteHead) {
        Write-Output "SyncState: already at upstream"
        return
    }

    if (Test-GitSuccess @("merge-base", "--is-ancestor", $localHead, $remoteHead)) {
        if ($NoFastForward) {
            Write-Blocked "LOCAL_BEHIND_REMOTE" "remote has new commits; rerun bk sync without -NoFastForward to update safely"
            exit 2
        }
        Write-Output "SyncState: fast-forwarding local branch to upstream"
        & git -C $RepoRoot merge --ff-only $upstream
        if ($LASTEXITCODE -ne 0) {
            Write-Blocked "FAST_FORWARD_FAILED" "git merge --ff-only failed; manual inspection required"
            exit 2
        }
        return
    }

    if (Test-GitSuccess @("merge-base", "--is-ancestor", $remoteHead, $localHead)) {
        Write-Blocked "LOCAL_AHEAD_REMOTE" "local branch has commits not present on upstream; let /bk work own push/handoff"
        exit 2
    }

    Write-Blocked "LOCAL_REMOTE_DIVERGED" "local and upstream diverged; wrapper refuses merge/rebase"
    exit 2
}

function Get-StatusMode {
    if ($Mode -ne "auto") { return $Mode }
    $hasCoordBranch = Test-GitSuccess @("show-ref", "--verify", "--quiet", "refs/remotes/origin/blue-k/coordination")
    if ($hasCoordBranch) { return "real" }
    $hasTestStart = Test-Path (Join-Path $RepoRoot "blue-k-git-baton-testkit\_coord\from-cc\test-start.md")
    if ($hasTestStart) { return "test" }
    return "none"
}

function Get-YamlField {
    param([string]$Raw, [string]$Key)
    if ($Raw -match "(?m)^\s*${Key}\s*:\s*(.*?)\s*$") { return $Matches[1] }
    return "-"
}

function Show-TestStatus {
    $testkit = "blue-k-git-baton-testkit"
    $fromCc = Join-Path $RepoRoot "$testkit\_coord\from-cc"
    $fromCodex = Join-Path $RepoRoot "$testkit\_coord\from-codex"
    $resultsDir = Join-Path $fromCodex "test-results"
    $reviewDir = Join-Path $fromCc "review"

    Write-Output "BK Status: test mode (v0.10 walk-through)"
    Write-Output "RepoRoot: $RepoRoot"
    Write-Output ""

    $startFile = Join-Path $fromCc "test-start.md"
    if (Test-Path $startFile) {
        $startContent = Get-Content $startFile -Raw
        $startedAt = if ($startContent -match "StartedAt:\s*(\S+)") { $Matches[1] } else { "unknown" }
        $status = if ($startContent -match "Status:\s*(\S+)") { $Matches[1] } else { "unknown" }
        Write-Output "TestAuthorized: $status ($startedAt)"
    } else {
        Write-Output "TestAuthorized: no (waiting for _coord/from-cc/test-start.md)"
    }

    $readyFile = Join-Path $fromCodex "test-ready.md"
    if (Test-Path $readyFile) {
        $readyContent = Get-Content $readyFile -Raw
        $codexStatus = if ($readyContent -match "Status:\s*(\S+)") { $Matches[1] } else { "unknown" }
        $verifier = if ($readyContent -match "Verifier:\s*(\S+)") { $Matches[1] } else { "unknown" }
        Write-Output "CodexReady: $codexStatus (verifier: $verifier)"
    } else {
        Write-Output "CodexReady: no (waiting for _coord/from-codex/test-ready.md)"
    }

    Write-Output ""

    $scenarios = @(
        "ready_codex_main",
        "ready_cc_planner",
        "role_mismatch",
        "audit_report_blocks_runner",
        "atomic_unavailable",
        "active_lease_other_holder",
        "stale_lease_resume_original",
        "stale_lease_takeover_required",
        "lower_gate_block_cannot_be_accepted",
        "review_pending_finalize_only",
        "fix_required_routes_runner_fix",
        "superseded_topic_after_code_fix",
        "docs_only_freeze_violation",
        "dependency_fix_target_prereq"
    )

    Write-Output "Scenario progress (per test-protocol.md scenario table):"

    $resultCount = 0
    $reviewCount = 0
    foreach ($s in $scenarios) {
        $resultPath = Join-Path $resultsDir "$s.md"
        $reviewPath = Join-Path $reviewDir "$s.md"
        $hasResult = Test-Path $resultPath
        $hasReview = Test-Path $reviewPath
        $outcome = "-"
        $selfEval = "-"
        if ($hasResult) {
            $resultCount++
            $resultContent = Get-Content $resultPath -Raw
            if ($resultContent -match "Outcome:\s*(\S+)") { $outcome = $Matches[1] }
            if ($resultContent -match "SelfEvaluation:\s*(\S+)") { $selfEval = $Matches[1] }
        }
        if ($hasReview) { $reviewCount++ }
        $resultMark = if ($hasResult) { "OK" } else { ".." }
        $reviewMark = if ($hasReview) { "OK" } else { ".." }
        Write-Output ("  {0,-42} result:{1} review:{2}  outcome={3,-22} self={4}" -f $s, $resultMark, $reviewMark, $outcome, $selfEval)
    }

    Write-Output ""
    Write-Output ("Total: {0}/{1} result files, {2}/{1} reviews" -f $resultCount, $scenarios.Count, $reviewCount)

    $extras = @()
    if (Test-Path $resultsDir) {
        $extras = Get-ChildItem $resultsDir -Filter "*.md" -ErrorAction SilentlyContinue |
            Where-Object { $_.BaseName -ne ".gitkeep" -and $scenarios -notcontains $_.BaseName } |
            ForEach-Object { $_.BaseName }
    }
    if ($extras.Count -gt 0) {
        Write-Output ""
        Write-Output "Extra result files not in the protocol table:"
        $extras | ForEach-Object { Write-Output "  $_" }
    }

    Write-Output ""
    $branch = Invoke-GitText @("rev-parse", "--abbrev-ref", "HEAD")
    Write-Output "Last 3 commits on ${branch}:"
    $log = Invoke-GitText @("log", "--oneline", "-3")
    $log -split "`n" | ForEach-Object { Write-Output "  $_" }
}

function Show-RealStatus {
    Write-Output "BK Status: real mode"
    Write-Output "RepoRoot: $RepoRoot"
    Write-Output ""

    & git -C $RepoRoot fetch --prune origin *> $null

    if (-not (Test-GitSuccess @("show-ref", "--verify", "--quiet", "refs/remotes/origin/blue-k/coordination"))) {
        Write-Output "CoordinationBranch: missing (origin/blue-k/coordination not present)"
        Write-Output "Hint: the real Blue-K workflow has not started; switch to test mode with -Mode test if v0.10 walk-through is active."
        return
    }

    $batonRaw = & git -C $RepoRoot show "origin/blue-k/coordination:.blue-k/BATON.yaml" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $batonRaw) {
        Write-Output "BATON: missing on origin/blue-k/coordination"
        return
    }
    $batonText = ($batonRaw -join "`n")

    $holder = Get-YamlField $batonText "Holder"
    $ownerRole = Get-YamlField $batonText "OwnerRole"
    $lane = Get-YamlField $batonText "Lane"
    $workBranch = Get-YamlField $batonText "WorkBranch"
    $workHead = Get-YamlField $batonText "WorkBranchHead"
    $leaseToken = Get-YamlField $batonText "LeaseToken"
    $leaseExpires = Get-YamlField $batonText "LeaseExpiresAt"
    $state = Get-YamlField $batonText "State"
    $fixTarget = Get-YamlField $batonText "FixTarget"
    $consensusKind = Get-YamlField $batonText "ConsensusKind"
    $consensusStatus = Get-YamlField $batonText "ConsensusStatus"

    Write-Output "Task: $workBranch"
    Write-Output "Holder: $holder ($lane)"
    Write-Output "OwnerRole: $ownerRole"
    Write-Output "State: $state"
    Write-Output "Lease: token=$leaseToken expires=$leaseExpires"
    Write-Output "WorkBranchHead: $workHead"
    if ($fixTarget -ne "-") { Write-Output "FixTarget: $fixTarget" }
    if ($consensusKind -ne "-") { Write-Output ("Consensus: kind={0} status={1}" -f $consensusKind, $consensusStatus) }

    if ($workBranch -ne "-" -and (Test-GitSuccess @("show-ref", "--verify", "--quiet", "refs/remotes/origin/$workBranch"))) {
        Write-Output ""
        Write-Output "Progress tables on origin/${workBranch}:"
        foreach ($pf in @("docs/mian-k/MAIN_PACKAGE_PROGRESS.md", "docs/mian-k/OTHER_MIN_PACKAGE_PROGRESS.md")) {
            $pcontent = & git -C $RepoRoot show "origin/${workBranch}:$pf" 2>$null
            if ($LASTEXITCODE -eq 0 -and $pcontent) {
                $ptext = ($pcontent -join "`n")
                $running = ([regex]::Matches($ptext, "(?im)^\s*\|.*\brunning\b")).Count
                $reviewPending = ([regex]::Matches($ptext, "(?im)^\s*\|.*\breview_pending\b")).Count
                $done = ([regex]::Matches($ptext, "(?im)^\s*\|.*\bdone\b")).Count
                $pending = ([regex]::Matches($ptext, "(?im)^\s*\|.*\bpending\b")).Count
                Write-Output ("  {0,-50}  running:{1} review:{2} done:{3} pending:{4}" -f $pf, $running, $reviewPending, $done, $pending)
            }
        }

        $consensusLs = & git -C $RepoRoot ls-tree -r --name-only "origin/$workBranch" "docs/mian-k/_consensus" 2>$null
        if ($LASTEXITCODE -eq 0 -and $consensusLs) {
            $topics = ($consensusLs -split "`n") |
                ForEach-Object { if ($_ -match "^docs/mian-k/_consensus/([^/]+)/") { $Matches[1] } } |
                Where-Object { $_ } |
                Select-Object -Unique
            if ($topics) {
                Write-Output ""
                Write-Output "Open consensus topics under docs/mian-k/_consensus/:"
                $topics | ForEach-Object { Write-Output "  $_" }
            }
        }
    }

    Write-Output ""
    Write-Output "Last 3 commits on origin/blue-k/coordination:"
    $log = Invoke-GitText @("log", "--oneline", "-3", "origin/blue-k/coordination")
    $log -split "`n" | ForEach-Object { Write-Output "  $_" }
}

function Invoke-Simulator {
    if ($Coverage) {
        Write-Output "BK: coverage"
        Write-Output "CoverageMode: sync decision partitions"
        Write-Output "UserSurface: bk sync -> /bk work"
        Write-Output "DeveloperNote: internal scenarios are grouped behind this single sync entry"
        Invoke-SimulatorCommand @("--all")
    }
    if ($List) {
        Write-Output "DeveloperDiagnostic: listing internal scenario ids"
        Invoke-SimulatorCommand @("--list")
    }
    if ($All) {
        Write-Output "DeveloperDiagnostic: -All is deprecated; use bk sync -Coverage"
        Invoke-SimulatorCommand @("--all")
    }
    if ($ScenarioSpecified) {
        Write-Output "DeveloperDiagnostic: -Scenario is for internal debugging; user tests should use bk sync or bk sync -Coverage"
        Invoke-SimulatorCommand @("--scenario", $Scenario)
    }
    Invoke-SimulatorCommand @("--scenario", $Scenario) -CopyCommand
}

switch ($Command) {
    "sync" {
        if (-not ($Coverage -or $All -or $List -or $ScenarioSpecified)) {
            Sync-GitState
        }
        Invoke-Simulator
    }
    "work" {
        Write-Output "NEXT: Run bk sync, then paste its ChatCommand in the named CC or Codex chat window."
        Write-Output "WHY: shell-side bk work must not execute Blue-K tasks or call skills directly."
        Write-Output "CHAT_COMMANDS: /bk work, /bk resume, and /bk takeover are AI-chat commands selected by bk sync."
        exit 0
    }
    "status" {
        $resolved = Get-StatusMode
        switch ($resolved) {
            "test" { Show-TestStatus }
            "real" { Show-RealStatus }
            default {
                Write-Output "BK Status: no Blue-K state detected"
                Write-Output "Hint: neither origin/blue-k/coordination nor _coord/from-cc/test-start.md is present."
            }
        }
        exit 0
    }
    "help" {
        Write-Output "Usage:"
        Write-Output "  bk sync"
        Write-Output "  bk sync -Coverage"
        Write-Output "  bk work"
        Write-Output "  bk status [-Mode auto|test|real]"
        Write-Output ""
        Write-Output "sync fetches origin and safely fast-forwards a clean local branch before printing the decision sheet."
        Write-Output "sync also prints ChatCommand and copies it to the clipboard when a chat command is safe."
        Write-Output "coverage runs simulated boundary partitions behind the same sync entry without touching live git state."
        Write-Output "work is only a shell-side guard; execute the printed ChatCommand in the AI chat window."
        Write-Output "status prints a read-only dashboard (auto-detects test vs real mode); never changes BATON state."
        Write-Output ""
        Write-Output "Developer diagnostics:"
        Write-Output "  bk sync -Scenario <name>"
        Write-Output "  bk sync -List"
        Write-Output "  bk sync -All   (deprecated alias for coverage diagnostics)"
        exit 0
    }
}
