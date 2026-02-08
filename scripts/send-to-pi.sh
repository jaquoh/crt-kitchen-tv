#!/usr/bin/env bash
set -euo pipefail

# CRT-friendly transcode + optional upload to Pi
#
# Output profile (Pi Zero friendly):
# - H.264 Baseline, Level 3.0
# - 640x480 max, preserve aspect ratio, padded to exact 640x480
# - yuv420p
# - 25 fps (PAL-ish, CRT friendly)
# - AAC mono
#
# Requires: ffmpeg
# Optional: rsync (for upload via SSH)

usage() {
  cat <<'EOF'
Usage:
  send-to-pi.sh <input_file> [options]

Options:
  --out-dir <dir>       Local output directory (default: ./out)
  --name <name>         Base name for output (default: derived from input)
  --pi <user@host>      Upload via SSH/rsync to this Pi (optional)
  --dest <folder>       Destination collection folder on Pi (default: inbox)
  --remote-root <path>  Remote media root (default: /var/lib/crt-kitchen-tv/media)
  --no-upload           Only transcode locally
  --keep-temp           Keep temp file if used (currently not used)
  -h, --help            Show this help

Examples:
  ./scripts/send-to-pi.sh video.mov
  ./scripts/send-to-pi.sh video.mp4 --out-dir ~/Videos/crt
  ./scripts/send-to-pi.sh video.mp4 --pi crt@192.168.178.101 --dest inbox
EOF
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

INPUT="${1:-}"
if [[ -z "${INPUT}" || "${INPUT}" == "-h" || "${INPUT}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ ! -f "${INPUT}" ]]; then
  echo "Input file not found: ${INPUT}" >&2
  exit 1
fi

shift || true

OUT_DIR="./out"
BASENAME=""
PI_SSH=""
DEST="inbox"
REMOTE_ROOT="/var/lib/crt-kitchen-tv/media"
DO_UPLOAD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --name) BASENAME="$2"; shift 2 ;;
    --pi) PI_SSH="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --remote-root) REMOTE_ROOT="$2"; shift 2 ;;
    --no-upload) DO_UPLOAD=0; shift 1 ;;
    --keep-temp) shift 1 ;; # placeholder
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

need_cmd ffmpeg

mkdir -p "${OUT_DIR}"

if [[ -z "${BASENAME}" ]]; then
  BASENAME="$(basename "${INPUT}")"
  BASENAME="${BASENAME%.*}"
  # light sanitize: spaces -> underscores
  BASENAME="${BASENAME// /_}"
fi

OUTPUT="${OUT_DIR}/${BASENAME}_crt.mp4"

echo "== Transcoding for CRT =="
echo "Input : ${INPUT}"
echo "Output: ${OUTPUT}"

# Scale to fit within 640x480, keep aspect ratio, pad to 640x480.
# Also force yuv420p (important for compatibility) and baseline profile.
#
# Notes:
# - 25fps is CRT-friendly and reduces CPU load vs 30/60fps.
# - AAC mono keeps decoding easy and avoids stereo overhead.
# - Bitrate defaults are tuned for good quality on a small CRT.
ffmpeg -y -hide_banner \
  -i "${INPUT}" \
  -vf "scale=w=640:h=480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2,format=yuv420p,fps=25" \
  -c:v libx264 -profile:v baseline -level 3.0 -pix_fmt yuv420p \
  -preset slow -b:v 700k -maxrate 900k -bufsize 1400k \
  -g 50 -keyint_min 50 -sc_threshold 0 \
  -c:a aac -ac 1 -b:a 96k \
  -movflags +faststart \
  "${OUTPUT}"

echo "== Transcode complete =="

# Optional upload via rsync over SSH
if [[ ${DO_UPLOAD} -eq 1 && -n "${PI_SSH}" ]]; then
  need_cmd rsync
  REMOTE_DIR="${REMOTE_ROOT}/${DEST}/"
  echo "== Uploading to Pi via rsync =="
  echo "Target: ${PI_SSH}:${REMOTE_DIR}"
  rsync -av --progress "${OUTPUT}" "${PI_SSH}:${REMOTE_DIR}"
  echo "== Upload complete =="
else
  echo "== Upload skipped (no --pi provided or --no-upload set) =="
  echo "Tip: To upload via SSH: --pi crt@<pi-ip> --dest inbox"
  echo "Tip: If using Samba, just copy ${OUTPUT} into your mounted share."
fi

echo "Done."