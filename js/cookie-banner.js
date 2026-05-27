/*
 * Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
 * https://www.cognitivelogic.it
 * Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
 */
(function () {
  'use strict';

  var CONSENT_KEY = 'cl_cookie_consent';
  var CONSENT_TTL = 365; // days

  function hasConsent() {
    try { return !!localStorage.getItem(CONSENT_KEY); } catch (e) { return true; }
  }

  function saveConsent(value) {
    try { localStorage.setItem(CONSENT_KEY, value); } catch (e) {}
  }

  function removeBanner(el) {
    el.style.transform = 'translateY(120%)';
    el.style.opacity = '0';
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 400);
  }

  function createBanner() {
    var banner = document.createElement('div');
    banner.id = 'cl-cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Preferenze cookie');
    banner.innerHTML =
      '<div class="cl-cb-inner">' +
        '<div class="cl-cb-text">' +
          '<span class="cl-cb-label">Cookie &amp; Privacy</span>' +
          'Questo sito usa cookie tecnici necessari e carica font da Google Fonts ' +
          '(connessione a server Google LLC, USA). ' +
          '<a href="/cookie.html" class="cl-cb-link">Cookie Policy</a> · ' +
          '<a href="/privacy.html" class="cl-cb-link">Privacy Policy</a>' +
        '</div>' +
        '<div class="cl-cb-actions">' +
          '<button id="cl-cb-refuse" class="cl-cb-btn cl-cb-btn-ghost">Solo necessari</button>' +
          '<button id="cl-cb-accept" class="cl-cb-btn cl-cb-btn-primary">Accetta tutto</button>' +
        '</div>' +
      '</div>';

    var style = document.createElement('style');
    style.textContent =
      '#cl-cookie-banner{' +
        'position:fixed;bottom:0;left:0;right:0;z-index:9999;' +
        'background:rgba(7,17,31,0.97);' +
        'border-top:1px solid rgba(212,175,55,0.25);' +
        'backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);' +
        'transform:translateY(0);opacity:1;' +
        'transition:transform 0.35s ease,opacity 0.35s ease;' +
        'font-family:"DM Mono",monospace;' +
      '}' +
      '.cl-cb-inner{' +
        'max-width:1200px;margin:0 auto;' +
        'display:flex;align-items:center;justify-content:space-between;' +
        'gap:20px;padding:16px 24px;flex-wrap:wrap;' +
      '}' +
      '.cl-cb-label{' +
        'display:block;font-size:0.58rem;letter-spacing:0.18em;text-transform:uppercase;' +
        'color:rgba(212,175,55,0.8);margin-bottom:4px;' +
      '}' +
      '.cl-cb-text{font-size:0.74rem;color:rgba(217,207,191,0.85);line-height:1.6;flex:1;min-width:220px;}' +
      '.cl-cb-link{color:rgba(212,175,55,0.85);text-decoration:underline;text-underline-offset:2px;}' +
      '.cl-cb-link:hover{color:rgba(241,223,155,1);}' +
      '.cl-cb-actions{display:flex;gap:10px;flex-shrink:0;}' +
      '.cl-cb-btn{' +
        'font-family:"DM Mono",monospace;font-size:0.65rem;letter-spacing:0.1em;' +
        'text-transform:uppercase;padding:9px 18px;cursor:pointer;border:1px solid;' +
        'transition:background 0.2s,color 0.2s;white-space:nowrap;' +
      '}' +
      '.cl-cb-btn-primary{' +
        'background:rgba(212,175,55,0.15);border-color:rgba(212,175,55,0.5);' +
        'color:rgba(241,223,155,1);' +
      '}' +
      '.cl-cb-btn-primary:hover{background:rgba(212,175,55,0.28);}' +
      '.cl-cb-btn-ghost{' +
        'background:transparent;border-color:rgba(255,255,255,0.12);' +
        'color:rgba(169,157,139,0.9);' +
      '}' +
      '.cl-cb-btn-ghost:hover{border-color:rgba(255,255,255,0.3);color:rgba(217,207,191,1);}' +
      '@media(max-width:600px){' +
        '.cl-cb-inner{flex-direction:column;align-items:flex-start;}' +
        '.cl-cb-actions{width:100%;}' +
        '.cl-cb-btn{flex:1;text-align:center;}' +
      '}';

    document.head.appendChild(style);
    document.body.appendChild(banner);

    document.getElementById('cl-cb-accept').addEventListener('click', function () {
      saveConsent('all');
      removeBanner(banner);
    });

    document.getElementById('cl-cb-refuse').addEventListener('click', function () {
      saveConsent('necessary');
      removeBanner(banner);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      if (!hasConsent()) createBanner();
    });
  } else {
    if (!hasConsent()) createBanner();
  }
})();
