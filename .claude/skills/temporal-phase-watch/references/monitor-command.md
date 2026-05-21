# Monitor command — arm the from-codex/ watcher

Used by SKILL.md step 5. Skip if the deduplication check in step 1
already found this Monitor armed. Otherwise start a Monitor with the
settings below.

## Monitor settings

- **description:** `temporal-phase: new files in _coord/from-codex/`
- **persistent:** `true`
- **timeout_ms:** `3600000`

## Shell: bash (required)

The command uses process substitution `<(...)`, which is bash-only. Do
not run it under cmd.exe / PowerShell / sh — it will fail silently. On
Windows hosts, the Monitor tool runs via the Bash tool by default; if
your harness is different, wrap the command with `bash -c '...'`.

## Command

```bash
prev=""; while true; do git fetch -q origin master 2>/dev/null || true; cur=$(git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort); if [ "$cur" != "$prev" ]; then comm -13 <(echo "$prev") <(echo "$cur") | while IFS= read -r f; do [ -n "$f" ] && echo "NEW_FROM_CODEX: $f"; done; prev="$cur"; fi; sleep 60; done
```

The loop polls every 60 seconds, fetches origin/master quietly, lists
the from-codex/ directory, and emits one `NEW_FROM_CODEX: <filename>`
line for each newly-appeared file. See
`references/event-handling.md` for how to react to those lines.
