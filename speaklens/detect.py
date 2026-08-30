"""Find mistakes in a transcript and file each one under a theme.

Detection is rule-based on purpose (DEC-004). A 4B model asked to judge grammar
will confidently "correct" sentences that were already right, and a B1 learner
cannot tell the difference — so the model never decides what is wrong, only
explains what LanguageTool already found.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from . import themes as taxonomy

# Homebrew installs openjdk keg-only, so `java` is off the PATH and LanguageTool,
# which runs as a Java process, cannot start. Put it back for this process rather
# than requiring every caller to have sourced scripts/env.sh.
_JAVA_DIRS = ("/opt/homebrew/opt/openjdk/bin", "/usr/local/opt/openjdk/bin")


def ensure_java() -> None:
    if shutil.which("java") and _java_runs():
        return
    for candidate in _JAVA_DIRS:
        if (Path(candidate) / "java").exists():
            os.environ["PATH"] = f"{candidate}{os.pathsep}{os.environ['PATH']}"
            return
    raise SystemExit("no java found — install one with: brew install openjdk")


def _java_runs() -> bool:
    """`java` may exist as the macOS stub that only tells you to install a JDK."""
    import subprocess

    try:
        subprocess.run(["java", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return True


@dataclass(frozen=True)
class Mistake:
    rule_id: str
    theme_id: str
    theme_name: str
    text: str
    suggestion: str
    message: str
    offset: int
    sentence: str


def detect(sentences: list[str] | str, drop_noise: bool = True) -> list[Mistake]:
    """Return the learner mistakes in `sentences`, each filed under a theme.

    Takes a list of sentences rather than one blob because several LanguageTool
    rules — including ours for articles and question word order — only fire at a
    sentence start, and unpunctuated speech hands them no starts to fire at.

    `drop_noise` removes hyphenation, casing and typography findings. They are
    not learner mistakes — when speaking, punctuation is the transcriber's
    invention, not the speaker's — and leaving them in would pad the list with
    findings the speaker never produced.
    """
    import language_tool_python

    if isinstance(sentences, str):
        sentences = [sentences]

    ensure_java()
    tax = taxonomy.load()

    # Two passes, because the two rule shapes want opposite things from the input.
    # Sentence-anchored rules need short, correctly cut sentences. Rules spanning
    # several words need those words to still be together — and pause-based cutting
    # sometimes splits mid-sentence when the speaker hesitates, which is exactly
    # what a learner does. Running both and merging costs one extra pass and stops
    # either failure from silently swallowing mistakes.
    passes = list(sentences)
    whole = " ".join(sentences).strip()
    if whole and whole not in passes:
        passes.append(whole)

    mistakes: list[Mistake] = []
    seen: set[tuple[str, str, str]] = set()

    tool = language_tool_python.LanguageTool("en-US")
    try:
        for chunk in passes:
            for m in tool.check(chunk):
                theme = tax.classify(m.rule_id, m.category)
                if drop_noise and theme.noise:
                    continue
                key = (m.rule_id, m.matched_text, m.replacements[0] if m.replacements else "")
                if key in seen:
                    continue
                seen.add(key)
                mistakes.append(
                    Mistake(
                        rule_id=m.rule_id,
                        theme_id=theme.id,
                        theme_name=theme.name_es,
                        text=m.matched_text,
                        suggestion=key[2],
                        message=m.message,
                        offset=m.offset,
                        sentence=chunk,
                    )
                )
    finally:
        tool.close()
    return mistakes

