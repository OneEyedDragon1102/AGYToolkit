# Anti-Bloat Sentinel: Blocks AI emojis in code and monolithic file dumps
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
        $content = if ($toolName -eq "write_file") { $args.Content } else { $args.Replacement }

        if ($path -and $content) {
            $ext = [System.IO.Path]::GetExtension($path).ToLower()
            $codeExtensions = @(".java", ".ts", ".js", ".py", ".go", ".rs", ".cpp", ".c", ".cs")

            # Check for non-markdown code files
            if ($codeExtensions -contains $ext) {
                # 1. Emoji detection regex
                $emojiPattern = "[\uD83C-\uDBFF\uDC00-\uDFFF\u2600-\u26FF\u2700-\u27BF]"
                if ($content -match $emojiPattern) {
                    $response = @{
                        decision = "deny"
                        reason   = "Anti-Bloat Sentinel: Emojis detected in production code ($path). Remove all emojis before proceeding."
                    }
                    Write-Output ($response | ConvertTo-Json -Compress)
                    exit 0
                }

                # 2. Monolithic file size gate (>600 lines for a single file)
                $lineCount = ($content -split "\r?\n").Count
                if ($lineCount -gt 600 -and $toolName -eq "write_file" -and -not $args.Append) {
                    $response = @{
                        decision = "deny"
                        reason   = "Anti-Bloat Sentinel: Monolithic file detected ($lineCount lines in $path). Break down into modular components (max 600 lines per file)."
                    }
                    Write-Output ($response | ConvertTo-Json -Compress)
                    exit 0
                }
            }
        }
    }

    Write-Output '{"decision": "allow"}'
}
catch {
    Write-Output '{"decision": "allow"}'
}
