# Een bericht toevoegen aan "Blijf op koers"

Alles staat in **`berichten.json`**, in dezelfde map als dit bestand. Dat is de
enige plaats waar een bericht bestaat: de kaarten op de pagina worden eruit
geschreven.

## Zo doet u het

1. Open `data/berichten.json` op github.com en klik het potloodje.
2. Kopieer een bestaand blok (van `{` tot en met `},`), plak het bovenaan de
   lijst en pas de velden aan.
3. Sla op met "Commit changes". Vercel zet de site binnen de minuut online.

Loopt er iets mis met de punctuatie, dan faalt de controle bij het opslaan en
staat er niets fout op de site. Twijfelt u: stuur de tekst door, dan zetten we
hem erop.

## De velden

| veld | verplicht | wat |
|---|---|---|
| `id` | ja | korte naam zonder spaties, uniek — bijvoorbeeld `ontbijtsessie-mei-2027` |
| `type` | ja | `evenement`, `nieuws` of `inzicht` — bepaalt het label en het filter |
| `categorie` | ja | hoe het in de lijst heet, bijvoorbeeld `Inzichten & Advies` |
| `titel` | ja | de kop |
| `datum` | ja | `jjjj-mm-dd`; hierop wordt gesorteerd, nieuwste bovenaan |
| `datumWeergave` | ja | dezelfde datum zoals hij op het scherm hoort, bijvoorbeeld `19 november 2026` |
| `tijd` | bij een evenement | bijvoorbeeld `08:30 — 10:30` |
| `locatie` | bij een evenement | adres |
| `deelname` | nee | bijvoorbeeld `Max. 10 families` |
| `leestijd` | nee | `4 min leestijd`, of bij een evenement `Aanmelden voor 12 november` |
| `uitgelicht` | nee | `true` bij het ene bericht dat bovenaan groot uitgelicht staat |
| `inleiding` | ja | twee zinnen; dit staat op de kaart |
| `inhoud` | ja | de volledige tekst, in HTML: `<p>…</p>`, eventueel `<ul><li>…</li></ul>` en `<strong>…</strong>` |

Zet `uitgelicht` bij hoogstens één bericht. Staat het bij niemand, dan toont de
pagina gewoon het kaartenraster.

## Na een wijziging buiten github.com

Bewerkt u het bestand lokaal, draai dan even:

```
python tools/berichten.py
```

Dat schrijft de kaarten in `blijf-op-koers.html` bij. `python tools/berichten.py --check`
zegt alleen of het nog klopt; dat is ook wat de controle bij elke push doet.
