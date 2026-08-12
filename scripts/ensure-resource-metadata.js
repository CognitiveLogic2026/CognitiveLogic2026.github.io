#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),root=path.resolve(__dirname,"..");
for(const file of process.argv.slice(2)){
 const target=path.resolve(root,file); let html=fs.readFileSync(target,"utf8");
 const canonical=`https://cognitivelogic.it/${path.dirname(file).replace(/\\/g,"/")}/`.replace(/\/+/g,"/").replace("https:/","https://");
 if(!/rel="canonical"/.test(html)) html=html.replace("</title>",`</title><link rel="canonical" href="${canonical}">`);
 const title=html.match(/<title>(.*?) \| Cognitive Logic<\/title>/)?.[1]||"Cognitive Logic";
 const description=html.match(/<meta name="description" content="([^"]*)">/)?.[1]||"Documento Cognitive Logic";
 if(!/property="og:title"/.test(html)) html=html.replace("</title>",`</title><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${canonical}"><meta property="og:type" content="article"><meta property="og:image" content="https://cognitivelogic.it/img/qen-homepage-og.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="https://cognitivelogic.it/img/qen-homepage-og.png">`);
 fs.writeFileSync(target,html);
}
