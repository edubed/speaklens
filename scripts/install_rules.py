"""
Install the Spanish-L1 rules into LanguageTool.

LanguageTool ships grammar-l2-de.xml and grammar-l2-fr.xml for German and French
speakers learning English, but has no Spanish equivalent — which is why setting
mother_tongue='es' does nothing: the file it would load does not exist, and the
list of languages that have one is fixed in LanguageTool's own code.

Two other routes were tried and rejected:

  * the `rulesFile` config key, which the client accepts but which never
    registers the rules;
  * dropping the file in as grammar-l2-es.xml, which LanguageTool ignores for
    the same reason mother_tongue='es' does nothing.

What does work is injecting the rules into en/grammar.xml, which LanguageTool
loads for every English variant. That file belongs to LanguageTool, so this
script is written to be safe about touching it: it backs the original up once,
wraps the injection in marker comments, and is idempotent. Re-run it after any
LanguageTool reinstall — setup.sh does that (DEC-015).

    python scripts/install_rules.py            install or update
    python scripts/install_rules.py --remove   restore LanguageTool's file
    python scripts/install_rules.py --check    report status only
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

BEGIN = "<!-- BEGIN speaklens spanish-l1 rules — installed by scripts/install_rules.py -->"
END = "<!-- END speaklens spanish-l1 rules -->"

SOURCE = Path(__file__).resolve().parent.parent / "rules" / "grammar-l2-es.xml"


def find_grammar_file() -> Path:
    """Locate en/grammar.xml inside the LanguageTool the client downloaded."""
    cache = Path.home() / ".cache" / "language_tool_python"
    candidates = sorted(cache.glob("LanguageTool-*/org/languagetool/rules/en/grammar.xml"))
    if not candidates:
        raise SystemExit(
            "LanguageTool not found under ~/.cache/language_tool_python.\n"
            "Run any check once so the client downloads it, then re-run this."
        )
    return candidates[-1]


def extract_categories(source: Path) -> str:
    """Pull the <category> blocks out of our rule file, leaving its <rules> root behind."""
    xml = source.read_text(encoding="utf-8")
    blocks = re.findall(r"<category\b.*?</category>", xml, re.S)
    if not blocks:
        raise SystemExit(f"no <category> blocks found in {source}")
    return "\n".join(blocks)


def strip_existing(xml: str) -> str:
    return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), "", xml, flags=re.S).rstrip() + "\n"


def count_rules(payload: str) -> int:
    return len(re.findall(r"<rule\b", payload))


def main() -> int:
    target = find_grammar_file()
    backup = target.with_suffix(".xml.speaklens-backup")
    xml = target.read_text(encoding="utf-8")
    installed = BEGIN in xml

    if "--check" in sys.argv:
        print(f"grammar.xml: {target}")
        print(f"estado:      {'instalado' if installed else 'no instalado'}")
        print(f"backup:      {'sí' if backup.exists() else 'no'}")
        return 0

    # Keep one pristine copy of LanguageTool's own file, taken before we ever edit it.
    if not backup.exists():
        shutil.copy2(target, backup)

    if "--remove" in sys.argv:
        if not installed:
            print("no había nada instalado")
            return 0
        target.write_text(strip_existing(xml), encoding="utf-8")
        print(f"reglas removidas de {target.name}")
        return 0

    payload = extract_categories(SOURCE)
    body = strip_existing(xml)

    if "</rules>" not in body:
        raise SystemExit(f"unexpected format: no closing </rules> in {target}")

    injected = body.replace("</rules>", f"{BEGIN}\n{payload}\n{END}\n</rules>", 1)
    target.write_text(injected, encoding="utf-8")

    print(f"{count_rules(payload)} reglas instaladas en {target.name}")
    print(f"backup del original: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
