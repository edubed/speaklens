# Source this before running anything that needs Java or the virtualenv:
#
#   source scripts/env.sh
#
# Homebrew installs openjdk keg-only, meaning it deliberately stays off the PATH
# so it cannot shadow a system Java. LanguageTool runs as a Java process and
# looks for `java` on the PATH, so it has to be added back somewhere. Doing it
# here keeps the requirement inside the repo instead of in ~/.zshrc, so cloning
# the project is enough to run it and nothing on the machine changes.

SPEAKLENS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"

for candidate in \
  /opt/homebrew/opt/openjdk/bin \
  /usr/local/opt/openjdk/bin
do
  if [ -x "$candidate/java" ]; then
    export PATH="$candidate:$PATH"
    break
  fi
done

if ! command -v java >/dev/null 2>&1; then
  echo "warning: no java on PATH — LanguageTool will not start." >&2
  echo "         install one with:  brew install openjdk" >&2
fi

export PATH="$SPEAKLENS_ROOT/.venv/bin:$PATH"
