# Te doen

Wat er nog openstaat aan deze site, en waarop het wacht. Geen wensenlijst: alles
wat hier staat is besproken en beslist, of wacht op één duidelijk antwoord.

---

## Analytics en vindbaarheid

**Wacht op:** de site draait op Cloudflare onder `polares.be` of `new.polares.be`.

**Waarom niet eerder.** Search Console verifieert een *domein*; vanaf een lokale
server kan dat niet. Het meetscript moet op de echte URL getest worden. En het
testadres mag niet meetellen in de cijfers: `_headers` zet daar al
`X-Robots-Tag: noindex` op (alles behalve `polares.be`), het meetscript moet
dezelfde uitzondering krijgen.

### Eerst beslissen (Polares)

1. **Welke teller?**
   - *Gratis:* Cloudflare Web Analytics. Cookieloos, onbeperkt, één scriptregel.
     Geeft bezoekers, pagina's, verwijzers, land en toestel. Amerikaans bedrijf.
     Meet geen klikken op e-mail of telefoon.
   - *Ongeveer tien euro per maand:* een Europese teller (Plausible, Simple
     Analytics). Gegevens in de EU, en wél meetbaar of iemand op `info@polares.be`
     klikt of het formulier verstuurt. Prijzen wijzigen; check ze op dat moment.
2. **Welk Google-account** voor Search Console? Liefst een kantooraccount, geen
   persoonlijk: het moet een collega kunnen overnemen.
3. De DNS van polares.be staat bij Cloudflare. Verificatie via een DNS-record
   verdient de voorkeur boven een bestand of meta-tag: die blijft geldig los van
   wat er op de site verandert. Cloudflare Web Analytics staat dan ook in
   hetzelfde account.

De accounts maakt Polares zelf aan.

### Stappen

1. Search Console: domeinverificatie via een DNS TXT-record.
2. Bing Webmaster Tools: kan de verificatie van Google overnemen. Telt mee voor
   de antwoorden van Copilot.
3. `sitemap.xml` indienen in beide.
4. Meetscript toevoegen aan alle pagina's **en aan `tools/sjabloon-bericht.html`**,
   anders missen de berichtpagina's het bij de volgende keer dat het script draait.
5. Het meetscript uitschakelen op een niet-productieadres, zodat testverkeer niet
   meetelt.
6. `privacyverklaring.html` bijwerken. Daar staat nu letterlijk "geen tracking-
   of analysetools"; dat klopt dan niet meer. Neem meteen het vlaggetje mee dat
   hieronder bij de kleine punten staat.
7. Bij een betalende teller: doelen instellen voor klikken op `info@polares.be`,
   op het telefoonnummer en op het versturen van het formulier.
8. Een controle toevoegen aan `tools/check-consistentie.py` die nagaat dat elke
   pagina het meetscript draagt.

### Cookiebanner

**Niet nodig** met deze opzet, zolang de teller cookieloos is: er wordt niets op
het toestel van de bezoeker gezet of gelezen, en dát is waar de toestemmingsregel
over gaat. Search Console staat er helemaal buiten, want dat zet geen script op
de site.

Wel vermelden in de privacyverklaring: geen toestemming nodig is niet hetzelfde
als niets zeggen.

**Wél een banner nodig zodra** er Google Analytics bij komt, of een ingesloten
YouTube-video, een Google Maps-kaartje, een LinkedIn-widget, of lettertypen van
Google's servers in plaats van de eigen. Nu komt er geen enkel extern verzoek van
de site; dat is de moeite waard om te bewaken.

Dit is geen juridisch advies. Laat het meenemen wanneer een jurist de
privacyverklaring nakijkt.

### Na te kijken zodra het draait

- Zijn alle pagina's geïndexeerd, de berichtpagina's inbegrepen?
- Meldt Search Console fouten in de structured data van de evenementen?
- Sluit de teller het testadres uit?

---

## Voor de site live gaat

- **De zes berichten op Blijf op koers zijn voorbeelden.** Ze staan met datum en
  plaats in `sitemap.xml` en in de structured data, dus zodra het domein hierop
  draait kan Google verzonnen evenementen indexeren. Vervangen in
  `data/berichten.json`, daarna `python tools/berichten.py` en
  `python tools/og-afbeeldingen.py`. Zie `data/LEESMIJ.md`.
- **Het formulier verstuurt nog niet zelf.** Het valt terug op het
  mailprogramma van de bezoeker; dat werkt, maar is een drempel. De site staat op
  Cloudflare, dus geen `contact.php`: het wordt een kleine Cloudflare-functie op
  `/api/contact`, en `VERZENDPUNT` in `index.html` gaat daarnaar wijzen (daarna
  `python tools/gedeeld.py`). Wacht op één keuze: versturen via Microsoft 365
  (Graph API, met een app-registratie in het eigen tenant) of via een
  verzenddienst. De mail van Polares loopt via Microsoft, dus een verzenddienst
  moet in SPF en DKIM mee. Sleutels horen in de instellingen van Cloudflare,
  nooit in de repo. Het adres van de bezoeker hoort in `Reply-To`, nooit in
  `From`. Zet ook `html_handling` en de route voor `/api/*` na in
  `wrangler.jsonc`.
- **Privacyverklaring: Cloudflare vermelden.** Cloudflare levert de site en ziet
  daarbij de IP-adressen van bezoekers. Eén zin, mee te nemen wanneer de jurist
  de tekst nakijkt.
- **Privacyverklaring en algemene voorwaarden** staan als basistekst in de
  bestanden, met een notitie dat een jurist ze moet nakijken.
- **De oude hosting opzeggen**, bij de vroegere websitebouwer, pas als de site
  een week stabiel op Cloudflare draait.

---

## Kleiner, niet blokkerend

- `algemene-voorwaarden.html` en `privacyverklaring.html` hebben nog geen kop,
  menu of huidige voet.
- **Fleur** mist haar familienaam; die staat niet in het brondocument.
- **Valérie Mulayi** heeft nog geen portret (nu een kader met de poolster).
- Bevestigen: `nathalie.vandevelde@polares.be` (aaneen?) en `valerie@polares.be`
  (zonder accent).
- De teksten bij de symbolen van de constellatie zouden bijgestuurd worden.
- `sessionStorage['polares-visited']` slaat één vlaggetje op om de intro-animatie
  over te slaan bij een tweede pagina. Geen persoonsgegeven, maar de
  privacyverklaring zegt nu "geen cookies". Vermelden of het trucje schrappen.
- Op een telefoon scrolt de pagina zeven pixels horizontaal, door de SVG van de
  constellatie die buiten haar kader tekent.
- De aanwijzing "Klik op een hemellichaam" schuift aan het eind van het
  klikvenster onder het witte blad van het traject.
