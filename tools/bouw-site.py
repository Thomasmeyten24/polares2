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

import base64
import hashlib
import os
import re
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

# Blijf op koers staat voorlopig niet online: de berichten zijn nog
# voorbeelden. In de repo en het CMS blijft alles gewoon werken en
# gecontroleerd; alleen dist/ laat het weg (zie zonder_blijf_op_koers). Op True
# zetten om het weer te publiceren.
BLIJF_OP_KOERS = False


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


def csp_hashes() -> None:
    """Vult in dist/_headers de hashes in van elk script dat in een pagina
    staat. Alleen scripts zonder src en zonder type (of met een JavaScript-
    type): een blok met gegevens, zoals JSON-LD, voert de browser niet uit."""
    hashes = set()
    for pagina in UIT.rglob("*.html"):
        for attrs, inhoud in re.findall(r"<script([^>]*)>([\s\S]*?)</script>", pagina.read_text(encoding="utf-8")):
            if "src=" in attrs:
                continue
            soort = re.search(r'type="([^"]+)"', attrs)
            if soort and soort.group(1) not in ("text/javascript", "module"):
                continue
            digest = base64.b64encode(hashlib.sha256(inhoud.encode("utf-8")).digest()).decode()
            hashes.add(f"'sha256-{digest}'")
    kop = UIT / "_headers"
    tekst = kop.read_text(encoding="utf-8")
    if "__SCRIPT_HASHES__" not in tekst:
        print("FOUT: _headers heeft geen __SCRIPT_HASHES__ voor de Content-Security-Policy", file=sys.stderr)
        raise SystemExit(1)
    tekst = tekst.replace("__SCRIPT_HASHES__", " ".join(sorted(hashes)))
    regel = next(r for r in tekst.splitlines() if "Content-Security-Policy:" in r)
    if len(regel) > 2000:
        print(f"FOUT: de Content-Security-Policy is {len(regel)} tekens; Cloudflare aanvaardt er 2000", file=sys.stderr)
        raise SystemExit(1)
    kop.write_text(tekst, encoding="utf-8")
    print(f"Content-Security-Policy: {len(hashes)} scripts, {len(regel)} tekens")


def zonder_blijf_op_koers() -> None:
    """Haalt Blijf op koers uit dist/: de pagina's, hun deelafbeeldingen, de
    links in menu, voet en 404, en de adressen in de sitemap. Oude links
    (/nieuws van de Craft-site) gaan tijdelijk (302) naar de homepage, zodat
    Google ze niet als definitief verhuisd onthoudt."""
    (UIT / "blijf-op-koers.html").unlink()
    shutil.rmtree(UIT / "blijf-op-koers")
    shutil.rmtree(UIT / "assets" / "og")

    link = r'href="(?:/|\.\./)?blijf-op-koers\.html"'
    patronen = [
        rf'\n[ \t]*<li><a {link}>[^<]*</a></li>',            # voet
        rf'\n[ \t]*<a {link} class="overlay__link"[^>]*>[\s\S]*?</a>',  # menu
        rf'\n[ \t]*<a class="more-link" {link}>[\s\S]*?</a>',  # 404
    ]
    for pagina in UIT.glob("*.html"):
        tekst = pagina.read_text(encoding="utf-8")
        for p in patronen:
            tekst = re.sub(p, "", tekst)
        if "blijf-op-koers" in tekst:
            print(f"FOUT: {pagina.name} verwijst nog naar Blijf op koers", file=sys.stderr)
            raise SystemExit(1)
        pagina.write_text(tekst, encoding="utf-8")

    sitemap = UIT / "sitemap.xml"
    tekst = re.sub(r"\n[ \t]*<url>\s*<loc>[^<]*/blijf-op-koers[^<]*</loc>[\s\S]*?</url>", "",
                   sitemap.read_text(encoding="utf-8"))
    if "blijf-op-koers" in tekst:
        print("FOUT: sitemap.xml bevat nog Blijf op koers", file=sys.stderr)
        raise SystemExit(1)
    sitemap.write_text(tekst, encoding="utf-8")

    regels = []
    for regel in (UIT / "_redirects").read_text(encoding="utf-8").splitlines():
        if "/blijf-op-koers.html" in regel and not regel.startswith("#"):
            regel = regel.split()[0].ljust(41) + "/".ljust(41) + "302"
        regels.append(regel)
    regels += ["", "# Blijf op koers staat voorlopig niet online (BLIJF_OP_KOERS in tools/bouw-site.py)",
               "/blijf-op-koers.html".ljust(41) + "/".ljust(41) + "302",
               "/blijf-op-koers/*".ljust(41) + "/".ljust(41) + "302"]
    (UIT / "_redirects").write_text("\n".join(regels) + "\n", encoding="utf-8")
    print("Blijf op koers: niet gepubliceerd")


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

    if not BLIJF_OP_KOERS:
        zonder_blijf_op_koers()
    csp_hashes()

    aantal = sum(1 for p in UIT.rglob("*") if p.is_file())
    grootte = sum(p.stat().st_size for p in UIT.rglob("*") if p.is_file())
    print(f"dist/: {aantal} bestanden, {grootte / 1024 / 1024:.1f} MB ({len(paginas)} pagina's in de hoofdmap)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
