# Een bericht toevoegen aan "Blijf op koers"

Alles staat in **`berichten.json`**, in dezelfde map als dit bestand. Dat is de
enige plaats waar een bericht bestaat. Daaruit worden geschreven:

* het overzicht op `blijf-op-koers.html`;
* een **eigen pagina per bericht**, `blijf-op-koers/<id>.html`;
* de regels in `sitemap.xml`.

Elk bericht heeft een eigen adres omdat dat de enige manier is om er vanuit
Google of vanaf LinkedIn rechtstreeks op te landen. Een zoekmachine rangschikt
per pagina, en een gedeelde link toont de titel en de afbeelding van de pagina
waarnaar hij wijst.

## Zo doet u het

1. Open `data/berichten.json` op github.com en klik het potloodje.
2. Kopieer een bestaand blok (van `{` tot en met `},`), plak het bovenaan de
   lijst en pas de velden aan.
3. Sla op met "Commit changes".

Loopt er iets mis met de punctuatie, dan faalt de controle bij het opslaan en
staat er niets fout op de site. Twijfelt u: stuur de tekst door, dan zetten we
hem erop.

> **Let op:** wie alleen op github.com werkt, laat de gegenereerde pagina's
> achter. Iemand moet daarna nog `python tools/berichten.py` draaien en het
> resultaat mee committen; de controle in GitHub Actions zegt het als dat
> vergeten is. Zie hieronder.

## De velden

| veld | verplicht | wat |
|---|---|---|
| `id` | ja | korte naam zonder spaties, uniek, bijvoorbeeld `ontbijtsessie-mei-2027`. **Dit wordt het webadres** en verandert dus best niet meer nadat het bericht gedeeld is. Alleen kleine letters, cijfers en koppeltekens. |
| `type` | ja | `evenement`, `nieuws` of `inzicht`; bepaalt het label en het filter |
| `categorie` | ja | hoe het in de lijst heet, bijvoorbeeld `Inzichten & Advies` |
| `titel` | ja | de kop |
| `titelKort` | nee | kortere kop voor het tabblad en het zoekresultaat, als de titel lang is. Google toont ongeveer zestig tekens. |
| `datum` | ja | `jjjj-mm-dd`; hierop wordt gesorteerd, nieuwste bovenaan |
| `datumWeergave` | ja | dezelfde datum zoals hij op het scherm hoort, bijvoorbeeld `19 november 2026` |
| `tijd` | bij een evenement | `08:30 tot 10:30`. Hieruit komen begin- en einduur in de gegevens voor Google. |
| `locatie` | bij een evenement | adres |
| `deelname` | nee | bijvoorbeeld `Max. 10 families` |
| `leestijd` | nee | `4 min leestijd`, of bij een evenement `Aanmelden voor 12 november` |
| `uitgelicht` | nee | `true` bij het ene bericht dat bovenaan groot uitgelicht staat |
| `inleiding` | ja | twee zinnen; dit staat op de kaart, in het zoekresultaat en in het linkvoorbeeld |
| `inhoud` | ja | de volledige tekst, in HTML: `<p>…</p>`, eventueel `<ul><li>…</li></ul>` en `<strong>…</strong>` |

Zet `uitgelicht` bij hoogstens één bericht. Staat het bij niemand, dan toont de
pagina gewoon het kaartenraster.

## De pagina's bijwerken

Na een wijziging aan `berichten.json`:

```
python tools/berichten.py
```

Dat schrijft het overzicht, de pagina per bericht en de sitemap bij, en gooit de
pagina weg van een bericht dat u uit de JSON gehaald hebt. Het gebruikt alleen
de Python-standaardbibliotheek.

`python tools/berichten.py --check` zegt alleen of alles nog klopt. Dat is ook
wat de controle bij elke push doet: loopt het uiteen, dan faalt de build in
plaats van dat de site stilletjes achterloopt.

## De afbeelding voor het delen

Elk bericht krijgt een eigen kaart van 1200 bij 630 in `assets/og/`, die
LinkedIn en WhatsApp tonen bij een gedeelde link:

```
pip install pillow fonttools brotli
python tools/og-afbeeldingen.py
```

Dat maakt alleen wat nog ontbreekt; `--alles` maakt ze allemaal opnieuw. Draai
daarna nog eens `python tools/berichten.py`, want dat pikt de nieuwe afbeelding
op in de pagina.

Ontbreekt de afbeelding, dan valt het bericht terug op het algemene beeld van de
site. Dat werkt, maar dan lijken alle gedeelde links op elkaar.

## Het uitzicht van een berichtpagina

De opmaak staat in `tools/sjabloon-bericht.html`. Pas die aan, niet de bestanden
in `blijf-op-koers/`: die worden bij de volgende keer overschreven.
