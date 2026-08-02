#!/usr/bin/env bash
# Records a mono 16 kHz WAV from the default microphone, which is what Whisper wants.
#
#   ./record.sh --list      list available audio input devices
#   ./record.sh             record 60s from device 0
#   ./record.sh 90 1        record 90s from device 1
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/audio/attempt.wav"

if [[ "${1:-}" == "--list" ]]; then
  echo "Audio input devices (look for your microphone, note its index):"
  ffmpeg -hide_banner -f avfoundation -list_devices true -i "" 2>&1 | sed -n '/AVFoundation audio devices/,$p'
  exit 0
fi

DURATION="${1:-60}"
DEVICE="${2:-0}"

mkdir -p "$DIR/audio"

cat <<EOF

  Recording ${DURATION}s from audio device ${DEVICE}.

  Read these five sentences out loud, WITH the mistakes exactly as written.
  Pause about a second between them. Speak at your normal pace.

    1. Yesterday I go to the meeting.
    2. I have thirty two years old.
    3. She don't like the project.
    4. I am agree with you.
    5. Explain me the problem.

  Starting in 3 seconds. Press q to stop early.

EOF

sleep 3

ffmpeg -hide_banner -loglevel warning \
  -f avfoundation -i ":${DEVICE}" \
  -t "${DURATION}" -ar 16000 -ac 1 \
  -y "$OUT"

echo ""
echo "Saved to $OUT"
echo "Now run:  python spike/analyze.py"
