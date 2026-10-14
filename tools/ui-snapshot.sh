#!/usr/bin/env bash
# Save / list / restore the GUI source so a design experiment can be undone in one command.
#
#   tools/ui-snapshot.sh save <name>      # tar gui/src/{renderer,main,preload} + gui/package.json
#   tools/ui-snapshot.sh list
#   tools/ui-snapshot.sh restore <name>   # puts those paths back exactly as saved (the current state is saved first as "before-restore")
#
# Snapshots live in ui_design/_snapshots/ (excluded from sync-to-repo.sh). videobeaux-gui has no git on purpose.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$HERE/ui_design/_snapshots"
PATHS=(gui/src/renderer gui/src/main gui/src/preload gui/package.json gui/index.html)
mkdir -p "$DIR"

existing_paths() { local p; for p in "${PATHS[@]}"; do [ -e "$HERE/$p" ] && echo "$p"; done; }

save() {
  local name="${1:?usage: ui-snapshot.sh save <name>}"
  local file="$DIR/$(date +%Y%m%d-%H%M%S)-$name.tgz"
  ( cd "$HERE" && tar -czf "$file" --exclude='node_modules' --exclude='.DS_Store' $(existing_paths) )
  echo "saved $file ($(du -h "$file" | cut -f1))"
}

find_snap() {  # newest snapshot whose name part matches
  ls -1 "$DIR"/*-"$1".tgz 2>/dev/null | sort | tail -1
}

case "${1:-}" in
  save) save "${2:-}" ;;
  list) ls -1 "$DIR" 2>/dev/null | sed 's/^/  /' || true ;;
  restore)
    snap="$(find_snap "${2:?usage: ui-snapshot.sh restore <name>}")"
    [ -n "$snap" ] || { echo "no snapshot named '$2' (try: $0 list)"; exit 1; }
    save before-restore
    # remove what the snapshot covers, then unpack it, so files added since the snapshot disappear too
    ( cd "$HERE" && for p in $(existing_paths); do rm -rf "$p"; done && tar -xzf "$snap" )
    echo "restored $snap"
    ;;
  *) echo "usage: $0 save <name> | list | restore <name>"; exit 2 ;;
esac
