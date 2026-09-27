// ── Polares: het contactformulier ───────────────────────────────────────────
// De site is statisch; alleen POST /api/contact komt hier terecht (zie
// run_worker_first in wrangler.jsonc). Alles andere serveert Cloudflare
// rechtstreeks uit dist/, met de regels uit _headers en _redirects.
//
// Het bericht gaat via Resend (resend.com) naar één vast adres: ONTVANGER in
// wrangler.jsonc. Niets uit het verzoek van de bezoeker bepaalt de ontvanger.
// Het adres van de bezoeker komt in Reply-To, nooit in From: From is altijd
// ons eigen, bij Resend geverifieerde adres, anders strandt het op SPF en DKIM.
//
// De API-sleutel van Resend staat als geheim in Cloudflare (RESEND_API_KEY),
// nooit in de code of de repo. Geef die sleutel bij Resend alleen
// verzendrechten, en alleen voor het domein van AFZENDER.

import { maakMail, ontsnap } from './mail.js';

const LIMIET = { naam: 200, email: 254, telefoon: 40, bericht: 5000 };
const MAX_BYTES = 20000;
// dezelfde eisen als in contact.html; geen tekens die in een mailto-link of
// een adreskop iets anders betekenen
const ADRES = /^[^\s@,;:<>()[\]"\\?#%&]+@[^\s@,;:<>()[\]"\\?#%&]+\.[^\s@,;:<>()[\]"\\?#%&.]{2,}$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== '/api/contact') return env.ASSETS.fetch(request);

    if (request.method !== 'POST') {
      return json({ ok: false, fout: 'Alleen POST.' }, 405, { Allow: 'POST' });
    }

    // Zonder JavaScript verstuurt de browser het formulier zelf, als gewoon
    // formulier; dan antwoorden we met een pagina in plaats van JSON.
    const soort = (request.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
    const alsPagina = soort === 'application/x-www-form-urlencoded';
    const antwoord = (inhoud, st) => (alsPagina ? pagina(inhoud.ok, st, url) : json(inhoud, st));

    // Alleen vanaf de site zelf en alleen over HTTPS: een formulier op een
    // andere site mag dit eindpunt niet gebruiken. Browsers sturen Origin
    // altijd mee bij een POST. De hele origin vergelijken, als tekst: dat
    // vangt ook "null", http en rare waarden zonder dat er iets kan falen.
    const lokaal = url.hostname === 'localhost' || url.hostname === '127.0.0.1';
    if ((url.protocol !== 'https:' && !lokaal) || request.headers.get('Origin') !== url.origin) {
      return antwoord({ ok: false, fout: 'Niet toegestaan.' }, 403);
    }

    let d;
    try {
      if (Number(request.headers.get('Content-Length') || 0) > MAX_BYTES) throw new Error('te groot');
      const ruw = await request.text();
      if (ruw.length > MAX_BYTES) throw new Error('te groot');
      d = alsPagina ? Object.fromEntries(new URLSearchParams(ruw)) : JSON.parse(ruw);
      if (!d || typeof d !== 'object') throw new Error('geen object');
    } catch {
      return antwoord({ ok: false, fout: 'Ongeldig verzoek.' }, 400);
    }

    // Het onzichtbare veld: een mens laat het leeg, een robot vult het in.
    // Dan zeggen we "gelukt" zonder iets te versturen, zodat de robot niet
    // leert dat hij betrapt is. ('website' is de oude naam van het veld.)
    if (regel(d.cform_extra) || regel(d.website)) return antwoord({ ok: true }, 200);

    const naam = regel(d.naam);
    const email = regel(d.email);
    const telefoon = regel(d.telefoon);
    const tekst = alinea(d.bericht);
    // zonder JavaScript kan de keuze niet het veld verbergen: wie een bericht
    // schreef, wil dat het meekomt
    const wijze = d.wijze === 'bericht' || (alsPagina && tekst) ? 'bericht' : 'bellen';
    const bericht = wijze === 'bericht' ? tekst : '';

    // Te lang wordt niet stil ingekort: de bezoeker hoort het.
    for (const [veld, waarde] of Object.entries({ naam, email, telefoon, bericht })) {
      if ([...waarde].length > LIMIET[veld]) return antwoord({ ok: false, fout: 'Te lang.', veld }, 413);
    }

    // Dezelfde eisen als in de browser: minstens één manier om te antwoorden,
    // en wat ingevuld is moet kloppen.
    const mailOk = email !== '' && ADRES.test(email);
    const telOk = telefoon !== '' && telefoon.replace(/\D/g, '').length >= 8;
    if (!mailOk && !telOk) return antwoord({ ok: false, fout: 'Geen geldig adres of nummer.' }, 400);
    if ((email && !mailOk) || (telefoon && !telOk)) return antwoord({ ok: false, fout: 'Een ingevuld veld klopt niet.' }, 400);
    if (wijze === 'bericht' && bericht.replace(/\s/g, '').length < 2) return antwoord({ ok: false, fout: 'Geen bericht.' }, 400);

    // het tijdstip zoals Polares het leest, niet in UTC
    const moment = new Intl.DateTimeFormat('nl-BE', {
      timeZone: 'Europe/Brussels', dateStyle: 'long', timeStyle: 'short',
    }).format(new Date());
    const mail = maakMail({ naam, email, telefoon, wijze, bericht, mailOk, telOk, host: url.host, moment });

    // Nog geen sleutel ingesteld: 501, en dan valt het formulier in de browser
    // terug op het mailprogramma van de bezoeker in plaats van te falen.
    if (!env.RESEND_API_KEY) {
      console.error('versturen niet ingesteld: RESEND_API_KEY ontbreekt');
      return antwoord({ ok: false, fout: 'Versturen is niet ingesteld.' }, 501);
    }
    const stuur = (metAntwoordadres) =>
      // RESEND_API is alleen voor lokaal testen tegen een nagebootste server
      fetch(env.RESEND_API || 'https://api.resend.com/emails', {
        method: 'POST',
        // hangt Resend, dan geeft de bezoeker niet eindeloos op 'Versturen…'
        signal: AbortSignal.timeout(10000),
        headers: {
          Authorization: 'Bearer ' + env.RESEND_API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: 'Polares website <' + env.AFZENDER + '>',
          to: [env.ONTVANGER],
          ...(metAntwoordadres ? { reply_to: email } : {}),
          subject: mail.onderwerp,
          text: mail.tekst,
          html: mail.html,
        }),
      });
    try {
      let r = await stuur(mailOk);
      // Weigert Resend het antwoordadres, dan toch versturen zonder: het
      // adres staat ook in de mail zelf, en het bericht gaat niet verloren.
      if (r.status === 422 && mailOk) {
        console.error('Resend weigerde het antwoordadres; opnieuw zonder', (await r.text()).slice(0, 300));
        r = await stuur(false);
      }
      if (!r.ok) throw new Error('Resend ' + r.status + ': ' + (await r.text()).slice(0, 300));
    } catch (e) {
      // de fout zelf in de logboeken van Cloudflare, niet bij de bezoeker
      console.error('versturen mislukt', e && (e.message || e));
      return antwoord({ ok: false, fout: 'Versturen mislukt.' }, 502);
    }
    return antwoord({ ok: true }, 200);
  },
};

// Onzichtbare en sturende tekens die niets in een naam of adres te zoeken
// hebben: stuurtekens, zero-width-tekens en de bidi-tekens waarmee tekst
// zich anders kan voordoen dan hij is.
const ONZICHTBAAR = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F\u200B-\u200F\u202A-\u202E\u2060-\u2064\u2066-\u2069\uFEFF]/g;

// één regel: ook geen regeleinden, want naam en adres komen in het onderwerp
function regel(v) {
  return typeof v === 'string' ? v.replace(ONZICHTBAAR, '').replace(/\s+/g, ' ').trim() : '';
}

// een bericht: regeleinden en tabs blijven, al de rest zoals hierboven
function alinea(v) {
  return typeof v === 'string' ? v.replace(/\r\n?/g, '\n').replace(ONZICHTBAAR, (c) => (c === '\t' || c === '\n' ? c : '')).trim() : '';
}

function json(inhoud, status = 200, extra = {}) {
  return new Response(JSON.stringify(inhoud), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Robots-Tag': 'noindex',
      ...extra,
    },
  });
}

// Het antwoord voor wie het formulier zonder JavaScript verstuurde: een
// eenvoudige pagina in de stijl van de site, met de weg terug.
function pagina(ok, status, url) {
  const titel = ok ? 'Bedankt, we hebben uw vraag goed ontvangen.' : 'Het versturen lukte niet.';
  const zin = ok
    ? 'We nemen persoonlijk contact met u op.'
    : (status === 413 ? 'Uw bericht is te lang: hoogstens 5000 tekens. ' : status === 400 ? 'Controleer het e-mailadres of het telefoonnummer. ' : '')
      + 'U kunt ons ook rechtstreeks bereiken: mail naar <a href="mailto:info@polares.be">info@polares.be</a> of bel <a href="tel:+3254235050">+32 54 23 50 50</a>.';
  const html = '<!DOCTYPE html><html lang="nl-BE"><head><meta charset="utf-8">'
    + '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
    + '<title>' + ontsnap(ok ? 'Bedankt | Polares' : 'Niet verstuurd | Polares') + '</title>'
    + '<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
    + '<style>body{margin:0;font-family:"Source Sans Pro",system-ui,-apple-system,"Segoe UI",sans-serif;color:#10324E;background:#FAFBFC;line-height:1.7}'
    + 'main{max-width:40rem;margin:0 auto;padding:clamp(3rem,10vw,7rem) 1.5rem}'
    + 'h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(1.7rem,4vw,2.4rem);line-height:1.2;margin:0 0 1rem}'
    + 'p{color:#5A7388;margin:0 0 2rem}a{color:#10324E}.terug{font-size:13px;letter-spacing:.08em;text-transform:uppercase}'
    + ':focus-visible{outline:2px solid #10324E;outline-offset:2px}</style></head>'
    + '<body><main><h1>' + ontsnap(titel) + '</h1><p>' + zin + '</p>'
    + '<a class="terug" href="' + ontsnap(ok ? '/' : '/contact.html') + '">' + (ok ? '&#8592; Terug naar polares.be' : '&#8592; Terug naar het formulier') + '</a>'
    + '</main></body></html>';
  return new Response(html, {
    status,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Robots-Tag': 'noindex',
    },
  });
}
