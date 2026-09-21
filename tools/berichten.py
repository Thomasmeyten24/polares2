#!/usr/bin/env python3
"""
Zet data/berichten.json om in de kaarten op blijf-op-koers.html.

Een bericht bestaat op één plaats: data/berichten.json. Dit script schrijft
daaruit de tellers, het uitgelichte bericht en het kaartenraster in de pagina,
tussen de BEGIN/EIND-merktekens. Zo staat de tekst gewoon in de HTML — een
zoekmachine en een linkvoorbeeld zien hem dus — zonder dat iemand hem twee keer
moet bijhouden.

    python tools/berichten.py            # schrijft de pagina bij
    python tools/berichten.py --check    # controleert alleen, exitcode 1 als
                                         # de pagina niet meer klopt met de data

Draait op de standaardbibliotheek, net als de consistentiecontrole.
"""

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "berichten.json"
PAGINA = ROOT / "blijf-op-koers.html"

# Zoveel mogelijk in de taal van de site: het type bepaalt de kleur van het
# label en de tekst op het label.
SOORTEN = {
    "evenement": "Evenement",
    "nieuws": "Nieuws",
    "inzicht": "Inzicht",
}
FILTERS = [
    ("alles", "Alles"),
    ("evenement", "Evenementen"),
    ("nieuws", "Nieuws"),
    ("inzicht", "Inzichten"),
]

STER = ('<svg aria-hidden="true" width="10" height="10" viewBox="0 0 100 100" fill="currentColor">'
        '<path d="M42 0 L58 0 L58 17.8 A24.2 24.2 0 0 0 82.2 42 L100 42 L100 58 L82.2 58 '
        'A24.2 24.2 0 0 0 58 82.2 L58 100 L42 100 L42 82.2 A24.2 24.2 0 0 0 17.8 58 L0 58 '
        'L0 42 L17.8 42 A24.2 24.2 0 0 0 42 17.8 Z"/></svg>')
PIJL = ('<svg aria-hidden="true" viewBox="0 0 37 12" fill="none" stroke="currentColor" '
        'stroke-width="1" width="26" height="9"><line x1="0" y1="6" x2="35" y2="6"/>'
        '<polyline points="30,1 36,6 30,11" fill="none"/></svg>')


def e(tekst: str) -> str:
    return html.escape(str(tekst), quote=True)


def lees_berichten() -> list[dict]:
    berichten = json.loads(DATA.read_text(encoding="utf-8"))
    berichten.sort(key=lambda b: b["datum"], reverse=True)
    return berichten


def tellers(berichten: list[dict]) -> str:
    regels = []
    for sleutel, naam in FILTERS:
        n = len(berichten) if sleutel == "alles" else sum(1 for b in berichten if b["type"] == sleutel)
        actief = ' aria-selected="true" class="filter is-actief"' if sleutel == "alles" else ' aria-selected="false" class="filter"'
        regels.append(
            f'          <button type="button" role="tab" data-soort="{sleutel}"{actief}>'
            f'{naam} <span class="filter__aantal">{n}</span></button>'
        )
    return "\n".join(regels)


def volledig(b: dict) -> str:
    """De hele tekst staat in de pagina; met JavaScript verhuist hij naar het
    leesvenster, zonder blijft hij gewoon leesbaar onder de kaart staan."""
    gegevens = ""
    if b.get("tijd") or b.get("locatie"):
        rijen = []
        if b.get("datumWeergave"):
            wanneer = b["datumWeergave"] + (" · " + b["tijd"] if b.get("tijd") else "")
            rijen.append(("Wanneer", wanneer))
        if b.get("locatie"):
            rijen.append(("Waar", b["locatie"]))
        if b.get("deelname"):
            rijen.append(("Deelname", b["deelname"]))
        binnen = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in rijen)
        gegevens = f'\n          <dl class="lezer__gegevens">{binnen}</dl>'
    return (f'        <div class="bericht__volledig" id="tekst-{e(b["id"])}">{gegevens}\n'
            f'          {b["inhoud"]}\n        </div>')


def kaart(b: dict) -> str:
    soort = b["type"]
    extra = b.get("leestijd", "")
    return f"""      <article class="bericht" data-soort="{e(soort)}" data-id="{e(b["id"])}">
        <p class="bericht__kop">
          <span class="badge badge--{e(soort)}">{e(SOORTEN.get(soort, soort))}</span>
          <time class="bericht__datum" datetime="{e(b["datum"])}">{e(b["datumWeergave"])}</time>
        </p>
        <h3 class="bericht__titel"><button class="bericht__opener" type="button" data-opent="{e(b["id"])}">{e(b["titel"])}</button></h3>
        <p class="bericht__inleiding">{e(b["inleiding"])}</p>
        <p class="bericht__voet">
          <span class="bericht__extra">{e(extra)}</span>
          <span class="bericht__lees" aria-hidden="true">Lees meer {PIJL}</span>
        </p>
{volledig(b)}
      </article>"""


def uitgelicht(b: dict) -> str:
    rijen = []
    if b.get("datumWeergave"):
        wanneer = b["datumWeergave"] + (" · " + b["tijd"] if b.get("tijd") else "")
        rijen.append(("Datum en tijd", wanneer))
    if b.get("locatie"):
        rijen.append(("Locatie", b["locatie"]))
    if b.get("deelname"):
        rijen.append(("Deelname", b["deelname"]))
    meta = "\n".join(
        f'            <div class="uitgelicht__rij"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>'
        for k, v in rijen
    )
    knop = "Programma en aanmelden" if b["type"] == "evenement" else "Lees het volledige bericht"
    kop = "Aankomend evenement" if b["type"] == "evenement" else SOORTEN.get(b["type"], b["type"])
    deadline = f'\n          <p class="uitgelicht__deadline">{e(b["leestijd"])}</p>' if b.get("leestijd") else ""
    return f"""      <article class="uitgelicht" data-soort="{e(b["type"])}" data-id="{e(b["id"])}">
        <div class="uitgelicht__tekst">
          <p class="bericht__kop"><span class="badge badge--{e(b["type"])}">{e(kop)}</span></p>
          <h2 class="uitgelicht__titel"><button class="bericht__opener" type="button" data-opent="{e(b["id"])}">{e(b["titel"])}</button></h2>
          <p class="uitgelicht__inleiding">{e(b["inleiding"])}</p>
          <p><button class="btn bericht__opener" type="button" data-opent="{e(b["id"])}">{e(knop)}</button></p>
        </div>
        <div class="uitgelicht__meta">
          <span class="uitgelicht__ster" aria-hidden="true">{STER}</span>
          <dl>
{meta}
          </dl>{deadline}
        </div>
{volledig(b)}
      </article>"""


def vervang(pagina: str, merk: str, inhoud: str) -> str:
    patroon = re.compile(
        r"([ \t]*<!-- BEGIN_" + merk + r"[^>]*-->)(.*?)([ \t]*<!-- EIND_" + merk + r" -->)",
        re.S,
    )
    if not patroon.search(pagina):
        raise SystemExit(f"merkteken {merk} niet gevonden in {PAGINA.name}")

    def bouw_blok(m: re.Match) -> str:
        tussen = "\n" + inhoud + "\n" if inhoud else "\n"
        return m.group(1) + tussen + m.group(3)

    return patroon.sub(bouw_blok, pagina)


def bouw() -> str:
    berichten = lees_berichten()
    kop = next((b for b in berichten if b.get("uitgelicht")), None)
    rest = [b for b in berichten if b is not kop]

    pagina = PAGINA.read_text(encoding="utf-8")
    pagina = vervang(pagina, "FILTERS", tellers(berichten))
    pagina = vervang(pagina, "UITGELICHT", uitgelicht(kop) if kop else "")
    pagina = vervang(pagina, "BERICHTEN", "\n\n".join(kaart(b) for b in rest))
    return pagina


def main() -> int:
    nieuw = bouw()
    if "--check" in sys.argv:
        if nieuw != PAGINA.read_text(encoding="utf-8"):
            print(f"FOUT: {PAGINA.name} loopt niet meer gelijk met {DATA.name}.")
            print("      Draai 'python tools/berichten.py' en commit het resultaat.")
            return 1
        print(f"{PAGINA.name} loopt gelijk met {DATA.name}.")
        return 0
    if nieuw == PAGINA.read_text(encoding="utf-8"):
        print("Niets te doen: de pagina liep al gelijk met de gegevens.")
        return 0
    PAGINA.write_text(nieuw, encoding="utf-8")
    print(f"{PAGINA.name} bijgewerkt uit {DATA.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
