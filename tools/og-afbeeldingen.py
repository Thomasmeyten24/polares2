#!/usr/bin/env python3
"""
Maakt de voorbeeldafbeelding die LinkedIn, WhatsApp en X tonen bij een gedeelde
link naar een bericht: assets/og/<id>.png, 1200 bij 630.

Zonder eigen afbeelding krijgt elk bericht hetzelfde beeld van de site, en dan
zien zes gedeelde links er identiek uit. Dat ondergraaft net waarvoor de aparte
pagina's bestaan, dus krijgt elk bericht zijn eigen kaart met de titel erop.

    python tools/og-afbeeldingen.py            # maakt wat ontbreekt of verouderd is
    python tools/og-afbeeldingen.py --alles    # maakt alles opnieuw

Dit script staat los van tools/berichten.py omdat het Pillow en fontTools nodig
heeft; die horen niet tot de standaardbibliotheek en dus ook niet tot wat de
controle in GitHub Actions moet kunnen draaien. Draai het met de hand wanneer er
een bericht bijkomt, en draai daarna tools/berichten.py: dat pikt de nieuwe
afbeelding vanzelf op.

    pip install pillow fonttools brotli
"""

import io
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "berichten.json"
UIT = ROOT / "assets" / "og"
LETTERS = ROOT / "assets" / "fonts"
LOGO = ROOT / "assets" / "POLARES_LOGO_WIT_woordmerk.png"

B, H = 1200, 630
RAND = 72
NAVY = (7, 24, 38)
DIEP = (14, 42, 66)
WIT = (255, 255, 255)

SOORTEN = {"evenement": "Evenement", "nieuws": "Nieuws", "inzicht": "Inzicht"}


def lettertype(naam: str, grootte: int) -> ImageFont.FreeTypeFont:
    """Pillow leest geen woff2. De site heeft alleen woff2, dus pakken we het
    bestand uit naar een gewone TrueType in het geheugen."""
    tt = TTFont(LETTERS / naam)
    buffer = io.BytesIO()
    tt.flavor = None
    tt.save(buffer)
    buffer.seek(0)
    return ImageFont.truetype(buffer, grootte)


def achtergrond() -> Image.Image:
    """Dezelfde hemel als de hero: donker naar de randen toe, iets lichter
    rond het midden bovenaan."""
    doek = Image.new("RGB", (B, H), NAVY)
    tek = ImageDraw.Draw(doek)
    mx, my = B * 0.5, H * 0.18
    straal = (B ** 2 + H ** 2) ** 0.5 * 0.62
    for i in range(int(straal), 0, -6):
        f = 1 - i / straal
        kleur = tuple(round(NAVY[k] + (DIEP[k] - NAVY[k]) * f ** 2) for k in range(3))
        tek.ellipse([mx - i, my - i, mx + i, my + i], fill=kleur)

    # een handvol sterren, vast patroon zodat dezelfde titel altijd hetzelfde
    # beeld oplevert en een herbouw geen ruis in git geeft
    import random
    r = random.Random(20260922)
    for _ in range(90):
        x, y = r.uniform(0, B), r.uniform(0, H)
        straal_s = r.uniform(0.6, 1.9)
        alpha = int(r.uniform(28, 115))
        laag = Image.new("RGBA", doek.size, (0, 0, 0, 0))
        ImageDraw.Draw(laag).ellipse([x - straal_s, y - straal_s, x + straal_s, y + straal_s],
                                     fill=(255, 255, 255, alpha))
        doek = Image.alpha_composite(doek.convert("RGBA"), laag).convert("RGB")
    return doek


def plak(doek: Image.Image, pad: Path, breedte: int, xy: tuple[int, int], alpha: float = 1.0) -> None:
    beeld = Image.open(pad).convert("RGBA")
    hoogte = round(beeld.height * breedte / beeld.width)
    beeld = beeld.resize((breedte, hoogte), Image.LANCZOS)
    if alpha < 1:
        k = beeld.split()[3].point(lambda v: round(v * alpha))
        beeld.putalpha(k)
    doek.paste(beeld, xy, beeld)


def gespatieerd(tek: ImageDraw.ImageDraw, xy, tekst, font, kleur, spatie: float) -> None:
    x, y = xy
    for teken in tekst:
        tek.text((x, y), teken, font=font, fill=kleur)
        x += font.getlength(teken) + spatie


def breek(tekst: str, font, breedte: int, maxregels: int) -> list[str]:
    woorden, regels, huidig = tekst.split(), [], ""
    for w in woorden:
        proef = (huidig + " " + w).strip()
        if font.getlength(proef) <= breedte or not huidig:
            huidig = proef
        else:
            regels.append(huidig)
            huidig = w
    regels.append(huidig)
    if len(regels) > maxregels:
        regels = regels[:maxregels]
        while regels[-1] and font.getlength(regels[-1] + "…") > breedte:
            regels[-1] = regels[-1].rsplit(" ", 1)[0] if " " in regels[-1] else regels[-1][:-1]
        regels[-1] += "…"
    return regels


def kaart(b: dict) -> Image.Image:
    doek = achtergrond()
    plak(doek, LOGO, 232, (RAND, RAND))
    tek = ImageDraw.Draw(doek)

    klein = lettertype("source-sans-pro-700.woff2", 19)
    gespatieerd(tek, (RAND + 2, RAND + 92), SOORTEN.get(b["type"], b["type"]).upper(),
                klein, (161, 178, 192), 3.4)

    # de titel krimpt tot hij in vier regels past
    for korps in (58, 52, 46, 41):
        serif = lettertype("cantata-one-400.woff2", korps)
        regels = breek(b["titel"], serif, B - 2 * RAND - 40, 4)
        hoogte = len(regels) * korps * 1.28
        if len(regels) < 4 or korps == 41:
            break
    y = H - RAND - 58 - hoogte
    for regel in regels:
        tek.text((RAND, y), regel, font=serif, fill=WIT)
        y += korps * 1.28

    datum = lettertype("source-sans-pro-400.woff2", 21)
    tek.text((RAND, H - RAND - 26), b.get("datumWeergave", ""), font=datum, fill=(146, 166, 184))
    tek.line([(RAND, H - RAND - 46), (RAND + 46, H - RAND - 46)], fill=(70, 96, 122), width=1)
    return doek


def main() -> int:
    berichten = json.loads(DATA.read_text(encoding="utf-8"))
    UIT.mkdir(parents=True, exist_ok=True)
    opnieuw = "--alles" in sys.argv
    gemaakt = 0
    for b in berichten:
        doel = UIT / f"{b['id']}.png"
        if doel.exists() and not opnieuw:
            continue
        kaart(b).save(doel, "PNG", optimize=True)
        print(f"gemaakt: {doel.relative_to(ROOT)}  ({doel.stat().st_size // 1024} kB)")
        gemaakt += 1

    hoort = {f"{b['id']}.png" for b in berichten}
    for p in sorted(UIT.glob("*.png")):
        if p.name not in hoort:
            p.unlink()
            print(f"verwijderd: {p.relative_to(ROOT)}")

    if not gemaakt:
        print("Niets te doen: elke afbeelding bestond al. Gebruik --alles om ze te vernieuwen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
