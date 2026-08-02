#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const resources = JSON.parse(fs.readFileSync(path.join(root, "resources/data/resources.json"), "utf8"));

const decode = (text) => text
  .replace(/<[^>]+>/g, " ")
  .replaceAll("&amp;", "&").replaceAll("&lt;", "<").replaceAll("&gt;", ">").replaceAll("&quot;", '"').replaceAll("&#039;", "'")
  .replace(/\s+/g, " ").replace(/\s+([.,;:!?])/g, "$1").trim();
const cleanMarkdown = (text) => text
  .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
  .replace(/[*_`]/g, "").replace(/\s+/g, " ").trim();
const markdownParagraphs = (markdown) => {
  const paragraphs = []; let current = []; let inFence = false;
  const flush = () => { if (current.length) paragraphs.push(cleanMarkdown(current.join(" "))); current = []; };
  for (const line of markdown.split("\n")) {
    if (/^\s*```/.test(line)) { flush(); inFence = !inFence; continue; }
    if (inFence || !line.trim() || /^(#{1,6})\s+|^\s*(?:[-+*]|\d+[.)])\s+|^\s*>|^\s*\|/.test(line) || /^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/.test(line)) { flush(); continue; }
    current.push(line.trim());
  }
  flush(); return paragraphs.filter((paragraph) => paragraph.length > 20);
};

let failures = 0;
console.log("TITOLO | SORGENTE | DESTINAZIONE | CONTENUTO VISIBILE | ESITO");
for (const resource of resources) {
  const sourcePath = path.join(root, resource.source);
  const outputPath = path.join(root, resource.output);
  if (!fs.existsSync(sourcePath) || !fs.existsSync(outputPath)) {
    console.log(`${resource.title} | ${resource.source} | ${resource.url} | NO | FAIL`); failures += 1; continue;
  }
  const markdown = fs.readFileSync(sourcePath, "utf8").replace(/\r\n?/g, "\n");
  const html = fs.readFileSync(outputPath, "utf8");
  const article = html.match(/<article\b[^>]*>([\s\S]*?)<\/article>/i)?.[1] || "";
  const sourceHeadings = [...markdown.matchAll(/^(#{1,6})\s+(.+?)\s*#*$/gm)].map((match) => `${match[1].length}:${cleanMarkdown(match[2])}`);
  const htmlHeadings = [...article.matchAll(/<h([1-6])>([\s\S]*?)<\/h\1>/gi)].map((match) => `${match[1]}:${decode(match[2])}`);
  const headingsMatch = JSON.stringify(sourceHeadings) === JSON.stringify(htmlHeadings);
  const sourceParagraphs = markdownParagraphs(markdown).slice(0, 3);
  const articleText = decode(article);
  const paragraphsPresent = sourceParagraphs.every((paragraph) => articleText.includes(paragraph));
  const complete = headingsMatch && paragraphsPresent && article.length > markdown.length * 0.75;
  console.log(`${resource.title} | ${resource.source} | ${resource.url} | ${complete ? "SI" : "NO"} | ${complete ? "PASS" : "FAIL"}`);
  if (!complete) { failures += 1; console.error(`  headings ${htmlHeadings.length}/${sourceHeadings.length}; primi paragrafi ${paragraphsPresent ? "presenti" : "mancanti"}`); }
}
console.log(`\nConfronto Markdown/HTML: ${resources.length - failures}/${resources.length} documenti validi.`);
process.exitCode = failures ? 1 : 0;
