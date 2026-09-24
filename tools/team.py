#!/usr/bin/env python3
"""
Schrijft het raster van medewerkers op ons-team.html uit data/team.json.

data/team.json is de enige plaats waar een medewerker bestaat: naam, functie
(één of twee regels), e-mailadres, LinkedIn en portret. De volgorde in het
bestand is de volgorde op de pagina. Het CMS bewerkt dat bestand; dit script
maakt er de HTML van, tussen

    <!-- BEGIN_TEAM --> ... <!-- EIND_TEAM -->

in ons-team.html.

Een portret dat niet al een webp van 560 bij 747 is (een foto die net via het
CMS is opgeladen, bijvoorbeeld), wordt bijgesneden tot 3 bij 4 en omgezet naar
assets/team/<naam>.webp. Dat vraagt Pillow; zonder Pillow wordt de foto zoals
hij is gebruikt, en snijdt de CSS hem bij.

    python tools/team.py            # schrijft de pagina bij
    python tools/team.py --check    # controleert alleen, exitcode 1 bij verschil
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "team.json"
PAGINA = ROOT / "ons-team.html"
FOTOS = ROOT / "assets" / "team"
MAAT = (560, 747)

STER = ('<svg aria-hidden="true" width="26" height="26" viewBox="0 0 100 100" fill="currentColor">'
        '<path d="M42 0 L58 0 L58 17.8 A24.2 24.2 0 0 0 82.2 42 L100 42 L100 58 L82.2 58 '
        'A24.2 24.2 0 0 0 58 82.2 L58 100 L42 100 L42 82.2 A24.2 24.2 0 0 0 17.8 58 L0 58 '
        'L0 42 L17.8 42 A24.2 24.2 0 0 0 42 17.8 Z"/></svg>')
PIJL = ('<svg aria-hidden="true" viewBox="0 0 37 12" fill="none" stroke="currentColor" '
        'stroke-width="1" width="22" height="8"><line x1="0" y1="6" x2="35" y2="6"/>'
        '<polyline points="30,1 36,6 30,11" fill="none"/></svg>')


def e(tekst) -> str:
    return html.escape(str(tekst), quote=True)


def slug(naam: str) -> str:
    t = unicodedata.normalize("NFKD", naam).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def lees() -> list[dict]:
    team = []
    for i, m in enumerate(json.loads(DATA.read_text(encoding="utf-8")), 1):
        naam = (m.get("naam") or "").strip()
        if not naam:
            raise SystemExit(f"medewerker {i} in data/team.json heeft geen naam")
        rollen = [r.strip() for r in (m.get("rollen") or []) if isinstance(r, str) and r.strip()]
        if not rollen:
            raise SystemExit(f"{naam}: geen functie ingevuld")
        email = (m.get("email") or "").strip().lower()
        if email and not re.fullmatch(r"[a-z0-9._-]+@polares\.be", email):
            raise SystemExit(f"{naam}: '{email}' is geen adres op @polares.be")
        linkedin = (m.get("linkedin") or "").strip()
        if linkedin and not linkedin.startswith("https://"):
            raise SystemExit(f"{naam}: de LinkedIn-link moet met https:// beginnen")
        # het CMS kan een pad met of zonder / vooraan bewaren
        foto = (m.get("foto") or "").strip().lstrip("/")
        if foto and not (ROOT / foto).exists():
            raise SystemExit(f"{naam}: de foto '{foto}' bestaat niet")
        team.append({"naam": naam, "rollen": rollen, "email": email, "linkedin": linkedin, "foto": foto})
    return team


def portret(m: dict, schrijf: bool) -> str:
    """Het pad van een portret in de juiste maat; maakt het zo nodig aan."""
    bron = ROOT / m["foto"]
    doel = FOTOS / f"{slug(m['naam'])}.webp"
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return m["foto"]
    with Image.open(bron) as im:
        if bron.suffix.lower() == ".webp" and im.size == MAAT:
            return m["foto"]
        if schrijf:
            # 3 bij 4, iets boven het midden: daar zit bij een portret het gezicht
            vorm = ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"), MAAT,
                                method=Image.LANCZOS, centering=(0.5, 0.35))
            vorm.save(doel, "WEBP", quality=82, method=6)
            print(f"portret gemaakt: {doel.relative_to(ROOT)} (uit {m['foto']})")
    return str(doel.relative_to(ROOT))


def lid(m: dict, schrijf: bool) -> str:
    if m["foto"]:
        foto = (f'            <div class="lid__foto"><img src="{e(portret(m, schrijf))}" alt="{e(m["naam"])}" '
                f'width="{MAAT[0]}" height="{MAAT[1]}" loading="lazy" decoding="async"></div>\n')
    else:
        foto = (f'            <div class="lid__foto lid__foto--leeg" role="img" '
                f'aria-label="Nog geen portret van {e(m["naam"])}">{STER}</div>\n')
    regels = [
        '          <li class="lid">\n', foto, '            <div>\n',
        f'              <p class="lid__naam">{e(m["naam"])}</p>\n',
        '              <p class="lid__rol">' + "".join(f"<span>{e(r)}</span>" for r in m["rollen"]) + "</p>\n",
    ]
    if m["email"]:
        regels.append(f'              <p><a class="lid__mail" href="mailto:{e(m["email"])}">{e(m["email"])}</a></p>\n')
    if m["linkedin"]:
        regels.append(f'              <a class="lid__linkedin" href="{e(m["linkedin"])}" target="_blank" '
                      f'rel="noopener noreferrer">LinkedIn {PIJL}</a>\n')
    regels += ['            </div>\n', '          </li>\n']
    return "".join(regels)


def bouw(schrijf: bool) -> str:
    tekst = PAGINA.read_text(encoding="utf-8")
    blok = ('<!-- BEGIN_TEAM (geschreven door tools/team.py uit data/team.json; bewerk daar) -->\n'
            '      <ul class="team-grid">\n'
            + "".join(lid(m, schrijf) for m in lees())
            + '      </ul>\n      <!-- EIND_TEAM -->')
    nieuw, n = re.subn(r"<!-- BEGIN_TEAM[^>]*-->.*?<!-- EIND_TEAM -->", lambda _: blok, tekst, flags=re.S)
    if n != 1:
        raise SystemExit("merktekens BEGIN_TEAM/EIND_TEAM niet gevonden in ons-team.html")
    return nieuw


def main() -> int:
    if "--check" in sys.argv:
        if bouw(schrijf=False) != PAGINA.read_text(encoding="utf-8"):
            print("FOUT: ons-team.html loopt niet gelijk met data/team.json. Draai 'python tools/team.py'.")
            return 1
        print("ons-team.html loopt gelijk met data/team.json.")
        return 0
    nieuw = bouw(schrijf=True)
    if nieuw == PAGINA.read_text(encoding="utf-8"):
        print("Niets te doen: ons-team.html liep al gelijk met data/team.json.")
    else:
        PAGINA.write_text(nieuw, encoding="utf-8")
        print("bijgewerkt: ons-team.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
