#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const cataloguePath = path.join(root, "resources/data/resources.json");

const escapeHtml = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const inline = (value) => {
  let output = escapeHtml(value);
  output = output.replace(/`([^`]+)`/g, '<code class="notranslate" translate="no">$1</code>');
  output = output.replace(/!\[([^\]]*)\]\(([^ )]+)(?:\s+"[^"]*")?\)/g, '<img src="$2" alt="$1">');
  output = output.replace(/\[([^\]]+)\]\(([^ )]+)(?:\s+"[^"]*")?\)/g, '<a href="$2">$1</a>');
  output = output.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/__([^_]+)__/g, "<strong>$1</strong>");
  output = output.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  return output;
};
const isTableSeparator = (line) => {
  const cells = line.trim().replace(/^\||\|$/g, "").split("|");
  return cells.length > 0 && cells.every((cell) => /^\s*:?-{3,}:?\s*$/.test(cell));
};

function markdownToHtml(markdown) {
  const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i += 1; continue; }
    const fence = line.match(/^\s*```\s*([^\s`]*)/);
    const closingFence = fence ? lines.findIndex((candidate, index) => index > i && /^\s*```\s*$/.test(candidate)) : -1;
    const interveningHeading = fence && closingFence > i
      ? lines.slice(i + 1, closingFence).some((candidate) => /^#{1,6}\s+/.test(candidate))
      : false;
    if (fence && closingFence > i && !interveningHeading) {
      const code = []; i += 1;
      while (i < closingFence) code.push(lines[i++]);
      if (i < lines.length) i += 1;
      const language = fence[1] ? ` class="language-${escapeHtml(fence[1])}"` : "";
      html.push(`<pre class="notranslate" translate="no"><code${language}>${escapeHtml(code.join("\n"))}</code></pre>`); continue;
    }
    if (fence) { html.push(`<p><code class="notranslate" translate="no">${escapeHtml(line.trim())}</code></p>`); i += 1; continue; }
    const heading = line.match(/^(#{1,6})\s+(.+?)\s*#*$/);
    if (heading) { const level = heading[1].length; html.push(`<h${level}>${inline(heading[2])}</h${level}>`); i += 1; continue; }
    if (/^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/.test(line)) { html.push("<hr>"); i += 1; continue; }
    if (line.includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const cells = (row) => row.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
      const headers = cells(line); i += 2; const rows = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) rows.push(cells(lines[i++]));
      html.push(`<div class="document-table-wrap"><table><thead><tr>${headers.map((cell) => `<th>${inline(cell)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${inline(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`); continue;
    }
    if (/^\s*>/.test(line)) {
      const quote = []; while (i < lines.length && /^\s*>/.test(lines[i])) quote.push(lines[i++].replace(/^\s*>\s?/, ""));
      html.push(`<blockquote>${inline(quote.join(" "))}</blockquote>`); continue;
    }
    const list = line.match(/^\s*(?:([-+*])|(\d+)[.)])\s+(.+)$/);
    if (list) {
      const ordered = Boolean(list[2]); const tag = ordered ? "ol" : "ul"; const items = [];
      while (i < lines.length) { const match = lines[i].match(/^\s*(?:([-+*])|(\d+)[.)])\s+(.+)$/); if (!match || Boolean(match[2]) !== ordered) break; items.push(match[3]); i += 1; }
      html.push(`<${tag}>${items.map((item) => `<li>${inline(item)}</li>`).join("")}</${tag}>`); continue;
    }
    const paragraph = [line.trim()]; i += 1;
    while (i < lines.length && lines[i].trim() && !/^(#{1,6})\s+|^\s*```|^\s*>|^\s*(?:[-+*]|\d+[.)])\s+/.test(lines[i]) && !(lines[i].includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) && !/^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/.test(lines[i])) { paragraph.push(lines[i].trim()); i += 1; }
    html.push(`<p>${inline(paragraph.join(" "))}</p>`);
  }
  return html.join("\n");
}

function page(resource, body) {
  const title = escapeHtml(resource.title); const category = escapeHtml(resource.categoryLabel || resource.category); const type = escapeHtml(resource.type);
  return `<!doctype html><html lang="${escapeHtml(resource.language || "en")}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${title} | Cognitive Logic</title><meta name="description" content="${escapeHtml(resource.description)}"><link rel="stylesheet" href="/css/fonts-local.css"><link rel="stylesheet" href="/css/style.css?v=3"><link rel="stylesheet" href="/resources/style.css?v=2"></head><body>
<a class="skip-link" href="#main">Vai al contenuto principale</a><header class="site-header"><div class="container header-inner"><a href="/index.html" class="brand" aria-label="Cognitive Logic — Home"><span class="wordmark wordmark--nav notranslate" translate="no"><span class="wm-top">Cognitive</span><span class="wm-bot">Logic</span></span></a><nav class="main-nav" aria-label="Navigazione principale"><a href="/resources/">Resource Center</a><a href="/research.html">Research</a><a href="/international-watch/">International Watch</a><a href="/trust.html">Trust Center</a></nav></div></header>
<main id="main"><section class="document-hero"><div class="container"><nav class="breadcrumbs" aria-label="Percorso"><a href="/index.html">Home</a> / <a href="/resources/">Resource Center</a> / <span class="notranslate" translate="no">${title}</span></nav><p class="resource-kicker">${category}</p><h1 class="notranslate" translate="no">${title}</h1><dl class="document-metadata"><div><dt>Categoria</dt><dd>${category}</dd></div><div><dt>Formato</dt><dd>${type} · HTML statico</dd></div></dl></div></section>
<section class="section"><div class="container document-layout"><article class="resource-document" data-source="${escapeHtml(resource.source)}">${body}</article></div></section><section class="document-return"><div class="container"><a href="/resources/">← Torna al Resource Center</a></div></section></main>
<footer class="site-footer"><div class="container footer-inner"><div><div class="wordmark wordmark--footer notranslate" translate="no"><span class="wm-top">Cognitive</span><span class="wm-bot">Logic</span></div><div class="footer-copy">© 2026 Roberto Bob Malini — <span class="notranslate" translate="no">Cognitive Logic</span></div></div><div class="footer-links"><a href="/resources/">Resource Center</a><a href="/privacy.html">Privacy</a></div></div></footer></body></html>`;
}

function rebaseDocumentLinks(html, sourcePath) {
  const sourceDirectory = path.posix.dirname(sourcePath);
  return html.replace(/\b(href|src)="([^"]+)"/g, (match, attribute, target) => {
    if (/^(?:[a-z][a-z0-9+.-]*:|\/|#)/i.test(target)) return match;
    return `${attribute}="/${path.posix.normalize(path.posix.join(sourceDirectory, target))}"`;
  });
}

const catalogue = JSON.parse(fs.readFileSync(cataloguePath, "utf8")); let generated = 0;
for (const resource of catalogue) {
  if (!resource.source || !resource.output) throw new Error(`Missing source/output mapping for ${resource.id}`);
  const source = path.resolve(root, resource.source); const output = path.resolve(root, resource.output);
  if (!source.startsWith(`${root}${path.sep}`) || !output.startsWith(`${root}${path.sep}`)) throw new Error(`Unsafe path for ${resource.id}`);
  if (!fs.existsSync(source)) throw new Error(`Source not found: ${resource.source}`);
  const rendered = rebaseDocumentLinks(markdownToHtml(fs.readFileSync(source, "utf8")), resource.source); fs.mkdirSync(path.dirname(output), { recursive: true }); fs.writeFileSync(output, page(resource, rendered)); generated += 1;
}
const cataloguePagePath = path.join(root, "resources/index.html");
const cataloguePage = fs.readFileSync(cataloguePagePath, "utf8");
const cards = catalogue.map((resource) => `<a class="resource-result-card" href="${escapeHtml(resource.url)}">
  <div class="resource-result-meta"><span class="resource-badge">${escapeHtml(resource.type)}</span>${resource.featured ? '<span class="resource-badge resource-badge--featured">In evidenza</span>' : ""}</div>
  <h2 class="notranslate" translate="no">${escapeHtml(resource.title)}</h2><p>${escapeHtml(resource.description)}</p>
  <div class="resource-topic-list">${resource.topics.map((topic) => `<span class="resource-topic">${escapeHtml(topic)}</span>`).join("")}</div>
  <span class="resource-result-link">Apri documento →</span>
</a>`).join("\n");
const updatedCataloguePage = cataloguePage.replace(
  /(<!-- RESOURCE_CARDS_START -->)[\s\S]*?(<!-- RESOURCE_CARDS_END -->)/,
  `$1\n${cards}\n        $2`
);
if (updatedCataloguePage === cataloguePage) throw new Error("Resource catalogue markers not found");
fs.writeFileSync(cataloguePagePath, updatedCataloguePage);
console.log(`Generated ${generated} static resource documents.`);
