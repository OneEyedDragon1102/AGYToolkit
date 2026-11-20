#!/usr/bin/env bash
# Secret & Leak Sentinel: Deterministic Pre-Commit Gate
# Scans staged diffs for plaintext credentials, private keys, cloud tokens, host leaks, and sensitive files.
set -euo pipefail

INPUT_JSON=$(cat)

if [ -z "$INPUT_JSON" ]; then
  echo '{"decision": "allow"}'
  exit 0
fi

CMD=$(echo "$INPUT_JSON" | grep -o '"CommandLine"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*:[[:space:]]*"//;s/"$//' || true)

if [ -z "$CMD" ]; then
  echo '{"decision": "allow"}'
  exit 0
fi

# Check for git add .env
if echo "$CMD" | grep -qE 'git[[:space:]]+add[[:space:]]+.*\.env($|[[:space:]])'; then
  if ! echo "$CMD" | grep -qE '\.env\.(example|template|sample)'; then
    echo '{"decision": "deny", "reason": "Secret & Leak Sentinel: Staging plaintext .env files is forbidden. Use .env.example or environment variables."}'
    exit 0
  fi
fi

# Check for git commit
if echo "$CMD" | grep -qE 'git[[:space:]]+commit'; then
  # 1. Sensitive Files Gate
  STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)
  if [ -n "$STAGED_FILES" ]; then
    while IFS= read -r file; do
      [ -z "$file" ] && continue
      if echo "$file" | grep -qE '^\.env$|^\.env\.(local|prod|stage|staging|dev|test)$|\.pem$|\.key$|id_rsa$|id_ed25519$|\.p12$|\.pfx$|\.keystore$|(^|/)credentials\.json$|(^|/)service[-_]account\.json$'; then
        if ! echo "$file" | grep -qE '\.(example|template|sample)$'; then
          echo "{\"decision\": \"deny\", \"reason\": \"Secret & Leak Sentinel: Staged sensitive file ($file) detected. Never commit sensitive credentials or environment secrets.\"}"
          exit 0
        fi
      fi
    done <<< "$STAGED_FILES"
  fi

  # 2. Inspect Staged Diff Content
  DIFF_OUTPUT=$(git diff --cached -U0 2>/dev/null || true)
  if [ -n "$DIFF_OUTPUT" ]; then
    ADDED_LINES=$(echo "$DIFF_OUTPUT" | grep -E '^\+[^+]' || true)

    # A. Private Key Gate
    if echo "$ADDED_LINES" | grep -v 'privateKeyPattern' | grep -qE '-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----'; then
      echo '{"decision": "deny", "reason": "Secret & Leak Sentinel: Staged private key block detected. Remove private key from commit diff."}'
      exit 0
    fi

    # B. AWS Credentials Gate
    if echo "$ADDED_LINES" | grep -qE 'AKIA[0-9A-Z]{16}|aws_secret_access_key[[:space:]]*[:=]'; then
      echo '{"decision": "deny", "reason": "Secret & Leak Sentinel: Staged AWS credentials detected. Remove cloud access keys from commit diff."}'
      exit 0
    fi

    # C. Host Path Leaks
    if echo "$ADDED_LINES" | grep -qiE 'C:\\+Users\\+[a-zA-Z0-9_-]+|/home/[a-zA-Z0-9_-]+'; then
      # Filter out generic user placeholders
      LEAK=$(echo "$ADDED_LINES" | grep -oiE 'C:\\+Users\\+[a-zA-Z0-9_-]+|/home/[a-zA-Z0-9_-]+' | grep -vEi 'username|runner|circleci|root|node|ubuntu|user' | head -n 1 || true)
      if [ -n "$LEAK" ]; then
        echo "{\"decision\": \"deny\", \"reason\": \"Secret & Leak Sentinel: Local host filesystem path / username leak detected ($LEAK). Use relative paths or environment variables.\"}"
        exit 0
      fi
    fi
  fi
fi

echo '{"decision": "allow"}'
