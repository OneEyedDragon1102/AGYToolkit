# Auto-compaction hook for tiered agent memory on PostToolUse
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$inputJson = [Console]::In.ReadToEnd()

if ([string]::IsNullOrWhiteSpace($inputJson)) {
    Write-Output '{"decision": "allow"}'
    exit 0
}

try {
    # Resolve memory directory relative to hook (.agents/hooks -> .agents/memory)
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $agentsDir = Split-Path -Parent $scriptDir
    $memDir = Join-Path $agentsDir "memory"
    $activeSessionPath = Join-Path $memDir "active-session.md"
    $decisionsPath = Join-Path $memDir "decisions.md"

    $needsCompaction = $false
    if (Test-Path $activeSessionPath) {
        $sessionSize = (Get-Item $activeSessionPath).Length
        # 85% of 1024 bytes = ~870
        if ($sessionSize -ge 870) {
            $needsCompaction = $true
        }
    }
    if (Test-Path $decisionsPath) {
        $decisionsSize = (Get-Item $decisionsPath).Length
        # 85% of 3072 bytes = ~2611
        if ($decisionsSize -ge 2611) {
            $needsCompaction = $true
        }
    }

    if ($needsCompaction) {
        $repoRoot = Split-Path -Parent $agentsDir
        $py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { $null }
        if ($py) {
            $env:PYTHONPATH = "$repoRoot\automation\src;$env:PYTHONPATH"
            $res = & $py -m agy_toolkit memory auto-compact "$repoRoot" --json 2>$null
            if ($res) {
                Write-Output '{"decision": "allow", "advice": "Memory auto-compacted. Consider running /compact in AGY IDE."}'
                exit 0
            }
        }
    }

    Write-Output '{"decision": "allow"}'
}
catch {
    Write-Output '{"decision": "allow"}'
}
