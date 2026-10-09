# Te doen

Wat er nog openstaat aan deze site, en waarop het wacht. Geen wensenlijst: alles
wat hier staat is besproken en beslist, of wacht op één duidelijk antwoord.

---

## Analytics en vindbaarheid

**Kan nu:** de site draait sinds 9 oktober op `polares.be`.

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

Live sinds 9 oktober 2026. De registratie staat bij INWX, de nameservers bij
Cloudflare, en `polares.be`, `www.polares.be` en `polares.meyten.com` hangen
als custom domain aan de Worker (`routes` in `wrangler.jsonc`). www gaat met de
Redirect Rule "Redirect from WWW to root" naar polares.be; Always Use HTTPS
staat aan. De mailrecords zijn ongewijzigd overgenomen.

De oude hosting (`linweb424.webhosting.be`) zegt de vorige beheerder op. De
records die er nog naartoe wezen (`ftp`, `staging`, `ssh`) zijn op 9 oktober
verwijderd, en de SPF-record is ingekort; de oude waarden staan in
`DNS-BACKUP.md`.

Nog te doen:

1. De SPF-record laat nog `ip4:78.23.80.15` toe, een Telenet-aansluiting,
   vermoedelijk het kantoor. Nagaan bij Polares of iets daar rechtstreeks
   mail als @polares.be verstuurt (NAS, scanner, boekhoudpakket). Zo niet, dan
   de SPF terugbrengen tot `v=spf1 include:spf.protection.outlook.com -all`.
2. `polares.meyten.com` loskoppelen zodra het niet meer nodig is als testadres:
   uit `routes` in `wrangler.jsonc` halen en pushen.

## Voor de site live gaat

- **Blijf op koers staat voorlopig niet online** (sinds 9 oktober): de zes
  berichten zijn nog voorbeelden. `BLIJF_OP_KOERS = False` in
  `tools/bouw-site.py` laat de pagina's, hun deelafbeeldingen, de links in menu,
  voet en 404 en de adressen in de sitemap weg uit `dist/`; oude adressen gaan
  tijdelijk (302) naar de homepage. In de repo en het CMS blijft alles werken.
  Weer online: echte berichten in het CMS, dan de schakelaar op `True`.
- **Het formulier verstuurt via Resend** (`worker/index.js`, op
  `/api/contact`, gratis plan: 3.000 mails per maand, 100 per dag), van
  `website@polares.be` naar `info@polares.be`. polares.be is sinds 9 oktober
  geverifieerd bij Resend (regio Ireland, records op `send`, `rsend` en
  `resend._domainkey`). Het adres van de bezoeker staat in `Reply-To`, nooit
  in `From`.
- **Privacyverklaring en algemene voorwaarden** laten nakijken door een jurist.
  De privacyverklaring vermeldt sinds 24 september het contactformulier,
  Cloudflare, Resend en Microsoft als verwerkers, en het vlaggetje in de
  sessieopslag; punt 4 en punt 6 verdienen de meeste aandacht. Sinds 27
  september ook MyPolares (MyFaro) en LinkedIn, en onder het formulier staat
  een regel over het gebruik van de gegevens: neem die mee. In de voet staat
  "KBO BE 1032.172.446": laat de jurist ook de wettelijke vermeldingen
  (ondernemingsnummer, RPR en rechtbank) nakijken.
- **Always Use HTTPS voor het testadres.** `polares.meyten.com` antwoordt nog
  over gewone HTTP. In Cloudflare, zone meyten.com: SSL/TLS → Edge
  Certificates → Always Use HTTPS. De site stuurt zelf al HSTS mee (`_headers`),
  maar die werkt pas na een eerste bezoek over HTTPS.
- **De nachtelijke update van Blijf op koers nakijken.** `.github/workflows/dagelijks.yml`
  commit de pagina's als er een evenement voorbij is. Na de eerste keer dat dat
  gebeurt (na 15 oktober: "Aanmelden afgesloten" bij de rondetafel) nagaan
  dat Cloudflare daarna ook echt opnieuw gebouwd heeft. Werkt dat niet, dan
  een deploy hook van Cloudflare aanroepen vanuit de workflow.

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
