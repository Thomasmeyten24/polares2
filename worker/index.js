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

const LIMIET = { naam: 200, email: 254, telefoon: 40, bericht: 5000 };

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== '/api/contact') return env.ASSETS.fetch(request);

    if (request.method !== 'POST') {
      return json({ ok: false, fout: 'Alleen POST.' }, 405, { Allow: 'POST' });
    }

    // Alleen vanaf de site zelf: een formulier op een andere site mag dit
    // eindpunt niet gebruiken. Browsers sturen Origin altijd mee bij een POST.
    const herkomst = request.headers.get('Origin');
    if (!herkomst || new URL(herkomst).host !== url.host) {
      return json({ ok: false, fout: 'Niet toegestaan.' }, 403);
    }

    let d;
    try {
      if (Number(request.headers.get('Content-Length') || 0) > 20000) throw new Error('te groot');
      d = await request.json();
    } catch {
      return json({ ok: false, fout: 'Ongeldig verzoek.' }, 400);
    }

    // Het onzichtbare veld: een mens laat het leeg, een robot vult het in.
    // Dan zeggen we "gelukt" zonder iets te versturen, zodat de robot niet
    // leert dat hij betrapt is.
    if (tekst(d.website)) return json({ ok: true });

    const naam = tekst(d.naam).slice(0, LIMIET.naam);
    const email = tekst(d.email).slice(0, LIMIET.email);
    const telefoon = tekst(d.telefoon).slice(0, LIMIET.telefoon);
    const wijze = d.wijze === 'bericht' ? 'bericht' : 'bellen';
    const bericht = wijze === 'bericht' ? tekst(d.bericht).slice(0, LIMIET.bericht) : '';

    // Dezelfde eisen als in de browser: minstens één manier om te antwoorden,
    // en wat ingevuld is moet kloppen.
    const mailOk = email !== '' && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
    const telOk = telefoon !== '' && telefoon.replace(/\D/g, '').length >= 8;
    if (!mailOk && !telOk) return json({ ok: false, fout: 'Geen geldig adres of nummer.' }, 400);
    if (wijze === 'bericht' && bericht.length < 2) return json({ ok: false, fout: 'Geen bericht.' }, 400);

    const onderwerp = (wijze === 'bericht' ? 'Bericht' : 'Contactverzoek') + ' via polares.be' + (naam ? ': ' + naam : '');
    const regels = [
      ['Naam', naam || '(niet ingevuld)'],
      ['E-mail', email || '(niet ingevuld)'],
      ['Telefoon', telefoon || '(niet ingevuld)'],
      ['Vraag', wijze === 'bericht' ? 'stuurt een bericht' : 'wil graag gecontacteerd worden'],
    ];
    const tekstversie = regels.map(([k, v]) => k + ': ' + v).join('\n')
      + (bericht ? '\n\n' + bericht : '')
      + '\n\n—\nVerstuurd via het contactformulier op ' + url.host + '.'
      + (mailOk ? ' Antwoorden gaat rechtstreeks naar ' + email + '.' : '');
    const htmlversie = '<table cellpadding="4" style="font-family:Arial,sans-serif;font-size:14px;color:#10324E">'
      + regels.map(([k, v]) => '<tr><td style="color:#5A7388">' + k + '</td><td>' + ontsnap(v) + '</td></tr>').join('')
      + '</table>'
      + (bericht ? '<p style="font-family:Arial,sans-serif;font-size:14px;color:#10324E;white-space:pre-wrap">' + ontsnap(bericht) + '</p>' : '')
      + '<p style="font-family:Arial,sans-serif;font-size:12px;color:#7E94A6">Verstuurd via het contactformulier op '
      + ontsnap(url.host) + '.' + (mailOk ? ' Antwoorden gaat rechtstreeks naar ' + ontsnap(email) + '.' : '') + '</p>';

    // Nog geen sleutel ingesteld: 501, en dan valt het formulier in de browser
    // terug op het mailprogramma van de bezoeker in plaats van te falen.
    if (!env.RESEND_API_KEY) {
      console.error('versturen niet ingesteld: RESEND_API_KEY ontbreekt');
      return json({ ok: false, fout: 'Versturen is niet ingesteld.' }, 501);
    }
    try {
      // RESEND_API is alleen voor lokaal testen tegen een nagebootste server
      const r = await fetch(env.RESEND_API || 'https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: 'Bearer ' + env.RESEND_API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: 'Polares website <' + env.AFZENDER + '>',
          to: [env.ONTVANGER],
          ...(mailOk ? { reply_to: email } : {}),
          subject: onderwerp,
          text: tekstversie,
          html: htmlversie,
        }),
      });
      if (!r.ok) throw new Error('Resend ' + r.status + ': ' + (await r.text()).slice(0, 300));
    } catch (e) {
      // de fout zelf in de logboeken van Cloudflare, niet bij de bezoeker
      console.error('versturen mislukt', e && (e.message || e));
      return json({ ok: false, fout: 'Versturen mislukt.' }, 502);
    }
    return json({ ok: true });
  },
};

function tekst(v) {
  return typeof v === 'string' ? v.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim() : '';
}

function ontsnap(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
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
