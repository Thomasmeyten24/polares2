#!/usr/bin/env python3
"""
Zet data/berichten.json om in de pagina's van Blijf op koers.

Een bericht bestaat op één plaats: data/berichten.json. Dit script schrijft
daaruit drie dingen:

  1. blijf-op-koers.html        het overzicht: tellers, uitgelicht bericht en
                                het kaartenraster
  2. blijf-op-koers/<id>.html   een eigen pagina per bericht, uit
                                tools/sjabloon-bericht.html
  3. sitemap.xml                de adressen van die pagina's

Elk bericht heeft een eigen adres omdat dat de enige manier is om er vanuit
Google of vanaf sociale media rechtstreeks op te landen: een zoekmachine
rangschikt per pagina, en een gedeelde link toont de titel en de afbeelding van
de pagina waar hij naar wijst. Stonden alle berichten op één pagina, dan
concurreren ze om dezelfde plaats en tonen alle links hetzelfde voorbeeld.

    python tools/berichten.py            # schrijft alles bij
    python tools/berichten.py --check    # controleert alleen, exitcode 1 als
                                         # er iets niet meer klopt met de data

Wat er op de pagina's staat, hangt ook af van de datum van vandaag: een
evenement dat voorbij is, heet "afgelopen" en heeft geen aanmeldknop meer, en
na de aanmeldtermijn staat er "Aanmelden afgesloten". Daarom draait
.github/workflows/dagelijks.yml dit script elke nacht; verandert er iets, dan
commit het de pagina's en bouwt Cloudflare de site opnieuw. Voor een test op
een andere dag: POLARES_VANDAAG=2026-11-01 python tools/berichten.py.

Draait op de standaardbibliotheek. De voorbeeldafbeeldingen voor het delen
worden apart gemaakt door tools/og-afbeeldingen.py, dat Pillow nodig heeft.
"""

from __future__ import annotations

import html
from datetime import date
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "berichten.json"
PAGINA = ROOT / "blijf-op-koers.html"
SJABLOON = Path(__file__).resolve().parent / "sjabloon-bericht.html"
MAP = ROOT / "blijf-op-koers"
SITEMAP = ROOT / "sitemap.xml"

SITE = "https://polares.be"
VANDAAG = date.fromisoformat(os.environ["POLARES_VANDAAG"]) if os.environ.get("POLARES_VANDAAG") else date.today()
OG_TERUGVAL = "/assets/og-image.png"

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


def e(tekst) -> str:
    return html.escape(str(tekst), quote=True)


# Wat een redacteur niet hoeft in te vullen, want het volgt uit iets anders.
CATEGORIE = {"evenement": "Evenement", "nieuws": "Nieuws & Updates", "inzicht": "Inzichten & Advies"}
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]
DAGEN = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
VERPLICHT = ("id", "type", "titel", "datum", "inleiding", "inhoud")


def normaliseer(b: dict) -> dict:
    """Maakt een bericht uit data/berichten.json klaar voor de pagina's.

    Het CMS bewaart een leeg veld als "" en een uitgeschakelde schakelaar als
    false; beide betekenen hier: niet ingevuld. Categorie en uitgeschreven
    datum worden afgeleid als ze ontbreken, zodat een redacteur ze niet
    hoeft te kennen. Een fout geeft een melding met de titel erin: die ziet
    de redacteur terug in het logboek van de build."""
    b = {k: (v.strip() if isinstance(v, str) else v) for k, v in b.items()}
    b = {k: v for k, v in b.items() if v not in ("", None, False)}
    naam = b.get("titel") or b.get("id") or "(bericht zonder titel)"
    for veld in VERPLICHT:
        if not b.get(veld):
            raise SystemExit(f"bericht '{naam}': het veld '{veld}' is leeg")
    if b["type"] not in CATEGORIE:
        raise SystemExit(f"bericht '{naam}': type moet evenement, nieuws of inzicht zijn, niet '{b['type']}'")
    try:
        d = date.fromisoformat(str(b["datum"])[:10])
    except ValueError:
        raise SystemExit(f"bericht '{naam}': de datum '{b['datum']}' is geen geldige datum (jjjj-mm-dd)")
    b["datum"] = d.isoformat()
    b.setdefault("categorie", CATEGORIE[b["type"]])
    # evenementen met de dag erbij, zoals op een uitnodiging
    b.setdefault("datumWeergave", (DAGEN[d.weekday()] + " " if b["type"] == "evenement" else "")
                 + f"{d.day} {MAANDEN[d.month - 1]} {d.year}")

    # Wat onder de kaart staat, volgt uit de gegevens en de datum van vandaag,
    # zodat het nooit achterloopt: de leestijd uit de tekst, bij een evenement
    # de aanmeldtermijn of dat het voorbij is.
    b["_voorbij"] = False
    b["_open"] = False
    if b["type"] == "evenement":
        tot = None
        if b.get("aanmeldenTot"):
            try:
                tot = date.fromisoformat(str(b["aanmeldenTot"])[:10])
            except ValueError:
                raise SystemExit(f"bericht '{naam}': 'aanmelden tot' ({b['aanmeldenTot']}) is geen geldige datum")
            if tot > d:
                raise SystemExit(f"bericht '{naam}': de aanmeldtermijn ligt na het evenement zelf")
        b["_voorbij"] = d < VANDAAG
        b["_open"] = not b["_voorbij"] and (tot is None or tot >= VANDAAG)
        b["_tot"] = f"{tot.day} {MAANDEN[tot.month - 1]}" if tot else ""
        if b["_voorbij"]:
            b["_extra"] = "Afgelopen"
        elif not b["_open"]:
            b["_extra"] = "Aanmelden afgesloten"
        else:
            b["_extra"] = f"Aanmelden voor {b['_tot']}" if tot else ""
    else:
        woorden = len(re.sub(r"<[^>]+>", " ", b["inhoud"]).split())
        b["_extra"] = f"{max(1, round(woorden / 200))} min leestijd"
    return b


def badge(b: dict) -> str:
    if b["type"] == "evenement" and b["_voorbij"]:
        return "Afgelopen evenement"
    return SOORTEN.get(b["type"], b["type"])


def lees_berichten() -> list[dict]:
    berichten = [normaliseer(b) for b in json.loads(DATA.read_text(encoding="utf-8"))]
    # eerst de komende evenementen, het eerstvolgende bovenaan; daarna de rest
    # van nieuw naar oud
    komend = sorted((b for b in berichten if b["type"] == "evenement" and not b["_voorbij"]), key=lambda b: b["datum"])
    rest = sorted((b for b in berichten if b not in komend), key=lambda b: b["datum"], reverse=True)
    berichten = komend + rest
    ids = [b["id"] for b in berichten]
    dubbel = {i for i in ids if ids.count(i) > 1}
    if dubbel:
        raise SystemExit(f"twee berichten delen hetzelfde id: {', '.join(sorted(dubbel))}")
    for b in berichten:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", b["id"]):
            raise SystemExit(f"id '{b['id']}' mag alleen kleine letters, cijfers en koppeltekens bevatten")
    return berichten


def pad(b: dict) -> str:
    """Adres van het bericht, gezien vanaf de hoofdmap van de site."""
    return f"blijf-op-koers/{b['id']}.html"


def url(b: dict) -> str:
    return f"{SITE}/{pad(b)}"


def og_afbeelding(b: dict) -> str:
    """Eigen voorbeeldafbeelding als die gemaakt is, anders die van de site.
    Zonder eigen afbeelding tonen alle gedeelde links hetzelfde beeld, wat net
    het punt van aparte pagina's ondergraaft; de terugval is dus een vangnet,
    geen eindstation."""
    eigen = ROOT / "assets" / "og" / f"{b['id']}.png"
    return SITE + (f"/assets/og/{b['id']}.png" if eigen.exists() else OG_TERUGVAL)


def beschrijving(b: dict, grens: int = 155) -> str:
    tekst = b["inleiding"].strip()
    if len(tekst) <= grens:
        return tekst
    kort = tekst[:grens].rsplit(" ", 1)[0].rstrip(" ,;:")
    return kort + "…"


def gegevens_rijen(b: dict) -> list[tuple[str, str]]:
    rijen = []
    if b.get("datumWeergave"):
        wanneer = b["datumWeergave"] + (" · " + b["tijd"] if b.get("tijd") else "")
        rijen.append(("Wanneer", wanneer))
    if b.get("locatie"):
        rijen.append(("Waar", b["locatie"]))
    if b.get("deelname"):
        rijen.append(("Deelname", b["deelname"]))
    if b["type"] == "evenement" and b["_open"] and b["_tot"]:
        rijen.append(("Aanmelden", "Tot " + b["_tot"]))
    return rijen


def actie(b: dict) -> tuple[str, str]:
    # aanmelden kan alleen zolang het evenement komt en de termijn loopt
    evenement = b["type"] == "evenement" and b["_open"]
    tekst = "Aanmelden voor dit evenement" if evenement else "Contact opnemen"
    onderwerp = ("Aanmelding: " if evenement else "Vraag over: ") + b["titel"]
    from urllib.parse import quote
    return tekst, f"mailto:info@polares.be?subject={quote(onderwerp)}"


# ── Het overzicht ────────────────────────────────────────────────────────────

def tellers(berichten: list[dict]) -> str:
    # gewone schakelknoppen: aria-pressed zegt welke filter aan staat
    regels = []
    for sleutel, naam in FILTERS:
        n = len(berichten) if sleutel == "alles" else sum(1 for b in berichten if b["type"] == sleutel)
        actief = ' aria-pressed="true" class="filter is-actief"' if sleutel == "alles" else ' aria-pressed="false" class="filter"'
        regels.append(
            f'          <button type="button" data-soort="{sleutel}"{actief}>'
            f'{naam} <span class="filter__aantal">{n}</span></button>'
        )
    return "\n".join(regels)


def kaart(b: dict) -> str:
    soort = b["type"]
    extra = b["_extra"]
    return f"""      <article class="bericht" data-soort="{e(soort)}">
        <p class="bericht__kop">
          <span class="badge badge--{e(soort)}">{e(badge(b))}</span>
          <time class="bericht__datum" datetime="{e(b["datum"])}">{e(b["datumWeergave"])}</time>
        </p>
        <h3 class="bericht__titel"><a class="bericht__opener" href="{e(pad(b))}">{e(b["titel"])}</a></h3>
        <p class="bericht__inleiding">{e(b["inleiding"])}</p>
        <p class="bericht__voet">
          <span class="bericht__extra">{e(extra)}</span>
          <span class="bericht__lees" aria-hidden="true">Lees meer {PIJL}</span>
        </p>
      </article>"""


def uitgelicht(b: dict) -> str:
    meta = "\n".join(
        f'            <div class="uitgelicht__rij"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>'
        for k, v in gegevens_rijen(b)
    )
    evenement = b["type"] == "evenement"
    if evenement:
        knop = "Programma en aanmelden" if b["_open"] else "Bekijk het programma"
    else:
        knop = "Lees het volledige bericht"
    kop = "Aankomend evenement" if evenement else SOORTEN.get(b["type"], b["type"])
    deadline = f'\n          <p class="uitgelicht__deadline">{e(b["_extra"])}</p>' if evenement and b["_extra"] else ""
    return f"""      <article class="uitgelicht" data-soort="{e(b["type"])}">
        <div class="uitgelicht__tekst">
          <p class="bericht__kop"><span class="badge badge--{e(b["type"])}">{e(kop)}</span></p>
          <h2 class="uitgelicht__titel"><a class="bericht__opener" href="{e(pad(b))}">{e(b["titel"])}</a></h2>
          <p class="uitgelicht__inleiding">{e(b["inleiding"])}</p>
          <p><a class="btn" href="{e(pad(b))}">{e(knop)}</a></p>
        </div>
        <div class="uitgelicht__meta">
          <span class="uitgelicht__ster" aria-hidden="true">{STER}</span>
          <dl>
{meta}
          </dl>{deadline}
        </div>
      </article>"""


def lijstdata(berichten: list[dict]) -> str:
    """Een ItemList voor het overzicht: zo ziet een zoekmachine in één oogopslag
    welke adressen eronder hangen."""
    data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Blijf op koers",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "url": url(b), "name": b["titel"]}
            for i, b in enumerate(berichten, 1)
        ],
    }
    ruw = json_ld(data)
    return ('  <script type="application/ld+json">\n'
            + "\n".join("  " + r for r in ruw.split("\n"))
            + "\n  </script>")


def json_ld(data) -> str:
    """JSON voor in een <script>-blok. Geen enkel CMS-veld mag het blok kunnen
    sluiten met </script>: <, > en & worden als \\u-code geschreven. Dat blijft
    geldige JSON met precies dezelfde betekenis."""
    ruw = json.dumps(data, ensure_ascii=False, indent=2)
    return ruw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


# ── De pagina per bericht ────────────────────────────────────────────────────

def tijdvak(b: dict) -> tuple[str, str]:
    """'08:30 tot 10:30' wordt begin- en eindtijd in ISO 8601, '08:30' alleen
    een begintijd. Zonder tijdzone: schema.org leest zo'n tijd als lokale tijd
    op de plaats van het evenement, en dat is precies wat hier bedoeld is."""
    datum = b["datum"]
    m = re.match(r"\s*(\d{1,2}[:.]\d{2})(?:\s*(?:tot|-|–)\s*(\d{1,2}[:.]\d{2}))?", b.get("tijd", "") or "")
    if not m:
        return datum, ""
    begin = m.group(1).replace(".", ":").zfill(5)
    eind = m.group(2).replace(".", ":").zfill(5) if m.group(2) else ""
    return f"{datum}T{begin}", (f"{datum}T{eind}" if eind else "")


def structured_data(b: dict) -> str:
    adres = {
        "@type": "PostalAddress",
        "streetAddress": "Dirk Martensstraat 41",
        "postalCode": "9300",
        "addressLocality": "Aalst",
        "addressCountry": "BE",
    }
    # dezelfde organisatie als in de gegevens op de homepage
    polares = {"@type": "Organization", "@id": SITE + "/#organisatie", "name": "Polares", "url": SITE + "/",
               "logo": SITE + "/assets/icon-512.png"}
    kruimels = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Polares", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blijf op koers",
             "item": SITE + "/blijf-op-koers.html"},
            {"@type": "ListItem", "position": 3, "name": b["titel"], "item": url(b)},
        ],
    }

    if b["type"] == "evenement":
        begin, eind = tijdvak(b)
        hoofd = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": b["titel"],
            "description": beschrijving(b, 300),
            "startDate": begin,
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": locatie(b, adres),
            "organizer": polares,
            "image": og_afbeelding(b),
            "url": url(b),
            "inLanguage": "nl-BE",
        }
        if eind:
            hoofd["endDate"] = eind
    else:
        hoofd = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": b["titel"],
            "description": beschrijving(b, 300),
            "datePublished": b["datum"],
            "dateModified": b["datum"],
            "author": polares,
            "publisher": polares,
            "image": og_afbeelding(b),
            "mainEntityOfPage": url(b),
            "inLanguage": "nl-BE",
        }

    ruw = json_ld([hoofd, kruimels])
    return "\n".join("  " + r for r in ruw.split("\n")).lstrip()


def locatie(b: dict, kantoor: dict) -> dict:
    """Het adres van het kantoor alleen als het evenement daar is; anders de
    plaats zoals ze in het CMS staat."""
    plaats = b.get("locatie", "")
    if not plaats or plaats.startswith("Kantoor Polares") or "Dirk Martensstraat" in plaats:
        return {"@type": "Place", "name": plaats.split(",")[0] if plaats else "Kantoor Polares", "address": kantoor}
    return {"@type": "Place", "name": plaats.split(",")[0], "address": plaats}


def gegevensblok(b: dict) -> str:
    rijen = gegevens_rijen(b)
    if not rijen or b["type"] != "evenement":
        return ""
    binnen = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in rijen)
    return f'      <dl class="artikel__gegevens">{binnen}</dl>\n'


def verder(b: dict, alle: list[dict]) -> str:
    rest = [a for a in alle if a["id"] != b["id"]][:3]
    if not rest:
        return ""
    items = "\n".join(
        f'        <li class="verder__item">\n'
        f'          <p class="verder__datum">{e(badge(a))} · {e(a["datumWeergave"])}</p>\n'
        f'          <h3 class="verder__kop"><a href="{e(a["id"])}.html">{e(a["titel"])}</a></h3>\n'
        f'        </li>'
        for a in rest
    )
    return f"""    <section class="verder" aria-labelledby="verder-h2">
      <h2 class="verder__titel" id="verder-h2">Meer op Blijf op koers</h2>
      <ul class="verder__lijst">
{items}
      </ul>
    </section>
"""


def bouw_bericht(b: dict, alle: list[dict]) -> str:
    knop, href = actie(b)
    velden = {
        "SOORT": e(b["type"]),
        "BADGE": e(badge(b)),
        "TITEL": e(b["titel"]),
        "TITEL_KORT": e(b.get("titelKort") or b["titel"]),
        "BESCHRIJVING": e(beschrijving(b)),
        "URL": e(url(b)),
        "OG_AFBEELDING": e(og_afbeelding(b)),
        "DATUM": e(b["datum"]),
        "DATUM_WEERGAVE": e(b["datumWeergave"]),
        "INLEIDING": e(b["inleiding"]),
        "INHOUD": b["inhoud"],
        "GEGEVENS": gegevensblok(b),
        "ACTIE_TEKST": e(knop),
        "ACTIE_HREF": e(href),
        "VERDER": verder(b, alle),
        "STRUCTURED_DATA": structured_data(b),
    }
    tekst = SJABLOON.read_text(encoding="utf-8")
    # een evenement heeft geen publicatiedatum: de datum is die van het
    # evenement zelf, en die ligt vaak in de toekomst
    publicatie = ("" if b["type"] == "evenement"
                  else f'  <meta property="article:published_time" content="{e(b["datum"])}">\n')
    tekst = tekst.replace("{{PUBLICATIE}}\n", publicatie)
    for sleutel, waarde in velden.items():
        tekst = tekst.replace("{{" + sleutel + "}}", waarde)
    rest = re.findall(r"\{\{[A-Z_]+\}\}", tekst)
    if rest:
        raise SystemExit(f"het sjabloon heeft een plaatshouder die niet is ingevuld: {rest[0]}")
    return tekst


# ── De sitemap ───────────────────────────────────────────────────────────────

def sitemap_regels(berichten: list[dict]) -> str:
    # lastmod alleen bij een artikel: bij een evenement is de datum die van
    # het evenement, niet van de pagina
    return "\n".join(
        f"  <url>\n"
        f"    <loc>{url(b)}</loc>\n"
        + (f"    <lastmod>{b['datum']}</lastmod>\n" if b["type"] != "evenement" else "")
        + f"    <changefreq>yearly</changefreq>\n"
        f"    <priority>0.5</priority>\n"
        f"  </url>"
        for b in berichten
    )


# ── Schrijven en vergelijken ─────────────────────────────────────────────────

def vervang(tekst: str, merk: str, inhoud: str, bestand: str) -> str:
    patroon = re.compile(
        r"([ \t]*<!-- BEGIN_" + merk + r"[^>]*-->)(.*?)([ \t]*<!-- EIND_" + merk + r" -->)",
        re.S,
    )
    if not patroon.search(tekst):
        raise SystemExit(f"merkteken {merk} niet gevonden in {bestand}")

    def bouw_blok(m: re.Match) -> str:
        tussen = "\n" + inhoud + "\n" if inhoud else "\n"
        return m.group(1) + tussen + m.group(3)

    return patroon.sub(bouw_blok, tekst)


def alles(berichten: list[dict]) -> dict[Path, str]:
    """Elk bestand dat dit script beheert, met de inhoud die het hoort te
    hebben. Zo zijn schrijven en controleren precies dezelfde berekening."""
    # een voorbij evenement staat nooit meer groot bovenaan
    kop = next((b for b in berichten if b.get("uitgelicht") and not b["_voorbij"]), None)
    rest = [b for b in berichten if b is not kop]

    pagina = PAGINA.read_text(encoding="utf-8")
    pagina = vervang(pagina, "FILTERS", tellers(berichten), PAGINA.name)
    pagina = vervang(pagina, "LIJSTDATA", lijstdata(berichten), PAGINA.name)
    pagina = vervang(pagina, "UITGELICHT", uitgelicht(kop) if kop else "", PAGINA.name)
    pagina = vervang(pagina, "BERICHTEN", "\n\n".join(kaart(b) for b in rest), PAGINA.name)

    sitemap = vervang(SITEMAP.read_text(encoding="utf-8"), "BERICHTEN",
                      sitemap_regels(berichten), SITEMAP.name)

    uit = {PAGINA: pagina, SITEMAP: sitemap}
    for b in berichten:
        uit[MAP / f"{b['id']}.html"] = bouw_bericht(b, berichten)
    return uit


def verweesd(berichten: list[dict]) -> list[Path]:
    """Pagina's van berichten die niet meer in de JSON staan."""
    if not MAP.is_dir():
        return []
    hoort = {f"{b['id']}.html" for b in berichten}
    return sorted(p for p in MAP.glob("*.html") if p.name not in hoort)


def main() -> int:
    berichten = lees_berichten()
    gewenst = alles(berichten)
    wees = verweesd(berichten)
    controle = "--check" in sys.argv

    afwijkend = [p for p, inhoud in gewenst.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != inhoud]

    if controle:
        if afwijkend or wees:
            print(f"FOUT: de pagina's lopen niet meer gelijk met {DATA.name}.")
            for p in afwijkend:
                print(f"      anders of ontbreekt: {p.relative_to(ROOT)}")
            for p in wees:
                print(f"      hoort er niet meer te staan: {p.relative_to(ROOT)}")
            print("      Draai 'python tools/berichten.py' en commit het resultaat.")
            return 1
        print(f"{len(gewenst)} bestanden lopen gelijk met {DATA.name}.")
        return 0

    if not afwijkend and not wees:
        print("Niets te doen: alles liep al gelijk met de gegevens.")
        return 0

    MAP.mkdir(exist_ok=True)
    for p in afwijkend:
        p.write_text(gewenst[p], encoding="utf-8")
        print(f"bijgewerkt: {p.relative_to(ROOT)}")
    for p in wees:
        p.unlink()
        print(f"verwijderd: {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
