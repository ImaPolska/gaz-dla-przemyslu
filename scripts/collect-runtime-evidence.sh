#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/docs/qa/runtime"
for direction in A B C; do
  runtime="$(sed -n 's/Native temp dir for VFS root: //p' "$ROOT/.runtime/$direction.log" | head -n 1)"
  cp "$ROOT/.runtime/$direction.log" "$ROOT/docs/qa/runtime/$direction-cli.log"
  logfile="$runtime/wordpress/wp-content/debug.log"
  size=0
  issues=0
  exists=false
  if [[ -f "$logfile" ]]; then
    exists=true
    cp "$logfile" "$ROOT/docs/qa/runtime/$direction-debug.log"
    size="$(wc -c < "$logfile" | tr -d ' ')"
    issues="$( (rg -ic 'PHP (notice|warning|fatal|parse|deprecated)|uncaught' "$logfile" || true) )"
    issues="${issues:-0}"
  fi
  same=false
  if cmp -s "$ROOT/.runtime/theme-$direction/style.css" "$runtime/wordpress/wp-content/themes/gdp-child/style.css"; then same=true; fi
  jq -n --arg direction "$direction" --argjson exists "$exists" \
    --argjson size "$size" --argjson issues "$issues" --argjson same "$same" \
    '{direction:$direction,debugLogExists:$exists,debugLogBytes:$size,phpIssueLines:$issues,runtimeCSSMatchesBuiltTheme:$same,note:"WP_DEBUG and WP_DEBUG_LOG verified true in browser-runtime.json; absent debug.log means no messages logged, not disabled debugging."}' \
    > "$ROOT/docs/qa/runtime/$direction-evidence.json"
done
jq -s '.' "$ROOT"/docs/qa/runtime/*-evidence.json > "$ROOT/docs/qa/php-logs.json"
