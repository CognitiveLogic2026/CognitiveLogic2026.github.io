#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const pages = ["index.html","services.html","assessment.html","contact.html","framework.html","methodology.html","validation.html","case-studies.html","coste360.html","trust.html","about.html","engagement.html","research.html","operational-record.html","copilot.html"];
const activeFor = file => ({"services.html":"services","assessment.html":"assessment","framework.html":"method","methodology.html":"method","validation.html":"evidence","case-studies.html":"evidence","coste360.html":"evidence","trust.html":"evidence","operational-record.html":"evidence","research.html":"research","about.html":"about","contact.html":"contact"}[file] || "");
const link = (href,label,key,active) => `<a href="${href}"${key===active?' class="active" aria-current="page"':""}>${label}</a>`;
function header(file) {
  const active=activeFor(file);
  return `<header class="site-header"><div class="container header-inner"><a href="/" class="brand notranslate" translate="no" aria-label="Cognitive Logic — Home"><span class="wordmark wordmark--nav"><span class="wm-top">Cognitive</span><span class="wm-bot">Logic</span></span></a><nav class="main-nav" aria-label="Navigazione principale">${link("/services.html","Servizi","services",active)}${link("/assessment.html","Assessment","assessment",active)}${link("/framework.html","Metodo","method",active)}<details class="nav-group"><summary${active==="evidence"?' aria-current="page"':""}>Evidenze</summary><div class="nav-group-menu"><a href="/validation.html">Validation</a><a href="/case-studies.html">Case Studies</a><a href="/trust.html">Trust Center</a><a href="/operational-record.html">Operational Record</a><a href="/coste360.html">Coste360</a></div></details>${link("/research.html","Ricerca","research",active)}${link("/about.html","Chi siamo","about",active)}${link("/contact.html","Contatti","contact",active)}</nav><div class="header-end"><div class="nav-lang" aria-label="Lingua"><a href="/${file}" class="active" lang="it" aria-current="page">IT</a><span class="nav-sep">·</span><a href="/index_en.html" lang="en">EN</a></div><a href="/copilot.html" class="btn btn-ghost"${file==="copilot.html"?' aria-current="page"':""}>QEN Sovereign Copilot</a></div></div></header>`;
}
for (const file of pages) {
  const target=path.join(root,file); let html=fs.readFileSync(target,"utf8");
  const next=html.replace(/<header\b[\s\S]*?<\/header>/i,header(file));
  if(!/<header\b[\s\S]*?<\/header>/i.test(html)) throw new Error(`Header non trovato: ${file}`);
  html=next.replaceAll("Quantificazione Etica Naturale — Knowledge Infrastructure per AI Ethics, Compliance e Territorio.","AI Governance Infrastructure — conoscenza, evidenze e decisioni verificabili.");
  fs.writeFileSync(target,html);
}
