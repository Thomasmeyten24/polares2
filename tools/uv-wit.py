#!/usr/bin/env python3
"""
Maakt witte versies van de tekeningen in de constellatie.

De tekeningen in assets/uv/ zijn donkerblauw (#11314d en #1c3755), want ze
worden ook op een witte achtergrond gebruikt: in het traject van hoofdstuk II en
bij de satelliet van hoofdstuk I. In de constellatie staan ze op de nachtelijke
hemel en moeten ze wit zijn.

Dat gebeurde met "filter: brightness(0) invert(1)" in CSS. Safari past een
CSS-filter niet toe op een <image> in een SVG, dus op een iPhone bleven de
hemellichamen donkerblauw op donkerblauw: zichtbaar noch aantikbaar terug te
vinden. Een witte kopie van het bestand heeft dat probleem niet, op geen enkele
browser.

    python tools/uv-wit.py

Schrijft assets/uv/<naam>-wit.svg en assets/uv/zwartgat-ring-wit.webp. De
webp-versie vraagt Pillow; ontbreekt dat, dan slaat het script die over en zegt
het erbij.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UV = ROOT / "assets" / "uv"

# De twee tinten van de lijntekeningen. Ze worden allebei zuiver wit, net zoals
# het CSS-filter ze allebei wit maakte.
TINTEN = ("#11314d", "#1c3755")
TEKENINGEN = ["kompas", "gps", "munt", "leefwereld", "satelliet",
              "expertise", "vermogen", "komeet"]


def svgs() -> int:
    gedaan = 0
    for naam in TEKENINGEN:
        bron = UV / f"{naam}.svg"
        if not bron.exists():
            print(f"ontbreekt: {bron.relative_to(ROOT)}")
            continue
        tekst = bron.read_text(encoding="utf-8")
        gevonden = set(m.lower() for m in re.findall(r"#[0-9a-fA-F]{6}", tekst))
        vreemd = gevonden - set(TINTEN)
        if vreemd:
            raise SystemExit(f"{naam}.svg heeft een onverwachte kleur: {sorted(vreemd)}")
        for tint in TINTEN:
            tekst = re.sub(re.escape(tint), "#ffffff", tekst, flags=re.I)
        doel = UV / f"{naam}-wit.svg"
        if doel.exists() and doel.read_text(encoding="utf-8") == tekst:
            continue
        doel.write_text(tekst, encoding="utf-8")
        print(f"geschreven: {doel.relative_to(ROOT)}")
        gedaan += 1
    return gedaan


def zwartgat() -> None:
    bron = UV / "zwartgat-ring.webp"
    doel = UV / "zwartgat-ring-wit.webp"
    if not bron.exists():
        print(f"ontbreekt: {bron.relative_to(ROOT)}")
        return
    try:
        from PIL import Image
    except ImportError:
        print("Pillow ontbreekt; zwartgat-ring-wit.webp niet gemaakt "
              "(pip install pillow)")
        return
    beeld = Image.open(bron).convert("RGBA")
    # alleen de kleur vervangen, de doorzichtigheid houdt de vorm
    wit = Image.new("RGBA", beeld.size, (255, 255, 255, 0))
    wit.putalpha(beeld.getchannel("A"))
    wit.save(doel, "WEBP", lossless=True)
    print(f"geschreven: {doel.relative_to(ROOT)}  ({doel.stat().st_size // 1024} kB)")


def main() -> int:
    svgs()
    zwartgat()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
