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

# Two very different kinds of take, and they must not be confused.
#
#   (default)      read the spike sentences aloud — tests whether the transcriber
#                  preserves deliberate mistakes (DEC-011)
#   --prompt N     answer prompt N out loud, unscripted — the only kind of sample
#                  the fluency metrics can read (DEC-010)
#
# Reading aloud degrades every fluency number exactly the way hesitation does, so
# a read take would have the metrics diagnose a stammer that is not there.
if [[ "${1:-}" == "--prompt" ]]; then
  INDEX="${2:-1}"
  DURATION="${3:-45}"
  DEVICE="${4:-0}"
  OUT="$DIR/audio/answer.wav"

  mkdir -p "$DIR/audio"
  # The prompts file is located from $ROOT rather than from __file__: this script
  # is piped into Python on stdin, where __file__ is "<stdin>" and resolves to the
  # working directory instead of to this file.
  "$PYTHON" - "$INDEX" "$ROOT" <<'PY'
import sys, yaml, pathlib
spec = yaml.safe_load(
    (pathlib.Path(sys.argv[2]) / "data" / "prompts.yaml").read_text(encoding="utf-8")
)
prompt = spec["prompts"][int(sys.argv[1]) - 1]
print(f"\n  ANSWER THIS OUT LOUD. Do not write anything down first.\n")
print(f"    {' '.join(prompt['text'].split())}\n")
print(f"    ({prompt['hint_es']})\n")
print("  Hesitating is fine — that IS the measurement. If you blank, keep")
print("  talking anyway: silence and false starts are the data.\n")
PY
else
  DURATION="${1:-100}"
  DEVICE="${2:-0}"
  mkdir -p "$DIR/audio"
  # Single source of truth for the sentences: they live in analyze.py.
  "$PYTHON" "$DIR/analyze.py" --print-script
fi

cat <<EOF
  Speak up and stay close to the mic. The previous take averaged -39 dB and
  Whisper dropped short words because of it.

  Recording ${DURATION}s from device ${DEVICE}, starting in 3 seconds.
  Press q when you are done.

EOF

sleep 3

ffmpeg -hide_banner -loglevel warning \
  -f avfoundation -i ":${DEVICE}" \
  -t "${DURATION}" -ar 16000 -ac 1 \
  -y "$OUT"

echo ""
echo "Saved to $OUT"

# Judge the take by its peak, not its mean: mean_volume averages in the pauses
# between sentences, so a perfectly audible recording with deliberate gaps scores
# as "quiet" and gets rejected for no reason. Peak tells us whether the voice
# actually reached the mic; loudness normalisation below fixes everything else.
LEVELS=$(ffmpeg -hide_banner -i "$OUT" -af volumedetect -f null - 2>&1 || true)
MEAN=$(echo "$LEVELS" | awk -F': ' '/mean_volume/ {print $2}' | awk '{print $1}')
PEAK=$(echo "$LEVELS" | awk -F': ' '/max_volume/ {print $2}' | awk '{print $1}')

echo "Level check:  mean ${MEAN} dB   peak ${PEAK} dB"

if [[ -n "${PEAK:-}" ]] && awk -v p="$PEAK" 'BEGIN {exit !(p < -30)}'; then
  cat <<EOF

  TOO QUIET. The loudest moment barely reached the microphone, so there is no
  signal to recover. Move closer, speak up, and record again.

EOF
  exit 1
fi

# Every take gets normalised to a consistent loudness so that transcription
# results are comparable across sessions and never confounded by mic distance.
NORM="${OUT%.wav}_norm.wav"
ffmpeg -hide_banner -loglevel error -i "$OUT" \
  -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 16000 -ac 1 -y "$NORM"

echo "Normalised to $NORM"
echo ""
if [[ "${1:-}" == "--prompt" ]]; then
  echo "Now run:  .venv/bin/python -m speaklens.cli $OUT"
else
  echo "Now run:  .venv/bin/python spike/analyze.py $NORM"
fi
