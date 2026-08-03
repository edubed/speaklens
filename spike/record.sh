#!/usr/bin/env bash
# Records a mono 16 kHz WAV from the microphone, which is what Whisper wants,
# then checks the level — the first spike run lost words to a too-quiet recording.
#
#   ./record.sh --list      list available audio input devices
#   ./record.sh             record 100s from device 0
#   ./record.sh 120 1       record 120s from device 1
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$DIR")"
OUT="$DIR/audio/attempt.wav"
PYTHON="$ROOT/.venv/bin/python"

if [[ "${1:-}" == "--list" ]]; then
  echo "Audio input devices (look for your microphone, note its index):"
  ffmpeg -hide_banner -f avfoundation -list_devices true -i "" 2>&1 \
    | sed -n '/AVFoundation audio devices/,$p' | grep -v "Error opening" || true
  exit 0
fi

DURATION="${1:-100}"
DEVICE="${2:-0}"

mkdir -p "$DIR/audio"

# Single source of truth for the sentences: they live in analyze.py.
"$PYTHON" "$DIR/analyze.py" --print-script

cat <<EOF
  Speak up and stay close to the mic. The previous take averaged -39 dB and
  Whisper dropped short words because of it.

  Recording ${DURATION}s from device ${DEVICE}, starting in 3 seconds.
  Press q when you finish the last sentence.

EOF

sleep 3

ffmpeg -hide_banner -loglevel warning \
  -f avfoundation -i ":${DEVICE}" \
  -t "${DURATION}" -ar 16000 -ac 1 \
  -y "$OUT"

echo ""
echo "Saved to $OUT"

LEVELS=$(ffmpeg -hide_banner -i "$OUT" -af volumedetect -f null - 2>&1 || true)
MEAN=$(echo "$LEVELS" | awk -F': ' '/mean_volume/ {print $2}' | awk '{print $1}')
PEAK=$(echo "$LEVELS" | awk -F': ' '/max_volume/ {print $2}' | awk '{print $1}')

echo "Level check:  mean ${MEAN} dB   peak ${PEAK} dB"

if [[ -n "${MEAN:-}" ]] && awk -v m="$MEAN" 'BEGIN {exit !(m < -32)}'; then
  cat <<EOF

  TOO QUIET. Below about -32 dB mean, the transcriber starts dropping
  unstressed words and the results stop meaning anything. Move closer to the
  mic, raise your voice, and record again before analysing.

EOF
  exit 1
fi

echo ""
echo "Level is fine. Now run:  .venv/bin/python spike/analyze.py"
