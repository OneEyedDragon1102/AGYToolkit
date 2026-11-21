# Secret & Leak Sentinel: Deterministic Pre-Commit Gate
# Scans staged diffs for plaintext credentials, private keys, cloud tokens, host filesystem leaks, and sensitive files.
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

        # Check if the command is a git commit or staging sensitive env files
        $isCommit = $cmd -match "git\s+commit"
        $isStagingEnv = $cmd -match "git\s+add\s+.*\.env($|\s)"

        if ($isStagingEnv) {
            # Staging raw .env directly
            if ($cmd -notmatch "\.env\.(example|template|sample)") {
                $response = @{
                    decision = "deny"
                    reason   = "Secret & Leak Sentinel: Staging plaintext .env files is forbidden. Use .env.example or environment variables."
                }
                Write-Output ($response | ConvertTo-Json -Compress)
                exit 0
            }
        }

        if ($isCommit) {
            # 1. Sensitive Filenames Gate
            $stagedFiles = (git diff --cached --name-only 2>$null)
            if ($stagedFiles) {
                $fileList = $stagedFiles -split "\r?\n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
                $sensitiveFilePatterns = @(
                    "^\.env$",
                    "^\.env\.(local|prod|stage|staging|dev|test)$",
                    "\.pem$",
                    "\.key$",
                    "id_rsa$",
                    "id_ed25519$",
                    "\.p12$",
                    "\.pfx$",
                    "\.keystore$",
                    "(^|/)credentials\.json$",
                    "(^|/)service[-_]account\.json$"
                )

                foreach ($f in $fileList) {
                    $normalized = $f.Trim()
                    foreach ($pattern in $sensitiveFilePatterns) {
                        if ($normalized -match $pattern -and $normalized -notmatch "\.(example|template|sample)$") {
                            $response = @{
                                decision = "deny"
                                reason   = "Secret & Leak Sentinel: Staged sensitive file ($normalized) detected. Never commit sensitive credentials or environment secrets."
                            }
                            Write-Output ($response | ConvertTo-Json -Compress)
                            exit 0
                        }
                    }
                }
            }

            # 2. Inspect Staged Diff for Sensitive Content
            $diffOutput = (git diff --cached -U0 2>$null)
            if ($diffOutput) {
                $diffLines = $diffOutput -split "\r?\n"
                $addedLines = $diffLines | Where-Object { $_ -match '^\+[^+]' }

                # A. Private Key Gate
                $privateKeyPattern = '-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----'
                foreach ($line in $addedLines) {
                    if ($line -match '(\$privateKeyPattern|pattern\s*=)') { continue }
                    if ($line -match $privateKeyPattern) {
                        $response = @{
                            decision = "deny"
                            reason   = "Secret & Leak Sentinel: Staged private key block detected. Remove private key from commit diff."
                        }
                        Write-Output ($response | ConvertTo-Json -Compress)
                        exit 0
                    }
                }

                # B. AWS / Cloud Credential Gate
                $awsKeyPattern = '\bAKIA[0-9A-Z]{16}\b'
                $awsSecretPattern = '(?i)aws_secret_access_key\s*[:=]\s*[''"][A-Za-z0-9/+=]{30,}[''"]'
                foreach ($line in $addedLines) {
                    if ($line -match $awsKeyPattern -or $line -match $awsSecretPattern) {
                        $response = @{
                            decision = "deny"
                            reason   = "Secret & Leak Sentinel: Staged AWS credentials detected. Remove cloud access keys from commit diff."
                        }
                        Write-Output ($response | ConvertTo-Json -Compress)
                        exit 0
                    }
                }

                # C. Hardcoded Plaintext Passwords & Tokens Gate
                $credRegex = '(?i)(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*[''"]([^''"\r\n]+)[''"]'
                $ignoredValues = @("", "change_me", "your_password", "todo", "dummy", "test", "example", "placeholder", "xxx")

                foreach ($line in $addedLines) {
                    if ($line -match $credRegex) {
                        $val = $matches[2].Trim()
                        $lowerVal = $val.ToLower()

                        # Check if placeholder or variable substitution
                        $isPlaceholder = $false
                        if ($val.StartsWith("`$") -or $val.StartsWith("<") -or $val.StartsWith("{{") -or $val.StartsWith("%")) {
                            $isPlaceholder = $true
                        } elseif ($ignoredValues -contains $lowerVal) {
                            $isPlaceholder = $true
                        }

                        if (-not $isPlaceholder -and $val.Length -ge 3) {
                            $response = @{
                                decision = "deny"
                                reason   = "Secret & Leak Sentinel: Hardcoded credential or plaintext password detected in staged diff. Use environment variables or secrets manager."
                            }
                            Write-Output ($response | ConvertTo-Json -Compress)
                            exit 0
                        }
                    }
                }

                # D. Host Filesystem & Username Leak Gate
                $hostPathRegex = '(?i)(C:\\{1,2}Users\\{1,2}([a-zA-Z0-9_-]+)|[/\\]home[/\\]([a-zA-Z0-9_-]+))'
                $genericUsernames = @("username", "user", "runner", "circleci", "root", "node", "app", "ubuntu")

                foreach ($line in $addedLines) {
                    if ($line -match $hostPathRegex) {
                        $capturedUser = if ($matches[2]) { $matches[2] } else { $matches[3] }
                        if ($capturedUser -and $genericUsernames -notcontains $capturedUser.ToLower()) {
                            $response = @{
                                decision = "deny"
                                reason   = "Secret & Leak Sentinel: Local host filesystem path / username leak detected ($($matches[1])). Use relative paths or environment variables."
                            }
                            Write-Output ($response | ConvertTo-Json -Compress)
                            exit 0
                        }
                    }
                }
            }
        }
    }

    Write-Output '{"decision": "allow"}'
}
catch {
    Write-Output '{"decision": "allow"}'
}
