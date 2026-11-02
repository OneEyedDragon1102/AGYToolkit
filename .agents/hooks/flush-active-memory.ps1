# Flushes modified file paths to active-session.md on PostToolUse in downstream workspaces
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$inputJson = [Console]::In.ReadToEnd()

if ([string]::IsNullOrWhiteSpace($inputJson)) {
    Write-Output "{}"
    exit 0
}

try {
    $payload = $inputJson | ConvertFrom-Json
    $toolName = $payload.toolCall.name
    $args = $payload.toolCall.args

    if ($toolName -eq "write_file" -or $toolName -eq "edit_file") {
        $filePath = $args.Path
        if ($filePath) {
            # Resolve memory path relative to this script's directory (.agents/hooks -> .agents/memory)
            $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
            $activeSessionPath = Join-Path (Split-Path -Parent $scriptDir) "memory\active-session.md"

            if (Test-Path $activeSessionPath) {
                $content = Get-Content -Path $activeSessionPath -Raw -Encoding UTF8
                $fileName = [System.IO.Path]::GetFileName($filePath)

                # If file not already recorded in active session, append it
                if ($content -notmatch [regex]::Escape($fileName)) {
                    $insertTarget = "## Modified Files"
                    if ($content -match $insertTarget) {
                        $newContent = $content -replace $insertTarget, "$insertTarget`n- ``$fileName``"
                        # Keep under 1KB
                        if ($newContent.Length -le 1024) {
                            Set-Content -Path $activeSessionPath -Value $newContent -Encoding UTF8 -NoNewline
                        }
                    }
                }
            }
        }
    }

    Write-Output "{}"
}
catch {
    Write-Output "{}"
}
