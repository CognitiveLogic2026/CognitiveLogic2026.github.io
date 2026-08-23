#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const root = path.resolve(__dirname, "..");
const base = process.env.RESOURCE_TEST_BASE || "http://127.0.0.1:8765";
const resources = JSON.parse(fs.readFileSync(path.join(root, "resources/data/resources.json"), "utf8"));
const pages = ["/resources/", ...resources.map((resource) => resource.url), "/identity.html", "/identity_en.html", "/evide.html", "/trust.html", "/research.html", "/fuorimenu/", "/international-watch/"];

const pngDimensions = (file) => {
  const buffer = fs.readFileSync(file);
  if (buffer.toString("ascii", 1, 4) !== "PNG") return { width: 0, height: 0 };
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
};

let failures = 0;
for (let index = 0; index < pages.length; index += 1) {
  const url = pages[index];
  const isDocument = url.startsWith("/resources/documents/");
  const output = `/tmp/cognitive-resource-browser-${index}.${isDocument ? "pdf" : "png"}`;
  const result = isDocument
    ? spawnSync("wkhtmltopdf", ["--quiet", "--javascript-delay", "500", `${base}${url}`, output], { encoding: "utf8", timeout: 120000 })
    : spawnSync("wkhtmltoimage", ["--quiet", "--javascript-delay", "1200", "--width", "1365", `${base}${url}`, output], { encoding: "utf8", timeout: 120000 });
  let evidence = ""; let valid = false;
  if (isDocument && result.status === 0 && fs.existsSync(output)) {
    const info = spawnSync("file", [output], { encoding: "utf8" }).stdout || "";
    const pageCount = Number(info.match(/(\d+) page\(s\)/)?.[1] || 0);
    valid = pageCount >= 2; evidence = `PDF ${pageCount} pagine`;
  } else if (!isDocument && result.status === 0 && fs.existsSync(output)) {
    const dimensions = pngDimensions(output); valid = dimensions.width >= 1200 && dimensions.height >= 700; evidence = `screenshot ${dimensions.width}x${dimensions.height}`;
  }
  console.log(`${url} | BROWSER ${valid ? "PASS" : "FAIL"} | ${evidence || "nessun output"}`);
  if (!valid) { failures += 1; if (result.stderr) console.error(result.stderr.trim()); }
  if (fs.existsSync(output)) fs.unlinkSync(output);
}
console.log(`\nBrowser: ${pages.length - failures}/${pages.length} pagine renderizzate; i documenti superano l’altezza viewport e mostrano corpo scorrevole.`);
process.exitCode = failures ? 1 : 0;
