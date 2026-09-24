#!/usr/bin/env python3
"""
Kopieert het contactformulier van index.html naar de andere pagina's.

De site heeft geen build-stap, dus staan de kop, de voet en het menu op elke
pagina opnieuw. Voor het contactformulier is dat te veel om met de hand gelijk
te houden: het is bijna driehonderd regels stijl, opmaak en JavaScript, en het
moet straks in één keer mee als het naar contact.php gaat versturen.

index.html is de bron. Daar staan drie blokken tussen merktekens:

    /* BEGIN_CFORM */ ... /* EIND_CFORM */      in de stylesheet
    <!-- BEGIN_CFORM --> ... <!-- EIND_CFORM -->  de dialoog zelf
    // BEGIN_CFORM ... // EIND_CFORM               het script

Dit script schrijft die drie in elke doelpagina tussen dezelfde merktekens.

contact.html is anders: daar staat het formulier op de pagina zelf, niet in
een venster. Die pagina krijgt de stijl en het script, en van de opmaak alleen
de velden, het stuk tussen

    <!-- BEGIN_CFORM_VELDEN --> ... <!-- EIND_CFORM_VELDEN -->

Kop, knoppen en melding horen bij die pagina zelf.

    python tools/gedeeld.py            # schrijft de pagina's bij
    python tools/gedeeld.py --check    # controleert alleen, exitcode 1 bij verschil

Draait op de standaardbibliotheek, net als de andere controles.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRON = ROOT / "index.html"
DOELEN = [
    ROOT / "uw-familie.html",
    ROOT / "uw-bedrijf.html",
    ROOT / "ons-team.html",
    ROOT / "blijf-op-koers.html",
    ROOT / "tools" / "sjabloon-bericht.html",
]

# Pagina's met het formulier op de pagina zelf in plaats van in een venster.
OP_PAGINA = [ROOT / "contact.html"]

# merk, begin, eind. De drie talen hebben elk hun eigen commentaarvorm.
# (?!_) houdt BEGIN_CFORM_VELDEN buiten het begin van het hele venster.
BLOKKEN = [
    ("css", r"/\* BEGIN_CFORM[^*]*\*/", r"/\* EIND_CFORM \*/"),
    ("markup", r"<!-- BEGIN_CFORM(?!_)[^>]*-->", r"<!-- EIND_CFORM -->"),
    ("js", r"// BEGIN_CFORM[^\n]*", r"// EIND_CFORM"),
]
VELDEN = ("velden", r"<!-- BEGIN_CFORM_VELDEN[^>]*-->", r"<!-- EIND_CFORM_VELDEN -->")

# De berichtpagina's staan een map dieper, dus hun verwijzingen ook.
DIEPER = {"sjabloon-bericht.html"}


def haal(tekst: str, begin: str, eind: str, waar: str) -> str:
    m = re.search(begin + r"(.*?)" + eind, tekst, re.S)
    if not m:
        raise SystemExit(f"merktekens van dit blok niet gevonden in {waar}")
    return m.group(1)


def zet(tekst: str, begin: str, eind: str, inhoud: str, waar: str) -> str:
    patroon = re.compile("(" + begin + ")(.*?)(" + eind + ")", re.S)
    if not patroon.search(tekst):
        raise SystemExit(f"merktekens van dit blok niet gevonden in {waar}")
    return patroon.sub(lambda m: m.group(1) + inhoud + m.group(3), tekst, count=1)


def bouw() -> dict[Path, str]:
    bron = BRON.read_text(encoding="utf-8")
    stukken = {merk: haal(bron, b, e, BRON.name) for merk, b, e in BLOKKEN}

    uit = {}
    for doel in DOELEN:
        tekst = doel.read_text(encoding="utf-8")
        for merk, b, e in BLOKKEN:
            inhoud = stukken[merk]
            if doel.name in DIEPER:
                inhoud = inhoud.replace('href="index.html', 'href="../index.html')
            tekst = zet(tekst, b, e, inhoud, doel.name)
        uit[doel] = tekst

    velden = haal(bron, VELDEN[1], VELDEN[2], BRON.name)
    for doel in OP_PAGINA:
        tekst = doel.read_text(encoding="utf-8")
        for merk, b, e in BLOKKEN:
            if merk != "markup":
                tekst = zet(tekst, b, e, stukken[merk], doel.name)
        tekst = zet(tekst, VELDEN[1], VELDEN[2], velden, doel.name)
        uit[doel] = tekst
    return uit


def main() -> int:
    gewenst = bouw()
    anders = [p for p, inhoud in gewenst.items()
              if p.read_text(encoding="utf-8") != inhoud]

    if "--check" in sys.argv:
        if anders:
            print(f"FOUT: het contactformulier loopt niet meer gelijk met {BRON.name}.")
            for p in anders:
                print(f"      anders: {p.relative_to(ROOT)}")
            print("      Draai 'python tools/gedeeld.py' en commit het resultaat.")
            return 1
        print(f"{len(gewenst)} pagina's dragen hetzelfde contactformulier als {BRON.name}.")
        return 0

    if not anders:
        print("Niets te doen: alle pagina's liepen al gelijk.")
        return 0
    for p in anders:
        p.write_text(gewenst[p], encoding="utf-8")
        print(f"bijgewerkt: {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
