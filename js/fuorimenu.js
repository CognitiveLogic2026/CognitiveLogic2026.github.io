(() => {
  "use strict";
  const container = document.querySelector("[data-fuorimenu-feed]");
  const status = document.querySelector("[data-feed-status]");
  if (!container || !status) return;

  const fallback = () => {
    status.textContent = "Aggiornamento live non disponibile: sono mostrate le pubblicazioni già sincronizzate.";
    const link = document.createElement("a");
    link.href = "https://fuorimenu.substack.com/";
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = " Consulta FuoriMenù su Substack ↗";
    status.append(link);
  };

  const formatDate = (value) => {
    const normalized = String(value || "").replace(" ", "T");
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return String(value || "Data non disponibile");
    return new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "long", year: "numeric" }).format(date);
  };

  const createArticle = (item) => {
    const url = new URL(String(item.url || ""), window.location.origin);
    if (url.protocol !== "https:" || url.hostname !== "fuorimenu.substack.com") return null;
    const article = document.createElement("a");
    article.className = "fm-article";
    article.href = url.href;
    article.target = "_blank";
    article.rel = "noopener noreferrer";
    article.setAttribute("aria-label", `${item.titolo || "Pubblicazione FuoriMenù"} — apri su Substack`);
    const meta = document.createElement("div");
    meta.className = "fm-article-meta";
    const category = document.createElement("span");
    category.textContent = `Categoria: ${item.tag || "FuoriMenù"}`;
    const date = document.createElement("time");
    date.dateTime = String(item.data || "").slice(0, 10);
    date.textContent = formatDate(item.data);
    const title = document.createElement("h3");
    title.textContent = item.titolo || "Pubblicazione FuoriMenù";
    const excerpt = document.createElement("p");
    excerpt.textContent = item.estratto || "Leggi la pubblicazione originale su FuoriMenù.";
    const cta = document.createElement("span");
    cta.className = "fm-article-link";
    cta.textContent = "Leggi l’originale ↗";
    meta.append(category, date);
    article.append(meta, title, excerpt, cta);
    return article;
  };

  const request = new XMLHttpRequest();
  request.open("GET", "/data/fuorimenu.json", true);
  request.setRequestHeader("Accept", "application/json");
  request.onload = () => {
    try {
      if (request.status < 200 || request.status >= 300) throw new Error("Feed non disponibile");
      const data = JSON.parse(request.responseText);
      const articles = Array.isArray(data.articoli) ? data.articoli.slice(0, 6).map(createArticle).filter(Boolean) : [];
      if (!articles.length) throw new Error("Feed vuoto");
      container.replaceChildren(...articles);
      status.textContent = `${articles.length} pubblicazioni recenti dal feed originale.`;
      status.classList.add("hidden");
    } catch (error) { fallback(); }
  };
  request.onerror = fallback;
  request.send();
})();
