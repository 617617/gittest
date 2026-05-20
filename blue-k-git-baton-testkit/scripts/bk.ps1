param(
    [Parameter(Position = 0)]
    [ValidateSet("sync", "work", "help")]
    [string]$Command = "sync",

    [string]$Scenario = "ready_codex_main",
    [switch]$Coverage,
    [switch]$All,
    [switch]$List,
    [switch]$NoFastForward
)

$ErrorActionPreference = "Stop"

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
        [string]$Next = "NEXT: Do not run /bk work"
    )
    Write-Output $Next
    Write-Output "FailureCode: $Code"
    Write-Output "WHY: $Why"
    Write-Output "RepoRoot: $RepoRoot"
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
        Write-Blocked "LOCAL_DIRTY_BEFORE_SYNC_DECISION" "working tree has tracked or untracked changes; commit/stash/clean before /bk work"
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

function Invoke-Simulator {
    if ($Coverage) {
        Write-Output "BK: coverage"
        Write-Output "CoverageMode: sync decision partitions"
        Write-Output "UserSurface: bk sync -> /bk work"
        Write-Output "DeveloperNote: internal scenarios are grouped behind this single sync entry"
        & python $Simulator --all
        exit $LASTEXITCODE
    }
    if ($List) {
        Write-Output "DeveloperDiagnostic: listing internal scenario ids"
        & python $Simulator --list
        exit $LASTEXITCODE
    }
    if ($All) {
        Write-Output "DeveloperDiagnostic: -All is deprecated; use bk sync -Coverage"
        & python $Simulator --all
        exit $LASTEXITCODE
    }
    if ($PSBoundParameters.ContainsKey("Scenario")) {
        Write-Output "DeveloperDiagnostic: -Scenario is for internal debugging; user tests should use bk sync or bk sync -Coverage"
    }
    & python $Simulator --scenario $Scenario
    exit $LASTEXITCODE
}

switch ($Command) {
    "sync" {
        Sync-GitState
        Invoke-Simulator
    }
    "work" {
        Write-Output "NEXT: Send /bk work in the CC or Codex chat window named by bk sync."
        Write-Output "WHY: shell-side bk work must not execute Blue-K tasks or call skills directly."
        exit 0
    }
    "help" {
        Write-Output "Usage:"
        Write-Output "  bk sync"
        Write-Output "  bk sync -Coverage"
        Write-Output "  bk work"
        Write-Output ""
        Write-Output "sync fetches origin and safely fast-forwards a clean local branch before printing the decision sheet."
        Write-Output "coverage runs boundary partitions behind the same sync entry without exposing per-scenario commands to users."
        Write-Output "work is only a shell-side guard; execute /bk work in the AI chat window."
        Write-Output ""
        Write-Output "Developer diagnostics:"
        Write-Output "  bk sync -Scenario <name>"
        Write-Output "  bk sync -List"
        Write-Output "  bk sync -All   (deprecated alias for coverage diagnostics)"
        exit 0
    }
}
