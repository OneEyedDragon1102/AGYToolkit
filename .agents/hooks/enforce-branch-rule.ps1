# Enforces that no git commits are made directly on 'main' branch
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$inputJson = [Console]::In.ReadToEnd()

if ([string]::IsNullOrWhiteSpace($inputJson)) {
    Write-Output '{"decision": "allow"}'
    exit 0
}

try {
    $payload = $inputJson | ConvertFrom-Json
    $toolName = $payload.toolCall.name
    $args = $payload.toolCall.args

    if ($toolName -eq "run_command" -and $args.CommandLine) {
        $cmd = $args.CommandLine.Trim()
        
        # Check if the command is a git commit or direct push to main
        if ($cmd -match "git\s+commit" -or $cmd -match "git\s+push\s+.*main") {
            # Check current branch
            $currentBranch = (git branch --show-current 2>$null)
            if ($currentBranch -eq "main") {
                $response = @{
                    decision = "deny"
                    reason   = "Branch Rule Violation: Direct commits or pushes to 'main' are strictly forbidden. Switch to a feature branch (feature/<name>)."
                }
                Write-Output ($response | ConvertTo-Json -Compress)
                exit 0
            }
        }
    }

    Write-Output '{"decision": "allow"}'
}
catch {
    Write-Output '{"decision": "allow"}'
}
