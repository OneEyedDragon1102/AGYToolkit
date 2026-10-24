#!/usr/bin/env bash
# Anti-Bloat Sentinel: Blocks AI emojis in code and monolithic file dumps

input_json=$(cat)

if [ -z "$input_json" ]; then
    echo '{"decision": "allow"}'
    exit 0
fi

python3 -c "
import sys, json, os, re

try:
    data = json.load(sys.stdin)
    tool = data.get('toolCall', {}).get('name')
    args = data.get('toolCall', {}).get('args', {})

    if tool in ('write_file', 'edit_file'):
        path = args.get('Path', '')
        content = args.get('Content', '') if tool == 'write_file' else args.get('Replacement', '')
        ext = os.path.splitext(path)[1].lower()
        code_exts = {'.java', '.ts', '.js', '.py', '.go', '.rs', '.cpp', '.c', '.cs'}

        if ext in code_exts and content:
            emoji_regex = re.compile(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]')
            if emoji_regex.search(content):
                print(json.dumps({'decision': 'deny', 'reason': f'Anti-Bloat Sentinel: Emojis detected in production code ({path}).'}))
                sys.exit(0)

            if tool == 'write_file' and not args.get('Append', False):
                lines = content.splitlines()
                if len(lines) > 600:
                    print(json.dumps({'decision': 'deny', 'reason': f'Anti-Bloat Sentinel: Monolithic file ({len(lines)} lines in {path}).'}))
                    sys.exit(0)

    print(json.dumps({'decision': 'allow'}))
except Exception:
    print(json.dumps({'decision': 'allow'}))
" <<< "$input_json"
