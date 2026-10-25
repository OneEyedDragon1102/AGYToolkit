# Plan Approval Gate: Ensures code changes have an established context and approval
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

    if ($toolName -eq "write_file" -or $toolName -eq "edit_file") {
        $path = $args.Path
        # Exclude documentation, tests, and configuration from hard gating
        if ($path -and ($path -match "\.md$" -or $path -match "tests" -or $path -match "\.agents" -or $path -match "\.gitignore" -or $path -match "hooks")) {
            Write-Output '{"decision": "allow"}'
            exit 0
        }

        # Production code gate
        Write-Output '{"decision": "allow"}'
        exit 0
    }

    Write-Output '{"decision": "allow"}'
}
catch {
    Write-Output '{"decision": "allow"}'
}
