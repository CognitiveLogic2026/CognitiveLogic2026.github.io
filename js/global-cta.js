(() => {
  "use strict";

  if (document.getElementById("cl-global-cta")) return;

  const main = document.querySelector("main");
  if (!main) return;

  const path = location.pathname.toLowerCase();
  const lang = (document.documentElement.lang || "it").toLowerCase();
  const en = lang.startsWith("en") ||
    /_en\.html$|\/en\//.test(path);

  const isBrief = path === "/brief/" ||
    path === "/brief/index.html";
  const isFuori = path === "/fuorimenu/" ||
    path === "/fuorimenu/index.html";

  const isUtility = /\/(confirmed|unsubscribed)\//.test(path) ||
    /\/(privacy|privacy_en|cookie|cookie_en|legal|legal_en|accessibilita|accessibility_en|whistleblowing)\.html$/.test(path);

  if (isUtility) return;

  const isHospitality =
    /fuorimenu|restaurant|hotellerie|ristorazione|horeca|hospitality|turismo|coastal|balneari|bolkestein|concessioni-balneari/.test(path);

  const isAssessment =
    /assessment|services\.html|discovery\.html/.test(path);

  const isEditorial =
    /international-watch|research|resources|case-studies|brief|articles|manifesto/.test(path);

  const t = en ? {
    share: "Share this page",
    intro: "Share this analysis with colleagues and readers.",
    copy: "Copy link",
    copied: "Link copied",
    failed: "Select and copy the page address",
    email: "Email",
    newsletters: "Explore our newsletters",
    brief: "Subscribe to Cognitive Logic Brief",
    fuori: "Subscribe to FuoriMenù",
    assessment: "Explore our assessments",
    restaurant: "Restaurant assessment",
    hotel: "Hotel assessment",
    contact: "Contact Cognitive Logic"
  } : {
    share: "Condividi questa pagina",
    intro: "Condividi questo contenuto con colleghi e lettori.",
    copy: "Copia link",
    copied: "Link copiato",
    failed: "Seleziona e copia l'indirizzo della pagina",
    email: "Email",
    newsletters: "Segui le nostre newsletter",
    brief: "Iscriviti a Cognitive Logic Brief",
    fuori: "Iscriviti a FuoriMenù",
    assessment: "Scopri gli assessment",
    restaurant: "Assessment ristorazione",
    hotel: "Assessment hotellerie",
    contact: "Contatta Cognitive Logic"
  };

  const canonical = document.querySelector('link[rel="canonical"]');
  const candidate = canonical ? canonical.href : "";

  let url = location.origin + location.pathname;
  try {
    const parsed = new URL(candidate);
    if (parsed.protocol === "https:" &&
        parsed.hostname === "cognitivelogic.it") {
      url = parsed.href;
    }
  } catch (_) {}

  const title = document.title;

  const section = document.createElement("section");
  section.id = "cl-global-cta";
  section.className = "cl-cta";
  section.setAttribute("aria-label", t.share);

  function heading(text) {
    const h = document.createElement("h2");
    h.textContent = text;
    return h;
  }

  function group() {
    const el = document.createElement("div");
    el.className = "cl-cta-links";
    return el;
  }

  function link(parent, label, href, external = false) {
    const a = document.createElement("a");
    a.textContent = label;
    a.href = href;
    if (external) {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    }
    parent.append(a);
    return a;
  }

  section.append(heading(t.share));

  const intro = document.createElement("p");
  intro.textContent = t.intro;
  section.append(intro);

  const shares = group();

  link(
    shares, "LinkedIn",
    "https://www.linkedin.com/sharing/share-offsite/?url=" +
      encodeURIComponent(url),
    true
  );

  link(
    shares, "WhatsApp",
    "https://api.whatsapp.com/send?text=" +
      encodeURIComponent(title + " " + url),
    true
  );

  link(
    shares, t.email,
    "mailto:?subject=" + encodeURIComponent(title) +
      "&body=" + encodeURIComponent(url)
  );

  const copy = document.createElement("button");
  copy.type = "button";
  copy.textContent = t.copy;

  const status = document.createElement("span");
  status.className = "cl-cta-status";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");

  copy.addEventListener("click", async () => {
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error("clipboard_unavailable");
      }
      await navigator.clipboard.writeText(url);
      status.textContent = t.copied;
    } catch (_) {
      status.textContent = t.failed + ": " + url;
    }
  });

  shares.append(copy);
  section.append(shares, status);

  function addBlock(titleText, entries) {
    const block = document.createElement("div");
    block.className = "cl-cta-newsletters";
    block.append(heading(titleText));
    const links = group();
    for (const entry of entries) {
      link(links, entry[0], entry[1], entry[2] || false);
    }
    block.append(links);
    section.append(block);
  }

  // Le pagine di iscrizione conservano i loro moduli.
  if (!isBrief && !isFuori) {
    const brief = [t.brief, "/brief/"];
    const fuori = [
      t.fuori,
      "https://fuorimenu.substack.com/subscribe",
      true
    ];

    addBlock(
      t.newsletters,
      isHospitality ? [fuori, brief] : [brief, fuori]
    );
  }

  // CTA commerciali soltanto su contenuti pertinenti.
  if (isHospitality && !isFuori && !isAssessment) {
    addBlock(t.assessment, [
      [t.restaurant, "/restaurant-assessment/"],
      [t.hotel, "/hotellerie-assessment/"]
    ]);
  } else if (isAssessment) {
    // Evita di riproporre lo stesso assessment.
    addBlock(t.assessment, [
      [t.contact, "/contact.html"]
    ]);
  } else if (isEditorial && !isBrief) {
    addBlock(t.assessment, [
      [t.assessment, "/assessment.html"]
    ]);
  }

  const footer = document.querySelector("footer");

  if (footer) {
    footer.before(section);
  } else {
    main.append(section);
  }
})();
