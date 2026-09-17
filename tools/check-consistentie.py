#!/usr/bin/env python3
"""
Consistentiecontrole voor de Polares-site.

Zolang er geen build-stap is, staan sommige feiten op meerdere plaatsen in de
HTML: contactgegevens, het ondernemingsnummer, de FAQ-teksten. Dit script
controleert of die overal identiek zijn, zodat ze niet stilletjes uit elkaar
groeien. Draaien met:

    python tools/check-consistentie.py

Geeft exitcode 1 bij een fout, zodat het ook als CI-stap kan dienen.
Vervalt zodra de inhoud uit één contentbestand gegenereerd wordt.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fouten: list[str] = []
gedaan: list[str] = []


def lees(naam: str) -> str:
    return (ROOT / naam).read_text(encoding="utf-8")


def zichtbare_tekst(html: str) -> str:
    """Tekst zoals een crawler hem ziet: zonder script, style en tags.

    Tags worden vervangen door een spatie zodat woorden niet aan elkaar
    plakken. Staat er een link midden in een zin, dan levert dat een spatie
    vóór het leesteken op; die halen we weg zodat de vergelijking met de
    structured data niet op zo'n opmaakartefact struikelt.
    """
    body = html.split("<body>", 1)[-1]
    body = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body)
    return re.sub(r"\s+([.,;:!?])", r"\1", body).strip()


def cijfers(s: str) -> str:
    return "".join(c for c in s if c.isdigit())


def controleer(naam: str, ok: bool, detail: str = "") -> None:
    (gedaan if ok else fouten).append(f"{naam}{' — ' + detail if detail else ''}")


index = lees("index.html")
privacy = lees("privacyverklaring.html")
voorwaarden = lees("algemene-voorwaarden.html")

# ── De structured data is de referentie: daar staan de feiten gestructureerd ──
ld_ruw = re.search(r'application/ld\+json">([\s\S]*?)</script>', index)
if not ld_ruw:
    print("FOUT: geen structured data gevonden in index.html")
    sys.exit(1)

try:
    ld = json.loads(ld_ruw.group(1))
    controleer("structured data is geldige JSON", True)
except json.JSONDecodeError as e:
    print(f"FOUT: structured data is geen geldige JSON — {e}")
    sys.exit(1)

knopen = {n["@type"]: n for n in ld["@graph"]}
org = knopen.get("FinancialService")
faq = knopen.get("FAQPage")

if not org or not faq:
    print("FOUT: FinancialService of FAQPage ontbreekt in de graaf")
    sys.exit(1)

# ── 1. Contactgegevens moeten overal gelijk zijn ─────────────────────────────
index_tekst = zichtbare_tekst(index)

telefoon = cijfers(org["telephone"])
gevonden_tel = {cijfers(t) for t in re.findall(r'href="tel:([^"]+)"', index)}
controleer(
    "telefoonnummer overal gelijk",
    gevonden_tel == {telefoon},
    f"structured data {telefoon}, in de pagina {gevonden_tel or 'niets'}",
)

email = org["email"]
gevonden_mail = set(re.findall(r'href="mailto:([^"]+)"', index))
controleer(
    "e-mailadres overal gelijk",
    gevonden_mail == {email},
    f"structured data {email}, in de pagina {gevonden_mail or 'niets'}",
)

adres = org["address"]
for veld in ("streetAddress", "addressLocality", "postalCode"):
    controleer(
        f"adres ({veld}) staat in de pagina",
        adres[veld] in index_tekst,
        adres[veld],
    )

# ── 2. Bedrijfsnaam en ondernemingsnummer: ook op de juridische pagina's ─────
kbo = cijfers(org["vatID"])
naam = org["legalName"]

for bestand, inhoud in (
    ("index.html", index),
    ("privacyverklaring.html", privacy),
    ("algemene-voorwaarden.html", voorwaarden),
):
    tekst = zichtbare_tekst(inhoud)
    controleer(f"juridische naam in {bestand}", naam in tekst, naam)
    controleer(
        f"ondernemingsnummer in {bestand}",
        kbo in cijfers(tekst),
        org["vatID"],
    )

# ── 3. FAQ: markup en zichtbare tekst moeten woordelijk gelijk zijn ──────────
# Google vereist dit, en het is precies het soort tekst dat ongemerkt uiteenloopt.
for vraag in faq["mainEntity"]:
    v = vraag["name"]
    a = vraag["acceptedAnswer"]["text"]
    controleer(f"FAQ-vraag zichtbaar: {v[:45]}", v in index_tekst)
    controleer(f"FAQ-antwoord identiek: {v[:45]}", a in index_tekst)

# ── 4. Interne links en ankers moeten bestaan ────────────────────────────────
ankers = set(re.findall(r'id="([^"]+)"', index))
for href in set(re.findall(r'href="#([^"]+)"', index)):
    controleer(f"anker #{href} bestaat", href in ankers)

for href in set(re.findall(r'href="([a-z0-9-]+\.html)"', index)):
    controleer(f"pagina {href} bestaat", (ROOT / href).exists())

# ── 5. Verwezen bestanden moeten op schijf staan ─────────────────────────────
verwijzingen = set(re.findall(r'(?:src|href)="(assets/[^"]+)"', index))
verwijzingen |= {
    "assets/" + m for m in re.findall(r'href="assets/([^"]+)"', index)
}
for pad in sorted(verwijzingen):
    controleer(f"bestand {pad} aanwezig", (ROOT / pad).exists())

# ── 6. Hoofdstuknummering moet doorlopen ─────────────────────────────────────
# Toen de FAQ erbij kwam moest Contact met de hand van VII naar VIII; zoiets
# wil je niet nog eens over het hoofd zien.
romeins = re.findall(r'class="label[^"]*">([IVX]+) —', index)
verwacht = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][: len(romeins)]
controleer(
    "hoofdstukken doorlopend genummerd",
    romeins == verwacht,
    f"gevonden {romeins}",
)

# De meridiaan houdt een eigen lijst met hoofdstuk-id's bij — die moeten bestaan
meridiaan = re.search(r"var chapters = \[([\s\S]*?)\]\.map", index)
if meridiaan:
    for sectie in re.findall(r"\['([a-z]+)',", meridiaan.group(1)):
        controleer(f"meridiaan verwijst naar bestaande sectie #{sectie}", sectie in ankers)

# ── Uitslag ──────────────────────────────────────────────────────────────────
print(f"\n{len(gedaan)} controles geslaagd")
if fouten:
    print(f"\n{len(fouten)} PROBLEE{'M' if len(fouten) == 1 else 'MEN'}:\n")
    for f in fouten:
        print(f"  FOUT: {f}")
    sys.exit(1)

print("Alles consistent.\n")
