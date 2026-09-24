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

## De domeinnaam polares.be

De site draait op Cloudflare, voorlopig op `polares.meyten.com`. Om ze op
`polares.be` te zetten:

1. **De registratie van polares.be naar het eigen Combell-account.** Ze staat
   nu in het pakket van de vroegere websitebouwer; stopt dat pakket, dan kan de
   domeinnaam verlopen, en dan vallen site én mail weg. Dringend, los van de rest.
2. **De nameservers naar Cloudflare**: `dolly.ns.cloudflare.com` en
   `micah.ns.cloudflare.com`, in de plaats van de drie `european-server`. De
   zone staat in Cloudflare klaar, met alle records identiek en grijs (DNS
   only); nagekeken tegen de bestaande DNS, 27 van 28 gelijk (alleen de AAAA van
   `staging` ontbreekt, en die gaat weg).
3. **De lancering**, zodra de zone actief is: de A- en AAAA-records van `@` en
   `www` verwijderen, `polares.be` en `www.polares.be` als custom domain aan
   het project koppelen, de Redirect Rule "WWW to root" aanzetten en Always Use
   HTTPS. MX, TXT en de Microsoft-records blijven zoals ze zijn.
4. Nadien: `polares.meyten.com` loskoppelen, en na een week de oude hosting
   opzeggen.

## Voor de site live gaat

- **De zes berichten op Blijf op koers zijn voorbeelden.** Ze staan met datum en
  plaats in `sitemap.xml` en in de structured data, dus zodra het domein hierop
  draait kan Google verzonnen evenementen indexeren. Vervangen of verwijderen
  in het CMS, onder Blijf op koers.
- **Het formulier verstuurt via Resend** (`worker/index.js`, op
  `/api/contact`, gratis plan: 3.000 mails per maand, 100 per dag). Tijdens het
  testen van `polares@meyten.com` naar `thomas@meyten.com`. Voor de lancering:
  1. Bij Resend `polares.be` toevoegen als domein, regio Ireland. De records
     komen op `send.polares.be` en `resend._domainkey.polares.be`; de MX en
     SPF van Microsoft blijven ongemoeid.
  2. In `wrangler.jsonc` `AFZENDER` op polares.be zetten (bijvoorbeeld
     `website@polares.be`) en `ONTVANGER` op `info@polares.be`.
  3. Een nieuwe API-sleutel, alleen verzendrechten en alleen voor polares.be,
     als geheim `RESEND_API_KEY` in Cloudflare. De oude sleutel intrekken.
  Het adres van de bezoeker staat in `Reply-To`, nooit in `From`.
- **Privacyverklaring en algemene voorwaarden** laten nakijken door een jurist.
  De privacyverklaring vermeldt sinds 24 september het contactformulier,
  Cloudflare, Resend en Microsoft als verwerkers, en het vlaggetje in de
  sessieopslag; punt 4 en punt 6 verdienen de meeste aandacht.
- **Vercel loskoppelen.** Elke push gaat daar nog naartoe en publiceert de hele
  repo (ook `tools/`, `data/`, `TE-DOEN.md`) op een `vercel.app`-adres. Daarna
  `vercel.json` weghalen.

---

## Het CMS in gebruik nemen

Pages CMS is ingesteld (`.pages.yml`, uitleg in `data/LEESMIJ.md`). Wat nog
moet, en wat alleen de eigenaar van de GitHub-repo kan:

1. Aanmelden op app.pagescms.org met het GitHub-account van de repo.
2. De GitHub-app van Pages CMS installeren, alleen voor de repo `polares2`.
3. De redacteurs uitnodigen per e-mail (Collaborators). Zij hebben geen
   GitHub-account nodig.
4. Eén proefbewerking doen en nagaan dat ze na een minuut of twee online staat.

## Kleiner, niet blokkerend

- `algemene-voorwaarden.html` en `privacyverklaring.html` hebben nog geen kop,
  menu of huidige voet.
- **Fleur** mist haar familienaam, en **Valérie Mulayi** heeft nog geen portret
  (nu een kader met de poolster). Beide kan de redactie zelf aanvullen in het
  CMS, onder Ons team.
- Bevestigen: `nathalie.vandevelde@polares.be` (aaneen?) en `valerie@polares.be`
  (zonder accent).
- Het contactformulier heeft geen limiet per bezoeker. Misbruik kan alleen
  spam in de eigen inbox geven en kost niets; komt het voor, dan een limiet.
