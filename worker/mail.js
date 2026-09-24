// ── De mail die Polares krijgt bij een bericht via het formulier ──────────────
// In de huisstijl van de site, maar met wat mailprogramma's aankunnen: tabellen
// en inline stijl, geen eigen lettertypes (Georgia staat in voor Cantata One),
// geen afbeeldingen (die blokkeert Outlook standaard, en een logo dat niet
// laadt oogt slordiger dan een woordmerk in tekst) en geen SVG (Gmail toont
// dat niet). Kleuren uit het design system van de site.

const K = {
  navy900: '#071826', navy600: '#10324E', navy400: '#5A7388', navy300: '#7E94A6',
  navy200: '#A1B2C0', navy100: '#D8DEE5', navy50: '#EEF1F5', lijn: '#E5E5E5', wit: '#FFFFFF',
};
const SERIF = "Georgia, 'Times New Roman', serif";
const SANS = "'Source Sans Pro', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

export function maakMail(v) {
  // v: { naam, email, telefoon, wijze, bericht, mailOk, telOk, host, moment }
  const wie = v.naam || 'Een bezoeker';
  const titel = v.wijze === 'bericht' ? 'Nieuw bericht via de website' : 'Contactverzoek via de website';
  const zin = v.wijze === 'bericht' ? wie + ' stuurt een bericht.' : wie + ' wil graag gecontacteerd worden.';
  const onderwerp = (v.wijze === 'bericht' ? 'Bericht' : 'Contactverzoek') + ' via polares.be' + (v.naam ? ': ' + v.naam : '');
  const telHref = 'tel:' + v.telefoon.replace(/[^\d+]/g, '');
  const antwoordHref = 'mailto:' + v.email + '?subject=' + encodeURIComponent('Re: ' + onderwerp);

  // ── tekstversie: voor wie geen HTML toont, en voor de spamfilters ────────
  const tekst = [
    'POLARES · CONTACTFORMULIER', '',
    titel, zin, '',
    'Naam:      ' + (v.naam || '(niet ingevuld)'),
    'E-mail:    ' + (v.email || '(niet ingevuld)'),
    'Telefoon:  ' + (v.telefoon || '(niet ingevuld)'),
    ...(v.bericht ? ['', 'Bericht:', v.bericht] : []),
    '', '—',
    'Verstuurd via het contactformulier op ' + v.host + ', ' + v.moment + '.',
    v.mailOk ? 'Beantwoorden gaat rechtstreeks naar ' + v.email + '.' : 'Geen e-mailadres opgegeven: bel terug op het nummer hierboven.',
  ].join('\n');

  // ── HTML ──────────────────────────────────────────────────────────────────
  const rij = (label, waarde) =>
    '<tr><td style="padding:0 0 18px 0;">'
    + '<div style="font-family:' + SANS + ';font-size:11px;letter-spacing:2px;text-transform:uppercase;color:' + K.navy400 + ';padding-bottom:4px;">' + label + '</div>'
    + '<div style="font-family:' + SANS + ';font-size:16px;line-height:24px;color:' + K.navy600 + ';">' + waarde + '</div>'
    + '</td></tr>';
  const link = (href, tekst) =>
    '<a href="' + ontsnap(href) + '" style="color:' + K.navy600 + ';text-decoration:underline;text-underline-offset:3px;">' + ontsnap(tekst) + '</a>';
  const leeg = '<span style="color:' + K.navy300 + ';">niet ingevuld</span>';
  // losse blokken en geen tabelcellen: past het niet naast elkaar, dan
  // springt de tweede knop gewoon onder de eerste
  const knop = (href, tekst, vol) =>
    '<a href="' + ontsnap(href) + '" style="display:inline-block;margin:0 10px 12px 0;font-family:' + SANS
    + ';font-size:12px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;text-decoration:none;padding:14px 26px;border:1px solid '
    + K.navy600 + ';' + (vol ? 'background:' + K.navy600 + ';color:' + K.wit + ';' : 'background:' + K.wit + ';color:' + K.navy600 + ';')
    + '">' + tekst + '</a>';

  const knoppen = (v.mailOk ? knop(antwoordHref, 'Beantwoorden', true) : '') + (v.telOk ? knop(telHref, 'Bellen', !v.mailOk) : '');

  // de eerste regels in het voorbeeld van de inbox, niet zichtbaar in de mail
  const voorbeeld = v.bericht ? v.bericht.replace(/\s+/g, ' ').slice(0, 110) : zin;

  const html = '<!DOCTYPE html><html lang="nl"><head><meta charset="utf-8">'
    + '<meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">'
    + '<title>' + ontsnap(onderwerp) + '</title>'
    + '<style>@media (max-width:520px){.p{padding-left:24px!important;padding-right:24px!important}.buiten{padding:16px 10px!important}}</style>'
    + '</head>'
    + '<body style="margin:0;padding:0;background:' + K.navy50 + ';">'
    + '<div style="display:none;max-height:0;overflow:hidden;opacity:0;">' + ontsnap(voorbeeld) + '</div>'
    + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:' + K.navy50 + ';">'
    + '<tr><td class="buiten" align="center" style="padding:32px 16px;">'
    + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:' + K.wit + ';border:1px solid ' + K.lijn + ';border-radius:14px;overflow:hidden;">'

    // kop: het donkere blauw van de hero, het woordmerk en de poolster
    + '<tr><td class="p" style="background:' + K.navy900 + ';padding:30px 40px 26px 40px;">'
    + '<div style="font-family:' + SERIF + ';font-size:26px;letter-spacing:6px;color:' + K.wit + ';line-height:30px;">POLARES<span style="font-size:14px;vertical-align:top;letter-spacing:0;">&#10022;</span></div>'
    + '<div style="font-family:' + SANS + ';font-size:11px;letter-spacing:3px;text-transform:uppercase;color:' + K.navy200 + ';padding-top:10px;">Contactformulier</div>'
    + '</td></tr>'

    // titel en de ene zin die zegt wat er gevraagd wordt
    + '<tr><td class="p" style="padding:36px 40px 8px 40px;">'
    + '<div style="font-family:' + SANS + ';font-size:11px;letter-spacing:2px;text-transform:uppercase;color:' + K.navy600 + ';padding-bottom:10px;">&#10022;&nbsp;&nbsp;' + (v.wijze === 'bericht' ? 'Bericht' : 'Contactverzoek') + '</div>'
    + '<div style="font-family:' + SERIF + ';font-size:26px;line-height:32px;color:' + K.navy600 + ';">' + ontsnap(titel) + '</div>'
    + '<div style="font-family:' + SERIF + ';font-size:17px;line-height:26px;color:' + K.navy400 + ';padding-top:10px;">' + ontsnap(zin) + '</div>'
    + '</td></tr>'

    // de gegevens
    + '<tr><td class="p" style="padding:24px 40px 6px 40px;"><div style="border-top:1px solid ' + K.lijn + ';font-size:0;line-height:0;">&nbsp;</div></td></tr>'
    + '<tr><td class="p" style="padding:14px 40px 0 40px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
    + rij('Naam', v.naam ? ontsnap(v.naam) : leeg)
    + rij('E-mail', v.email ? (v.mailOk ? link('mailto:' + v.email, v.email) : ontsnap(v.email)) : leeg)
    + rij('Telefoon', v.telefoon ? (v.telOk ? link(telHref, v.telefoon) : ontsnap(v.telefoon)) : leeg)
    + '</table></td></tr>'

    // het bericht, als een citaat met de haarlijn van de site
    + (v.bericht
      ? '<tr><td class="p" style="padding:4px 40px 10px 40px;">'
        + '<div style="font-family:' + SANS + ';font-size:11px;letter-spacing:2px;text-transform:uppercase;color:' + K.navy400 + ';padding-bottom:8px;">Bericht</div>'
        + '<div style="border-left:2px solid ' + K.navy100 + ';padding:4px 0 4px 18px;font-family:' + SERIF + ';font-size:16px;line-height:26px;color:' + K.navy600 + ';white-space:pre-wrap;">' + ontsnap(v.bericht) + '</div>'
        + '</td></tr>'
      : '')

    // wat je ermee doet
    + (knoppen
      ? '<tr><td class="p" style="padding:22px 40px 12px 40px;">' + knoppen + '</td></tr>'
      : '')

    // voet
    + '<tr><td class="p" style="padding:22px 40px 30px 40px;border-top:1px solid ' + K.lijn + ';background:#FAFBFC;">'
    + '<div style="font-family:' + SANS + ';font-size:12px;line-height:19px;color:' + K.navy300 + ';">'
    + 'Verstuurd via het contactformulier op ' + ontsnap(v.host) + ', ' + ontsnap(v.moment) + '.<br>'
    + (v.mailOk ? 'Beantwoorden gaat rechtstreeks naar ' + ontsnap(v.email) + '.' : 'Geen e-mailadres opgegeven: bel terug op het nummer hierboven.')
    + '</div></td></tr>'

    + '</table></td></tr></table></body></html>';

  return { onderwerp, tekst, html };
}

export function ontsnap(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
