# Back-up van verwijderde DNS-records

Records van polares.be die verwijderd zijn bij het opruimen van de oude
hosting (`linweb424.webhosting.be`, beheerd door de vorige websitebouwer).
Blijkt er toch iets aan te hangen, zet het record dan terug in Cloudflare
(polares.be → DNS → Records) met precies deze waarden, op "DNS only".

Genoteerd op 9 oktober 2026, zoals ze toen publiek in de DNS stonden.

| Naam | Type | Inhoud | Waarvoor |
|---|---|---|---|
| `ftp.polares.be` | A | `5.134.4.184` | bestanden opladen naar de oude hosting |
| `staging.polares.be` | A | `5.134.4.194` | testversie van de oude site |
| `staging.polares.be` | AAAA | `2a00:1c98:1000:1174:0:2:22d6:9ed9` | idem; stond niet in Cloudflare, alleen bij de vorige DNS |
| `ssh.polares.be` | CNAME | `ssh044.webhosting.be` | inloggen op de server van de oude hosting |

## SPF-record (TXT op polares.be)

Vóór de aanpassing:

```
v=spf1 a ip4:78.23.80.15 ip4:188.93.84.76/32 ip4:188.93.85.86/32 include:spf.protection.outlook.com -all
```

- `a`: het adres van de website; sinds de lancering is dat Cloudflare.
- `ip4:78.23.80.15`: een Telenet-aansluiting, vermoedelijk het kantoor.
- `ip4:188.93.84.76/32`: ITAF Hosting (`itafpanel05.itafhosting.be`).
- `ip4:188.93.85.86/32`: vermoedelijk ook ITAF; geen omgekeerde DNS.
- `include:spf.protection.outlook.com`: Microsoft 365.
