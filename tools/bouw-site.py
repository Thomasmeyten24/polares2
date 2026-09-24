#!/usr/bin/env python3
"""
Zet de bestanden die online horen in dist/. Cloudflare publiceert die map.

De repo bevat meer dan de site: de hulpscripts in tools/, de berichten in
data/, notities als TE-DOEN.md. Die horen niet op een openbare server. In
plaats van een lijst met wat níet mee mag (die vergeet je aan te vullen) staat
hier wat wél mee mag. Een nieuwe pagina op het hoogste niveau komt vanzelf mee;
een nieuwe map moet hier bij.

Cloudflare draait dit bij elke push naar main, vóór het publiceren:

    python3 tools/bouw-site.py

Alleen de standaardbibliotheek, zodat de bouwomgeving niets hoeft te installeren.
"""

import shutil
import sys
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


def main() -> int:
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
