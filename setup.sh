#!/usr/bin/env bash
# Take a fresh clone to a working diagnostic, in one command (DEC-015).
#
#   ./setup.sh           install everything, then prove the detector is armed
#   ./setup.sh --check   prove it, change nothing — after a LanguageTool upgrade
#
# Downloads about 1.9 GB the first time: Whisper medium.en (~1.5 GB) and
# LanguageTool with its Java runtime (~250 MB). Both are cached outside the repo,
# so running this again is fast and safe.
#
# It deliberately does NOT install Ollama. The local LLM wrote the Spanish
# explanations once and they are frozen in data/explanations.yaml (DEC-021);
# nothing generates text while the app runs, so nothing needs a model server. You
# only need Ollama to rewrite those explanations, and on an 8 GB machine you want
# it dead while transcribing anyway.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
STEP=0

step()  { STEP=$((STEP + 1)); printf '\n[%d/%d] %s\n' "$STEP" "$TOTAL" "$1"; }
have()  { command -v "$1" >/dev/null 2>&1; }
die()   { printf '\n  %s\n\n' "$1" >&2; exit 1; }

# Homebrew installs openjdk keg-only, so `java` stays off the PATH on purpose and
# LanguageTool — a Java process — cannot start. Same fix as scripts/env.sh, kept
# inside the repo so cloning is enough and nothing on the machine changes.
for candidate in /opt/homebrew/opt/openjdk/bin /usr/local/opt/openjdk/bin; do
  [ -x "$candidate/java" ] && export PATH="$candidate:$PATH" && break
done

# The one check worth running on its own. LanguageTool's own grammar.xml is where
# our rules live, so upgrading LanguageTool silently reverts the detector from 88%
# recall to 27% — with no error, just fewer mistakes found. This asks the detector
# to catch something only our rules can catch, which is the difference between
# "installed" and "working".
verify() {
  "$PYTHON" - <<'PY'
import sys
from speaklens.detect import detect

found = {m.rule_id for m in detect(["I have hungry", "I am engineer"])}
missing = {"ES_TENER_STATE", "ES_ARTICLE_JOB_AN"} - found
if missing:
    print(f"  las reglas propias no están activas: falta {', '.join(sorted(missing))}")
    print("  corré:  .venv/bin/python scripts/install_rules.py")
    sys.exit(1)
print("  el detector encuentra los errores que sólo nuestras reglas ven")
PY
}

if [ "${1:-}" = "--check" ]; then
  TOTAL=1
  [ -x "$PYTHON" ] || die "no hay virtualenv todavía — corré ./setup.sh sin argumentos"
  step "Verificando la instalación"
  cd "$ROOT" && verify
  echo ""
  exit 0
fi

TOTAL=6
cd "$ROOT"

step "Dependencias del sistema (ffmpeg, openjdk)"
if have brew; then
  # `brew install` on an already-installed formula is a no-op that still prints a
  # wall of text, so ask first and stay quiet when there is nothing to do.
  for formula in ffmpeg openjdk; do
    if brew list --formula "$formula" >/dev/null 2>&1; then
      echo "  $formula ya está"
    else
      echo "  instalando $formula ..."
      brew install "$formula"
    fi
  done
  for candidate in /opt/homebrew/opt/openjdk/bin /usr/local/opt/openjdk/bin; do
    [ -x "$candidate/java" ] && export PATH="$candidate:$PATH" && break
  done
else
  have ffmpeg || die "falta ffmpeg y no hay Homebrew. Instalalo con el gestor de paquetes de tu sistema."
  have java   || die "falta Java y no hay Homebrew. Hace falta un JDK para LanguageTool."
  echo "  sin Homebrew, pero ffmpeg y java ya están"
fi

step "Virtualenv de Python"
if [ ! -x "$PYTHON" ]; then
  # Pinned to 3.12 because that is what the dependency versions in
  # requirements.txt were resolved against; 3.10+ works if that is what you have.
  INTERPRETER="$(command -v python3.12 || command -v python3 || true)"
  [ -n "$INTERPRETER" ] || die "no encontré python3. Instalá Python 3.12."
  "$INTERPRETER" -m venv "$ROOT/.venv"
  echo "  creado con $("$INTERPRETER" -V)"
else
  echo "  ya existe ($("$PYTHON" -V))"
fi
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet -r "$ROOT/requirements.txt"
echo "  dependencias instaladas"

step "Modelo de Whisper (medium.en, ~1.5 GB la primera vez)"
# medium.en rather than small.en because the metric that governs the choice is the
# false-positive rate, not speed: small.en invents corrections the learner cannot
# tell from real ones (DEC-018). int8 on CPU is what speaklens.transcribe asks for,
# so this warms exactly the cache the app will use.
"$PYTHON" - <<'PY'
from faster_whisper import WhisperModel
from speaklens.transcribe import MODEL

WhisperModel(MODEL, device="cpu", compute_type="int8")
print(f"  {MODEL} listo")
PY

step "LanguageTool (~250 MB la primera vez)"
# This has to happen before the rules are installed: the client downloads
# LanguageTool on first use, and install_rules.py edits a file inside that
# download. Skip the order and the next step has nothing to patch.
"$PYTHON" - <<'PY'
import language_tool_python
from speaklens.detect import ensure_java

ensure_java()
tool = language_tool_python.LanguageTool("en-US")
try:
    tool.check("This is a test.")
finally:
    tool.close()
print("  descargado y arranca")
PY

step "Reglas de hispanohablante dentro de LanguageTool"
# Rules LanguageTool ships for nobody: it has grammar-l2-de.xml and
# grammar-l2-fr.xml, and nothing for Spanish. They are injected into its own
# grammar.xml, with a backup and marker comments — see scripts/install_rules.py.
"$PYTHON" "$ROOT/scripts/install_rules.py" | sed 's/^/  /'

step "Verificando que todo funcione"
"$PYTHON" "$ROOT/tests/check.py" | tail -1 | sed 's/^/  /'
verify

cat <<EOF

Listo. Grabá una respuesta y miralo funcionar:

  ./spike/record.sh --prompt 1
  .venv/bin/python -m speaklens.cli spike/audio/answer.wav --open

Si alguna vez actualizás LanguageTool, corré ./setup.sh --check: sus rules se
reinstalan enteras y se llevan puestas las nuestras sin decir nada.

EOF
