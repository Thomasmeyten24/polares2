# De inhoud van polares.be bewerken

Twee dingen op de site worden bijgehouden als gegevens, niet als pagina's:

* **Blijf op koers**: `berichten.json`. Daaruit komen het overzicht, een eigen
  pagina per bericht, de deelafbeelding per bericht en de regels in de sitemap.
* **Ons team**: `team.json`. Daaruit komt het raster op `ons-team.html`.

De rest van de site (de teksten op de pagina's, de opmaak, de constellatie) is
handwerk en staat in de HTML-bestanden zelf.

## Via het CMS (de gewone weg)

1. Ga naar **app.pagescms.org** en meld je aan. Wie uitgenodigd is, kreeg een
   e-mail; een GitHub-account is daarvoor niet nodig.
2. Kies **Blijf op koers** of **Ons team**.
3. Pas aan, of voeg een nieuw item toe, en klik op **Save**.

Na het opslaan bouwt Cloudflare de site opnieuw. Na een minuut of twee staat de
wijziging online, ook de nieuwe deelafbeelding en de sitemap.

Loopt er iets mis (een verplicht veld leeg, een ongeldig webadres), dan
publiceert Cloudflare niets en blijft de vorige versie gewoon online. De
melding staat dan in Cloudflare onder Workers & Pages → polares → Deployments,
met de naam van het bericht of de medewerker erin.

## Een bericht

| veld | wat |
|---|---|
| Titel | de kop |
| Soort | evenement, nieuws of inzicht; bepaalt het label en het filter |
| Datum | bij een evenement de dag zelf; de nieuwste staan bovenaan |
| Inleiding | twee zinnen voor de kaart, Google en het voorbeeld van een gedeelde link |
| Tekst | de volledige tekst |
| Uur, Plaats, Deelname | bij een evenement; het uur als `08:30 tot 10:30` |
| Onder de titel | `4 min leestijd`, of `Aanmelden voor 12 november` |
| Korte titel | alleen als de titel lang is; Google toont ongeveer zestig tekens |
| Groot bovenaan | bij hoogstens één bericht |
| Webadres | kleine letters, cijfers en koppeltekens, bijvoorbeeld `ontbijtsessie-mei-2027`. **Niet meer wijzigen als het bericht gedeeld is**: een gedeelde link wijst naar dit adres. |

De categorie ("Inzichten & Advies") en de datum voluit ("Donderdag 19 november
2026") hoeven niet ingevuld te worden: `tools/berichten.py` leidt ze af.

## Een medewerker

| veld | wat |
|---|---|
| Naam | voornaam en familienaam |
| Functie | één regel per functie, meestal één |
| E-mailadres | op @polares.be, of leeg |
| LinkedIn | de volledige link, of leeg |
| Portret | een staande foto; de site snijdt hem bij tot 3 bij 4 en maakt hem licht |

De volgorde in de lijst is de volgorde op de pagina.

## Voor wie lokaal werkt

```
python3 tools/bouw-site.py
```

Dat doet wat Cloudflare doet: de pagina's maken uit de gegevens, de
consistentiecontrole draaien en `dist/` vullen. Na een wijziging in het CMS
lopen de gemaakte bestanden in de repo zelf achter; draai dit eerst, en commit
wat verandert als je die bestanden bijgewerkt in de repo wilt.

Pillow en fontTools zijn nodig voor de deelafbeeldingen en de portretten
(`pip install pillow fonttools brotli`). Ontbreken ze lokaal, dan blijven de
bestaande afbeeldingen gewoon staan.

De opmaak van een berichtpagina staat in `tools/sjabloon-bericht.html`. Pas die
aan, niet de bestanden in `blijf-op-koers/`: die worden bij elke build
overschreven. Hetzelfde geldt voor het raster op `ons-team.html`, tussen de
merktekens `BEGIN_TEAM` en `EIND_TEAM`.

Wat het CMS toont, staat in `.pages.yml` in de hoofdmap. Een veld dat daar niet
staat, kan het CMS bij het opslaan weglaten; de consistentiecontrole bewaakt dat
elk veld uit de gegevens er ook in staat.
