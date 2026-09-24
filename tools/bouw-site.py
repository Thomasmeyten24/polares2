#!/usr/bin/env python3
"""
Bouwt de site en zet wat online hoort in dist/. Cloudflare publiceert die map.

Cloudflare draait dit bij elke push naar main, dus ook na elke wijziging in het
CMS. Het doet drie dingen, en stopt bij de eerste fout; dan publiceert Cloudflare
niets en blijft de vorige versie gewoon online staan:

1. De pagina's maken uit de gegevens: de deelafbeeldingen en de pagina's van
   Blijf op koers uit data/berichten.json, en het team uit data/team.json.
2. De consistentiecontrole draaien.
3. Kopiëren wat online moet. De repo bevat meer dan de site: tools/, data/,
   notities als TE-DOEN.md. In plaats van een lijst met wat níet mee mag (die
   vergeet je aan te vullen) staat hier wat wél mee mag. Een nieuwe pagina op
   het hoogste niveau komt vanzelf mee; een nieuwe map moet hier bij.

De deelafbeeldingen en het omzetten van portretten vragen Pillow en fontTools.
Op Cloudflare en in GitHub Actions installeert dit script ze zelf, in een
tijdelijke map. Lokaal gebruikt het wat er is; ontbreekt Pillow, dan blijven de
bestaande afbeeldingen staan.

    python3 tools/bouw-site.py

Na een wijziging in het CMS lopen de gegenereerde bestanden in de repo zelf
achter; de site online klopt wel, want die wordt hier gebouwd. Wie lokaal werkt,
draait dit script eerst.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UIT = ROOT / "dist"

# losse bestanden in de hoofdmap
BESTANDEN = [
    "favicon.svg", "favicon.ico", "apple-touch-icon.png",
    "robots.txt", "site.webmanifest", "sitemap.xml",
    # de regels voor Cloudflare: doorsturingen en headers
    "_redirects", "_headers",
]
# mappen die in hun geheel meegaan
MAPPEN = ["assets", "blijf-op-koers"]


# in een bouwomgeving (Cloudflare, GitHub Actions) mogen we zelf installeren
IN_BUILD = bool(os.environ.get("WORKERS_CI") or os.environ.get("CI"))
PAKKETTEN = ["pillow", "fonttools", "brotli"]


def pillow_pad() -> str | None:
    """Een map waarin Pillow en fontTools staan, of None als het niet lukt.
    In een tijdelijke map (--target) en niet in de systeem-Python: die mag
    op moderne bouwomgevingen niet aangepast worden."""
    try:
        import PIL, fontTools  # noqa: F401
        return ""
    except ImportError:
        pass
    if not IN_BUILD:
        return None
    doel = tempfile.mkdtemp(prefix="polares-pip-")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                        "--target", doel, *PAKKETTEN], capture_output=True, text=True)
    if r.returncode != 0:
        print("waarschuwing: Pillow kon niet geïnstalleerd worden; de bestaande afbeeldingen blijven staan")
        print(r.stderr.strip()[-600:])
        return None
    return doel


def stap(naam: str, args: list[str], extra_pad: str | None = None) -> None:
    env = dict(os.environ)
    if extra_pad:
        env["PYTHONPATH"] = extra_pad + os.pathsep + env.get("PYTHONPATH", "")
    print(f"── {naam}", flush=True)
    r = subprocess.run([sys.executable, *args], cwd=ROOT, env=env)
    if r.returncode != 0:
        print(f"\nFOUT bij '{naam}'. Er wordt niets gepubliceerd; de vorige versie blijft online.")
        raise SystemExit(1)


def genereer() -> None:
    pad = pillow_pad()
    if pad is None:
        print("── deelafbeeldingen: overgeslagen (geen Pillow), de bestaande blijven staan", flush=True)
    else:
        # altijd allemaal: een titel die in het CMS wijzigt, moet ook op de kaart wijzigen
        stap("deelafbeeldingen", ["tools/og-afbeeldingen.py", "--alles"], pad)
    stap("berichten", ["tools/berichten.py"])
    stap("team", ["tools/team.py"], pad)
    stap("consistentiecontrole", ["tools/check-consistentie.py"])


def main() -> int:
    genereer()
    print("── dist/", flush=True)
    if UIT.exists():
        shutil.rmtree(UIT)
    UIT.mkdir()

    paginas = sorted(p.name for p in ROOT.glob("*.html"))
    for naam in paginas + BESTANDEN:
        bron = ROOT / naam
        if not bron.exists():
            print(f"FOUT: {naam} ontbreekt", file=sys.stderr)
            return 1
        shutil.copy2(bron, UIT / naam)
    for naam in MAPPEN:
        shutil.copytree(ROOT / naam, UIT / naam, ignore=shutil.ignore_patterns(".*"))

    aantal = sum(1 for p in UIT.rglob("*") if p.is_file())
    grootte = sum(p.stat().st_size for p in UIT.rglob("*") if p.is_file())
    print(f"dist/: {aantal} bestanden, {grootte / 1024 / 1024:.1f} MB ({len(paginas)} pagina's in de hoofdmap)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
