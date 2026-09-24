#!/usr/bin/env python3
"""
Tekent de kaart van de omgeving van het kantoor voor contact.html.

Een ingebedde Google Maps of OpenStreetMap zou bij elk bezoek een derde partij
aanspreken, en de eerste zet cookies. Deze kaart is een gewoon bestand op de
eigen server: assets/kaart-kantoor.svg. De straten, het spoor en de Dender
komen uit OpenStreetMap; de stijl is die van de site: navy, witte haarlijnen,
de poolster op het kantoor en de stippellijn van het station naar de deur.

De wandelroute wordt hier zelf uitgerekend, als kortste pad over de wegen en
voetpaden. De lengte ervan staat onderaan in de uitvoer; die hoort bij de tekst
op contact.html ("op zes minuten wandelen van het station").

Het resultaat bevat kaartgegevens van OpenStreetMap (ODbL). De naamsvermelding
"© OpenStreetMap-bijdragers" moet daarom onder de kaart blijven staan.

    python tools/kaart.py                 # haalt de gegevens op en tekent
    python tools/kaart.py --osm osm.json  # tekent uit een eerder opgehaald bestand

Vraagt: pip install fonttools brotli (voor de labels in de huisletter).
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
UIT = ROOT / "assets" / "kaart-kantoor.svg"
LETTERS = ROOT / "assets" / "fonts"

# Dirk Martensstraat 41, 9300 Aalst (OpenStreetMap, gebouw 931661199)
KANTOOR = (50.9420177, 4.0329466)
# het kaartvenster: breed genoeg voor het station aan de oostkant
MIDDEN = (50.94250, 4.03640)
BREED_M = 1150            # meter van links naar rechts
B, H = 1600, 900          # eenheden van het SVG-venster (16:9)

WANDELTEMPO = 80          # meter per minuut

STER = ("M42 0 L58 0 L58 17.8 A24.2 24.2 0 0 0 82.2 42 L100 42 L100 58 L82.2 58 "
        "A24.2 24.2 0 0 0 58 82.2 L58 100 L42 100 L42 82.2 A24.2 24.2 0 0 0 17.8 58 "
        "L0 58 L0 42 L17.8 42 A24.2 24.2 0 0 0 42 17.8 Z")


# ── projectie ───────────────────────────────────────────────────────────────
SCHAAL = B / BREED_M
COS0 = math.cos(math.radians(MIDDEN[0]))


def xy(lat: float, lon: float) -> tuple[float, float]:
    x = (lon - MIDDEN[1]) * COS0 * 111320 * SCHAAL + B / 2
    y = -(lat - MIDDEN[0]) * 110540 * SCHAAL + H / 2
    return x, y


def venster_graden(marge: float = 1.15) -> tuple[float, float, float, float]:
    halfb = BREED_M / 2 * marge / (COS0 * 111320)
    halfh = BREED_M * H / B / 2 * marge / 110540
    return (MIDDEN[0] - halfh, MIDDEN[1] - halfb, MIDDEN[0] + halfh, MIDDEN[1] + halfb)


# ── gegevens ────────────────────────────────────────────────────────────────
def haal_op() -> dict:
    z, w, n, o = venster_graden()
    bbox = f"{z:.5f},{w:.5f},{n:.5f},{o:.5f}"
    vraag = f"""[out:json][timeout:90];
(
  way["highway"]({bbox});
  way["railway"="rail"]({bbox});
  way["waterway"~"river|canal"]({bbox});
  way["natural"="water"]({bbox});
  relation["natural"="water"]({bbox});
  way["leisure"="park"]({bbox});
  way["landuse"~"grass|recreation_ground"]({bbox});
  way["building"]({bbox});
  node["railway"="station"]({bbox});
);
out geom;"""
    verzoek = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": vraag}).encode(),
        headers={"User-Agent": "polares.be kaartgenerator (eenmalig, statisch)"},
    )
    with urllib.request.urlopen(verzoek, timeout=120) as r:
        return json.load(r)


# ── tekenen ─────────────────────────────────────────────────────────────────
def vereenvoudig(punten, marge=.7):
    """Douglas-Peucker: laat punten weg die minder dan `marge` van de lijn
    afwijken. Op deze schaal is dat onzichtbaar en het scheelt de helft."""
    if len(punten) < 3:
        return punten
    (ax, ay), (bx, by) = punten[0], punten[-1]
    dx, dy = bx - ax, by - ay
    lang = math.hypot(dx, dy) or 1e-9
    verst, idx = 0.0, 0
    for i in range(1, len(punten) - 1):
        px, py = punten[i]
        d = abs(dy * px - dx * py + bx * ay - by * ax) / lang
        if d > verst:
            verst, idx = d, i
    if verst <= marge:
        return [punten[0], punten[-1]]
    return vereenvoudig(punten[: idx + 1], marge)[:-1] + vereenvoudig(punten[idx:], marge)


def getal(v: float) -> str:
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def pad(punten, sluit=False) -> str:
    """Relatieve coördinaten op een tiende: de kaart telt duizenden huizen, en
    elk teken per punt telt mee in het bestand."""
    punten = vereenvoudig(punten)
    (x0, y0) = punten[0]
    d = [f"M{getal(x0)} {getal(y0)}"]
    px, py = round(x0, 1), round(y0, 1)
    stap = []
    for x, y in punten[1:]:
        x, y = round(x, 1), round(y, 1)
        stap.append(f"{getal(x - px)} {getal(y - py)}")
        px, py = x, y
    if stap:
        d.append("l" + " ".join(stap))
    return "".join(d) + ("z" if sluit else "")


def paden(lijst) -> str:
    # één pad per laag: de opmaak is per laag toch dezelfde
    return '<path d="' + "".join(lijst) + '"/>' if lijst else ""


def in_beeld(punten, marge=60) -> bool:
    return any(-marge <= x <= B + marge and -marge <= y <= H + marge for x, y in punten)


def lijn_van(el) -> list[tuple[float, float]]:
    return [xy(p["lat"], p["lon"]) for p in el.get("geometry", []) if p]


# Straten per soort: dikte en helderheid. Grote assen lichter en breder, de
# voetpaden nauwelijks zichtbaar: de kaart moet rustig blijven.
STRATEN = [
    ({"primary", "trunk", "primary_link", "trunk_link"},            2.6, .62),
    ({"secondary", "secondary_link"},                                2.3, .56),
    ({"tertiary", "tertiary_link"},                                  2.0, .50),
    ({"residential", "unclassified", "living_street"},              1.4, .40),
    ({"pedestrian"},                                                 1.4, .34),
    ({"service"},                                                    .8, .20),
    ({"footway", "path", "cycleway", "steps", "track", "bridleway"}, .6, .14),
]


def soort(hw: str):
    for i, (namen, dik, licht) in enumerate(STRATEN):
        if hw in namen:
            return i, dik, licht
    return None


# ── wandelroute ─────────────────────────────────────────────────────────────
NIET_TE_VOET = {"motorway", "motorway_link", "trunk", "construction", "proposed", "no", "platform", "raceway"}


def meter(a, b) -> float:
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def route(elementen, van, naar):
    buren, plek = {}, {}
    for el in elementen:
        t = el.get("tags", {})
        if el["type"] != "way" or "highway" not in t or t["highway"] in NIET_TE_VOET:
            continue
        if t.get("foot") == "no" or t.get("access") in ("private", "no"):
            continue
        knopen, geo = el.get("nodes", []), el.get("geometry", [])
        if len(knopen) != len(geo):
            continue
        for k, g in zip(knopen, geo):
            plek[k] = (g["lat"], g["lon"])
        for a, b in zip(knopen, knopen[1:]):
            d = meter(plek[a], plek[b])
            buren.setdefault(a, []).append((b, d))
            buren.setdefault(b, []).append((a, d))

    def dichtst(p):
        return min(buren, key=lambda k: meter(plek[k], p))

    start, doel = dichtst(van), dichtst(naar)
    afstand, vorige, rij = {start: 0.0}, {}, [(0.0, start)]
    while rij:
        d, k = heapq.heappop(rij)
        if k == doel:
            break
        if d > afstand[k]:
            continue
        for b, w in buren[k]:
            nd = d + w
            if nd < afstand.get(b, math.inf):
                afstand[b], vorige[b] = nd, k
                heapq.heappush(rij, (nd, b))
    keten, k = [doel], doel
    while k != start:
        k = vorige[k]
        keten.append(k)
    keten.reverse()
    return [plek[k] for k in keten], afstand[doel]


# ── labels in de huisletter, als contour ────────────────────────────────────
# Een SVG die als <img> geladen wordt, kan de lettertypes van de pagina niet
# gebruiken. De letters worden daarom omgezet in paden.
_fonts = {}


def letter(naam: str) -> TTFont:
    if naam not in _fonts:
        tt = TTFont(LETTERS / naam)
        tt.flavor = None
        _fonts[naam] = tt
    return _fonts[naam]


def tekst(s: str, fontnaam: str, grootte: float, x: float, y: float,
          spatiering: float = 0, anker: str = "start") -> str:
    tt = letter(fontnaam)
    upm = tt["head"].unitsPerEm
    cmap, glyphs, hmtx = tt.getBestCmap(), tt.getGlyphSet(), tt["hmtx"]
    f = grootte / upm
    breedte = sum(hmtx[cmap[ord(c)]][0] * f + spatiering for c in s) - spatiering
    cx = x - (breedte if anker == "end" else breedte / 2 if anker == "middle" else 0)
    delen = []
    for c in s:
        naam = cmap[ord(c)]
        pen = SVGPathPen(glyphs)
        glyphs[naam].draw(TransformPen(pen, (f, 0, 0, -f, cx, y)))
        if pen.getCommands():
            delen.append(pen.getCommands())
        cx += hmtx[naam][0] * f + spatiering
    return " ".join(delen)


# ── samenstellen ────────────────────────────────────────────────────────────
def teken(osm: dict) -> tuple[str, float]:
    global KX, KY
    KX, KY = xy(*KANTOOR)
    el = osm["elements"]
    gebouwen, groen, water, rivieren, spoor, straten = [], [], [], [], [], [[] for _ in STRATEN]
    station = None

    for e in el:
        t = e.get("tags", {})
        if e["type"] == "node" and t.get("railway") == "station":
            station = (e["lat"], e["lon"])
            continue
        if e["type"] == "relation":
            for lid in e.get("members", []):
                if lid.get("role") == "outer" and lid.get("geometry"):
                    p = [xy(g["lat"], g["lon"]) for g in lid["geometry"] if g]
                    if in_beeld(p):
                        water.append(pad(p, True))
            continue
        p = lijn_van(e)
        if len(p) < 2 or not in_beeld(p):
            continue
        if "building" in t:
            # het masker dooft de huizen uit naar de rand; wat daarbuiten ligt,
            # is onzichtbaar en hoeft niet in het bestand
            mx = sum(q[0] for q in p) / len(p) - KX
            my = sum(q[1] for q in p) / len(p) - KY
            if math.hypot(mx, my) < B * .5:
                gebouwen.append(pad(p, True))
        elif t.get("natural") == "water":
            water.append(pad(p, True))
        elif t.get("waterway") in ("river", "canal"):
            rivieren.append(pad(p))
        elif t.get("leisure") == "park" or t.get("landuse") in ("grass", "recreation_ground"):
            groen.append(pad(p, True))
        elif t.get("railway") == "rail":
            if t.get("service") in ("yard", "siding", "spur"):
                continue
            spoor.append(pad(p))
        elif "highway" in t:
            s = soort(t["highway"])
            if s and t.get("area") != "yes":
                straten[s[0]].append(pad(p))

    if not station:
        raise SystemExit("geen station gevonden in de gegevens")
    weg, lengte = route(el, station, KANTOOR)
    weg_xy = [xy(*p) for p in weg]
    kx, ky = xy(*KANTOOR)
    sx, sy = xy(*station)
    # De route eindigt op de deur. Het dichtste kruispunt kan voorbij het
    # kantoor liggen; dan zou de lijn erlangs schieten en terugkeren. Daarom
    # knippen we ze af op het punt van de route dat het dichtst bij de deur ligt.
    beste = (math.inf, 0, weg_xy[0])
    for i, ((ax, ay), (bx, by)) in enumerate(zip(weg_xy, weg_xy[1:])):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((kx - ax) * dx + (ky - ay) * dy) / ((dx * dx + dy * dy) or 1e-9)))
        px, py = ax + t * dx, ay + t * dy
        d = math.hypot(kx - px, ky - py)
        if d < beste[0]:
            beste = (d, i, (px, py))
    _, i, voet = beste
    weg_xy = weg_xy[: i + 1] + [voet, (kx, ky)]

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}" width="{B}" height="{H}">')
    o.append("<!-- Kaartgegevens © OpenStreetMap-bijdragers (ODbL). Gemaakt met tools/kaart.py. -->")
    o.append("<defs>")
    o.append(f'<radialGradient id="g" cx="{kx / B:.3f}" cy="{ky / H:.3f}" r=".85">'
             '<stop offset="0" stop-color="#0E2A42"/><stop offset=".5" stop-color="#0A2236"/>'
             '<stop offset="1" stop-color="#071826"/></radialGradient>')
    # de huizen lossen op naar de randen: het oog blijft bij het kantoor
    o.append(f'<radialGradient id="v" cx="{kx:.0f}" cy="{ky:.0f}" r="{B * .55:.0f}" gradientUnits="userSpaceOnUse">'
             '<stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#fff" stop-opacity=".7"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    o.append(f'<mask id="m"><rect width="{B}" height="{H}" fill="url(#v)"/></mask>')
    o.append("</defs>")
    o.append(f'<rect width="{B}" height="{H}" fill="url(#g)"/>')

    o.append(f'<g fill="#fff" fill-opacity=".035">{paden(groen)}</g>')
    o.append(f'<g fill="#7E94A6" fill-opacity=".2">{paden(water)}</g>')
    o.append(f'<g fill="none" stroke="#7E94A6" stroke-opacity=".28" stroke-width="14" stroke-linecap="round" stroke-linejoin="round">'
             f'{paden(rivieren)}</g>')
    o.append(f'<g mask="url(#m)" fill="#fff" fill-opacity=".07">{paden(gebouwen)}</g>')

    # kleinste eerst, zodat de grote assen er bovenop liggen
    for i in reversed(range(len(STRATEN))):
        _, dik, licht = STRATEN[i]
        if straten[i]:
            o.append(f'<g fill="none" stroke="#fff" stroke-opacity="{licht}" stroke-width="{dik}" '
                     f'stroke-linecap="round" stroke-linejoin="round">'
                     f'{paden(straten[i])}</g>')

    o.append(f'<g fill="none" stroke="#fff" stroke-opacity=".32" stroke-width="1.2" stroke-dasharray="10 5">'
             f'{paden(spoor)}</g>')

    # de wandelroute: de stippellijn van de site
    o.append(f'<path d="{pad(weg_xy)}" fill="none" stroke="#fff" stroke-width="3.2" '
             'stroke-dasharray="0 9" stroke-linecap="round" stroke-linejoin="round"/>')

    # het station: een open ring
    o.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="#0A2236" stroke="#fff" stroke-opacity=".85" stroke-width="1.6"/>')
    o.append(f'<path d="{tekst("STATION AALST", "source-sans-pro-700.woff2", 15, sx, sy - 22, 2.4, "middle")}" '
             'fill="#fff" fill-opacity=".72"/>')

    # het kantoor: de poolster met een zachte gloed
    o.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="46" fill="#fff" fill-opacity=".06"/>')
    o.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="24" fill="#fff" fill-opacity=".08"/>')
    ster = 30
    o.append(f'<path d="{STER}" fill="#fff" transform="translate({kx - ster / 2:.1f},{ky - ster / 2:.1f}) scale({ster / 100})"/>')
    o.append(f'<path d="{tekst("Polares", "cantata-one-400.woff2", 30, kx, ky - 44, 0, "middle")}" fill="#fff"/>')
    o.append(f'<path d="{tekst("DIRK MARTENSSTRAAT 41", "source-sans-pro-400.woff2", 13, kx, ky + 50, 2.2, "middle")}" '
             'fill="#fff" fill-opacity=".7"/>')
    o.append("</svg>")
    getekend = sum(math.hypot(bx - ax, by - ay) for (ax, ay), (bx, by) in zip(weg_xy, weg_xy[1:])) / SCHAAL
    return "\n".join(o) + "\n", getekend


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--osm", type=Path, help="een eerder opgehaald Overpass-bestand")
    ap.add_argument("--bewaar", type=Path, help="bewaar de opgehaalde gegevens hier")
    a = ap.parse_args()

    osm = json.loads(a.osm.read_text()) if a.osm else haal_op()
    if a.bewaar:
        a.bewaar.write_text(json.dumps(osm))
    svg, lengte = teken(osm)
    UIT.write_text(svg, encoding="utf-8")
    minuten = lengte / WANDELTEMPO
    print(f"{UIT.relative_to(ROOT)}: {len(svg) // 1024} kB")
    print(f"wandelroute station → kantoor: {lengte:.0f} m, ongeveer {minuten:.1f} minuten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
