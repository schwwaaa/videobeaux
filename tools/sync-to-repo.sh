#!/usr/bin/env bash
# Copy this working tree (videobeaux-gui) into the real git repository (videobeaux) — additively.
#
#   tools/sync-to-repo.sh            # dry run: shows what would change
#   tools/sync-to-repo.sh --apply    # copies the files
#   tools/sync-to-repo.sh --apply --repo /path/to/videobeaux
#
# - never deletes anything in the repo (no --delete)
# - never overwrites files that are NEWER in the repo than here (rsync --update): your edits made directly in the
#   repo survive; use --force-all to override that
# - skips build output, caches, virtualenvs, models, installers and test reports
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$HERE/../videobeaux" 2>/dev/null && pwd || true)"
APPLY=0; FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --force-all) FORCE=1; shift ;;
    --repo) REPO="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
[ -d "$REPO/.git" ] || { echo "Not a git repository: ${REPO:-<unset>} (use --repo PATH)"; exit 1; }

FLAGS=(-a --itemize-changes --exclude='.git/' --exclude='node_modules/' --exclude='venv/' --exclude='.venv/' --exclude='out/'
       --exclude='dist/' --exclude='__pycache__/' --exclude='*.egg-info/' --exclude='.DS_Store' --exclude='gui/resources/'
       --exclude='models/' --exclude='.tools/' --exclude='*.onnx' --exclude='voices-*.bin' --exclude='tests/smoke/reports/'
       --exclude='tools/ffmpeg-build/out/' --exclude='.claude/' --exclude='gui/.harness*' --exclude='media/' --exclude='outputs/' --exclude='ui_design/_snapshots/')
[ "$FORCE" = 1 ] || FLAGS+=(--update)
[ "$APPLY" = 1 ] || FLAGS+=(--dry-run)

echo "from: $HERE"; echo "to:   $REPO"; [ "$APPLY" = 1 ] && echo "(applying)" || echo "(dry run — add --apply to copy)"
rsync "${FLAGS[@]}" "$HERE/" "$REPO/" | grep -v '^\.d' | sed 's/^/  /' || true
echo "done. Review with:  git -C \"$REPO\" status"
